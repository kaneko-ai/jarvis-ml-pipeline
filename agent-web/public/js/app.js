/* ===== Particle Engine ===== */
function initParticles() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let particles = [];
  const PARTICLE_COUNT = 60;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticle() {
    return {
      x: Math.random() * canvas.width,
      y: canvas.height + Math.random() * 100,
      size: Math.random() * 2.5 + 0.5,
      speedY: -(Math.random() * 0.4 + 0.1),
      speedX: (Math.random() - 0.5) * 0.2,
      opacity: Math.random() * 0.6 + 0.2,
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: Math.random() * 0.02 + 0.005,
      color: Math.random() > 0.3 ? "rgba(212,160,23," : "rgba(255,255,255,",
    };
  }

  function init() {
    resize();
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const p = createParticle();
      p.y = Math.random() * canvas.height;
      particles.push(p);
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.speedX;
      p.y += p.speedY;
      p.pulse += p.pulseSpeed;
      const alpha = p.opacity * (0.5 + 0.5 * Math.sin(p.pulse));
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = p.color + alpha.toFixed(3) + ")";
      ctx.fill();
      if (p.y < -10 || p.x < -10 || p.x > canvas.width + 10) {
        particles[i] = createParticle();
      }
    }
    requestAnimationFrame(animate);
  }

  window.addEventListener("resize", resize);
  init();
  animate();
}

/* ===== State ===== */
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

const elements = {
  modelSelector: document.querySelector("#model-selector"),
  currentModelLabel: document.querySelector("#current-model-label"),
  sessionHistory: document.querySelector("#session-history"),
  chatMessages: document.querySelector("#chat-messages"),
  chatForm: document.querySelector("#chat-input-form"),
  chatInput: document.querySelector("#chat-input"),
  sendButton: document.querySelector("#send-button"),
  newSessionBtn: document.querySelector("#new-session-btn"),
};

const sseDecoder = new TextDecoder("utf-8");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatTimestamp(iso) {
  if (!iso) return "";
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return diffMinutes + "m ago";
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return diffHours + "h ago";
  return Math.floor(diffHours / 24) + "d ago";
}

function scrollChatToBottom() {
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function formatElapsedTime(ms) {
  if (!Number.isFinite(ms) || ms < 0) return "";
  return (ms / 1000).toFixed(1) + "s";
}

function parseDurationMs(value) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (!value) return null;
  var text = String(value).trim();
  var match = text.match(/^([\d.]+)\s*(ms|s)$/i);
  if (!match) return null;
  var amount = Number(match[1]);
  if (!Number.isFinite(amount)) return null;
  return match[2].toLowerCase() === "s" ? amount * 1000 : amount;
}

function tryParseJson(value) {
  var trimmed = String(value || "").trim();
  if (!trimmed || !/^[\[{]/.test(trimmed)) return null;
  try {
    return JSON.parse(trimmed);
  } catch (error) {
    return null;
  }
}

function highlightJsonString(prettyJson) {
  var source = String(prettyJson || "");
  var html = "";
  var lastIndex = 0;
  var tokenPattern = /("(?:\\.|[^\\"])*")(?=\s*:)|("(?:\\.|[^\\"])*")|\b(?:true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?/g;

  source.replace(tokenPattern, function(match, keyToken, stringToken, offset) {
    html += escapeHtml(source.slice(lastIndex, offset));
    var className = "json-number";
    if (keyToken) {
      className = "json-key";
    } else if (stringToken) {
      className = "json-string";
    } else if (/^(true|false|null)$/.test(match)) {
      className = "json-bool";
    }
    html += '<span class="' + className + '">' + escapeHtml(match) + "</span>";
    lastIndex = offset + match.length;
    return match;
  });

  html += escapeHtml(source.slice(lastIndex));
  return html;
}

function formatJsonBlock(jsonString) {
  var parsed = tryParseJson(jsonString);
  if (parsed === null) return "";
  var prettyJson = JSON.stringify(parsed, null, 2);
  var lineCount = prettyJson.split("\n").length;
  var block =
    '<pre class="json-formatted"><code class="language-json">' +
    highlightJsonString(prettyJson) +
    "</code></pre>";
  if (lineCount > 10) {
    return '<details class="json-collapse" open><summary>JSON (' + lineCount + ' lines)</summary>' + block + '</details>';
  }
  return block;
}

function createCitationTokenStore() {
  var store = [];
  return {
    push: function(html) {
      var token = "@@CITE_LINK_" + store.length + "@@";
      store.push({ token: token, html: html });
      return token;
    },
    restore: function(text) {
      var restored = String(text || "");
      for (var i = 0; i < store.length; i += 1) {
        restored = restored.replaceAll(store[i].token, store[i].html);
      }
      return restored;
    },
  };
}

function buildDoiLink(doi) {
  var safeDoi = String(doi || "").trim();
  if (!safeDoi) return "";
  return (
    '<a href="https://doi.org/' + safeDoi + '" class="cite-link" target="_blank" rel="noreferrer noopener">DOI:' + safeDoi + "</a>" +
    '<a href="https://api.unpaywall.org/v2/' + encodeURIComponent(safeDoi) + '?email=jarvis@example.com" class="pdf-lookup" target="_blank" rel="noreferrer noopener" title="Check Unpaywall">📥</a>'
  );
}

function buildPmidLink(pmid) {
  var safePmid = String(pmid || "").trim();
  if (!safePmid) return "";
  return '<a href="https://pubmed.ncbi.nlm.nih.gov/' + safePmid + '" class="cite-link" target="_blank" rel="noreferrer noopener">PMID:' + safePmid + '</a>';
}

function linkifyCitations(text) {
  if (!text) return "";
  var citationTokens = createCitationTokenStore();
  var linked = String(text)
    .replace(/\bPMID:\s*(\d{4,9})\b/gi, function(_, pmid) {
      return citationTokens.push(buildPmidLink(pmid));
    })
    .replace(/\bDOI:\s*(10\.\d{4,9}\/[\-._;()/:A-Z0-9]+?)([.,;)\]]?)(?=\s|$)/gi, function(_, doi, trailing) {
      return citationTokens.push(buildDoiLink(doi)) + (trailing || "");
    })
    .replace(/\b(10\.\d{4,9}\/[\-._;()/:A-Z0-9]+?)([.,;)\]]?)(?=\s|$)/gi, function(_, doi, trailing) {
      return citationTokens.push(buildDoiLink(doi)) + (trailing || "");
    });

  return citationTokens.restore(linked);
}

function splitTrailingPunctuation(rawText) {
  var text = String(rawText || "");
  var trailing = "";
  while (/[.,;)\]]$/.test(text)) {
    trailing = text.slice(-1) + trailing;
    text = text.slice(0, -1);
  }
  return { text: text, trailing: trailing };
}

