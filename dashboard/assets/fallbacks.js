(function (global) {
    async function resolveWithFallback({ apiFn, fileFn, noneFn }) {
        try {
            return await apiFn();
        } catch (err) {
            if (err && err.kind === 'NOT_IMPLEMENTED') {
                if (fileFn) {
                    try {
                        return await fileFn();
                    } catch (fileErr) {
                        if (noneFn) {
                            return await noneFn();
                        }
                        throw fileErr;
                    }
                }
                if (noneFn) {
                    return await noneFn();
                }
            }
            throw err;
        }
    }

    global.JarvisFallbacks = {
        resolveWithFallback
    };
})(window);
