import { buildDoiLink, escapeHtml, fetchJson, fetchPipelineResultFile, formatElapsedTime, showNotification, showToast } from './utils.js';

const PIPELINE_TOTAL_STEPS = 7;
const PIPELINE_PROGRESS_STEPS = ['Search', 'Fetch', 'Score', 'Summarize', 'Store', 'Archive', 'Export'];
const pipelineState = {
  eventSource: null,
  running: false,
  historyLoaded: false,
  startedAt: 0,
  storedCount: 0,
  archivedCount: 0,
  bound: false,
};

const digestState = {
  eventSource: null,
  running: false,
  historyLoaded: false,
};

const pipelineStepDefaults = [
  'Waiting for search start...',
  'Waiting for deduplication...',
  'Waiting for relevance scoring...',
  'Waiting for ranking...',
  'Waiting for Gemini summarization...',
  'Waiting for output formatting...',
  'Waiting for file save...',
];

function getPipelineStepCards() {
  return Array.from(document.querySelectorAll('.pipeline-step-card'));
}

function getPipelineProgressSteps() {
  return Array.from(document.querySelectorAll('.pipeline-progress .pipeline-step'));
}

function clampNumber(value, min, max) {
  return Math.min(Math.max(Number(value) || 0, min), max);
}

function setPipelineRunButtonState(running) {
  const button = document.getElementById('pipeline-run-btn');
  if (!button) return;
  button.disabled = Boolean(running);
  button.textContent = running ? 'Running...' : 'Run Pipeline';
}

function setPipelineStatusMessage(message, type) {
  const status = document.getElementById('pipeline-status-message');
  if (!status) return;
  status.classList.remove('error', 'success');
  if (type) status.classList.add(type);
  status.textContent = message || '';
}

function renderPipelineEmptyResults(message) {
  const body = document.getElementById('pipeline-results-body');
  if (!body) return;
  const table = body.closest('.pipeline-results-table');
  if (table) table.classList.remove('pipeline-results-table-rich');
  body.innerHTML = `<tr><td colspan="5" class="pipeline-empty-row">${escapeHtml(message || 'No results yet.')}</td></tr>`;
}

function ensurePipelineProgressBar() {
  const shell = document.querySelector('.pipeline-shell');
  const status = document.getElementById('pipeline-status-message');
  if (!shell || !status) return null;

  const existing = document.getElementById('pipeline-progress');
  if (existing) return existing;

  const progress = document.createElement('div');
  progress.id = 'pipeline-progress';
  progress.className = 'pipeline-progress';
  progress.setAttribute('aria-label', 'Pipeline Progress Overview');

  for (let index = 0; index < PIPELINE_PROGRESS_STEPS.length; index += 1) {
    const step = document.createElement('div');
    step.className = 'pipeline-step';
    step.dataset.step = String(index + 1);
    step.innerHTML = `<span class="step-num">${index + 1}</span><span class="step-label">${escapeHtml(PIPELINE_PROGRESS_STEPS[index])}</span>`;
    progress.appendChild(step);
  }

  if (status.nextSibling) {
    shell.insertBefore(progress, status.nextSibling);
  } else {
    shell.appendChild(progress);
  }
  return progress;
}

function resetPipelineSteps() {
  const cards = getPipelineStepCards();
  cards.forEach((card, index) => {
    card.classList.remove('active', 'completed');
    const messageElement = card.querySelector('[data-step-message]');
    if (messageElement) messageElement.textContent = pipelineStepDefaults[index] || 'Waiting for progress...';
    const fillElement = card.querySelector('[data-step-fill]');
    if (fillElement) fillElement.style.width = '0%';
    const percentElement = card.querySelector('[data-step-percent]');
    if (percentElement) percentElement.textContent = '0%';
  });
  getPipelineProgressSteps().forEach((step) => step.classList.remove('active', 'completed'));
}

function deriveStepLocalProgress(step, globalProgress) {
  const current = clampNumber(step, 1, PIPELINE_TOTAL_STEPS);
  const progress = clampNumber(globalProgress, 0, 100);
  const start = ((current - 1) / PIPELINE_TOTAL_STEPS) * 100;
  const end = (current / PIPELINE_TOTAL_STEPS) * 100;
  if (progress <= start) return 0;
  if (progress >= end) return 100;
  return clampNumber(((progress - start) / (end - start)) * 100, 0, 100);
}

