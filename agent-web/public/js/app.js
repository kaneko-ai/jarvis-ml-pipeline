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

/* ===== Markdown Rendering ===== */
function formatMarkdown(raw) {
  if (!raw) return "";
  var result = "";
  var remaining = raw;
  var codeStart = remaining.indexOf("`");

  while (codeStart !== -1) {
    var before = remaining.slice(0, codeStart);
    result += formatInlineText(before);

    var afterOpen = remaining.slice(codeStart + 3);
    var newlinePos = afterOpen.indexOf("\n");
    var codeEnd = afterOpen.indexOf("`", newlinePos > -1 ? newlinePos : 0);

    if (newlinePos === -1 || codeEnd === -1) {
      result += formatInlineText(remaining.slice(codeStart));
      remaining = "";
      break;
    }

    var lang = afterOpen.slice(0, newlinePos).trim() || "plaintext";
    var code = afterOpen.slice(newlinePos + 1, codeEnd);
    var highlighted = escapeHtml(code);
    if (typeof hljs !== "undefined" && lang !== "plaintext" && hljs.getLanguage(lang)) {
      try { highlighted = hljs.highlight(code, { language: lang }).value; } catch(e) {}
    }
    result +=
      '<div class="code-block-wrapper">' +
      '<div class="code-block-header"><span>' + escapeHtml(lang) + '</span>' +
      '<button class="code-copy-btn" onclick="copyCode(this)" type="button">copy</button></div>' +
      '<pre><code class="hljs language-' + escapeHtml(lang) + '">' + highlighted + '</code></pre></div>';

    remaining = afterOpen.slice(codeEnd + 3);
    codeStart = remaining.indexOf("`");
  }

  result += formatInlineText(remaining);
  return result;
}

function formatInlineText(text) {
  if (!text) return "";
  var escaped = escapeHtml(text);
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, "<br>");
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
    node.className = "inline-activity-item " + status;
    node.innerHTML = '<span class="ia-dot"></span><div class="ia-content"><div class="ia-title"></div><div class="ia-meta"></div></div>';
    state.activityItems.set(step, node);
    timeline.appendChild(node);
  }
  node.className = "inline-activity-item " + status;
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
  details.className = "inline-activity-item done";
  var preview = String(payload.result || "").slice(0, 200);
  details.innerHTML =
    '<summary style="display:flex;align-items:center;gap:8px;cursor:pointer;">' +
    '<span class="ia-dot"></span>' +
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

function renderMessage(role, content) {
  var bubble = document.createElement("article");
  bubble.className = "message " + role;
  bubble.innerHTML = formatMarkdown(content);
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
  var bubble = ensureAssistantBubble();
  var cur = bubble.dataset.rawContent || "";
  var next = cur + content;
  bubble.dataset.rawContent = next;
  bubble.innerHTML = formatMarkdown(next);
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
        if (eventName === "activity") upsertActivity(payload.step, payload.status, payload.time);
        if (eventName === "delta") appendAssistantDelta(payload.content);
        if (eventName === "tool_call") { state.researchMode = true; syncResearchBadge(); renderToolCall(payload); }
        if (eventName === "done") {
          state.messages.push({ role: "assistant", content: payload.fullContent });
          state.assistantMessageElement = null;
          finalizeInlineActivity();
          elements.currentModelLabel.textContent =
            (state.models.find(function(m) { return m.id === payload.model; }) || {}).name || payload.model || model;
          syncResearchBadge();
          await refreshSessions();
        }
        if (eventName === "error") {
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
    upsertActivity("error", "error", "", error.message);
    showToast(error.message);
  } finally {
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

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      var targetTab = btn.dataset.tab;
      tabButtons.forEach(function(button) {
        button.classList.toggle("active", button === btn);
      });
      tabPanels.forEach(function(panel) {
        panel.classList.toggle("active", panel.id === targetTab);
      });
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
}

/* ===== Initialize ===== */
async function initialize() {
  initParticles();
  bindTabNavigation();
  bindEvents();
  ensureResearchBadge();
  ensureCopilotBadge();
  ensureUsageDisplay();
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