function isPdfCardCandidate(rawText) {
  var text = String(rawText || "");
  if (/^https?:\/\//i.test(text)) {
    return /\.pdf(?:$|[?#])/i.test(text);
  }
  if (/^[A-Za-z]:\\/.test(text)) {
    return /\\pdf-archive\\/i.test(text) && /\.pdf$/i.test(text);
  }
  if (/^\/?data\/pdf-archive\//i.test(text)) {
    return /\.pdf$/i.test(text);
  }
  return false;
}

function normalizePdfHref(rawText) {
  var text = String(rawText || "").trim();
  if (!text) return "";
  if (/^https?:\/\//i.test(text)) return text;
  if (/^\/?data\/pdf-archive\//i.test(text)) {
    return text.startsWith("/") ? text : "/" + text;
  }
  if (/^[A-Za-z]:\\/.test(text)) {
    return "file:///" + text.replaceAll("\\", "/");
  }
  return text;
}

function getPdfFilename(rawText) {
  var text = String(rawText || "").split("#")[0].split("?")[0].replaceAll("\\", "/");
  var parts = text.split("/");
  return parts[parts.length - 1] || "document.pdf";
}

function buildPdfCard(rawText) {
  var href = normalizePdfHref(rawText);
  var title = getPdfFilename(rawText);
  return (
    '<div class="pdf-card">' +
    '<span class="pdf-icon">📄</span>' +
    '<div class="pdf-info">' +
    '<span class="pdf-title">' + escapeHtml(title) + "</span>" +
    '<span class="pdf-size">PDF Document</span>' +
    "</div>" +
    '<div class="pdf-actions">' +
    '<a href="' + escapeHtml(href) + '" target="_blank" rel="noreferrer noopener" class="btn-pdf">Open</a>' +
    "</div>" +
    "</div>"
  );
}

function replacePdfCards(text) {
  if (!text) return "";
  var pattern = /https?:\/\/[^\s<>"']+|[A-Za-z]:\\[^\s<>"']+|\/data\/pdf-archive\/[^\s<>"']+|data\/pdf-archive\/[^\s<>"']+/gi;
  return String(text).replace(pattern, function(match) {
    var split = splitTrailingPunctuation(match);
    if (!isPdfCardCandidate(split.text)) return match;
    return buildPdfCard(split.text) + split.trailing;
  });
}

function replacePdfArchivedBadge(text) {
  if (!text) return "";
  var badge = '<span class="pdf-badge">📁 PDF Archived</span>';
  var withPhraseBadge = String(text).replace(/\bPDF archived\b/gi, badge);
  return withPhraseBadge.replace(/(^|[^\/\\\w-])(pdf-archive)(?=$|[^\/\\\w-])/gi, function(_, prefix) {
    return prefix + badge;
  });
}

/* ===== Markdown Rendering ===== */
function formatMarkdown(raw) {
  if (!raw) return "";
  var normalized = String(raw).replace(/\r\n/g, "\n");
  var codeBlocks = [];
  var withoutCode = normalized.replace(/```([^\n`]*)\n([\s\S]*?)```/g, function(_, rawLang, rawCode) {
    var lang = (rawLang || "").trim() || "plaintext";
    var code = String(rawCode || "");
    var jsonHtml = "";
    if (lang.toLowerCase() === "json" || (!rawLang && tryParseJson(code) !== null)) {
      jsonHtml = formatJsonBlock(code);
    }

    var highlighted = escapeHtml(code);
    if (!jsonHtml && typeof hljs !== "undefined" && lang !== "plaintext" && hljs.getLanguage(lang)) {
      try { highlighted = hljs.highlight(code, { language: lang }).value; } catch (e) {}
    }

    var html = jsonHtml || (
      '<div class="code-block-wrapper">' +
      '<div class="code-block-header"><span>' + escapeHtml(lang) + '</span>' +
      '<button class="code-copy-btn" onclick="copyCode(this)" type="button">copy</button></div>' +
      '<pre><code class="hljs language-' + escapeHtml(lang) + '">' + highlighted + '</code></pre></div>'
    );

    var token = "@@CODE_BLOCK_" + codeBlocks.length + "@@";
    codeBlocks.push({ token: token, html: html });
    return token;
  });

  if (!codeBlocks.length) {
    var standaloneJson = formatJsonBlock(withoutCode);
    if (standaloneJson) return standaloneJson;
  }

  var result = formatInlineText(withoutCode);
  for (var i = 0; i < codeBlocks.length; i += 1) {
    result = result.replaceAll(codeBlocks[i].token, codeBlocks[i].html);
  }

  return result;
}

function applyInlineMarkdownStyles(text) {
  if (!text) return "";
  var inlineCodeTokens = [];
  var withoutInlineCode = String(text).replace(/`([^`]+)`/g, function(_, code) {
    var token = "@@INLINE_CODE_" + inlineCodeTokens.length + "@@";
    inlineCodeTokens.push({ token: token, html: '<code class="inline-code">' + code + '</code>' });
    return token;
  });
  var styled = replacePdfCards(withoutInlineCode);
  styled = replacePdfArchivedBadge(styled);
  styled = linkifyCitations(styled).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  for (var i = 0; i < inlineCodeTokens.length; i += 1) {
    styled = styled.replaceAll(inlineCodeTokens[i].token, inlineCodeTokens[i].html);
  }
  return styled;
}

function formatInlineText(text) {
  if (!text) return "";
  var escaped = escapeHtml(text);
  var headingTokens = [];

  var tokenized = escaped.split("\n").map(function(line) {
    var h2 = line.match(/^##\s+(.+)$/);
    if (h2) {
      var h2Token = "@@MD_H2_" + headingTokens.length + "@@";
      headingTokens.push({ token: h2Token, html: '<h2 class="md-heading md-heading-h2">' + applyInlineMarkdownStyles(h2[1]) + "</h2>" });
      return h2Token;
    }

    var h3 = line.match(/^###\s+(.+)$/);
    if (h3) {
      var h3Token = "@@MD_H3_" + headingTokens.length + "@@";
      headingTokens.push({ token: h3Token, html: '<h3 class="md-heading md-heading-h3">' + applyInlineMarkdownStyles(h3[1]) + "</h3>" });
      return h3Token;
    }

    return line;
  }).join("\n");

  var formatted = applyInlineMarkdownStyles(tokenized).replace(/\n/g, "<br>");
  for (var i = 0; i < headingTokens.length; i += 1) {
    formatted = formatted.replace(headingTokens[i].token, headingTokens[i].html);
  }

  return formatted;
}

function getMarkdownHeadingLevel(node) {
  if (!node || node.nodeType !== 1 || !node.tagName) return 0;
  var tagName = node.tagName.toUpperCase();
  if (tagName === "H2") return 2;
  if (tagName === "H3") return 3;
  return 0;
}

function trimSectionBreaks(container) {
  if (!container) return;
  while (container.firstChild && container.firstChild.nodeType === 1 && container.firstChild.tagName.toUpperCase() === "BR") {
    container.removeChild(container.firstChild);
  }
  while (container.lastChild && container.lastChild.nodeType === 1 && container.lastChild.tagName.toUpperCase() === "BR") {
    container.removeChild(container.lastChild);
  }
}

function buildCollapsibleMarkdownSections(container) {
  if (!container) return;
  var children = Array.from(container.childNodes);
  var cursor = 0;

  while (cursor < children.length) {
    var node = children[cursor];
    var level = getMarkdownHeadingLevel(node);
    if (!level) {
      cursor += 1;
      continue;
    }

    var details = document.createElement("details");
    details.className = "markdown-section markdown-section-level-" + level;
    details.open = true;

    var summary = document.createElement("summary");
    summary.className = "markdown-section-summary";
    summary.innerHTML = node.innerHTML;
    details.appendChild(summary);

    var body = document.createElement("div");
    body.className = "markdown-section-body";
    var inner = document.createElement("div");
    inner.className = "markdown-section-body-inner";
    body.appendChild(inner);
    details.appendChild(body);

    container.insertBefore(details, node);
    node.remove();
    cursor += 1;

    while (cursor < children.length) {
      var candidate = children[cursor];
      var candidateLevel = getMarkdownHeadingLevel(candidate);
      if (candidateLevel && candidateLevel <= level) break;
      inner.appendChild(candidate);
      cursor += 1;
    }

    trimSectionBreaks(inner);
    if (level === 2) {
      buildCollapsibleMarkdownSections(inner);
    }
  }
}

function enhanceAssistantMarkdown(contentEl) {
  if (!contentEl) return;
  buildCollapsibleMarkdownSections(contentEl);
}

function normalizeReasoningKind(value) {
  var raw = String(value || "").trim().toLowerCase();
  if (!raw) return "Thinking";
  if (raw.indexOf("think") !== -1) return "Thinking";
  if (raw.indexOf("search") !== -1) return "Searching";
  if (raw.indexOf("analy") !== -1 || raw.indexOf("evidence") !== -1) return "Analyzing";
  if (raw.indexOf("read") !== -1 || raw.indexOf("browse") !== -1) return "Reading";
  if (raw.indexOf("generat") !== -1 || raw.indexOf("write") !== -1 || raw.indexOf("respond") !== -1) return "Generating";
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}

function getReasoningIcon(kind) {
  switch (normalizeReasoningKind(kind)) {
    case "Thinking": return "💭";
    case "Searching": return "🔍";
    case "Analyzing": return "📊";
    case "Reading": return "📖";
    case "Generating": return "✍️";
    default: return "⚡";
  }
}

function formatReasoningLabel(stepName) {
  var step = String(stepName || "").trim().toLowerCase();
  var labels = {
    thinking: "Thinking through the request",
    browse_url: "Reading URL content",
    semantic_search: "Searching semantic index",
    live_paper_search: "Searching live papers",
    evidence_grade: "Analyzing evidence strength",
    generate_response: "Generating response",
  };
  if (labels[step]) return labels[step];
  var humanized = step.split("_").filter(Boolean).map(function(part) {
    return part.charAt(0).toUpperCase() + part.slice(1);
  }).join(" ");
  return humanized || "Processing step";
}

function createReasoningTrace(steps) {
  var details = document.createElement("details");
  details.className = "reasoning-trace";
  details.open = true;

  var summary = document.createElement("summary");
  summary.innerHTML =
    '<span class="trace-icon">⚡</span>' +
    'Reasoning (<span class="trace-count">0</span> steps)' +
    '<span class="trace-time"></span>';
  details.appendChild(summary);

  var traceSteps = document.createElement("div");
  traceSteps.className = "trace-steps";
  details.appendChild(traceSteps);

  (steps || []).forEach(function(step) {
    if (step && step.node) traceSteps.appendChild(step.node);
  });

  return details;
}

function renderReasoningStep(step) {
  var node = document.createElement("div");
  node.className = "trace-step";
  node.innerHTML =
    '<span class="trace-step-icon">' + getReasoningIcon(step.kind) + '</span>' +
    '<span class="trace-step-text">' + escapeHtml(step.text) + '</span>' +
    '<span class="trace-step-time"></span>';
  step.node = node;
  return node;
}

function updateReasoningTraceMeta(bubble, totalMs) {
  if (!bubble || !bubble._reasoningTrace) return;
  var trace = bubble._reasoningTrace;
  var countEl = trace.querySelector(".trace-count");
  var timeEl = trace.querySelector(".trace-time");
  if (countEl) countEl.textContent = String((bubble._reasoningSteps || []).length);
  if (timeEl) timeEl.textContent = totalMs && totalMs > 0 ? formatElapsedTime(totalMs) : "";
}

function ensureReasoningTraceState(bubble) {
  if (!bubble) return null;
  if (!bubble._reasoningTrace) {
    bubble._reasoningTrace = createReasoningTrace([]);
    bubble._reasoningSteps = [];
    bubble._reasoningStartedAt = Date.now();
    bubble._reasoningLineBuffer = "";
    var contentEl = getMessageContentElement(bubble);
    bubble.insertBefore(bubble._reasoningTrace, contentEl);
  }
  return bubble._reasoningTrace;
}

function updateReasoningStepDuration(step) {
  if (!step || !step.node) return;
  var timeEl = step.node.querySelector(".trace-step-time");
  if (!timeEl) return;
  timeEl.textContent = step.durationMs ? formatElapsedTime(step.durationMs) : "";
}

function finalizeReasoningStep(step, endedAt, explicitDurationMs) {
  if (!step || step.endedAt) return;
  var finishedAt = Number.isFinite(endedAt) ? endedAt : Date.now();
  var computedDuration = explicitDurationMs;
  if (!Number.isFinite(computedDuration)) {
    computedDuration = Math.max(finishedAt - step.startedAt, 0);
  }
  step.endedAt = finishedAt;
  step.durationMs = computedDuration;
  updateReasoningStepDuration(step);
}

function getOpenReasoningStep(bubble, key) {
  if (!bubble || !bubble._reasoningSteps) return null;
  for (var i = bubble._reasoningSteps.length - 1; i >= 0; i -= 1) {
    var step = bubble._reasoningSteps[i];
    if (!step.endedAt && (!key || step.key === key)) return step;
  }
  return null;
}

function appendReasoningStep(stepPayload) {
  var bubble = ensureAssistantBubble();
  var trace = ensureReasoningTraceState(bubble);
  if (!trace) return null;
  var now = Date.now();
  var existing = stepPayload.key ? getOpenReasoningStep(bubble, stepPayload.key) : null;
  if (existing) return existing;

  var previous = getOpenReasoningStep(bubble);
  if (previous) finalizeReasoningStep(previous, now);

  var step = {
    key: stepPayload.key || ("step_" + bubble._reasoningSteps.length),
    kind: normalizeReasoningKind(stepPayload.kind),
    text: stepPayload.text || "Processing step",
    startedAt: now,
    durationMs: 0,
    endedAt: null,
    node: null,
  };
  bubble._reasoningSteps.push(step);
  renderReasoningStep(step);
  var container = trace.querySelector(".trace-steps");
  if (container) container.appendChild(step.node);
  updateReasoningTraceMeta(bubble, now - bubble._reasoningStartedAt);
  return step;
}

function handleReasoningActivity(payload) {
  if (!payload || (!payload.step && !payload.type)) return;
  var bubble = ensureAssistantBubble();
  var kind = normalizeReasoningKind(payload.type || payload.step);
  var label = payload.message || payload.text || formatReasoningLabel(payload.step || payload.type);
  var key = String(payload.step || payload.type || label).trim().toLowerCase();

  if (payload.status === "running" || !payload.status) {
    appendReasoningStep({ key: key, kind: kind, text: label });
    return;
  }

  var durationMs = parseDurationMs(payload.time);
  var step = getOpenReasoningStep(bubble, key);
  if (!step) {
    step = appendReasoningStep({ key: key, kind: kind, text: label });
  }
  finalizeReasoningStep(step, Date.now(), durationMs);
  updateReasoningTraceMeta(bubble, Date.now() - bubble._reasoningStartedAt);
}

function consumeReasoningDelta(content) {
  if (!content) return;
  var bubble = ensureAssistantBubble();
  if (typeof bubble._reasoningLineBuffer !== "string") bubble._reasoningLineBuffer = "";
  bubble._reasoningLineBuffer += String(content);
  var lines = bubble._reasoningLineBuffer.split(/\r?\n/);
  bubble._reasoningLineBuffer = lines.pop() || "";

  lines.forEach(function(line) {
    var match = line.trim().match(/^(Thinking|Searching|Analyzing|Reading|Generating):\s*(.+)$/i);
    if (!match) return;
    appendReasoningStep({
      key: "line_" + match[1].toLowerCase() + "_" + ((bubble._reasoningSteps || []).length),
      kind: match[1],
      text: match[2] || match[1],
    });
  });
}

function finalizeReasoningTrace(bubble) {
  if (!bubble) return;
  var trailingLine = String(bubble._reasoningLineBuffer || "").trim();
  if (trailingLine) {
    var trailingMatch = trailingLine.match(/^(Thinking|Searching|Analyzing|Reading|Generating):\s*(.+)$/i);
    if (trailingMatch) {
      appendReasoningStep({
        key: "line_" + trailingMatch[1].toLowerCase() + "_" + ((bubble._reasoningSteps || []).length),
        kind: trailingMatch[1],
        text: trailingMatch[2] || trailingMatch[1],
      });
    }
    bubble._reasoningLineBuffer = "";
  }
  if (!bubble._reasoningTrace || !bubble._reasoningSteps || !bubble._reasoningSteps.length) return;
  var endedAt = Date.now();
  var openStep = getOpenReasoningStep(bubble);
  if (openStep) finalizeReasoningStep(openStep, endedAt);
  updateReasoningTraceMeta(bubble, endedAt - bubble._reasoningStartedAt);
}

window.copyCode = function(btn) {
  var wrapper = btn.closest(".code-block-wrapper");
  var code = wrapper.querySelector("code");
  navigator.clipboard.writeText(code.innerText || code.textContent).then(function() {
    btn.textContent = "copied!";
    setTimeout(function() { btn.textContent = "copy"; }, 2000);
  });
};

/* ===== Badges ===== */
function ensureResearchBadge() {
  var badge = document.querySelector("#research-mode-badge");
  if (!badge) {
    badge = document.createElement("span");
    badge.id = "research-mode-badge";
    badge.textContent = "Research Mode";
    badge.hidden = true;
    badge.style.cssText = "margin-left:10px;padding:2px 8px;border-radius:999px;border:1px solid rgba(212,160,23,0.32);background:rgba(140,102,21,0.24);color:#f0d060;font-size:0.75rem;font-weight:600;";
    elements.currentModelLabel.insertAdjacentElement("afterend", badge);
  }
  return badge;
}

function syncResearchBadge() { ensureResearchBadge().hidden = !state.researchMode; }

function ensureCopilotBadge() {
  var badge = document.querySelector("#copilot-status-badge");
  if (!badge) {
    badge = document.createElement("div");
    badge.id = "copilot-status-badge";
    badge.style.cssText = "margin-top:0.75rem;padding:0.55rem 0.75rem;border-radius:12px;font-size:0.8rem;font-weight:600;line-height:1.4;";
    elements.modelSelector.insertAdjacentElement("afterend", badge);
  }
  return badge;
}

function syncCopilotBadge() {
  var badge = ensureCopilotBadge();
  if (state.copilotConnected) {
    badge.textContent = "\u2728 Copilot Connected";
    badge.style.color = "#b9ffd1";
    badge.style.background = "rgba(38,120,77,0.24)";
    badge.style.border = "1px solid rgba(87,214,135,0.35)";
  } else {
    badge.textContent = "Copilot Offline - LiteLLM Fallback";
    badge.style.color = "#ffe7a8";
    badge.style.background = "rgba(140,102,21,0.2)";
    badge.style.border = "1px solid rgba(244,196,48,0.35)";
  }
}

/* ===== Model Selector ===== */
function renderModelSelector(models) {
  var select = elements.modelSelector;
  if (!select) return;
  select.innerHTML = "";
  var tiers = { pro: [], "pro+": [], unknown: [], local: [] };
  for (var m of models) { (tiers[m.tier] || tiers.unknown).push(m); }

  function addGroup(label, list, locked) {
    if (!list.length) return;
    var group = document.createElement("optgroup");
    group.label = label;
    for (var m of list) {
      var opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = locked ? "\u26A0 " + m.id + " (Pro+)" : (m.name || m.id);
      if (locked) { opt.style.color = "#666"; opt.style.fontStyle = "italic"; }
      if (m.default) opt.selected = true;
      group.appendChild(opt);
    }
    select.appendChild(group);
  }

  addGroup("\u2728 Copilot Pro", tiers.pro, false);
  addGroup("Unverified", tiers.unknown, false);
  addGroup("\u26A0 Pro+ (/mo)", tiers["pro+"], true);
  addGroup("Local Fallback", tiers.local, false);

  if (!select.value) {
    for (var p of ["claude-sonnet-4.6", "gpt-4.1", "o4-mini"]) {
      var opt = select.querySelector('option[value="' + p + '"]');
      if (opt) { select.value = p; break; }
    }
  }
}

/* ===== Usage ===== */
function ensureUsageDisplay() {
  if (document.getElementById("usage-display")) return;
  var sidebar = document.getElementById("sidebar");
  if (!sidebar) return;
  var ref = sidebar.querySelector("[id*='copilot-status']") || sidebar.querySelector("button");
  var div = document.createElement("div");
  div.id = "usage-display";
  div.innerHTML =
    '<div style="margin-top:10px;padding:8px 12px;background:rgba(20,20,40,0.8);border:1px solid rgba(212,160,23,0.1);border-radius:12px;font-size:12px;">' +
    '<div style="color:var(--accent-primary);margin-bottom:4px;font-weight:bold;letter-spacing:1px;">\u2728 COPILOT USAGE</div>' +
    '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">' +
    '<span style="color:#e0e0e0;">Premium Requests</span>' +
    '<span id="usage-percent" style="color:#e0e0e0;">--</span></div>' +
    '<div style="background:#2a2a3e;border-radius:4px;height:6px;overflow:hidden;">' +
    '<div id="usage-bar" style="height:100%;width:0%;background:var(--success);border-radius:4px;transition:width 0.5s;"></div></div></div>';
  if (ref && ref.parentNode) ref.parentNode.insertBefore(div, ref.nextSibling);
  else sidebar.appendChild(div);
}

async function updateUsage() {
  ensureUsageDisplay();
  try {
    var res = await fetch("/api/usage");
    var data = await res.json();
    var percentEl = document.getElementById("usage-percent");
    var barEl = document.getElementById("usage-bar");
    state.copilotConnected = Boolean(data.available);
    syncCopilotBadge();
    if (data.available) {
      var percent = 0;
      var raw = JSON.stringify(data);
      var pm = raw.match(/"percentage"\s*:\s*([\d.]+)/);
      if (pm) percent = parseFloat(pm[1]);
      if (data.copilot_usage?.premium_requests?.percentage !== undefined) percent = data.copilot_usage.premium_requests.percentage;
      if (data.percentage !== undefined) percent = data.percentage;
      if (data.chat?.percentage !== undefined) percent = data.chat.percentage;
      if (percentEl) percentEl.textContent = percent.toFixed(1) + "%";
      if (barEl) {
        barEl.style.width = Math.min(percent, 100) + "%";
        barEl.style.background = percent > 80 ? "#ef4444" : percent > 50 ? "#eab308" : "var(--success)";
      }
    } else {
      if (percentEl) percentEl.textContent = "N/A";
      if (barEl) barEl.style.width = "0%";
    }
  } catch (e) {}
}

/* ===== Inline Activity ===== */
function ensureInlineActivity() {
  if (state.inlineActivityEl) return state.inlineActivityEl;
  var block = document.createElement("div");
  block.className = "inline-activity";
  block.innerHTML =
    '<div class="inline-activity-header">' +
    '<span class="inline-activity-title">\u2728 Agent Activity</span>' +
    '<span class="inline-activity-status" id="inline-status">running</span></div>' +
    '<div class="inline-activity-timeline" id="inline-timeline"></div>';
  elements.chatMessages.appendChild(block);
  state.inlineActivityEl = block;
  scrollChatToBottom();
  return block;
}

function upsertActivity(step, status, time, extra) {
  ensureInlineActivity();
  if (status === "running") state.activityStartedAt.set(step, Date.now());
  var timeline = document.getElementById("inline-timeline");
  var node = state.activityItems.get(step);
  if (!node) {
    node = document.createElement("div");
    node.className = "inline-activity-item activity-item " + status;
    node.innerHTML = '<span class="ia-dot activity-dot"></span><div class="ia-content"><div class="ia-title"></div><div class="ia-meta"></div></div>';
    state.activityItems.set(step, node);
    timeline.appendChild(node);
  }
  node.className = "inline-activity-item activity-item " + status;
  var dot = node.querySelector(".activity-dot");
  if (dot) dot.className = "ia-dot activity-dot " + status;
  var label = step.split("_").map(function(t) { return t.charAt(0).toUpperCase() + t.slice(1); }).join(" ");
  node.querySelector(".ia-title").textContent = label;
  var elapsed = time || "";
  if (!elapsed && state.activityStartedAt.has(step)) elapsed = (Date.now() - state.activityStartedAt.get(step)) + "ms";
  node.querySelector(".ia-meta").textContent = [status, elapsed, extra || ""].filter(Boolean).join(" \u00B7 ");
  scrollChatToBottom();
}

function renderToolCall(payload) {
  ensureInlineActivity();
  var timeline = document.getElementById("inline-timeline");
  var details = document.createElement("details");
  details.className = "inline-activity-item activity-item done";
  var preview = String(payload.result || "").slice(0, 200);
  details.innerHTML =
    '<summary style="display:flex;align-items:center;gap:8px;cursor:pointer;">' +
    '<span class="ia-dot activity-dot done"></span>' +
    '<span class="ia-title">\u2728 [tool] ' + escapeHtml(payload.name || "tool_call") + '</span></summary>' +
    '<div class="ia-meta" style="margin-left:20px;">' + escapeHtml(payload.time || "") + '</div>' +
    '<div style="margin:4px 0 0 20px;font-size:0.8rem;color:var(--text-muted);white-space:pre-wrap;word-break:break-word;">' + escapeHtml(preview) + '</div>';
  timeline.appendChild(details);
  scrollChatToBottom();
}

function finalizeInlineActivity() {
  var statusEl = document.getElementById("inline-status");
  if (statusEl) { statusEl.textContent = "done"; statusEl.className = "inline-activity-status done"; }
}

function resetActivity() {
  state.activityItems.clear();
  state.activityStartedAt.clear();
  state.researchMode = false;
  if (state.inlineActivityEl && state.inlineActivityEl.parentElement) {
    state.inlineActivityEl.remove();
  }
  state.inlineActivityEl = null;
  syncResearchBadge();
}

/* ===== Message Rendering ===== */
function setStreaming(v) {
  state.isStreaming = v;
  elements.sendButton.disabled = v;
}

function getMessageContentElement(bubble) {
  if (!bubble) return null;
  var contentEl = bubble.querySelector(".message-content");
  if (contentEl) return contentEl;
  contentEl = document.createElement("div");
  contentEl.className = "message-content";
  contentEl.innerHTML = bubble.innerHTML;
  bubble.innerHTML = "";
  bubble.appendChild(contentEl);
  return contentEl;
}

function wrapTextSliceWithClass(node, start, end, className) {
  if (!node || !node.parentNode) return false;
  var text = node.nodeValue || "";
  if (start < 0 || end > text.length || start >= end) return false;
  var before = text.slice(0, start);
  var middle = text.slice(start, end);
  var after = text.slice(end);
  var fragment = document.createDocumentFragment();
  if (before) fragment.appendChild(document.createTextNode(before));
  var marker = document.createElement("span");
  marker.className = className;
  marker.textContent = middle;
  fragment.appendChild(marker);
  if (after) fragment.appendChild(document.createTextNode(after));
  node.parentNode.replaceChild(fragment, node);
  return true;
}

function applyStreamingTextReveal(bubble, contentEl, addedLength) {
  if (!bubble || !contentEl) return;
  if (bubble._textRevealTimer) clearTimeout(bubble._textRevealTimer);
  var remaining = Number(addedLength) || 0;
  var nodes = [];
  var walker = document.createTreeWalker(contentEl, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (var i = nodes.length - 1; i >= 0 && remaining > 0; i -= 1) {
    var node = nodes[i];
    var len = (node.nodeValue || "").length;
    if (!len) continue;
    var take = Math.min(len, remaining);
    var start = len - take;
    var applied = wrapTextSliceWithClass(node, start, len, "text-reveal");
    if (applied) remaining -= take;
  }
  if (remaining > 0) contentEl.classList.add("text-reveal");
  bubble._textRevealTimer = setTimeout(function() {
    var highlighted = contentEl.querySelectorAll(".text-reveal");
    for (var mark of highlighted) mark.classList.remove("text-reveal");
    contentEl.classList.remove("text-reveal");
    bubble._textRevealTimer = null;
  }, 300);
}

function renderMessage(role, content) {
  var bubble = document.createElement("article");
  bubble.className = "message message-bubble " + role;
  var contentEl = document.createElement("div");
  contentEl.className = "message-content";
  contentEl.innerHTML = formatMarkdown(content);
  if (role === "assistant") {
    enhanceAssistantMarkdown(contentEl);
  }
  bubble.appendChild(contentEl);
  bubble.dataset.renderedTextLength = String((contentEl.textContent || "").length);
  elements.chatMessages.appendChild(bubble);
  scrollChatToBottom();
  return bubble;
}

function renderEmptyState(msg) {
  elements.chatMessages.innerHTML = '<div class="empty-state">' + msg + '</div>';
}

function showToast(msg) {
  var t = document.createElement("div");
  t.className = "toast";
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function() { t.remove(); }, 3000);
}

async function fetchJson(url, opts) {
  var r = await fetch(url, opts || {});
  if (!r.ok) throw new Error(r.status + " " + r.statusText);
  return r.json();
}

/* ===== Memory ===== */
var memoryState = {
  bindingsApplied: false,
};

function renderFactsList(facts) {
  var listEl = document.getElementById("facts-list");
  if (!listEl) return;

  if (!Array.isArray(facts) || !facts.length) {
    listEl.innerHTML = '<li class="pipeline-empty-row">No facts yet.</li>';
    return;
  }

  listEl.innerHTML = facts.map(function(fact) {
    var key = String(fact && fact.key ? fact.key : "").trim();
    var value = String(fact && fact.value ? fact.value : "").trim();
    var category = String(fact && fact.category ? fact.category : "general").trim() || "general";
    var encodedKey = encodeURIComponent(key);

    return (
      '<li class="memory-list-item">' +
        '<div class="memory-item-main">' +
          '<div class="memory-item-key">' + escapeHtml(key || "-") + "</div>" +
          '<div class="memory-item-value">' + escapeHtml(value || "-") + "</div>" +
          '<div class="memory-item-meta">Category: ' + escapeHtml(category) + "</div>" +
        "</div>" +
        '<button type="button" class="btn-gold memory-delete-btn" data-delete-fact-key="' + encodedKey + '">🗑️</button>' +
      "</li>"
    );
  }).join("");
}

function renderPreferencesList(preferences) {
  var listEl = document.getElementById("prefs-list");
  if (!listEl) return;

  var entries = Object.entries(preferences || {});
  if (!entries.length) {
    listEl.innerHTML = '<li class="pipeline-empty-row">No preferences yet.</li>';
    return;
  }

  listEl.innerHTML = entries.map(function(entry) {
    var key = String(entry[0] || "").trim();
    var value = String(entry[1] || "").trim();
    return (
      '<li class="memory-list-item">' +
        '<div class="memory-item-main">' +
          '<div class="memory-item-key">' + escapeHtml(key || "-") + "</div>" +
          '<div class="memory-item-value">' + escapeHtml(value || "-") + "</div>" +
        "</div>" +
      "</li>"
    );
  }).join("");
}

function renderMemoryContext(contextText) {
  var contextEl = document.getElementById("memory-context");
  if (!contextEl) return;
  var safeContext = String(contextText || "").trim();
  contextEl.textContent = safeContext || "No context available.";
}

async function fetchMemoryFacts() {
  try {
    return await fetchJson("/api/memory/facts");
  } catch (error) {
    showToast("Failed to load memory facts: " + (error.message || "unknown"));
    return [];
  }
}

async function fetchMemoryPreferences() {
  try {
    return await fetchJson("/api/memory/preferences");
  } catch (error) {
    showToast("Failed to load preferences: " + (error.message || "unknown"));
    return {};
  }
}

async function fetchMemoryContext() {
  try {
    var contextPayload = await fetchJson("/api/memory/context");
    return contextPayload && contextPayload.context ? contextPayload.context : "";
  } catch (error) {
    showToast("Failed to load memory context: " + (error.message || "unknown"));
    return "";
  }
}

async function loadMemoryPanel() {
  var factsEl = document.getElementById("facts-list");
  if (factsEl) factsEl.innerHTML = '<li class="pipeline-empty-row">Loading facts...</li>';
  var prefsEl = document.getElementById("prefs-list");
  if (prefsEl) prefsEl.innerHTML = '<li class="pipeline-empty-row">Loading preferences...</li>';
  renderMemoryContext("Loading memory context...");

  var data = await Promise.all([
    fetchMemoryFacts(),
    fetchMemoryPreferences(),
    fetchMemoryContext(),
  ]);

  renderFactsList(data[0]);
  renderPreferencesList(data[1]);
  renderMemoryContext(data[2]);
}

async function deleteMemoryFactByKey(key) {
  try {
    await fetchJson("/api/memory/facts/" + encodeURIComponent(key), {
      method: "DELETE",
    });
    return true;
  } catch (error) {
    showToast("Failed to delete fact: " + (error.message || "unknown"));
    return false;
  }
}

async function addMemoryFact(payload) {
  try {
    await fetchJson("/api/memory/facts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return true;
  } catch (error) {
    showToast("Failed to add fact: " + (error.message || "unknown"));
    return false;
  }
}

async function addMemoryPreference(payload) {
  try {
    await fetchJson("/api/memory/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return true;
  } catch (error) {
    showToast("Failed to add preference: " + (error.message || "unknown"));
    return false;
  }
}

async function handleAddFactSubmit(event) {
  event.preventDefault();
  var form = event.currentTarget;
  var keyInput = form.querySelector('[name="key"]');
  var valueInput = form.querySelector('[name="value"]');
  var categoryInput = form.querySelector('[name="category"]');

  var payload = {
    key: keyInput ? keyInput.value.trim() : "",
    value: valueInput ? valueInput.value.trim() : "",
    category: categoryInput ? categoryInput.value.trim() : "",
  };

  if (!payload.key || !payload.value) {
    showToast("Fact key and value are required.");
    return;
  }

  var ok = await addMemoryFact(payload);
  if (!ok) return;

  form.reset();
  showToast("Fact added.");
  await loadMemoryPanel();
}

async function handleAddPreferenceSubmit(event) {
  event.preventDefault();
  var form = event.currentTarget;
  var keyInput = form.querySelector('[name="key"]');
  var valueInput = form.querySelector('[name="value"]');

  var payload = {
    key: keyInput ? keyInput.value.trim() : "",
    value: valueInput ? valueInput.value.trim() : "",
  };

  if (!payload.key || !payload.value) {
    showToast("Preference key and value are required.");
    return;
  }

  var ok = await addMemoryPreference(payload);
  if (!ok) return;

  form.reset();
  showToast("Preference added.");
  await loadMemoryPanel();
}

function bindMemoryPanelEvents() {
  if (memoryState.bindingsApplied) return;
  memoryState.bindingsApplied = true;

  var factsList = document.getElementById("facts-list");
  if (factsList) {
    factsList.addEventListener("click", function(event) {
      var target = event.target.closest("[data-delete-fact-key]");
      if (!target) return;

      var encodedKey = target.getAttribute("data-delete-fact-key") || "";
      var factKey = "";
      try {
        factKey = decodeURIComponent(encodedKey);
      } catch (error) {
        showToast("Failed to decode fact key.");
        return;
      }

      if (!factKey) return;
      deleteMemoryFactByKey(factKey).then(function(ok) {
        if (!ok) return;
        loadMemoryPanel().catch(function(error) {
          showToast("Failed to refresh memory panel: " + (error.message || "unknown"));
        });
      });
    });
  }

  var addFactForm = document.getElementById("add-fact-form");
  if (addFactForm) {
    addFactForm.addEventListener("submit", function(event) {
      handleAddFactSubmit(event).catch(function(error) {
        showToast("Failed to submit fact: " + (error.message || "unknown"));
      });
    });
  }

  var addPrefForm = document.getElementById("add-pref-form");
  if (addPrefForm) {
    addPrefForm.addEventListener("submit", function(event) {
      handleAddPreferenceSubmit(event).catch(function(error) {
        showToast("Failed to submit preference: " + (error.message || "unknown"));
      });
    });
  }
}

/* ===== Pipeline ===== */
const PIPELINE_TOTAL_STEPS = 7;
const pipelineState = {
  eventSource: null,
  running: false,
  historyLoaded: false,
};

const pipelineStepDefaults = [
  "Waiting for search start...",
  "Waiting for deduplication...",
  "Waiting for relevance scoring...",
  "Waiting for ranking...",
  "Waiting for Gemini summarization...",
  "Waiting for output formatting...",
  "Waiting for file save...",
];

function getPipelineStepCards() {
  return Array.from(document.querySelectorAll(".pipeline-step-card"));
}

function clampNumber(value, min, max) {
  return Math.min(Math.max(Number(value) || 0, min), max);
}

function setPipelineRunButtonState(running) {
  var btn = document.getElementById("pipeline-run-btn");
  if (!btn) return;
  btn.disabled = Boolean(running);
  btn.textContent = running ? "Running..." : "Run";
}

function setPipelineStatusMessage(message, type) {
  var statusEl = document.getElementById("pipeline-status-message");
  if (!statusEl) return;
  statusEl.classList.remove("error", "success");
  if (type) statusEl.classList.add(type);
  statusEl.textContent = message || "";
}

function renderPipelineEmptyResults(message) {
  var body = document.getElementById("pipeline-results-body");
  if (!body) return;
  var rowMessage = message || "No results yet.";
  body.innerHTML =
    '<tr><td colspan="5" class="pipeline-empty-row">' + escapeHtml(rowMessage) + '</td></tr>';
}

function resetPipelineSteps() {
  var cards = getPipelineStepCards();
  for (var i = 0; i < cards.length; i += 1) {
    var card = cards[i];
    card.classList.remove("active", "completed");

    var messageEl = card.querySelector("[data-step-message]");
    if (messageEl) {
      messageEl.textContent = pipelineStepDefaults[i] || "Waiting for progress...";
    }

    var fillEl = card.querySelector("[data-step-fill]");
    if (fillEl) {
      fillEl.style.width = "0%";
    }

    var percentEl = card.querySelector("[data-step-percent]");
    if (percentEl) {
      percentEl.textContent = "0%";
    }
  }
}

function deriveStepLocalProgress(step, globalProgress) {
  var current = clampNumber(step, 1, PIPELINE_TOTAL_STEPS);
  var progress = clampNumber(globalProgress, 0, 100);
  var start = ((current - 1) / PIPELINE_TOTAL_STEPS) * 100;
  var end = (current / PIPELINE_TOTAL_STEPS) * 100;
  if (progress <= start) return 0;
  if (progress >= end) return 100;
  return clampNumber(((progress - start) / (end - start)) * 100, 0, 100);
}

function updatePipelineSteps(step, progress, message) {
  var currentStep = clampNumber(step, 1, PIPELINE_TOTAL_STEPS);
  var safeProgress = clampNumber(progress, 0, 100);
  var cards = getPipelineStepCards();

  for (var i = 0; i < cards.length; i += 1) {
    var card = cards[i];
    var cardStep = i + 1;
    var fillEl = card.querySelector("[data-step-fill]");
    var percentEl = card.querySelector("[data-step-percent]");

    card.classList.toggle("active", cardStep === currentStep && safeProgress < 100);
    card.classList.toggle("completed", cardStep < currentStep);

    var stepProgress = 0;
    if (cardStep < currentStep) {
      stepProgress = 100;
    } else if (cardStep === currentStep) {
      stepProgress = deriveStepLocalProgress(currentStep, safeProgress);
      if (safeProgress >= 100) {
        card.classList.remove("active");
        card.classList.add("completed");
        stepProgress = 100;
      }
    }

    if (fillEl) fillEl.style.width = stepProgress.toFixed(1) + "%";
    if (percentEl) percentEl.textContent = Math.round(stepProgress) + "%";
  }

  var activeCard = document.querySelector('.pipeline-step-card[data-step="' + currentStep + '"]');
  if (activeCard) {
    var messageEl = activeCard.querySelector("[data-step-message]");
    if (messageEl && message) {
      messageEl.textContent = message;
    }
  }
}

function normalizePipelineUrl(rawUrl) {
  if (!rawUrl) return "";
  var text = String(rawUrl).trim();
  if (!text) return "";
  if (text.startsWith("http://") || text.startsWith("https://")) return text;
  if (text.startsWith("10.")) return "https://doi.org/" + text;
  return "";
}

function normalizePipelineAuthors(rawAuthors) {
  if (Array.isArray(rawAuthors)) return rawAuthors.join(", ");
  if (rawAuthors === null || rawAuthors === undefined) return "-";
  var text = String(rawAuthors).trim();
  return text || "-";
}

function normalizePipelineScore(rawScore) {
  if (!Number.isFinite(Number(rawScore))) return "-";
  return Number(rawScore).toFixed(1);
}

function renderPipelineResults(papers) {
  var body = document.getElementById("pipeline-results-body");
  if (!body) return;
  body.innerHTML = "";

  if (!Array.isArray(papers) || !papers.length) {
    renderPipelineEmptyResults("No papers returned by pipeline.");
    return;
  }

  for (var paper of papers) {
    var row = document.createElement("tr");

    var titleCell = document.createElement("td");
    var authorsCell = document.createElement("td");
    var yearCell = document.createElement("td");
    var sourceCell = document.createElement("td");
    var scoreCell = document.createElement("td");

    var title = paper.title ? String(paper.title) : "-";
    var url = normalizePipelineUrl(paper.url || paper.link || paper.doi);
    if (url) {
      var link = document.createElement("a");
      link.className = "pipeline-results-title-link";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.href = url;
      link.textContent = title;
      titleCell.appendChild(link);
    } else {
      titleCell.textContent = title;
    }

    authorsCell.textContent = normalizePipelineAuthors(paper.authors);
    yearCell.textContent = paper.year ? String(paper.year) : "-";
    sourceCell.textContent = paper.source || paper.journal || "-";
    scoreCell.textContent = normalizePipelineScore(paper.score);

    row.appendChild(titleCell);
    row.appendChild(authorsCell);
    row.appendChild(yearCell);
    row.appendChild(sourceCell);
    row.appendChild(scoreCell);
    body.appendChild(row);

    if (paper.summary) {
      var summaryRow = document.createElement("tr");
      var summaryCell = document.createElement("td");
      summaryCell.colSpan = 5;
      summaryCell.style.cssText = "padding:8px 16px;color:#aaa;font-size:0.85em;border-bottom:1px solid #333;background:#0d0d0d;";
      summaryCell.textContent = paper.summary;
      summaryRow.appendChild(summaryCell);
      body.appendChild(summaryRow);
    }
  }
}

function formatPipelineHistoryDate(rawDate) {
  if (!rawDate) return "--";
  var parsed = new Date(rawDate);
  if (Number.isNaN(parsed.getTime())) return String(rawDate);
  return parsed.toLocaleString("ja-JP");
}

function renderPipelineHistory(items) {
  var list = document.getElementById("pipeline-history-list");
  if (!list) return;
  list.innerHTML = "";

  if (!Array.isArray(items) || !items.length) {
    list.innerHTML = '<li class="pipeline-empty-row">No history yet.</li>';
    return;
  }

  for (var item of items) {
    var li = document.createElement("li");
    li.className = "pipeline-history-item";
    li.innerHTML =
      '<div><div class="pipeline-history-query">' + escapeHtml(item.query || "(unknown query)") + '</div>' +
      '<div class="pipeline-history-meta">' + escapeHtml(formatPipelineHistoryDate(item.date)) + '</div></div>' +
      '<div class="pipeline-history-meta">Papers: ' + escapeHtml(String(item.paperCount ?? "-")) + '</div>';
    list.appendChild(li);
  }
}

async function loadPipelineHistory(force) {
  if (pipelineState.historyLoaded && !force) return;
  try {
    var history = await fetchJson("/api/pipeline/history");
    renderPipelineHistory(history);
    pipelineState.historyLoaded = true;
  } catch (error) {
    renderPipelineHistory([]);
    setPipelineStatusMessage("Failed to load history: " + error.message, "error");
  }
}

function buildPipelineFileCandidates(filePath) {
  var raw = String(filePath || "").trim().replace(/\\/g, "/");
  if (!raw) return [];

  var normalized = raw.replace(/^\/+/, "").replace(/^\.\//, "");
  var candidates = [];

  function addCandidate(url) {
    if (!url || candidates.includes(url)) return;
    candidates.push(url);
  }

  addCandidate("/" + normalized);

  if (normalized.startsWith("agent-web/")) {
    addCandidate("/" + normalized.slice("agent-web/".length));
  }

  if (normalized.startsWith("data/")) {
    addCandidate("/" + normalized);
  }

  var dataIndex = normalized.indexOf("data/");
  if (dataIndex >= 0) {
    addCandidate("/" + normalized.slice(dataIndex));
  }

  var filename = normalized.split("/").pop();
  if (filename) {
    addCandidate("/data/" + filename);
  }

  return candidates;
}

async function fetchPipelineResultFile(filePath) {
  var candidates = buildPipelineFileCandidates(filePath);
  var lastError = null;

  for (var candidate of candidates) {
    try {
      var response = await fetch(candidate, { cache: "no-store" });
      if (!response.ok) {
        lastError = new Error(response.status + " " + response.statusText);
        continue;
      }
      var payload = await response.json();
      if (payload && Array.isArray(payload.papers)) {
        return payload;
      }
      lastError = new Error("Result file payload missing papers array");
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error("Unable to fetch pipeline result file");
}

function stopPipelineStream() {
  if (pipelineState.eventSource) {
    pipelineState.eventSource.close();
    pipelineState.eventSource = null;
  }
  pipelineState.running = false;
  setPipelineRunButtonState(false);
}

async function handlePipelineMessage(payload, sourceRef) {
  if (pipelineState.eventSource !== sourceRef) return;

  if (payload.error) {
    setPipelineStatusMessage("Pipeline error: " + payload.error, "error");
    stopPipelineStream();
    return;
  }

  if (payload.done) {
    updatePipelineSteps(PIPELINE_TOTAL_STEPS, 100, "Pipeline completed.");
    var summary = "Completed: " + String(payload.paperCount ?? 0) + " papers";
    setPipelineStatusMessage(summary, "success");

    var rendered = false;
    if (payload.file) {
      try {
        var resultFile = await fetchPipelineResultFile(payload.file);
        renderPipelineResults(resultFile.papers || []);
        rendered = true;
      } catch (error) {
        renderPipelineEmptyResults("Completed, but failed to load results file.");
        setPipelineStatusMessage(summary + " (result fetch failed)", "error");
      }
    }

    if (!rendered) {
      renderPipelineEmptyResults("Completed. Result details are not available from API response.");
    }

    pipelineState.historyLoaded = false;
    await loadPipelineHistory(true);
    stopPipelineStream();
    return;
  }

  if (typeof payload.step === "number") {
    updatePipelineSteps(payload.step, payload.progress, payload.message || "Running...");
    setPipelineStatusMessage(payload.message || ("Step " + payload.step + " in progress"));
  }
}

function runPipelineQuery(query) {
  var trimmedQuery = String(query || "").trim();
  if (!trimmedQuery || pipelineState.running) return;

  stopPipelineStream();
  pipelineState.running = true;
  setPipelineRunButtonState(true);
  resetPipelineSteps();
  renderPipelineEmptyResults("Pipeline running...");
  setPipelineStatusMessage("Running pipeline for: " + trimmedQuery);

  var streamUrl = "/api/pipeline/run?query=" + encodeURIComponent(trimmedQuery) + "&limit=50";
  var eventSource = new EventSource(streamUrl);
  pipelineState.eventSource = eventSource;

  eventSource.onmessage = function(event) {
    if (pipelineState.eventSource !== eventSource) return;
    try {
      var payload = JSON.parse(event.data);
      Promise.resolve(handlePipelineMessage(payload, eventSource)).catch(function(error) {
        setPipelineStatusMessage("Pipeline error: " + error.message, "error");
        stopPipelineStream();
      });
    } catch (error) {
      setPipelineStatusMessage("Invalid stream payload", "error");
      stopPipelineStream();
    }
  };

  eventSource.onerror = function() {
    if (pipelineState.eventSource !== eventSource) return;
    setPipelineStatusMessage("Pipeline stream disconnected.", "error");
    stopPipelineStream();
  };
}

function bindPipelineEvents() {
  var form = document.getElementById("pipeline-form");
  var queryInput = document.getElementById("pipeline-query-input");
  var refreshBtn = document.getElementById("pipeline-refresh-history-btn");

  if (form && queryInput) {
    form.addEventListener("submit", function(event) {
      event.preventDefault();
      var query = queryInput.value.trim();
      if (!query) {
        setPipelineStatusMessage("Query is required.", "error");
        return;
      }
      runPipelineQuery(query);
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", function() {
      pipelineState.historyLoaded = false;
      loadPipelineHistory(true);
    });
  }
}

function initializePipelineUI() {
  resetPipelineSteps();
  renderPipelineEmptyResults("No results yet.");
  setPipelineStatusMessage("Enter a query and run the pipeline.");
  setPipelineRunButtonState(false);
}
/* ===== Session Management ===== */
function renderSessionList(sessions) {
  elements.sessionHistory.innerHTML = "";
  if (!sessions.length) {
    elements.sessionHistory.innerHTML = '<div class="empty-state">No sessions yet</div>';
    return;
  }
  for (var s of sessions) {
    var item = document.createElement("button");
    item.type = "button";
    item.className = "session-item " + (s.id === state.currentSessionId ? "active" : "");
    item.innerHTML =
      '<div class="session-title-row"><div>' +
      '<div class="session-title">' + escapeHtml(s.title || "Untitled") + '</div>' +
      '<div class="session-meta">' + escapeHtml(s.model || "") + '</div>' +
      '<div class="session-meta">' + formatTimestamp(s.updated_at) + '</div>' +
      '</div><span class="delete-session-btn" data-sid="' + s.id + '">x</span></div>';
    item.addEventListener("click", (function(sid) {
      return async function(ev) {
        var del = ev.target.closest("[data-sid]");
        if (del) { ev.stopPropagation(); await deleteSession(del.dataset.sid); return; }
        await loadSession(sid);
      };
    })(s.id));
    elements.sessionHistory.appendChild(item);
  }
}

async function refreshSessions() {
  renderSessionList(await fetchJson("/api/sessions"));
}

function resolveStatusContainer() {
  return document.getElementById("status-panel") || document.querySelector("h3 + div");
}

async function updateSystemStatus() {
  var c = resolveStatusContainer();
  if (!c) return;
  try {
    var [skills, mcp] = await Promise.all([
      fetch("/api/skills").then(function(r) { return r.json(); }),
      fetch("/api/mcp/servers").then(function(r) { return r.json(); }),
    ]);
    var h = '<div style="font-size:12px;">';
    h += '<div style="color:var(--accent-primary);font-weight:bold;letter-spacing:1px;margin-bottom:6px;">\u2728 MCP SERVERS</div>';
    for (var sv of mcp) {
      h += '<div style="display:flex;justify-content:space-between;margin-bottom:3px;">' +
        '<span style="color:#e0e0e0;">' + escapeHtml(sv.name) + '</span>' +
        '<span style="color:var(--success);font-size:10px;">' + sv.tools.length + ' tools</span></div>';
    }
    h += '<div style="color:var(--accent-primary);font-weight:bold;letter-spacing:1px;margin-top:10px;margin-bottom:6px;">\u2728 SKILLS</div>';
    var cats = {};
    for (var sk of skills) { if (!cats[sk.category]) cats[sk.category] = []; cats[sk.category].push(sk); }
    for (var [cat, list] of Object.entries(cats)) {
      h += '<div style="color:var(--text-muted);font-size:10px;text-transform:uppercase;margin-top:4px;">' + escapeHtml(cat) + '</div>';
      for (var sk2 of list) {
        h += '<div style="color:#e0e0e0;margin-left:8px;margin-bottom:2px;font-size:11px;">- ' + escapeHtml(sk2.name) + '</div>';
      }
    }
    h += "</div>";
    c.innerHTML = h;
  } catch (e) {}
}

async function loadModels() {
  state.models = await fetchJson("/api/models");
  renderModelSelector(state.models);
  state.copilotConnected = state.models.some(function(m) { return m.tier && m.tier !== "local"; });
  syncCopilotBadge();
  ensureUsageDisplay();
  var active = state.models.find(function(m) { return m.default; }) || state.models[0];
  if (active) {
    if (!elements.modelSelector.value) elements.modelSelector.value = active.id;
    var sel = state.models.find(function(m) { return m.id === elements.modelSelector.value; }) || active;
    elements.currentModelLabel.textContent = sel.name || sel.id;
    syncResearchBadge();
  }
}

async function loadSession(id) {
  var session = await fetchJson("/api/sessions/" + id);
  state.currentSessionId = session.id;
  state.messages = session.messages || [];
  state.assistantMessageElement = null;
  resetActivity();
  elements.chatMessages.innerHTML = "";
  if (!state.messages.length) {
    renderEmptyState("No messages in this session");
  } else {
    for (var msg of state.messages) {
      renderMessage(msg.role, msg.content);
    }
  }
  var am = state.models.find(function(m) { return m.id === session.model; });
  elements.currentModelLabel.textContent = (am ? am.name : null) || session.model || "Unknown";
  syncResearchBadge();
  await refreshSessions();
}

function newSession() {
  state.currentSessionId = null;
  state.messages = [];
  state.assistantMessageElement = null;
  elements.chatMessages.innerHTML = "";
  renderEmptyState("\u2728 Start a new conversation");
  resetActivity();
  refreshSessions().catch(function(e) { showToast(e.message); });
}

async function deleteSession(id) {
  if (!window.confirm("Delete this session?")) return;
  await fetchJson("/api/sessions/" + id, { method: "DELETE" });
  if (state.currentSessionId === id) { newSession(); return; }
  await refreshSessions();
}

function ensureAssistantBubble() {
  if (!state.assistantMessageElement) {
    state.assistantMessageElement = renderMessage("assistant", "");
  }
  return state.assistantMessageElement;
}

function appendAssistantDelta(content) {
  consumeReasoningDelta(content);
  var bubble = ensureAssistantBubble();
  var cur = bubble.dataset.rawContent || "";
  var previousRenderedLength = Number(bubble.dataset.renderedTextLength || "0");
  var next = cur + content;
  bubble.dataset.rawContent = next;
  var contentEl = getMessageContentElement(bubble);
  contentEl.innerHTML = formatMarkdown(next);
  enhanceAssistantMarkdown(contentEl);
  var nextRenderedLength = (contentEl.textContent || "").length;
  bubble.dataset.renderedTextLength = String(nextRenderedLength);
  applyStreamingTextReveal(bubble, contentEl, Math.max(nextRenderedLength - previousRenderedLength, 0));
  scrollChatToBottom();
}

/* ===== Send Message (SSE) ===== */
async function sendMessage(content) {
  if (!content.trim() || state.isStreaming) return;
  if (elements.chatMessages.querySelector(".empty-state")) elements.chatMessages.innerHTML = "";
  var model = elements.modelSelector.value;
  state.messages.push({ role: "user", content: content });
  renderMessage("user", content);
  resetActivity();
  state.assistantMessageElement = null;
  setStreaming(true);
  elements.currentModelLabel.textContent =
    (state.models.find(function(m) { return m.id === model; }) || {}).name || model;

  try {
    var response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId: state.currentSessionId, message: content, model: model }),
    });
    if (!response.ok || !response.body) throw new Error("Failed to start stream");
    var reader = response.body.getReader();
    var buffer = "";
    while (true) {
      var result = await reader.read();
      if (result.done) break;
      buffer += sseDecoder.decode(result.value, { stream: true });
      var chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";
      for (var chunk of chunks) {
        var lines = chunk.split("\n");
        var eventName = "message";
        var data = "";
        for (var line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;
        var payload = JSON.parse(data);
        if (eventName === "session") state.currentSessionId = payload.sessionId;
        if (eventName === "activity") {
          upsertActivity(payload.step, payload.status, payload.time);
          handleReasoningActivity(payload);
        }
        if (eventName !== "activity" && eventName !== "delta" && payload && (payload.step || payload.type)) {
          handleReasoningActivity(payload);
        }
        if (eventName === "delta") appendAssistantDelta(payload.content);
        if (eventName === "tool_call") { state.researchMode = true; syncResearchBadge(); renderToolCall(payload); }
        if (eventName === "done") {
          finalizeReasoningTrace(state.assistantMessageElement);
          state.messages.push({ role: "assistant", content: payload.fullContent });
          state.assistantMessageElement = null;
          finalizeInlineActivity();
          elements.currentModelLabel.textContent =
            (state.models.find(function(m) { return m.id === payload.model; }) || {}).name || payload.model || model;
          syncResearchBadge();
          await refreshSessions();
        }
        if (eventName === "error") {
          finalizeReasoningTrace(state.assistantMessageElement);
          if (payload.message && payload.message.includes("not supported")) {
            renderMessage("system", "This model requires Pro+. Use claude-sonnet-4.6 or gpt-4.1.");
          } else {
            renderMessage("system", "Error: " + (payload.message || "Stream error"));
          }
          showToast(payload.message || "Stream error");
        }
        if (eventName === "warning") showToast(payload.message || "Warning");
      }
    }
  } catch (error) {
    finalizeReasoningTrace(state.assistantMessageElement);
    upsertActivity("error", "error", "", error.message);
    showToast(error.message);
  } finally {
    finalizeReasoningTrace(state.assistantMessageElement);
    setStreaming(false);
    elements.chatInput.value = "";
    autoResizeTextarea();
    scrollChatToBottom();
  }
}

/* ===== Events ===== */
function autoResizeTextarea() {
  elements.chatInput.style.height = "auto";
  elements.chatInput.style.height = Math.min(elements.chatInput.scrollHeight, 200) + "px";
}

function bindTabNavigation() {
  var tabButtons = document.querySelectorAll(".tab-btn");
  var tabPanels = document.querySelectorAll(".tab-panel");
  if (!tabButtons.length || !tabPanels.length) return;

  tabButtons.forEach(function(btn) {
    btn.addEventListener("click", function() {
      var requestedTab = btn.dataset.tab;
      var targetTab = requestedTab === "memory" ? "memory-view" : requestedTab;
      tabButtons.forEach(function(button) {
        button.classList.toggle("active", button === btn);
      });
      tabPanels.forEach(function(panel) {
        var isTarget = panel.id === targetTab;
        panel.classList.toggle("active", isTarget);
        panel.classList.toggle("hidden", !isTarget);
      });
      if (targetTab === "pipeline-container") {
        loadPipelineHistory().catch(function() {});
      }
      if (targetTab === "memory-view") {
        loadMemoryPanel().catch(function(error) {
          showToast("Failed to load memory panel: " + (error.message || "unknown"));
        });
      }
    });
  });
}

function bindEvents() {
  elements.modelSelector.addEventListener("change", function() {
    var a = state.models.find(function(m) { return m.id === elements.modelSelector.value; });
    elements.currentModelLabel.textContent = a ? (a.name || a.id) : "Unknown";
    syncResearchBadge();
  });
  elements.chatForm.addEventListener("submit", async function(ev) {
    ev.preventDefault();
    await sendMessage(elements.chatInput.value);
  });
  elements.chatInput.addEventListener("input", autoResizeTextarea);
  elements.chatInput.addEventListener("keydown", async function(ev) {
    if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); await sendMessage(elements.chatInput.value); }
  });
  elements.newSessionBtn.addEventListener("click", newSession);
  bindPipelineEvents();
  bindMemoryPanelEvents();
  window.addEventListener("beforeunload", stopPipelineStream);
}

/* ===== Initialize ===== */
async function initialize() {
  initParticles();
  bindTabNavigation();
  bindEvents();
  ensureResearchBadge();
  ensureCopilotBadge();
  ensureUsageDisplay();
  initializePipelineUI();
  renderEmptyState("\u2728 Loading...");
  try {
    await Promise.all([loadModels(), refreshSessions(), updateSystemStatus()]);
    updateUsage();
    setInterval(updateUsage, 60000);
    renderEmptyState("\u2728 Start a new conversation");
  } catch (error) {
    showToast(error.message);
    renderEmptyState("Failed to load");
  }
}

initialize();



/* ===== Monitor Tab ===== */
var monitorRefreshIntervalId = null;
var monitorBindingsApplied = false;

var MONITOR_COLORS = {
  ok: "#00ff88",
  error: "#ff4444",
  degraded: "#ffaa00",
  cardA: "#1a1a2e",
  cardB: "#111",
  border: "#333",
  text: "#e8ecf2",
  muted: "#9ca3af",
};

function formatUptimeToClock(seconds) {
  var total = Math.max(0, Number(seconds) || 0);
  var hours = Math.floor(total / 3600);
  var minutes = Math.floor((total % 3600) / 60);
  var secs = Math.floor(total % 60);
  return String(hours).padStart(2, "0") + ":" + String(minutes).padStart(2, "0") + ":" + String(secs).padStart(2, "0");
}

function monitorStatusKind(value) {
  if (value === true) return "ok";
  if (value === false || value == null) return "error";
  var normalized = String(value).toLowerCase();
  if (normalized === "ok" || normalized === "up" || normalized === "healthy" || normalized === "pass") return "ok";
  if (normalized === "degraded" || normalized === "warn" || normalized === "warning") return "degraded";
  if (normalized === "down" || normalized === "error" || normalized === "unhealthy" || normalized === "fail") return "error";
  return "error";
}

function monitorKindColor(kind) {
  if (kind === "ok") return MONITOR_COLORS.ok;
  if (kind === "degraded") return MONITOR_COLORS.degraded;
  return MONITOR_COLORS.error;
}

function setMonitorIndicator(dotId, valueId, rawValue) {
  var dot = document.getElementById(dotId);
  var value = document.getElementById(valueId);
  if (!dot || !value) return;
  var kind = monitorStatusKind(rawValue);
  var color = monitorKindColor(kind);
  var text = kind === "ok" ? "UP" : (kind === "degraded" ? "DEGRADED" : "DOWN");
  dot.style.background = color;
  dot.style.boxShadow = "0 0 10px " + color;
  value.textContent = text;
  value.style.color = color;
}

function setMonitorHealthValue(rawValue) {
  var value = document.getElementById("monitor-health-value");
  if (!value) return;
  var kind = monitorStatusKind(rawValue);
  var color = monitorKindColor(kind);
  var text = kind === "ok" ? "healthy" : (kind === "degraded" ? "degraded" : "unhealthy");
  value.textContent = text;
  value.style.color = color;
}

function updateMonitorHistoryTable(historyList) {
  var body = document.getElementById("monitor-history-body");
  if (!body) return;
  if (!Array.isArray(historyList) || !historyList.length) {
    body.innerHTML = '<tr><td colspan="5" style="padding:12px;color:' + MONITOR_COLORS.muted + ';text-align:center;">No history found.</td></tr>';
    return;
  }

  body.innerHTML = historyList.map(function(item) {
    var query = escapeHtml(item.query || "-");
    var filename = escapeHtml(item.filename || "-");
    var date = item.date ? escapeHtml(new Date(item.date).toLocaleString()) : "-";
    var paperCount = item.paperCount != null ? String(item.paperCount) : "-";
    var sizeKB = item.sizeKB != null ? String(item.sizeKB) : "-";
    return (
      "<tr>" +
        '<td style="padding:10px;border-bottom:1px solid ' + MONITOR_COLORS.border + ';color:' + MONITOR_COLORS.text + ';">' + filename + "</td>" +
        '<td style="padding:10px;border-bottom:1px solid ' + MONITOR_COLORS.border + ';color:' + MONITOR_COLORS.text + ';">' + query + "</td>" +
        '<td style="padding:10px;border-bottom:1px solid ' + MONITOR_COLORS.border + ';color:' + MONITOR_COLORS.text + ';">' + date + "</td>" +
        '<td style="padding:10px;border-bottom:1px solid ' + MONITOR_COLORS.border + ';color:' + MONITOR_COLORS.text + ';text-align:right;">' + paperCount + "</td>" +
        '<td style="padding:10px;border-bottom:1px solid ' + MONITOR_COLORS.border + ';color:' + MONITOR_COLORS.text + ';text-align:right;">' + sizeKB + "</td>" +
      "</tr>"
    );
  }).join("");
}

function setMonitorLastUpdateText(text) {
  var stamp = document.getElementById("monitor-last-updated");
  if (!stamp) return;
  stamp.textContent = text;
}

async function refreshMonitorStatus() {
  try {
    var results = await Promise.all([
      fetchJson("/api/monitor/status"),
      fetchJson("/api/monitor/health"),
      fetchJson("/api/monitor/history"),
    ]);
    var status = results[0] || {};
    var health = results[1] || {};
    var history = results[2] || [];

    setMonitorIndicator("monitor-copilot-dot", "monitor-copilot-value", status.copilotApi);
    setMonitorIndicator("monitor-db-dot", "monitor-db-value", status.db);
    setMonitorHealthValue(health.status);

    var uptimeValue = document.getElementById("monitor-uptime-value");
    if (uptimeValue) uptimeValue.textContent = formatUptimeToClock(status.uptime);

    updateMonitorHistoryTable(history);
    var ts = status.timestamp || new Date().toISOString();
    setMonitorLastUpdateText("Last updated: " + new Date(ts).toLocaleString());
  } catch (error) {
    setMonitorLastUpdateText("Monitor refresh failed");
    updateMonitorHistoryTable([]);
    setMonitorHealthValue("unhealthy");
    setMonitorIndicator("monitor-copilot-dot", "monitor-copilot-value", false);
    setMonitorIndicator("monitor-db-dot", "monitor-db-value", false);
    var uptimeValueOnError = document.getElementById("monitor-uptime-value");
    if (uptimeValueOnError) uptimeValueOnError.textContent = "--:--:--";
    showToast(error && error.message ? error.message : "Failed to refresh monitor");
  }
}

function stopMonitorAutoRefresh() {
  if (monitorRefreshIntervalId) {
    clearInterval(monitorRefreshIntervalId);
    monitorRefreshIntervalId = null;
  }
}

function startMonitorAutoRefresh() {
  refreshMonitorStatus().catch(function() {});
  if (monitorRefreshIntervalId) return;
  monitorRefreshIntervalId = setInterval(function() {
    refreshMonitorStatus().catch(function() {});
  }, 10000);
}

function monitorHandleTabSwitch(targetTabId) {
  if (targetTabId === "monitor-container") {
    startMonitorAutoRefresh();
  } else {
    stopMonitorAutoRefresh();
  }
}

function bindMonitorTabAutoRefresh() {
  if (monitorBindingsApplied) return;
  monitorBindingsApplied = true;
  var tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach(function(btn) {
    btn.addEventListener("click", function() {
      monitorHandleTabSwitch(btn.dataset.tab);
    });
  });

  var activeBtn = document.querySelector(".tab-btn.active");
  if (activeBtn) monitorHandleTabSwitch(activeBtn.dataset.tab);
}

function initializeMonitorTabUI() {
  var container = document.getElementById("monitor-container");
  if (!container) return;
  if (container.dataset.monitorReady === "1") return;
  container.dataset.monitorReady = "1";

  var styleId = "monitor-inline-style";
  if (!document.getElementById(styleId)) {
    var style = document.createElement("style");
    style.id = styleId;
    style.textContent =
      "#monitor-container .monitor-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:18px;}" +
      "#monitor-container .monitor-card{background:linear-gradient(180deg," + MONITOR_COLORS.cardA + ", " + MONITOR_COLORS.cardB + ");border:1px solid " + MONITOR_COLORS.border + ";border-radius:12px;padding:14px;}" +
      "#monitor-container .monitor-card-title{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:" + MONITOR_COLORS.muted + ";margin-bottom:8px;}" +
      "#monitor-container .monitor-card-value{font-size:22px;font-weight:700;color:" + MONITOR_COLORS.text + ";display:flex;align-items:center;gap:8px;}" +
      "#monitor-container .monitor-dot{width:10px;height:10px;border-radius:999px;display:inline-block;}" +
      "#monitor-container .monitor-history-wrap{background:linear-gradient(180deg," + MONITOR_COLORS.cardA + ", " + MONITOR_COLORS.cardB + ");border:1px solid " + MONITOR_COLORS.border + ";border-radius:12px;padding:14px;overflow:auto;}" +
      "#monitor-container .monitor-history-title{font-size:15px;font-weight:600;color:" + MONITOR_COLORS.text + ";margin-bottom:10px;}" +
      "#monitor-container .monitor-history-table{width:100%;border-collapse:collapse;min-width:680px;}" +
      "#monitor-container .monitor-history-table th{padding:10px;text-align:left;color:" + MONITOR_COLORS.muted + ";font-size:12px;text-transform:uppercase;border-bottom:1px solid " + MONITOR_COLORS.border + ";}" +
      "#monitor-container .monitor-meta{margin:10px 2px 0;color:" + MONITOR_COLORS.muted + ";font-size:12px;}";
    document.head.appendChild(style);
  }

  container.innerHTML =
    '<section style="padding:18px 0;">' +
      '<div class="monitor-grid">' +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Copilot API</div>' +
          '<div class="monitor-card-value"><span id="monitor-copilot-dot" class="monitor-dot" style="background:' + MONITOR_COLORS.error + ';"></span><span id="monitor-copilot-value">DOWN</span></div>' +
        "</article>" +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Database</div>' +
          '<div class="monitor-card-value"><span id="monitor-db-dot" class="monitor-dot" style="background:' + MONITOR_COLORS.error + ';"></span><span id="monitor-db-value">DOWN</span></div>' +
        "</article>" +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Health</div>' +
          '<div id="monitor-health-value" class="monitor-card-value" style="color:' + MONITOR_COLORS.error + ';">unhealthy</div>' +
        "</article>" +
        '<article class="monitor-card">' +
          '<div class="monitor-card-title">Uptime</div>' +
          '<div id="monitor-uptime-value" class="monitor-card-value">00:00:00</div>' +
        "</article>" +
      "</div>" +
      '<section class="monitor-history-wrap">' +
        '<div class="monitor-history-title">Pipeline History</div>' +
        '<table class="monitor-history-table">' +
          "<thead>" +
            "<tr>" +
              "<th>Filename</th>" +
              "<th>Query</th>" +
              "<th>Date</th>" +
              "<th>Papers</th>" +
              "<th>Size (KB)</th>" +
            "</tr>" +
          "</thead>" +
          '<tbody id="monitor-history-body">' +
            '<tr><td colspan="5" style="padding:12px;color:' + MONITOR_COLORS.muted + ';text-align:center;">Loading...</td></tr>' +
          "</tbody>" +
        "</table>" +
        '<div id="monitor-last-updated" class="monitor-meta">Last updated: --</div>' +
      "</section>" +
    "</section>";
}

function bootMonitorTab() {
  initializeMonitorTabUI();
  bindMonitorTabAutoRefresh();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootMonitorTab);
} else {
  bootMonitorTab();
}

window.refreshMonitorStatus = refreshMonitorStatus;


/* ===== Daily Digest ===== */
var digestState = {
  eventSource: null,
  running: false,
  historyLoaded: false,
};

function setDigestRunButtonState(running) {
  var button = document.getElementById("digest-run-btn");
  if (!button) return;
  button.disabled = Boolean(running);
  button.textContent = running ? "Running..." : "Run Daily Digest";
}

function setDigestStatusMessage(message, type) {
  var el = document.getElementById("digest-status-message");
  if (!el) return;
  el.classList.remove("error", "success");
  if (type) el.classList.add(type);
  el.textContent = message || "";
}

function normalizeDigestUrl(rawUrl) {
  if (!rawUrl) return "";
  var url = String(rawUrl).trim();
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("10.")) return "https://doi.org/" + url;
  return "";
}

function parseDigestKeywordStats(summary) {
  if (!summary || typeof summary !== "object") return [];
  if (Array.isArray(summary.keywordStats)) {
    return summary.keywordStats
      .map(function(entry) {
        if (!entry || typeof entry !== "object") return null;
        var keyword = String(entry.keyword || entry.term || "").trim();
        if (!keyword) return null;
        var count = Number(entry.count ?? entry.paperCount ?? 0);
        return {
          keyword: keyword,
          count: Number.isFinite(count) ? count : 0,
        };
      })
      .filter(Boolean);
  }

  if (summary.keywordStats && typeof summary.keywordStats === "object") {
    return Object.entries(summary.keywordStats).map(function(tuple) {
      var keyword = String(tuple[0] || "").trim();
      var count = Number(tuple[1] ?? 0);
      return {
        keyword: keyword,
        count: Number.isFinite(count) ? count : 0,
      };
    });
  }

  return [];
}

function parseDigestTopPapers(summary, result) {
  var source = [];
  if (summary && Array.isArray(summary.topPapers)) {
    source = summary.topPapers;
  } else if (result && Array.isArray(result.topPapers)) {
    source = result.topPapers;
  } else if (result && Array.isArray(result.papers)) {
    source = result.papers;
  } else if (result && Array.isArray(result.results)) {
    source = result.results;
  }

  return source
    .map(function(paper) {
      if (!paper || typeof paper !== "object") return null;
      var title = String(paper.title || paper.paperTitle || "").trim();
      if (!title) return null;
      return {
        title: title,
        keyword: String(paper.keyword || paper.term || "").trim(),
        source: String(paper.source || paper.journal || "").trim(),
        year: Number(paper.year) || null,
        score: Number(paper.score) || null,
        url: normalizeDigestUrl(paper.url || paper.link || paper.doi),
      };
    })
    .filter(Boolean)
    .slice(0, 10);
}

function renderDigestKeywordStats(summary) {
  var container = document.getElementById("digest-results-keywords");
  if (!container) return;

  var stats = parseDigestKeywordStats(summary);
  if (!stats.length) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = stats
    .map(function(entry) {
      return '<span class="digest-keyword-chip">' +
        escapeHtml(entry.keyword) +
        ': ' +
        escapeHtml(String(entry.count)) +
        "</span>";
    })
    .join("");
}

function renderDigestTopPapers(summary, result) {
  var list = document.getElementById("digest-top-papers-list");
  if (!list) return;

  var papers = parseDigestTopPapers(summary, result);
  if (!papers.length) {
    list.innerHTML = '<li class="pipeline-empty-row">Top papers will appear here.</li>';
    return;
  }

  list.innerHTML = papers
    .map(function(paper) {
      var titleHtml = escapeHtml(paper.title);
      if (paper.url) {
        titleHtml =
          '<a class="digest-top-paper-title" target="_blank" rel="noopener noreferrer" href="' +
          escapeHtml(paper.url) +
          '">' +
          titleHtml +
          "</a>";
      } else {
        titleHtml = '<span class="digest-top-paper-title">' + titleHtml + "</span>";
      }

      var meta = [paper.keyword, paper.source, paper.year, paper.score ? ("score " + paper.score.toFixed(1)) : ""]
        .filter(Boolean)
        .map(function(value) { return escapeHtml(String(value)); })
        .join(" | ");

      return '<li class="digest-top-paper-item">' +
        titleHtml +
        '<div class="digest-top-paper-meta">' + (meta || "-") + "</div>" +
        "</li>";
    })
    .join("");
}

function renderDigestSummary(summary, result) {
  var summaryEl = document.getElementById("digest-results-summary");
  if (!summaryEl) return;

  var safeSummary = summary && typeof summary === "object" ? summary : {};
  var keywordCount = Number(safeSummary.keywordCount ?? parseDigestKeywordStats(safeSummary).length ?? 0);
  var totalPapers = Number(
    safeSummary.totalPapers ??
      safeSummary.total_papers ??
      (Array.isArray(result && result.papers) ? result.papers.length : 0)
  );

  summaryEl.textContent =
    "Keywords: " + (Number.isFinite(keywordCount) ? keywordCount : 0) +
    " | Total papers: " +
    (Number.isFinite(totalPapers) ? totalPapers : 0);

  renderDigestKeywordStats(safeSummary);
  renderDigestTopPapers(safeSummary, result);
}

function formatDigestHistoryDate(rawDate) {
  if (!rawDate) return "--";
  var parsed = new Date(rawDate);
  if (Number.isNaN(parsed.getTime())) return String(rawDate);
  return parsed.toLocaleString("ja-JP");
}

function renderDigestHistory(items) {
  var body = document.getElementById("digest-history-body");
  if (!body) return;

  if (!Array.isArray(items) || !items.length) {
    body.innerHTML = '<tr><td colspan="5" class="pipeline-empty-row">No digest history yet.</td></tr>';
    return;
  }

  body.innerHTML = items
    .map(function(item) {
      var filename = String(item.filename || "").trim();
      var encodedName = encodeURIComponent(filename);
      return (
        "<tr>" +
          "<td>" + escapeHtml(formatDigestHistoryDate(item.date)) + "</td>" +
          "<td>" + escapeHtml(String(item.keywordCount ?? "-")) + "</td>" +
          "<td>" + escapeHtml(String(item.totalPapers ?? "-")) + "</td>" +
          "<td>" + escapeHtml(String(item.sizeKB ?? "-")) + "</td>" +
          '<td><button type="button" class="digest-history-link" data-digest-report="' + encodedName + '">Download</button></td>' +
        "</tr>"
      );
    })
    .join("");
}

async function loadDigestHistory(force) {
  if (digestState.historyLoaded && !force) return;
  try {
    var history = await fetchJson("/api/digest/history");
    renderDigestHistory(history);
    digestState.historyLoaded = true;
  } catch (error) {
    renderDigestHistory([]);
    setDigestStatusMessage("Failed to load digest history: " + error.message, "error");
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
  var keywordInput = document.getElementById("digest-keywords-input");
  var rawKeywords = keywordInput ? keywordInput.value.trim() : "";
  var query = rawKeywords ? ("?keywords=" + encodeURIComponent(rawKeywords)) : "";
  return "/api/digest/run" + query;
}

async function handleDigestPayload(payload, sourceRef) {
  if (digestState.eventSource !== sourceRef) return;

  if (payload.error) {
    setDigestStatusMessage("Digest error: " + payload.error, "error");
    stopDigestStream();
    return;
  }

  if (payload.done) {
    renderDigestSummary(payload.summary, payload.result);
    setDigestStatusMessage("Daily Digest completed.", "success");
    digestState.historyLoaded = false;
    await loadDigestHistory(true);
    stopDigestStream();
    return;
  }

  if (payload.message) {
    setDigestStatusMessage(payload.message);
  }
}

function runDailyDigestFromUI() {
  if (digestState.running) return;

  stopDigestStream();
  digestState.running = true;
  setDigestRunButtonState(true);
  setDigestStatusMessage("Daily Digest is running...");

  var summaryEl = document.getElementById("digest-results-summary");
  if (summaryEl) summaryEl.textContent = "Digest running...";
  var statsEl = document.getElementById("digest-results-keywords");
  if (statsEl) statsEl.innerHTML = "";
  var topList = document.getElementById("digest-top-papers-list");
  if (topList) topList.innerHTML = '<li class="pipeline-empty-row">Digest running...</li>';

  var streamUrl = buildDigestStreamUrl();
  var eventSource = new EventSource(streamUrl);
  digestState.eventSource = eventSource;

  eventSource.onmessage = function(event) {
    if (digestState.eventSource !== eventSource) return;
    try {
      var payload = JSON.parse(event.data);
      Promise.resolve(handleDigestPayload(payload, eventSource)).catch(function(error) {
        setDigestStatusMessage("Digest stream error: " + error.message, "error");
        stopDigestStream();
      });
    } catch (error) {
      setDigestStatusMessage("Invalid digest stream payload.", "error");
      stopDigestStream();
    }
  };

  eventSource.onerror = function() {
    if (digestState.eventSource !== eventSource) return;
    setDigestStatusMessage("Digest stream disconnected.", "error");
    stopDigestStream();
  };
}

async function downloadDigestReport(filename) {
  var safeFilename = String(filename || "").trim();
  if (!safeFilename) return;

  var endpoint = "/api/digest/report/" + encodeURIComponent(safeFilename);
  var response = await fetch(endpoint);
  if (!response.ok) {
    throw new Error(response.status + " " + response.statusText);
  }

  var blob = await response.blob();
  var blobUrl = window.URL.createObjectURL(blob);
  var anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = safeFilename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(blobUrl);
}

function bindDigestEvents() {
  var runButton = document.getElementById("digest-run-btn");
  var refreshButton = document.getElementById("digest-refresh-history-btn");
  var historyBody = document.getElementById("digest-history-body");

  if (runButton) {
    runButton.addEventListener("click", function() {
      runDailyDigestFromUI();
    });
  }

  if (refreshButton) {
    refreshButton.addEventListener("click", function() {
      digestState.historyLoaded = false;
      loadDigestHistory(true).catch(function(error) {
        showToast(error.message || "Failed to load digest history");
      });
    });
  }

  if (historyBody) {
    historyBody.addEventListener("click", function(event) {
      var target = event.target.closest("[data-digest-report]");
      if (!target) return;
      var filename = decodeURIComponent(target.getAttribute("data-digest-report") || "");
      downloadDigestReport(filename).catch(function(error) {
        showToast("Download failed: " + (error.message || "unknown"));
      });
    });
  }

  var pipelineTabButton = document.querySelector('.tab-btn[data-tab="pipeline-container"]');
  if (pipelineTabButton) {
    pipelineTabButton.addEventListener("click", function() {
      loadDigestHistory().catch(function() {});
    });
  }

  window.addEventListener("beforeunload", stopDigestStream);
}

function initializeDigestUI() {
  setDigestRunButtonState(false);
  setDigestStatusMessage('Click "Run Daily Digest" to start.');
  renderDigestHistory([]);
  var activePipelineTab = document.querySelector('.tab-btn.active[data-tab="pipeline-container"]');
  if (activePipelineTab) {
    loadDigestHistory().catch(function() {});
  }
}

function bootDigestUI() {
  bindDigestEvents();
  initializeDigestUI();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootDigestUI);
} else {
  bootDigestUI();
}

var sidebarToggle = document.getElementById("sidebarToggle");
var sidebar = document.querySelector(".sidebar") || document.getElementById("sidebar");

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener("click", function() {
    sidebar.classList.toggle("open");
  });

  document.querySelectorAll(".nav-btn, .tab-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.remove("open");
      }
    });
  });

  window.addEventListener("resize", function() {
    if (window.innerWidth > 768) {
      sidebar.classList.remove("open");
    }
  });
}





var themeToggle = document.getElementById("themeToggle");
var themeIcon = themeToggle ? themeToggle.querySelector(".theme-icon") : null;

function setTheme(theme) {
  var nextTheme = theme === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", nextTheme);
  try {
    localStorage.setItem("jarvis-theme", nextTheme);
  } catch (error) {
    // Ignore storage failures in restricted environments.
  }
  if (themeIcon) themeIcon.textContent = nextTheme === "light" ? "☀️" : "🌙";
}

var savedTheme = "dark";
try {
  savedTheme = localStorage.getItem("jarvis-theme") || "dark";
} catch (error) {
  savedTheme = "dark";
}
setTheme(savedTheme);

if (themeToggle) {
  themeToggle.addEventListener("click", function() {
    var current = document.documentElement.getAttribute("data-theme");
    setTheme(current === "light" ? "dark" : "light");
  });
}