function inferPipelineProgressStep(step, message) {
  const text = String(message || '').toLowerCase();
  if (text.includes('saving result file') || text.includes('pipeline completed')) return 7;
  if (text.includes('archiv')) return 6;
  if (text.includes('database') || text.includes('structured json') || text.includes('formatting')) return 5;
  if (text.includes('summar') || text.includes('gemini')) return 4;
  if (text.includes('score') || text.includes('ranking') || text.includes('selected')) return 3;
  if (text.includes('dedup') || text.includes('fetch')) return 2;
  if (text.includes('search')) return 1;

  const numericStep = clampNumber(step, 1, PIPELINE_TOTAL_STEPS);
  if (numericStep <= 3) return numericStep;
  if (numericStep === 4) return 3;
  if (numericStep === 5) return 4;
  if (numericStep === 6) return 5;
  return 7;
}

function updatePipelineSteps(step, progress, message) {
  const currentStep = clampNumber(step, 1, PIPELINE_TOTAL_STEPS);
  const safeProgress = clampNumber(progress, 0, 100);
  const cards = getPipelineStepCards();

  cards.forEach((card, index) => {
    const cardStep = index + 1;
    const fillElement = card.querySelector('[data-step-fill]');
    const percentElement = card.querySelector('[data-step-percent]');

    card.classList.toggle('active', cardStep === currentStep && safeProgress < 100);
    card.classList.toggle('completed', cardStep < currentStep);

    let stepProgress = 0;
    if (cardStep < currentStep) {
      stepProgress = 100;
    } else if (cardStep === currentStep) {
      stepProgress = deriveStepLocalProgress(currentStep, safeProgress);
      if (safeProgress >= 100) {
        card.classList.remove('active');
        card.classList.add('completed');
        stepProgress = 100;
      }
    }

    if (fillElement) fillElement.style.width = `${stepProgress.toFixed(1)}%`;
    if (percentElement) percentElement.textContent = `${Math.round(stepProgress)}%`;
  });

  const activeCard = document.querySelector(`.pipeline-step-card[data-step="${currentStep}"]`);
  if (activeCard) {
    const messageElement = activeCard.querySelector('[data-step-message]');
    if (messageElement && message) messageElement.textContent = message;
  }

  const visualStep = inferPipelineProgressStep(currentStep, message);
  getPipelineProgressSteps().forEach((progressStep, index) => {
    const progressIndex = index + 1;
    progressStep.classList.toggle('completed', progressIndex < visualStep || (visualStep === PIPELINE_TOTAL_STEPS && safeProgress >= 100));
    progressStep.classList.toggle('active', progressIndex === visualStep && !(visualStep === PIPELINE_TOTAL_STEPS && safeProgress >= 100));
  });
}

function normalizePipelineUrl(rawUrl) {
  if (!rawUrl) return '';
  const text = String(rawUrl).trim();
  if (!text) return '';
  if (text.startsWith('http://') || text.startsWith('https://')) return text;
  if (text.startsWith('10.')) return `https://doi.org/${text}`;
  return '';
}

function normalizePipelineAuthors(rawAuthors) {
  if (Array.isArray(rawAuthors)) return rawAuthors.join(', ');
  if (rawAuthors === null || rawAuthors === undefined) return '-';
  const text = String(rawAuthors).trim();
  return text || '-';
}

function normalizePipelineScore(rawScore) {
  if (!Number.isFinite(Number(rawScore))) return '-';
  return Number(rawScore).toFixed(1);
}

function formatPipelineDuration() {
  if (!pipelineState.startedAt) return '-';
  return formatElapsedTime(Date.now() - pipelineState.startedAt);
}

function buildPipelineResultMeta(paper) {
  const journal = paper.journal ? String(paper.journal).trim() : '';
  const year = paper.year ? String(paper.year).trim() : '';
  if (journal && year) return `${journal}, ${year}`;
  return journal || year || (paper.source ? String(paper.source) : '-');
}

