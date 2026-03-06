import { escapeHtml, fetchJson, fetchPipelineResultFile, showToast } from './utils.js';

const dashboardState = {
  loading: false,
};

function setDashboardStatValue(elementId, value, title) {
  const element = document.getElementById(elementId);
  if (!element) return;
  element.textContent = value;
  if (title) {
    element.title = title;
  } else {
    element.removeAttribute('title');
  }
}

function formatDashboardHealthKey(key) {
  return String(key || '')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function dashboardHealthClass(value) {
  if (value === true) return 'health-ok';
  if (value === false || value == null) return 'health-err';
  const normalized = String(value).trim().toLowerCase();
  if (['ok', 'online', 'up', 'healthy', 'true'].includes(normalized)) return 'health-ok';
  if (['error', 'offline', 'down', 'false', 'unhealthy'].includes(normalized)) return 'health-err';
  return '';
}

function renderDashboardHealth(status) {
  const container = document.getElementById('system-health');
  if (!container) return;
  if (!status || typeof status !== 'object') {
    container.innerHTML = '<div class="health-row"><span class="health-key">Status</span><span class="health-val health-err">Unavailable</span></div>';
    return;
  }

  const rows = ['<div class="health-row"><span class="health-key">Status</span><span class="health-val health-ok">Online</span></div>'];
  Object.keys(status).forEach((key) => {
    const rawValue = status[key];
    const renderedValue = rawValue && typeof rawValue === 'object' ? JSON.stringify(rawValue) : rawValue;
    rows.push(
      '<div class="health-row">' +
        `<span class="health-key">${escapeHtml(formatDashboardHealthKey(key))}</span>` +
        `<span class="health-val ${dashboardHealthClass(rawValue)}">${escapeHtml(String(renderedValue))}</span>` +
      '</div>',
    );
  });

  container.innerHTML = rows.join('');
}

function formatDashboardDigestDate(rawDate) {
  if (!rawDate) return '--';
  const parsed = new Date(rawDate);
  if (Number.isNaN(parsed.getTime())) return String(rawDate).slice(0, 10);
  return parsed.toISOString().slice(0, 10);
}

function renderRecentDigests(items) {
  const container = document.getElementById('recent-digests');
  if (!container) return;
  if (!Array.isArray(items) || !items.length) {
    container.innerHTML = '<div class="digest-timeline-item"><span class="digest-date">--</span><span class="digest-info">No digests yet</span></div>';
    return;
  }

  container.innerHTML = items.slice(0, 5).map((item) => {
    const filename = String(item.filename || '').trim();
    const reportName = filename ? filename.replace(/\.json$/i, '.md') : filename;
    const totalPapers = Number(item.totalPapers ?? item.paperCount ?? 0);
    const info = Number.isFinite(totalPapers) ? `${totalPapers} papers` : 'Digest report';
    const link = reportName
      ? `<a href="/api/digest/report/${encodeURIComponent(reportName)}" target="_blank" class="btn-gold btn-sm">View</a>`
      : '';
    return '<div class="digest-timeline-item">' +
      `<span class="digest-date">${escapeHtml(formatDashboardDigestDate(item.date))}</span>` +
      `<span class="digest-info">${escapeHtml(info)}</span>` +
      link +
      '</div>';
  }).join('');
}

function inferDashboardPaperCount(status) {
  if (!status || typeof status !== 'object') return null;
  for (const key of Object.keys(status)) {
    if (!key.toLowerCase().includes('paper')) continue;
    const parsed = Number(status[key]);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

function buildDashboardPaperKey(paper) {
  if (!paper || typeof paper !== 'object') return '';
  return String(paper.doi || paper.pmid || paper.title || paper.id || '').trim().toLowerCase();
}

async function resolveDashboardPaperCount(historyItems) {
  if (!Array.isArray(historyItems) || !historyItems.length) return null;
  const uniquePapers = new Set();
  const results = await Promise.allSettled(historyItems.map((item) => {
    if (!item || !item.filename) return Promise.resolve(null);
    return fetchPipelineResultFile(`data/${item.filename}`);
  }));

  results.forEach((result) => {
    if (result.status !== 'fulfilled' || !result.value || !Array.isArray(result.value.papers)) return;
    result.value.papers.forEach((paper) => {
      const key = buildDashboardPaperKey(paper);
      if (key) uniquePapers.add(key);
    });
  });

  return uniquePapers.size || null;
}

export async function loadDashboard() {
  if (dashboardState.loading) return;
  dashboardState.loading = true;

  try {
    const results = await Promise.allSettled([
      fetchJson('/api/monitor/status'),
      fetchJson('/api/sessions'),
      fetchJson('/api/memory/facts'),
      fetchJson('/api/digest/history'),
      fetchJson('/api/pipeline/history'),
    ]);

    const statusResult = results[0].status === 'fulfilled' ? results[0].value : null;
    const sessionsResult = results[1].status === 'fulfilled' && Array.isArray(results[1].value) ? results[1].value : null;
    const factsResult = results[2].status === 'fulfilled' && Array.isArray(results[2].value) ? results[2].value : null;
    const digestsResult = results[3].status === 'fulfilled' && Array.isArray(results[3].value) ? results[3].value : null;
    const pipelineHistoryResult = results[4].status === 'fulfilled' && Array.isArray(results[4].value) ? results[4].value : null;

    renderDashboardHealth(statusResult);
    renderRecentDigests(digestsResult || []);
    setDashboardStatValue('stat-sessions-count', sessionsResult ? String(sessionsResult.length) : '-');
    setDashboardStatValue('stat-facts-count', factsResult ? String(factsResult.length) : '-');
    setDashboardStatValue('stat-digests-count', digestsResult ? String(digestsResult.length) : '-');

    let paperCount = inferDashboardPaperCount(statusResult);
    if (!Number.isFinite(paperCount)) {
      try {
        paperCount = await resolveDashboardPaperCount(pipelineHistoryResult || []);
      } catch {
        paperCount = null;
      }
    }

    if (Number.isFinite(paperCount)) {
      setDashboardStatValue('stat-papers-count', String(paperCount));
    } else {
      setDashboardStatValue('stat-papers-count', '-', 'Run a pipeline to populate');
    }
  } catch (error) {
    showToast(error.message || 'Failed to load dashboard', 'error');
  } finally {
    dashboardState.loading = false;
  }
}

export async function init() {
  await loadDashboard();
}

export async function onActivate() {
  await loadDashboard();
}
