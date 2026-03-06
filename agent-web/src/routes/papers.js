import { Router } from 'express';
import {
  getPapers,
  countPapers,
  searchPapers,
  getPaperByDoi,
  addTag,
  removeTag,
  getTagsForPaper,
  getAllTags,
  getPapersByTag,
} from '../db/papers-repository.js';

const router = Router();

// Keep imports available for future API expansion.
void searchPapers;
void getPaperByDoi;

// GET /api/papers/tags — all tags with counts
router.get('/tags', (req, res) => {
  try {
    res.json(getAllTags());
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// GET /api/papers/by-tag/:tag — papers filtered by tag
router.get('/by-tag/:tag', (req, res) => {
  try {
    const papers = getPapersByTag(req.params.tag);
    res.json({ papers, tag: req.params.tag });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// GET /api/papers/stats — aggregate stats for charts
router.get('/stats', (req, res) => {
  try {
    const papers = getPapers({ limit: 500 });

    const byYear = {};
    const bySource = {};
    const byKeyword = {};
    const byJournal = {};

    for (const p of papers) {
      if (p.year) byYear[p.year] = (byYear[p.year] || 0) + 1;
      if (p.source) bySource[p.source] = (bySource[p.source] || 0) + 1;
      if (p.keyword) byKeyword[p.keyword] = (byKeyword[p.keyword] || 0) + 1;
      if (p.journal) byJournal[p.journal] = (byJournal[p.journal] || 0) + 1;
    }

    const topJournals = Object.entries(byJournal)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .reduce((o, [k, v]) => {
        o[k] = v;
        return o;
      }, {});

    res.json({
      total: papers.length,
      byYear,
      bySource,
      byKeyword,
      topJournals,
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// GET /api/papers/graph — return nodes and edges for citation graph
router.get('/graph', (req, res) => {
  try {
    const limit = Math.min(Number(req.query.limit) || 100, 500);
    const keyword = req.query.keyword || undefined;
    const papers = getPapers({ keyword, limit });

    const nodes = papers.map((p) => ({
      id: p.id,
      title: p.title || 'Untitled',
      authors: p.authors || '',
      year: p.year,
      journal: p.journal || '',
      doi: p.doi,
      pmid: p.pmid,
      score: p.score,
      source: p.source || 'unknown',
      keyword: p.keyword || '',
    }));

    const edges = [];
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        const a = nodes[i];
        const b = nodes[j];
        let weight = 0;

        if (a.keyword && b.keyword && a.keyword === b.keyword) weight += 3;
        if (a.source && b.source && a.source === b.source) weight += 1;
        if (a.year && b.year && Math.abs(a.year - b.year) <= 2) weight += 1;
        if (a.journal && b.journal && a.journal === b.journal) weight += 2;

        if (weight >= 3) {
          edges.push({ source: a.id, target: b.id, weight });
        }
      }
    }

    res.json({ nodes, edges, total: countPapers() });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// GET /api/papers — list papers with optional filters
router.get('/', (req, res) => {
  try {
    const { keyword, source, limit, offset } = req.query;
    const papers = getPapers({
      keyword: keyword || undefined,
      source: source || undefined,
      limit: limit ? Number(limit) : 200,
      offset: offset ? Number(offset) : 0,
    });
    res.json({ papers, total: countPapers() });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// GET /api/papers/:id/tags — tags for a specific paper
router.get('/:id/tags', (req, res) => {
  try {
    res.json(getTagsForPaper(Number(req.params.id)));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// POST /api/papers/:id/tags — add a tag to a paper
router.post('/:id/tags', (req, res) => {
  try {
    const { tag, color } = req.body || {};
    if (!tag) return res.status(400).json({ error: 'tag is required' });
    const added = addTag(Number(req.params.id), tag.trim(), color);
    res.json({ added, tags: getTagsForPaper(Number(req.params.id)) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// DELETE /api/papers/:id/tags/:tag — remove a tag
router.delete('/:id/tags/:tag', (req, res) => {
  try {
    const removed = removeTag(Number(req.params.id), req.params.tag);
    res.json({ removed });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
