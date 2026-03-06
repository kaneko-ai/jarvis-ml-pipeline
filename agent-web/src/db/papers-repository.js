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

      CREATE TABLE IF NOT EXISTS paper_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        color TEXT DEFAULT '#d4af37',
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(paper_id, tag),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_paper_tags_paper
      ON paper_tags(paper_id);

      CREATE INDEX IF NOT EXISTS idx_paper_tags_tag
      ON paper_tags(tag);

      CREATE TABLE IF NOT EXISTS paper_annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        note TEXT DEFAULT '',
        color TEXT DEFAULT '#ffeb3b',
        page INTEGER DEFAULT 0,
        position_json TEXT DEFAULT '{}',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_annotations_paper
      ON paper_annotations(paper_id);

      CREATE TABLE IF NOT EXISTS reading_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL UNIQUE,
        status TEXT DEFAULT 'unread' CHECK(status IN ('unread','reading','done')),
        priority INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        due_date TEXT,
        started_at TEXT,
        finished_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_reading_list_status
      ON reading_list(status);
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

    const safeLimit = Number.isFinite(Number(limit)) ? Math.max(1, Math.min(500, Number(limit))) : 20;
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

export function deletePaper(identifier) {
  try {
    if (identifier === null || identifier === undefined) {
      return false;
    }

    const db = getDb();
    const rawIdentifier = String(identifier).trim();
    if (!rawIdentifier) {
      return false;
    }

    const isNumericId =
      typeof identifier === "number" ||
      (typeof identifier === "string" && /^\d+$/.test(rawIdentifier));

    const result = isNumericId
      ? db.prepare("DELETE FROM papers WHERE id = ?").run(Number(rawIdentifier))
      : db.prepare("DELETE FROM papers WHERE doi = ?").run(rawIdentifier);

    return result.changes > 0;
  } catch (error) {
    console.error("Failed to delete paper:", error);
    throw error;
  }
}

export function addTag(paperId, tag, color) {
  const db = getDb();
  const result = db.prepare(
    "INSERT OR IGNORE INTO paper_tags (paper_id, tag, color) VALUES (?, ?, ?)"
  ).run(paperId, tag, color || "#d4af37");
  return result.changes > 0;
}

export function removeTag(paperId, tag) {
  const db = getDb();
  const result = db.prepare(
    "DELETE FROM paper_tags WHERE paper_id = ? AND tag = ?"
  ).run(paperId, tag);
  return result.changes > 0;
}

export function getTagsForPaper(paperId) {
  const db = getDb();
  return db.prepare(
    "SELECT tag, color FROM paper_tags WHERE paper_id = ? ORDER BY tag"
  ).all(paperId);
}

export function getAllTags() {
  const db = getDb();
  return db.prepare(
    "SELECT tag, color, COUNT(*) as count FROM paper_tags GROUP BY tag, color ORDER BY count DESC"
  ).all();
}

export function getPapersByTag(tag, limit = 50) {
  const db = getDb();
  return db.prepare(`
    SELECT p.*, GROUP_CONCAT(pt.tag || ':' || pt.color) as tags
    FROM papers p
    JOIN paper_tags pt ON p.id = pt.paper_id
    WHERE pt.tag = ?
    GROUP BY p.id
    ORDER BY p.created_at DESC
    LIMIT ?
  `).all(tag, limit);
}
export function addAnnotation(
  paperId,
  text,
  note = "",
  color = "#ffeb3b",
  page = 0,
  positionJson = "{}"
) {
  const db = getDb();
  const result = db.prepare(
    "INSERT INTO paper_annotations (paper_id, text, note, color, page, position_json) VALUES (?, ?, ?, ?, ?, ?)"
  ).run(paperId, text, note, color, page, positionJson);
  return { id: Number(result.lastInsertRowid), inserted: result.changes > 0 };
}

export function getAnnotationsForPaper(paperId) {
  const db = getDb();
  return db.prepare(
    "SELECT id, paper_id, text, note, color, page, position_json, created_at FROM paper_annotations WHERE paper_id = ? ORDER BY page, id"
  ).all(paperId);
}

export function deleteAnnotation(annotationId) {
  const db = getDb();
  return db.prepare("DELETE FROM paper_annotations WHERE id = ?").run(annotationId).changes > 0;
}

export function searchAnnotations(query) {
  const db = getDb();
  const pattern = `%${String(query).trim()}%`;
  return db.prepare(`
    SELECT a.id, a.paper_id, a.text, a.note, a.color, a.page, a.created_at, p.title as paper_title, p.doi
    FROM paper_annotations a
    JOIN papers p ON a.paper_id = p.id
    WHERE a.text LIKE ? OR a.note LIKE ?
    ORDER BY a.created_at DESC LIMIT 100
  `).all(pattern, pattern);
}

export function addToReadingList(paperId, priority = 0, dueDate = null) {
  const db = getDb();
  const result = db.prepare(
    "INSERT OR IGNORE INTO reading_list (paper_id, priority, due_date) VALUES (?, ?, ?)"
  ).run(paperId, priority, dueDate);
  return { added: result.changes > 0 };
}

export function updateReadingStatus(paperId, status, notes = null) {
  const db = getDb();
  const now = new Date().toISOString();
  let extra = "";
  const params = [status, now];
  if (status === "reading") {
    extra = ", started_at = COALESCE(started_at, ?)";
    params.push(now);
  }
  if (status === "done") {
    extra += ", finished_at = ?";
    params.push(now);
  }
  if (notes !== null) {
    extra += ", notes = ?";
    params.push(notes);
  }
  params.push(paperId);
  const result = db.prepare(
    `UPDATE reading_list SET status = ?, updated_at = ?${extra} WHERE paper_id = ?`
  ).run(...params);
  return { updated: result.changes > 0 };
}

export function getReadingList(status = null, limit = 50) {
  const db = getDb();
  let sql = `
    SELECT r.*, p.title, p.authors, p.year, p.doi, p.source, p.score
    FROM reading_list r
    JOIN papers p ON r.paper_id = p.id
  `;
  const params = [];
  if (status) {
    sql += " WHERE r.status = ?";
    params.push(status);
  }
  sql += " ORDER BY r.priority DESC, r.created_at DESC LIMIT ?";
  params.push(limit);
  return db.prepare(sql).all(...params);
}

export function removeFromReadingList(paperId) {
  const db = getDb();
  return db.prepare("DELETE FROM reading_list WHERE paper_id = ?").run(paperId).changes > 0;
}

export function getReadingStats() {
  const db = getDb();
  const rows = db.prepare(
    "SELECT status, COUNT(*) as count FROM reading_list GROUP BY status"
  ).all();
  const stats = { unread: 0, reading: 0, done: 0, total: 0 };
  for (const row of rows) {
    stats[row.status] = row.count;
    stats.total += row.count;
  }
  return stats;
}

init();






