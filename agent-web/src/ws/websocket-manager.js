import { randomUUID } from 'node:crypto';
import { WebSocketServer } from 'ws';

let wss = null;
const clients = new Map();

export function initWebSocket(server) {
  if (wss) return wss;

  wss = new WebSocketServer({ server, path: '/ws' });

  wss.on('connection', (ws) => {
    const clientId = randomUUID();
    clients.set(clientId, { ws, sessionId: null, alive: true });

    ws.on('message', (raw) => {
      try {
        const msg = JSON.parse(raw.toString());
        handleMessage(clientId, msg);
      } catch {
        ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON' }));
      }
    });

    ws.on('pong', () => {
      const client = clients.get(clientId);
      if (client) client.alive = true;
    });

    ws.on('close', () => {
      clients.delete(clientId);
    });

    ws.send(JSON.stringify({
      type: 'connected',
      clientId,
      message: 'JARVIS WebSocket connected',
    }));
  });

  const interval = setInterval(() => {
    clients.forEach((client, id) => {
      if (!client.alive) {
        client.ws.terminate();
        clients.delete(id);
        return;
      }
      client.alive = false;
      client.ws.ping();
    });
  }, 30000);

  wss.on('close', () => {
    clearInterval(interval);
    clients.clear();
    wss = null;
  });

  return wss;
}

function handleMessage(clientId, msg) {
  const client = clients.get(clientId);
  if (!client) return;

  switch (msg.type) {
    case 'join-session':
      client.sessionId = msg.sessionId;
      break;
    case 'ping':
      client.ws.send(JSON.stringify({ type: 'pong', ts: Date.now() }));
      break;
    default:
      break;
  }
}

export function broadcastToSession(sessionId, data) {
  const payload = JSON.stringify(data);
  clients.forEach((client) => {
    if (client.sessionId === sessionId && client.ws.readyState === 1) {
      client.ws.send(payload);
    }
  });
}

export function broadcastAll(data) {
  const payload = JSON.stringify(data);
  clients.forEach((client) => {
    if (client.ws.readyState === 1) {
      client.ws.send(payload);
    }
  });
}

export function getClientCount() {
  return clients.size;
}