function getPipelinePaperExcerpt(paper) {
  const value = paper.abstract || paper.summary || '';
  const text = String(value || '').trim();
  if (!text) return 'No abstract available.';
  return text.length > 320 ? `${text.slice(0, 317)}...` : text;
}

function buildPipelinePaperLink(paper) {
  if (paper.doi) return buildDoiLink(paper.doi);
  const url = normalizePipelineUrl(paper.url || paper.link);
  if (!url) return '';
  return `<a href="${escapeHtml(url)}" class="cite-link" target="_blank" rel="noopener noreferrer">Open</a>`;
}

function buildPipelineSummary(papers) {
  const foundCount = Array.isArray(papers) ? papers.length : 0;
  const storedCount = pipelineState.storedCount || foundCount;
  return '<div class="pipeline-summary">' +
    `<span>Found <strong>${escapeHtml(String(foundCount))}</strong> papers</span>` +
    `<span>Stored <strong>${escapeHtml(String(storedCount))}</strong> to database</span>` +
    `<span>Duration: <strong>${escapeHtml(formatPipelineDuration())}</strong></span>` +
    '</div>';
}

function renderPipelineResults(papers) {
  const body = document.getElementById('pipeline-results-body');
  if (!body) return;
  body.innerHTML = '';

  const table = body.closest('.pipeline-results-table');
  if (table) table.classList.add('pipeline-results-table-rich');

  if (!Array.isArray(papers) || !papers.length) {
    renderPipelineEmptyResults('No papers returned by pipeline.');
    return;
  }

  const row = document.createElement('tr');
  const cell = document.createElement('td');
  cell.colSpan = 5;
  cell.className = 'pipeline-results-rich-cell';

  const wrapper = document.createElement('div');
  wrapper.className = 'pipeline-results-cards';
  for (const paper of papers) {
    const paperCard = document.createElement('div');
    paperCard.className = 'paper-card';
    paperCard.innerHTML =
      `<div class="paper-score">${escapeHtml(normalizePipelineScore(paper.score))}</div>` +
      '<div class="paper-content">' +
      `<h4 class="paper-title">${escapeHtml(paper.title ? String(paper.title) : '-')}</h4>` +
      `<p class="paper-authors">${escapeHtml(normalizePipelineAuthors(paper.authors))}</p>` +
      `<p class="paper-journal">${escapeHtml(buildPipelineResultMeta(paper))}</p>` +
      `<p class="paper-abstract">${escapeHtml(getPipelinePaperExcerpt(paper))}</p>` +
      '<div class="paper-links">' +
      (buildPipelinePaperLink(paper) || '') +
      `<span class="paper-source">${escapeHtml(String(paper.source || 'Pipeline'))}</span>` +
      '</div></div>';
    wrapper.appendChild(paperCard);
  }

  cell.appendChild(wrapper);
  const summaryHost = document.createElement('div');
  summaryHost.innerHTML = buildPipelineSummary(papers);
  if (summaryHost.firstChild) cell.appendChild(summaryHost.firstChild);
  row.appendChild(cell);
  body.appendChild(row);
}

function updatePipelineDerivedState(payload) {
  if (!payload?.message) return;
  const message = String(payload.message);
  const storedMatch = message.match(/Saved\s+(\d+)\s+papers?\s+to\s+database/i);
  if (storedMatch) pipelineState.storedCount = Number(storedMatch[1]) || pipelineState.storedCount;
  const archivedMatch = message.match(/Archived\s+(\d+)\s+PDFs?/i);
  if (archivedMatch) pipelineState.archivedCount = Number(archivedMatch[1]) || pipelineState.archivedCount;
}

function formatPipelineHistoryDate(rawDate) {
  if (!rawDate) return '--';
  const parsed = new Date(rawDate);
  if (Number.isNaN(parsed.getTime())) return String(rawDate);
  return parsed.toLocaleString('ja-JP');
}

