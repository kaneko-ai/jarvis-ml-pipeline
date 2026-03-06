/* global Chart */

import { escapeHtml, fetchJson, fetchPipelineResultFile, showToast } from './utils.js';

const dashboardState = {
  loading: false,
};

let chartInstances = {};

function destroyCharts() {
  for (const key of Object.keys(chartInstances)) {
    chartInstances[key]?.destroy();
    delete chartInstances[key];
  }
}

function getChartColors(count) {
  const palette = [
    '#d4af37', '#4caf50', '#2196f3', '#ff9800', '#e91e63',
    '#9c27b0', '#00bcd4', '#ff5722', '#8bc34a', '#3f51b5',
    '#ffc107', '#607d8b', '#795548', '#cddc39', '#f44336',
  ];
  return Array.from({ length: count }, (_, i) => palette[i % palette.length]);
}

function getThemeColors() {
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  return {
    text: isDark ? '#e0e0e0' : '#333333',
    grid: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.08)',
    bg: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
  };
}

function renderBarChart(canvasId, data, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data || typeof Chart === 'undefined') return;
  const labels = Object.keys(data).sort();
  const values = labels.map((k) => data[k]);
  const colors = getChartColors(labels.length);
  const theme = getThemeColors();

  chartInstances[canvasId] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: label || 'Count',
        data: values,
        backgroundColor: colors.map((c) => c + '99'),
        borderColor: colors,
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { ticks: { color: theme.text, maxRotation: 45 }, grid: { color: theme.grid } },
        y: { ticks: { color: theme.text }, grid: { color: theme.grid }, beginAtZero: true },
      },
    },
  });
}

function renderDoughnutChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data || typeof Chart === 'undefined') return;
  const labels = Object.keys(data);
  const values = labels.map((k) => data[k]);
  const colors = getChartColors(labels.length);
  const theme = getThemeColors();

  chartInstances[canvasId] = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors.map((c) => c + 'cc'),
        borderColor: colors,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: theme.text, font: { size: 11 } },
        },
      },
    },
  });
}

function renderHorizontalBarChart(canvasId, data, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data || typeof Chart === 'undefined') return;
  const labels = Object.keys(data);
  const values = labels.map((k) => data[k]);
  const colors = getChartColors(labels.length);
  const theme = getThemeColors();

  chartInstances[canvasId] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: label || 'Count',
        data: values,
        backgroundColor: colors.map((c) => c + '99'),
        borderColor: colors,
        borderWidth: 1,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: theme.text }, grid: { color: theme.grid }, beginAtZero: true },
        y: { ticks: { color: theme.text, font: { size: 10 } }, grid: { color: theme.grid } },
      },
    },
  });
}

async function loadCharts() {
  try {
    const res = await fetch('/api/papers/stats');
    if (!res.ok) return;
    const stats = await res.json();

    destroyCharts();
    renderBarChart('chart-by-year', stats.byYear, 'Papers');
    renderDoughnutChart('chart-by-source', stats.bySource);
    renderBarChart('chart-by-keyword', stats.byKeyword, 'Papers');
    renderHorizontalBarChart('chart-by-journal', stats.topJournals, 'Papers');
  } catch (e) {
    console.warn('[Dashboard] Charts failed:', e.message);
  }
}

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

    try {
      const [statsRes, itemsRes] = await Promise.all([
        fetch('/api/reading-list/stats'),
        fetch('/api/reading-list?status=unread&limit=5'),
      ]);
      const readingStats = await statsRes.json();
      const readingItems = await itemsRes.json();

      const statsEl = document.getElementById('reading-stats');
      if (statsEl && readingStats) {
        statsEl.innerHTML =
          `<span class="reading-stat">📖 Unread: <strong>${readingStats.unread || 0}</strong></span>` +
          `<span class="reading-stat">📚 Reading: <strong>${readingStats.reading || 0}</strong></span>` +
          `<span class="reading-stat">✅ Done: <strong>${readingStats.done || 0}</strong></span>`;
      }

      const itemsEl = document.getElementById('reading-items');
      if (itemsEl) {
        if (Array.isArray(readingItems) && readingItems.length > 0) {
          itemsEl.innerHTML = readingItems.map((item) =>
            `<div class="reading-item">` +
              `<span class="reading-item-title">${escapeHtml(item.title || 'Untitled')}</span>` +
              `<span class="reading-item-meta">${escapeHtml([item.authors, item.year].filter(Boolean).join(', '))}</span>` +
            `</div>`
          ).join('');
        } else {
          itemsEl.innerHTML = '<p class="pipeline-empty-row">No papers in reading list.</p>';
        }
      }
    } catch (e) {
      console.warn('[Dashboard] Reading list load failed:', e.message);
    }
  } catch (error) {
    showToast(error.message || 'Failed to load dashboard', 'error');
  } finally {
    dashboardState.loading = false;
  }
}

export async function init() {
  await loadDashboard();
  await loadCharts();
}

export async function onActivate() {
  await loadDashboard();
  await loadCharts();
}

