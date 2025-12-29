const ApiMap = (() => {
    let apiBase = '';
    let apiMap = null;
    let apiMapPromise = null;

    function setApiBase(base) {
        apiBase = base || '';
    }

    async function loadApiMap() {
        if (apiMap) {
            return apiMap;
        }
        if (!apiMapPromise) {
            const url = `${apiBase}/api/map/v1`;
            apiMapPromise = fetch(url, { cache: 'no-store' })
                .then((res) => {
                    if (!res.ok) {
                        throw new Error(`api map load failed: ${res.status}`);
                    }
                    return res.json();
                })
                .then((data) => {
                    apiMap = data;
                    return apiMap;
                });
        }
        return apiMapPromise;
    }

    function requireApiMap() {
        if (!apiMap) {
            throw new Error('API map not loaded');
        }
        return apiMap;
    }

    function getPath(key) {
        const map = requireApiMap();
        const path = map.base_paths[key];
        if (!path) {
            throw new Error(`Unknown API map key: ${key}`);
        }
        return `${apiBase}${path}`;
    }

    function formatPath(key, params = {}) {
        const map = requireApiMap();
        let path = map.base_paths[key];
        if (!path) {
            throw new Error(`Unknown API map key: ${key}`);
        }
        Object.entries(params).forEach(([paramKey, value]) => {
            path = path.replace(`{${paramKey}}`, encodeURIComponent(value));
        });
        return `${apiBase}${path}`;
    }

    function withQuery(url, query) {
        if (!query || Object.keys(query).length === 0) {
            return url;
        }
        const resolved = new URL(url, window.location.origin);
        Object.entries(query).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                resolved.searchParams.set(key, value);
            }
        });
        return resolved.toString();
    }

    function apiFetch(key, { pathParams, query, ...options } = {}) {
        const baseUrl = pathParams ? formatPath(key, pathParams) : getPath(key);
        const url = withQuery(baseUrl, query);
        return fetch(url, options);
    }

    return {
        setApiBase,
        loadApiMap,
        getPath,
        formatPath,
        apiFetch,
    };
})();

window.ApiMap = ApiMap;
