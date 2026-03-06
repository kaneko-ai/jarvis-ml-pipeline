import { Router } from 'express';
import {
  addToReadingList,
  updateReadingStatus,
  getReadingList,
  removeFromReadingList,
  getReadingStats,
} from '../db/papers-repository.js';

const router = Router();

router.get('/stats', (req, res) => {
  try {
    res.json(getReadingStats());
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.get('/', (req, res) => {
  try {
    const status = req.query.status || null;
    const limit = Math.min(Number(req.query.limit) || 50, 200);
    res.json(getReadingList(status, limit));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/', (req, res) => {
  const { paperId, priority, dueDate } = req.body || {};
  if (!paperId) return res.status(400).json({ error: 'paperId is required' });
  try {
    const result = addToReadingList(Number(paperId), Number(priority) || 0, dueDate || null);
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.patch('/:paperId', (req, res) => {
  const { status, notes } = req.body || {};
  if (!status || !['unread', 'reading', 'done'].includes(status)) {
    return res.status(400).json({ error: 'status must be unread, reading, or done' });
  }
  try {
    const result = updateReadingStatus(Number(req.params.paperId), status, notes ?? null);
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.delete('/:paperId', (req, res) => {
  try {
    const removed = removeFromReadingList(Number(req.params.paperId));
    res.json({ removed });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
