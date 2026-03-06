const translations = {
  en: {
    'nav.chat': 'Chat',
    'nav.pipeline': 'Pipeline',
    'nav.monitor': 'Monitor',
    'nav.dashboard': 'Dashboard',
    'nav.graph': 'Graph',
    'nav.memory': 'Memory',
    'nav.search': 'Search',
    'sidebar.newSession': 'New Session',
    'sidebar.sessionHistory': 'Session History',
    'sidebar.systemStatus': 'System Status',
    'sidebar.model': 'Model',
    'sidebar.mcpServers': 'MCP Servers',
    'sidebar.skills': 'Skills',
    'chat.placeholder': 'Ask JARVIS anything...',
    'chat.send': 'Send',
    'chat.export': 'Export Chat',
    'chat.newSession': 'New Session',
    'chat.thinking': 'Thinking...',
    'pipeline.title': 'Research Pipeline',
    'pipeline.query': 'Search query (e.g. CRISPR gene therapy)',
    'pipeline.run': 'Run Pipeline',
    'pipeline.maxResults': 'Max Results',
    'pipeline.history': 'Pipeline History',
    'pipeline.running': 'Running...',
    'pipeline.complete': 'Complete',
    'pipeline.results': 'Results',
    'pipeline.refresh': 'Refresh',
    'monitor.title': 'System Monitor',
    'monitor.status': 'Status',
    'monitor.health': 'Health Check',
    'monitor.refresh': 'Refresh',
    'dashboard.title': 'Dashboard',
    'dashboard.totalPapers': 'Total Papers',
    'dashboard.totalSessions': 'Total Sessions',
    'dashboard.digestHistory': 'Digest History',
    'dashboard.systemHealth': 'System Health',
    'dashboard.readingList': 'Reading List',
    'memory.title': 'Memory',
    'memory.facts': 'Facts',
    'memory.preferences': 'Preferences',
    'memory.context': 'Context',
    'memory.addFact': 'Add Fact',
    'memory.addPreference': 'Add Preference',
    'memory.key': 'Key',
    'memory.value': 'Value',
    'memory.save': 'Save',
    'memory.delete': 'Delete',
    'search.title': 'Paper Search',
    'search.placeholder': 'Search query (e.g. CRISPR gene therapy)',
    'search.button': 'Search',
    'search.searchType': 'Search Type',
    'search.sources': 'Sources',
    'search.maxResults': 'Max Results',
    'search.yearFrom': 'Year From',
    'search.yearTo': 'Year To',
    'search.noResults': 'No papers found. Try different keywords.',
    'search.found': 'Found',
    'search.papersFor': 'papers for',
    'auth.title': 'JARVIS Authentication',
    'auth.prompt': 'Enter your auth token to continue',
    'auth.placeholder': 'Paste auth token',
    'auth.submit': 'Authenticate',
    'auth.hint': 'Token is displayed in the server console on startup.',
    'auth.invalid': 'Invalid token',
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.close': 'Close',
    'common.unknown': 'Unknown',
    'common.untitled': 'Untitled'
  },
  ja: {
    'nav.chat': 'チャット',
    'nav.pipeline': 'パイプライン',
    'nav.monitor': 'モニター',
    'nav.dashboard': 'ダッシュボード',
    'nav.graph': 'グラフ',
    'nav.memory': 'メモリ',
    'nav.search': '検索',
    'sidebar.newSession': '新規セッション',
    'sidebar.sessionHistory': 'セッション履歴',
    'sidebar.systemStatus': 'システム状態',
    'sidebar.model': 'モデル',
    'sidebar.mcpServers': 'MCP サーバー',
    'sidebar.skills': 'スキル',
    'chat.placeholder': 'JARVISに何でも聞いてください...',
    'chat.send': '送信',
    'chat.export': 'チャット出力',
    'chat.newSession': '新規セッション',
    'chat.thinking': '考え中...',
    'pipeline.title': '研究パイプライン',
    'pipeline.query': '検索クエリ (例: CRISPR遺伝子治療)',
    'pipeline.run': 'パイプライン実行',
    'pipeline.maxResults': '最大件数',
    'pipeline.history': 'パイプライン履歴',
    'pipeline.running': '実行中...',
    'pipeline.complete': '完了',
    'pipeline.results': '結果',
    'pipeline.refresh': '更新',
    'monitor.title': 'システムモニター',
    'monitor.status': 'ステータス',
    'monitor.health': 'ヘルスチェック',
    'monitor.refresh': '更新',
    'dashboard.title': 'ダッシュボード',
    'dashboard.totalPapers': '論文数',
    'dashboard.totalSessions': 'セッション数',
    'dashboard.digestHistory': 'ダイジェスト履歴',
    'dashboard.systemHealth': 'システム状態',
    'dashboard.readingList': 'リーディングリスト',
    'memory.title': 'メモリ',
    'memory.facts': 'ファクト',
    'memory.preferences': '設定',
    'memory.context': 'コンテキスト',
    'memory.addFact': 'ファクト追加',
    'memory.addPreference': '設定追加',
    'memory.key': 'キー',
    'memory.value': '値',
    'memory.save': '保存',
    'memory.delete': '削除',
    'search.title': '論文検索',
    'search.placeholder': '検索クエリ (例: CRISPR遺伝子治療)',
    'search.button': '検索',
    'search.searchType': '検索タイプ',
    'search.sources': 'ソース',
    'search.maxResults': '最大件数',
    'search.yearFrom': '開始年',
    'search.yearTo': '終了年',
    'search.noResults': '論文が見つかりませんでした。別のキーワードをお試しください。',
    'search.found': '件の論文が見つかりました',
    'search.papersFor': '',
    'auth.title': 'JARVIS 認証',
    'auth.prompt': '認証トークンを入力してください',
    'auth.placeholder': '認証トークンを貼り付け',
    'auth.submit': '認証',
    'auth.hint': 'トークンはサーバー起動時のコンソールに表示されます。',
    'auth.invalid': 'トークンが無効です',
    'common.loading': '読み込み中...',
    'common.error': 'エラー',
    'common.save': '保存',
    'common.cancel': 'キャンセル',
    'common.delete': '削除',
    'common.close': '閉じる',
    'common.unknown': '不明',
    'common.untitled': '無題'
  }
};

let currentLang = localStorage.getItem('jarvis-lang') || 'en';

export function t(key) {
  return translations[currentLang]?.[key] || translations.en?.[key] || key;
}

export function getLang() {
  return currentLang;
}

export function setLang(lang) {
  if (!translations[lang]) return;
  currentLang = lang;
  localStorage.setItem('jarvis-lang', lang);
  document.documentElement.setAttribute('lang', lang);
  applyTranslations();
}

export function toggleLang() {
  setLang(currentLang === 'en' ? 'ja' : 'en');
}

export function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach((element) => {
    const key = element.getAttribute('data-i18n');
    const translated = t(key);
    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
      element.placeholder = translated;
    } else {
      element.textContent = translated;
    }
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach((element) => {
    element.placeholder = t(element.getAttribute('data-i18n-placeholder'));
  });

  window.dispatchEvent(new CustomEvent('lang-changed', { detail: { lang: currentLang } }));
}

export function init() {
  document.documentElement.setAttribute('lang', currentLang);
  applyTranslations();
}


