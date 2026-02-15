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
    health: "/api/health",
    health_cron: "/api/health/cron",
    runs_list: "/api/runs",
    runs_detail: "/api/runs/:runId",
    runs_files: "/api/runs/:runId/files",
    runs_events: "/api/runs/:runId/events",
    qa_report: "/api/qa/report",
    feedback_risk: "/api/feedback/risk",
    feedback_import: "/api/feedback/import",
    decision_simulate: "/api/decision/simulate",
  };

  const getApiMap = () => window.api_map_v1 || DEFAULT_API_MAP;

  const buildNotImplementedError = (message, detail = "") => ({
    kind: "NOT_IMPLEMENTED",
    status: 501,
    message,
    detail,
    hint: "未実装：バックエンドAPIが存在しません",
  });

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

  const withTimeout = async (url, request, timeoutMs) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, {
        ...request,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }
  };

  const normalizeThrownError = (error, response = null) => {
    if (error && error.kind) {
      return error;
    }
    if (window.JarvisErrors && typeof window.JarvisErrors.normalizeError === "function") {
      return window.JarvisErrors.normalizeError(error, response);
    }
    return {
      kind: "UNKNOWN",
      status: response?.status || 0,
      message: error?.message || "Unexpected error",
      detail: "",
      hint: "",
    };
  };

  const apiFetch = async (path, options = {}) => {
    if (!path) {
      throw buildNotImplementedError("未実装：バックエンドAPIが存在しません", "path is null");
    }
    const url = buildUrl(path);
    if (!url) {
      throw {
        kind: "CONFIG_ERROR",
        status: 0,
        message: "API_BASE が設定されていません。Settings で設定してください。",
        detail: "missing_api_base",
      };
    }

    const { method = "GET", body, headers = {}, timeout = 15000 } = options;
    const finalHeaders = {
      Accept: "application/json",
      ...headers,
    };

    const token = getApiToken();
    if (!token) {
      throw {
        kind: "UNAUTHORIZED",
        status: 401,
        message: "API_TOKEN が設定されていません。Settings で設定してください。",
        detail: "missing_api_token",
      };
    }
    finalHeaders.Authorization = `Bearer ${token}`;

    let payload = body;
    if (body && !(body instanceof FormData)) {
      finalHeaders["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }

    let response;
    try {
      response = await withTimeout(
        url,
        {
          method,
          headers: finalHeaders,
          body: payload,
        },
        timeout
      );
    } catch (error) {
      if (error?.name === "AbortError") {
        throw {
          kind: "TIMEOUT",
          status: 0,
          message: "リクエストがタイムアウトしました",
          detail: `timeout_ms=${timeout}`,
        };
      }
      throw normalizeThrownError(error);
    }

    const contentType = response.headers.get("content-type") || "";
    const rawText = await response.text();
    let data = null;
    if (rawText) {
      if (contentType.includes("application/json")) {
        try {
          data = JSON.parse(rawText);
        } catch (error) {
          throw {
            kind: "BAD_RESPONSE",
            status: response.status,
            message: "JSON の解析に失敗しました",
            detail: error.message,
          };
        }
      } else {
        data = rawText;
      }
    }

    if (response.status === 401 || response.status === 403) {
      if (!window.location.pathname.endsWith("settings.html")) {
        window.location.href = "settings.html";
      }
      throw {
        kind: "UNAUTHORIZED",
        status: response.status,
        message: "認証エラー: Settingsでトークンを設定してください。",
        detail: typeof data === "string" ? data : JSON.stringify(data || {}),
      };
    }

    if (response.status === 404 || response.status === 501) {
      throw buildNotImplementedError("未実装：バックエンドAPIが存在しません", path);
    }

    if (![200, 201].includes(response.status)) {
      throw {
        kind: response.status >= 500 ? "SERVER_ERROR" : "BAD_RESPONSE",
        status: response.status,
        message: `HTTP ${response.status}`,
        detail: typeof data === "string" ? data : JSON.stringify(data || {}),
      };
    }

    return data;
  };

  const apiFetchSafe = async (path, options = {}) => {
    try {
      const data = await apiFetch(path, options);
      return { ok: true, data };
    } catch (error) {
      return { ok: false, error: normalizeThrownError(error) };
    }
  };

  let capabilitiesCache = null;
  let capabilitiesPromise = null;

  const getCapabilities = async () => {
    if (capabilitiesCache) {
      return { ok: true, data: capabilitiesCache };
    }
    const path = getPath("capabilities") || "/api/capabilities";
    if (capabilitiesPromise) {
      return capabilitiesPromise;
    }
    capabilitiesPromise = apiFetchSafe(path)
      .then((result) => {
        if (result.ok) {
          capabilitiesCache = result.data;
        }
        return result;
      })
      .finally(() => {
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
      return buildUrl(`/api/runs/${encodeURIComponent(runId)}/files/${encodeURIComponent(file)}`);
    }
    if (isAbsoluteUrl(file.url)) return file.url;
    if (isAbsoluteUrl(file.download_url)) return file.download_url;
    if (isAbsoluteUrl(file.downloadUrl)) return file.downloadUrl;
    return (
      (file.path
        ? buildUrl(`/api/runs/${encodeURIComponent(runId)}/files/${encodeURIComponent(file.path)}`)
        : null) ||
      (file.key
        ? buildUrl(`/api/runs/${encodeURIComponent(runId)}/files/${encodeURIComponent(file.key)}`)
        : null)
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

  const listRuns = () => apiFetch(getPath("runs_list") || "/api/runs");
  const getRun = (runId) => apiFetch(formatPath("runs_detail", { runId }) || `/api/runs/${encodeURIComponent(runId)}`);
  const listRunFiles = (runId) =>
    apiFetch(formatPath("runs_files", { runId }) || `/api/runs/${encodeURIComponent(runId)}/files`);
  const getRunEventsUrl = (runId) =>
    buildUrl(formatPath("runs_events", { runId }) || `/api/runs/${encodeURIComponent(runId)}/events`);
  const getHealth = () => apiFetch(getPath("health") || "/api/health");
  const getCronHealth = () => apiFetch(getPath("health_cron") || "/api/health/cron");
  const createRun = (payload) => apiFetch(getPath("runs_list") || "/api/runs", { method: "POST", body: payload });
  const getQaReport = (runId) => apiFetch(formatPath("qa_report", {}, { run_id: runId }) || `/api/qa/report?run_id=${encodeURIComponent(runId)}`);
  const importFeedback = (payload) => apiFetch(getPath("feedback_import") || "/api/feedback/import", { method: "POST", body: payload });
  const getFeedbackRisk = (runId) =>
    apiFetch(formatPath("feedback_risk", {}, { run_id: runId }) || `/api/feedback/risk?run_id=${encodeURIComponent(runId)}`);
  const decisionSimulate = (payload) =>
    apiFetch(getPath("decision_simulate") || "/api/decision/simulate", { method: "POST", body: payload });

  return {
    STORAGE_BASE,
    STORAGE_TOKEN,
    getApiBase,
    getApiToken,
    setApiConfig,
    clearApiConfig,
    getApiMap,
    getPath,
    formatPath,
    buildUrl,
    apiFetch,
    apiFetchSafe,
    resolveFileUrl,
    normalizeFileEntry,
    listRuns,
    getRun,
    listRunFiles,
    getRunEventsUrl,
    getHealth,
    getCronHealth,
    createRun,
    getQaReport,
    importFeedback,
    getFeedbackRisk,
    decisionSimulate,
    getCapabilities,
    isFeatureEnabled,
    buildNotImplementedError,
  };
})();

window.app = app;
