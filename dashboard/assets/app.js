(() => {
  async function fetchConfig() {
    try {
      const res = await fetch("config.json", { cache: "no-store" });
      if (!res.ok) return {};
      return await res.json();
    } catch (err) {
      return {};
    }
  }

  async function getApiBase() {
    if (window.API_BASE) return window.API_BASE;
    const config = await fetchConfig();
    return config.apiBase || "";
  }

  async function fetchJson(endpoint) {
    const apiBase = await getApiBase();
    const res = await fetch(`${apiBase}${endpoint}`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`Request failed: ${res.status}`);
    }
    return await res.json();
  }

  function renderStatusBadge(status) {
    const normalized = status || "unknown";
    return normalized;
  }

  async function refreshOpsStatusCard() {
    const statusEl = document.getElementById("ops-status-text");
    const indicator = document.getElementById("ops-status-indicator");
    if (!statusEl || !indicator) return;
    try {
      const [health, summary] = await Promise.all([
        fetchJson("/api/obs/health"),
        fetchJson("/api/obs/metrics/summary"),
      ]);
      const total = summary.runs_total || 0;
      const failed = summary.runs_failed || 0;
      const failureRate = total ? failed / total : 0;
      let status = "green";
      if (!health.cron?.last_heartbeat) {
        status = "red";
      } else if (failureRate >= 0.5) {
        status = "red";
      } else if (failed > 0 || summary.runs_in_progress > 0) {
        status = "yellow";
      }
      indicator.dataset.status = status;
      statusEl.textContent = renderStatusBadge(status);
      const cronEl = document.getElementById("ops-status-cron");
      if (cronEl) cronEl.textContent = health.cron?.last_heartbeat || "n/a";
      const stalledEl = document.getElementById("ops-status-stalled");
      if (stalledEl) stalledEl.textContent = summary.runs_in_progress || 0;
      const failRateEl = document.getElementById("ops-status-failure-rate");
      if (failRateEl) {
        failRateEl.textContent = total ? `${Math.round(failureRate * 100)}%` : "0%";
      }
    } catch (err) {
      indicator.dataset.status = "red";
      statusEl.textContent = "red";
    }
  }

  async function refreshOpsDashboard() {
    const statusEl = document.getElementById("ops-health-status");
    try {
      const [health, summary, topErrors, rules] = await Promise.all([
        fetchJson("/api/obs/health"),
        fetchJson("/api/obs/metrics/summary"),
        fetchJson("/api/obs/metrics/errors/top?days=30"),
        fetchJson("/api/obs/alerts/rules"),
      ]);
      let status = "green";
      const total = summary.runs_total || 0;
      const failed = summary.runs_failed || 0;
      const failureRate = total ? failed / total : 0;
      if (!health.cron?.last_heartbeat) {
        status = "red";
      } else if (failureRate >= 0.5) {
        status = "red";
      } else if (failed > 0 || summary.runs_in_progress > 0) {
        status = "yellow";
      }
      if (statusEl) {
        statusEl.textContent = `Status: ${renderStatusBadge(status)}`;
      }
      const stalledList = document.getElementById("ops-stalled-list");
      if (stalledList) {
        stalledList.textContent = `Running: ${summary.runs_in_progress || 0}`;
      }
      const failedList = document.getElementById("ops-failed-list");
      if (failedList) {
        const items = topErrors
          .map((err) => `${err.error_type}: ${err.count}`)
          .join("\n");
        failedList.textContent = items || "No failures reported";
      }
      const alertsList = document.getElementById("ops-alerts-list");
      if (alertsList) {
        alertsList.textContent = `Last cron heartbeat: ${health.cron?.last_heartbeat || "n/a"}`;
      }
      const rulesList = document.getElementById("ops-rules-list");
      if (rulesList) {
        const items = rules.rules
          .map((rule) => `${rule.rule_id} (${rule.enabled ? "ON" : "OFF"})`)
          .join("\n");
        rulesList.textContent = items || "No rules configured";
      }
    } catch (err) {
      if (statusEl) {
        statusEl.textContent = "Status: unknown";
      }
    }
  }

  window.JarvisOps = {
    refreshOpsStatusCard,
    refreshOpsDashboard,
  };

  document.addEventListener("DOMContentLoaded", () => {
    refreshOpsStatusCard();
    refreshOpsDashboard();
  });
})();
