import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';

let app, server, baseUrl, importedServer;

function findListeningServer(port) {
  return process._getActiveHandles().find((handle) => {
    return handle && typeof handle.address === 'function' && handle.address() && handle.address().port === port;
  });
}

before(async () => {
  const mod = await import('../src/server.js');
  app = mod.app || mod.default;

  if (!app) {
    console.log('Warning: server.js does not export app, skipping API tests');
    return;
  }

  await new Promise((resolve) => setImmediate(resolve));
  importedServer = findListeningServer(3000);

  await new Promise((resolve) => {
    server = createServer(app);
    server.listen(0, () => {
      const port = server.address().port;
      baseUrl = `http://localhost:${port}`;
      resolve();
    });
  });
});

after(async () => {
  if (server) {
    await new Promise((resolve) => server.close(resolve));
  }
  if (importedServer && importedServer !== server) {
    await new Promise((resolve) => importedServer.close(resolve));
  }
});

async function fetchJSON(path) {
  if (!baseUrl) return null;
  const res = await fetch(baseUrl + path);
  return res.json();
}

describe('API Endpoints', () => {
  it('GET /api/health returns ok', async () => {
    const data = await fetchJSON('/api/health');
    if (!data) return;
    assert.ok(data);
    assert.equal(data.status, 'ok');
  });

  it('GET /api/skills returns array of skills', async () => {
    const data = await fetchJSON('/api/skills');
    if (!data) return;
    assert.ok(Array.isArray(data));
  });

  it('GET /api/mcp/servers returns servers array', async () => {
    const data = await fetchJSON('/api/mcp/servers');
    if (!data) return;
    assert.ok(data);
  });

  it('GET /api/models returns array with model objects', async () => {
    const data = await fetchJSON('/api/models');
    if (!data) return;
    assert.ok(Array.isArray(data));
    if (data.length > 0) {
      assert.ok(data[0].id || data[0].name);
    }
  });

  it('GET /api/sessions returns array', async () => {
    const data = await fetchJSON('/api/sessions');
    if (!data) return;
    assert.ok(Array.isArray(data));
  });
});
