import express from "express";
import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { notifyDigestComplete } from "../skills/discord-notify.js";

const router = express.Router();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const agentWebRoot = path.join(__dirname, "..", "..");
const projectRoot = path.join(agentWebRoot, "..");
const digestDir = path.join(agentWebRoot, "data", "digests");

const digestModuleCandidates = [
  path.join(projectRoot, "daily-digest.js"),
  path.join(projectRoot, "scripts", "daily-digest.js"),
  path.join(agentWebRoot, "daily-digest.js"),
  path.join(agentWebRoot, "src", "daily-digest.js"),
  path.join(agentWebRoot, "src", "skills", "daily-digest.js"),
];

let cachedDigestFn = null;

function parseKeywords(rawKeywords) {
  if (Array.isArray(rawKeywords)) {
    return rawKeywords
      .flatMap((value) => String(value).split(","))
      .map((value) => value.trim())
      .filter(Boolean);
  }

  if (typeof rawKeywords === "string") {
    return rawKeywords
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
  }

  return [];
}

function resolveDefaultKeywords(config = {}) {
  const candidates = [
    config?.digest?.keywords,
    config?.daily_digest?.keywords,
    config?.dailyDigest?.keywords,
    config?.search?.digest_keywords,
    config?.search?.default_keywords,
  ];

  for (const candidate of candidates) {
    const parsed = parseKeywords(candidate);
    if (parsed.length) {
      return parsed;
    }
  }

  return [];
}

function resolveKeywords(req) {
  const queryKeywords = parseKeywords(req.query?.keywords);
  if (queryKeywords.length) {
    return queryKeywords;
  }

  return resolveDefaultKeywords(req.app?.locals?.config || {});
}

function initSSE(res) {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  if (typeof res.flushHeaders === "function") {
    res.flushHeaders();
  }
}

function sendSSE(res, payload) {
  res.write(`data: ${JSON.stringify(payload)}\n\n`);
}

function pickFirstNumber(...values) {
  for (const value of values) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return 0;
}

function extractKeywordStats(result) {
  if (!result || typeof result !== "object") {
    return [];
  }

  if (Array.isArray(result.keywordStats)) {
    return result.keywordStats
      .map((entry) => {
        if (!entry || typeof entry !== "object") {
          return null;
        }
        const keyword = String(entry.keyword ?? entry.term ?? "").trim();
        if (!keyword) {
          return null;
        }
        return {
          keyword,
          count: pickFirstNumber(
            entry.count,
            entry.paperCount,
            Array.isArray(entry.papers) ? entry.papers.length : undefined
          ),
        };
      })
      .filter(Boolean);
  }

  if (result.keywordStats && typeof result.keywordStats === "object") {
    return Object.entries(result.keywordStats)
      .map(([keyword, count]) => ({
        keyword,
        count: pickFirstNumber(count),
      }))
      .filter((entry) => entry.keyword);
  }

  if (Array.isArray(result.byKeyword)) {
    return result.byKeyword
      .map((entry) => {
        if (!entry || typeof entry !== "object") {
          return null;
        }
        const keyword = String(entry.keyword ?? entry.term ?? "").trim();
        if (!keyword) {
          return null;
        }
        return {
          keyword,
          count: pickFirstNumber(
            entry.count,
            entry.paperCount,
            Array.isArray(entry.papers) ? entry.papers.length : undefined
          ),
        };
      })
      .filter(Boolean);
  }

  if (Array.isArray(result.keywordCounts)) {
    return result.keywordCounts
      .map((entry) => {
        if (!entry || typeof entry !== "object") {
          return null;
        }
        const keyword = String(entry.keyword ?? entry.term ?? "").trim();
        if (!keyword) {
          return null;
        }
        return {
          keyword,
          count: pickFirstNumber(entry.count, entry.paperCount),
        };
      })
      .filter(Boolean);
  }

  if (result.byKeyword && typeof result.byKeyword === "object") {
    return Object.entries(result.byKeyword)
      .map(([keyword, value]) => ({
        keyword,
        count: pickFirstNumber(
          value?.count,
          value?.paperCount,
          Array.isArray(value?.papers) ? value.papers.length : undefined,
          value
        ),
      }))
      .filter((entry) => entry.keyword);
  }

  if (Array.isArray(result.keywords)) {
    return result.keywords
      .map((keyword) => String(keyword ?? "").trim())
      .filter(Boolean)
      .map((keyword) => ({ keyword, count: 0 }));
  }

  if (Array.isArray(result.config?.keywords)) {
    return result.config.keywords
      .map((keyword) => String(keyword ?? "").trim())
      .filter(Boolean)
      .map((keyword) => ({ keyword, count: 0 }));
  }

  return [];
}

