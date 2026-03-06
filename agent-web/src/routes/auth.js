import { Router } from 'express';
import { getOrCreateToken, isAuthBypassed } from '../middleware/auth.js';

const router = Router();

router.post('/login', (req, res) => {
  const { token } = req.body || {};
  const expected = getOrCreateToken();

  if (token === expected) {
    res.cookie('jarvis_token', token, {
      httpOnly: true,
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60 * 1000,
    });
    return res.json({ status: 'authenticated', expiresIn: '7d' });
  }

  res.status(401).json({ error: 'Invalid token' });
});

router.get('/status', (req, res) => {
  const token = getOrCreateToken();
  const authHeader = req.headers.authorization;
  const cookies = req.headers.cookie || '';
  const cookieMatch = cookies.match(/jarvis_token=([^;]+)/);

  const authenticated = Boolean(
    isAuthBypassed() ||
      (authHeader && authHeader.split(' ')[1] === token) ||
      (cookieMatch && cookieMatch[1] === token) ||
      req.query.token === token,
  );

  res.json({ authenticated });
});

router.post('/logout', (req, res) => {
  res.clearCookie('jarvis_token');
  res.json({ status: 'logged out' });
});

export default router;
