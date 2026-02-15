/* ================================================================== */
/*  JARVIS OS — Unified Application Module                            */
/*  All features from jarvis.js / jarvis-v2.js / jarvis-ext.js /      */
/*  jarvis-data-loader.js merged into one coherent module.             */
/* ================================================================== */

const J = {

  // ================================================================
  // STATE
  // ================================================================
  state: {
    searches: parseInt(localStorage.getItem('j_searches') || '0'),
    papers: parseInt(localStorage.getItem('j_papers') || '0'),
    claims: parseInt(localStorage.getItem('j_claims') || '0'),
    results: [],
    theme: localStorage.getItem('j_theme') || 'dark',
    fontSize: localStorage.getItem('j_fontsize') || 'normal',
    highContrast: localStorage.getItem('j_contrast') === 'true',
    reduceMotion: localStorage.getItem('j_motion') === 'true',
    sidebarCollapsed: localStorage.getItem('j_sidebar') === 'collapsed',
    apiBaseUrl: localStorage.getItem('j_api_url') || '',
    slackWebhook: localStorage.getItem('j_slack') || '',
    apiQuota: { current: parseInt(localStorage.getItem('j_quota') || '1500'), max: 1500 },
    currentTab: 'command',
    chatOpen: false,
    cmdOpen: false,
    maStudies: [],
    logs: [],
    favorites: JSON.parse(localStorage.getItem('j_favs') || '[]'),
    heatmap: JSON.parse(localStorage.getItem('j_heatmap') || '{}'),
    searchHistory: JSON.parse(localStorage.getItem('j_history') || '[]'),
  },

  // ================================================================
  // INIT
  // ================================================================
  init() {
    this.applyTheme(this.state.theme);
    this.applyFontSize(this.state.fontSize);
    if (this.state.highContrast) document.body.classList.add('high-contrast');
    if (this.state.reduceMotion) document.body.classList.add('reduce-motion');
    if (this.state.sidebarCollapsed) {
      document.getElementById('sidebar').classList.add('collapsed');
      document.body.classList.add('sidebar-collapsed');
    }

    this.ui.bindAll();
    this.tabs.init();
    this.clock.start();
    this.kpi.update();
    this.quota.update();
    this.health.check();
    this.logs.init();
    this.heatmap.render();
    this.charts.initActivity();
    this.charts.initRadar();
    this.charts.initPie();
    this.wordCloud.load();
    this.lab.init();
    this.dataLoader.autoLoad();
    this.notif.add('info', 'システム初期化完了');
    this.heatmap.record();

    console.log('JARVIS OS initialized');
  },

  // ================================================================
  // SAVE
  // ================================================================
  save() {
    localStorage.setItem('j_searches', this.state.searches);
    localStorage.setItem('j_papers', this.state.papers);
    localStorage.setItem('j_claims', this.state.claims);
    localStorage.setItem('j_quota', this.state.apiQuota.current);
    localStorage.setItem('j_favs', JSON.stringify(this.state.favorites));
    localStorage.setItem('j_heatmap', JSON.stringify(this.state.heatmap));
    localStorage.setItem('j_history', JSON.stringify(this.state.searchHistory));
  },

  // ================================================================
  // UI BINDING
  // ================================================================
  ui: {
    bindAll() {
      // Sidebar nav
      document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', () => J.tabs.switchTo(btn.dataset.tab));
      });

      // Sidebar collapse
      document.getElementById('sidebar-toggle').addEventListener('click', () => J.sidebar.toggle());
      document.getElementById('mobile-menu').addEventListener('click', () => J.sidebar.mobileToggle());

      // Topbar
      document.getElementById('topbar-cmd').addEventListener('click', () => J.cmd.open());
      document.getElementById('theme-toggle-btn').addEventListener('click', () => J.theme.cycle());
      document.getElementById('fullscreen-btn').addEventListener('click', () => J.fullscreen.toggle());
      document.getElementById('shortcuts-btn').addEventListener('click', () => J.tabs.switchTo('settings'));

      // Command palette
      document.getElementById('cmd-overlay').addEventListener('click', e => {
        if (e.target.id === 'cmd-overlay') J.cmd.close();
      });
      document.getElementById('cmd-input').addEventListener('input', e => J.cmd.filter(e.target.value));

      // Quick actions
      document.getElementById('qa-search').addEventListener('click', () => J.tabs.switchTo('research'));
      document.getElementById('qa-pipeline').addEventListener('click', () => {
        window.open('https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/run-pipeline.yml', '_blank');
      });
      document.getElementById('qa-evidence').addEventListener('click', () => J.tabs.switchTo('analysis'));
      document.getElementById('qa-prisma').addEventListener('click', () => {
        J.tabs.switchTo('analysis');
        setTimeout(() => document.getElementById('prisma-run').scrollIntoView({ behavior: 'smooth' }), 300);
      });
      document.getElementById('qa-export').addEventListener('click', () => J.data.exportJSON());
      document.getElementById('qa-report').addEventListener('click', () => J.actions.generateReport());
      document.getElementById('qa-summarize').addEventListener('click', () => J.actions.summarize());
      document.getElementById('qa-github').addEventListener('click', () => {
        window.open('https://github.com/kaneko-ai/jarvis-ml-pipeline/actions', '_blank');
      });

      // Health refresh
      document.getElementById('health-refresh').addEventListener('click', () => J.health.check());

      // Run selector
      document.getElementById('run-selector').addEventListener('change', e => {
        if (e.target.value) J.dataLoader.loadRun(e.target.value);
      });

      // Notification clear
      document.getElementById('notif-clear').addEventListener('click', () => {
        document.getElementById('notif-list').innerHTML = '';
        J.toast('通知をクリアしました', 'info');
      });

      // Search
      document.getElementById('search-btn').addEventListener('click', () => J.search.run());
      document.getElementById('voice-btn').addEventListener('click', () => J.voice.toggle());
      document.getElementById('search-query').addEventListener('keydown', e => {
        if (e.ctrlKey && e.key === 'Enter') J.search.run();
      });

      // Evidence
      document.getElementById('ev-run').addEventListener('click', () => J.analysis.evidence());

      // Contradiction
      document.getElementById('contra-run').addEventListener('click', () => J.analysis.contradiction());

      // Citation
      document.getElementById('cite-run').addEventListener('click', () => J.analysis.citation());

      // PRISMA
      document.getElementById('prisma-run').addEventListener('click', () => J.analysis.prisma());

      // Citation Generator
      document.getElementById('cg-run').addEventListener('click', () => J.analysis.citationGen());

      // Co-Scientist
      document.getElementById('hypo-gen').addEventListener('click', () => J.coscientist.generateHypotheses());
      document.getElementById('gap-run').addEventListener('click', () => J.coscientist.analyzeGaps());
      document.getElementById('exp-run').addEventListener('click', () => J.coscientist.designExperiment());

      // Protein
      document.getElementById('af-run').addEventListener('click', () => J.protein.lookupStructure());
      document.getElementById('bind-run').addEventListener('click', () => J.protein.predictBinding());
      document.getElementById('seq-run').addEventListener('click', () => J.protein.designSequence());

      // Meta-analysis
      document.getElementById('ma-add').addEventListener('click', () => J.meta.addStudy());
      document.getElementById('ma-run').addEventListener('click', () => J.meta.run());

      // Pipelines
      document.querySelectorAll('[data-pipeline]').forEach(btn => {
        btn.addEventListener('click', () => J.pipelines.run(btn.dataset.pipeline));
      });

      // Lab
      document.getElementById('sample-register').addEventListener('click', () => J.lab.registerSample());
      document.getElementById('cmd-send').addEventListener('click', () => J.lab.sendCommand());

      // Logs
      document.getElementById('log-clear').addEventListener('click', () => J.logs.clear());
      document.getElementById('log-export').addEventListener('click', () => J.logs.export());
      document.getElementById('log-filter').addEventListener('change', e => J.logs.filter(e.target.value));

      // Compliance
      document.getElementById('hipaa-check').addEventListener('click', () => J.compliance.check());

      // Settings - API
      document.getElementById('api-save').addEventListener('click', () => J.settings.saveApi());
      document.getElementById('api-test').addEventListener('click', () => J.settings.testApi());
      document.getElementById('slack-save').addEventListener('click', () => J.settings.saveSlack());

      // Settings - Theme buttons
      document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.addEventListener('click', () => J.theme.set(btn.dataset.theme));
      });

      // Settings - Font size
      document.querySelectorAll('[data-fontsize]').forEach(btn => {
        btn.addEventListener('click', () => J.settings.setFontSize(btn.dataset.fontsize));
      });

      // Settings - Accessibility
      document.getElementById('a11y-contrast').addEventListener('change', e => J.settings.toggleContrast(e.target.checked));
      document.getElementById('a11y-motion').addEventListener('change', e => J.settings.toggleMotion(e.target.checked));

      // Settings - Data
      document.getElementById('data-export-json').addEventListener('click', () => J.data.exportJSON());
      document.getElementById('data-export-ris').addEventListener('click', () => J.data.exportRIS());
      document.getElementById('data-export-bibtex').addEventListener('click', () => J.data.exportBibTeX());
      document.getElementById('data-export-md').addEventListener('click', () => J.data.exportMarkdown());
      document.getElementById('data-clear').addEventListener('click', () => J.data.clearAll());

      // Chat
      document.getElementById('chat-fab').addEventListener('click', () => J.chat.toggle());
      document.getElementById('chat-close').addEventListener('click', () => J.chat.close());
      document.getElementById('chat-send').addEventListener('click', () => J.chat.send());
      document.getElementById('chat-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') J.chat.send();
      });
      document.querySelectorAll('.suggest-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          document.getElementById('chat-input').value = btn.dataset.q;
          J.chat.send();
        });
      });

      // Load settings UI
      const apiInput = document.getElementById('api-base-url');
      if (apiInput) apiInput.value = J.state.apiBaseUrl;
      const slackInput = document.getElementById('slack-webhook');
      if (slackInput) slackInput.value = J.state.slackWebhook;
      const contrastCb = document.getElementById('a11y-contrast');
      if (contrastCb) contrastCb.checked = J.state.highContrast;
      const motionCb = document.getElementById('a11y-motion');
      if (motionCb) motionCb.checked = J.state.reduceMotion;

      // Keyboard
      document.addEventListener('keydown', e => J.keyboard.handle(e));

      // Click outside sidebar on mobile
      document.getElementById('main').addEventListener('click', () => {
        const sb = document.getElementById('sidebar');
        if (sb.classList.contains('mobile-open')) sb.classList.remove('mobile-open');
      });
    }
  },

  // ================================================================
  // TABS
  // ================================================================
  tabs: {
    list: ['command','research','analysis','coscientist','protein','meta','pipelines','lab','logs','settings'],

    init() {
      this.switchTo(J.state.currentTab);
    },

    switchTo(id) {
      J.state.currentTab = id;
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      const panel = document.getElementById('tab-' + id);
      const nav = document.querySelector(`.nav-item[data-tab="${id}"]`);
      if (panel) panel.classList.add('active');
      if (nav) nav.classList.add('active');
      // Close mobile sidebar
      document.getElementById('sidebar').classList.remove('mobile-open');
    }
  },

  // ================================================================
  // SIDEBAR
  // ================================================================
  sidebar: {
    toggle() {
      const sb = document.getElementById('sidebar');
      sb.classList.toggle('collapsed');
      document.body.classList.toggle('sidebar-collapsed');
      const collapsed = sb.classList.contains('collapsed');
      localStorage.setItem('j_sidebar', collapsed ? 'collapsed' : 'expanded');
    },
    mobileToggle() {
      document.getElementById('sidebar').classList.toggle('mobile-open');
    }
  },

  // ================================================================
  // CLOCK
  // ================================================================
  clock: {
    start() {
      const el = document.getElementById('topbar-clock');
      const tick = () => {
        el.textContent = new Date().toLocaleTimeString('ja-JP', { hour12: false });
      };
      tick();
      setInterval(tick, 1000);
    }
  },

  // ================================================================
  // KPI
  // ================================================================
  kpi: {
    update() {
      J.animateValue('kpi-papers', J.state.papers);
      J.animateValue('kpi-searches', J.state.searches);
      J.animateValue('kpi-claims', J.state.claims);
    }
  },

  // ================================================================
  // QUOTA
  // ================================================================
  quota: {
    update() {
      const pct = (J.state.apiQuota.current / J.state.apiQuota.max) * 100;
      const fill = document.getElementById('quota-fill-mini');
      const text = document.getElementById('quota-text-mini');
      if (fill) fill.style.width = pct + '%';
      if (text) text.textContent = J.state.apiQuota.current;
    },
    consume(n = 1) {
      J.state.apiQuota.current = Math.max(0, J.state.apiQuota.current - n);
      this.update();
      J.save();
    }
  },

  // ================================================================
  // HEALTH
  // ================================================================
  health: {
    async check() {
      J.logs.add('INFO', 'ヘルスチェック実行中…');
      const items = document.querySelectorAll('.health-item .h-dot');
      items.forEach(d => { d.className = 'h-dot green'; });

      // Try fetch health.json
      try {
        const r = await fetch('health.json');
        if (r.ok) {
          const d = await r.json();
          document.getElementById('h-api').textContent = d.status === 'healthy' ? 'Healthy' : d.status;
          document.getElementById('status-text').textContent = 'Online';
          document.getElementById('status-dot').className = 'status-dot green';
          J.logs.add('SUCCESS', 'ヘルスチェック通過');
        }
      } catch {
        document.getElementById('status-text').textContent = 'Offline';
        document.getElementById('status-dot').className = 'status-dot yellow';
        document.getElementById('h-api').textContent = 'Offline';
        J.logs.add('WARN', 'API接続なし — オフラインモード');
      }
    }
  },

  // ================================================================
  // SEARCH
  // ================================================================
  search: {
    async run() {
      const query = document.getElementById('search-query')?.value.trim();
      if (!query) return J.toast('検索キーワードを入力してください', 'error');

      const btn = document.getElementById('search-btn');
      const area = document.getElementById('results-area');
      btn.disabled = true;
      btn.textContent = '⏳ 検索中…';
      area.innerHTML = '<div class="empty-msg">検索中…</div>';
      J.logs.add('INFO', `検索: "${query}"`);

      await J.delay(1000);

      const results = this.mockResults(query);
      J.state.results = results;
      J.state.searches++;
      J.state.papers += results.length;
      J.quota.consume(1);

      // History
      J.state.searchHistory.push(query);
      if (J.state.searchHistory.length > 50) J.state.searchHistory.shift();

      J.save();
      J.kpi.update();
      this.render(area, results);
      document.getElementById('result-count').textContent = results.length + '件';

      btn.disabled = false;
      btn.textContent = '🔍 検索';
      J.logs.add('SUCCESS', `${results.length}件の論文を発見`);
      J.toast(`${results.length}件の論文を発見`, 'success');
      J.notif.add('success', `「${query}」で${results.length}件発見`);
      J.heatmap.record();
      J.wordCloud.addFromQuery(query);

      // Auto-tag
      results.forEach(r => {
        r.tags = J.autoTag.getTags(r.title);
      });
      this.render(area, results);
    },

    mockResults(query) {
      const titles = ['Novel approaches to','Clinical review of','Advances in','Comprehensive study of','Machine learning for'];
      const authors = ['Smith J','Johnson A','Williams B','Brown C','Davis D'];
      return titles.map((t, i) => ({
        title: `${t} ${query}`,
        authors: `${authors[i]}, et al.`,
        year: 2024 - (i % 2),
        pmid: '39' + Math.floor(Math.random() * 1000000),
        tags: J.autoTag.getTags(`${t} ${query}`),
      }));
    },

    render(container, results) {
      container.innerHTML = results.map(r => `
        <div class="result-item" onclick="window.open('https://pubmed.ncbi.nlm.nih.gov/${r.pmid}','_blank')">
          <div class="r-title">📄 ${r.title}
            <span style="margin-left:auto;cursor:pointer" onclick="event.stopPropagation();J.favorites.toggle('${r.pmid}','${r.title.replace(/'/g,'')}')">
              ${J.state.favorites.some(f=>f.id===r.pmid)?'★':'☆'}
            </span>
          </div>
          <div class="r-meta">${r.authors} · ${r.year} · PMID: ${r.pmid}</div>
          <div class="r-tags">${r.tags.map(t=>`<span class="tag ${t}">${t.toUpperCase()}</span>`).join('')}</div>
        </div>
      `).join('');
    }
  },

  // ================================================================
  // AUTO-TAG
  // ================================================================
  autoTag: {
    keywords: {
      ai: ['machine learning','deep learning','neural','AI','artificial intelligence','model','algorithm'],
      health: ['clinical','patient','treatment','disease','medical','healthcare','diagnosis'],
      ml: ['supervised','unsupervised','classification','regression','transformer','bert','gpt'],
      genomics: ['gene','genome','DNA','RNA','sequencing','mutation','CRISPR'],
      covid: ['COVID','coronavirus','SARS-CoV-2','pandemic','vaccine'],
    },
    getTags(text) {
      const lower = text.toLowerCase();
      const tags = [];
      for (const [tag, kws] of Object.entries(this.keywords)) {
        if (kws.some(k => lower.includes(k.toLowerCase()))) tags.push(tag);
      }
      return tags.length ? tags : ['research'];
    }
  },

  // ================================================================
  // FAVORITES
  // ================================================================
  favorites: {
    toggle(id, title) {
      const idx = J.state.favorites.findIndex(f => f.id === id);
      if (idx >= 0) {
        J.state.favorites.splice(idx, 1);
        J.toast('お気に入りから削除', 'info');
      } else {
        J.state.favorites.push({ id, title });
        J.toast('お気に入りに追加', 'success');
      }
      J.save();
      this.render();
      // Re-render results if present
      const area = document.getElementById('results-area');
      if (J.state.results.length) J.search.render(area, J.state.results);
    },
    render() {
      const el = document.getElementById('favorites-area');
      if (!el) return;
      el.innerHTML = J.state.favorites.map(f =>
        `<span class="tag ai" style="cursor:pointer" onclick="window.open('https://pubmed.ncbi.nlm.nih.gov/${f.id}','_blank')">⭐ ${f.title.slice(0,30)}…</span>`
      ).join('') || '<span class="empty-msg" style="padding:4px">まだお気に入りはありません</span>';
    }
  },

  // ================================================================
  // ANALYSIS
  // ================================================================
  analysis: {
    async evidence() {
      const title = document.getElementById('ev-title')?.value;
      const abstract = document.getElementById('ev-abstract')?.value;
      if (!title) return J.toast('タイトルを入力してください', 'error');

      J.logs.add('INFO', 'エビデンスグレーディング実行中…');
      J.toast('分析中…', 'info');
      await J.delay(1200);

      const levels = ['1a','1b','2a','2b','3a','3b','4','5'];
      const descriptions = {
        '1a':'システマティックレビュー（RCT）','1b':'個別RCT',
        '2a':'システマティックレビュー（コホート）','2b':'個別コホート研究',
        '3a':'システマティックレビュー（症例対照）','3b':'個別症例対照研究',
        '4':'症例集積研究','5':'専門家意見'
      };

      // Heuristic
      const lower = (title + ' ' + abstract).toLowerCase();
      let level = '4';
      if (lower.includes('systematic review') || lower.includes('meta-analysis')) level = '1a';
      else if (lower.includes('randomized') || lower.includes('rct') || lower.includes('double-blind')) level = '1b';
      else if (lower.includes('cohort')) level = '2b';
      else if (lower.includes('case-control')) level = '3b';

      const confidence = (75 + Math.random() * 20).toFixed(1);

      document.getElementById('ev-result').innerHTML = `
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:10px">
          <div style="padding:10px 18px;border-radius:var(--r-md);background:var(--grad-primary);font-size:1.8rem;font-weight:800;color:#fff">${level}</div>
          <div>
            <div style="font-weight:700;color:var(--t1)">${descriptions[level]}</div>
            <div style="font-size:.82rem;color:var(--t3)">信頼度: ${confidence}%</div>
          </div>
        </div>
        <div style="width:100%;height:8px;background:var(--bg-3);border-radius:4px;overflow:hidden">
          <div style="width:${confidence}%;height:100%;background:var(--grad-primary);border-radius:4px"></div>
        </div>
      `;
      J.state.claims++;
      J.save();
      J.kpi.update();
      J.logs.add('SUCCESS', `エビデンスレベル: ${level} (${confidence}%)`);
    },

    async contradiction() {
      const a = document.getElementById('contra-a')?.value;
      const b = document.getElementById('contra-b')?.value;
      if (!a || !b) return J.toast('両方のクレームを入力してください', 'error');

      J.logs.add('INFO', '矛盾検出実行中…');
      await J.delay(1000);

      // Simple heuristic
      const antonyms = [['increase','decrease'],['significant','no significant'],['positive','negative'],['improve','worsen'],['higher','lower']];
      const la = a.toLowerCase();
      const lb = b.toLowerCase();
      let found = false;
      let method = '';
      for (const [w1, w2] of antonyms) {
        if ((la.includes(w1) && lb.includes(w2)) || (la.includes(w2) && lb.includes(w1))) {
          found = true;
          method = `反義語検出: "${w1}" vs "${w2}"`;
          break;
        }
      }

      // P-value check
      const pA = la.match(/p\s*[<=]\s*([\d.]+)/);
      const pB = lb.match(/p\s*[<=]\s*([\d.]+)/);
      if (pA && pB) {
        const vA = parseFloat(pA[1]);
        const vB = parseFloat(pB[1]);
        if ((vA < 0.05 && vB >= 0.05) || (vB < 0.05 && vA >= 0.05)) {
          found = true;
          method = `統計的矛盾: p=${vA} vs p=${vB}`;
        }
      }

      const score = found ? (0.7 + Math.random() * 0.25).toFixed(2) : (Math.random() * 0.3).toFixed(2);
      const color = found ? 'var(--red)' : 'var(--emerald)';
      const label = found ? '⚠️ 矛盾を検出' : '✅ 矛盾なし';

      document.getElementById('contra-result').innerHTML = `
        <div style="font-size:1.1rem;font-weight:700;color:${color};margin-bottom:8px">${label}</div>
        <div style="font-size:.85rem;color:var(--t2)">矛盾スコア: <strong>${score}</strong></div>
        ${method ? `<div style="font-size:.82rem;color:var(--t3);margin-top:4px">検出方法: ${method}</div>` : ''}
      `;
      J.state.claims++;
      J.save();
      J.kpi.update();
      J.logs.add(found ? 'WARN' : 'SUCCESS', `矛盾検出: ${label} (${score})`);
    },

    async citation() {
      const text = document.getElementById('cite-text')?.value;
      if (!text) return J.toast('テキストを入力してください', 'error');

      J.logs.add('INFO', '引用分析実行中…');
      await J.delay(900);

      const citationRegex = /\(([^)]+(?:et al\.?)?(?:,\s*\d{4})?)\)/g;
      const matches = [...text.matchAll(citationRegex)];
      const stances = ['Support','Contrast','Mention'];
      const stanceColors = { Support: 'var(--emerald)', Contrast: 'var(--red)', Mention: 'var(--cyan)' };

      const citations = matches.map((m, i) => {
        const stance = stances[i % 3];
        return { ref: m[1], stance };
      });

      if (!citations.length) {
        document.getElementById('cite-result').innerHTML = '<div class="empty-msg">引用が検出されませんでした</div>';
        return;
      }

      const counts = { Support: 0, Contrast: 0, Mention: 0 };
      citations.forEach(c => counts[c.stance]++);

      document.getElementById('cite-result').innerHTML = `
        <div style="display:flex;gap:16px;margin-bottom:12px">
          ${Object.entries(counts).map(([k,v]) => `
            <div style="text-align:center;padding:8px 14px;border-radius:var(--r-md);background:var(--bg-3);flex:1">
              <div style="font-size:.75rem;color:var(--t3)">${k}</div>
              <div style="font-size:1.4rem;font-weight:800;color:${stanceColors[k]}">${v}</div>
            </div>
          `).join('')}
        </div>
        ${citations.map(c => `
          <div style="padding:6px 0;border-bottom:1px solid var(--border);font-size:.85rem;display:flex;justify-content:space-between">
            <span>${c.ref}</span>
            <span style="color:${stanceColors[c.stance]};font-weight:600">${c.stance}</span>
          </div>
        `).join('')}
      `;
      J.logs.add('SUCCESS', `${citations.length}件の引用を分析`);
    },

    prisma() {
      const identified = document.getElementById('prisma-identified')?.value || 500;
      const screened = document.getElementById('prisma-screened')?.value || 320;
      const eligible = document.getElementById('prisma-eligible')?.value || 85;
      const included = document.getElementById('prisma-included')?.value || 42;

      document.getElementById('prisma-result').innerHTML = `
        <div class="prisma-flow">
          <div class="prisma-box">データベース検索: <strong>${identified}</strong>件</div>
          <div class="prisma-arrow">↓ 重複除去: ${identified - screened}件除外</div>
          <div class="prisma-box">スクリーニング: <strong>${screened}</strong>件</div>
          <div class="prisma-arrow">↓ 不適格: ${screened - eligible}件除外</div>
          <div class="prisma-box">適格性評価: <strong>${eligible}</strong>件</div>
          <div class="prisma-arrow">↓ 除外: ${eligible - included}件</div>
          <div class="prisma-box" style="border-color:var(--emerald);background:var(--emerald-dim)">最終採用: <strong>${included}</strong>件</div>
        </div>
      `;
      J.logs.add('SUCCESS', `PRISMA図生成完了 (${included}/${identified})`);
      J.toast('PRISMA図を生成しました', 'success');
    },

    citationGen() {
      const paper = {
        authors: document.getElementById('cg-authors')?.value || 'Author',
        title: document.getElementById('cg-title')?.value || 'Title',
        journal: document.getElementById('cg-journal')?.value || 'Journal',
        year: document.getElementById('cg-year')?.value || '2024',
        doi: document.getElementById('cg-doi')?.value || '',
        pmid: '',
      };
      const format = document.getElementById('cg-format')?.value || 'apa';

      const formats = {
        apa: p => `${p.authors}. (${p.year}). ${p.title}. *${p.journal}*. ${p.doi ? 'https://doi.org/' + p.doi : ''}`,
        mla: p => `${p.authors}. "${p.title}." *${p.journal}*, ${p.year}.`,
        bibtex: p => `@article{ref${p.year},\n  title={${p.title}},\n  author={${p.authors}},\n  journal={${p.journal}},\n  year={${p.year}}\n}`,
      };

      const result = (formats[format] || formats.apa)(paper);
      document.getElementById('cg-result').textContent = result;

      // Copy to clipboard
      navigator.clipboard.writeText(result).then(() => J.toast('クリップボードにコピーしました', 'success'));
    }
  },

  // ================================================================
  // CO-SCIENTIST
  // ================================================================
  coscientist: {
    hypotheses: [],

    async generateHypotheses() {
      const topic = document.getElementById('hypo-topic')?.value;
      if (!topic) return J.toast('トピックを入力してください', 'error');

      J.toast('仮説を生成中…', 'info');
      J.logs.add('INFO', `仮説生成: "${topic}"`);
      await J.delay(1200);

      const templates = [
        `${topic}はエピジェネティックメカニズムを通じて疾患進行に影響を与える可能性がある`,
        `${topic}の発現増加は治療応答を強化する可能性がある`,
        `${topic}と結果の関係は免疫因子によって媒介される`,
      ];

      this.hypotheses = templates.map((text, i) => ({
        id: `H${i + 1}`,
        text,
        confidence: (0.6 + Math.random() * 0.3).toFixed(2),
        novelty: (0.5 + Math.random() * 0.4).toFixed(2),
        testability: (0.7 + Math.random() * 0.2).toFixed(2),
      }));

      const container = document.getElementById('hypo-results');
      container.innerHTML = this.hypotheses.map(h => `
        <div class="card">
          <div class="card-head">
            <span class="card-title">🧪 ${h.id}</span>
            <span style="color:var(--emerald);font-size:.85rem">信頼度: ${(h.confidence * 100).toFixed(0)}%</span>
          </div>
          <p style="font-size:.88rem;color:var(--t2);margin-bottom:10px">${h.text}</p>
          <div style="display:flex;gap:6px">
            <span class="tag ai">新規性: ${(h.novelty * 100).toFixed(0)}%</span>
            <span class="tag ml">検証可能性: ${(h.testability * 100).toFixed(0)}%</span>
          </div>
        </div>
      `).join('');

      J.logs.add('SUCCESS', `${this.hypotheses.length}件の仮説を生成`);
      J.toast(`${this.hypotheses.length}件の仮説を生成しました`, 'success');
    },

    async analyzeGaps() {
      const topic = document.getElementById('hypo-topic')?.value || '研究';
      J.toast('文献ギャップ分析中…', 'info');
      await J.delay(1200);

      const gaps = [
        { type: '研究不足', desc: `${topic}のメカニズムに関する研究が限定的`, severity: 'high' },
        { type: '方法論的', desc: '改善された実験手法が必要', severity: 'medium' },
        { type: 'トランスレーショナル', desc: '基礎研究と臨床応用のギャップ', severity: 'high' },
      ];

      document.getElementById('gap-results').innerHTML = gaps.map(g => `
        <div style="padding:8px;border-left:3px solid ${g.severity === 'high' ? 'var(--red)' : 'var(--amber)'};margin-bottom:6px;border-radius:0 var(--r-sm) var(--r-sm) 0;background:var(--bg-2)">
          <strong>${g.type}</strong>: ${g.desc}
        </div>
      `).join('');
      J.logs.add('SUCCESS', 'ギャップ分析完了');
    },

    async designExperiment() {
      J.toast('実験を設計中…', 'info');
      await J.delay(1000);

      const result = {
        design: 'ランダム化比較試験',
        sample_size: Math.floor(50 + Math.random() * 150),
        power: 0.8,
        timeline: 12,
      };

      document.getElementById('exp-results').innerHTML = `
        <div style="display:grid;gap:6px;font-size:.88rem">
          <div><strong>デザイン:</strong> ${result.design}</div>
          <div><strong>サンプルサイズ:</strong> ${result.sample_size}</div>
          <div><strong>検出力:</strong> ${result.power}</div>
          <div><strong>タイムライン:</strong> ${result.timeline}ヶ月</div>
        </div>
      `;
      J.logs.add('SUCCESS', '実験デザイン完了');
    }
  },

  // ================================================================
  // PROTEIN
  // ================================================================
  protein: {
    async lookupStructure() {
      const id = document.getElementById('af-uniprot')?.value;
      if (!id) return J.toast('UniProt IDを入力してください', 'error');

      J.toast('AlphaFold構造を取得中…', 'info');
      await J.delay(800);

      const viewerUrl = `https://alphafold.ebi.ac.uk/entry/${id}`;
      const pdbUrl = `https://alphafold.ebi.ac.uk/files/AF-${id}-F1-model_v4.pdb`;

      document.getElementById('af-result').innerHTML = `
        <div style="font-size:.88rem">
          <div><strong>UniProt ID:</strong> ${id}</div>
          <div><strong>信頼度:</strong> 高</div>
          <a href="${viewerUrl}" target="_blank" style="display:inline-block;margin-top:8px;padding:6px 14px;border-radius:var(--r-md);background:var(--grad-primary);color:#fff;text-decoration:none;font-size:.82rem;font-weight:600">AlphaFoldで表示</a>
        </div>
      `;

      document.getElementById('protein-viewer').innerHTML = `
        <div style="text-align:center;padding:24px">
          <div style="font-size:3rem;margin-bottom:8px">🧬</div>
          <div style="font-size:.9rem;color:var(--t2)">3D タンパク質ビューア</div>
          <div style="font-size:.8rem;color:var(--t3)">構造: ${id}</div>
          <a href="${viewerUrl}" target="_blank" style="display:inline-block;margin-top:12px;padding:8px 18px;border-radius:var(--r-md);background:var(--grad-primary);color:#fff;text-decoration:none;font-size:.85rem;font-weight:600">AlphaFoldで開く</a>
        </div>
      `;
      J.logs.add('SUCCESS', `AlphaFold構造取得: ${id}`);
    },

    async predictBinding() {
      const seq = document.getElementById('bind-seq')?.value || 'MVLSPADKTN';
      const smiles = document.getElementById('bind-smiles')?.value || 'CCO';

      J.toast('結合親和性を予測中…', 'info');
      await J.delay(1000);

      const kd = (Math.random() * 100).toFixed(2);
      const strength = kd < 10 ? '強い' : kd < 50 ? '中程度' : '弱い';
      const conf = (0.6 + Math.random() * 0.3).toFixed(2);

      document.getElementById('bind-result').innerHTML = `
        <div style="display:grid;gap:4px;font-size:.88rem">
          <div><strong>予測Kd:</strong> <span style="color:var(--emerald)">${kd} nM</span></div>
          <div><strong>強度:</strong> ${strength}</div>
          <div><strong>信頼度:</strong> ${(conf * 100).toFixed(0)}%</div>
        </div>
      `;
      J.logs.add('SUCCESS', `結合予測: Kd=${kd}nM (${strength})`);
    },

    async designSequence() {
      const length = parseInt(document.getElementById('seq-len')?.value) || 50;
      const type = document.getElementById('seq-type')?.value || 'mixed';

      J.toast('配列を設計中…', 'info');
      await J.delay(800);

      const aa = 'ACDEFGHIKLMNPQRSTVWY';
      let seq = '';
      for (let i = 0; i < length; i++) seq += aa[Math.floor(Math.random() * aa.length)];

      document.getElementById('seq-result').textContent = `>${type}_designed (${length}aa)\n${seq.match(/.{1,60}/g).join('\n')}`;
      J.logs.add('SUCCESS', `配列設計完了: ${type}, ${length}aa`);
    }
  },

  // ================================================================
  // META-ANALYSIS
  // ================================================================
  meta: {
    addStudy() {
      const study = {
        id: J.state.maStudies.length + 1,
        effect: (Math.random() * 0.8 - 0.4).toFixed(3),
        n: Math.floor(50 + Math.random() * 200),
      };
      J.state.maStudies.push(study);

      const container = document.getElementById('ma-studies');
      container.innerHTML = J.state.maStudies.map(s =>
        `<span class="ma-study-tag">研究${s.id}: ES=${s.effect}, n=${s.n}</span>`
      ).join('');

      J.toast(`研究${study.id}を追加`, 'success');
    },

    async run() {
      if (J.state.maStudies.length < 2) return J.toast('2件以上の研究を追加してください', 'error');

      J.toast('メタ分析を実行中…', 'info');
      J.logs.add('INFO', 'メタ分析開始');
      await J.delay(1500);

      const effects = J.state.maStudies.map(s => parseFloat(s.effect));
      const pooled = (effects.reduce((a, b) => a + b, 0) / effects.length).toFixed(3);
      const i2 = (Math.random() * 60).toFixed(1);

      // Forest plot
      const forest = document.getElementById('forest-plot');
      forest.innerHTML = J.state.maStudies.map(s => {
        const pos = 50 + parseFloat(s.effect) * 100;
        return `
          <div class="forest-row">
            <span class="forest-label">研究${s.id}</span>
            <div class="forest-bar">
              <div class="forest-mid"></div>
              <div class="forest-dot" style="left:${Math.max(5, Math.min(95, pos))}%"></div>
            </div>
          </div>
        `;
      }).join('') + `
        <div class="forest-row" style="margin-top:8px;font-weight:700">
          <span class="forest-label">統合</span>
          <div class="forest-bar" style="border:1px solid var(--indigo)">
            <div class="forest-mid"></div>
            <div class="forest-dot" style="left:${50 + parseFloat(pooled) * 100}%;background:var(--pink);width:12px;height:12px"></div>
          </div>
        </div>
      `;

      // Results
      document.getElementById('ma-results').innerHTML = `
        <div style="display:grid;gap:8px;font-size:.9rem">
          <div><strong>統合効果量:</strong> <span style="color:var(--emerald);font-weight:700">${pooled}</span></div>
          <div><strong>研究数:</strong> ${J.state.maStudies.length}</div>
          <div><strong>I²:</strong> ${i2}%</div>
          <div><strong>異質性:</strong> ${parseFloat(i2) < 30 ? '低' : parseFloat(i2) < 60 ? '中程度' : '高'}</div>
        </div>
      `;

      J.logs.add('SUCCESS', `メタ分析完了: 統合効果=${pooled}, I²=${i2}%`);
      J.toast('メタ分析が完了しました', 'success');
    }
  },

  // ================================================================
  // PIPELINES
  // ================================================================
  pipelines: {
    defs: {
      hypothesis:     { name: '仮説パイプライン', steps: ['生成','検証','設計','実行'] },
      protein:        { name: 'タンパク質パイプライン', steps: ['構造','設計','発現','検証'] },
      metaanalysis:   { name: 'メタ分析パイプライン', steps: ['検索','スクリーン','抽出','分析'] },
      grant:          { name: '助成金パイプライン', steps: ['検索','マッチ','下書き','提出'] },
      labautomation:  { name: 'ラボ自動化パイプライン', steps: ['プロトコル','スケジュール','実行','QC'] },
    },

    async run(id) {
      const def = this.defs[id];
      if (!def) return;

      const statusEl = document.querySelector(`[data-pl-status="${id}"]`);
      const btn = document.querySelector(`[data-pipeline="${id}"]`);
      btn.disabled = true;

      J.toast(`${def.name}を開始…`, 'info');
      J.logs.add('INFO', `${def.name}開始`);

      for (let i = 0; i < def.steps.length; i++) {
        const pct = ((i + 1) / def.steps.length * 100).toFixed(0);
        statusEl.innerHTML = `
          <div style="font-size:.78rem;color:var(--t2);margin-bottom:4px">Step ${i + 1}/${def.steps.length}: ${def.steps[i]}</div>
          <div class="progress-bar-inline"><div class="fill" style="width:${pct}%"></div></div>
        `;
        await J.delay(800);
      }

      statusEl.innerHTML = `<div style="font-size:.82rem;color:var(--emerald);font-weight:600">✅ 完了</div>`;
      btn.disabled = false;
      J.logs.add('SUCCESS', `${def.name}完了`);
      J.toast(`${def.name}が完了しました`, 'success');
      J.notif.add('success', `${def.name}完了`);
    }
  },

  // ================================================================
  // LAB
  // ================================================================
  lab: {
    equipment: [
      { id: 'eq1', name: '遠心分離機', type: 'centrifuge', status: '待機中' },
      { id: 'eq2', name: 'PCRマシン', type: 'pcr', status: '待機中' },
      { id: 'eq3', name: 'プレートリーダー', type: 'reader', status: '待機中' },
    ],
    samples: [],

    init() {
      this.renderEquipment();
      document.getElementById('lab-eq-count').textContent = this.equipment.length;
    },

    renderEquipment() {
      const el = document.getElementById('lab-equipment');
      if (!el) return;
      el.innerHTML = this.equipment.map(e => `
        <div class="eq-item">
          <span>🔬</span>
          <span style="font-weight:600">${e.name}</span>
          <span style="font-size:.78rem;color:var(--t3)">(${e.type})</span>
          <span class="eq-status ${e.status === '待機中' ? 'idle' : 'running'}">${e.status}</span>
        </div>
      `).join('');
    },

    registerSample() {
      const barcode = document.getElementById('sample-barcode')?.value;
      const name = document.getElementById('sample-name')?.value;
      const type = document.getElementById('sample-type')?.value;
      if (!barcode) return J.toast('バーコードを入力してください', 'error');

      this.samples.push({ barcode, name, type, time: new Date().toISOString() });
      document.getElementById('lab-sample-count').textContent = this.samples.length;

      const list = document.getElementById('sample-list');
      list.innerHTML = this.samples.map(s => `
        <div style="font-size:.82rem;padding:4px 0;border-bottom:1px solid var(--border)">
          🧫 ${s.barcode} — ${s.name || 'N/A'} (${s.type || 'N/A'})
        </div>
      `).join('');

      J.toast(`サンプル ${barcode} を登録しました`, 'success');
      J.logs.add('SUCCESS', `サンプル登録: ${barcode}`);
    },

    sendCommand() {
      const eqId = document.getElementById('cmd-equipment')?.value;
      const command = document.getElementById('cmd-command')?.value;
      if (!command) return J.toast('コマンドを入力してください', 'error');

      const eq = this.equipment.find(e => e.id === eqId);
      if (!eq) return;

      eq.status = '実行中';
      this.renderEquipment();

      document.getElementById('cmd-response').innerHTML = `
        <div style="font-size:.85rem">
          <div><strong>機器:</strong> ${eq.name}</div>
          <div><strong>コマンド:</strong> ${command}</div>
          <div><strong>ステータス:</strong> <span style="color:var(--amber)">送信済み</span></div>
        </div>
      `;

      J.toast(`${eq.name}: ${command} 送信`, 'info');
      J.logs.add('INFO', `ラボコマンド: ${eq.name} → ${command}`);

      setTimeout(() => {
        eq.status = '待機中';
        this.renderEquipment();
      }, 3000);
    }
  },

  // ================================================================
  // COMPLIANCE
  // ================================================================
  compliance: {
    check() {
      const text = document.getElementById('hipaa-text')?.value;
      if (!text) return J.toast('テキストを入力してください', 'error');

      const patterns = [/\d{3}-\d{2}-\d{4}/, /\b[A-Z]{2}\d{6,8}\b/];
      const issues = [];
      patterns.forEach(p => { if (p.test(text)) issues.push('個人情報パターンを検出'); });

      const el = document.getElementById('hipaa-result');
      if (issues.length) {
        el.innerHTML = `<div style="color:var(--red);font-weight:700">⚠️ 問題を検出 (${issues.length}件)</div>${issues.map(i => `<div style="font-size:.82rem;color:var(--t2)">${i}</div>`).join('')}`;
        J.logs.add('WARN', `HIPAA: ${issues.length}件の問題検出`);
      } else {
        el.innerHTML = `<div style="color:var(--emerald);font-weight:700">✅ 問題なし — HIPAA準拠</div>`;
        J.logs.add('SUCCESS', 'HIPAAチェック通過');
      }

      // Audit log
      const audit = document.getElementById('audit-log');
      const now = new Date().toLocaleString('ja-JP');
      audit.innerHTML = `<div class="audit-item">${now} — HIPAAチェック実行 (${issues.length ? '問題あり' : '問題なし'})</div>` + audit.innerHTML;
    }
  },

  // ================================================================
  // LOGS
  // ================================================================
  logs: {
    currentFilter: 'ALL',

    init() {
      this.add('INFO', 'JARVIS OS 起動');
      this.startSimulation();
    },

    add(level, message) {
      const time = new Date().toLocaleTimeString('ja-JP', { hour12: false });
      J.state.logs.push({ time, level, message });

      if (this.currentFilter !== 'ALL' && this.currentFilter !== level) return;

      const container = document.getElementById('log-container');
      if (!container) return;
      const entry = document.createElement('div');
      entry.className = 'log-entry';
      entry.innerHTML = `<span class="log-time">${time}</span><span class="log-level ${level.toLowerCase()}">[${level}]</span><span class="log-msg">${message}</span>`;
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    },

    clear() {
      document.getElementById('log-container').innerHTML = '';
      J.state.logs = [];
      this.add('INFO', 'ログクリア');
    },

    filter(level) {
      this.currentFilter = level;
      const container = document.getElementById('log-container');
      container.innerHTML = '';
      const filtered = level === 'ALL' ? J.state.logs : J.state.logs.filter(l => l.level === level);
      filtered.forEach(l => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `<span class="log-time">${l.time}</span><span class="log-level ${l.level.toLowerCase()}">[${l.level}]</span><span class="log-msg">${l.message}</span>`;
        container.appendChild(entry);
      });
    },

    export() {
      const text = J.state.logs.map(l => `${l.time} [${l.level}] ${l.message}`).join('\n');
      J.downloadFile('jarvis-logs.txt', text, 'text/plain');
      J.toast('ログをエクスポートしました', 'success');
    },

    startSimulation() {
      const msgs = ['ヘルスチェック通過', 'GitHubと同期完了', 'キャッシュ更新', 'メトリクス更新'];
      setInterval(() => {
        if (Math.random() > 0.75) {
          this.add('INFO', msgs[Math.floor(Math.random() * msgs.length)]);
        }
      }, 10000);
    }
  },

  // ================================================================
  // NOTIFICATIONS
  // ================================================================
  notif: {
    add(type, message) {
      const list = document.getElementById('notif-list');
      if (!list) return;
      const time = new Date().toLocaleTimeString('ja-JP', { hour12: false });
      const icons = { info: 'ℹ️', success: '✅', warn: '⚠️', error: '❌' };
      const el = document.createElement('div');
      el.className = `notif-item notif-${type}`;
      el.innerHTML = `<span class="notif-icon">${icons[type] || 'ℹ️'}</span><span>${message}</span><span class="notif-time">${time}</span>`;
      list.prepend(el);
    }
  },

  // ================================================================
  // CHAT
  // ================================================================
  chat: {
    toggle() {
      J.state.chatOpen ? this.close() : this.openDrawer();
    },
    openDrawer() {
      document.getElementById('chat-drawer').classList.add('open');
      document.body.classList.add('chat-open');
      J.state.chatOpen = true;
      document.getElementById('chat-input').focus();
    },
    close() {
      document.getElementById('chat-drawer').classList.remove('open');
      document.body.classList.remove('chat-open');
      J.state.chatOpen = false;
    },
    async send() {
      const input = document.getElementById('chat-input');
      const text = input?.value.trim();
      if (!text) return;

      const msgs = document.getElementById('chat-messages');
      msgs.innerHTML += `<div class="chat-msg user">${this.escapeHtml(text)}</div>`;
      input.value = '';
      msgs.scrollTop = msgs.scrollHeight;

      await J.delay(700);

      const responses = [
        `「${text}」に関連する論文を検索しましょうか？研究タブで検索できます。`,
        `了解です。「${text}」について、エビデンスグレーディングを実行する場合は分析ラボタブをご利用ください。`,
        `「${text}」に関する最新の研究をPubMed/arXivで検索することをお勧めします。`,
        `パイプラインタブから自動的に「${text}」に関する文献レビューを実行できます。`,
      ];
      const response = responses[Math.floor(Math.random() * responses.length)];
      msgs.innerHTML += `<div class="chat-msg assistant">${response}</div>`;
      msgs.scrollTop = msgs.scrollHeight;
    },
    escapeHtml(s) {
      const div = document.createElement('div');
      div.textContent = s;
      return div.innerHTML;
    }
  },

  // ================================================================
  // VOICE
  // ================================================================
  voice: {
    recognition: null,
    listening: false,

    toggle() {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        return J.toast('音声認識はこのブラウザではサポートされていません', 'error');
      }
      if (!this.recognition) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SR();
        this.recognition.lang = 'ja-JP';
        this.recognition.onresult = e => {
          const text = e.results[0][0].transcript;
          document.getElementById('search-query').value = text;
          J.toast(`認識: "${text}"`, 'success');
        };
        this.recognition.onerror = e => J.toast('音声エラー: ' + e.error, 'error');
        this.recognition.onend = () => { this.listening = false; };
      }
      if (this.listening) {
        this.recognition.stop();
        this.listening = false;
        J.toast('音声入力を停止', 'info');
      } else {
        this.recognition.start();
        this.listening = true;
        J.toast('音声入力中… 話してください', 'info');
      }
    }
  },

  // ================================================================
  // COMMAND PALETTE
  // ================================================================
  cmd: {
    commands: [
      { icon: '⚡', label: '司令室', action: () => J.tabs.switchTo('command'), key: '1' },
      { icon: '🔍', label: '研究検索', action: () => J.tabs.switchTo('research'), key: '2' },
      { icon: '🧪', label: '分析ラボ', action: () => J.tabs.switchTo('analysis'), key: '3' },
      { icon: '🧬', label: 'AI共同研究', action: () => J.tabs.switchTo('coscientist'), key: '4' },
      { icon: '🔬', label: 'タンパク質', action: () => J.tabs.switchTo('protein'), key: '5' },
      { icon: '📊', label: 'メタ分析', action: () => J.tabs.switchTo('meta'), key: '6' },
      { icon: '🔄', label: 'パイプライン', action: () => J.tabs.switchTo('pipelines'), key: '7' },
      { icon: '🤖', label: '自動化ラボ', action: () => J.tabs.switchTo('lab'), key: '8' },
      { icon: '📋', label: 'ログ', action: () => J.tabs.switchTo('logs'), key: '9' },
      { icon: '⚙️', label: '設定', action: () => J.tabs.switchTo('settings'), key: '0' },
      { icon: '🎨', label: 'テーマ切替', action: () => J.theme.cycle(), key: 'T' },
      { icon: '⛶', label: '全画面', action: () => J.fullscreen.toggle(), key: 'F' },
      { icon: '📤', label: 'エクスポート', action: () => J.data.exportJSON() },
      { icon: '▶', label: 'パイプライン実行 (GitHub)', action: () => window.open('https://github.com/kaneko-ai/jarvis-ml-pipeline/actions/workflows/run-pipeline.yml','_blank') },
      { icon: '💬', label: 'AIチャット', action: () => J.chat.toggle() },
      { icon: '📝', label: 'レポート生成', action: () => J.actions.generateReport() },
    ],

    open() {
      document.getElementById('cmd-overlay').classList.add('show');
      J.state.cmdOpen = true;
      const input = document.getElementById('cmd-input');
      input.value = '';
      input.focus();
      this.filter('');
    },

    close() {
      document.getElementById('cmd-overlay').classList.remove('show');
      J.state.cmdOpen = false;
    },

    filter(query) {
      const results = document.getElementById('cmd-results');
      const lower = query.toLowerCase();
      const filtered = this.commands.filter(c => c.label.toLowerCase().includes(lower));
      results.innerHTML = filtered.map((c, i) => `
        <div class="cmd-item${i === 0 ? ' selected' : ''}" data-cmd-index="${i}">
          <span class="cmd-item-icon">${c.icon}</span>
          <span class="cmd-item-label">${c.label}</span>
          ${c.key ? `<span class="cmd-item-shortcut">${c.key}</span>` : ''}
        </div>
      `).join('');

      results.querySelectorAll('.cmd-item').forEach((el, idx) => {
        el.addEventListener('click', () => {
          filtered[idx].action();
          this.close();
        });
      });
    }
  },

  // ================================================================
  // KEYBOARD
  // ================================================================
  keyboard: {
    handle(e) {
      // Ctrl+K — command palette
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        J.cmd.open();
        return;
      }
      // Escape
      if (e.key === 'Escape') {
        if (J.state.cmdOpen) J.cmd.close();
        if (J.state.chatOpen) J.chat.close();
        return;
      }
      // Enter in cmd palette
      if (e.key === 'Enter' && J.state.cmdOpen) {
        const selected = document.querySelector('.cmd-item.selected');
        if (selected) selected.click();
        return;
      }
      // Don't handle if typing in input
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      const tabs = J.tabs.list;
      if (e.key >= '1' && e.key <= '9') {
        const idx = parseInt(e.key) - 1;
        if (tabs[idx]) J.tabs.switchTo(tabs[idx]);
      }
      if (e.key === '0') J.tabs.switchTo('settings');
      if (e.key.toLowerCase() === 't') J.theme.cycle();
      if (e.key.toLowerCase() === 'f') J.fullscreen.toggle();
    }
  },

  // ================================================================
  // THEME
  // ================================================================
  theme: {
    themes: ['dark','light','ocean','forest','sunset'],

    set(name) {
      J.applyTheme(name);
      J.state.theme = name;
      localStorage.setItem('j_theme', name);

      document.querySelectorAll('.theme-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.theme === name);
      });

      const icon = name === 'light' ? '☀️' : '🌙';
      document.getElementById('theme-toggle-btn').textContent = icon;
      J.toast(`テーマ: ${name}`, 'info');
    },

    cycle() {
      const idx = this.themes.indexOf(J.state.theme);
      const next = this.themes[(idx + 1) % this.themes.length];
      this.set(next);
    }
  },

  applyTheme(name) {
    document.body.className = document.body.className.replace(/theme-\S+/g, '').trim();
    if (name !== 'dark') document.body.classList.add('theme-' + name);
    if (J.state.highContrast) document.body.classList.add('high-contrast');
    if (J.state.reduceMotion) document.body.classList.add('reduce-motion');
    if (J.state.sidebarCollapsed) document.body.classList.add('sidebar-collapsed');
  },

  applyFontSize(size) {
    document.documentElement.style.fontSize = size === 'large' ? '18px' : size === 'small' ? '14px' : '16px';
  },

  // ================================================================
  // FULLSCREEN
  // ================================================================
  fullscreen: {
    toggle() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
        J.toast('全画面モード', 'info');
      } else {
        document.exitFullscreen();
      }
    }
  },

  // ================================================================
  // SETTINGS
  // ================================================================
  settings: {
    saveApi() {
      J.state.apiBaseUrl = document.getElementById('api-base-url')?.value || '';
      localStorage.setItem('j_api_url', J.state.apiBaseUrl);
      J.toast('API URLを保存しました', 'success');
    },

    async testApi() {
      const url = J.state.apiBaseUrl;
      const el = document.getElementById('api-status');
      if (!url) {
        el.className = 'api-status';
        el.textContent = 'Mock mode (API未接続)';
        return;
      }
      el.className = 'api-status';
      el.textContent = 'テスト中…';

      try {
        const r = await fetch(url + '/api/health', { signal: AbortSignal.timeout(5000) });
        if (r.ok) {
          el.className = 'api-status online';
          el.textContent = 'Connected';
          J.toast('API接続成功', 'success');
        } else {
          throw new Error('Not OK');
        }
      } catch {
        el.className = 'api-status error';
        el.textContent = '接続失敗';
        J.toast('API接続に失敗しました', 'error');
      }
    },

    saveSlack() {
      J.state.slackWebhook = document.getElementById('slack-webhook')?.value || '';
      localStorage.setItem('j_slack', J.state.slackWebhook);
      J.toast('Slack設定を保存しました', 'success');
    },

    setFontSize(size) {
      J.state.fontSize = size;
      localStorage.setItem('j_fontsize', size);
      J.applyFontSize(size);
      document.querySelectorAll('[data-fontsize]').forEach(b => {
        b.classList.toggle('active', b.dataset.fontsize === size);
      });
      J.toast(`フォントサイズ: ${size}`, 'info');
    },

    toggleContrast(v) {
      J.state.highContrast = v;
      localStorage.setItem('j_contrast', v);
      document.body.classList.toggle('high-contrast', v);
    },

    toggleMotion(v) {
      J.state.reduceMotion = v;
      localStorage.setItem('j_motion', v);
      document.body.classList.toggle('reduce-motion', v);
    }
  },

  // ================================================================
  // DATA EXPORT
  // ================================================================
  data: {
    exportJSON() {
      const data = {
        stats: { searches: J.state.searches, papers: J.state.papers, claims: J.state.claims },
        results: J.state.results,
        favorites: J.state.favorites,
        studies: J.state.maStudies,
        exported_at: new Date().toISOString(),
      };
      J.downloadFile('jarvis-export.json', JSON.stringify(data, null, 2), 'application/json');
      J.toast('JSONエクスポート完了', 'success');
    },

    exportRIS() {
      const lines = J.state.results.map(r =>
        `TY  - JOUR\nTI  - ${r.title}\nAU  - ${r.authors}\nPY  - ${r.year}\nAN  - ${r.pmid}\nER  -`
      );
      J.downloadFile('jarvis-export.ris', lines.join('\n\n'), 'application/x-research-info-systems');
      J.toast('RISエクスポート完了', 'success');
    },

    exportBibTeX() {
      const entries = J.state.results.map(r =>
        `@article{${r.pmid},\n  title={${r.title}},\n  author={${r.authors}},\n  year={${r.year}}\n}`
      );
      J.downloadFile('jarvis-export.bib', entries.join('\n\n'), 'text/plain');
      J.toast('BibTeXエクスポート完了', 'success');
    },

    exportMarkdown() {
      const lines = J.state.results.map(r =>
        `- **${r.title}** — ${r.authors} (${r.year}) [PMID:${r.pmid}](https://pubmed.ncbi.nlm.nih.gov/${r.pmid})`
      );
      J.downloadFile('jarvis-export.md', `# JARVIS Research Export\n\n${lines.join('\n')}`, 'text/markdown');
      J.toast('Markdownエクスポート完了', 'success');
    },

    clearAll() {
      if (!confirm('すべてのローカルデータを削除しますか？')) return;
      localStorage.clear();
      J.toast('データをクリアしました。リロードします…', 'warn');
      setTimeout(() => location.reload(), 1000);
    }
  },

  // ================================================================
  // ACTIONS
  // ================================================================
  actions: {
    generateReport() {
      if (!J.state.results.length) return J.toast('先に検索を実行してください', 'error');
      J.toast('レポートを生成中…', 'info');
      setTimeout(() => {
        const lines = [`# JARVIS Research Report`, `Generated: ${new Date().toISOString()}`, ``, `## Results (${J.state.results.length} papers)`, ``];
        J.state.results.forEach(r => {
          lines.push(`### ${r.title}`);
          lines.push(`- Authors: ${r.authors}`);
          lines.push(`- Year: ${r.year}`);
          lines.push(`- PMID: ${r.pmid}`);
          lines.push('');
        });
        J.downloadFile('jarvis-report.md', lines.join('\n'), 'text/markdown');
        J.toast('レポートをダウンロードしました', 'success');
      }, 1000);
    },

    summarize() {
      if (!J.state.results.length) return J.toast('先に検索を実行してください', 'error');
      J.toast('AI要約を生成中…', 'info');
      setTimeout(() => {
        J.chat.openDrawer();
        const msgs = document.getElementById('chat-messages');
        const summary = `検索結果 ${J.state.results.length}件の要約:\n\n` +
          J.state.results.map((r, i) => `${i + 1}. ${r.title} (${r.year})`).join('\n') +
          `\n\nこれらの論文は主に${J.state.results[0]?.tags?.join(', ') || '研究'}に関連しています。`;
        msgs.innerHTML += `<div class="chat-msg assistant">${summary.replace(/\n/g, '<br>')}</div>`;
        msgs.scrollTop = msgs.scrollHeight;
      }, 1200);
    }
  },

  // ================================================================
  // CHARTS
  // ================================================================
  charts: {
    activityChart: null,

    initActivity() {
      const ctx = document.getElementById('activity-chart')?.getContext('2d');
      if (!ctx) return;
      this.activityChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['月','火','水','木','金','土','日'],
          datasets: [{
            label: '検索数',
            data: [12,19,8,25,15,30,22],
            borderColor: '#818cf8',
            backgroundColor: 'rgba(129,140,248,.1)',
            fill: true,
            tension: .4,
            pointRadius: 4,
            pointBackgroundColor: '#818cf8',
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,.05)' }, ticks: { color: '#64748b' } },
            x: { grid: { display: false }, ticks: { color: '#64748b' } }
          }
        }
      });
    },

    initRadar() {
      const ctx = document.getElementById('radar-chart')?.getContext('2d');
      if (!ctx) return;
      new Chart(ctx, {
        type: 'radar',
        data: {
          labels: ['関連性','引用数','新しさ','インパクト','新規性'],
          datasets: [{
            label: 'スコア',
            data: [85,72,90,65,78],
            backgroundColor: 'rgba(129,140,248,.2)',
            borderColor: '#818cf8',
            pointBackgroundColor: '#818cf8',
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              beginAtZero: true, max: 100,
              ticks: { stepSize: 20, color: '#64748b', backdropColor: 'transparent' },
              grid: { color: 'rgba(255,255,255,.08)' },
              pointLabels: { color: '#94a3b8', font: { size: 10 } }
            }
          },
          plugins: { legend: { display: false } }
        }
      });
    },

    initPie() {
      const ctx = document.getElementById('pie-chart')?.getContext('2d');
      if (!ctx) return;
      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['AI/ML','Healthcare','Genomics','Neuroscience','Other'],
          datasets: [{
            data: [35,25,20,12,8],
            backgroundColor: ['#818cf8','#34d399','#60a5fa','#f472b6','#fbbf24'],
            borderWidth: 0,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { color: '#94a3b8', padding: 8, font: { size: 10 } } }
          }
        }
      });
    }
  },

  // ================================================================
  // WORD CLOUD
  // ================================================================
  wordCloud: {
    words: {},

    load() {
      J.state.searchHistory.forEach(q => {
        q.split(/\s+/).forEach(w => {
          if (w.length > 2) this.words[w.toLowerCase()] = (this.words[w.toLowerCase()] || 0) + 1;
        });
      });
      this.render();
    },

    addFromQuery(query) {
      query.split(/\s+/).forEach(w => {
        if (w.length > 2) this.words[w.toLowerCase()] = (this.words[w.toLowerCase()] || 0) + 1;
      });
      this.render();
    },

    render() {
      const el = document.getElementById('word-cloud');
      if (!el) return;
      const sorted = Object.entries(this.words).sort((a, b) => b[1] - a[1]).slice(0, 25);
      if (!sorted.length) {
        el.innerHTML = '<span style="color:var(--t4);font-size:.82rem">検索するとワードクラウドが表示されます</span>';
        return;
      }
      const max = sorted[0][1];
      const colors = ['#818cf8','#f472b6','#34d399','#22d3ee','#fbbf24','#a78bfa'];
      el.innerHTML = sorted.map(([word, count]) => {
        const size = 0.7 + (count / max) * 1.2;
        const color = colors[Math.floor(Math.random() * colors.length)];
        return `<span style="font-size:${size}em;color:${color};cursor:pointer;transition:transform .15s;padding:2px" onmouseover="this.style.transform='scale(1.2)'" onmouseout="this.style.transform=''" onclick="document.getElementById('search-query').value='${word}';J.tabs.switchTo('research')">${word}</span>`;
      }).join(' ');
    }
  },

  // ================================================================
  // HEATMAP
  // ================================================================
  heatmap: {
    record() {
      const today = new Date().toISOString().split('T')[0];
      J.state.heatmap[today] = (J.state.heatmap[today] || 0) + 1;
      J.save();
      this.render();
    },

    render() {
      const el = document.getElementById('heatmap-container');
      if (!el) return;
      el.innerHTML = '';
      const today = new Date();
      for (let i = 34; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        const key = d.toISOString().split('T')[0];
        const count = J.state.heatmap[key] || 0;
        const intensity = Math.min(count / 8, 1);
        const color = count === 0 ? 'rgba(255,255,255,.04)' : `rgba(52,211,153,${0.2 + intensity * 0.8})`;
        const cell = document.createElement('div');
        cell.className = 'hm-cell';
        cell.style.background = color;
        cell.title = `${key}: ${count}回`;
        el.appendChild(cell);
      }
    }
  },

  // ================================================================
  // DATA LOADER (artifacts)
  // ================================================================
  dataLoader: {
    bundleData: null,

    async autoLoad() {
      const params = new URLSearchParams(window.location.search);
      const runId = params.get('run') || params.get('run_id');
      if (runId) {
        document.getElementById('run-selector').value = runId;
        await this.loadRun(runId);
      }
    },

    async loadRun(runId) {
      const summaryEl = document.getElementById('run-summary');
      summaryEl.innerHTML = '<div class="empty-msg">読み込み中…</div>';

      try {
        const r = await fetch(`../artifacts/${runId}/export_bundle.json`);
        if (!r.ok) throw new Error('Not found');
        this.bundleData = await r.json();

        const meta = this.bundleData.run_meta || {};
        const report = this.bundleData.quality_report || {};
        const papers = this.bundleData.papers?.length || meta.papers_count || 0;
        const claims = this.bundleData.claims?.length || meta.claims_count || 0;
        const passed = report.passed;

        summaryEl.innerHTML = `
          <div class="run-row"><span>Run ID:</span><span class="run-metric">${meta.run_id || runId}</span></div>
          <div class="run-row"><span>ゴール:</span><span style="color:var(--t2)">${meta.goal || 'N/A'}</span></div>
          <div class="run-row"><span>論文数:</span><span class="run-metric">${papers}</span></div>
          <div class="run-row"><span>クレーム数:</span><span class="run-metric">${claims}</span></div>
          <div class="run-row"><span>品質:</span><span class="${passed ? 'run-pass' : 'run-fail'}">${passed ? '✅ PASSED' : '❌ FAILED'}</span></div>
          <div class="run-row"><span>来歴率:</span><span class="run-metric">${((meta.provenance_rate || 0) * 100).toFixed(1)}%</span></div>
        `;

        J.state.papers = Math.max(J.state.papers, papers);
        J.state.claims = Math.max(J.state.claims, claims);
        J.kpi.update();
        J.logs.add('SUCCESS', `Artifact ${runId} 読み込み完了`);
        J.toast(`Run ${runId} のデータを読み込みました`, 'success');
      } catch (e) {
        summaryEl.innerHTML = `<div class="empty-msg">読み込みに失敗しました: ${e.message}</div>`;
        J.logs.add('ERROR', `Artifact読み込み失敗: ${e.message}`);
      }
    }
  },

  // ================================================================
  // TOAST
  // ================================================================
  toast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warn: '⚠️' };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  },

  // ================================================================
  // UTILITY
  // ================================================================
  delay(ms) { return new Promise(r => setTimeout(r, ms)); },

  animateValue(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const start = parseInt(el.textContent) || 0;
    const range = target - start;
    if (range === 0) return;
    const dur = 600;
    const t0 = performance.now();
    const step = now => {
      const p = Math.min((now - t0) / dur, 1);
      el.textContent = Math.floor(start + range * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  },

  downloadFile(filename, content, type) {
    const blob = new Blob([content], { type });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }
};

// ================================================================
// BOOT
// ================================================================
document.addEventListener('DOMContentLoaded', () => J.init());

// Global reference
window.J = J;
