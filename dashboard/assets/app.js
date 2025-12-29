let API_BASE = '';
let runs = [];
let currentTab = 'overview';
let currentJobId = null;
let jobPoller = null;
let eventPoller = null;
let researchResults = [];
let tierFilter = 'all';

async function loadConfig() {
    try {
        const res = await fetch('config.json', { cache: 'no-store' });
        if (res.ok) {
            const config = await res.json();
            API_BASE = config.apiBase || '';
        }
    } catch (e) {
        API_BASE = '';
    }
}

async function initializeApi() {
    await loadConfig();
    ApiMap.setApiBase(API_BASE);
    try {
        await ApiMap.loadApiMap();
    } catch (error) {
        console.error('Failed to load API map:', error);
    }
}

// === Tab Navigation ===
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));

    document.getElementById('tab-' + tabId).classList.add('active');
    document.querySelector(`.nav-tab[onclick="showTab('${tabId}')"]`).classList.add('active');
    currentTab = tabId;
}

function resolveRunId() {
    const input = document.getElementById('research-run-id');
    if (input && input.value.trim()) {
        return input.value.trim();
    }
    if (currentJobId) {
        return currentJobId;
    }
    if (runs.length > 0) {
        return runs[0].run_id;
    }
    return '';
}

async function loadResearchRank() {
    const runId = resolveRunId();
    const query = document.getElementById('research-query').value.trim();
    const topK = document.getElementById('research-top-k').value || 50;
    if (!runId) {
        document.getElementById('research-results').innerHTML = '<p>run_id がありません。</p>';
        return;
    }

    try {
        const res = await ApiMap.apiFetch('research_rank', {
            query: {
                run_id: runId,
                q: query,
                top_k: topK,
                mode: 'hybrid',
            },
        });
        if (!res.ok) {
            throw new Error(await res.text());
        }
        const payload = await res.json();
        researchResults = payload.results || [];
        renderResearchResults();
    } catch (err) {
        document.getElementById('research-results').innerHTML = `<p style="color: var(--danger);">rank failed: ${err}</p>`;
    }
}

function setTierFilter(tier) {
    tierFilter = tier;
    renderResearchResults();
}

function renderResearchResults() {
    const container = document.getElementById('research-results');
    if (!researchResults.length) {
        container.innerHTML = '<p>結果がありません。</p>';
        return;
    }
    const filtered = tierFilter === 'all'
        ? researchResults
        : researchResults.filter(item => item.tier === tierFilter);

    container.innerHTML = filtered.map(item => {
        const auditFlags = (item.audit_flags || []).map(flag => `<span class="badge badge-warning">${flag}</span>`).join(' ');
        const oaBadge = item.oa_status ? `<span class="badge badge-success">${item.oa_status}</span>` : '';
        const claims = (item.top_claims || []).map(claim => {
            const weak = (claim.audit_flags || []).includes('weak_evidence');
            const evidenceHtml = (claim.evidence || []).map(ev => `
                        <div class="evidence-item">📌 ${ev.chunk_id} (${ev.locator?.section || 'section'}:${ev.locator?.paragraph_index || 0}) — ${ev.quote}</div>
                    `).join('');
            return `
                        <div class="claim-item ${weak ? 'claim-warning' : ''}">
                            <div><strong>${claim.claim_type}</strong>: ${claim.claim_text}</div>
                            ${weak ? '<div style="color: var(--warning); font-size: 0.85em;">⚠ weak evidence</div>' : ''}
                            ${evidenceHtml}
                        </div>
                    `;
        }).join('');

        return `
                    <div class="paper-card">
                        <h4>${item.title || item.canonical_paper_id}</h4>
                        <div class="paper-meta">
                            <span class="tier-badge tier-${item.tier}">Tier ${item.tier}</span>
                            <span>score ${item.score}</span>
                            <span>${item.year || ''}</span>
                            <span>${item.journal || ''}</span>
                            ${oaBadge}
                            ${auditFlags}
                        </div>
                        <details style="margin-top: 10px;">
                            <summary>Top claims (${(item.top_claims || []).length})</summary>
                            ${claims || '<div class="claim-item">No claims</div>'}
                        </details>
                    </div>
                `;
    }).join('');
}

function downloadManifest() {
    const runId = resolveRunId();
    if (!runId) {
        alert('run_id がありません');
        return;
    }
    const url = ApiMap.formatPath('run_manifest', { run_id: runId });
    window.open(url, '_blank');
}

