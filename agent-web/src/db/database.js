import Database from "better-sqlite3";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { v4 as uuidv4 } from "uuid";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dbPath = path.join(__dirname, "..", "..", "chat-history.db");

let dbInstance;

function parseJsonField(value) {
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function normalizeMessage(row) {
  return {
    ...row,
    agent_activity: parseJsonField(row.agent_activity),
    tool_calls: parseJsonField(row.tool_calls),
  };
}

function initializeDatabase(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS sessions (
      id TEXT PRIMARY KEY,
      title TEXT,
      model TEXT,
      created_at TEXT,
      updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT,
      role TEXT,
      content TEXT,
      agent_activity TEXT,
      tool_calls TEXT,
      created_at TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_messages_session_id
    ON messages(session_id, created_at);

    CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
    ON sessions(updated_at DESC);
  `);
}

export function getDb() {
  if (!dbInstance) {
    dbInstance = new Database(dbPath);
    dbInstance.pragma("journal_mode = WAL");
    initializeDatabase(dbInstance);
  }

  return dbInstance;
}

export function createSession(title = "New Session", model = "gemini/gemini-2.0-flash") {
  const db = getDb();
  const now = new Date().toISOString();
  const session = {
    id: uuidv4(),
    title,
    model,
    created_at: now,
    updated_at: now,
  };

  db.prepare(`
    INSERT INTO sessions (id, title, model, created_at, updated_at)
    VALUES (@id, @title, @model, @created_at, @updated_at)
  `).run(session);

  return session;
}

export function getMessages(sessionId) {
  const db = getDb();
  const rows = db.prepare(`
    SELECT id, session_id, role, content, agent_activity, tool_calls, created_at
    FROM messages
    WHERE session_id = ?
    ORDER BY id ASC
  `).all(sessionId);

  return rows.map(normalizeMessage);
}

export function getSession(id) {
  const db = getDb();
  const session = db.prepare(`
    SELECT id, title, model, created_at, updated_at
    FROM sessions
    WHERE id = ?
  `).get(id);

  if (!session) {
    return null;
  }

  return {
    ...session,
    messages: getMessages(id),
  };
}

export function listSessions(limit = 50) {
  const db = getDb();
  const safeLimit = Number.isFinite(Number(limit)) ? Math.max(1, Math.min(200, Number(limit))) : 50;

  return db.prepare(`
    SELECT id, title, model, created_at, updated_at
    FROM sessions
    ORDER BY updated_at DESC
    LIMIT ?
  `).all(safeLimit);
}

export function deleteSession(id) {
  const db = getDb();
  const transaction = db.transaction((sessionId) => {
    db.prepare("DELETE FROM messages WHERE session_id = ?").run(sessionId);
    return db.prepare("DELETE FROM sessions WHERE id = ?").run(sessionId);
  });

  const result = transaction(id);
  return result.changes > 0;
}

export function addMessage(sessionId, role, content, agentActivity = null, toolCalls = null) {
  const db = getDb();
  const now = new Date().toISOString();
  const statement = db.prepare(`
    INSERT INTO messages (session_id, role, content, agent_activity, tool_calls, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `);

  const result = statement.run(
    sessionId,
    role,
    content,
    agentActivity ? JSON.stringify(agentActivity) : null,
    toolCalls ? JSON.stringify(toolCalls) : null,
    now
  );

  db.prepare(`
    UPDATE sessions
    SET updated_at = ?, title = COALESCE(title, ?)
    WHERE id = ?
  `).run(now, content.slice(0, 60), sessionId);

  return {
    id: result.lastInsertRowid,
    session_id: sessionId,
    role,
    content,
    agent_activity: agentActivity,
    tool_calls: toolCalls,
    created_at: now,
  };
}
