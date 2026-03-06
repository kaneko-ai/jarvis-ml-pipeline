import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const agentWebRoot = path.join(__dirname, '..');

describe('Annotations Module', () => {
  it('annotations route file exists', () => {
    assert.ok(fs.existsSync(path.join(agentWebRoot, 'src', 'routes', 'annotations.js')));
  });

  it('papers-repository exports annotation functions', async () => {
    const mod = await import(pathToFileURL(path.join(agentWebRoot, 'src', 'db', 'papers-repository.js')).href);
    assert.equal(typeof mod.addAnnotation, 'function');
    assert.equal(typeof mod.getAnnotationsForPaper, 'function');
    assert.equal(typeof mod.deleteAnnotation, 'function');
    assert.equal(typeof mod.searchAnnotations, 'function');
  });

  it('searchAnnotations returns array for empty results', async () => {
    const mod = await import(pathToFileURL(path.join(agentWebRoot, 'src', 'db', 'papers-repository.js')).href);
    const results = mod.searchAnnotations('xyznonexistent12345');
    assert.ok(Array.isArray(results));
  });
});

describe('Annotations API', () => {
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

  it('GET /api/annotations/search without q returns 400', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/annotations/search`);
    assert.equal(res.status, 400);
  });

  it('GET /api/annotations/search with q returns array', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/annotations/search?q=test`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data));
  });

  it('GET /api/annotations/999999 returns empty array', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/annotations/999999`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data));
    assert.equal(data.length, 0);
  });

  it('POST /api/annotations/1 without text returns 400', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/annotations/1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    assert.equal(res.status, 400);
  });
});

