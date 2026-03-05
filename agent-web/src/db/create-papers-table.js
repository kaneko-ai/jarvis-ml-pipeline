import Database from 'better-sqlite3';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.join(__dirname, 'jarvis.db');
const db = new Database(dbPath);

db.exec(`
  CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT,
    journal TEXT,
    year INTEGER,
    abstract TEXT,
    summary TEXT,
    source TEXT,
    doi TEXT,
    pmid TEXT,
    score REAL,
    evidence_level TEXT,
    keyword TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  )
`);

// 確認
const info = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'").get();
if (info) {
  console.log('SUCCESS: papers table created (or already exists)');
} else {
  console.log('ERROR: papers table was not created');
}

db.close();
