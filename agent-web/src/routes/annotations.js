import { Router } from 'express';
import {
  addAnnotation,
  getAnnotationsForPaper,
  deleteAnnotation,
  searchAnnotations,
} from '../db/papers-repository.js';

const router = Router();

router.get('/search', (req, res) => {
  const q = String(req.query.q || '').trim();
  if (!q) return res.status(400).json({ error: 'q parameter is required' });
  try {
    res.json(searchAnnotations(q));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.get('/:paperId', (req, res) => {
  try {
    res.json(getAnnotationsForPaper(Number(req.params.paperId)));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/:paperId', (req, res) => {
  const { text, note, color, page, position } = req.body || {};
  if (!text) return res.status(400).json({ error: 'text is required' });
  try {
    const result = addAnnotation(
      Number(req.params.paperId),
      text,
      note || '',
      color || '#ffeb3b',
      Number(page) || 0,
      typeof position === 'object' ? JSON.stringify(position) : String(position || '{}')
    );
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.delete('/:id', (req, res) => {
  try {
    const removed = deleteAnnotation(Number(req.params.id));
    res.json({ removed });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
