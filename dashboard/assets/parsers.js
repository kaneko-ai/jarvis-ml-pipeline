(function (global) {
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function parseJsonl(text) {
        if (!text) return [];
        return text
            .split(/\r?\n/)
            .map(line => line.trim())
            .filter(Boolean)
            .map(line => {
                try {
                    return JSON.parse(line);
                } catch (err) {
                    return null;
                }
            })
            .filter(Boolean);
    }

    function renderMarkdownPreview(text) {
        if (!text) return '';
        return escapeHtml(text).replace(/\r?\n/g, '<br>');
    }

    function normalizeFiles(files) {
        if (!files) return [];
        if (Array.isArray(files)) {
            return files.map((item) => {
                if (typeof item === 'string') {
                    return { name: item };
                }
                if (item && typeof item === 'object') {
                    return {
                        name: item.name || item.filename || item.path || '',
                        url: item.url || item.download_url || null,
                        exists: item.exists
                    };
                }
                return null;
            }).filter(Boolean);
        }
        if (typeof files === 'object') {
            return Object.entries(files)
                .map(([name, info]) => ({
                    name,
                    exists: info && typeof info === 'object' ? info.exists : true,
                    size: info && typeof info === 'object' ? info.size : null
                }))
                .filter(item => item.exists !== false);
        }
        return [];
    }

    function findBySuffix(files, suffix) {
        const list = normalizeFiles(files);
        return list.find(item => item.name && item.name.endsWith(suffix)) || null;
    }

    function findByNameContains(files, token) {
        const list = normalizeFiles(files);
        const lowered = token.toLowerCase();
        return list.find(item => item.name && item.name.toLowerCase().includes(lowered)) || null;
    }

    function inferArtifacts(files) {
        return {
            packageZip: findByNameContains(files, 'package') || findBySuffix(files, 'package.zip'),
            notesZip: findByNameContains(files, 'notes') || findBySuffix(files, 'notes.zip'),
            draftsDocx: findBySuffix(files, '.docx'),
            slidesPptx: findBySuffix(files, '.pptx'),
            manifest: findByNameContains(files, 'manifest') || findBySuffix(files, '.json')
        };
    }

    global.JarvisParsers = {
        escapeHtml,
        parseJsonl,
        renderMarkdownPreview,
        normalizeFiles,
        findBySuffix,
        findByNameContains,
        inferArtifacts
    };
})(window);