function normalizePaperEntry(entry) {
  if (!entry || typeof entry !== "object") {
    return null;
  }

  const title = String(entry.title ?? entry.paperTitle ?? "").trim();
  if (!title) {
    return null;
  }

  return {
    title,
    keyword: String(entry.keyword ?? entry.term ?? "").trim() || null,
    source: String(entry.source ?? entry.journal ?? "").trim() || null,
    year: pickFirstNumber(entry.year) || null,
    score: pickFirstNumber(entry.score, entry.relevance) || null,
    url: String(entry.url ?? entry.link ?? entry.doi ?? "").trim() || null,
  };
}

function extractTopPapers(result) {
  if (!result || typeof result !== "object") {
    return [];
  }

  const candidates = [result.topPapers, result.top_papers, result.papers, result.results];

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      const normalized = candidate.map(normalizePaperEntry).filter(Boolean);
      if (normalized.length) {
        return normalized.slice(0, 10);
      }
    }
  }

  return [];
}

function summarizeDigestResult(result, keywords) {
  const payload = result?.payload && typeof result.payload === "object" ? result.payload : result;
  const keywordStats = extractKeywordStats(payload);
  const topPapers = extractTopPapers(payload);

  const totalFromStats = keywordStats.reduce((sum, entry) => sum + (entry.count || 0), 0);
  const totalPapers = pickFirstNumber(
    payload?.totalPapers,
    payload?.total_papers,
    payload?.paperCount,
    payload?.totalDeduped,
    payload?.totalMerged,
    payload?.papers?.length,
    payload?.results?.length,
    payload?.topPapers?.length,
    totalFromStats,
    topPapers.length
  );

  const keywordCount = keywordStats.length || keywords.length;

  return {
    keywordCount,
    totalPapers,
    keywordStats,
    topPapers,
  };
}

