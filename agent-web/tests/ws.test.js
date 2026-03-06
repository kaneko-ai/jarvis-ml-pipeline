import { after, before, describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { createServer } from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import WebSocket from 'ws';

process.env.NODE_ENV = 'test';
process.env.JARVIS_AUTH = 'disabled';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

let app;
let httpServer;
let wsServer;
let baseUrl;
let wsUrl;

before(async () => {
  const mod = await import('../src/server.js');
  app = mod.app || mod.default;
  if (!app) return;

  const { initWebSocket } = await import('../src/ws/websocket-manager.js');

  await new Promise((resolve) => {
    httpServer = createServer(app);
    wsServer = initWebSocket(httpServer);
    httpServer.listen(0, () => {
      const port = httpServer.address().port;
      baseUrl = 'http://localhost:' + port;
      wsUrl = 'ws://localhost:' + port + '/ws';
      resolve();
    });
  });
});

after(async () => {
  if (wsServer) {
    await new Promise((resolve) => wsServer.close(resolve));
  }
  if (httpServer) {
    await new Promise((resolve) => httpServer.close(resolve));
  }
});

describe('WebSocket', () => {
  it('ws manager file exists', () => {
    assert.ok(existsSync(path.join(__dirname, '..', 'src', 'ws', 'websocket-manager.js')));
  });

  it('ws-client module exists in public', () => {
    assert.ok(existsSync(path.join(__dirname, '..', 'public', 'js', 'modules', 'ws-client.js')));
  });

  it('accepts websocket connections on /ws', async () => {
    if (!wsUrl) return;

    await new Promise((resolve, reject) => {
      const client = new WebSocket(wsUrl);
      client.once('message', (raw) => {
        const data = JSON.parse(raw.toString());
        assert.equal(data.type, 'connected');
        assert.ok(data.clientId);
        client.close();
        resolve();
      });
      client.once('error', reject);
    });
  });

  it('/api/health includes wsClients field', async () => {
    if (!baseUrl) return;
    const res = await fetch(baseUrl + '/api/health');
    const data = await res.json();
    assert.equal(data.status, 'ok');
    assert.ok('wsClients' in data);
  });
});