function renderPipelineHistory(items) {
  const list = document.getElementById('pipeline-history-list');
  if (!list) return;
  if (!Array.isArray(items) || !items.length) {
    list.innerHTML = '<li class="pipeline-empty-row">No history yet.</li>';
    return;
  }
  list.innerHTML = items.map((item) => {
    return '<li class="pipeline-history-item">' +
      `<div><div class="pipeline-history-query">${escapeHtml(item.query || '(unknown query)')}</div>` +
      `<div class="pipeline-history-meta">${escapeHtml(formatPipelineHistoryDate(item.date))}</div></div>` +
      `<div class="pipeline-history-meta">Papers: ${escapeHtml(String(item.paperCount ?? '-'))}</div>` +
      '</li>';
  }).join('');
}

async function loadPipelineHistory(force = false) {
  if (pipelineState.historyLoaded && !force) return;
  try {
    const history = await fetchJson('/api/pipeline/history');
    renderPipelineHistory(history);
    pipelineState.historyLoaded = true;
  } catch (error) {
    renderPipelineHistory([]);
    setPipelineStatusMessage(`Failed to load history: ${error.message}`, 'error');
  }
}

function stopPipelineStream() {
  if (pipelineState.eventSource) {
    pipelineState.eventSource.close();
    pipelineState.eventSource = null;
  }
  pipelineState.running = false;
  setPipelineRunButtonState(false);
}

async function refreshDashboard() {
  try {
    const mod = await import('./dashboard.js');
    await mod.loadDashboard?.();
  } catch {
  }
}

async function handlePipelineMessage(payload, sourceRef) {
  if (pipelineState.eventSource !== sourceRef) return;

  if (payload.error) {
    setPipelineStatusMessage(`Pipeline error: ${payload.error}`, 'error');
    showToast(`Pipeline error: ${payload.error}`, 'error');
    stopPipelineStream();
    return;
  }

  if (payload.done) {
    updatePipelineSteps(PIPELINE_TOTAL_STEPS, 100, 'Pipeline completed.');
    const summary = `Completed: ${String(payload.paperCount ?? 0)} papers`;
    setPipelineStatusMessage(summary, 'success');

    let rendered = false;
    if (payload.file) {
      try {
        const resultFile = await fetchPipelineResultFile(payload.file);
        renderPipelineResults(resultFile.papers || []);
        rendered = true;
      } catch {
        renderPipelineEmptyResults('Completed, but failed to load results file.');
        setPipelineStatusMessage(`${summary} (result fetch failed)`, 'error');
      }
    }

    if (!rendered && payload.results && Array.isArray(payload.results.papers)) {
      renderPipelineResults(payload.results.papers || []);
      rendered = true;
    }
    if (!rendered) {
      renderPipelineEmptyResults('Completed. Result details are not available from API response.');
    }

    pipelineState.historyLoaded = false;
    await loadPipelineHistory(true);
    refreshDashboard();
    showNotification('Pipeline Complete', { body: 'Research pipeline has finished.', tag: 'jarvis-pipeline' });
    showToast('Pipeline completed!', 'success');
    stopPipelineStream();
    return;
  }

  if (typeof payload.step === 'number') {
    updatePipelineDerivedState(payload);
    updatePipelineSteps(payload.step, payload.progress, payload.message || 'Running...');
    setPipelineStatusMessage(payload.message || `Step ${payload.step} in progress`);
  }
}

function runPipelineQuery(query) {
  const trimmedQuery = String(query || '').trim();
  if (!trimmedQuery || pipelineState.running) return;

  stopPipelineStream();
  pipelineState.running = true;
  pipelineState.startedAt = Date.now();
  pipelineState.storedCount = 0;
  pipelineState.archivedCount = 0;
  setPipelineRunButtonState(true);
  ensurePipelineProgressBar();
  resetPipelineSteps();
  renderPipelineEmptyResults('Pipeline running...');
  setPipelineStatusMessage(`Running pipeline for: ${trimmedQuery}`);

  const streamUrl = `/api/pipeline/run?query=${encodeURIComponent(trimmedQuery)}&limit=50`;
  const eventSource = new EventSource(streamUrl);
  pipelineState.eventSource = eventSource;

  eventSource.onmessage = (event) => {
    if (pipelineState.eventSource !== eventSource) return;
    try {
      const payload = JSON.parse(event.data);
      Promise.resolve(handlePipelineMessage(payload, eventSource)).catch((error) => {
        setPipelineStatusMessage(`Pipeline error: ${error.message}`, 'error');
        showToast(`Pipeline error: ${error.message}`, 'error');
        stopPipelineStream();
      });
    } catch {
      setPipelineStatusMessage('Invalid stream payload', 'error');
      showToast('Pipeline error: Invalid stream payload', 'error');
      stopPipelineStream();
    }
  };

  eventSource.onerror = () => {
    if (pipelineState.eventSource !== eventSource) return;
    setPipelineStatusMessage('Pipeline stream disconnected.', 'error');
    showToast('Pipeline stream disconnected.', 'error');
    stopPipelineStream();
  };
}

