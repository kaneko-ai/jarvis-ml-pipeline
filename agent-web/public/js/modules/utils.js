const PIPELINE_FILE_PREFIXES = ["", "agent-web/", "data/"];

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function formatTimestamp(iso) {
  if (!iso) return "";
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

export function formatElapsedTime(ms) {
  if (!Number.isFinite(ms) || ms < 0) return "";
  return `${(ms / 1000).toFixed(1)}s`;
}

export function parseDurationMs(value) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (!value) return null;
  const text = String(value).trim();
  const match = text.match(/^([\d.]+)\s*(ms|s)$/i);
  if (!match) return null;
  const amount = Number(match[1]);
  if (!Number.isFinite(amount)) return null;
  return match[2].toLowerCase() === "s" ? amount * 1000 : amount;
}

export function tryParseJson(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed || !/^[\[{]/.test(trimmed)) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    return null;
  }
}

export function highlightJSON(prettyJson) {
  const source = String(prettyJson || "");
  let html = "";
  let lastIndex = 0;
  const tokenPattern = /("(?:\\.|[^\\"])*")(?=\s*:)|("(?:\\.|[^\\"])*")|\b(?:true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?/g;

  source.replace(tokenPattern, (match, keyToken, stringToken, offset) => {
    html += escapeHtml(source.slice(lastIndex, offset));
    let className = "json-number";
    if (keyToken) {
      className = "json-key";
    } else if (stringToken) {
      className = "json-string";
    } else if (/^(true|false|null)$/.test(match)) {
      className = "json-bool";
    }
    html += `<span class="${className}">${escapeHtml(match)}</span>`;
    lastIndex = offset + match.length;
    return match;
  });

  html += escapeHtml(source.slice(lastIndex));
  return html;
}

export function formatJsonBlock(jsonString) {
  const parsed = tryParseJson(jsonString);
  if (parsed === null) return "";
  const prettyJson = JSON.stringify(parsed, null, 2);
  const lineCount = prettyJson.split("\n").length;
  const block = `<pre class="json-formatted"><code class="language-json">${highlightJSON(prettyJson)}</code></pre>`;
  if (lineCount > 10) {
    return `<details class="json-collapse" open><summary>JSON (${lineCount} lines)</summary>${block}</details>`;
  }
  return block;
}

export function buildDoiLink(doi) {
  const safeDoi = String(doi || "").trim();
  if (!safeDoi) return "";
  return `<a href="https://doi.org/${safeDoi}" class="cite-link" target="_blank" rel="noreferrer noopener">DOI:${safeDoi}</a><a href="https://api.unpaywall.org/v2/${encodeURIComponent(safeDoi)}?email=jarvis@example.com" class="pdf-lookup" target="_blank" rel="noreferrer noopener" title="Check Unpaywall">📥</a>`;
}

export function buildPmidLink(pmid) {
  const safePmid = String(pmid || "").trim();
  if (!safePmid) return "";
  return `<a href="https://pubmed.ncbi.nlm.nih.gov/${safePmid}" class="cite-link" target="_blank" rel="noreferrer noopener">PMID:${safePmid}</a>`;
}

function createCitationTokenStore() {
  const store = [];
  return {
    push(html) {
      const token = `@@CITE_LINK_${store.length}@@`;
      store.push({ token, html });
      return token;
    },
    restore(text) {
      let restored = String(text || "");
      for (const entry of store) {
        restored = restored.replaceAll(entry.token, entry.html);
      }
      return restored;
    },
  };
}

export function autoLinkDOI(text) {
  if (!text) return "";
  const citationTokens = createCitationTokenStore();
  const linked = String(text)
    .replace(/\bPMID:\s*(\d{4,9})\b/gi, (_, pmid) => citationTokens.push(buildPmidLink(pmid)))
    .replace(/\bDOI:\s*(10\.\d{4,9}\/[\-._;()/:A-Z0-9]+?)([.,;)\]]?)(?=\s|$)/gi, (_, doi, trailing) => `${citationTokens.push(buildDoiLink(doi))}${trailing || ""}`)
    .replace(/\b(10\.\d{4,9}\/[\-._;()/:A-Z0-9]+?)([.,;)\]]?)(?=\s|$)/gi, (_, doi, trailing) => `${citationTokens.push(buildDoiLink(doi))}${trailing || ""}`);

  return citationTokens.restore(linked);
}

export async function fetchJson(url, opts) {
  const response = await fetch(url, opts || {});
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

export function createToastContainer() {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  return container;
}

export function showToast(message, type = "info") {
  const container = createToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add("toast-show");
  });

  setTimeout(() => {
    toast.classList.remove("toast-show");
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, 3000);
}

