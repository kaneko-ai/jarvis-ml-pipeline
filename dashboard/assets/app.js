const app = (() => {
  const STORAGE_BASE = "JAVIS_API_BASE";
  const STORAGE_TOKEN = "JAVIS_API_TOKEN";

  const getApiBase = () => (localStorage.getItem(STORAGE_BASE) || "").trim();
  const getApiToken = () => (localStorage.getItem(STORAGE_TOKEN) || "").trim();

  const setApiConfig = (base, token) => {
    localStorage.setItem(STORAGE_BASE, (base || "").trim());
    localStorage.setItem(STORAGE_TOKEN, (token || "").trim());
  };

  const getApiMap = () => window.api_map_v1 || {};

  const getPath = (key) => {
    const entry = getApiMap()[key];
    if (!entry) return null;
    if (typeof entry === "string") return entry;
    return entry.path || null;
  };

  const formatQuery = (query = {}) => {
    const entries = Object.entries(query).filter(([, value]) => value !== undefined && value !== null);
    if (!entries.length) return "";
    const params = entries
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join("&");
    return params ? `?${params}` : "";
  };

  const formatPath = (key, params = {}, query = {}) => {
    const rawPath = getPath(key);
    if (!rawPath) return null;
    let missingParam = false;
    const filled = rawPath.replace(/:([A-Za-z0-9_]+)/g, (_, token) => {
      const value = params[token];
      if (value === undefined || value === null) {
        missingParam = true;
        return "";
      }
      return encodeURIComponent(value);
    });
    if (missingParam) return null;
    return `${filled}${formatQuery(query)}`;
  };

  const buildUrl = (path) => {
    if (!path) return null;
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
    if (!path) {
      throw new Error("APIが未実装です。");
    }
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
      return buildUrl(formatPath("runs_files", { runId, file })) || file;
    }
    return (
      file.url ||
      file.download_url ||
      file.downloadUrl ||
      (file.path ? buildUrl(formatPath("runs_files", { runId, file: file.path })) : null) ||
      (file.key ? buildUrl(formatPath("runs_files", { runId, file: file.key })) : null)
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

  const listRuns = () => apiFetch(getPath("runs_list"));
  const getRun = (runId) => apiFetch(formatPath("runs_detail", { runId }));
  const getRunEventsUrl = (runId) => buildUrl(formatPath("runs_events", { runId }));
  const getHealth = () => apiFetch(getPath("health"));
  const getCronHealth = () => apiFetch(getPath("health_cron"));
  const getRank = (runId, topK = 50) =>
    apiFetch(formatPath("research_rank", {}, { run_id: runId, top_k: topK }));
  const getPaper = (runId, paperId) =>
    apiFetch(formatPath("research_paper", { paperId }, { run_id: runId }));
  const getQaReport = (runId) => apiFetch(formatPath("qa_report", {}, { run_id: runId }));
  const buildSubmission = (payload) => apiFetch(getPath("submission_build"), { method: "POST", body: payload });
  const getSubmissionLatest = (runId) => apiFetch(formatPath("submission_latest", { runId }));
  const getSubmissionEmail = (runId) => apiFetch(formatPath("submission_email", { runId }));
  const getSubmissionChangelog = (runId) => apiFetch(formatPath("submission_changelog", { runId }));
  const listSchedules = () => apiFetch(getPath("schedules_list"));
  const createSchedule = (payload) => apiFetch(getPath("schedules_create"), { method: "POST", body: payload });
  const updateSchedule = (scheduleId, payload) =>
    apiFetch(formatPath("schedules_update", { scheduleId }), { method: "PATCH", body: payload });
  const runScheduleNow = (scheduleId, force = false) =>
    apiFetch(formatPath("schedules_run", { scheduleId }, { force }), { method: "POST" });
  const getScheduleHistory = (scheduleId, limit = 50) =>
    apiFetch(formatPath("schedules_history", { scheduleId }, { limit }));
  const importFeedback = (payload) => apiFetch(getPath("feedback_import"), { method: "POST", body: payload });
  const getFeedbackRisk = (runId) => apiFetch(formatPath("feedback_risk", {}, { run_id: runId }));
  const decisionSimulate = (payload) => apiFetch(getPath("decision_simulate"), { method: "POST", body: payload });
  const financeOptimize = (payload) => apiFetch(getPath("finance_optimize"), { method: "POST", body: payload });

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
    getPath,
    formatPath,
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
