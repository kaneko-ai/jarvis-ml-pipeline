(function (global) {
    const KEY_API_BASE = 'JAVIS_API_BASE';
    const KEY_API_TOKEN = 'JAVIS_API_TOKEN';
    const KEY_CAP_CACHE = 'JAVIS_CAP_CACHE';
    const KEY_LAST_RUN = 'JAVIS_LAST_RUN';

    function getApiBase() {
        return (localStorage.getItem(KEY_API_BASE) || '').trim();
    }

    function setApiBase(value) {
        if (value === null || value === undefined) {
            localStorage.removeItem(KEY_API_BASE);
            return;
        }
        localStorage.setItem(KEY_API_BASE, String(value).trim());
    }

    function getToken() {
        return (localStorage.getItem(KEY_API_TOKEN) || '').trim();
    }

    function setToken(value) {
        if (value === null || value === undefined) {
            localStorage.removeItem(KEY_API_TOKEN);
            return;
        }
        localStorage.setItem(KEY_API_TOKEN, String(value).trim());
    }

    function getCapCache() {
        const raw = localStorage.getItem(KEY_CAP_CACHE);
        if (!raw) return null;
        try {
            const parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== 'object') return null;
            if (parsed.expiresAt && Date.now() > parsed.expiresAt) {
                localStorage.removeItem(KEY_CAP_CACHE);
                return null;
            }
            return parsed.value || null;
        } catch (err) {
            localStorage.removeItem(KEY_CAP_CACHE);
            return null;
        }
    }

    function setCapCache(value, ttlMs) {
        const payload = {
            value,
            expiresAt: ttlMs ? Date.now() + ttlMs : null
        };
        localStorage.setItem(KEY_CAP_CACHE, JSON.stringify(payload));
    }

    function clearAllSettings() {
        [KEY_API_BASE, KEY_API_TOKEN, KEY_CAP_CACHE, KEY_LAST_RUN].forEach((key) => {
            localStorage.removeItem(key);
        });
    }

    function getLastRun() {
        return (localStorage.getItem(KEY_LAST_RUN) || '').trim();
    }

    function setLastRun(value) {
        if (value === null || value === undefined) {
            localStorage.removeItem(KEY_LAST_RUN);
            return;
        }
        localStorage.setItem(KEY_LAST_RUN, String(value).trim());
    }

    global.JarvisStorage = {
        getApiBase,
        setApiBase,
        getToken,
        setToken,
        getCapCache,
        setCapCache,
        clearAllSettings,
        getLastRun,
        setLastRun
    };
})(window);
