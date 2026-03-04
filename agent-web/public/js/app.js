const state = {
  currentSessionId: null,
  messages: [],
  models: [],
  isStreaming: false,
  assistantMessageElement: null,
  activities: new Map(),
  activityStartedAt: new Map(),
  researchMode: false,
  copilotConnected: false,
};

const elements = {
  modelSelector: document.querySelector("#model-selector"),
  currentModelLabel: document.querySelector("#current-model-label"),
  sessionHistory: document.querySelector("#session-history"),
  mcpStatus: document.querySelector("#mcp-status"),
  skillsStatus: document.querySelector("#skills-status"),
  chatMessages: document.querySelector("#chat-messages"),
  activityPanel: document.querySelector("#agent-activity-panel"),
  activityTimeline: document.querySelector("#activity-timeline"),
  activityStatus: document.querySelector("#activity-status"),
  toggleActivityBtn: document.querySelector("#toggle-activity-btn"),
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

function formatMarkdown(content) {
  const escaped = escapeHtml(content);
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

function formatTimestamp(iso) {
  if (!iso) {
    return "";
  }

  const diffMs = Date.now() - new Date(iso).getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 1) {
    return "just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function scrollChatToBottom() {
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function ensureResearchBadge() {
  let badge = document.querySelector("#research-mode-badge");
  if (!badge) {
    badge = document.createElement("span");
    badge.id = "research-mode-badge";
    badge.textContent = "Research Mode";
    badge.hidden = true;
    badge.style.marginLeft = "10px";
    badge.style.padding = "2px 8px";
    badge.style.borderRadius = "999px";
    badge.style.border = "1px solid rgba(101, 184, 255, 0.32)";
    badge.style.background = "rgba(43, 86, 130, 0.24)";
    badge.style.color = "#9fd0ff";
    badge.style.fontSize = "0.75rem";
    badge.style.fontWeight = "600";
    elements.currentModelLabel.insertAdjacentElement("afterend", badge);
  }
  return badge;
}

function syncResearchBadge() {
  ensureResearchBadge().hidden = !state.researchMode;
}

function ensureCopilotBadge() {
  let badge = document.querySelector("#copilot-status-badge");
  if (!badge) {
    badge = document.createElement("div");
    badge.id = "copilot-status-badge";
    badge.style.marginTop = "0.75rem";
    badge.style.padding = "0.55rem 0.75rem";
    badge.style.borderRadius = "12px";
    badge.style.fontSize = "0.8rem";
    badge.style.fontWeight = "600";
    badge.style.lineHeight = "1.4";
    elements.modelSelector.insertAdjacentElement("afterend", badge);
  }
  return badge;
}

function syncCopilotBadge() {
  const badge = ensureCopilotBadge();
  if (state.copilotConnected) {
    badge.textContent = "Copilot Connected";
    badge.style.color = "#b9ffd1";
    badge.style.background = "rgba(38, 120, 77, 0.24)";
    badge.style.border = "1px solid rgba(87, 214, 135, 0.35)";
  } else {
    badge.textContent = "Copilot Offline - LiteLLM Fallback";
    badge.style.color = "#ffe7a8";
    badge.style.background = "rgba(140, 102, 21, 0.2)";
    badge.style.border = "1px solid rgba(244, 196, 48, 0.35)";
  }
}

function renderModelSelector(models) {
  const select = elements.modelSelector;
  if (!select) return;
  select.innerHTML = "";

  const proModels = models.filter((m) => m.tier === "pro");
  const proPlus = models.filter((m) => m.tier === "pro+");
  const unknown = models.filter((m) => m.tier === "unknown");
  const local = models.filter((m) => m.tier === "local");

  function addGroup(label, list, locked) {
    if (list.length === 0) return;
    const group = document.createElement("optgroup");
    group.label = label;
    for (const m of list) {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = locked ? `🔒 ${m.id} (Pro+)` : (m.name || m.id);
      if (locked) {
        opt.style.color = "#666";
        opt.style.fontStyle = "italic";
      }
      if (m.default) opt.selected = true;
      group.appendChild(opt);
    }
    select.appendChild(group);
  }

  addGroup("Copilot Pro (Available)", proModels, false);
  addGroup("Unverified", unknown, false);
  addGroup("🔒 Copilot Pro+ ($39/mo)", proPlus, true);
  addGroup("💻 Local Fallback", local, false);

  if (!select.value || select.value === "") {
    const preferred = ["claude-sonnet-4.6", "gpt-4.1", "o4-mini"];
    for (const p of preferred) {
      const opt = select.querySelector(`option[value="${p}"]`);
      if (opt) {
        select.value = p;
        break;
      }
    }
  }
}

function ensureUsageDisplay() {
  if (document.getElementById("usage-display")) return;
  const sidebar = document.getElementById("sidebar") || document.querySelector(".sidebar");
  if (!sidebar) return;
  
  const badge = sidebar.querySelector("[class*='status'], [id*='copilot-status']") 
    || sidebar.querySelector("button");
  
  const usageDiv = document.createElement("div");
  usageDiv.id = "usage-display";
  usageDiv.innerHTML = `
    <div style="margin-top:10px;padding:8px 12px;background:#1a1a2e;border-radius:8px;font-size:12px;">
      <div style="color:#888;margin-bottom:4px;font-weight:bold;letter-spacing:1px;">COPILOT USAGE</div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
        <span style="color:#e0e0e0;">Premium Requests</span>
        <span id="usage-percent" style="color:#e0e0e0;">--</span>
      </div>
      <div style="background:#2a2a3e;border-radius:4px;height:6px;overflow:hidden;">
        <div id="usage-bar" style="height:100%;width:0%;background:#4ade80;border-radius:4px;transition:width 0.5s;"></div>
      </div>
    </div>
  `;
  
  if (badge && badge.parentNode) {
    badge.parentNode.insertBefore(usageDiv, badge.nextSibling);
  } else {
    sidebar.appendChild(usageDiv);
  }
}

async function updateUsage() {
  ensureUsageDisplay();
  try {
    const res = await fetch("/api/usage");
    const data = await res.json();
    const percentEl = document.getElementById("usage-percent");
    const barEl = document.getElementById("usage-bar");
    
    state.copilotConnected = Boolean(data.available);
    syncCopilotBadge();

    if (data.available) {
      let percent = 0;
      const raw = JSON.stringify(data);
      
      const percentMatch = raw.match(/"percentage"\s*:\s*([\d.]+)/);
      if (percentMatch) {
        percent = parseFloat(percentMatch[1]);
      }
      if (data.copilot_usage?.premium_requests?.percentage !== undefined) {
        percent = data.copilot_usage.premium_requests.percentage;
      }
      if (data.percentage !== undefined) {
        percent = data.percentage;
      }
      if (data.chat?.percentage !== undefined) {
        percent = data.chat.percentage;
      }
      
      if (percentEl) percentEl.textContent = percent.toFixed(1) + "%";
      if (barEl) {
        barEl.style.width = Math.min(percent, 100) + "%";
        if (percent > 80) barEl.style.background = "#ef4444";
        else if (percent > 50) barEl.style.background = "#eab308";
        else barEl.style.background = "#4ade80";
      }
    } else {
      if (percentEl) percentEl.textContent = "N/A";
      if (barEl) {
        barEl.style.width = "0%";
        barEl.style.background = "#6b7280";
      }
    }
  } catch (e) {
    // silently fail
  }
}

function setStreaming(isStreaming) {
  state.isStreaming = isStreaming;
  elements.sendButton.disabled = isStreaming;
  elements.activityStatus.textContent = isStreaming ? "running" : "idle";
  elements.activityStatus.className = `indicator ${isStreaming ? "running" : "idle"}`;
}

function renderMessage(role, content) {
  const bubble = document.createElement("article");
  bubble.className = `message ${role}`;
  bubble.innerHTML = formatMarkdown(content);
  elements.chatMessages.appendChild(bubble);
  scrollChatToBottom();
  return bubble;
}

function renderEmptyState(message) {
  elements.chatMessages.innerHTML = `<div class="empty-state">${message}</div>`;
}

function prettyStep(step) {
  return step
    .split("_")
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}

function resolvedElapsed(step, time = "") {
  if (time) {
    return time;
  }
  const startedAt = state.activityStartedAt.get(step);
  if (!startedAt) {
    return "";
  }
  return `${Date.now() - startedAt}ms`;
}

function upsertActivity(step, status, time, extra = "") {
  if (status === "running") {
    state.activityStartedAt.set(step, Date.now());
  }

  let node = state.activities.get(step);
  if (!node) {
    node = document.createElement("div");
    node.className = `activity-item ${status}`;
    node.dataset.step = step;
    node.innerHTML = `
      <div class="activity-item-title"></div>
      <div class="activity-meta"></div>
    `;
    state.activities.set(step, node);
    elements.activityTimeline.appendChild(node);
  }

  node.className = `activity-item ${status}`;
  node.querySelector(".activity-item-title").textContent = prettyStep(step);
  node.querySelector(".activity-meta").textContent = [status, resolvedElapsed(step, time), extra]
    .filter(Boolean)
    .join(" | ");
}

function renderToolCall(payload) {
  const details = document.createElement("details");
  details.className = "activity-item done";

  const preview = String(payload.result || "").slice(0, 200);
  const fullText = String(payload.result || "");
  const meta = ["done", payload.time].filter(Boolean).join(" | ");

  details.innerHTML = `
    <summary class="activity-item-title">[tool] ${escapeHtml(payload.name || "tool_call")}</summary>
    <div class="activity-meta">${escapeHtml(meta)}</div>
    <div style="margin-top: 8px; white-space: pre-wrap; word-break: break-word;">${escapeHtml(preview)}</div>
    ${
      fullText.length > 200
        ? `<div style="margin-top: 8px; opacity: 0.82; white-space: pre-wrap; word-break: break-word;">${escapeHtml(
            fullText
          )}</div>`
        : ""
    }
  `;

  elements.activityTimeline.appendChild(details);
}

function resetActivity() {
  state.activities.clear();
  state.activityStartedAt.clear();
  state.researchMode = false;
  elements.activityTimeline.innerHTML = "";
  elements.activityStatus.textContent = "idle";
  elements.activityStatus.className = "indicator idle";
  syncResearchBadge();
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 3000);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function renderSessionList(sessions) {
  elements.sessionHistory.innerHTML = "";

  if (!sessions.length) {
    elements.sessionHistory.innerHTML = `<div class="empty-state">No sessions yet</div>`;
    return;
  }

  for (const session of sessions) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `session-item ${session.id === state.currentSessionId ? "active" : ""}`;
    item.innerHTML = `
      <div class="session-title-row">
        <div>
          <div class="session-title">${escapeHtml(session.title || "Untitled Session")}</div>
          <div class="session-meta">${escapeHtml(session.model || "")}</div>
          <div class="session-meta">${formatTimestamp(session.updated_at)}</div>
        </div>
        <span class="delete-session-btn" data-session-delete="${session.id}">x</span>
      </div>
    `;

    item.addEventListener("click", async (event) => {
      const deleteTarget = event.target.closest("[data-session-delete]");
      if (deleteTarget) {
        event.stopPropagation();
        await deleteSession(deleteTarget.dataset.sessionDelete);
        return;
      }

      await loadSession(session.id);
    });

    elements.sessionHistory.appendChild(item);
  }
}

async function refreshSessions() {
  const sessions = await fetchJson("/api/sessions");
  renderSessionList(sessions);
}

function renderStatusList(container, items, emptyLabel, formatter) {
  container.innerHTML = "";
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">${emptyLabel}</div>`;
    return;
  }

  for (const item of items) {
    container.appendChild(formatter(item));
  }
}

function createStatusLine(label, detail, status = "active") {
  const line = document.createElement("div");
  line.className = "status-line";
  line.innerHTML = `
    <span class="status-dot ${status}"></span>
    <div>
      <div>${escapeHtml(label)}</div>
      <small>${escapeHtml(detail)}</small>
    </div>
  `;
  return line;
}

function resolveStatusContainer() {
  return document.getElementById("status-panel")
    || document.getElementById("system-status")
    || document.querySelector("[class*='system-status']")
    || document.querySelector("h3 + div");
}

async function updateSystemStatus() {
  const statusContainer = resolveStatusContainer();
  if (!statusContainer) return;

  try {
    const [skillsRes, mcpRes] = await Promise.all([
      fetch("/api/skills").then((r) => r.json()),
      fetch("/api/mcp/servers").then((r) => r.json()),
    ]);

    let html = '<div style="font-size:12px;">';
    html += '<div style="color:#888;font-weight:bold;letter-spacing:1px;margin-bottom:6px;">MCP SERVERS</div>';
    for (const server of mcpRes) {
      html += `<div style="display:flex;justify-content:space-between;margin-bottom:3px;">
        <span style="color:#e0e0e0;">${escapeHtml(server.name)}</span>
        <span style="color:#4ade80;font-size:10px;">${server.tools.length} tools</span>
      </div>`;
    }

    html += '<div style="color:#888;font-weight:bold;letter-spacing:1px;margin-top:10px;margin-bottom:6px;">SKILLS</div>';
    const categories = {};
    for (const skill of skillsRes) {
      if (!categories[skill.category]) categories[skill.category] = [];
      categories[skill.category].push(skill);
    }
    for (const [cat, skills] of Object.entries(categories)) {
      html += `<div style="color:#888;font-size:10px;text-transform:uppercase;margin-top:4px;">${escapeHtml(cat)}</div>`;
      for (const skill of skills) {
        html += `<div style="color:#e0e0e0;margin-left:8px;margin-bottom:2px;font-size:11px;" title="${escapeHtml(skill.description || "")}">- ${escapeHtml(skill.name)}</div>`;
      }
    }

    html += "</div>";
    statusContainer.innerHTML = html;
  } catch (e) {
    // silently fail
  }
}

async function loadModels() {
  state.models = await fetchJson("/api/models");
  renderModelSelector(state.models);
  state.copilotConnected = state.models.some((model) => model.tier && model.tier !== "local");
  syncCopilotBadge();
  ensureUsageDisplay();

  const activeModel = state.models.find((model) => model.default) ?? state.models[0];
  if (activeModel) {
    if (!elements.modelSelector.value) {
      elements.modelSelector.value = activeModel.id;
    }
    const selected = state.models.find((model) => model.id === elements.modelSelector.value) ?? activeModel;
    elements.currentModelLabel.textContent = selected.name ?? selected.id;
    syncResearchBadge();
  }
}

async function loadSession(id) {
  const session = await fetchJson(`/api/sessions/${id}`);
  state.currentSessionId = session.id;
  state.messages = session.messages ?? [];
  state.assistantMessageElement = null;
  resetActivity();
  elements.chatMessages.innerHTML = "";

  if (!state.messages.length) {
    renderEmptyState("No messages in this session");
  } else {
    for (const message of state.messages) {
      renderMessage(message.role, message.content);
      if (Array.isArray(message.tool_calls) && message.tool_calls.length) {
        state.researchMode = true;
      }
    }
  }

  const activeModel = state.models.find((model) => model.id === session.model);
  elements.currentModelLabel.textContent = activeModel?.name ?? session.model ?? "Unknown model";
  syncResearchBadge();
  await refreshSessions();
}

function newSession() {
  state.currentSessionId = null;
  state.messages = [];
  state.assistantMessageElement = null;
  elements.chatMessages.innerHTML = "";
  renderEmptyState("Start a new conversation");
  resetActivity();
  refreshSessions().catch((error) => showToast(error.message));
}

async function deleteSession(id) {
  const confirmed = window.confirm("Delete this session?");
  if (!confirmed) {
    return;
  }

  await fetchJson(`/api/sessions/${id}`, { method: "DELETE" });
  if (state.currentSessionId === id) {
    newSession();
    return;
  }
  await refreshSessions();
}

function ensureAssistantBubble() {
  if (!state.assistantMessageElement) {
    state.assistantMessageElement = renderMessage("assistant", "");
  }
  return state.assistantMessageElement;
}

function appendAssistantDelta(content) {
  const bubble = ensureAssistantBubble();
  const currentText = bubble.dataset.rawContent ?? "";
  const nextText = currentText + content;
  bubble.dataset.rawContent = nextText;
  bubble.innerHTML = formatMarkdown(nextText);
  scrollChatToBottom();
}

async function sendMessage(content) {
  if (!content.trim() || state.isStreaming) {
    return;
  }

  if (elements.chatMessages.querySelector(".empty-state")) {
    elements.chatMessages.innerHTML = "";
  }

  const selectedModel = elements.modelSelector.value;
  state.messages.push({ role: "user", content });
  renderMessage("user", content);
  resetActivity();
  state.assistantMessageElement = null;
  setStreaming(true);
  elements.currentModelLabel.textContent =
    state.models.find((model) => model.id === selectedModel)?.name ?? selectedModel;

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sessionId: state.currentSessionId,
        message: content,
        model: selectedModel,
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error("Failed to start stream");
    }

    const reader = response.body.getReader();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      buffer += sseDecoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        const lines = chunk.split("\n");
        let eventName = "message";
        let data = "";

        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventName = line.slice(6).trim();
          }
          if (line.startsWith("data:")) {
            data += line.slice(5).trim();
          }
        }

        if (!data) {
          continue;
        }

        const payload = JSON.parse(data);
        if (eventName === "session") {
          state.currentSessionId = payload.sessionId;
        }
        if (eventName === "activity") {
          upsertActivity(payload.step, payload.status, payload.time);
        }
        if (eventName === "delta") {
          appendAssistantDelta(payload.content);
        }
        if (eventName === "tool_call") {
          state.researchMode = true;
          syncResearchBadge();
          renderToolCall(payload);
        }
        if (eventName === "done") {
          state.messages.push({ role: "assistant", content: payload.fullContent });
          state.assistantMessageElement = null;
          elements.currentModelLabel.textContent =
            state.models.find((model) => model.id === payload.model)?.name ?? payload.model ?? selectedModel;
          syncResearchBadge();
          await refreshSessions();
        }
        if (eventName === "error") {
          if (payload.message && (payload.message.includes("model_not_supported") || payload.message.includes("not supported"))) {
            renderMessage("system", "このモデルはCopilot Pro+（$39/月）が必要です。claude-sonnet-4.6 または gpt-4.1 をお試しください。");
          } else {
            renderMessage("system", "Error: " + (payload.message || "Stream error"));
          }
          showToast(payload.message || "Stream error");
        }
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

