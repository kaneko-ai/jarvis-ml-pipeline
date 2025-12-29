const app = (() => {
  const STORAGE_BASE = "JAVIS_API_BASE";
  const STORAGE_TOKEN = "JAVIS_API_TOKEN";

  const getApiBase = () => (localStorage.getItem(STORAGE_BASE) || "").trim();
  const getApiToken = () => (localStorage.getItem(STORAGE_TOKEN) || "").trim();

  const setApiConfig = (base, token) => {
    localStorage.setItem(STORAGE_BASE, (base || "").trim());
    localStorage.setItem(STORAGE_TOKEN, (token || "").trim());
  };

  const buildUrl = (path) => {
    if (path.startsWith("http")) return path;
    const base = getApiBase();
    if (!base) return null;
    return `${base.replace(/\/$/, "")}${path}`;
  };

  const withTimeout = (promise, timeoutMs) => {
    let timer;
    const timeoutPromise = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error("Request timeout")), timeoutMs);
    });
    return Promise.race([promise, timeoutPromise]).finally(() => clearTimeout(timer));
  };

  const apiFetch = async (path, options = {}) => {
    const url = buildUrl(path);
    if (!url) {
      throw new Error("API_BASEが未設定です。Settingsで設定してください。");
    }
    const { method = "GET", body, headers = {}, timeout = 15000 } = options;
    const finalHeaders = {
      Accept: "application/json",
      ...headers,
    };
    const token = getApiToken();
    if (token) {
      finalHeaders.Authorization = `Bearer ${token}`;
    }
    let payload = body;
    if (body && !(body instanceof FormData)) {
      finalHeaders["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }

    const response = await withTimeout(
      fetch(url, {
        method,
        headers: finalHeaders,
        body: payload,
      }),
      timeout
    );

    const contentType = response.headers.get("content-type") || "";
    const rawText = await response.text();
    let data = null;
    if (rawText) {
      if (contentType.includes("application/json")) {
        try {
          data = JSON.parse(rawText);
        } catch (error) {
          throw new Error(`JSONパースに失敗しました: ${error.message}`);
        }
      } else {
        data = rawText;
      }
    }

    if (![200, 201].includes(response.status)) {
      const message = typeof data === "string" ? data : JSON.stringify(data);
      throw new Error(`HTTP ${response.status}: ${message || "Request failed"}`);
    }

    return data;
  };

  const apiFetchSafe = async (path, options = {}) => {
    try {
      const data = await apiFetch(path, options);
      return { ok: true, data };
    } catch (error) {
      return { ok: false, error };
    }
  };

  const resolveFileUrl = (runId, file) => {
    if (!file) return null;
    if (typeof file === "string") {
      return buildUrl(`/api/runs/${runId}/files/${encodeURIComponent(file)}`) || file;
    }
    return (
      file.url ||
      file.download_url ||
      file.downloadUrl ||
      (file.path ? buildUrl(`/api/runs/${runId}/files/${encodeURIComponent(file.path)}`) : null) ||
      (file.key ? buildUrl(`/api/runs/${runId}/files/${encodeURIComponent(file.key)}`) : null)
    );
  };

  const normalizeFileEntry = (file) => {
    if (!file) return null;
    if (typeof file === "string") {
      return { name: file.split("/").pop(), path: file };
    }
    return {
      name: file.name || file.path || file.key || "file",
      path: file.path || file.key || file.name,
      ...file,
    };
  };

  const listRuns = () => apiFetch("/api/runs");
  const getRun = (runId) => apiFetch(`/api/runs/${runId}`);
  const getRunEventsUrl = (runId) => buildUrl(`/api/runs/${runId}/events`);
  const getHealth = () => apiFetch("/api/health");
  const getCronHealth = () => apiFetch("/api/health/cron");
  const getRank = (runId, topK = 50) =>
    apiFetch(`/api/research/rank?run_id=${encodeURIComponent(runId)}&top_k=${topK}`);
  const getPaper = (runId, paperId) =>
    apiFetch(`/api/research/paper/${encodeURIComponent(paperId)}?run_id=${encodeURIComponent(runId)}`);
  const getQaReport = (runId) => apiFetch(`/api/qa/report?run_id=${encodeURIComponent(runId)}`);
  const buildSubmission = (payload) => apiFetch("/api/submission/build", { method: "POST", body: payload });
  const getSubmissionLatest = (runId) => apiFetch(`/api/submission/run/${encodeURIComponent(runId)}/latest`);
  const getSubmissionEmail = (runId) => apiFetch(`/api/submission/run/${encodeURIComponent(runId)}/email`);
  const getSubmissionChangelog = (runId) => apiFetch(`/api/submission/run/${encodeURIComponent(runId)}/changelog`);
  const listSchedules = () => apiFetch("/api/schedules");
  const createSchedule = (payload) => apiFetch("/api/schedules", { method: "POST", body: payload });
  const updateSchedule = (scheduleId, payload) =>
    apiFetch(`/api/schedules/${encodeURIComponent(scheduleId)}`, { method: "PATCH", body: payload });
  const runScheduleNow = (scheduleId, force = false) =>
    apiFetch(`/api/schedules/${encodeURIComponent(scheduleId)}/run?force=${force}`, { method: "POST" });
  const getScheduleHistory = (scheduleId, limit = 50) =>
    apiFetch(`/api/schedules/${encodeURIComponent(scheduleId)}/history?limit=${limit}`);
  const importFeedback = (payload) => apiFetch("/api/feedback/import", { method: "POST", body: payload });
  const getFeedbackRisk = (runId) => apiFetch(`/api/feedback/risk?run_id=${encodeURIComponent(runId)}`);
  const decisionSimulate = (payload) => apiFetch("/api/decision/simulate", { method: "POST", body: payload });
  const financeOptimize = (payload) => apiFetch("/api/finance/optimize", { method: "POST", body: payload });

  return {
    STORAGE_BASE,
    STORAGE_TOKEN,
    getApiBase,
    getApiToken,
    setApiConfig,
    apiFetch,
    apiFetchSafe,
    resolveFileUrl,
    normalizeFileEntry,
    listRuns,
    getRun,
    getRunEventsUrl,
    getHealth,
    getCronHealth,
    getRank,
    getPaper,
    getQaReport,
    buildSubmission,
    getSubmissionLatest,
    getSubmissionEmail,
    getSubmissionChangelog,
    listSchedules,
    createSchedule,
    updateSchedule,
    runScheduleNow,
    getScheduleHistory,
    importFeedback,
    getFeedbackRisk,
    decisionSimulate,
    financeOptimize,
    buildUrl,
  };
})();

window.app = app;