function setDigestRunButtonState(running) {
  const button = document.getElementById('digest-run-btn');
  if (!button) return;
  button.disabled = Boolean(running);
  button.textContent = running ? 'Running...' : 'Run Daily Digest';
}

function setDigestStatusMessage(message, type) {
  const element = document.getElementById('digest-status-message');
  if (!element) return;
  element.classList.remove('error', 'success');
  if (type) element.classList.add(type);
  element.textContent = message || '';
}

function normalizeDigestUrl(rawUrl) {
  if (!rawUrl) return '';
  const url = String(rawUrl).trim();
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  if (url.startsWith('10.')) return `https://doi.org/${url}`;
  return '';
}

function parseDigestKeywordStats(summary) {
  if (!summary || typeof summary !== 'object') return [];
  if (Array.isArray(summary.keywordStats)) {
    return summary.keywordStats.map((entry) => {
      if (!entry || typeof entry !== 'object') return null;
      const keyword = String(entry.keyword || entry.term || '').trim();
      if (!keyword) return null;
      const count = Number(entry.count ?? entry.paperCount ?? 0);
      return { keyword, count: Number.isFinite(count) ? count : 0 };
    }).filter(Boolean);
  }
  if (summary.keywordStats && typeof summary.keywordStats === 'object') {
    return Object.entries(summary.keywordStats).map(([keyword, count]) => ({
      keyword: String(keyword || '').trim(),
      count: Number.isFinite(Number(count)) ? Number(count) : 0,
    }));
  }
  return [];
}

function parseDigestTopPapers(summary, result) {
  let source = [];
  if (summary && Array.isArray(summary.topPapers)) source = summary.topPapers;
  else if (result && Array.isArray(result.topPapers)) source = result.topPapers;
  else if (result && Array.isArray(result.papers)) source = result.papers;
  else if (result && Array.isArray(result.results)) source = result.results;

  return source.map((paper) => {
    if (!paper || typeof paper !== 'object') return null;
    const title = String(paper.title || paper.paperTitle || '').trim();
    if (!title) return null;
    return {
      title,
      keyword: String(paper.keyword || paper.term || '').trim(),
      source: String(paper.source || paper.journal || '').trim(),
      year: Number(paper.year) || null,
      score: Number(paper.score) || null,
      url: normalizeDigestUrl(paper.url || paper.link || paper.doi),
    };
  }).filter(Boolean).slice(0, 10);
}

function renderDigestKeywordStats(summary) {
  const container = document.getElementById('digest-results-keywords');
  if (!container) return;
  const stats = parseDigestKeywordStats(summary);
  if (!stats.length) {
    container.innerHTML = '';
    return;
  }
  container.innerHTML = stats.map((entry) => `<span class="digest-keyword-chip">${escapeHtml(entry.keyword)}: ${escapeHtml(String(entry.count))}</span>`).join('');
}

function renderDigestTopPapers(summary, result) {
  const list = document.getElementById('digest-top-papers-list');
  if (!list) return;
  const papers = parseDigestTopPapers(summary, result);
  if (!papers.length) {
    list.innerHTML = '<li class="pipeline-empty-row">Top papers will appear here.</li>';
    return;
  }

  list.innerHTML = papers.map((paper) => {
    const titleHtml = paper.url
      ? `<a class="digest-top-paper-title" target="_blank" rel="noopener noreferrer" href="${escapeHtml(paper.url)}">${escapeHtml(paper.title)}</a>`
      : `<span class="digest-top-paper-title">${escapeHtml(paper.title)}</span>`;
    const meta = [paper.keyword, paper.source, paper.year, paper.score ? `score ${paper.score.toFixed(1)}` : '']
      .filter(Boolean)
      .map((value) => escapeHtml(String(value)))
      .join(' | ');
    return `<li class="digest-top-paper-item">${titleHtml}<div class="digest-top-paper-meta">${meta || '-'}</div></li>`;
  }).join('');
}

