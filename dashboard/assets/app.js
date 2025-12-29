(function (global) {
    const storage = global.JarvisStorage;
    const errors = global.JarvisErrors;
    const parsers = global.JarvisParsers;
    const fallbacks = global.JarvisFallbacks;
    const capabilities = global.JarvisCapabilities;

    const DEFAULT_TIMEOUT_MS = 15000;

    function buildUrl(path) {
        if (!path) return '';
        if (/^https?:\/\//i.test(path)) return path;
        const base = storage.getApiBase();
        if (!base) return path;
        return `${base.replace(/\/$/, '')}${path}`;
    }

    async function apiFetch(path, opts = {}) {
        const controller = new AbortController();
        const timeout = opts.timeoutMs || DEFAULT_TIMEOUT_MS;
        const token = storage.getToken();
        const headers = new Headers(opts.headers || {});
        if (token) {
            headers.set('Authorization', `Bearer ${token}`);
        }
        const url = buildUrl(path);
        const timer = setTimeout(() => controller.abort(), timeout);
        try {
            const response = await fetch(url, {
                ...opts,
                headers,
                signal: controller.signal
            });
            if (!response.ok) {
                throw errors.normalizeError(null, response);
            }
            return response;
        } catch (err) {
            if (err && err.kind) {
                throw err;
            }
            throw errors.normalizeError(err, err && err.response ? err.response : null);
        } finally {
            clearTimeout(timer);
        }
    }

    async function apiJson(path, opts = {}) {
        const response = await apiFetch(path, opts);
        try {
            return await response.json();
        } catch (err) {
            throw errors.normalizeError(err, response);
        }
    }

    async function apiText(path, opts = {}) {
        const response = await apiFetch(path, opts);
        try {
            return await response.text();
        } catch (err) {
            throw errors.normalizeError(err, response);
        }
    }

    function apiDownloadUrl(path) {
        return buildUrl(path);
    }

    async function bootstrapSettings() {
        if (storage.getApiBase()) return storage.getApiBase();
        try {
            const response = await fetch('config.json', { cache: 'no-store' });
            if (!response.ok) return '';
            const config = await response.json();
            if (config.apiBase) {
                storage.setApiBase(config.apiBase);
                return config.apiBase;
            }
        } catch (err) {
            return '';
        }
        return '';
    }

    async function ensureCapability(key) {
        const caps = await capabilities.getCapabilities();
        if (caps && caps.endpoints && caps.endpoints[key] === false) {
            throw errors.normalizeError({ kind: 'NOT_IMPLEMENTED', message: 'Endpoint not implemented' }, { status: 404 });
        }
    }

    async function listRuns() {
        await ensureCapability('runs_list');
        const data = await apiJson('/api/runs?limit=50');
        return data.runs || data.data || [];
    }

    async function getRun(runId) {
        await ensureCapability('run_detail');
        return await apiJson(`/api/runs/${encodeURIComponent(runId)}`);
    }

    async function getRunFiles(runId) {
        try {
            const data = await apiJson(`/api/runs/${encodeURIComponent(runId)}/files`);
            return data.files || data;
        } catch (err) {
            if (err.kind === 'NOT_IMPLEMENTED') {
                const run = await getRun(runId);
                return run.files || [];
            }
            throw err;
        }
    }

    async function getRunFileText(runId, filename) {
        return await apiText(`/api/runs/${encodeURIComponent(runId)}/files/${encodeURIComponent(filename)}`);
    }

    async function getRunProgress(runId) {
        const run = await getRun(runId);
        return {
            status: run.status,
            progress: run.progress || 0,
            counts: run.counts || {},
            metrics: run.metrics || {},
            run
        };
    }

    async function getRunEvents(runId) {
        try {
            await ensureCapability('run_events');
            return await apiJson(`/api/runs/${encodeURIComponent(runId)}/events?tail=200`);
        } catch (err) {
            if (err.kind === 'NOT_IMPLEMENTED') {
                return {
                    events: [],
                    poll: true,
                    run: await getRun(runId)
                };
            }
            throw err;
        }
    }

    async function getRank(runId, topK, query) {
        return fallbacks.resolveWithFallback({
            apiFn: async () => {
                await ensureCapability('research_rank');
                return await apiJson(`/api/research/rank?run_id=${encodeURIComponent(runId)}&q=${encodeURIComponent(query || '')}&top_k=${topK || 50}&mode=hybrid`);
            },
            fileFn: async () => {
                const text = await getRunFileText(runId, 'research_rank.json');
                return JSON.parse(text);
            },
            noneFn: async () => ({ results: [], status: 'NOT_IMPLEMENTED' })
        });
    }

    async function getPaperClaims(runId, paperId) {
        return fallbacks.resolveWithFallback({
            apiFn: async () => {
                await ensureCapability('research_paper');
                return await apiJson(`/api/research/paper/${encodeURIComponent(paperId)}?run_id=${encodeURIComponent(runId)}`);
            },
            fileFn: async () => {
                const text = await getRunFileText(runId, `claims/${paperId}.claims.jsonl`);
                return { claims: parsers.parseJsonl(text) };
            },
            noneFn: async () => ({ claims: [], status: 'NOT_IMPLEMENTED' })
        });
    }

    async function getQAReport(runId) {
        return fallbacks.resolveWithFallback({
            apiFn: async () => {
                await ensureCapability('qa_report');
                return await apiJson(`/api/qa/report?run_id=${encodeURIComponent(runId)}`);
            },
            fileFn: async () => {
                try {
                    const jsonText = await getRunFileText(runId, 'qa_report.json');
                    return { format: 'json', data: JSON.parse(jsonText) };
                } catch (err) {
                    const mdText = await getRunFileText(runId, 'qa_report.md');
                    return { format: 'markdown', data: mdText };
                }
            },
            noneFn: async () => ({ format: 'none', data: null, status: 'NOT_IMPLEMENTED' })
        });
    }

    async function getExportLinks(runId) {
        const files = await getRunFiles(runId);
        const artifacts = parsers.inferArtifacts(files);
        const links = [];
        const mapping = {
            packageZip: 'package.zip',
            notesZip: 'notes.zip',
            draftsDocx: 'drafts.docx',
            slidesPptx: 'slides.pptx',
            manifest: 'manifest.json'
        };
        Object.entries(artifacts).forEach(([key, file]) => {
            if (file && file.name) {
                links.push({
                    label: mapping[key] || file.name,
                    filename: file.name,
                    url: apiDownloadUrl(`/api/runs/${encodeURIComponent(runId)}/files/${encodeURIComponent(file.name)}`)
                });
            }
        });
        return links;
    }

    async function buildSubmission(runId, payload) {
        await ensureCapability('submission_build');
        return await apiJson(`/api/submission/build?run_id=${encodeURIComponent(runId)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {})
        });
    }

    async function getSubmissionLatest(runId) {
        try {
            await ensureCapability('submission_build');
            return await apiJson(`/api/submission/latest?run_id=${encodeURIComponent(runId)}`);
        } catch (err) {
            const files = await getRunFiles(runId);
            const submission = parsers.findByNameContains(files, 'submission') || parsers.findBySuffix(files, '.zip');
            return submission ? {
                filename: submission.name,
                url: apiDownloadUrl(`/api/runs/${encodeURIComponent(runId)}/files/${encodeURIComponent(submission.name)}`)
            } : null;
        }
    }

    async function getFeedbackRisk(runId) {
        await ensureCapability('feedback_risk');
        return await apiJson(`/api/feedback/risk?run_id=${encodeURIComponent(runId)}`);
    }

    async function importFeedback(text, meta) {
        await ensureCapability('feedback_risk');
        return await apiJson('/api/feedback/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, meta })
        });
    }

    async function simulateDecision(input) {
        await ensureCapability('decision_simulate');
        return await apiJson('/api/decision/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(input || {})
        });
    }

    async function optimizeFinance(input) {
        await ensureCapability('finance_optimize');
        return await apiJson('/api/finance/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(input || {})
        });
    }

    async function simulateFinance(input) {
        await ensureCapability('finance_optimize');
        return await apiJson('/api/finance/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(input || {})
        });
    }

    async function listJobs(payload) {
        return await apiJson('/api/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {})
        });
    }

    async function getJob(jobId) {
        return await apiJson(`/api/jobs/${encodeURIComponent(jobId)}`);
    }

    async function getJobEvents(jobId) {
        return await apiJson(`/api/jobs/${encodeURIComponent(jobId)}/events?tail=200`);
    }

    async function searchCorpus(query, topK) {
        return await apiJson(`/api/search?q=${encodeURIComponent(query)}&top_k=${topK || 20}`);
    }

    async function uploadFiles(endpoint, files) {
        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }
        return await apiJson(endpoint, {
            method: 'POST',
            body: formData
        });
    }

    function getManifestUrl(runId) {
        return apiDownloadUrl(`/api/runs/${encodeURIComponent(runId)}/manifest`);
    }

    global.JarvisApp = {
        apiFetch,
        apiJson,
        apiText,
        apiDownloadUrl,
        bootstrapSettings,
        listRuns,
        getRun,
        getRunFiles,
        getRunFileText,
        getRunProgress,
        getRunEvents,
        getRank,
        getPaperClaims,
        getQAReport,
        getExportLinks,
        buildSubmission,
        getSubmissionLatest,
        getFeedbackRisk,
        importFeedback,
        simulateDecision,
        optimizeFinance,
        simulateFinance,
        listJobs,
        getJob,
        getJobEvents,
        searchCorpus,
        uploadFiles,
        getManifestUrl
    };
})(window);
