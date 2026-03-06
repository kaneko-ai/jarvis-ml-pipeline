import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';

process.env.NODE_ENV = 'test';

let app;
let server;
let baseUrl;

before(async () => {
  const mod = await import('../src/server.js');
  app = mod.app || mod.default;
  if (!app) return;
  await new Promise((resolve) => {
    server = createServer(app);
    server.listen(0, () => {
      baseUrl = `http://localhost:${server.address().port}`;
      resolve();
    });
  });
});

after(async () => {
  if (server) await new Promise((resolve) => server.close(resolve));
});

describe('Auth Endpoints', () => {
  it('GET /api/health is open (no auth required)', async () => {
    const res = await fetch(`${baseUrl}/api/health`);
    assert.equal(res.status, 200);
  });

  it('GET /api/auth/status returns authenticated in test env', async () => {
    const res = await fetch(`${baseUrl}/api/auth/status`);
    const data = await res.json();
    assert.equal(data.authenticated, true);
  });

  it('POST /api/auth/login with wrong token returns 401', async () => {
    const res = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: 'wrong-token' }),
    });
    assert.equal(res.status, 401);
  });

  it('API endpoints accessible in test mode', async () => {
    const res = await fetch(`${baseUrl}/api/skills`);
    assert.equal(res.status, 200);
  });
});