function renderDigestSummary(summary, result) {
  const summaryElement = document.getElementById('digest-results-summary');
  if (!summaryElement) return;

  const safeSummary = summary && typeof summary === 'object' ? summary : {};
  const keywordCount = Number(safeSummary.keywordCount ?? parseDigestKeywordStats(safeSummary).length ?? 0);
  const totalPapers = Number(safeSummary.totalPapers ?? safeSummary.total_papers ?? (Array.isArray(result?.papers) ? result.papers.length : 0));
  summaryElement.textContent = `Keywords: ${Number.isFinite(keywordCount) ? keywordCount : 0} | Total papers: ${Number.isFinite(totalPapers) ? totalPapers : 0}`;
  renderDigestKeywordStats(safeSummary);
  renderDigestTopPapers(safeSummary, result);
}

function formatDigestHistoryDate(rawDate) {
  if (!rawDate) return '--';
  const parsed = new Date(rawDate);
  if (Number.isNaN(parsed.getTime())) return String(rawDate);
  return parsed.toLocaleString('ja-JP');
}

function renderDigestHistory(items) {
  const body = document.getElementById('digest-history-body');
  if (!body) return;
  if (!Array.isArray(items) || !items.length) {
    body.innerHTML = '<tr><td colspan="5" class="pipeline-empty-row">No digest history yet.</td></tr>';
    return;
  }
  body.innerHTML = items.map((item) => {
    const filename = String(item.filename || '').trim();
    return '<tr>' +
      `<td>${escapeHtml(formatDigestHistoryDate(item.date))}</td>` +
      `<td>${escapeHtml(String(item.keywordCount ?? '-'))}</td>` +
      `<td>${escapeHtml(String(item.totalPapers ?? '-'))}</td>` +
      `<td>${escapeHtml(String(item.sizeKB ?? '-'))}</td>` +
      `<td><button type="button" class="digest-history-link" data-digest-report="${encodeURIComponent(filename)}">Download</button></td>` +
      '</tr>';
  }).join('');
}

async function loadDigestHistory(force = false) {
  if (digestState.historyLoaded && !force) return;
  try {
    const history = await fetchJson('/api/digest/history');
    renderDigestHistory(history);
    digestState.historyLoaded = true;
  } catch (error) {
    renderDigestHistory([]);
    setDigestStatusMessage(`Failed to load digest history: ${error.message}`, 'error');
  }
}

function stopDigestStream() {
  if (digestState.eventSource) {
    digestState.eventSource.close();
    digestState.eventSource = null;
  }
  digestState.running = false;
  setDigestRunButtonState(false);
}

function buildDigestStreamUrl() {
  const keywordInput = document.getElementById('digest-keywords-input');
  const rawKeywords = keywordInput ? keywordInput.value.trim() : '';
  const query = rawKeywords ? `?keywords=${encodeURIComponent(rawKeywords)}` : '';
  return `/api/digest/run${query}`;
}

async function handleDigestPayload(payload, sourceRef) {
  if (digestState.eventSource !== sourceRef) return;

  if (payload.error) {
    setDigestStatusMessage(`Digest error: ${payload.error}`, 'error');
    showToast(`Digest error: ${payload.error}`, 'error');
    stopDigestStream();
    return;
  }

  if (payload.done) {
    renderDigestSummary(payload.summary, payload.result);
    setDigestStatusMessage('Daily Digest completed.', 'success');
    digestState.historyLoaded = false;
    await loadDigestHistory(true);
    refreshDashboard();
    showNotification('Daily Digest Complete', { body: 'New papers have been collected and summarized.', tag: 'jarvis-digest' });
    showToast('Daily Digest completed successfully!', 'success');
    stopDigestStream();
    return;
  }

  if (payload.message) setDigestStatusMessage(payload.message);
}

