import { Router } from 'express';
import { countPapers, insertPaper as addPaper } from '../db/papers-repository.js';

const router = Router();

router.post('/bibtex', (req, res) => {
  try {
    const { content } = req.body || {};
    if (!content) return res.status(400).json({ error: 'No content provided' });

    const papers = parseBibTeX(content);
    let imported = 0;
    for (const paper of papers) {
      const result = addPaper(paper);
      if (result?.inserted) imported += 1;
    }

    return res.json({ imported, total: papers.length, dbCount: countPapers() });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

router.post('/ris', (req, res) => {
  try {
    const { content } = req.body || {};
    if (!content) return res.status(400).json({ error: 'No content provided' });

    const papers = parseRIS(content);
    let imported = 0;
    for (const paper of papers) {
      const result = addPaper(paper);
      if (result?.inserted) imported += 1;
    }

    return res.json({ imported, total: papers.length, dbCount: countPapers() });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

function parseBibTeX(text) {
  const entries = [];
  const entryRegex = /@(\w+)\s*\{([^,]*),([\s\S]*?)\n?\}\s*(?=@|$)/g;
  let match;

  while ((match = entryRegex.exec(text)) !== null) {
    const type = match[1].toLowerCase();
    if (type === 'string' || type === 'comment' || type === 'preamble') continue;

    const fields = parseFields(match[3]);
    entries.push({
      title: fields.title || 'Untitled',
      authors: fields.author || '',
      journal: fields.journal || fields.booktitle || '',
      year: fields.year ? parseInt(fields.year, 10) || null : null,
      doi: fields.doi || null,
      pmid: fields.pmid || null,
      abstract: fields.abstract || '',
      source: 'bibtex-import',
      score: null,
    });
  }

  return entries;
}

function parseFields(text) {
  const fields = {};
  const fieldRegex = /(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|"([^"]*)"|(\d+))/g;
  let match;

  while ((match = fieldRegex.exec(text)) !== null) {
    const key = match[1].toLowerCase();
    const value = (match[2] || match[3] || match[4] || '').trim();
    fields[key] = value;
  }

  return fields;
}

function parseRIS(text) {
  const entries = [];
  const lines = text.split(/\r?\n/);
  let current = null;
  let authors = [];

  for (const line of lines) {
    const tag = line.substring(0, 2).trim();
    const sep = line.substring(2, 6);
    const value = line.substring(6).trim();

    if (tag === 'TY' && sep.includes('-')) {
      current = {};
      authors = [];
      continue;
    }

    if (tag === 'ER' && current) {
      current.authors = authors.join('; ');
      current.source = 'ris-import';
      current.score = null;
      entries.push(current);
      current = null;
      authors = [];
      continue;
    }

    if (!current) continue;

    switch (tag) {
      case 'TI':
      case 'T1':
        current.title = value;
        break;
      case 'AU':
      case 'A1':
        authors.push(value);
        break;
      case 'JO':
      case 'JF':
      case 'T2':
        current.journal = value;
        break;
      case 'PY':
      case 'Y1':
        current.year = parseInt(value, 10) || null;
        break;
      case 'DO':
        current.doi = value;
        break;
      case 'AB':
      case 'N2':
        current.abstract = value;
        break;
      case 'AN':
        if (/^\d+$/.test(value)) current.pmid = value;
        break;
      default:
        break;
    }
  }

  return entries;
}

export default router;