// === KPI Update (S-02: Fixed Definition) ===
function updateKPIs() {
    const total = runs.length;
    const successful = runs.filter(r => r.status === 'success').length;
    const contractValid = runs.filter(r => r.contract_valid).length;
    const avgCoverage = runs.length > 0
        ? runs.reduce((sum, r) => sum + (r.metrics?.evidence_coverage || 0), 0) / runs.length
        : 0;

    // Total papers/claims from all runs
    let totalPapers = 0, totalClaims = 0;
    runs.forEach(r => {
        totalPapers += r.metrics?.paper_count || 0;
        totalClaims += r.metrics?.claim_count || 0;
    });

    document.getElementById('kpi-runs').textContent = total;
    document.getElementById('kpi-success').textContent = total > 0 ? `${((successful / total) * 100).toFixed(0)}%` : '-';
    document.getElementById('kpi-coverage').textContent = `${(avgCoverage * 100).toFixed(1)}%`;
    document.getElementById('kpi-contract').textContent = `${contractValid}/${total}`;
    document.getElementById('kpi-papers').textContent = totalPapers || '-';
    document.getElementById('kpi-claims').textContent = totalClaims || '-';

    document.getElementById('success-bar').style.width = total > 0 ? `${(successful / total) * 100}%` : '0%';
}

// === Load Runs ===
async function loadRuns() {
    try {
        const res = await ApiMap.apiFetch('runs_list', { query: { limit: 50 } });
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        runs = data.runs || [];
        renderRecentRuns();
        renderRunsTable();
        updateKPIs();
    } catch (e) {
        console.error('Failed to load runs:', e);
        document.getElementById('recent-runs-container').innerHTML = '<p style="color: var(--text-secondary);">データ読み込みエラー</p>';
    }
}

// === Render Recent Runs ===
function renderRecentRuns() {
    const container = document.getElementById('recent-runs-container');
    if (runs.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">実行履歴がありません</p>';
        return;
    }

    let html = '<table class="data-table"><thead><tr><th>Run ID</th><th>Timestamp</th><th>Status</th><th>Gate</th><th>Coverage</th></tr></thead><tbody>';
    runs.slice(0, 10).forEach(run => {
        const statusClass = run.status === 'success' ? 'badge-success' : run.status === 'failed' ? 'badge-danger' : 'badge-warning';
        const coverage = ((run.metrics?.evidence_coverage || 0) * 100).toFixed(1);
        html += `<tr onclick="showRunDetail('${run.run_id}')">
                    <td>${run.run_id?.substring(0, 16) || '-'}...</td>
                    <td>${run.timestamp || '-'}</td>
                    <td><span class="badge ${statusClass}">${run.status || 'unknown'}</span></td>
                    <td>${run.gate_passed ? '✅' : '❌'}</td>
                    <td>${coverage}%</td>
                </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

// === Render Runs Table ===
function renderRunsTable() {
    const container = document.getElementById('runs-table-container');
    if (runs.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">実行履歴がありません</p>';
        return;
    }

    let html = '<table class="data-table"><thead><tr><th>Run ID</th><th>Timestamp</th><th>Status</th><th>Gate</th><th>Contract</th><th>Coverage</th></tr></thead><tbody>';
    runs.forEach(run => {
        const statusClass = run.status === 'success' ? 'badge-success' : run.status === 'failed' ? 'badge-danger' : 'badge-warning';
        const coverage = ((run.metrics?.evidence_coverage || 0) * 100).toFixed(1);
        html += `<tr onclick="showRunDetail('${run.run_id}')">
                    <td>${run.run_id?.substring(0, 20) || '-'}...</td>
                    <td>${run.timestamp || '-'}</td>
                    <td><span class="badge ${statusClass}">${run.status || 'unknown'}</span></td>
                    <td>${run.gate_passed ? '✅' : '❌'}</td>
                    <td>${run.contract_valid ? '10/10' : 'Missing'}</td>
                    <td>${coverage}%</td>
                </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

// === Run Query ===
async function runQuery() {
    const query = document.getElementById('query-input').value;
    if (!query) { showToast('クエリを入力してください', 'warning'); return; }

    const btn = document.getElementById('run-query-btn');
    const status = document.getElementById('query-status');

    btn.disabled = true;
    status.innerHTML = '<div class="spinner"></div><p>パイプライン実行中...</p>';

    try {
        const res = await ApiMap.apiFetch('jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'collect_and_ingest',
                payload: {
                    query,
                    max_results: parseInt(document.getElementById('max-papers').value),
                    oa_only: document.getElementById('oa-only').value === 'true',
                    domain: document.getElementById('domain-select').value,
                },
            }),
        });

        const result = await res.json();
        status.innerHTML = `<p style="color: var(--success);">✅ ジョブ投入: ${result.job_id}</p>`;
        showToast('ジョブ投入完了', 'success');
        startJobPolling(result.job_id);
    } catch (e) {
        status.innerHTML = `<p style="color: var(--danger);">❌ エラー: ${e.message}</p>`;
        showToast('実行エラー', 'danger');
    } finally {
        btn.disabled = false;
    }
}

