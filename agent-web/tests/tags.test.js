import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';

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

  const { insertPaper } = await import('../src/db/papers-repository.js');
  insertPaper({
    title: 'Test Paper for Tags',
    doi: '10.1234/tag-test-' + Date.now(),
    year: 2025,
    source: 'test',
  });
});

after(async () => {
  if (server) await new Promise((r) => server.close(r));
});

describe('Paper Tags API', () => {
  it('GET /api/papers/tags returns array', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/papers/tags`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data));
  });

  it('POST /api/papers/:id/tags adds a tag', async () => {
    if (!baseUrl) return;
    const papersRes = await fetch(`${baseUrl}/api/papers?limit=1`);
    const papersData = await papersRes.json();
    if (!papersData.papers?.length) return;
    const paperId = papersData.papers[0].id;

    const res = await fetch(`${baseUrl}/api/papers/${paperId}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag: 'test-tag', color: '#ff5722' }),
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(data.tags);
  });

  it('GET /api/papers/:id/tags returns tags for paper', async () => {
    if (!baseUrl) return;
    const papersRes = await fetch(`${baseUrl}/api/papers?limit=1`);
    const papersData = await papersRes.json();
    if (!papersData.papers?.length) return;
    const paperId = papersData.papers[0].id;

    const res = await fetch(`${baseUrl}/api/papers/${paperId}/tags`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data));
  });

  it('POST /api/papers/:id/tags rejects missing tag', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/papers/1/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    assert.equal(res.status, 400);
  });
});
