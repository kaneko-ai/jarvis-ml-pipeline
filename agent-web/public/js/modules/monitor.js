import { fetchJson, showToast } from './utils.js';

let monitorRefreshIntervalId = null;
let monitorBindingsApplied = false;

const MONITOR_COLORS = {
  ok: '#00ff88',
  error: '#ff4444',
  degraded: '#ffaa00',
  cardA: '#1a1a2e',
  cardB: '#111',
  border: '#333',
  text: '#e8ecf2',
  muted: '#9ca3af',
};

function formatUptimeToClock(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = Math.floor(total % 60);
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function monitorStatusKind(value) {
  if (value === true) return 'ok';
  if (value === false || value == null) return 'error';
  const normalized = String(value).toLowerCase();
  if (['ok', 'up', 'healthy', 'pass'].includes(normalized)) return 'ok';
  if (['degraded', 'warn', 'warning'].includes(normalized)) return 'degraded';
  if (['down', 'error', 'unhealthy', 'fail'].includes(normalized)) return 'error';
  return 'error';
}

function monitorKindColor(kind) {
  if (kind === 'ok') return MONITOR_COLORS.ok;
  if (kind === 'degraded') return MONITOR_COLORS.degraded;
  return MONITOR_COLORS.error;
}

function setMonitorIndicator(dotId, valueId, rawValue) {
  const dot = document.getElementById(dotId);
  const value = document.getElementById(valueId);
  if (!dot || !value) return;
  const kind = monitorStatusKind(rawValue);
  const color = monitorKindColor(kind);
  const text = kind === 'ok' ? 'UP' : (kind === 'degraded' ? 'DEGRADED' : 'DOWN');
  dot.style.background = color;
  dot.style.boxShadow = `0 0 10px ${color}`;
  value.textContent = text;
  value.style.color = color;
}

function setMonitorHealthValue(rawValue) {
  const value = document.getElementById('monitor-health-value');
  if (!value) return;
  const kind = monitorStatusKind(rawValue);
  const color = monitorKindColor(kind);
  const text = kind === 'ok' ? 'healthy' : (kind === 'degraded' ? 'degraded' : 'unhealthy');
  value.textContent = text;
  value.style.color = color;
}

function updateMonitorHistoryTable(historyList) {
  const body = document.getElementById('monitor-history-body');
  if (!body) return;
  if (!Array.isArray(historyList) || !historyList.length) {
    body.innerHTML = `<tr><td colspan="5" style="padding:12px;color:${MONITOR_COLORS.muted};text-align:center;">No history found.</td></tr>`;
    return;
  }

  body.innerHTML = historyList.map((item) => {
    const query = String(item.query || '-');
    const filename = String(item.filename || '-');
    const date = item.date ? new Date(item.date).toLocaleString() : '-';
    const paperCount = item.paperCount != null ? String(item.paperCount) : '-';
    const sizeKB = item.sizeKB != null ? String(item.sizeKB) : '-';
    return '<tr>' +
      `<td style="padding:10px;border-bottom:1px solid ${MONITOR_COLORS.border};color:${MONITOR_COLORS.text};">${filename}</td>` +
      `<td style="padding:10px;border-bottom:1px solid ${MONITOR_COLORS.border};color:${MONITOR_COLORS.text};">${query}</td>` +
      `<td style="padding:10px;border-bottom:1px solid ${MONITOR_COLORS.border};color:${MONITOR_COLORS.text};">${date}</td>` +
      `<td style="padding:10px;border-bottom:1px solid ${MONITOR_COLORS.border};color:${MONITOR_COLORS.text};text-align:right;">${paperCount}</td>` +
      `<td style="padding:10px;border-bottom:1px solid ${MONITOR_COLORS.border};color:${MONITOR_COLORS.text};text-align:right;">${sizeKB}</td>` +
      '</tr>';
  }).join('');
}

function setMonitorLastUpdateText(text) {
  const stamp = document.getElementById('monitor-last-updated');
  if (!stamp) return;
  stamp.textContent = text;
}

export async function refreshMonitorStatus() {
  try {
    const [status, health, history] = await Promise.all([
      fetchJson('/api/monitor/status'),
      fetchJson('/api/monitor/health'),
      fetchJson('/api/monitor/history'),
    ]);

    setMonitorIndicator('monitor-copilot-dot', 'monitor-copilot-value', status.copilotApi);
    setMonitorIndicator('monitor-db-dot', 'monitor-db-value', status.db);
    setMonitorHealthValue(health.status);

    const uptimeValue = document.getElementById('monitor-uptime-value');
    if (uptimeValue) uptimeValue.textContent = formatUptimeToClock(status.uptime);

    updateMonitorHistoryTable(history);
    const ts = status.timestamp || new Date().toISOString();
    setMonitorLastUpdateText(`Last updated: ${new Date(ts).toLocaleString()}`);
  } catch (error) {
    setMonitorLastUpdateText('Monitor refresh failed');
    updateMonitorHistoryTable([]);
    setMonitorHealthValue('unhealthy');
    setMonitorIndicator('monitor-copilot-dot', 'monitor-copilot-value', false);
    setMonitorIndicator('monitor-db-dot', 'monitor-db-value', false);
    const uptimeValue = document.getElementById('monitor-uptime-value');
    if (uptimeValue) uptimeValue.textContent = '--:--:--';
    showToast(error?.message || 'Failed to refresh monitor');
  }
}

function stopMonitorAutoRefresh() {
  if (monitorRefreshIntervalId) {
    clearInterval(monitorRefreshIntervalId);
    monitorRefreshIntervalId = null;
  }
}

function startMonitorAutoRefresh() {
  refreshMonitorStatus().catch(() => {});
  if (monitorRefreshIntervalId) return;
  monitorRefreshIntervalId = setInterval(() => {
    refreshMonitorStatus().catch(() => {});
  }, 10000);
}

function initializeMonitorTabUI() {
  const container = document.getElementById('monitor-view');
  if (!container) return;
  if (container.dataset.monitorReady === '1') return;
  container.dataset.monitorReady = '1';

  const styleId = 'monitor-inline-style';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent =
      '#monitor-view .monitor-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:18px;}' +
      `#monitor-view .monitor-card{background:linear-gradient(180deg,${MONITOR_COLORS.cardA}, ${MONITOR_COLORS.cardB});border:1px solid ${MONITOR_COLORS.border};border-radius:12px;padding:14px;}` +
      `#monitor-view .monitor-card-title{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:${MONITOR_COLORS.muted};margin-bottom:8px;}` +
      `#monitor-view .monitor-card-value{font-size:22px;font-weight:700;color:${MONITOR_COLORS.text};display:flex;align-items:center;gap:8px;}` +
      '#monitor-view .monitor-dot{width:10px;height:10px;border-radius:999px;display:inline-block;}' +
      `#monitor-view .monitor-history-wrap{background:linear-gradient(180deg,${MONITOR_COLORS.cardA}, ${MONITOR_COLORS.cardB});border:1px solid ${MONITOR_COLORS.border};border-radius:12px;padding:14px;overflow:auto;}` +
      `#monitor-view .monitor-history-title{font-size:15px;font-weight:600;color:${MONITOR_COLORS.text};margin-bottom:10px;}` +
      '#monitor-view .monitor-history-table{width:100%;border-collapse:collapse;min-width:680px;}' +
      `#monitor-view .monitor-history-table th{padding:10px;text-align:left;color:${MONITOR_COLORS.muted};font-size:12px;text-transform:uppercase;border-bottom:1px solid ${MONITOR_COLORS.border};}` +
      `#monitor-view .monitor-meta{margin:10px 2px 0;color:${MONITOR_COLORS.muted};font-size:12px;}`;
    document.head.appendChild(style);
  }

  container.innerHTML =
    '<section style="padding:18px 0;">' +
      '<div class="monitor-grid">' +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Copilot API</div>' +
          `<div class="monitor-card-value"><span id="monitor-copilot-dot" class="monitor-dot" style="background:${MONITOR_COLORS.error};"></span><span id="monitor-copilot-value">DOWN</span></div>` +
        '</article>' +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Database</div>' +
          `<div class="monitor-card-value"><span id="monitor-db-dot" class="monitor-dot" style="background:${MONITOR_COLORS.error};"></span><span id="monitor-db-value">DOWN</span></div>` +
        '</article>' +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Health</div>' +
          `<div id="monitor-health-value" class="monitor-card-value" style="color:${MONITOR_COLORS.error};">unhealthy</div>` +
        '</article>' +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Uptime</div>' +
          '<div id="monitor-uptime-value" class="monitor-card-value">00:00:00</div>' +
        '</article>' +
      '</div>' +
      '<section class="monitor-history-wrap">' +
        '<div class="monitor-history-title">Pipeline History</div>' +
        '<table class="monitor-history-table">' +
          '<thead><tr><th>Filename</th><th>Query</th><th>Date</th><th>Papers</th><th>Size (KB)</th></tr></thead>' +
          `<tbody id="monitor-history-body"><tr><td colspan="5" style="padding:12px;color:${MONITOR_COLORS.muted};text-align:center;">Loading...</td></tr></tbody>` +
        '</table>' +
        '<div id="monitor-last-updated" class="monitor-meta">Last updated: --</div>' +
      '</section>' +
    '</section>';
}

export async function init() {
  if (monitorBindingsApplied) return;
  monitorBindingsApplied = true;
  initializeMonitorTabUI();
}

export async function onActivate() {
  initializeMonitorTabUI();
  startMonitorAutoRefresh();
}

export async function onDeactivate() {
  stopMonitorAutoRefresh();
}