function runDailyDigestFromUI() {
  if (digestState.running) return;

  stopDigestStream();
  digestState.running = true;
  setDigestRunButtonState(true);
  setDigestStatusMessage('Daily Digest is running...');

  const summaryElement = document.getElementById('digest-results-summary');
  if (summaryElement) summaryElement.textContent = 'Digest running...';
  const keywordsElement = document.getElementById('digest-results-keywords');
  if (keywordsElement) keywordsElement.innerHTML = '';
  const topList = document.getElementById('digest-top-papers-list');
  if (topList) topList.innerHTML = '<li class="pipeline-empty-row">Digest running...</li>';

  const eventSource = new EventSource(buildDigestStreamUrl());
  digestState.eventSource = eventSource;

  eventSource.onmessage = (event) => {
    if (digestState.eventSource !== eventSource) return;
    try {
      const payload = JSON.parse(event.data);
      Promise.resolve(handleDigestPayload(payload, eventSource)).catch((error) => {
        setDigestStatusMessage(`Digest stream error: ${error.message}`, 'error');
        showToast(`Digest stream error: ${error.message}`, 'error');
        stopDigestStream();
      });
    } catch {
      setDigestStatusMessage('Invalid digest stream payload.', 'error');
      showToast('Digest stream error: Invalid digest stream payload.', 'error');
      stopDigestStream();
    }
  };

  eventSource.onerror = () => {
    if (digestState.eventSource !== eventSource) return;
    setDigestStatusMessage('Digest stream disconnected.', 'error');
    showToast('Digest stream disconnected.', 'error');
    stopDigestStream();
  };
}

async function downloadDigestReport(filename) {
  const safeFilename = String(filename || '').trim();
  if (!safeFilename) return;
  const response = await fetch(`/api/digest/report/${encodeURIComponent(safeFilename)}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const blob = await response.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = safeFilename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(blobUrl);
}

function bindPipelineEvents() {
  if (pipelineState.bound) return;
  pipelineState.bound = true;

  const form = document.getElementById('pipeline-form');
  const queryInput = document.getElementById('pipeline-query-input');
  const refreshButton = document.getElementById('pipeline-refresh-history-btn');
  const runButton = document.getElementById('digest-run-btn');
  const digestRefresh = document.getElementById('digest-refresh-history-btn');
  const digestHistoryBody = document.getElementById('digest-history-body');

  if (form && queryInput) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const query = queryInput.value.trim();
      if (!query) {
        setPipelineStatusMessage('Query is required.', 'error');
        return;
      }
      runPipelineQuery(query);
    });
  }

  refreshButton?.addEventListener('click', () => {
    pipelineState.historyLoaded = false;
    loadPipelineHistory(true);
  });

  runButton?.addEventListener('click', () => {
    runDailyDigestFromUI();
  });

  digestRefresh?.addEventListener('click', () => {
    digestState.historyLoaded = false;
    loadDigestHistory(true).catch((error) => {
      showToast(error.message || 'Failed to load digest history');
    });
  });

  digestHistoryBody?.addEventListener('click', (event) => {
    const target = event.target.closest('[data-digest-report]');
    if (!target) return;
    const filename = decodeURIComponent(target.getAttribute('data-digest-report') || '');
    downloadDigestReport(filename).catch((error) => {
      showToast(`Download failed: ${error.message || 'unknown'}`);
    });
  });

  window.addEventListener('beforeunload', stopPipelineStream);
  window.addEventListener('beforeunload', stopDigestStream);
}

function initializePipelineUI() {
  ensurePipelineProgressBar();
  resetPipelineSteps();
  renderPipelineEmptyResults('No results yet.');
  setPipelineStatusMessage('Enter a query and run the pipeline.');
  setPipelineRunButtonState(false);
  setDigestRunButtonState(false);
  setDigestStatusMessage('Click "Run Daily Digest" to start.');
}

export async function init() {
  bindPipelineEvents();
  initializePipelineUI();
}

export async function onActivate() {
  await Promise.allSettled([loadPipelineHistory(), loadDigestHistory()]);
}
