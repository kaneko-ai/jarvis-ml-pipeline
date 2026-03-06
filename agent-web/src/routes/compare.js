import { Router } from 'express';
import { getPapers } from '../db/papers-repository.js';

const router = Router();

function buildComparisonTable(papers) {
  const headers = ['Title', 'Authors', 'Year', 'Source', 'Journal', 'Score', 'Evidence Level', 'DOI'];
  const rows = papers.map((paper) => ({
    title: paper.title || 'Untitled',
    authors: paper.authors || 'Unknown',
    year: paper.year || '-',
    source: paper.source || '-',
    journal: paper.journal || '-',
    score: paper.score != null ? String(Number(paper.score).toFixed(1)) : '-',
    evidence_level: paper.evidence_level || '-',
    doi: paper.doi || '-',
  }));

  const mdHeaders = '| ' + headers.join(' | ') + ' |';
  const mdSep = '| ' + headers.map(() => '---').join(' | ') + ' |';
  const mdRows = rows.map((row) =>
    '| ' + [row.title, row.authors, row.year, row.source, row.journal, row.score, row.evidence_level, row.doi].join(' | ') + ' |'
  );

  return {
    headers,
    rows,
    markdown: [mdHeaders, mdSep, ...mdRows].join('\n'),
    paperCount: papers.length,
  };
}

router.post('/', (req, res) => {
  const { paperIds } = req.body || {};
  if (!Array.isArray(paperIds) || paperIds.length < 2) {
    return res.status(400).json({ error: 'paperIds must be an array with at least 2 IDs' });
  }
  if (paperIds.length > 10) {
    return res.status(400).json({ error: 'Maximum 10 papers for comparison' });
  }

  try {
    const allPapers = getPapers({ limit: 500 });
    const idSet = new Set(paperIds.map(Number));
    const selected = allPapers.filter((paper) => idSet.has(paper.id));

    if (selected.length < 2) {
      return res.status(404).json({ error: 'Not enough papers found for comparison' });
    }

    res.json(buildComparisonTable(selected));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.get('/fields', (req, res) => {
  res.json({
    fields: ['title', 'authors', 'year', 'source', 'journal', 'score', 'evidence_level', 'doi', 'abstract', 'keyword'],
  });
});

export default router;
