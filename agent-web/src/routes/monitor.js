import express from "express";
import Database from "better-sqlite3";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const router = express.Router();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const copilotApiUrl = process.env.COPILOT_API_URL || "http://localhost:4141";
const dbPath = path.join(__dirname, "..", "db", "jarvis.db");
const dataDir = path.join(__dirname, "..", "..", "data");
const memoryLimitBytes = 500 * 1024 * 1024;

const createPipelineRunsTableSql = `
  CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    paper_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error TEXT
  );
`;

function ensurePipelineRunsTable() {
  const db = new Database(dbPath);
  try {
    db.exec(createPipelineRunsTableSql);
  } finally {
    db.close();
  }
}

function safeDecode(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

async function checkCopilotApi() {
  try {
    const response = await fetch(copilotApiUrl, {
      signal: AbortSignal.timeout(3000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

function checkDb() {
  let db;
  try {
    db = new Database(dbPath, { readonly: true });
    db.prepare("SELECT 1").get();
    return true;
  } catch {
    return false;
  } finally {
    if (db) {
      db.close();
    }
  }
}

function parsePaperCount(payload) {
  if (Array.isArray(payload)) {
    return payload.length;
  }

  if (payload && typeof payload === "object") {
    if (typeof payload.paperCount === "number") {
      return payload.paperCount;
    }

    if (Array.isArray(payload.papers)) {
      return payload.papers.length;
    }
  }

  return 0;
}

router.get("/status", async (req, res) => {
  try {
    const [copilotUp, dbOk] = await Promise.all([checkCopilotApi(), Promise.resolve(checkDb())]);

    res.json({
      copilotApi: copilotUp ? "up" : "down",
      db: dbOk ? "ok" : "error",
      uptime: process.uptime(),
      nodeVersion: process.version,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({
      error: "Failed to collect monitor status",
      message: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

router.get("/health", async (req, res) => {
  try {
    const [copilotUp, dbOk] = await Promise.all([checkCopilotApi(), Promise.resolve(checkDb())]);
    const memoryOk = process.memoryUsage().heapUsed < memoryLimitBytes;

    const checks = {
      copilot: copilotUp ? "ok" : "error",
      db: dbOk ? "ok" : "error",
      memory: memoryOk ? "ok" : "error",
    };

    const failures = Object.values(checks).filter((value) => value !== "ok").length;
    const status = failures === 0 ? "healthy" : failures === 1 ? "degraded" : "unhealthy";

    res.json({ status, checks });
  } catch (error) {
    res.status(500).json({
      status: "unhealthy",
      checks: {
        copilot: "error",
        db: "error",
        memory: "error",
      },
      error: error.message,
    });
  }
});

router.get("/history", async (req, res) => {
  try {
    const entries = await fs.readdir(dataDir, { withFileTypes: true });
    const fileEntries = entries.filter((entry) => entry.isFile() && entry.name.endsWith(".json"));
    const results = [];

    for (const entry of fileEntries) {
      const match = entry.name.match(/^(\d{4}-\d{2}-\d{2})-(.+)\.json$/);
      if (!match) {
        continue;
      }

      const filename = entry.name;
      const date = match[1];
      const query = safeDecode(match[2]);
      const filePath = path.join(dataDir, filename);
      const stats = await fs.stat(filePath);

      let paperCount = 0;
      try {
        const content = await fs.readFile(filePath, "utf8");
        const parsed = JSON.parse(content);
        paperCount = parsePaperCount(parsed);
      } catch {
        paperCount = 0;
      }

      results.push({
        filename,
        query,
        date,
        paperCount,
        sizeKB: Number((stats.size / 1024).toFixed(2)),
      });
    }

    results.sort((a, b) => b.date.localeCompare(a.date) || b.filename.localeCompare(a.filename));
    res.json(results);
  } catch (error) {
    if (error.code === "ENOENT") {
      return res.json([]);
    }

    return res.status(500).json({
      error: "Failed to read pipeline run history",
      message: error.message,
    });
  }
});

try {
  ensurePipelineRunsTable();
} catch (error) {
  console.error(`Failed to initialize pipeline_runs table: ${error.message}`);
}

export default router;
