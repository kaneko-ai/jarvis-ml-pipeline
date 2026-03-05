import Database from "better-sqlite3";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dbPath = path.join(__dirname, "..", "..", "chat-history.db");

let dbInstance;

function getDb() {
  if (!dbInstance) {
    dbInstance = new Database(dbPath);
    dbInstance.pragma("journal_mode = WAL");
  }
  return dbInstance;
}

function normalizePaper(paper = {}) {
  return {
    title: paper.title ?? "",
    authors: paper.authors ?? null,
    journal: paper.journal ?? null,
    year: paper.year ?? null,
    abstract: paper.abstract ?? null,
    summary: paper.summary ?? null,
    source: paper.source ?? null,
    doi: paper.doi ?? null,
    pmid: paper.pmid ?? null,
    score: paper.score ?? null,
    evidence_level: paper.evidence_level ?? null,
    keyword: paper.keyword ?? null,
  };
}

export function init() {
  try {
    const db = getDb();
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
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(title, year)
      );

      CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_doi_unique
      ON papers(doi)
      WHERE doi IS NOT NULL AND trim(doi) <> '';

      CREATE INDEX IF NOT EXISTS idx_papers_keyword
      ON papers(keyword);

      CREATE INDEX IF NOT EXISTS idx_papers_source
      ON papers(source);

      CREATE INDEX IF NOT EXISTS idx_papers_pmid
      ON papers(pmid);
    `);
  } catch (error) {
    console.error("Failed to initialize papers table:", error);
    throw error;
  }
}

export function insertPaper(paper) {
  try {
    const db = getDb();
    const normalized = normalizePaper(paper);
    const result = db.prepare(`
      INSERT OR IGNORE INTO papers
      (title, authors, journal, year, abstract, summary, source, doi, pmid, score, evidence_level, keyword)
      VALUES
      (@title, @authors, @journal, @year, @abstract, @summary, @source, @doi, @pmid, @score, @evidence_level, @keyword)
    `).run(normalized);

    return {
      inserted: result.changes > 0,
      id: result.changes > 0 ? Number(result.lastInsertRowid) : null,
      changes: result.changes,
    };
  } catch (error) {
    console.error("Failed to insert paper:", error);
    throw error;
  }
}

export function insertPapers(papers) {
  try {
    const db = getDb();
    const list = Array.isArray(papers) ? papers : [];
    const statement = db.prepare(`
      INSERT OR IGNORE INTO papers
      (title, authors, journal, year, abstract, summary, source, doi, pmid, score, evidence_level, keyword)
      VALUES
      (@title, @authors, @journal, @year, @abstract, @summary, @source, @doi, @pmid, @score, @evidence_level, @keyword)
    `);

    const transaction = db.transaction((items) => {
      let inserted = 0;
      for (const item of items) {
        const result = statement.run(normalizePaper(item));
        if (result.changes > 0) {
          inserted += 1;
        }
      }
      return {
        total: items.length,
        inserted,
        ignored: items.length - inserted,
      };
    });

    return transaction(list);
  } catch (error) {
    console.error("Failed to insert papers:", error);
    throw error;
  }
}

export function getPapers({ keyword, source, limit = 20, offset = 0 } = {}) {
  try {
    const db = getDb();
    const where = [];
    const params = [];

    if (keyword) {
      where.push("keyword = ?");
      params.push(keyword);
    }

    if (source) {
      where.push("source = ?");
      params.push(source);
    }

    const safeLimit = Number.isFinite(Number(limit)) ? Math.max(1, Math.min(200, Number(limit))) : 20;
    const safeOffset = Number.isFinite(Number(offset)) ? Math.max(0, Number(offset)) : 0;

    let sql = `
      SELECT id, title, authors, journal, year, abstract, summary, source, doi, pmid, score, evidence_level, keyword, created_at
      FROM papers
    `;

    if (where.length > 0) {
      sql += ` WHERE ${where.join(" AND ")}`;
    }

    sql += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?";
    params.push(safeLimit, safeOffset);

    return db.prepare(sql).all(...params);
  } catch (error) {
    console.error("Failed to get papers:", error);
    throw error;
  }
}

export function getPaperByDoi(doi) {
  try {
    if (!doi) {
      return null;
    }

    const db = getDb();
    return db.prepare(`
      SELECT id, title, authors, journal, year, abstract, summary, source, doi, pmid, score, evidence_level, keyword, created_at
      FROM papers
      WHERE doi = ?
      LIMIT 1
    `).get(doi) ?? null;
  } catch (error) {
    console.error("Failed to get paper by DOI:", error);
    throw error;
  }
}

export function getPaperByPmid(pmid) {
  try {
    if (!pmid) {
      return null;
    }

    const db = getDb();
    return db.prepare(`
      SELECT id, title, authors, journal, year, abstract, summary, source, doi, pmid, score, evidence_level, keyword, created_at
      FROM papers
      WHERE pmid = ?
      LIMIT 1
    `).get(pmid) ?? null;
  } catch (error) {
    console.error("Failed to get paper by PMID:", error);
    throw error;
  }
}

export function searchPapers(query) {
  try {
    const text = typeof query === "string" ? query.trim() : "";
    if (!text) {
      return [];
    }

    const db = getDb();
    const pattern = `%${text}%`;
    return db.prepare(`
      SELECT id, title, authors, journal, year, abstract, summary, source, doi, pmid, score, evidence_level, keyword, created_at
      FROM papers
      WHERE title LIKE ? OR abstract LIKE ?
      ORDER BY created_at DESC, id DESC
      LIMIT 100
    `).all(pattern, pattern);
  } catch (error) {
    console.error("Failed to search papers:", error);
    throw error;
  }
}

export function countPapers() {
  try {
    const db = getDb();
    const row = db.prepare("SELECT COUNT(*) AS count FROM papers").get();
    return row?.count ?? 0;
  } catch (error) {
    console.error("Failed to count papers:", error);
    throw error;
  }
}

export function deletePaper(id) {
  try {
    const db = getDb();
    const result = db.prepare("DELETE FROM papers WHERE id = ?").run(id);
    return result.changes > 0;
  } catch (error) {
    console.error("Failed to delete paper:", error);
    throw error;
  }
}

init();
