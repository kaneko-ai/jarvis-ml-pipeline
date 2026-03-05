import Database from "better-sqlite3";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Keep this aligned with database.js / papers-repository.js database location.
const dbPath = path.join(__dirname, "..", "..", "chat-history.db");

let dbInstance;

function normalizeText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeConfidence(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 1.0;
  return Math.max(0, Math.min(1, n));
}

function getDb() {
  if (!dbInstance) {
    dbInstance = new Database(dbPath);
    dbInstance.pragma("journal_mode = WAL");
    initMemoryStore();
  }
  return dbInstance;
}

function initMemoryStore() {
  dbInstance.exec(`
    CREATE TABLE IF NOT EXISTS facts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT NOT NULL,
      value TEXT NOT NULL,
      source_session TEXT,
      category TEXT DEFAULT 'general',
      confidence REAL DEFAULT 1.0,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now')),
      UNIQUE(key)
    );

    CREATE TABLE IF NOT EXISTS user_preferences (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT NOT NULL UNIQUE,
      value TEXT NOT NULL,
      updated_at TEXT DEFAULT (datetime('now'))
    );
  `);
}

export function storeFact({ key, value, sourceSession = null, category = "general", confidence = 1.0 } = {}) {
  const safeKey = normalizeText(key);
  const safeValue = normalizeText(value);
  const safeCategory = normalizeText(category) || "general";
  const safeSourceSession = normalizeText(sourceSession) || null;
  const safeConfidence = normalizeConfidence(confidence);

  if (!safeKey || !safeValue) {
    return null;
  }

  const db = getDb();
  db.prepare(`
    INSERT OR REPLACE INTO facts (key, value, source_session, category, confidence, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
  `).run(safeKey, safeValue, safeSourceSession, safeCategory, safeConfidence);

  return getFact(safeKey);
}

export function getFact(key) {
  const safeKey = normalizeText(key);
  if (!safeKey) {
    return null;
  }

  const db = getDb();
  return db.prepare(`
    SELECT id, key, value, source_session, category, confidence, created_at, updated_at
    FROM facts
    WHERE key = ?
    LIMIT 1
  `).get(safeKey) ?? null;
}

export function getFactsByCategory(category) {
  const safeCategory = normalizeText(category);
  if (!safeCategory) {
    return [];
  }

  const db = getDb();
  return db.prepare(`
    SELECT id, key, value, source_session, category, confidence, created_at, updated_at
    FROM facts
    WHERE category = ?
    ORDER BY updated_at DESC, id DESC
  `).all(safeCategory);
}

export function getAllFacts() {
  const db = getDb();
  return db.prepare(`
    SELECT id, key, value, source_session, category, confidence, created_at, updated_at
    FROM facts
    ORDER BY updated_at DESC, id DESC
  `).all();
}

export function deleteFact(key) {
  const safeKey = normalizeText(key);
  if (!safeKey) {
    return false;
  }

  const db = getDb();
  const result = db.prepare("DELETE FROM facts WHERE key = ?").run(safeKey);
  return result.changes > 0;
}

export function setPreference(key, value) {
  const safeKey = normalizeText(key);
  const safeValue = normalizeText(value);
  if (!safeKey || !safeValue) {
    return null;
  }

  const db = getDb();
  db.prepare(`
    INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
    VALUES (?, ?, datetime('now'))
  `).run(safeKey, safeValue);

  return getPreference(safeKey);
}

export function getPreference(key) {
  const safeKey = normalizeText(key);
  if (!safeKey) {
    return null;
  }

  const db = getDb();
  const row = db.prepare(`
    SELECT value
    FROM user_preferences
    WHERE key = ?
    LIMIT 1
  `).get(safeKey);

  return row?.value ?? null;
}

export function getAllPreferences() {
  const db = getDb();
  const rows = db.prepare(`
    SELECT key, value
    FROM user_preferences
    ORDER BY key ASC
  `).all();

  const preferences = {};
  for (const row of rows) {
    preferences[row.key] = row.value;
  }
  return preferences;
}

export function getMemoryContext() {
  const facts = getAllFacts();
  const preferences = getAllPreferences();

  const factPairs = facts.map((fact) => `${fact.key}=${fact.value}`);
  const prefPairs = Object.entries(preferences).map(([key, value]) => `${key}=${value}`);

  if (factPairs.length === 0 && prefPairs.length === 0) {
    return "";
  }

  const sections = [];
  if (factPairs.length > 0) {
    sections.push(`User facts: ${factPairs.join(", ")}`);
  }
  if (prefPairs.length > 0) {
    sections.push(`Preferences: ${prefPairs.join(", ")}`);
  }

  return sections.join("\n");
}

function extractName(text) {
  const patterns = [
    /\byour\s+name\s+is\s+([^\n\r.,!?;:]+)/i,
    /\bname\s*:\s*([^\n\r.,!?;]+)/i,
  ];

  for (const pattern of patterns) {
    const match = pattern.exec(text);
    if (match?.[1]) {
      const candidate = normalizeText(match[1]).replace(/^['\"]+|['\"]+$/g, "");
      if (candidate) {
        return candidate;
      }
    }
  }
  return null;
}

export function extractAndStoreFacts(assistantResponse, sessionId) {
  const text = normalizeText(assistantResponse);
  const sourceSession = normalizeText(sessionId) || null;

  if (!text) {
    return { stored: [] };
  }

  const stored = [];
  const extractedName = extractName(text);
  if (extractedName) {
    const fact = storeFact({
      key: "user_name",
      value: extractedName,
      sourceSession,
      category: "identity",
      confidence: 0.9,
    });
    if (fact) stored.push(fact.key);
  }

  const keywordChecks = ["PD-1", "CRISPR", "spermidine"];
  let interestIndex = 1;
  for (const keyword of keywordChecks) {
    if (!text.toLowerCase().includes(keyword.toLowerCase())) {
      continue;
    }

    const fact = storeFact({
      key: `research_interest_${interestIndex}`,
      value: keyword,
      sourceSession,
      category: "research_interest",
      confidence: 0.8,
    });
    if (fact) {
      stored.push(fact.key);
      interestIndex += 1;
    }
  }

  return { stored };
}

getDb();