function autoResizeTextarea() {
  elements.chatInput.style.height = "auto";
  elements.chatInput.style.height = `${Math.min(elements.chatInput.scrollHeight, 200)}px`;
}

function bindEvents() {
  elements.modelSelector.addEventListener("change", () => {
    const active = state.models.find((model) => model.id === elements.modelSelector.value);
    elements.currentModelLabel.textContent = active?.name ?? active?.id ?? "Unknown model";
    syncResearchBadge();
  });

  elements.chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await sendMessage(elements.chatInput.value);
  });

  elements.chatInput.addEventListener("input", autoResizeTextarea);
  elements.chatInput.addEventListener("keydown", async (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await sendMessage(elements.chatInput.value);
    }
  });

  elements.newSessionBtn.addEventListener("click", newSession);
  elements.toggleActivityBtn.addEventListener("click", () => {
    elements.activityPanel.classList.toggle("collapsed");
  });
}

async function initialize() {
  bindEvents();
  ensureResearchBadge();
  ensureCopilotBadge();
  ensureUsageDisplay();
  renderEmptyState("Loading...");

  try {
    await Promise.all([loadModels(), refreshSessions(), updateSystemStatus()]);
    updateUsage();
    setInterval(updateUsage, 60000);
    updateSystemStatus();
    renderEmptyState("Start a new conversation");
  } catch (error) {
    showToast(error.message);
    renderEmptyState("Failed to load application state");
  }
}

initialize();