// === Search Corpus ===
async function searchCorpus() {
    const query = document.getElementById('search-input').value;
    if (!query) { showToast('検索キーワードを入力', 'warning'); return; }

    const container = document.getElementById('search-results');
    container.innerHTML = '<div class="spinner"></div>';

    try {
        const res = await ApiMap.apiFetch('search', {
            query: {
                q: query,
                top_k: 20,
            },
        });
        const data = await res.json();

        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary);">結果がありません</p>';
            return;
        }

        container.innerHTML = data.results.map(r => `
                    <div class="search-result">
                        <div class="search-result-title">${r.paper_title || 'Unknown Paper'}</div>
                        <div class="search-result-meta">
                            📍 ${r.locator?.section || 'Unknown'} | Score: ${r.score?.toFixed(2) || 0}
                        </div>
                        <div class="search-result-snippet">${highlightText(r.text?.substring(0, 300) || '', query)}...</div>
                    </div>
                `).join('');
    } catch (e) {
        container.innerHTML = '<p style="color: var(--danger);">検索エラー</p>';
    }
}

function highlightText(text, query) {
    const words = query.toLowerCase().split(/\s+/);
    let result = text;
    words.forEach(w => {
        if (w.length > 2) {
            const regex = new RegExp(`(${w})`, 'gi');
            result = result.replace(regex, '<span class="highlight">$1</span>');
        }
    });
    return result;
}

// === Collect Papers ===
async function collectPapers() {
    const query = document.getElementById('collect-query').value;
    if (!query) { showToast('検索クエリを入力', 'warning'); return; }

    const status = document.getElementById('collect-status');
    status.innerHTML = '<div class="spinner"></div><p>収集中...</p>';

    try {
        const res = await ApiMap.apiFetch('jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'collect_and_ingest',
                payload: {
                    query,
                    max_results: parseInt(document.getElementById('collect-max').value),
                    oa_only: document.getElementById('collect-oa').checked,
                },
            }),
        });

        const result = await res.json();
        status.innerHTML = `<p style="color: var(--success);">✅ ジョブ投入: ${result.job_id}</p>`;
        showToast('収集ジョブ開始', 'success');
        startJobPolling(result.job_id);
    } catch (e) {
        status.innerHTML = `<p style="color: var(--danger);">❌ エラー: ${e.message}</p>`;
    }
}

// === Upload ===
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');

uploadZone.onclick = () => fileInput.click();
uploadZone.ondragover = e => { e.preventDefault(); uploadZone.classList.add('dragover'); };
uploadZone.ondragleave = () => uploadZone.classList.remove('dragover');
uploadZone.ondrop = async e => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    await handleUpload(e.dataTransfer.files);
};
fileInput.onchange = async e => await handleUpload(e.target.files);

async function handleUpload(files) {
    if (files.length === 0) return;

    const status = document.getElementById('upload-status');
    status.innerHTML = '<div class="spinner"></div><p>アップロード中...</p>';

    const formData = new FormData();
    for (const file of files) formData.append('files', file);

    try {
        let endpointKey = 'upload_pdf';
        if (files[0].name.endsWith('.bib')) endpointKey = 'upload_bibtex';
        else if (files[0].name.endsWith('.zip')) endpointKey = 'upload_zip';

        const res = await ApiMap.apiFetch(endpointKey, { method: 'POST', body: formData });
        const result = await res.json();

        status.innerHTML = `<p style="color: var(--success);">✅ Accepted: ${result.accepted}, Duplicates: ${result.duplicates}, Rejected: ${result.rejected}</p>`;
        showToast('アップロード完了', 'success');
    } catch (e) {
        status.innerHTML = `<p style="color: var(--danger);">❌ ${e.message}</p>`;
    }
}

