let API_BASE = '';
const scenarioCards = document.getElementById('scenario-cards');
const cashflowBody = document.getElementById('cashflow-body');
const optimizeNote = document.getElementById('optimize-note');

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

function statusBadge(status) {
    if (status === 'feasible') return 'success';
    if (status === 'risky') return 'warning';
    return 'danger';
}

function renderScenarios(scenarios) {
    scenarioCards.innerHTML = '';
    scenarios.forEach((scenario) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
                    <h3>${scenario.name}</h3>
                    <p class="badge ${statusBadge(scenario.status)}">${scenario.status}</p>
                    <p>Expected Balance End: ${scenario.expected_balance_end.toFixed(0)}</p>
                    <p>Bankruptcy Risk: ${(scenario.bankruptcy_risk * 100).toFixed(1)}%</p>
                    <p>Research Hours Avg: ${scenario.research_hours_avg.toFixed(1)}</p>
                    <p class="note">${scenario.recommendation}</p>
                `;
        card.addEventListener('click', () => renderCashflows(scenario.summary.monthly));
        scenarioCards.appendChild(card);
    });
    if (scenarios.length) {
        renderCashflows(scenarios[0].summary.monthly);
    }
}

function renderCashflows(monthly) {
    cashflowBody.innerHTML = '';
    monthly.forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
                    <td>${row.month}</td>
                    <td>${row.expected_balance_end.toFixed(0)}</td>
                    <td>${row.downside_balance_end.toFixed(0)}</td>
                `;
        cashflowBody.appendChild(tr);
    });
}

async function loadSimulation() {
    const response = await ApiMap.apiFetch('finance_simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ months: 36 }),
    });
    const data = await response.json();
    renderScenarios(data.scenarios || []);
}

async function runOptimize() {
    const response = await ApiMap.apiFetch('finance_optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ months: 36 }),
    });
    const data = await response.json();
    optimizeNote.textContent = `推奨シナリオ: ${data.scenario} (${data.status}) - ${data.recommendation}`;
}

async function downloadReport() {
    const url = ApiMap.getPath('finance_download') + '?format=zip';
    window.location.href = url;
}

function startFinanceDashboard() {
    document.getElementById('optimize-btn').addEventListener('click', runOptimize);
    document.getElementById('download-btn').addEventListener('click', downloadReport);
    loadSimulation();
}

initializeApi().then(() => {
    startFinanceDashboard();
});
