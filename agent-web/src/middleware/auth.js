import { randomBytes } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TOKEN_FILE = path.join(__dirname, '..', '..', 'data', '.auth-token');

let AUTH_TOKEN = process.env.JARVIS_AUTH_TOKEN || null;

function isTestEnvironment() {
  return process.env.NODE_ENV === 'test' || process.execArgv.includes('--test');
}

export function getOrCreateToken() {
  if (AUTH_TOKEN) return AUTH_TOKEN;

  if (existsSync(TOKEN_FILE)) {
    AUTH_TOKEN = readFileSync(TOKEN_FILE, 'utf-8').trim();
    if (AUTH_TOKEN) return AUTH_TOKEN;
  }

  AUTH_TOKEN = randomBytes(32).toString('hex');
  const dataDir = path.dirname(TOKEN_FILE);
  if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true });
  }
  writeFileSync(TOKEN_FILE, `${AUTH_TOKEN}\n`, 'utf-8');
  return AUTH_TOKEN;
}

export function authMiddleware(req, res, next) {
  const openPaths = ['/api/health', '/api/auth/login', '/api/auth/status'];
  if (openPaths.includes(req.path)) return next();

  if (process.env.JARVIS_AUTH === 'disabled') return next();
  if (isTestEnvironment()) return next();

  const token = getOrCreateToken();
  const authHeader = req.headers.authorization;
  if (authHeader) {
    const [scheme, value] = authHeader.split(' ');
    if (scheme === 'Bearer' && value === token) return next();
  }

  if (req.query.token === token) return next();

  const cookies = req.headers.cookie || '';
  const match = cookies.match(/jarvis_token=([^;]+)/);
  if (match && match[1] === token) return next();

  res.status(401).json({ error: 'Unauthorized. Provide Bearer token or login.' });
}

export function isAuthBypassed() {
  return process.env.JARVIS_AUTH === 'disabled' || isTestEnvironment();
}

export default authMiddleware;
