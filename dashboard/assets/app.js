const app = (() => {
  const {
    STORAGE_BASE,
    STORAGE_TOKEN,
    getApiBase,
    getApiToken,
    setApiConfig,
    clearApiConfig,
  } = storage;

  const isAbsoluteUrl = (value) => /^https?:\/\//i.test(value || "");

  const DEFAULT_API_MAP = {
    capabilities: "/api/capabilities",
    runs_list: "/api/runs",
    runs_detail: "/api/runs/:runId",
    research_rank: "/api/research/rank",
    research_paper: "/api/research/paper/:paperId",
    qa_report: "/api/qa/report",
    submission_build: "/api/submission/build",
    submission_latest: "/api/submission/latest/:runId",
    submission_email: "/api/submission/email/:runId",
    submission_changelog: "/api/submission/changelog/:runId",
    schedules_list: "/api/schedules",
    schedules_create: "/api/schedules",
    schedules_update: "/api/schedules/:scheduleId",
    schedules_run: "/api/schedules/:scheduleId/run",
  };

  const getApiMap = () => window.api_map_v1 || DEFAULT_API_MAP;

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
    if (isAbsoluteUrl(path)) return path;
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
    if (!token) {
      throw new Error("API_TOKENが未設定です。Settingsで設定してください。");
    }
    finalHeaders.Authorization = `Bearer ${token}`;
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

    if (response.status === 401) {
      if (!window.location.pathname.endsWith("settings.html")) {
        window.location.href = "settings.html";
      }
      throw new Error("認証エラー: Settingsでトークンを設定してください。");
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

  let capabilitiesCache = null;
  let capabilitiesPromise = null;

  const getCapabilities = async () => {
    if (capabilitiesCache) {
      return { ok: true, data: capabilitiesCache };
    }
    if (!getApiBase()) {
      return { ok: false, error: new Error("API_BASEが未設定です。Settingsで設定してください。") };
    }
    if (capabilitiesPromise) {
      return capabilitiesPromise;
    }
    capabilitiesPromise = apiFetchSafe("/api/capabilities").then((result) => {
      if (result.ok) {
        capabilitiesCache = result.data;
      }
      return result;
    }).finally(() => {
      capabilitiesPromise = null;
    });
    return capabilitiesPromise;
  };

  const isFeatureEnabled = (capabilities, featureKey) => {
    if (!capabilities || !capabilities.features) return false;
    return Boolean(capabilities.features[featureKey]);
  };

  const resolveFileUrl = (runId, file) => {
    if (!file) return null;
    if (typeof file === "string") {
      if (isAbsoluteUrl(file)) return file;
      return buildUrl(`/api/runs/${runId}/files/${encodeURIComponent(file)}`);
    }
    if (isAbsoluteUrl(file.url)) return file.url;
    if (isAbsoluteUrl(file.download_url)) return file.download_url;
    if (isAbsoluteUrl(file.downloadUrl)) return file.downloadUrl;
    return (
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
  const listRunFiles = (runId) => apiFetch(`/api/runs/${runId}/files`);
  const getRunEventsUrl = (runId) => buildUrl(`/api/runs/${runId}/events`);
  const getHealth = () => apiFetch("/api/health");
  const getCronHealth = () => apiFetch("/api/health/cron");
  const createRun = (payload) => apiFetch("/api/runs", { method: "POST", body: payload });
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
    apiFetch(`/api/schedules/${encodeURIComponent(scheduleId)}/history?limit=${limit}`);
  const importFeedback = (payload) => apiFetch("/api/feedback/import", { method: "POST", body: payload });
  const getFeedbackRisk = (runId) => apiFetch(`/api/feedback/risk?run_id=${encodeURIComponent(runId)}`);
  const decisionSimulate = (payload) => apiFetch("/api/decision/simulate", { method: "POST", body: payload });
  const financeOptimize = (payload) => apiFetch("/api/finance/optimize", { method: "POST", body: payload });
  const getKbStatus = () => apiFetch("/api/kb/status");
  const getKbTopic = (topic) => apiFetch(`/api/kb/topic/${encodeURIComponent(topic)}`);
  const getKbPaper = (pmid) => apiFetch(`/api/kb/paper/${encodeURIComponent(pmid)}`);
  const listPacks = () => apiFetch("/api/packs");
  const generatePack = () => apiFetch("/api/packs/generate", { method: "POST" });
  const buildPackDownloadUrl = (packId) => buildUrl(`/api/packs/${encodeURIComponent(packId)}/download`);

  return {
    STORAGE_BASE,
    STORAGE_TOKEN,
    getApiBase,
    getApiToken,
    setApiConfig,
    clearApiConfig,
    apiFetch,
    apiFetchSafe,
    resolveFileUrl,
    normalizeFileEntry,
    getPath,
    formatPath,
    listRuns,
    getRun,
    listRunFiles,
    getRunEventsUrl,
    getHealth,
    getCronHealth,
    createRun,
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
    getKbStatus,
    getKbTopic,
    getKbPaper,
    listPacks,
    generatePack,
    buildPackDownloadUrl,
    buildUrl,
    getCapabilities,
    isFeatureEnabled,
  };
})();

window.app = app;
