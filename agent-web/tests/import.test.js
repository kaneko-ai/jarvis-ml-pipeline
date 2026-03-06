import { after, before, describe, it } from 'node:test';
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
});

after(async () => {
  if (server) await new Promise((resolve) => server.close(resolve));
});

const sampleBib = `
@article{smith2024,
  title = {CRISPR Gene Therapy Advances},
  author = {Smith, John and Doe, Jane},
  journal = {Nature},
  year = {2024},
  doi = {10.1234/test-import-001},
  abstract = {A sample paper about CRISPR.}
}
@article{tanaka2023,
  title = {PD-1 Immunotherapy Review},
  author = {Tanaka, Yuki},
  journal = {Science},
  year = {2023},
  doi = {10.1234/test-import-002}
}
`;

const sampleRIS = `TY  - JOUR
TI  - Spermidine Autophagy Study
AU  - Yamamoto, Kenji
AU  - Suzuki, Aki
JO  - Cell
PY  - 2025
DO  - 10.1234/test-import-003
AB  - Research on spermidine.
ER  - 
`;

describe('Import API', () => {
  it('POST /api/import/bibtex imports papers', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/import/bibtex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: sampleBib }),
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.total, 2);
    assert.ok(data.imported >= 0);
  });

  it('POST /api/import/ris imports papers', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/import/ris`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: sampleRIS }),
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.total, 1);
  });

  it('POST /api/import/bibtex rejects empty content', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/import/bibtex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    assert.equal(res.status, 400);
  });

  it('handles duplicate DOIs gracefully', async () => {
    if (!baseUrl) return;
    const res = await fetch(`${baseUrl}/api/import/bibtex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: sampleBib }),
    });
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.imported, 0);
  });
});