function inferDateFromFilename(filename) {
  const match = filename.match(/(\d{4}-\d{2}-\d{2})/);
  if (!match) {
    return null;
  }
  const date = new Date(`${match[1]}T00:00:00.000Z`);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function inferTotalPapersFromPayload(payload) {
  return pickFirstNumber(
    payload?.totalPapers,
    payload?.total_papers,
    payload?.paperCount,
    payload?.totalDeduped,
    payload?.totalMerged,
    payload?.topPapers?.length,
    payload?.papers?.length,
    payload?.results?.length
  );
}

function inferKeywordCountFromPayload(payload) {
  const stats = extractKeywordStats(payload);
  if (stats.length) {
    return stats.length;
  }

  if (Array.isArray(payload?.keywords)) {
    return payload.keywords.length;
  }

  if (Array.isArray(payload?.config?.keywords)) {
    return payload.config.keywords.length;
  }

  return 0;
}

async function resolveDigestFunction() {
  if (cachedDigestFn) {
    return cachedDigestFn;
  }

  for (const candidate of digestModuleCandidates) {
    if (!fs.existsSync(candidate)) {
      continue;
    }

    const moduleUrl = pathToFileURL(candidate).href;
    const module = await import(moduleUrl);
    const resolved =
      typeof module.runDailyDigest === "function"
        ? module.runDailyDigest
        : typeof module.default === "function"
          ? module.default
          : null;

    if (resolved) {
      cachedDigestFn = resolved;
      return cachedDigestFn;
    }
  }

  throw new Error(
    "runDailyDigest() was not found. Expected daily-digest.js exporting runDailyDigest()."
  );
}

async function invokeRunDailyDigest(runDailyDigest, keywords, onProgress) {
  const source = Function.prototype.toString.call(runDailyDigest);
  const acceptsObject = /\(\s*\{/.test(source) || /\(\s*options\b/.test(source);

  if (acceptsObject) {
    return runDailyDigest({ keywords, onProgress });
  }

  if (runDailyDigest.length >= 2) {
    return runDailyDigest(keywords, onProgress);
  }

  if (runDailyDigest.length === 1) {
    return runDailyDigest(keywords);
  }

  return runDailyDigest();
}

async function handleDigestRun(req, res) {
  initSSE(res);

  const keywords = resolveKeywords(req);
  const startedAt = new Date().toISOString();

  let clientClosed = false;
  req.on("close", () => {
    clientClosed = true;
  });

  try {
    sendSSE(res, {
      status: "started",
      message: `Running daily digest for ${keywords.length || 0} keyword(s)...`,
      keywords,
      startedAt,
    });

    const runDailyDigest = await resolveDigestFunction();

    const result = await invokeRunDailyDigest(runDailyDigest, keywords, (progressPayload) => {
      if (clientClosed) {
        return;
      }

      if (typeof progressPayload === "string") {
        sendSSE(res, {
          status: "progress",
          message: progressPayload,
        });
        return;
      }

      if (progressPayload && typeof progressPayload === "object") {
        sendSSE(res, {
          status: "progress",
          ...progressPayload,
        });
      }
    });

    const summary = summarizeDigestResult(result, keywords);
    const digestNotificationPayload = {
      date:
        result?.payload?.date ||
        result?.date ||
        new Date().toISOString().slice(0, 10),
      keywordCounts: summary.keywordStats,
      totalDeduped: summary.totalPapers,
      topPapers: summary.topPapers,
    };

    Promise.resolve()
      .then(() => notifyDigestComplete(digestNotificationPayload))
      .catch((notifyError) => {
        console.warn("[Digest] Discord notification skipped:", notifyError.message);
      });

    if (!clientClosed) {
      sendSSE(res, {
        done: true,
        status: "completed",
        completedAt: new Date().toISOString(),
        summary,
        result: result ?? null,
      });
    }
  } catch (error) {
    if (!clientClosed) {
      sendSSE(res, {
        error: error?.message || "Digest run failed.",
      });
    }
  } finally {
    if (!clientClosed) {
      res.end();
    }
  }
}

router.get("/run", handleDigestRun);
router.post("/run", handleDigestRun);

router.get("/history", async (req, res) => {
  try {
    const entries = await fsp.readdir(digestDir, { withFileTypes: true });
    const digestFiles = entries.filter(
      (entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".json")
    );

    const items = [];
    for (const entry of digestFiles) {
      const filePath = path.join(digestDir, entry.name);
      const stat = await fsp.stat(filePath);

      let payload = null;
      try {
        const raw = await fsp.readFile(filePath, "utf8");
        payload = JSON.parse(raw);
      } catch {
        payload = null;
      }

      const basePayload =
        payload?.payload && typeof payload.payload === "object" ? payload.payload : payload;

      const date =
        basePayload?.generatedAt ||
        basePayload?.date ||
        inferDateFromFilename(entry.name) ||
        stat.mtime.toISOString();

      const keywordCount = basePayload ? inferKeywordCountFromPayload(basePayload) : 0;
      const totalPapers = basePayload ? inferTotalPapersFromPayload(basePayload) : 0;

      items.push({
        filename: entry.name,
        date,
        keywordCount,
        totalPapers,
        sizeKB: Number((stat.size / 1024).toFixed(2)),
        _mtimeMs: stat.mtimeMs,
      });
    }

    items.sort((a, b) => b._mtimeMs - a._mtimeMs);

    return res.json(items.map(({ _mtimeMs, ...item }) => item));
  } catch (error) {
    if (error?.code === "ENOENT") {
      return res.json([]);
    }

    return res.status(500).json({
      error: error?.message || "Failed to read digest history.",
    });
  }
});

router.get("/report/:filename", async (req, res) => {
  try {
    const rawName = String(req.params.filename || "").trim();
    const safeName = path.basename(rawName);

    if (!safeName || safeName !== rawName) {
      return res.status(404).json({ error: "Report not found." });
    }

    const extension = path.extname(safeName).toLowerCase();
    if (extension !== ".json" && extension !== ".md") {
      return res.status(404).json({ error: "Report not found." });
    }

    const reportPath = path.join(digestDir, safeName);

    try {
      await fsp.access(reportPath, fs.constants.R_OK);
    } catch {
      return res.status(404).json({ error: "Report not found." });
    }

    return res.sendFile(reportPath);
  } catch (error) {
    return res.status(500).json({
      error: error?.message || "Failed to read digest report.",
    });
  }
});

export default router;
