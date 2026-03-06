import { autoLinkDOI, escapeHtml, fetchJson, formatElapsedTime, formatJsonBlock, formatTimestamp, parseDurationMs, requestNotificationPermission, showToast, updateNotificationToggleState } from './utils.js';

const state = {
  currentSessionId: null,
  messages: [],
  models: [],
  isStreaming: false,
  assistantMessageElement: null,
  inlineActivityEl: null,
  activityItems: new Map(),
  activityStartedAt: new Map(),
  researchMode: false,
  copilotConnected: false,
};

const elements = {};
const sseDecoder = new TextDecoder('utf-8');
let initialized = false;
let usageIntervalId = null;

function cacheElements() {
  elements.modelSelector = document.querySelector('#model-selector');
  elements.currentModelLabel = document.querySelector('#current-model-label');
  elements.sessionHistory = document.querySelector('#session-history');
  elements.chatMessages = document.querySelector('#chat-messages');
  elements.chatForm = document.querySelector('#chat-input-form');
  elements.chatInput = document.querySelector('#chat-input');
  elements.sendButton = document.querySelector('#send-button');
  elements.newSessionBtn = document.querySelector('#new-session-btn');
}

function scrollChatToBottom() {
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function splitTrailingPunctuation(rawText) {
  let text = String(rawText || '');
  let trailing = '';
  while (/[.,;)\]]$/.test(text)) {
    trailing = text.slice(-1) + trailing;
    text = text.slice(0, -1);
  }
  return { text, trailing };
}

