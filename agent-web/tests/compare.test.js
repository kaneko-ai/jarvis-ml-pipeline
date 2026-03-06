import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createServer } from 'node:http';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const agentWebRoot = path.join(__dirname, '..');

describe('Compare Module', () => {
  it('compare route file exists', () => {
    assert.ok(fs.existsSync(path.join(agentWebRoot, 'src', 'routes', 'compare.js')));
  });

  it('search.js includes compare functionality', () => {
    const js = fs.readFileSync(path.join(agentWebRoot, 'public', 'js', 'modules', 'search.js'), 'utf8');
    assert.ok(js.includes('compare-check') || js.includes('compare'));
    assert.ok(js.includes('/api/compare'));
  });

  it('styles.css includes compare styles', () => {
    const css = fs.readFileSync(path.join(agentWebRoot, 'public', 'css', 'styles.css'), 'utf8');
    assert.ok(css.includes('compare-bar'));
  });
});

describe('Compare API', () => {
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

  it('GET /api/compare/fields returns fields array', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/compare/fields`);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.ok(Array.isArray(data.fields));
    assert.ok(data.fields.length > 0);
  });

  it('POST /api/compare without paperIds returns 400', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    assert.equal(res.status, 400);
  });

  it('POST /api/compare with single ID returns 400', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paperIds: [1] }),
    });
    assert.equal(res.status, 400);
  });

  it('POST /api/compare with >10 IDs returns 400', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paperIds: [1,2,3,4,5,6,7,8,9,10,11] }),
    });
    assert.equal(res.status, 400);
  });
});

