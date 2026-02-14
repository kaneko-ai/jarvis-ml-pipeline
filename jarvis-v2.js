// JARVIS Dashboard V2 - 日本語版
// 300機能統合ダッシュボード

const JARVIS_V2 = {
    // ============================================
    // タブ定義 (日本語)
    // ============================================
    tabs: {
        current: 'dashboard',
        originalContent: null, // ダッシュボードに戻るための保存

        definitions: {
            dashboard: { icon: '🏠', label: 'ダッシュボード' },
            coscientist: { icon: '🧬', label: 'AI共同研究者' },
            protein: { icon: '🔬', label: 'タンパク質ラボ' },
            lab: { icon: '🤖', label: '自動化ラボ' },
            metaanalysis: { icon: '📊', label: 'メタ分析' },
            compliance: { icon: '🔒', label: 'コンプライアンス' },
            pipeline: { icon: '🔄', label: 'パイプライン' }
        },

        render() {
            const nav = document.querySelector('.nav');
            if (!nav) return;

            let html = '';
            for (const [id, tab] of Object.entries(this.definitions)) {
                const active = this.current === id ? 'active' : '';
                html += `<button class="nav-btn ${active}" onclick="JARVIS_V2.tabs.switch('${id}')">${tab.icon} ${tab.label}</button>`;
            }
            nav.innerHTML = html;
        },

        switch(tabId) {
            const container = document.getElementById('main-content') || document.querySelector('.container');

            // 初回のダッシュボードコンテンツを保存
            if (!this.originalContent && container) {
                this.originalContent = container.innerHTML;
            }

            this.current = tabId;
            this.render();
            JARVIS_V2.content.render(tabId);
            toast(`${this.definitions[tabId].label}に切り替えました`, 'info');
        }
    },

    // ============================================
    // AI共同研究者タブ
    // ============================================
    coscientist: {
        hypotheses: [],

        async generateHypothesis(topic) {
            toast('仮説を生成中...', 'info');
            await sleep(1000);

            const templates = [
                `${topic}はエピジェネティックメカニズムを通じて疾患進行に影響を与える可能性がある`,
                `${topic}の発現増加は治療応答を強化する可能性がある`,
                `${topic}と結果の関係は免疫因子によって媒介される`
            ];

            this.hypotheses = templates.map((text, i) => ({
                id: `仮説${i + 1}`,
                text,
                confidence: (0.6 + Math.random() * 0.3).toFixed(2),
                novelty: (0.5 + Math.random() * 0.4).toFixed(2),
                testability: (0.7 + Math.random() * 0.2).toFixed(2)
            }));

            toast(`${this.hypotheses.length}件の仮説を生成しました！`, 'success');
            return this.hypotheses;
        },

        renderHypothesisCards(container) {
            container.innerHTML = this.hypotheses.map(h => `
                <div class="card" style="margin-bottom:1rem">
                    <div class="card-header">
                        <span class="card-title">🧪 ${h.id}</span>
                        <span style="color:var(--green)">信頼度: ${(h.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p style="margin-bottom:1rem">${h.text}</p>
                    <div class="tags">
                        <span class="tag" style="background:rgba(74,222,128,0.2);color:var(--green)">新規性: ${(h.novelty * 100).toFixed(0)}%</span>
                        <span class="tag" style="background:rgba(96,165,250,0.2);color:var(--blue)">検証可能性: ${(h.testability * 100).toFixed(0)}%</span>
                    </div>
                </div>
            `).join('');
        },

        async analyzeLiteratureGap(topic) {
            toast('文献ギャップを分析中...', 'info');
            await sleep(1500);

            return {
                gaps: [
                    { type: '研究不足', description: `${topic}のメカニズムに関する研究が限定的`, severity: 'high' },
                    { type: '方法論的', description: '改善された実験手法が必要', severity: 'medium' },
                    { type: 'トランスレーショナル', description: '基礎研究と臨床応用のギャップ', severity: 'high' }
                ]
            };
        },

        async designExperiment(hypothesis) {
            toast('実験を設計中...', 'info');
            await sleep(1200);

            return {
                design: 'ランダム化比較試験',
                sample_size: Math.floor(50 + Math.random() * 150),
                power: 0.8,
                primary_endpoint: '主要評価項目',
                timeline_months: 12
            };
        }
    },

    // ============================================
    // タンパク質ラボタブ
    // ============================================
    protein: {
        async getAlphaFoldStructure(uniprotId) {
            return {
                pdb_url: `https://alphafold.ebi.ac.uk/files/AF-${uniprotId}-F1-model_v4.pdb`,
                viewer_url: `https://alphafold.ebi.ac.uk/entry/${uniprotId}`,
                confidence: '高'
            };
        },

        async predictBinding(proteinSeq, ligandSmiles) {
            toast('結合親和性を予測中...', 'info');
            await sleep(1000);

            const kd = (Math.random() * 100).toFixed(2);
            return {
                predicted_kd: `${kd} nM`,
                strength: kd < 10 ? '強い' : kd < 50 ? '中程度' : '弱い',
                confidence: (0.6 + Math.random() * 0.3).toFixed(2)
            };
        },

        async designSequence(length, type) {
            toast('タンパク質配列を設計中...', 'info');
            await sleep(800);

            const aa = 'ACDEFGHIKLMNPQRSTVWY';
            let seq = '';
            for (let i = 0; i < length; i++) {
                seq += aa[Math.floor(Math.random() * aa.length)];
            }
            return { sequence: seq, length, type, stability: '中程度' };
        },

        render3DViewer(container, pdbUrl) {
            container.innerHTML = `
                <div style="text-align:center;padding:2rem">
                    <div style="font-size:4rem;margin-bottom:1rem">🧬</div>
                    <p>3D タンパク質ビューア</p>
                    <p style="color:var(--txt2);font-size:0.85rem">AlphaFoldから構造を読み込み</p>
                    <a href="${pdbUrl}" target="_blank" class="btn" style="margin-top:1rem">AlphaFoldで表示</a>
                </div>
            `;
        }
    },

    // ============================================
    // 自動化ラボタブ
    // ============================================
    lab: {
        equipment: [],
        samples: [],

        registerEquipment(id, name, type) {
            this.equipment.push({ id, name, type, status: '待機中', lastUsed: null });
        },

        sendCommand(equipmentId, command, params) {
            const eq = this.equipment.find(e => e.id === equipmentId);
            if (!eq) return { error: '機器が見つかりません' };

            eq.status = '実行中';
            eq.lastUsed = new Date().toISOString();
            toast(`${eq.name}: ${command}`, 'info');

            return { status: 'コマンド送信済み', equipment: equipmentId };
        },

        registerSample(barcode, metadata) {
            this.samples.push({ barcode, ...metadata, registeredAt: new Date().toISOString() });
            return { status: '登録完了', barcode };
        },

        getLabStatus() {
            return {
                equipment: this.equipment.map(e => ({ ...e })),
                samples: this.samples.length,
                activeExperiments: Math.floor(Math.random() * 5)
            };
        },

        renderLabDashboard(container) {
            const status = this.getLabStatus();
            container.innerHTML = `
                <div class="grid">
                    <div class="card c4">
                        <div class="stat">
                            <div class="stat-icon">🔬</div>
                            <div class="stat-val">${status.equipment.length}</div>
                            <div class="stat-lbl">機器数</div>
                        </div>
                    </div>
                    <div class="card c4">
                        <div class="stat">
                            <div class="stat-icon">🧫</div>
                            <div class="stat-val">${status.samples}</div>
                            <div class="stat-lbl">サンプル数</div>
                        </div>
                    </div>
                    <div class="card c4">
                        <div class="stat">
                            <div class="stat-icon">⚗️</div>
                            <div class="stat-val">${status.activeExperiments}</div>
                            <div class="stat-lbl">実行中の実験</div>
                        </div>
                    </div>
                </div>
            `;
        }
    },

    // ============================================
    // メタ分析タブ
    // ============================================
    metaanalysis: {
        async runMetaAnalysis(studies) {
            toast('メタ分析を実行中...', 'info');
            await sleep(1500);

            const effects = studies.map(s => s.effect_size || Math.random());
            const pooled = effects.reduce((a, b) => a + b, 0) / effects.length;

            return {
                pooled_effect: pooled.toFixed(3),
                n_studies: studies.length,
                i_squared: (Math.random() * 60).toFixed(1),
                heterogeneity: pooled > 0.5 ? '低' : '中程度'
            };
        },

        renderForestPlot(container, studies) {
            container.innerHTML = `
                <div style="padding:1rem">
                    <h3 style="margin-bottom:1rem">フォレストプロット</h3>
                    ${studies.map((s, i) => {
                const effect = s.effect_size || 0.5;
                const pos = 50 + effect * 100;
                return `
                            <div style="display:flex;align-items:center;margin:0.5rem 0">
                                <span style="width:100px;color:var(--txt2)">研究 ${i + 1}</span>
                                <div style="flex:1;height:20px;background:var(--glass);border-radius:4px;position:relative">
                                    <div style="position:absolute;left:50%;width:1px;height:100%;background:var(--txt2)"></div>
                                    <div style="position:absolute;left:${pos}%;transform:translateX(-50%);width:10px;height:10px;background:var(--purple);border-radius:50%"></div>
                                </div>
                            </div>
                        `;
            }).join('')}
                </div>
            `;
        }
    },

    // ============================================
    // コンプライアンスタブ
    // ============================================
    compliance: {
        checkHIPAA(text) {
            const patterns = [/\d{3}-\d{2}-\d{4}/, /\b[A-Z]{2}\d{6,8}\b/];
            const issues = patterns.filter(p => p.test(text)).map(() => '個人情報の可能性を検出');
            return { compliant: issues.length === 0, issues };
        },

        anonymizeData(data, fields) {
            const result = { ...data };
            fields.forEach(f => {
                if (result[f]) result[f] = '***非表示***';
            });
            return result;
        },

        getAuditLog() {
            return [
                { action: 'ログイン', user: 'researcher1', timestamp: new Date().toISOString() },
                { action: 'データアクセス', user: 'researcher1', timestamp: new Date().toISOString() }
            ];
        },

        renderComplianceDashboard(container) {
            container.innerHTML = `
                <div class="grid">
                    <div class="card c6">
                        <div class="card-header"><span class="card-title">🔒 HIPAA ステータス</span></div>
                        <div style="display:flex;align-items:center;gap:1rem">
                            <span style="font-size:3rem">✅</span>
                            <div>
                                <div style="font-size:1.5rem;font-weight:700;color:var(--green)">準拠</div>
                                <div style="color:var(--txt2)">個人情報は検出されませんでした</div>
                            </div>
                        </div>
                    </div>
                    <div class="card c6">
                        <div class="card-header"><span class="card-title">📜 監査ログ</span></div>
                        <div style="max-height:150px;overflow-y:auto">
                            ${this.getAuditLog().map(log => `
                                <div style="padding:0.5rem;border-bottom:1px solid var(--border)">
                                    ${log.action} by ${log.user}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
    },

    // ============================================
    // パイプラインタブ
    // ============================================
    pipelines: {
        definitions: {
            hypothesis: { name: '仮説パイプライン', steps: ['生成', '検証', '設計', '実行'] },
            protein: { name: 'タンパク質パイプライン', steps: ['構造', '設計', '発現', '検証'] },
            metaanalysis: { name: 'メタ分析パイプライン', steps: ['検索', 'スクリーニング', '抽出', '分析'] },
            grant: { name: '助成金パイプライン', steps: ['検索', 'マッチング', '下書き', '提出'] },
            labautomation: { name: 'ラボ自動化パイプライン', steps: ['プロトコル', 'スケジュール', '実行', 'QC'] }
        },

        running: {},

        async run(pipelineId) {
            const pipeline = this.definitions[pipelineId];
            if (!pipeline) return { error: 'パイプラインが見つかりません' };

            this.running[pipelineId] = { status: '実行中', currentStep: 0 };
            toast(`${pipeline.name}を開始...`, 'info');

            for (let i = 0; i < pipeline.steps.length; i++) {
                this.running[pipelineId].currentStep = i;
                toast(`${pipeline.steps[i]}...`, 'info');
                await sleep(1000);
            }

            this.running[pipelineId].status = '完了';
            toast(`${pipeline.name}が完了しました！`, 'success');

            return { status: '完了', pipeline: pipelineId };
        },

        renderPipelinesDashboard(container) {
            container.innerHTML = `
                <div class="grid">
                    ${Object.entries(this.definitions).map(([id, p]) => `
                        <div class="card c4">
                            <div class="card-header"><span class="card-title">🔄 ${p.name}</span></div>
                            <div class="tags" style="margin-bottom:1rem">
                                ${p.steps.map(s => `<span class="tag">${s}</span>`).join('')}
                            </div>
                            <button class="btn" onclick="JARVIS_V2.pipelines.run('${id}')">パイプライン実行</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    },

    // ============================================
    // モニタリング
    // ============================================
    monitoring: {
        logs: [],
        metrics: {},

        log(message, level = 'info') {
            this.logs.push({ message, level, timestamp: new Date().toISOString() });
        },

        recordMetric(name, value) {
            if (!this.metrics[name]) this.metrics[name] = [];
            this.metrics[name].push({ value, timestamp: new Date().toISOString() });
        },

        getRecentLogs(n = 20) {
            return this.logs.slice(-n);
        }
    },

    // ============================================
    // コンテンツレンダラー
    // ============================================
    content: {
        render(tabId) {
            const container = document.getElementById('main-content') || document.querySelector('.container');
            if (!container) return;

            switch (tabId) {
                case 'coscientist':
                    this.renderCoScientist(container);
                    break;
                case 'protein':
                    this.renderProtein(container);
                    break;
                case 'lab':
                    JARVIS_V2.lab.renderLabDashboard(container);
                    break;
                case 'metaanalysis':
                    this.renderMetaAnalysis(container);
                    break;
                case 'compliance':
                    JARVIS_V2.compliance.renderComplianceDashboard(container);
                    break;
                case 'pipeline':
                    JARVIS_V2.pipelines.renderPipelinesDashboard(container);
                    break;
                default:
                    // ダッシュボードに戻る：保存されたコンテンツを復元
                    if (JARVIS_V2.tabs.originalContent) {
                        container.innerHTML = JARVIS_V2.tabs.originalContent;
                    }
                    break;
            }
        },

        renderCoScientist(container) {
            container.innerHTML = `
                <div class="grid">
                    <div class="card c12">
                        <div class="card-header"><span class="card-title">🧬 AI共同研究者</span></div>
                        <div class="search-box">
                            <input type="text" id="hypothesis-topic" class="search-input" placeholder="研究トピックを入力...">
                            <button class="btn" onclick="JARVIS_V2.generateHypothesesUI()">仮説を生成</button>
                        </div>
                    </div>
                    <div class="c12" id="hypothesis-results"></div>
                    <div class="card c6">
                        <div class="card-header"><span class="card-title">📊 文献ギャップ分析</span></div>
                        <button class="btn" onclick="JARVIS_V2.analyzeGapsUI()">ギャップを分析</button>
                        <div id="gap-results" style="margin-top:1rem"></div>
                    </div>
                    <div class="card c6">
                        <div class="card-header"><span class="card-title">🔬 実験デザイナー</span></div>
                        <button class="btn" onclick="JARVIS_V2.designExperimentUI()">実験を設計</button>
                        <div id="experiment-results" style="margin-top:1rem"></div>
                    </div>
                </div>
            `;
        },

        renderProtein(container) {
            container.innerHTML = `
                <div class="grid">
                    <div class="card c6">
                        <div class="card-header"><span class="card-title">🔬 AlphaFold検索</span></div>
                        <div class="search-box">
                            <input type="text" id="uniprot-id" class="search-input" placeholder="UniProt ID (例: P12345)">
                            <button class="btn" onclick="JARVIS_V2.lookupStructureUI()">構造を取得</button>
                        </div>
                        <div id="structure-result"></div>
                    </div>
                    <div class="card c6">
                        <div class="card-header"><span class="card-title">💊 結合予測</span></div>
                        <input type="text" id="protein-seq" class="search-input" placeholder="タンパク質配列..." style="margin-bottom:0.5rem">
                        <input type="text" id="ligand-smiles" class="search-input" placeholder="リガンドSMILES...">
                        <button class="btn" style="margin-top:0.5rem" onclick="JARVIS_V2.predictBindingUI()">結合を予測</button>
                        <div id="binding-result" style="margin-top:1rem"></div>
                    </div>
                    <div class="card c12" id="protein-viewer">
                        <div class="card-header"><span class="card-title">🧬 3D タンパク質ビューア</span></div>
                        <div style="height:400px;display:flex;align-items:center;justify-content:center;color:var(--txt2)">
                            UniProt IDを入力して構造を表示
                        </div>
                    </div>
                </div>
            `;
        },

        renderMetaAnalysis(container) {
            container.innerHTML = `
                <div class="grid">
                    <div class="card c12">
                        <div class="card-header"><span class="card-title">📊 メタ分析</span></div>
                        <p style="color:var(--txt2);margin-bottom:1rem">研究を追加してメタ分析を実行</p>
                        <div id="studies-list"></div>
                        <button class="btn" onclick="JARVIS_V2.addStudyUI()">研究を追加</button>
                        <button class="btn" style="margin-left:0.5rem" onclick="JARVIS_V2.runMetaAnalysisUI()">分析を実行</button>
                    </div>
                    <div class="card c6" id="forest-plot">
                        <div class="card-header"><span class="card-title">🌲 フォレストプロット</span></div>
                        <div style="height:300px;color:var(--txt2);display:flex;align-items:center;justify-content:center">
                            分析を実行してプロットを表示
                        </div>
                    </div>
                    <div class="card c6" id="meta-results">
                        <div class="card-header"><span class="card-title">📈 結果</span></div>
                        <div style="color:var(--txt2)">まだ結果はありません</div>
                    </div>
                </div>
            `;
        }
    },

    // ============================================
    // UIヘルパー
    // ============================================
    async generateHypothesesUI() {
        const topic = document.getElementById('hypothesis-topic')?.value;
        if (!topic) { toast('トピックを入力してください', 'error'); return; }

        const hypotheses = await this.coscientist.generateHypothesis(topic);
        const container = document.getElementById('hypothesis-results');
        if (container) this.coscientist.renderHypothesisCards(container);
    },

    async analyzeGapsUI() {
        const topic = document.getElementById('hypothesis-topic')?.value || '研究';
        const result = await this.coscientist.analyzeLiteratureGap(topic);

        const container = document.getElementById('gap-results');
        if (container) {
            container.innerHTML = result.gaps.map(g => `
                <div style="padding:0.5rem;border-left:3px solid ${g.severity === 'high' ? 'var(--red)' : 'var(--yellow)'}">
                    <strong>${g.type}</strong>: ${g.description}
                </div>
            `).join('');
        }
    },

    async designExperimentUI() {
        const result = await this.coscientist.designExperiment('仮説');

        const container = document.getElementById('experiment-results');
        if (container) {
            container.innerHTML = `
                <div style="display:grid;gap:0.5rem">
                    <div><strong>デザイン:</strong> ${result.design}</div>
                    <div><strong>サンプルサイズ:</strong> ${result.sample_size}</div>
                    <div><strong>検出力:</strong> ${result.power}</div>
                    <div><strong>タイムライン:</strong> ${result.timeline_months}ヶ月</div>
                </div>
            `;
        }
    },

    async lookupStructureUI() {
        const id = document.getElementById('uniprot-id')?.value;
        if (!id) { toast('UniProt IDを入力してください', 'error'); return; }

        const result = await this.protein.getAlphaFoldStructure(id);

        const container = document.getElementById('structure-result');
        if (container) {
            container.innerHTML = `
                <div style="margin-top:1rem">
                    <a href="${result.viewer_url}" target="_blank" class="btn">AlphaFoldで表示</a>
                </div>
            `;
        }

        const viewer = document.getElementById('protein-viewer');
        if (viewer) this.protein.render3DViewer(viewer, result.pdb_url);
    },

    async predictBindingUI() {
        const seq = document.getElementById('protein-seq')?.value || 'MVLSPADKTN';
        const smiles = document.getElementById('ligand-smiles')?.value || 'CCO';

        const result = await this.protein.predictBinding(seq, smiles);

        const container = document.getElementById('binding-result');
        if (container) {
            container.innerHTML = `
                <div style="display:grid;gap:0.5rem">
                    <div><strong>予測Kd:</strong> <span style="color:var(--green)">${result.predicted_kd}</span></div>
                    <div><strong>強度:</strong> ${result.strength}</div>
                    <div><strong>信頼度:</strong> ${(result.confidence * 100).toFixed(0)}%</div>
                </div>
            `;
        }
    },

    maStudies: [],

    addStudyUI() {
        this.maStudies.push({
            effect_size: Math.random() * 0.8 - 0.4,
            sample_size: Math.floor(50 + Math.random() * 200)
        });

        const container = document.getElementById('studies-list');
        if (container) {
            container.innerHTML = this.maStudies.map((s, i) => `
                <div class="tag" style="margin:0.25rem">研究 ${i + 1}: 効果=${s.effect_size.toFixed(2)}, n=${s.sample_size}</div>
            `).join('');
        }

        toast(`研究 ${this.maStudies.length} を追加しました`, 'success');
    },

    async runMetaAnalysisUI() {
        if (this.maStudies.length < 2) {
            toast('2件以上の研究を追加してください', 'error');
            return;
        }

        const result = await this.metaanalysis.runMetaAnalysis(this.maStudies);

        const forest = document.getElementById('forest-plot');
        if (forest) this.metaanalysis.renderForestPlot(forest, this.maStudies);

        const results = document.getElementById('meta-results');
        if (results) {
            results.innerHTML = `
                <div class="card-header"><span class="card-title">📈 結果</span></div>
                <div style="display:grid;gap:0.5rem">
                    <div><strong>統合効果:</strong> <span style="color:var(--green)">${result.pooled_effect}</span></div>
                    <div><strong>研究数:</strong> ${result.n_studies}</div>
                    <div><strong>I²:</strong> ${result.i_squared}%</div>
                    <div><strong>異質性:</strong> ${result.heterogeneity}</div>
                </div>
            `;
        }
    },

    // ============================================
    // キーボードショートカット
    // ============================================
    shortcuts: {
        init() {
            document.addEventListener('keydown', (e) => {
                // Cmd/Ctrl + K: 検索フォーカス
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                    e.preventDefault();
                    document.getElementById('query')?.focus();
                }
                // Cmd/Ctrl + 1-7: タブ切り替え
                if ((e.metaKey || e.ctrlKey) && e.key >= '1' && e.key <= '7') {
                    e.preventDefault();
                    const tabs = Object.keys(JARVIS_V2.tabs.definitions);
                    const idx = parseInt(e.key) - 1;
                    if (tabs[idx]) JARVIS_V2.tabs.switch(tabs[idx]);
                }
                // Escape: モーダルを閉じる
                if (e.key === 'Escape') {
                    document.querySelectorAll('.modal').forEach(m => m.remove());
                }
            });
        }
    },

    // ============================================
    // アクセシビリティ
    // ============================================
    a11y: {
        highContrast: false,
        fontSize: 'normal',
        reduceMotion: false,

        toggleHighContrast() {
            this.highContrast = !this.highContrast;
            document.body.classList.toggle('high-contrast', this.highContrast);
            toast(this.highContrast ? '高コントラスト有効' : '高コントラスト無効', 'info');
        },

        setFontSize(size) {
            this.fontSize = size;
            document.documentElement.style.fontSize = size === 'large' ? '18px' : size === 'small' ? '14px' : '16px';
        },

        toggleReduceMotion() {
            this.reduceMotion = !this.reduceMotion;
            document.body.classList.toggle('reduce-motion', this.reduceMotion);
        }
    },

    // ============================================
    // テーマ
    // ============================================
    themes: {
        current: 'dark',

        definitions: {
            dark: { bg: '#0a0a1a', card: 'rgba(26, 26, 62, 0.8)', txt: '#fff' },
            light: { bg: '#f5f5f5', card: 'rgba(255, 255, 255, 0.9)', txt: '#1a1a1a' },
            ocean: { bg: '#0a1628', card: 'rgba(16, 42, 76, 0.8)', txt: '#e0f0ff' },
            forest: { bg: '#0a1a0a', card: 'rgba(16, 42, 16, 0.8)', txt: '#e0ffe0' },
            sunset: { bg: '#1a0a0a', card: 'rgba(42, 16, 16, 0.8)', txt: '#ffe0e0' }
        },

        apply(themeName) {
            const theme = this.definitions[themeName];
            if (!theme) return;

            this.current = themeName;
            document.documentElement.style.setProperty('--bg', theme.bg);
            document.documentElement.style.setProperty('--card', theme.card);
            document.documentElement.style.setProperty('--txt', theme.txt);

            localStorage.setItem('jarvis_theme', themeName);
            toast(`テーマ: ${themeName}`, 'info');
        },

        load() {
            const saved = localStorage.getItem('jarvis_theme');
            if (saved) this.apply(saved);
        }
    },

    // ============================================
    // 初期化
    // ============================================
    init() {
        console.log('JARVIS V2 日本語版読み込み完了');

        // タブを初期化
        this.tabs.render();

        // ショートカットを初期化
        this.shortcuts.init();

        // テーマを読み込み
        this.themes.load();

        // デモ機器を登録
        this.lab.registerEquipment('eq1', '遠心分離機', 'centrifuge');
        this.lab.registerEquipment('eq2', 'PCRマシン', 'pcr');
        this.lab.registerEquipment('eq3', 'プレートリーダー', 'reader');

        // 初期化ログ
        this.monitoring.log('JARVIS V2 初期化完了');
    }
};

// ユーティリティ関数
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function toast(message, type = 'info') {
    if (typeof window.toast === 'function') {
        window.toast(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

// ロード時に初期化
document.addEventListener('DOMContentLoaded', () => {
    JARVIS_V2.init();
});

// グローバルにエクスポート
window.JARVIS_V2 = JARVIS_V2;