export function updateNotificationToggleState() {
  const toggle = document.getElementById("notifToggle");
  if (!toggle) return;
  if (!("Notification" in window)) {
    toggle.setAttribute("aria-disabled", "true");
    toggle.title = "Notifications are unavailable";
    toggle.textContent = "🔕";
    return;
  }

  toggle.removeAttribute("aria-disabled");
  const permission = Notification.permission;
  if (permission === "granted") {
    toggle.textContent = "🔔";
    toggle.title = "Notifications enabled";
    return;
  }
  if (permission === "denied") {
    toggle.textContent = "🔕";
    toggle.title = "Notifications blocked";
    return;
  }
  toggle.textContent = "🔔";
  toggle.title = "Enable notifications";
}

export async function requestNotificationPermission() {
  if (!("Notification" in window)) return "denied";
  if (Notification.permission !== "default") {
    updateNotificationToggleState();
    return Notification.permission;
  }
  const permission = await Notification.requestPermission();
  updateNotificationToggleState();
  return permission;
}

export function showNotification(title, options) {
  if (!("Notification" in window) || Notification.permission !== "granted") {
    showToast(title + (options?.body ? `: ${options.body}` : ""), "info");
    return null;
  }

  const safeOptions = options || {};
  const clickHandler = safeOptions.onclick;
  const defaults = {
    icon: "/css/favicon.ico",
    badge: "/css/favicon.ico",
    tag: `jarvis-${Date.now()}`,
    requireInteraction: false,
  };
  const notificationOptions = Object.assign({}, defaults, safeOptions);
  delete notificationOptions.onclick;

  try {
    const notification = new Notification(title, notificationOptions);
    notification.onclick = () => {
      window.focus();
      notification.close();
      if (typeof clickHandler === "function") clickHandler();
    };
    setTimeout(() => {
      notification.close();
    }, 8000);
    return notification;
  } catch {
    showToast(title + (safeOptions.body ? `: ${safeOptions.body}` : ""), "info");
    return null;
  }
}

export function buildPipelineFileCandidates(filePath) {
  const raw = String(filePath || "").trim().replace(/\\/g, "/");
  if (!raw) return [];

  const normalized = raw.replace(/^\/+/, "").replace(/^\.\//, "");
  const candidates = [];
  const addCandidate = (url) => {
    if (!url || candidates.includes(url)) return;
    candidates.push(url);
  };

  addCandidate(`/${normalized}`);
  for (const prefix of PIPELINE_FILE_PREFIXES) {
    if (prefix && normalized.startsWith(prefix)) {
      addCandidate(`/${normalized.slice(prefix.length)}`);
    }
  }
  if (normalized.startsWith("data/")) {
    addCandidate(`/${normalized}`);
  }
  const dataIndex = normalized.indexOf("data/");
  if (dataIndex >= 0) {
    addCandidate(`/${normalized.slice(dataIndex)}`);
  }
  const filename = normalized.split("/").pop();
  if (filename) {
    addCandidate(`/data/${filename}`);
  }

  return candidates;
}

export async function fetchPipelineResultFile(filePath) {
  const candidates = buildPipelineFileCandidates(filePath);
  let lastError = null;

  for (const candidate of candidates) {
    try {
      const response = await fetch(candidate, { cache: "no-store" });
      if (!response.ok) {
        lastError = new Error(`${response.status} ${response.statusText}`);
        continue;
      }
      const payload = await response.json();
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

export function initParticles() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let particles = [];
  const particleCount = 60;

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

  function reset() {
    resize();
    particles = [];
    for (let index = 0; index < particleCount; index += 1) {
      const particle = createParticle();
      particle.y = Math.random() * canvas.height;
      particles.push(particle);
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let index = particles.length - 1; index >= 0; index -= 1) {
      const particle = particles[index];
      particle.x += particle.speedX;
      particle.y += particle.speedY;
      particle.pulse += particle.pulseSpeed;
      const alpha = particle.opacity * (0.5 + 0.5 * Math.sin(particle.pulse));
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      ctx.fillStyle = `${particle.color}${alpha.toFixed(3)})`;
      ctx.fill();
      if (particle.y < -10 || particle.x < -10 || particle.x > canvas.width + 10) {
        particles[index] = createParticle();
      }
    }
    requestAnimationFrame(animate);
  }

  window.addEventListener("resize", resize);
  reset();
  animate();
}