function isPdfCardCandidate(rawText) {
  const text = String(rawText || '');
  if (/^https?:\/\//i.test(text)) return /\.pdf(?:$|[?#])/i.test(text);
  if (/^[A-Za-z]:\\/.test(text)) return /\\pdf-archive\\/i.test(text) && /\.pdf$/i.test(text);
  if (/^\/?data\/pdf-archive\//i.test(text)) return /\.pdf$/i.test(text);
  return false;
}

function normalizePdfHref(rawText) {
  const text = String(rawText || '').trim();
  if (!text) return '';
  if (/^https?:\/\//i.test(text)) return text;
  if (/^\/?data\/pdf-archive\//i.test(text)) return text.startsWith('/') ? text : `/${text}`;
  if (/^[A-Za-z]:\\/.test(text)) {
    const normalized = text.replace(/\\/g, '/');
    const marker = '/data/pdf-archive/';
    const index = normalized.toLowerCase().indexOf(marker);
    if (index >= 0) return normalized.slice(index);
  }
  return '';
}

function getPdfFilename(rawText) {
  const normalized = String(rawText || '').replace(/\\/g, '/');
  const segments = normalized.split('/').filter(Boolean);
  return segments.length ? segments[segments.length - 1] : normalized;
}

function buildPdfCard(rawText) {
  const href = normalizePdfHref(rawText);
  const filename = getPdfFilename(rawText);
  if (!href || !filename) return '';
  return `<a class="pdf-card" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer"><span class="pdf-card-icon">📄</span><span class="pdf-card-label">${escapeHtml(filename)}</span></a>`;
}

function replacePdfCards(text) {
  if (!text) return '';
  return String(text).replace(/(^|\s)((?:https?:\/\/\S+?\.pdf(?:[?#]\S*)?|[A-Za-z]:\\[^\s]+?\.pdf|\/?data\/pdf-archive\/[^\s]+?\.pdf))(?=$|\s)/g, (_, prefix, rawPath) => `${prefix}${buildPdfCard(rawPath) || escapeHtml(rawPath)}`);
}

function replacePdfArchivedBadge(text) {
  if (!text) return '';
  const badge = '<span class="pdf-badge">📁 PDF Archived</span>';
  const withPhraseBadge = String(text).replace(/\bPDF archived\b/gi, badge);
  return withPhraseBadge.replace(/(^|[^\/\\\w-])(pdf-archive)(?=$|[^\/\\\w-])/gi, (_, prefix) => prefix + badge);
}

function applyInlineMarkdownStyles(text) {
  if (!text) return '';
  const inlineCodeTokens = [];
  const withoutInlineCode = String(text).replace(/`([^`]+)`/g, (_, code) => {
    const token = `@@INLINE_CODE_${inlineCodeTokens.length}@@`;
    inlineCodeTokens.push({ token, html: `<code class="inline-code">${code}</code>` });
    return token;
  });
  let styled = replacePdfCards(withoutInlineCode);
  styled = replacePdfArchivedBadge(styled);
  styled = autoLinkDOI(styled).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  for (const item of inlineCodeTokens) {
    styled = styled.replaceAll(item.token, item.html);
  }
  return styled;
}

function formatInlineText(text) {
  if (!text) return '';
  const escaped = escapeHtml(text);
  const headingTokens = [];
  const tokenized = escaped.split('\n').map((line) => {
    const h2 = line.match(/^##\s+(.+)$/);
    if (h2) {
      const token = `@@MD_H2_${headingTokens.length}@@`;
      headingTokens.push({ token, html: `<h2 class="md-heading md-heading-h2">${applyInlineMarkdownStyles(h2[1])}</h2>` });
      return token;
    }
    const h3 = line.match(/^###\s+(.+)$/);
    if (h3) {
      const token = `@@MD_H3_${headingTokens.length}@@`;
      headingTokens.push({ token, html: `<h3 class="md-heading md-heading-h3">${applyInlineMarkdownStyles(h3[1])}</h3>` });
      return token;
    }
    return line;
  }).join('\n');
  let formatted = applyInlineMarkdownStyles(tokenized).replace(/\n/g, '<br>');
  for (const item of headingTokens) {
    formatted = formatted.replace(item.token, item.html);
  }
  return formatted;
}

function formatMarkdown(raw) {
  if (!raw) return '';
  const normalized = String(raw).replace(/\r\n/g, '\n');
  const codeBlocks = [];
  const withoutCode = normalized.replace(/```([^\n`]*)\n([\s\S]*?)```/g, (_, rawLang, rawCode) => {
    const lang = (rawLang || '').trim() || 'plaintext';
    const code = String(rawCode || '');
    let jsonHtml = '';
    if (lang.toLowerCase() === 'json') jsonHtml = formatJsonBlock(code);
    const html = jsonHtml || `<div class="code-block-wrapper"><div class="code-block-header"><span>${escapeHtml(lang)}</span><button class="code-copy-btn" onclick="copyCode(this)" type="button">copy</button></div><pre><code class="hljs language-${escapeHtml(lang)}">${escapeHtml(code)}</code></pre></div>`;
    const token = `@@CODE_BLOCK_${codeBlocks.length}@@`;
    codeBlocks.push({ token, html });
    return token;
  });
  if (!codeBlocks.length) {
    const standaloneJson = formatJsonBlock(withoutCode);
    if (standaloneJson) return standaloneJson;
  }
  let result = formatInlineText(withoutCode);
  for (const block of codeBlocks) {
    result = result.replaceAll(block.token, block.html);
  }
  return result;
}

function getMarkdownHeadingLevel(node) {
  if (!node || node.nodeType !== 1 || !node.tagName) return 0;
  const tagName = node.tagName.toUpperCase();
  if (tagName === 'H2') return 2;
  if (tagName === 'H3') return 3;
  return 0;
}

function trimSectionBreaks(container) {
  if (!container) return;
  while (container.firstChild && container.firstChild.nodeType === 1 && container.firstChild.tagName.toUpperCase() === 'BR') {
    container.removeChild(container.firstChild);
  }
  while (container.lastChild && container.lastChild.nodeType === 1 && container.lastChild.tagName.toUpperCase() === 'BR') {
    container.removeChild(container.lastChild);
  }
}

function buildCollapsibleMarkdownSections(container) {
  if (!container) return;
  const children = Array.from(container.childNodes);
  let cursor = 0;
  while (cursor < children.length) {
    const node = children[cursor];
    const level = getMarkdownHeadingLevel(node);
    if (!level) {
      cursor += 1;
      continue;
    }
    const details = document.createElement('details');
    details.className = `markdown-section markdown-section-level-${level}`;
    details.open = true;
    const summary = document.createElement('summary');
    summary.className = 'markdown-section-summary';
    summary.innerHTML = node.innerHTML;
    details.appendChild(summary);
    const body = document.createElement('div');
    body.className = 'markdown-section-body';
    const inner = document.createElement('div');
    inner.className = 'markdown-section-body-inner';
    body.appendChild(inner);
    details.appendChild(body);
    container.insertBefore(details, node);
    node.remove();
    cursor += 1;
    while (cursor < children.length) {
      const candidate = children[cursor];
      const candidateLevel = getMarkdownHeadingLevel(candidate);
      if (candidateLevel && candidateLevel <= level) break;
      inner.appendChild(candidate);
      cursor += 1;
    }
    trimSectionBreaks(inner);
    if (level === 2) buildCollapsibleMarkdownSections(inner);
  }
}

function enhanceAssistantMarkdown(contentElement) {
  if (contentElement) buildCollapsibleMarkdownSections(contentElement);
}

function normalizeReasoningKind(value) {
  const raw = String(value || '').trim().toLowerCase();
  if (!raw) return 'Thinking';
  if (raw.includes('think')) return 'Thinking';
  if (raw.includes('search')) return 'Searching';
  if (raw.includes('analy') || raw.includes('evidence')) return 'Analyzing';
  if (raw.includes('read') || raw.includes('browse')) return 'Reading';
  if (raw.includes('generat') || raw.includes('write') || raw.includes('respond')) return 'Generating';
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}

function getReasoningIcon(kind) {
  switch (normalizeReasoningKind(kind)) {
    case 'Thinking': return '💭';
    case 'Searching': return '🔍';
    case 'Analyzing': return '📊';
    case 'Reading': return '📖';
    case 'Generating': return '✍️';
    default: return '⚡';
  }
}

function formatReasoningLabel(stepName) {
  const step = String(stepName || '').trim().toLowerCase();
  const labels = {
    thinking: 'Thinking through the request',
    browse_url: 'Reading URL content',
    semantic_search: 'Searching semantic index',
    live_paper_search: 'Searching live papers',
    evidence_grade: 'Analyzing evidence strength',
    generate_response: 'Generating response',
  };
  if (labels[step]) return labels[step];
  const humanized = step.split('_').filter(Boolean).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
  return humanized || 'Processing step';
}

function createReasoningTrace(steps) {
  const details = document.createElement('details');
  details.className = 'reasoning-trace';
  details.open = true;
  const summary = document.createElement('summary');
  summary.innerHTML = '<span class="trace-icon">⚡</span>Reasoning (<span class="trace-count">0</span> steps)<span class="trace-time"></span>';
  details.appendChild(summary);
  const traceSteps = document.createElement('div');
  traceSteps.className = 'trace-steps';
  details.appendChild(traceSteps);
  (steps || []).forEach((step) => {
    if (step?.node) traceSteps.appendChild(step.node);
  });
  return details;
}

function renderReasoningStep(step) {
  const node = document.createElement('div');
  node.className = 'trace-step';
  node.innerHTML = `<span class="trace-step-icon">${getReasoningIcon(step.kind)}</span><span class="trace-step-text">${escapeHtml(step.text)}</span><span class="trace-step-time"></span>`;
  step.node = node;
  return node;
}
function updateReasoningTraceMeta(bubble, totalMs) {
  if (!bubble?._reasoningTrace) return;
  const countElement = bubble._reasoningTrace.querySelector('.trace-count');
  const timeElement = bubble._reasoningTrace.querySelector('.trace-time');
  if (countElement) countElement.textContent = String((bubble._reasoningSteps || []).length);
  if (timeElement) timeElement.textContent = totalMs && totalMs > 0 ? formatElapsedTime(totalMs) : '';
}

function getMessageContentElement(bubble) {
  if (!bubble) return null;
  let contentElement = bubble.querySelector('.message-content');
  if (contentElement) return contentElement;
  contentElement = document.createElement('div');
  contentElement.className = 'message-content';
  contentElement.innerHTML = bubble.innerHTML;
  bubble.innerHTML = '';
  bubble.appendChild(contentElement);
  return contentElement;
}

function ensureReasoningTraceState(bubble) {
  if (!bubble) return null;
  if (!bubble._reasoningTrace) {
    bubble._reasoningTrace = createReasoningTrace([]);
    bubble._reasoningSteps = [];
    bubble._reasoningStartedAt = Date.now();
    bubble._reasoningLineBuffer = '';
    bubble.insertBefore(bubble._reasoningTrace, getMessageContentElement(bubble));
  }
  return bubble._reasoningTrace;
}

function updateReasoningStepDuration(step) {
  if (!step?.node) return;
  const timeElement = step.node.querySelector('.trace-step-time');
  if (timeElement) timeElement.textContent = step.durationMs ? formatElapsedTime(step.durationMs) : '';
}

function finalizeReasoningStep(step, endedAt, explicitDurationMs) {
  if (!step || step.endedAt) return;
  const finishedAt = Number.isFinite(endedAt) ? endedAt : Date.now();
  let computedDuration = explicitDurationMs;
  if (!Number.isFinite(computedDuration)) computedDuration = Math.max(finishedAt - step.startedAt, 0);
  step.endedAt = finishedAt;
  step.durationMs = computedDuration;
  updateReasoningStepDuration(step);
}

function getOpenReasoningStep(bubble, key) {
  if (!bubble?._reasoningSteps) return null;
  for (let index = bubble._reasoningSteps.length - 1; index >= 0; index -= 1) {
    const step = bubble._reasoningSteps[index];
    if (!step.endedAt && (!key || step.key === key)) return step;
  }
  return null;
}

function renderMessage(role, content) {
  const bubble = document.createElement('article');
  bubble.className = `message message-bubble ${role}`;
  const contentElement = document.createElement('div');
  contentElement.className = 'message-content';
  contentElement.innerHTML = formatMarkdown(content);
  if (role === 'assistant') enhanceAssistantMarkdown(contentElement);
  bubble.appendChild(contentElement);
  bubble.dataset.renderedTextLength = String((contentElement.textContent || '').length);
  elements.chatMessages.appendChild(bubble);
  scrollChatToBottom();
  return bubble;
}

function renderEmptyState(message) {
  elements.chatMessages.innerHTML = `<div class="empty-state">${message}</div>`;
}

function ensureAssistantBubble() {
  if (!state.assistantMessageElement) state.assistantMessageElement = renderMessage('assistant', '');
  return state.assistantMessageElement;
}

function appendReasoningStep(stepPayload) {
  const bubble = ensureAssistantBubble();
  const trace = ensureReasoningTraceState(bubble);
  if (!trace) return null;
  const now = Date.now();
  const existing = stepPayload.key ? getOpenReasoningStep(bubble, stepPayload.key) : null;
  if (existing) return existing;
  const previous = getOpenReasoningStep(bubble);
  if (previous) finalizeReasoningStep(previous, now);
  const step = {
    key: stepPayload.key || `step_${bubble._reasoningSteps.length}`,
    kind: normalizeReasoningKind(stepPayload.kind),
    text: stepPayload.text || 'Processing step',
    startedAt: now,
    durationMs: 0,
    endedAt: null,
    node: null,
  };
  bubble._reasoningSteps.push(step);
  renderReasoningStep(step);
  trace.querySelector('.trace-steps')?.appendChild(step.node);
  updateReasoningTraceMeta(bubble, now - bubble._reasoningStartedAt);
  return step;
}

function handleReasoningActivity(payload) {
  if (!payload || (!payload.step && !payload.type)) return;
  const bubble = ensureAssistantBubble();
  const kind = normalizeReasoningKind(payload.type || payload.step);
  const label = payload.message || payload.text || formatReasoningLabel(payload.step || payload.type);
  const key = String(payload.step || payload.type || label).trim().toLowerCase();
  if (payload.status === 'running' || !payload.status) {
    appendReasoningStep({ key, kind, text: label });
    return;
  }
  let step = getOpenReasoningStep(bubble, key);
  if (!step) step = appendReasoningStep({ key, kind, text: label });
  finalizeReasoningStep(step, Date.now(), parseDurationMs(payload.time));
  updateReasoningTraceMeta(bubble, Date.now() - bubble._reasoningStartedAt);
}

function consumeReasoningDelta(content) {
  if (!content) return;
  const bubble = ensureAssistantBubble();
  if (typeof bubble._reasoningLineBuffer !== 'string') bubble._reasoningLineBuffer = '';
  bubble._reasoningLineBuffer += String(content);
  const lines = bubble._reasoningLineBuffer.split(/\r?\n/);
  bubble._reasoningLineBuffer = lines.pop() || '';
  lines.forEach((line) => {
    const match = line.trim().match(/^(Thinking|Searching|Analyzing|Reading|Generating):\s*(.+)$/i);
    if (!match) return;
    appendReasoningStep({ key: `line_${match[1].toLowerCase()}_${(bubble._reasoningSteps || []).length}`, kind: match[1], text: match[2] || match[1] });
  });
}

function finalizeReasoningTrace(bubble) {
  if (!bubble) return;
  const trailingLine = String(bubble._reasoningLineBuffer || '').trim();
  if (trailingLine) {
    const match = trailingLine.match(/^(Thinking|Searching|Analyzing|Reading|Generating):\s*(.+)$/i);
    if (match) appendReasoningStep({ key: `line_${match[1].toLowerCase()}_${(bubble._reasoningSteps || []).length}`, kind: match[1], text: match[2] || match[1] });
    bubble._reasoningLineBuffer = '';
  }
  if (!bubble._reasoningTrace || !bubble._reasoningSteps?.length) return;
  const endedAt = Date.now();
  const openStep = getOpenReasoningStep(bubble);
  if (openStep) finalizeReasoningStep(openStep, endedAt);
  updateReasoningTraceMeta(bubble, endedAt - bubble._reasoningStartedAt);
}

function ensureResearchBadge() {
  let badge = document.querySelector('#research-mode-badge');
  if (!badge) {
    badge = document.createElement('span');
    badge.id = 'research-mode-badge';
    badge.textContent = 'Research Mode';
    badge.hidden = true;
    badge.style.cssText = 'margin-left:10px;padding:2px 8px;border-radius:999px;border:1px solid rgba(212,160,23,0.32);background:rgba(140,102,21,0.24);color:#f0d060;font-size:0.75rem;font-weight:600;';
    elements.currentModelLabel.insertAdjacentElement('afterend', badge);
  }
  return badge;
}

function syncResearchBadge() {
  ensureResearchBadge().hidden = !state.researchMode;
}

function ensureCopilotBadge() {
  let badge = document.querySelector('#copilot-status-badge');
  if (!badge) {
    badge = document.createElement('div');
    badge.id = 'copilot-status-badge';
    badge.style.cssText = 'margin-top:0.75rem;padding:0.55rem 0.75rem;border-radius:12px;font-size:0.8rem;font-weight:600;line-height:1.4;';
    elements.modelSelector.insertAdjacentElement('afterend', badge);
  }
  return badge;
}

function syncCopilotBadge() {
  const badge = ensureCopilotBadge();
  if (state.copilotConnected) {
    badge.textContent = '✨ Copilot Connected';
    badge.style.color = '#b9ffd1';
    badge.style.background = 'rgba(38,120,77,0.24)';
    badge.style.border = '1px solid rgba(87,214,135,0.35)';
  } else {
    badge.textContent = 'Copilot Offline - LiteLLM Fallback';
    badge.style.color = '#ffe7a8';
    badge.style.background = 'rgba(140,102,21,0.2)';
    badge.style.border = '1px solid rgba(244,196,48,0.35)';
  }
}

function renderModelSelector(models) {
  const select = elements.modelSelector;
  if (!select) return;
  select.innerHTML = '';
  const tiers = { pro: [], 'pro+': [], unknown: [], local: [] };
  for (const model of models) (tiers[model.tier] || tiers.unknown).push(model);

  function addGroup(label, list, locked) {
    if (!list.length) return;
    const group = document.createElement('optgroup');
    group.label = label;
    for (const model of list) {
      const option = document.createElement('option');
      option.value = model.id;
      option.textContent = locked ? `⚠ ${model.id} (Pro+)` : (model.name || model.id);
      if (model.default) option.selected = true;
      group.appendChild(option);
    }
    select.appendChild(group);
  }

  addGroup('✨ Copilot Pro', tiers.pro, false);
  addGroup('Unverified', tiers.unknown, false);
  addGroup('⚠ Pro+ ($20/mo)', tiers['pro+'], true);
  addGroup('Local Fallback', tiers.local, false);
}

function ensureUsageDisplay() {
  if (document.getElementById('usage-display')) return;
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;
  const ref = sidebar.querySelector('[id*="copilot-status"]') || sidebar.querySelector('button');
  const div = document.createElement('div');
  div.id = 'usage-display';
  div.innerHTML = '<div style="margin-top:10px;padding:8px 12px;background:rgba(20,20,40,0.8);border:1px solid rgba(212,160,23,0.1);border-radius:12px;font-size:12px;"><div style="color:var(--accent-primary);margin-bottom:4px;font-weight:bold;letter-spacing:1px;">✨ COPILOT USAGE</div><div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:#e0e0e0;">Premium Requests</span><span id="usage-percent" style="color:#e0e0e0;">--</span></div><div style="background:#2a2a3e;border-radius:4px;height:6px;overflow:hidden;"><div id="usage-bar" style="height:100%;width:0%;background:var(--success);border-radius:4px;transition:width 0.5s;"></div></div></div>';
  if (ref?.parentNode) ref.parentNode.insertBefore(div, ref.nextSibling);
  else sidebar.appendChild(div);
}

async function updateUsage() {
  ensureUsageDisplay();
  try {
    const response = await fetch('/api/usage');
    const data = await response.json();
    const percentElement = document.getElementById('usage-percent');
    const barElement = document.getElementById('usage-bar');
    state.copilotConnected = Boolean(data.available);
    syncCopilotBadge();
    if (data.available) {
      let percent = 0;
      if (data.copilot_usage?.premium_requests?.percentage !== undefined) percent = data.copilot_usage.premium_requests.percentage;
      if (data.percentage !== undefined) percent = data.percentage;
      if (data.chat?.percentage !== undefined) percent = data.chat.percentage;
      if (percentElement) percentElement.textContent = `${percent.toFixed(1)}%`;
      if (barElement) {
        barElement.style.width = `${Math.min(percent, 100)}%`;
        barElement.style.background = percent > 80 ? '#ef4444' : percent > 50 ? '#eab308' : 'var(--success)';
      }
    } else {
      if (percentElement) percentElement.textContent = 'N/A';
      if (barElement) barElement.style.width = '0%';
    }
  } catch {
  }
}

function ensureInlineActivity() {
  if (state.inlineActivityEl) return state.inlineActivityEl;
  const block = document.createElement('div');
  block.className = 'inline-activity';
  block.innerHTML = '<div class="inline-activity-header"><span class="inline-activity-title">✨ Agent Activity</span><span class="inline-activity-status" id="inline-status">running</span></div><div class="inline-activity-timeline" id="inline-timeline"></div>';
  elements.chatMessages.appendChild(block);
  state.inlineActivityEl = block;
  scrollChatToBottom();
  return block;
}

function upsertActivity(step, status, time, extra) {
  ensureInlineActivity();
  if (status === 'running') state.activityStartedAt.set(step, Date.now());
  const timeline = document.getElementById('inline-timeline');
  let node = state.activityItems.get(step);
  if (!node) {
    node = document.createElement('div');
    node.className = `inline-activity-item activity-item ${status}`;
    node.innerHTML = '<span class="ia-dot activity-dot"></span><div class="ia-content"><div class="ia-title"></div><div class="ia-meta"></div></div>';
    state.activityItems.set(step, node);
    timeline.appendChild(node);
  }
  node.className = `inline-activity-item activity-item ${status}`;
  const dot = node.querySelector('.activity-dot');
  if (dot) dot.className = `ia-dot activity-dot ${status}`;
  const label = step.split('_').map((token) => token.charAt(0).toUpperCase() + token.slice(1)).join(' ');
  node.querySelector('.ia-title').textContent = label;
  let elapsed = time || '';
  if (!elapsed && state.activityStartedAt.has(step)) elapsed = `${Date.now() - state.activityStartedAt.get(step)}ms`;
  node.querySelector('.ia-meta').textContent = [status, elapsed, extra || ''].filter(Boolean).join(' · ');
  scrollChatToBottom();
}

function renderToolCall(payload) {
  ensureInlineActivity();
  const timeline = document.getElementById('inline-timeline');
  const details = document.createElement('details');
  details.className = 'inline-activity-item activity-item done';
  const preview = String(payload.result || '').slice(0, 200);
  details.innerHTML = '<summary style="display:flex;align-items:center;gap:8px;cursor:pointer;"><span class="ia-dot activity-dot done"></span><span class="ia-title">✨ [tool] ' + escapeHtml(payload.name || 'tool_call') + '</span></summary><div class="ia-meta" style="margin-left:20px;">' + escapeHtml(payload.time || '') + '</div><div style="margin:4px 0 0 20px;font-size:0.8rem;color:var(--text-muted);white-space:pre-wrap;word-break:break-word;">' + escapeHtml(preview) + '</div>';
  timeline.appendChild(details);
  scrollChatToBottom();
}

function finalizeInlineActivity() {
  const statusElement = document.getElementById('inline-status');
  if (statusElement) {
    statusElement.textContent = 'done';
    statusElement.className = 'inline-activity-status done';
  }
}

function resetActivity() {
  state.activityItems.clear();
  state.activityStartedAt.clear();
  state.researchMode = false;
  if (state.inlineActivityEl?.parentElement) state.inlineActivityEl.remove();
  state.inlineActivityEl = null;
  syncResearchBadge();
}

function setStreaming(value) {
  state.isStreaming = value;
  elements.sendButton.disabled = value;
}

function wrapTextSliceWithClass(node, start, end, className) {
  if (!node?.parentNode) return false;
  const text = node.nodeValue || '';
  if (start < 0 || end > text.length || start >= end) return false;
  const fragment = document.createDocumentFragment();
  if (text.slice(0, start)) fragment.appendChild(document.createTextNode(text.slice(0, start)));
  const marker = document.createElement('span');
  marker.className = className;
  marker.textContent = text.slice(start, end);
  fragment.appendChild(marker);
  if (text.slice(end)) fragment.appendChild(document.createTextNode(text.slice(end)));
  node.parentNode.replaceChild(fragment, node);
  return true;
}

function applyStreamingTextReveal(bubble, contentElement, addedLength) {
  if (!bubble || !contentElement) return;
  if (bubble._textRevealTimer) clearTimeout(bubble._textRevealTimer);
  let remaining = Number(addedLength) || 0;
  const nodes = [];
  const walker = document.createTreeWalker(contentElement, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (let index = nodes.length - 1; index >= 0 && remaining > 0; index -= 1) {
    const node = nodes[index];
    const len = (node.nodeValue || '').length;
    if (!len) continue;
    const take = Math.min(len, remaining);
    const start = len - take;
    if (wrapTextSliceWithClass(node, start, len, 'text-reveal')) remaining -= take;
  }
  if (remaining > 0) contentElement.classList.add('text-reveal');
  bubble._textRevealTimer = setTimeout(() => {
    contentElement.querySelectorAll('.text-reveal').forEach((mark) => mark.classList.remove('text-reveal'));
    contentElement.classList.remove('text-reveal');
    bubble._textRevealTimer = null;
  }, 300);
}
function renderSessionList(sessions) {
  elements.sessionHistory.innerHTML = '';
  if (!sessions.length) {
    elements.sessionHistory.innerHTML = '<div class="empty-state">No sessions yet</div>';
    return;
  }
  for (const session of sessions) {
    const item = document.createElement('div');
    item.className = `session-item ${session.id === state.currentSessionId ? 'active' : ''}`;
    item.tabIndex = 0;
    item.innerHTML = '<div class="session-title-row"><div class="session-main"><div class="session-title">' + escapeHtml(session.title || 'Untitled') + '</div><div class="session-meta">' + escapeHtml(session.model || '') + '</div><div class="session-meta">' + formatTimestamp(session.updated_at) + '</div></div><div class="session-actions"><button type="button" class="btn-export" title="Export as Markdown" data-export-session="' + escapeHtml(session.id) + '">📥</button><button type="button" class="delete-session-btn" data-sid="' + escapeHtml(session.id) + '">x</button></div></div>';
    item.addEventListener('click', async (event) => {
      const deleteButton = event.target.closest('[data-sid]');
      const exportButton = event.target.closest('[data-export-session]');
      if (deleteButton) {
        event.stopPropagation();
        await deleteSession(deleteButton.dataset.sid);
        return;
      }
      if (exportButton) {
        event.stopPropagation();
        exportSession(exportButton.dataset.exportSession);
        return;
      }
      await loadSession(session.id);
    });
    item.addEventListener('keydown', async (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      await loadSession(session.id);
    });
    elements.sessionHistory.appendChild(item);
  }
}

async function refreshSessions() {
  renderSessionList(await fetchJson('/api/sessions'));
}

function exportSession(sessionId) {
  const safeSessionId = String(sessionId || '').trim();
  if (!safeSessionId) return;
  window.open(`/api/sessions/${encodeURIComponent(safeSessionId)}/export`, '_blank');
}

function resolveStatusContainer() {
  return document.getElementById('status-panel') || document.querySelector('h3 + div');
}

async function updateSystemStatus() {
  const container = resolveStatusContainer();
  if (!container) return;
  try {
    const [skills, mcp] = await Promise.all([
      fetch('/api/skills').then((response) => response.json()),
      fetch('/api/mcp/servers').then((response) => response.json()),
    ]);
    let html = '<div style="font-size:12px;">';
    html += '<div style="color:var(--accent-primary);font-weight:bold;letter-spacing:1px;margin-bottom:6px;">✨ MCP SERVERS</div>';
    for (const server of mcp) {
      html += '<div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span style="color:#e0e0e0;">' + escapeHtml(server.name) + '</span><span style="color:var(--success);font-size:10px;">' + server.tools.length + ' tools</span></div>';
    }
    html += '<div style="color:var(--accent-primary);font-weight:bold;letter-spacing:1px;margin-top:10px;margin-bottom:6px;">✨ SKILLS</div>';
    const categories = {};
    for (const skill of skills) {
      if (!categories[skill.category]) categories[skill.category] = [];
      categories[skill.category].push(skill);
    }
    for (const [category, list] of Object.entries(categories)) {
      html += '<div style="color:var(--text-muted);font-size:10px;text-transform:uppercase;margin-top:4px;">' + escapeHtml(category) + '</div>';
      for (const skill of list) {
        html += '<div style="color:#e0e0e0;margin-left:8px;margin-bottom:2px;font-size:11px;">- ' + escapeHtml(skill.name) + '</div>';
      }
    }
    html += '</div>';
    container.innerHTML = html;
  } catch {
  }
}

async function loadModels() {
  state.models = await fetchJson('/api/models');
  renderModelSelector(state.models);
  state.copilotConnected = state.models.some((model) => model.tier && model.tier !== 'local');
  syncCopilotBadge();
  ensureUsageDisplay();
  const active = state.models.find((model) => model.default) || state.models[0];
  if (active) {
    if (!elements.modelSelector.value) elements.modelSelector.value = active.id;
    const selected = state.models.find((model) => model.id === elements.modelSelector.value) || active;
    elements.currentModelLabel.textContent = selected.name || selected.id;
    syncResearchBadge();
  }
}

async function loadSession(id) {
  const session = await fetchJson(`/api/sessions/${id}`);
  state.currentSessionId = session.id;
  state.messages = session.messages || [];
  state.assistantMessageElement = null;
  resetActivity();
  elements.chatMessages.innerHTML = '';
  if (!state.messages.length) renderEmptyState('No messages in this session');
  else state.messages.forEach((message) => renderMessage(message.role, message.content));
  const activeModel = state.models.find((model) => model.id === session.model);
  elements.currentModelLabel.textContent = (activeModel ? activeModel.name : null) || session.model || 'Unknown';
  syncResearchBadge();
  await refreshSessions();
}

function newSession() {
  state.currentSessionId = null;
  state.messages = [];
  state.assistantMessageElement = null;
  elements.chatMessages.innerHTML = '';
  renderEmptyState('✨ Start a new conversation');
  resetActivity();
  refreshSessions().catch((error) => showToast(error.message));
}

async function deleteSession(id) {
  if (!window.confirm('Delete this session?')) return;
  await fetchJson(`/api/sessions/${id}`, { method: 'DELETE' });
  if (state.currentSessionId === id) {
    newSession();
    return;
  }
  await refreshSessions();
}

function appendAssistantDelta(content) {
  consumeReasoningDelta(content);
  const bubble = ensureAssistantBubble();
  const current = bubble.dataset.rawContent || '';
  const previousRenderedLength = Number(bubble.dataset.renderedTextLength || '0');
  const next = current + content;
  bubble.dataset.rawContent = next;
  const contentElement = getMessageContentElement(bubble);
  contentElement.innerHTML = formatMarkdown(next);
  enhanceAssistantMarkdown(contentElement);
  const nextRenderedLength = (contentElement.textContent || '').length;
  bubble.dataset.renderedTextLength = String(nextRenderedLength);
  applyStreamingTextReveal(bubble, contentElement, Math.max(nextRenderedLength - previousRenderedLength, 0));
  scrollChatToBottom();
}

async function sendMessage(content) {
  if (!content.trim() || state.isStreaming) return;
  if (elements.chatMessages.querySelector('.empty-state')) elements.chatMessages.innerHTML = '';
  const model = elements.modelSelector.value;
  state.messages.push({ role: 'user', content });
  renderMessage('user', content);
  resetActivity();
  state.assistantMessageElement = null;
  setStreaming(true);
  elements.currentModelLabel.textContent = (state.models.find((item) => item.id === model) || {}).name || model;

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId: state.currentSessionId, message: content, model }),
    });
    if (!response.ok || !response.body) throw new Error('Failed to start stream');
    const reader = response.body.getReader();
    let buffer = '';
    while (true) {
      const result = await reader.read();
      if (result.done) break;
      buffer += sseDecoder.decode(result.value, { stream: true });
      const chunks = buffer.split('\n\n');
      buffer = chunks.pop() || '';
      for (const chunk of chunks) {
        const lines = chunk.split('\n');
        let eventName = 'message';
        let data = '';
        for (const line of lines) {
          if (line.startsWith('event:')) eventName = line.slice(6).trim();
          if (line.startsWith('data:')) data += line.slice(5).trim();
        }
        if (!data) continue;
        const payload = JSON.parse(data);
        if (eventName === 'session') state.currentSessionId = payload.sessionId;
        if (eventName === 'activity') {
          upsertActivity(payload.step, payload.status, payload.time);
          handleReasoningActivity(payload);
        }
        if (eventName !== 'activity' && eventName !== 'delta' && payload && (payload.step || payload.type)) handleReasoningActivity(payload);
        if (eventName === 'delta') appendAssistantDelta(payload.content);
        if (eventName === 'tool_call') {
          state.researchMode = true;
          syncResearchBadge();
          renderToolCall(payload);
        }
        if (eventName === 'done') {
          finalizeReasoningTrace(state.assistantMessageElement);
          state.messages.push({ role: 'assistant', content: payload.fullContent });
          state.assistantMessageElement = null;
          finalizeInlineActivity();
          elements.currentModelLabel.textContent = (state.models.find((item) => item.id === payload.model) || {}).name || payload.model || model;
          syncResearchBadge();
          await refreshSessions();
        }
        if (eventName === 'error') {
          finalizeReasoningTrace(state.assistantMessageElement);
          renderMessage('system', payload.message && payload.message.includes('not supported') ? 'This model requires Pro+. Use claude-sonnet-4.6 or gpt-4.1.' : `Error: ${payload.message || 'Stream error'}`);
          showToast(`Connection error: ${payload.message || 'Stream error'}`, 'error');
        }
        if (eventName === 'warning') showToast(payload.message || 'Warning', 'info');
      }
    }
  } catch (error) {
    finalizeReasoningTrace(state.assistantMessageElement);
    upsertActivity('error', 'error', '', error.message);
    showToast(`Connection error: ${error.message}`, 'error');
  } finally {
    finalizeReasoningTrace(state.assistantMessageElement);
    setStreaming(false);
    elements.chatInput.value = '';
    autoResizeTextarea();
    scrollChatToBottom();
  }
}

function autoResizeTextarea() {
  elements.chatInput.style.height = 'auto';
  elements.chatInput.style.height = `${Math.min(elements.chatInput.scrollHeight, 200)}px`;
}

function bindEvents() {
  elements.modelSelector.addEventListener('change', () => {
    const active = state.models.find((item) => item.id === elements.modelSelector.value);
    elements.currentModelLabel.textContent = active ? (active.name || active.id) : 'Unknown';
    syncResearchBadge();
  });
  elements.chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    await sendMessage(elements.chatInput.value);
  });
  elements.chatInput.addEventListener('input', autoResizeTextarea);
  elements.chatInput.addEventListener('keydown', async (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      await sendMessage(elements.chatInput.value);
    }
  });
  elements.newSessionBtn.addEventListener('click', newSession);
  document.getElementById('exportCurrentSession')?.addEventListener('click', () => {
    if (!state.currentSessionId) {
      showToast('No active session to export.', 'info');
      return;
    }
    exportSession(state.currentSessionId);
  });
  document.getElementById('notifToggle')?.addEventListener('click', async () => {
    if (!('Notification' in window)) {
      showToast('Browser notifications are not supported.', 'error');
      updateNotificationToggleState();
      return;
    }
    if (Notification.permission === 'default') {
      const permission = await requestNotificationPermission();
      if (permission === 'granted') showToast('Browser notifications enabled.', 'success');
      else if (permission === 'denied') showToast('Browser notifications blocked.', 'error');
      return;
    }
    if (Notification.permission === 'granted') showToast('Browser notifications are enabled.', 'success');
    else showToast('Browser notifications are blocked in this browser.', 'error');
    updateNotificationToggleState();
  });
}

window.copyCode = function copyCode(button) {
  const wrapper = button.closest('.code-block-wrapper');
  const code = wrapper?.querySelector('code');
  navigator.clipboard.writeText(code?.innerText || code?.textContent || '').then(() => {
    button.textContent = 'copied!';
    setTimeout(() => {
      button.textContent = 'copy';
    }, 2000);
  });
};

export async function init() {
  if (initialized) return;
  initialized = true;
  cacheElements();
  bindEvents();
  ensureResearchBadge();
  ensureCopilotBadge();
  ensureUsageDisplay();
  updateNotificationToggleState();
  renderEmptyState('✨ Loading...');
  try {
    await Promise.all([loadModels(), refreshSessions(), updateSystemStatus()]);
    await updateUsage();
    usageIntervalId = window.setInterval(updateUsage, 60000);
    renderEmptyState('✨ Start a new conversation');
  } catch (error) {
    showToast(error.message, 'error');
    renderEmptyState('Failed to load');
  }
  requestNotificationPermission().catch(() => {});
}

export async function onActivate() {
  elements.chatInput?.focus();
}
