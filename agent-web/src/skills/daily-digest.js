import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Database from "better-sqlite3";
import dotenv from "dotenv";
import yaml from "js-yaml";

import { searchLivePapers } from "../llm/paper-search.js";
import { summarizeBatch } from "../llm/gemini-summarizer.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const AGENT_WEB_ROOT = path.resolve(__dirname, "..", "..");
const PROJECT_ROOT = path.resolve(AGENT_WEB_ROOT, "..");

function toLocalDateString(date = new Date()) {
  const y = String(date.getFullYear());
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function normalizeTitle(title) {
  return String(title ?? "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function flattenSearchResults(searchResult) {
  return [
    ...(Array.isArray(searchResult?.pubmed) ? searchResult.pubmed : []),
    ...(Array.isArray(searchResult?.semanticScholar) ? searchResult.semanticScholar : []),
    ...(Array.isArray(searchResult?.openAlex) ? searchResult.openAlex : []),
  ];
}

function dedupeByTitle(papers) {
  const seen = new Set();
  const deduped = [];

  for (const paper of papers) {
    const key = normalizeTitle(paper?.title);
    if (!key || seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(paper);
  }

  return deduped;
}

function buildMarkdownReport({ date, keywordCounts, topPapers }) {
  const lines = [];
  lines.push(`# Daily Digest (${date})`);
  lines.push("");
  lines.push("## Keyword Counts");

  for (const entry of keywordCounts) {
    lines.push(`- ${entry.keyword}: ${entry.count} papers`);
  }

  lines.push("");
  lines.push("## Top Papers");

  if (topPapers.length === 0) {
    lines.push("- No papers available.");
    return `${lines.join("\n")}\n`;
  }

  topPapers.forEach((paper, index) => {
    const title = paper?.title || "No title";
    const authors = paper?.authors || "Unknown";
    const year = paper?.year || "Unknown";
    const summary = paper?.summary || "(Summary unavailable)";

    lines.push(`${index + 1}. ${title}`);
    lines.push(`   - Authors: ${authors}`);
    lines.push(`   - Year: ${year}`);
    lines.push(`   - Summary: ${summary}`);
    if (paper?.url) {
      lines.push(`   - URL: ${paper.url}`);
    }
  });

  return `${lines.join("\n")}\n`;
}

function readDigestConfig(configPath) {
  const raw = fs.readFileSync(configPath, "utf8");
  const parsed = yaml.load(raw) || {};
  const digest = parsed.digest || {};

  return {
    keywords: Array.isArray(digest.keywords) ? digest.keywords.map((v) => String(v).trim()).filter(Boolean) : [],
    papersPerKeyword: Number.isFinite(Number(digest.papers_per_keyword))
      ? Math.max(1, Number(digest.papers_per_keyword))
      : 10,
    summarizeTopN: Number.isFinite(Number(digest.summarize_top_n))
      ? Math.max(1, Number(digest.summarize_top_n))
      : 5,
    outputDir: String(digest.output_dir || "agent-web/data/digests"),
  };
}

function initializePipelineRunsTable(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS pipeline_runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      query TEXT NOT NULL,
      status TEXT NOT NULL,
      result_json TEXT,
      created_at TEXT NOT NULL
    )
  `);
}

function savePipelineRun({ dbPath, payload }) {
  const db = new Database(dbPath);
  try {
    initializePipelineRunsTable(db);
    db.prepare(`
      INSERT INTO pipeline_runs (query, status, result_json, created_at)
      VALUES (?, ?, ?, ?)
    `).run("daily-digest", "completed", JSON.stringify(payload), new Date().toISOString());
  } finally {
    db.close();
  }
}

function resolveRuntimePaths(options = {}) {
  const configPath = options.configPath || path.join(PROJECT_ROOT, "config.yaml");
  const envPath = options.envPath || path.resolve(process.cwd(), "../.env");
  const dbPath = options.dbPath || path.join(AGENT_WEB_ROOT, "chat-history.db");
  return { configPath, envPath, dbPath };
}

export default async function runDailyDigest(options = {}) {
  const { configPath, envPath, dbPath } = resolveRuntimePaths(options);

  try {
    dotenv.config({ path: envPath });

    const digestConfig = readDigestConfig(configPath);
    const keywords = digestConfig.keywords;
    if (keywords.length === 0) {
      throw new Error("digest.keywords is empty in config.yaml");
    }

    const papersPerKeyword = digestConfig.papersPerKeyword;
    const summarizeTopN = digestConfig.summarizeTopN;
    const outputDir = path.resolve(PROJECT_ROOT, digestConfig.outputDir);
    fs.mkdirSync(outputDir, { recursive: true });

    const mergedPapers = [];
    const keywordCounts = [];

    for (let i = 0; i < keywords.length; i += 1) {
      const keyword = keywords[i];
      console.log(`[Digest] Searching: ${keyword} (${i + 1}/${keywords.length})...`);

      try {
        const searchResult = await searchLivePapers(keyword, papersPerKeyword);
        const allForKeyword = flattenSearchResults(searchResult).slice(0, papersPerKeyword);

        keywordCounts.push({ keyword, count: allForKeyword.length });

        for (const paper of allForKeyword) {
          mergedPapers.push({
            ...paper,
            keyword,
          });
        }
      } catch (error) {
        console.error(`[Digest] Search failed for keyword: ${keyword}`, error?.message || error);
        keywordCounts.push({ keyword, count: 0 });
      }
    }

    const dedupedPapers = dedupeByTitle(mergedPapers);
    console.log(`[Digest] Deduplicated papers: ${mergedPapers.length} -> ${dedupedPapers.length}`);

    const topCandidates = dedupedPapers.slice(0, summarizeTopN);
    let topPapers = topCandidates;

    if (topCandidates.length > 0) {
      try {
        console.log(`[Digest] Summarizing top ${topCandidates.length} papers...`);
        const summarized = await summarizeBatch(topCandidates, {
          concurrency: 2,
          delayMs: 1200,
          timeoutMs: 30000,
          onProgress: ({ current, total }) => {
            console.log(`[Digest] Summarizing: ${current}/${total}`);
          },
        });

        topPapers = summarized.map((paper, index) => ({
          ...topCandidates[index],
          ...paper,
          summary: paper?.summary || topCandidates[index]?.summary || null,
        }));
      } catch (error) {
        console.error("[Digest] Summarization failed. Continue without summaries.", error?.message || error);
      }
    }

    const date = toLocalDateString();
    const markdownPath = path.join(outputDir, `digest-${date}.md`);
    const jsonPath = path.join(outputDir, `digest-${date}.json`);

    const payload = {
      date,
      generatedAt: new Date().toISOString(),
      config: {
        keywords,
        papers_per_keyword: papersPerKeyword,
        summarize_top_n: summarizeTopN,
      },
      keywordCounts,
      totalMerged: mergedPapers.length,
      totalDeduped: dedupedPapers.length,
      topPapers,
    };

    const markdown = buildMarkdownReport({
      date,
      keywordCounts,
      topPapers,
    });

    fs.writeFileSync(markdownPath, markdown, "utf8");
    fs.writeFileSync(jsonPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");

    savePipelineRun({ dbPath, payload });

    console.log(`[Digest] Saved markdown: ${markdownPath}`);
    console.log(`[Digest] Saved json: ${jsonPath}`);

    return {
      status: "completed",
      markdownPath,
      jsonPath,
      payload,
    };
  } catch (error) {
    console.error("[Digest] Failed to run daily digest:", error?.message || error);
    throw error;
  }
}

const isDirectRun =
  process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url));

if (isDirectRun) {
  runDailyDigest().catch(() => {
    process.exitCode = 1;
  });
}
