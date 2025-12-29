(function (global) {
    function renderStatusBadge(kind) {
        const labelMap = {
            READY: 'READY',
            BLOCKED: 'BLOCKED',
            UNAUTHORIZED: 'UNAUTHORIZED',
            NO_CONNECTION: 'NO_CONNECTION',
            NOT_IMPLEMENTED: 'NOT_IMPLEMENTED'
        };
        const label = labelMap[kind] || kind;
        return `<span class="status-badge status-${kind}">${label}</span>`;
    }

    function renderErrorPanel(normalizedError) {
        if (!normalizedError) return '';
        const hint = normalizedError.hint ? `<div class="error-hint">${normalizedError.hint}</div>` : '';
        const detail = normalizedError.detail ? `<div class="error-detail">${normalizedError.detail}</div>` : '';
        return `
            <div class="error-panel">
                <div class="error-header">${normalizedError.kind || 'ERROR'} (${normalizedError.status || '-'})</div>
                <div class="error-message">${normalizedError.message || ''}</div>
                ${detail}
                ${hint}
            </div>
        `;
    }

    function toast(message, type = 'info') {
        const toastEl = document.createElement('div');
        toastEl.className = `toast toast-${type}`;
        toastEl.textContent = message;
        document.body.appendChild(toastEl);
        setTimeout(() => toastEl.remove(), 3200);
    }

    function renderEmptyState(title, message, actions = []) {
        const actionHtml = actions.map(action => {
            return `<button class="btn btn-secondary" data-action="${action.id}">${action.label}</button>`;
        }).join('');
        return `
            <div class="empty-state">
                <h3>${title}</h3>
                <p>${message}</p>
                <div class="empty-actions">${actionHtml}</div>
            </div>
        `;
    }

    global.JarvisUI = {
        renderStatusBadge,
        renderErrorPanel,
        toast,
        renderEmptyState
    };
})(window);
