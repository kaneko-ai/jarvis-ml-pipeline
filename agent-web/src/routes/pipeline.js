import express from "express";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { searchLivePapers } from "../llm/paper-search.js";
import { ParallelRunner } from "../llm/parallel-runner.js";
import { summarizeBatch } from "../llm/gemini-summarizer.js";

const router = express.Router();
const TOTAL_STEPS = 7;
const PIPELINE_TIMEOUT_MS = 120000;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dataDir = path.join(__dirname, "..", "..", "data");

function ensureDataDirectory() {
  fs.mkdirSync(dataDir, { recursive: true });
}

function sendSSE(res, payload) {
  res.write(`data: ${JSON.stringify(payload)}\n\n`);
}

function sendProgress(res, step, progress, message) {
  sendSSE(res, { step, total: TOTAL_STEPS, progress, message });
}

function normalizeText(input) {
  return String(input ?? "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(input) {
  return normalizeText(input)
    .split(" ")
    .filter((token) => token.length > 1);
}

function titleSimilarity(titleA, titleB) {
  const a = normalizeText(titleA);
  const b = normalizeText(titleB);
  if (!a || !b) return 0;
  if (a === b) return 1;
  if (a.includes(b) || b.includes(a)) return 0.92;

  const setA = new Set(tokenize(a));
  const setB = new Set(tokenize(b));
  if (!setA.size || !setB.size) return 0;

  let intersection = 0;
  for (const token of setA) {
    if (setB.has(token)) intersection += 1;
  }
  const union = new Set([...setA, ...setB]).size;
  return union > 0 ? intersection / union : 0;
}

function deduplicateByTitle(papers, threshold = 0.85) {
  const deduped = [];
  for (const paper of papers) {
    const exists = deduped.some(
      (saved) => titleSimilarity(saved.title, paper.title) >= threshold
    );
    if (!exists) deduped.push(paper);
  }
  return deduped;
}

function scorePaperAgainstQuery(paper, queryKeywords) {
  const title = normalizeText(paper.title);
  const body = normalizeText(`${paper.title} ${paper.authors} ${paper.journal}`);
  let score = 0;

  for (const keyword of queryKeywords) {
    if (!keyword) continue;
    if (title.includes(keyword)) {
      score += 5;
    } else if (body.includes(keyword)) {
      score += 2;
    }
  }

  return score;
}

function extractSummaryText(summaryResult, fallbackPaper) {
  if (typeof summaryResult === "string") {
    const normalized = summaryResult.trim();
    return normalized || null;
  }

  if (summaryResult && typeof summaryResult === "object") {
    if (typeof summaryResult.summary === "string") {
      const normalized = summaryResult.summary.trim();
      return normalized || null;
    }

    if (typeof summaryResult.text === "string") {
      const normalized = summaryResult.text.trim();
      return normalized || null;
    }
  }

  if (fallbackPaper && typeof fallbackPaper.summary === "string") {
    const normalized = fallbackPaper.summary.trim();
    return normalized || null;
  }

  return null;
}

function sanitizeQueryForFilename(query) {
  const cleaned = String(query ?? "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, "")
    .replace(/^\.+/, "")
    .replace(/\.+$/, "")
    .slice(0, 80);
  return cleaned || "query";
}

function buildTimestampForFilename(date = new Date()) {
  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  const second = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day}_${hour}-${minute}-${second}`;
}

function inferQueryFromFilename(filename) {
  const base = filename.replace(/\.json$/i, "");
  return base.replace(/^\d{4}-\d{2}-\d{2}(?:_\d{2}-\d{2}-\d{2})?-/, "");
}

function createPipelineTimeoutError() {
  const error = new Error(
    `Pipeline timed out after ${Math.round(PIPELINE_TIMEOUT_MS / 1000)} seconds and was aborted.`
  );
  error.code = "PIPELINE_TIMEOUT";
  return error;
}

function isPipelineTimeoutError(error) {
  return error?.code === "PIPELINE_TIMEOUT";
}

ensureDataDirectory();

router.get("/run", async (req, res) => {
  const query = String(req.query.query ?? "").trim();
  const limit = Math.min(Math.max(Number.parseInt(req.query.limit, 10) || 50, 1), 200);

  if (!query) {
    return res.status(400).json({ error: "query is required" });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  if (typeof res.flushHeaders === "function") {
    res.flushHeaders();
  }

  const runner = new ParallelRunner();
  const pipelineStartedAt = Date.now();
  let clientClosed = false;
  let timedOut = false;

  const timeoutTimer = setTimeout(() => {
    timedOut = true;
    runner.shutdown();
  }, PIPELINE_TIMEOUT_MS);
  if (typeof timeoutTimer.unref === "function") {
    timeoutTimer.unref();
  }

  req.on("close", () => {
    clientClosed = true;
    runner.shutdown();
  });

  function ensurePipelineActive() {
    if (timedOut) {
      throw createPipelineTimeoutError();
    }
    if (clientClosed) {
      throw new Error("Client disconnected.");
    }
  }

  async function runWithPipelineDeadline(taskFactory) {
    ensurePipelineActive();

    const elapsedMs = Date.now() - pipelineStartedAt;
    const remainingMs = PIPELINE_TIMEOUT_MS - elapsedMs;
    if (remainingMs <= 0) {
      timedOut = true;
      runner.shutdown();
      throw createPipelineTimeoutError();
    }

    let timer = null;
    try {
      return await Promise.race([
        Promise.resolve().then(taskFactory),
        new Promise((_, reject) => {
          timer = setTimeout(() => {
            timedOut = true;
            runner.shutdown();
            reject(createPipelineTimeoutError());
          }, remainingMs);
        }),
      ]);
    } finally {
      if (timer) {
        clearTimeout(timer);
      }
    }
  }

  try {
    ensureDataDirectory();

    let searchResult = {
      pubmed: [],
      semanticScholar: [],
      openAlex: [],
    };
    let allPapers = [];
    let deduplicatedPapers = [];
    let scoredPapers = [];
    let topPapers = [];
    let papersWithSummaries = [];
    let output = null;

    sendProgress(res, 1, 0, "Searching papers from PubMed and Semantic Scholar...");
    try {
      const rawSearchResult = await runWithPipelineDeadline(() =>
        runner.runInPool("apiPool", () => searchLivePapers(query, limit))
      );
      ensurePipelineActive();

      searchResult = {
        pubmed: Array.isArray(rawSearchResult?.pubmed) ? rawSearchResult.pubmed : [],
        semanticScholar: Array.isArray(rawSearchResult?.semanticScholar)
          ? rawSearchResult.semanticScholar
          : [],
        openAlex: Array.isArray(rawSearchResult?.openAlex) ? rawSearchResult.openAlex : [],
      };

      const pubmedSucceeded = searchResult.pubmed.length > 0;
      const semanticSucceeded = searchResult.semanticScholar.length > 0;
      const openAlexSucceeded = searchResult.openAlex.length > 0;

      sendSSE(res, {
        sourceStatus: {
          pubmed: pubmedSucceeded ? "succeeded" : "failed",
          semanticScholar: semanticSucceeded ? "succeeded" : "failed",
          openAlex: openAlexSucceeded ? "succeeded" : "failed_or_unused",
        },
      });

      if (!pubmedSucceeded && !semanticSucceeded) {
        sendSSE(res, {
          error: "Search failed: PubMed and Semantic Scholar both failed. Pipeline stopped.",
        });
        return;
      }

      if (!pubmedSucceeded || !semanticSucceeded) {
        const fallbackWarning = !pubmedSucceeded
          ? "PubMed search failed. Continuing with Semantic Scholar only."
          : "Semantic Scholar search failed. Continuing with PubMed only.";
        sendSSE(res, { warning: fallbackWarning });
      }

      if (pubmedSucceeded && semanticSucceeded) {
        allPapers = [
          ...searchResult.pubmed,
          ...searchResult.semanticScholar,
          ...searchResult.openAlex,
        ];
      } else if (pubmedSucceeded) {
        allPapers = [...searchResult.pubmed];
      } else {
        allPapers = [...searchResult.semanticScholar];
      }

      sendProgress(
        res,
        1,
        15,
        `Search completed: ${allPapers.length} papers fetched. Sources pubmed=${pubmedSucceeded ? "ok" : "failed"}, semanticScholar=${semanticSucceeded ? "ok" : "failed"}.`
      );
    } catch (error) {
      if (clientClosed) return;
      const message = isPipelineTimeoutError(error)
        ? error.message
        : `Search step failed: ${error.message || "unknown error"}`;
      sendSSE(res, { error: message });
      return;
    }
    if (clientClosed) return;

    sendProgress(res, 2, 15, "Deduplicating papers by title similarity...");
    try {
      ensurePipelineActive();
      deduplicatedPapers = deduplicateByTitle(allPapers);
      sendProgress(
        res,
        2,
        25,
        `Deduplication completed: ${allPapers.length - deduplicatedPapers.length} duplicates removed.`
      );
    } catch (error) {
      if (clientClosed) return;
      const message = isPipelineTimeoutError(error)
        ? error.message
        : `Deduplication step failed: ${error.message || "unknown error"}`;
      sendSSE(res, { error: message });
      return;
    }
    if (clientClosed) return;

    sendProgress(res, 3, 25, "Scoring relevance against query keywords...");
    try {
      const keywords = [...new Set(tokenize(query))];
      scoredPapers = await runWithPipelineDeadline(() =>
        runner.runAll(
          "apiPool",
          deduplicatedPapers.map((paper) => async () => ({
            ...paper,
            score: scorePaperAgainstQuery(paper, keywords),
          }))
        )
      );
      ensurePipelineActive();
      sendProgress(res, 3, 40, "Relevance scoring completed.");
    } catch (error) {
      if (clientClosed) return;
      const message = isPipelineTimeoutError(error)
        ? error.message
        : `Scoring step failed: ${error.message || "unknown error"}`;
      sendSSE(res, { error: message });
      return;
    }
    if (clientClosed) return;

    sendProgress(res, 4, 40, "Sorting papers by score and taking top results...");
    try {
      ensurePipelineActive();
      topPapers = scoredPapers
        .sort((a, b) => (b.score || 0) - (a.score || 0))
        .slice(0, limit);
      sendProgress(res, 4, 50, `Top ${topPapers.length} papers selected.`);
    } catch (error) {
      if (clientClosed) return;
      const message = isPipelineTimeoutError(error)
        ? error.message
        : `Ranking step failed: ${error.message || "unknown error"}`;
      sendSSE(res, { error: message });
      return;
    }
    if (clientClosed) return;

    sendProgress(res, 5, 50, "Preparing Gemini summarization...");
    try {
      papersWithSummaries = topPapers.map((paper) => ({
        ...paper,
        summary: paper.summary ?? null,
      }));
      const summaryTargetCount = Math.min(10, papersWithSummaries.length);

      if (summaryTargetCount === 0) {
        sendProgress(res, 5, 80, "No papers available for summarization.");
      } else if (!process.env.GEMINI_API_KEY) {
        const warningMessage = "GEMINI_API_KEY is not set. Skipping Gemini summarization.";
        sendSSE(res, { warning: warningMessage });
        sendProgress(res, 5, 80, warningMessage);
      } else {
        const summarizedBatchResult = await runWithPipelineDeadline(() =>
          summarizeBatch(papersWithSummaries.slice(0, summaryTargetCount), {
            concurrency: 2,
            delayMs: 1200,
            timeoutMs: 30000,
            onProgress: (progressPayload, fallbackTotal) => {
              if (clientClosed || timedOut) return;

              let current = 0;
              let total = summaryTargetCount;

              if (typeof progressPayload === "number") {
                current = progressPayload;
                if (Number.isFinite(fallbackTotal) && fallbackTotal > 0) {
                  total = Number(fallbackTotal);
                }
              } else if (progressPayload && typeof progressPayload === "object") {
                const parsedCurrent = Number(
                  progressPayload.current ??
                    progressPayload.completed ??
                    progressPayload.index ??
                    progressPayload.count ??
                    0
                );
                const parsedTotal = Number(progressPayload.total ?? progressPayload.max ?? total);
                if (Number.isFinite(parsedCurrent)) {
                  current = parsedCurrent;
                }
                if (Number.isFinite(parsedTotal) && parsedTotal > 0) {
                  total = parsedTotal;
                }
              }

              const safeTotal = Math.max(1, Math.floor(total));
              const safeCurrent = Math.min(safeTotal, Math.max(0, Math.floor(current)));
              const progress = Math.min(
                80,
                Math.max(50, Math.round(50 + (safeCurrent / safeTotal) * 30))
              );
              sendProgress(
                res,
                5,
                progress,
                `Summarizing paper ${Math.max(1, safeCurrent)}/${safeTotal}...`
              );
            },
          })
        );
        ensurePipelineActive();

        const summarizedPapers = Array.isArray(summarizedBatchResult)
          ? summarizedBatchResult
          : Array.isArray(summarizedBatchResult?.papers)
            ? summarizedBatchResult.papers
            : [];

        papersWithSummaries = papersWithSummaries.map((paper, index) => {
          if (index >= summaryTargetCount) {
            return {
              ...paper,
              summary: paper.summary ?? null,
            };
          }

          return {
            ...paper,
            summary: extractSummaryText(summarizedPapers[index], paper),
            summaryError: summarizedPapers[index]?.summaryError,
            summaryWarning: summarizedPapers[index]?.summaryWarning,
          };
        });

        const summaryIssues = papersWithSummaries.slice(0, summaryTargetCount);
        const summaryErrorCount = summaryIssues.filter((paper) => paper.summaryError).length;
        const summaryWarningCount = summaryIssues.filter((paper) => paper.summaryWarning).length;

        if (summaryErrorCount > 0 || summaryWarningCount > 0) {
          const summaryWarningMessage =
            summaryErrorCount >= summaryTargetCount
              ? "Gemini summarization failed for all target papers. Continuing without summaries."
              : `Gemini summarization completed with issues: ${summaryErrorCount} errors, ${summaryWarningCount} warnings.`;
          sendSSE(res, { warning: summaryWarningMessage });
        }

        sendProgress(res, 5, 80, `Summarization completed for ${summaryTargetCount} papers.`);
      }
    } catch (error) {
      if (clientClosed) return;
      if (isPipelineTimeoutError(error)) {
        sendSSE(res, { error: error.message });
        return;
      }

      const warningMessage =
        `Gemini summarization failed: ${error.message || "unknown error"}. ` +
        "Continuing without summaries.";
      sendSSE(res, { warning: warningMessage });
      sendProgress(res, 5, 80, warningMessage);
    }
    if (clientClosed) return;

    sendProgress(res, 6, 80, "Formatting structured JSON result...");
    try {
      ensurePipelineActive();
      const generatedAt = new Date().toISOString();
      output = {
        query,
        limit,
        generatedAt,
        paperCount: papersWithSummaries.length,
        sourceCounts: {
          pubmed: searchResult.pubmed?.length ?? 0,
          semanticScholar: searchResult.semanticScholar?.length ?? 0,
          openAlex: searchResult.openAlex?.length ?? 0,
        },
        papers: papersWithSummaries.map((paper, index) => ({
          rank: index + 1,
          ...paper,
          summary: paper.summary ?? null,
        })),
      };
      sendProgress(res, 6, 90, "Structured JSON prepared.");
    } catch (error) {
      if (clientClosed) return;
      const message = isPipelineTimeoutError(error)
        ? error.message
        : `Formatting step failed: ${error.message || "unknown error"}`;
      sendSSE(res, { error: message });
      return;
    }
    if (clientClosed) return;

    sendProgress(res, 7, 90, "Saving result file...");
    let savedFile = null;
    try {
      ensurePipelineActive();
      const filename = `${buildTimestampForFilename()}-${sanitizeQueryForFilename(query)}.json`;
      const filePath = path.join(dataDir, filename);
      fs.writeFileSync(filePath, `${JSON.stringify(output, null, 2)}\n`, "utf8");
      savedFile = `agent-web/data/${filename}`;
    } catch (error) {
      if (clientClosed) return;
      if (isPipelineTimeoutError(error)) {
        sendSSE(res, { error: error.message });
        return;
      }
      const warningMessage =
        `Failed to save result file: ${error.message || "unknown error"}. ` +
        "Returning results via SSE only.";
      console.error(warningMessage);
      sendSSE(res, { warning: warningMessage });
    }

    sendProgress(res, 7, 100, "Pipeline completed.");
    const donePayload = {
      done: true,
      paperCount: papersWithSummaries.length,
      file: savedFile,
    };
    if (!savedFile) {
      donePayload.results = output;
    }
    sendSSE(res, donePayload);
  } catch (error) {
    if (!clientClosed) {
      const message = isPipelineTimeoutError(error)
        ? error.message
        : error.message || "Pipeline execution failed.";
      sendSSE(res, { error: message });
    }
  } finally {
    clearTimeout(timeoutTimer);
    runner.shutdown();
    if (!clientClosed) {
      res.end();
    }
  }
});

router.get("/history", (req, res) => {
  try {
    ensureDataDirectory();
    const files = fs
      .readdirSync(dataDir)
      .filter((filename) => filename.toLowerCase().endsWith(".json"))
      .map((filename) => {
        const filePath = path.join(dataDir, filename);
        const stat = fs.statSync(filePath);
        let query = inferQueryFromFilename(filename);
        let date = stat.mtime.toISOString();
        let paperCount = 0;

        try {
          const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
          query = parsed.query || query;
          date = parsed.generatedAt || date;
          paperCount = Number(parsed.paperCount ?? parsed.papers?.length ?? 0);
        } catch {
          paperCount = 0;
        }

        return {
          filename,
          query,
          date,
          paperCount,
          mtime: stat.mtimeMs,
        };
      })
      .sort((a, b) => b.mtime - a.mtime)
      .map(({ mtime, ...entry }) => entry);

    return res.json(files);
  } catch (error) {
    return res.status(500).json({ error: error.message || "Failed to read history." });
  }
});

export default router;
