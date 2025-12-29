(function (global) {
    const CACHE_TTL_MS = 5 * 60 * 1000;

    const ENDPOINTS = {
        health: '/api/health',
        runs_list: '/api/runs',
        run_detail: '/api/runs/{id}',
        run_events: '/api/runs/{id}/events',
        research_rank: '/api/research/rank',
        research_paper: '/api/research/paper/{paper_id}',
        qa_report: '/api/qa/report',
        export_package: '/api/export/run/{id}/package',
        submission_build: '/api/submission/build',
        feedback_risk: '/api/feedback/risk',
        decision_simulate: '/api/decision/simulate',
        finance_optimize: '/api/finance/optimize'
    };

    function buildUrl(path) {
        const base = global.JarvisStorage.getApiBase();
        if (!base) return path;
        return `${base.replace(/\/$/, '')}${path}`;
    }

    async function fetchWithMethod(url, method, headers) {
        try {
            const res = await fetch(url, { method, headers });
            return res;
        } catch (err) {
            return null;
        }
    }

    async function checkEndpoint(path) {
        const token = global.JarvisStorage.getToken();
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const url = buildUrl(path);
        let res = await fetchWithMethod(url, 'HEAD', headers);
        if (!res || res.status === 405 || res.status === 400) {
            res = await fetchWithMethod(url, 'GET', headers);
        }
        if (!res) return false;
        if (res.status === 401 || res.status === 403) return true;
        if (res.status === 404 || res.status === 501) return false;
        return res.status < 500;
    }

    async function resolveRunId() {
        try {
            const url = buildUrl('/api/runs?limit=1');
            const token = global.JarvisStorage.getToken();
            const headers = token ? { Authorization: `Bearer ${token}` } : {};
            const res = await fetch(url, { headers });
            if (!res.ok) return null;
            const data = await res.json();
            const run = data.runs && data.runs.length ? data.runs[0] : null;
            return run ? run.run_id : null;
        } catch (err) {
            return null;
        }
    }

    async function getCapabilities(force = false) {
        if (!force) {
            const cached = global.JarvisStorage.getCapCache();
            if (cached) return cached;
        }

        const result = {
            checkedAt: new Date().toISOString(),
            endpoints: {}
        };

        result.endpoints.health = await checkEndpoint(ENDPOINTS.health);
        result.endpoints.runs_list = await checkEndpoint(ENDPOINTS.runs_list);

        let runId = null;
        if (result.endpoints.runs_list) {
            runId = await resolveRunId();
        }

        const runDetailPath = runId ? `/api/runs/${runId}` : null;
        const runEventsPath = runId ? `/api/runs/${runId}/events` : null;

        result.endpoints.run_detail = runDetailPath ? await checkEndpoint(runDetailPath) : result.endpoints.runs_list;
        result.endpoints.run_events = runEventsPath ? await checkEndpoint(runEventsPath) : result.endpoints.runs_list;

        const remaining = {
            research_rank: ENDPOINTS.research_rank,
            research_paper: ENDPOINTS.research_paper.replace('{paper_id}', 'sample'),
            qa_report: ENDPOINTS.qa_report,
            export_package: ENDPOINTS.export_package.replace('{id}', 'sample'),
            submission_build: ENDPOINTS.submission_build,
            feedback_risk: ENDPOINTS.feedback_risk,
            decision_simulate: ENDPOINTS.decision_simulate,
            finance_optimize: ENDPOINTS.finance_optimize
        };

        for (const [key, path] of Object.entries(remaining)) {
            result.endpoints[key] = await checkEndpoint(path);
        }

        global.JarvisStorage.setCapCache(result, CACHE_TTL_MS);
        return result;
    }

    global.JarvisCapabilities = {
        getCapabilities,
        ENDPOINTS
    };
})(window);
