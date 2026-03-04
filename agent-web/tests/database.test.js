import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import Database from "better-sqlite3";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TEST_DB_PATH = path.join(__dirname, "test-chat-history.db");

let db;

function setupTestDB() {
  db = new Database(TEST_DB_PATH);
  db.exec(`
    CREATE TABLE IF NOT EXISTS sessions (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      model TEXT DEFAULT 'gpt-4.1',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
  db.exec(`
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      activity TEXT,
      tools TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    )
  `);
  return db;
}

describe("Database CRUD", () => {
  before(() => {
    setupTestDB();
  });

  after(() => {
    if (db) db.close();
    if (fs.existsSync(TEST_DB_PATH)) fs.unlinkSync(TEST_DB_PATH);
  });

  it("should create a session", () => {
    const stmt = db.prepare(
      "INSERT INTO sessions (id, title, model) VALUES (?, ?, ?)"
    );
    stmt.run("test-session-1", "Test Session", "claude-sonnet-4.6");
    const row = db
      .prepare("SELECT * FROM sessions WHERE id = ?")
      .get("test-session-1");
    assert.equal(row.id, "test-session-1");
    assert.equal(row.title, "Test Session");
    assert.equal(row.model, "claude-sonnet-4.6");
  });

  it("should add a message to session", () => {
    const stmt = db.prepare(
      "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)"
    );
    stmt.run("test-session-1", "user", "Hello JARVIS");
    const row = db
      .prepare("SELECT * FROM messages WHERE session_id = ?")
      .get("test-session-1");
    assert.equal(row.role, "user");
    assert.equal(row.content, "Hello JARVIS");
  });

  it("should retrieve multiple messages in order", () => {
    const stmt = db.prepare(
      "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)"
    );
    stmt.run("test-session-1", "assistant", "Hello! How can I help?");
    stmt.run("test-session-1", "user", "Search PD-1 papers");
    const rows = db
      .prepare(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC"
      )
      .all("test-session-1");
    assert.equal(rows.length, 3);
    assert.equal(rows[0].role, "user");
    assert.equal(rows[1].role, "assistant");
    assert.equal(rows[2].role, "user");
  });

  it("should delete a session and cascade messages", () => {
    db.exec("PRAGMA foreign_keys = ON");
    db.prepare("DELETE FROM sessions WHERE id = ?").run("test-session-1");
    const sessions = db
      .prepare("SELECT * FROM sessions WHERE id = ?")
      .all("test-session-1");
    assert.equal(sessions.length, 0);
    const messages = db
      .prepare("SELECT * FROM messages WHERE session_id = ?")
      .all("test-session-1");
    assert.equal(messages.length, 0);
  });

  it("should handle empty database queries", () => {
    const rows = db.prepare("SELECT * FROM sessions").all();
    assert.equal(rows.length, 0);
  });
});
