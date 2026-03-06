let ws = null;
let reconnectTimer = null;
let desiredSessionId = null;
const listeners = new Map();

export function connect(sessionId) {
  desiredSessionId = sessionId || desiredSessionId || 'default';

  if (ws && ws.readyState <= 1) {
    if (ws.readyState === WebSocket.OPEN && desiredSessionId) {
      ws.send(JSON.stringify({ type: 'join-session', sessionId: desiredSessionId }));
    }
    return;
  }

  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = protocol + '//' + location.host + '/ws';
  ws = new WebSocket(url);

  ws.onopen = () => {
    console.log('[WS] Connected');
    if (desiredSessionId) {
      ws.send(JSON.stringify({ type: 'join-session', sessionId: desiredSessionId }));
    }
    emit('connected', {});
    clearTimeout(reconnectTimer);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      emit(data.type, data);
    } catch {
    }
  };

  ws.onclose = () => {
    console.log('[WS] Disconnected, reconnecting in 3s...');
    emit('disconnected', {});
    reconnectTimer = setTimeout(() => connect(desiredSessionId), 3000);
  };

  ws.onerror = (err) => {
    console.warn('[WS] Error:', err.message || err);
  };
}

export function send(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

export function on(type, callback) {
  if (!listeners.has(type)) listeners.set(type, new Set());
  listeners.get(type).add(callback);
}

export function off(type, callback) {
  listeners.get(type)?.delete(callback);
}

function emit(type, data) {
  listeners.get(type)?.forEach((callback) => {
    try {
      callback(data);
    } catch (error) {
      console.error('[WS] listener error:', error);
    }
  });
  listeners.get('*')?.forEach((callback) => {
    try {
      callback({ type, ...data });
    } catch {
    }
  });
}

export function disconnect() {
  clearTimeout(reconnectTimer);
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = null;
  }
}

export function isConnected() {
  return Boolean(ws && ws.readyState === WebSocket.OPEN);
}
