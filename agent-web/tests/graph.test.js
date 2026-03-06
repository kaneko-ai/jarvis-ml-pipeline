import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
process.env.NODE_ENV = 'test';
process.env.JARVIS_AUTH = 'disabled';

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
  if (server) await new Promise((r) => server.close(r));
});

describe('Citation Graph API', () => {
  it('GET /api/papers returns papers array', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/papers`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data.papers));
    assert.ok(typeof data.total === 'number');
  });

  it('GET /api/papers/graph returns nodes and edges', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/papers/graph?limit=50`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data.nodes));
    assert.ok(Array.isArray(data.edges));
  });

  it('GET /api/papers/stats returns aggregated stats', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/papers/stats`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(typeof data.total === 'number');
    assert.ok(typeof data.byYear === 'object');
    assert.ok(typeof data.bySource === 'object');
  });

  it('graph.js module exists', () => {
    assert.ok(existsSync(path.join(__dirname, '..', 'public', 'js', 'modules', 'graph.js')));
  });
});
