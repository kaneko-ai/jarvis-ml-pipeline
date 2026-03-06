import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const agentWebRoot = path.join(__dirname, '..');

describe('Reading List Module', () => {
  it('reading-list route file exists', () => {
    assert.ok(fs.existsSync(path.join(agentWebRoot, 'src', 'routes', 'reading-list.js')));
  });

  it('papers-repository exports reading list functions', async () => {
    const mod = await import(pathToFileURL(path.join(agentWebRoot, 'src', 'db', 'papers-repository.js')).href);
    assert.equal(typeof mod.addToReadingList, 'function');
    assert.equal(typeof mod.updateReadingStatus, 'function');
    assert.equal(typeof mod.getReadingList, 'function');
    assert.equal(typeof mod.removeFromReadingList, 'function');
    assert.equal(typeof mod.getReadingStats, 'function');
  });

  it('getReadingStats returns stats object', async () => {
    const mod = await import(pathToFileURL(path.join(agentWebRoot, 'src', 'db', 'papers-repository.js')).href);
    const stats = mod.getReadingStats();
    assert.equal(typeof stats.unread, 'number');
    assert.equal(typeof stats.reading, 'number');
    assert.equal(typeof stats.done, 'number');
    assert.equal(typeof stats.total, 'number');
  });

  it('getReadingList returns array', async () => {
    const mod = await import(pathToFileURL(path.join(agentWebRoot, 'src', 'db', 'papers-repository.js')).href);
    const list = mod.getReadingList();
    assert.ok(Array.isArray(list));
  });
});

describe('Reading List API', () => {
  let app;
  let server;
  let baseUrl;

  before(async () => {
    const mod = await import(pathToFileURL(path.join(agentWebRoot, 'src', 'server.js')).href);
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

  it('GET /api/reading-list returns array', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/reading-list`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data));
  });

  it('GET /api/reading-list/stats returns stats object', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/reading-list/stats`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(typeof data.unread, 'number');
    assert.equal(typeof data.total, 'number');
  });

  it('POST /api/reading-list without paperId returns 400', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/reading-list`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    assert.equal(res.status, 400);
  });

  it('PATCH /api/reading-list/1 with invalid status returns 400', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/reading-list/1`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'invalid' }),
    });
    assert.equal(res.status, 400);
  });
});

