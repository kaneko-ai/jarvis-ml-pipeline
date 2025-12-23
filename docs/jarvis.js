// JARVIS Dashboard - Main JavaScript Module
const JARVIS = {
    // State
    state: {
        history: JSON.parse(localStorage.getItem('jarvis_history') || '[]'),
        results: [],
        totalSearches: parseInt(localStorage.getItem('jarvis_searches') || '0'),
        totalPapers: parseInt(localStorage.getItem('jarvis_papers') || '0'),
        theme: localStorage.getItem('jarvis_theme') || 'dark',
        lang: localStorage.getItem('jarvis_lang') || 'ja',
        apiQuota: { gemini: 1275, pubmed: 'unlimited' }
    },

    // Initialize
    init() {
        this.updateStats();
        this.loadTheme();
        this.setupKeyboardShortcuts();
        this.startLogSimulation();
        this.initCharts();
        document.querySelectorAll('.card').forEach((card, i) => {
            card.style.animationDelay = `${i * 0.05}s`;
            card.classList.add('animate-in');
        });
    },

    // Stats
    updateStats() {
        const stats = {
            'stat-searches': this.state.totalSearches,
            'stat-papers': this.state.totalPapers
        };
        Object.entries(stats).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) this.animateValue(el, 0, val, 1000);
        });
    },

    animateValue(el, start, end, duration) {
        const range = end - start;
        const startTime = performance.now();
        const update = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            el.textContent = Math.floor(start + range * this.easeOut(progress));
            if (progress < 1) requestAnimationFrame(update);
        };
        requestAnimationFrame(update);
    },

    easeOut(t) { return 1 - Math.pow(1 - t, 3); },

    // Theme
    loadTheme() {
        if (this.state.theme === 'light') document.body.classList.add('light-mode');
        const btn = document.querySelector('.theme-toggle');
        if (btn) btn.textContent = this.state.theme === 'dark' ? '🌙' : '☀️';
    },

    toggleTheme() {
        document.body.classList.toggle('light-mode');
        this.state.theme = document.body.classList.contains('light-mode') ? 'light' : 'dark';
        localStorage.setItem('jarvis_theme', this.state.theme);
        const btn = document.querySelector('.theme-toggle');
        if (btn) btn.textContent = this.state.theme === 'dark' ? '🌙' : '☀️';
        this.showToast('Theme changed', 'info');
    },

    // Tabs
    showTab(tab) {
        ['dashboard', 'research', 'chat', 'settings'].forEach(t => {
            const el = document.getElementById('tab-' + t);
            if (el) el.style.display = t === tab ? 'grid' : 'none';
        });
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
    },

    // Search
    setQuery(query) {
        const input = document.getElementById('search-query');
        if (input) { input.value = query; input.focus(); }
    },

    async runSearch() {
        const query = document.getElementById('search-query')?.value.trim();
        if (!query) return this.showToast('Please enter a search query', 'error');

        const btn = document.getElementById('search-btn');
        const results = document.getElementById('results-area');
        
        if (btn) { btn.disabled = true; btn.innerHTML = '⏳ Searching...'; }
        if (results) results.innerHTML = '<div class="skeleton" style="height:200px;margin:1rem"></div>';
        
        this.addLog('INFO', `Searching: "${query}"`);

        await this.delay(1200);

        const mockResults = this.generateMockResults(query);
        this.state.results = mockResults;
        this.state.totalSearches++;
        this.state.totalPapers += mockResults.length;
        this.state.apiQuota.gemini -= 1;

        this.saveState();
        this.renderResults(results, mockResults);
        
        if (btn) { btn.disabled = false; btn.innerHTML = '🔍 Search'; }
        this.updateStats();
        this.updateQuota();
        this.addLog('SUCCESS', `Found ${mockResults.length} papers`);
        this.showToast(`Found ${mockResults.length} papers!`, 'success');
    },

    generateMockResults(query) {
        const years = [2024, 2024, 2023, 2024, 2023];
        const tagSets = [['ai', 'ml'], ['health'], ['ai'], ['health', 'ml'], ['ai', 'ml']];
        return years.map((year, i) => ({
            title: `${['Novel approaches to', 'Clinical review of', 'Advances in', 'Comprehensive study of', 'Machine learning for'][i]} ${query}`,
            authors: `${['Smith J', 'Johnson A', 'Williams B', 'Brown C', 'Davis D'][i]}, et al.`,
            year,
            pmid: '39' + Math.floor(Math.random() * 1000000),
            tags: tagSets[i]
        }));
    },

    renderResults(container, results) {
        if (!container) return;
        container.innerHTML = results.map(r => `
            <div class="result-item" onclick="JARVIS.openPaper('${r.pmid}')">
                <div class="result-title">📄 ${r.title} <span style="margin-left:auto;cursor:pointer" onclick="event.stopPropagation();JARVIS.toggleFavorite('${r.pmid}')">⭐</span></div>
                <div class="result-meta">${r.authors} • ${r.year} • PMID: ${r.pmid}</div>
                <div class="result-tags">${r.tags.map(t => `<span class="tag ${t}">${t.toUpperCase()}</span>`).join('')}</div>
            </div>
        `).join('');
    },

    openPaper(pmid) { window.open(`https://pubmed.ncbi.nlm.nih.gov/${pmid}`, '_blank'); },

    toggleFavorite(pmid) { this.showToast('Added to favorites', 'success'); },

    saveState() {
        localStorage.setItem('jarvis_searches', this.state.totalSearches);
        localStorage.setItem('jarvis_papers', this.state.totalPapers);
    },

    updateQuota() {
        const pct = (this.state.apiQuota.gemini / 1500) * 100;
        const fill = document.getElementById('gemini-quota');
        const text = document.getElementById('gemini-remaining');
        if (fill) fill.style.width = pct + '%';
        if (text) text.textContent = `${this.state.apiQuota.gemini}/1500`;
    },

    // Toast Notifications
    showToast(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${{success:'✅',error:'❌',info:'ℹ️',warn:'⚠️'}[type]||'ℹ️'}</span><span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    },

    // Logs
    addLog(level, message) {
        const container = document.getElementById('log-container');
        if (!container) return;
        const time = new Date().toLocaleTimeString('ja-JP', { hour12: false });
        container.innerHTML += `<div class="log-entry"><span class="log-time">${time}</span><span class="log-level ${level.toLowerCase()}">[${level}]</span><span>${message}</span></div>`;
        container.scrollTop = container.scrollHeight;
    },

    clearLogs() {
        const container = document.getElementById('log-container');
        if (container) container.innerHTML = '';
        this.addLog('INFO', 'Logs cleared');
    },

    startLogSimulation() {
        const messages = ['Health check passed', 'Synced with GitHub', 'Cache refreshed', 'Metrics updated'];
        setInterval(() => {
            if (Math.random() > 0.7) this.addLog('INFO', messages[Math.floor(Math.random() * messages.length)]);
        }, 8000);
    },

    // Chat
    async sendChat() {
        const input = document.getElementById('chat-input');
        const messages = document.getElementById('chat-messages');
        const text = input?.value.trim();
        if (!text) return;

        messages.innerHTML += `<div class="chat-message user">${text}</div>`;
        input.value = '';
        messages.scrollTop = messages.scrollHeight;

        await this.delay(800);
        
        const responses = [
            `I found relevant papers about "${text}". Would you like a summary?`,
            `Based on "${text}", here are key findings from recent research...`,
            `Great topic! Let me search for the latest publications on "${text}".`
        ];
        messages.innerHTML += `<div class="chat-message assistant">${responses[Math.floor(Math.random() * responses.length)]}</div>`;
        messages.scrollTop = messages.scrollHeight;
    },

    askQuestion(q) {
        const input = document.getElementById('chat-input');
        if (input) input.value = q;
        this.showTab('chat');
        this.sendChat();
    },

    // Charts
    initCharts() {
        const ctx = document.getElementById('activity-chart')?.getContext?.('2d');
        if (!ctx || typeof Chart === 'undefined') return;
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Searches',
                    data: [12, 19, 8, 25, 15, 30, 22],
                    borderColor: '#a78bfa',
                    backgroundColor: 'rgba(167,139,250,0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#a0a0c0' } },
                    x: { grid: { display: false }, ticks: { color: '#a0a0c0' } }
                }
            }
        });
    },

    // Actions
    generateReport() {
        if (this.state.results.length === 0) return this.showToast('Run a search first', 'error');
        this.showToast('Generating report...', 'info');
        setTimeout(() => this.showToast('Report downloaded!', 'success'), 1500);
    },

    summarizeResults() {
        if (this.state.results.length === 0) return this.showToast('Run a search first', 'error');
        this.showToast('AI summarizing...', 'info');
    },

    exportData() {
        const data = { stats: { searches: this.state.totalSearches, papers: this.state.totalPapers }, results: this.state.results };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'jarvis_export.json'; a.click();
        this.showToast('Data exported!', 'success');
    },

    runPipeline() {
        this.showToast('Starting pipeline via GitHub Actions...', 'info');
        window.open('https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/run-pipeline.yml', '_blank');
    },

    // Keyboard
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', e => {
            if (e.ctrlKey && e.key === 'k') { e.preventDefault(); document.getElementById('search-query')?.focus(); }
            if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); this.runSearch(); }
            if (e.key === 'Escape') this.hideModal('shortcuts-modal');
            if (!e.ctrlKey && !e.altKey && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
                if (e.key === '1') this.showTab('dashboard');
                if (e.key === '2') this.showTab('research');
                if (e.key === '3') this.showTab('chat');
                if (e.key === '4') this.showTab('settings');
                if (e.key.toLowerCase() === 't') this.toggleTheme();
                if (e.key === '?') this.showModal('shortcuts-modal');
            }
        });
    },

    showModal(id) { document.getElementById(id)?.classList.add('show'); },
    hideModal(id) { document.getElementById(id)?.classList.remove('show'); },
    showShortcuts() { this.showModal('shortcuts-modal'); },

    // Utility
    delay(ms) { return new Promise(r => setTimeout(r, ms)); }
};

// Init on load
document.addEventListener('DOMContentLoaded', () => JARVIS.init());

// Global functions for onclick
const showTab = t => JARVIS.showTab(t);
const toggleTheme = () => JARVIS.toggleTheme();
const runSearch = () => JARVIS.runSearch();
const sendChat = () => JARVIS.sendChat();
const setQuery = q => JARVIS.setQuery(q);
const showShortcuts = () => JARVIS.showShortcuts();
const hideShortcuts = () => JARVIS.hideModal('shortcuts-modal');
const generateReport = () => JARVIS.generateReport();
const summarizeResults = () => JARVIS.summarizeResults();
const exportData = () => JARVIS.exportData();
const runPipeline = () => JARVIS.runPipeline();
const clearLogs = () => JARVIS.clearLogs();
const askQuestion = q => JARVIS.askQuestion(q);