// === Run Detail Modal ===
async function showRunDetail(runId) {
    const modal = document.getElementById('run-modal');
    const body = document.getElementById('modal-body');
    body.innerHTML = '<div class="spinner"></div>';
    modal.style.display = 'block';

    try {
        const res = await ApiMap.apiFetch('run_detail', { pathParams: { run_id: runId } });
        const run = await res.json();

        body.innerHTML = `
                    <h2>Run: ${runId}</h2>
                    <table class="data-table" style="margin: 20px 0;">
                        <tr><th>Status</th><td><span class="badge ${run.status === 'success' ? 'badge-success' : 'badge-danger'}">${run.status}</span></td></tr>
                        <tr><th>Gate Passed</th><td>${run.gate_passed ? '✅' : '❌'}</td></tr>
                        <tr><th>Contract Valid</th><td>${run.contract_valid ? '✅ 10/10' : '❌ Missing files'}</td></tr>
                        <tr><th>Timestamp</th><td>${run.timestamp || '-'}</td></tr>
                    </table>
                    
                    <h3>📊 Metrics</h3>
                    <table class="data-table" style="margin: 20px 0;">
                        ${Object.entries(run.metrics || {}).map(([k, v]) =>
            `<tr><th>${k}</th><td>${typeof v === 'number' ? v.toFixed(4) : v}</td></tr>`
        ).join('')}
                    </table>

                    <h3>📁 Files</h3>
                    <table class="data-table" style="margin: 20px 0;">
                        ${Object.entries(run.files || {}).map(([name, info]) =>
            `<tr><td>${info.exists ? '✅' : '❌'} ${name}</td><td>${info.size} bytes</td></tr>`
        ).join('')}
                    </table>

                    ${run.report ? `<h3>📝 Report</h3><pre style="max-height: 300px; overflow: auto; background: var(--bg-primary); padding: 15px; border-radius: 8px; white-space: pre-wrap;">${escapeHtml(run.report)}</pre>` : ''}
                `;
    } catch (e) {
        body.innerHTML = `<p style="color: var(--danger);">読み込みエラー: ${e.message}</p>`;
    }
}

function closeModal() { document.getElementById('run-modal').style.display = 'none'; }
window.onclick = e => { if (e.target === document.getElementById('run-modal')) closeModal(); };

// === Utilities ===
function escapeHtml(text) { const d = document.createElement('div'); d.textContent = text; return d.innerHTML; }

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.borderLeftColor = type === 'success' ? 'var(--success)' : type === 'danger' ? 'var(--danger)' : 'var(--warning)';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function refreshAll() {
    loadRuns();
    showToast('更新しました');
}

function startJobPolling(jobId) {
    currentJobId = jobId;
    const card = document.getElementById('job-card');
    card.classList.remove('hidden');
    document.getElementById('job-id').textContent = jobId;

    if (jobPoller) clearInterval(jobPoller);
    if (eventPoller) clearInterval(eventPoller);

    jobPoller = setInterval(fetchJobStatus, 1000);
    eventPoller = setInterval(fetchJobEvents, 1000);
    fetchJobStatus();
    fetchJobEvents();
}

async function fetchJobStatus() {
    if (!currentJobId) return;
    try {
        const res = await ApiMap.apiFetch('job_detail', { pathParams: { job_id: currentJobId } });
        if (!res.ok) return;
        const job = await res.json();
        updateJobCard(job);
        if (['success', 'failed', 'canceled'].includes(job.status)) {
            clearInterval(jobPoller);
            clearInterval(eventPoller);
            loadRuns();
        }
    } catch (e) {
        // ignore polling errors
    }
}

async function fetchJobEvents() {
    if (!currentJobId) return;
    try {
        const res = await ApiMap.apiFetch('job_events', {
            pathParams: { job_id: currentJobId },
            query: { tail: 200 },
        });
        if (!res.ok) return;
        const data = await res.json();
        const log = document.getElementById('job-log');
        log.textContent = (data.events || [])
            .map(ev => `[${ev.timestamp}] ${ev.level || 'info'} ${ev.message || ''}`)
            .join('\n');
        log.scrollTop = log.scrollHeight;
    } catch (e) {
        // ignore polling errors
    }
}

function updateJobCard(job) {
    const statusBadge = document.getElementById('job-status-badge');
    statusBadge.textContent = job.status || '-';
    statusBadge.className = `badge ${job.status === 'success' ? 'badge-success' : job.status === 'failed' ? 'badge-danger' : 'badge-warning'}`;
    document.getElementById('job-step').textContent = `step: ${job.step || '-'}`;
    document.getElementById('job-progress').style.width = `${job.progress || 0}%`;
    document.getElementById('job-progress-label').textContent = `${job.progress || 0}%`;
    const counts = job.counts || {};
    document.getElementById('job-counts').innerHTML = Object.entries(counts)
        .map(([k, v]) => `<div>${k}: ${v}</div>`)
        .join('');
    document.getElementById('job-error').textContent = job.error ? `Error: ${job.error}` : '';
}

// === Initialize ===
initializeApi().then(() => {
    loadRuns();
});
