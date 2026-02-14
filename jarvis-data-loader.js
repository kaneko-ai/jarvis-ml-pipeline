/**
 * JARVIS Real Data Loader
 * 
 * export_bundle.json / docs_store.json から実データを読み込み
 * デモ乱数データを置き換える
 */

const JARVISDataLoader = {
    // 現在のrun_id
    currentRunId: null,

    // 読み込み済みデータ
    bundleData: null,
    docsStore: null,

    // ベースパス
    basePath: '../artifacts',

    /**
     * 利用可能なrun_idを取得
     */
    async listRuns() {
        try {
            const response = await fetch(`${this.basePath}/runs.json`);
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.warn('runs.json not found, listing may not work');
        }
        return [];
    },

    /**
     * 特定run_idのexport_bundle.jsonを読み込み
     */
    async loadBundle(runId) {
        const bundlePath = `${this.basePath}/${runId}/export_bundle.json`;

        try {
            const response = await fetch(bundlePath);
            if (!response.ok) {
                throw new Error(`Bundle not found: ${bundlePath}`);
            }

            this.bundleData = await response.json();
            this.currentRunId = runId;

            console.log(`Loaded bundle for run: ${runId}`);
            return this.bundleData;

        } catch (e) {
            console.error('Failed to load bundle:', e);
            return null;
        }
    },

    /**
     * docs_store.jsonを読み込み
     */
    async loadDocsStore(runId) {
        runId = runId || this.currentRunId;
        const docsPath = `${this.basePath}/${runId}/docs_store.json`;

        try {
            const response = await fetch(docsPath);
            if (response.ok) {
                this.docsStore = await response.json();
                return this.docsStore;
            }
        } catch (e) {
            console.warn('docs_store.json not found');
        }
        return null;
    },

    /**
     * バンドルからサマリー情報を取得
     */
    getSummary() {
        if (!this.bundleData) return null;

        const meta = this.bundleData.run_meta || {};
        const report = this.bundleData.quality_report || {};

        return {
            runId: meta.run_id || 'unknown',
            goal: meta.goal || '',
            domain: meta.domain || '',
            timestamp: meta.timestamp || '',
            papersCount: meta.papers_count || 0,
            claimsCount: meta.claims_count || 0,
            provenanceRate: meta.provenance_rate || 0,
            qualityPassed: report.passed || false
        };
    },

    /**
     * Claimsを取得
     */
    getClaims() {
        if (!this.bundleData) return [];
        return this.bundleData.claims || [];
    },

    /**
     * Evidence Linksを取得
     */
    getEvidenceLinks() {
        if (!this.bundleData) return [];
        return this.bundleData.evidence_links || [];
    },

    /**
     * 論文リストを取得
     */
    getPapers() {
        if (!this.bundleData) return [];
        return this.bundleData.papers || [];
    },

    /**
     * スコアを取得
     */
    getScores() {
        if (!this.bundleData) return {};
        return this.bundleData.scores || {};
    },

    /**
     * Quality Reportを取得
     */
    getQualityReport() {
        if (!this.bundleData) return null;
        return this.bundleData.quality_report || null;
    },

    /**
     * 特定のevidence linkのテキストを取得
     */
    getEvidenceText(evidenceLink) {
        if (!this.docsStore) return evidenceLink.text || '';

        const doc = this.docsStore[evidenceLink.doc_id];
        if (!doc) return evidenceLink.text || '';

        // セクションまたはチャンクから取得
        if (evidenceLink.section && doc.sections && doc.sections[evidenceLink.section]) {
            const text = doc.sections[evidenceLink.section];
            if (evidenceLink.start !== undefined && evidenceLink.end !== undefined) {
                return text.slice(evidenceLink.start, evidenceLink.end);
            }
            return text;
        }

        if (evidenceLink.chunk_id && doc.chunks && doc.chunks[evidenceLink.chunk_id]) {
            return doc.chunks[evidenceLink.chunk_id];
        }

        return evidenceLink.text || '';
    },

    /**
     * ダッシュボードを実データで更新
     */
    updateDashboard() {
        if (!this.bundleData) {
            console.warn('No bundle loaded');
            return;
        }

        const summary = this.getSummary();

        // Stats更新
        this._updateStatElement('papers-count', summary.papersCount);
        this._updateStatElement('claims-count', summary.claimsCount);
        this._updateStatElement('provenance-rate', `${(summary.provenanceRate * 100).toFixed(1)}%`);
        this._updateStatElement('run-id', summary.runId);

        // Quality badge
        const qualityBadge = document.querySelector('.quality-badge');
        if (qualityBadge) {
            qualityBadge.textContent = summary.qualityPassed ? '✅ PASSED' : '❌ FAILED';
            qualityBadge.style.color = summary.qualityPassed ? 'var(--green)' : 'var(--red)';
        }

        // Claims table更新
        this._updateClaimsTable();

        // Papers list更新
        this._updatePapersList();

        console.log('Dashboard updated with real data');
    },

    _updateStatElement(id, value) {
        const el = document.getElementById(id) || document.querySelector(`[data-stat="${id}"]`);
        if (el) el.textContent = value;
    },

    _updateClaimsTable() {
        const container = document.getElementById('claims-list') || document.querySelector('.claims-container');
        if (!container) return;

        const claims = this.getClaims().slice(0, 20); // 最初の20件

        container.innerHTML = claims.map(c => `
            <div class="claim-item" style="padding:0.5rem;border-bottom:1px solid var(--border)">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem">
                    <span class="tag" style="background:${c.claim_type === 'fact' ? 'var(--green)' : 'var(--yellow)'}20">${c.claim_type}</span>
                    <span style="color:var(--txt2);font-size:0.8rem">${c.evidence_count} evidence</span>
                </div>
                <div style="font-size:0.9rem">${c.claim_text.slice(0, 200)}${c.claim_text.length > 200 ? '...' : ''}</div>
            </div>
        `).join('');
    },

    _updatePapersList() {
        const container = document.getElementById('papers-list') || document.querySelector('.papers-container');
        if (!container) return;

        const papers = this.getPapers().slice(0, 10);

        container.innerHTML = papers.map(p => `
            <div class="paper-item" style="padding:0.5rem;border-bottom:1px solid var(--border)">
                <div style="font-weight:500">${p.title || 'Untitled'}</div>
                <div style="font-size:0.8rem;color:var(--txt2)">${p.pmid ? `PMID: ${p.pmid}` : p.doc_id}</div>
            </div>
        `).join('');
    },

    /**
     * URLパラメータからrun_idを取得して自動読み込み
     */
    async autoLoad() {
        const urlParams = new URLSearchParams(window.location.search);
        const runId = urlParams.get('run') || urlParams.get('run_id');

        if (runId) {
            await this.loadBundle(runId);
            await this.loadDocsStore(runId);
            this.updateDashboard();
        }
    }
};

// JARVIS_V2に統合
if (typeof JARVIS_V2 !== 'undefined') {
    JARVIS_V2.dataLoader = JARVISDataLoader;

    // initにフック
    const originalInit = JARVIS_V2.init;
    JARVIS_V2.init = async function () {
        originalInit.call(this);

        // 自動読み込み試行
        await JARVISDataLoader.autoLoad();
    };
}

// グローバルエクスポート
window.JARVISDataLoader = JARVISDataLoader;
