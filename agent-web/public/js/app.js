import { getLang, init as initI18n, t, toggleLang } from './modules/i18n.js';
import { initParticles } from './modules/utils.js';
import { connect as wsConnect, on as wsOn } from './modules/ws-client.js';
import { init as initKeybinds } from './modules/keybinds.js';

const moduleCache = {};
let activeTab = null;

function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.register('/sw.js')
    .then((registration) => console.log('[SW] Registered:', registration.scope))
    .catch((error) => console.warn('[SW] Registration failed:', error));
}

function setupWebSocketStatus() {
  wsOn('connected', () => {
    const dot = document.getElementById('ws-status');
    if (dot) {
      dot.className = 'ws-dot connected';
      dot.title = 'WebSocket connected';
    }
  });
  wsOn('disconnected', () => {
    const dot = document.getElementById('ws-status');
    if (dot) {
      dot.className = 'ws-dot disconnected';
      dot.title = 'WebSocket disconnected';
    }
  });
}

async function checkAuth() {
  try {
    const response = await fetch('/api/auth/status');
    const data = await response.json();
    if (data.authenticated) {
      document.getElementById('login-overlay')?.classList.add('hidden');
      return true;
    }
  } catch {
  }

  document.getElementById('login-overlay')?.classList.remove('hidden');

  return new Promise((resolve) => {
    const form = document.getElementById('login-form');
    const tokenInput = document.getElementById('login-token');
    const errorElement = document.getElementById('login-error');
    if (!form || !tokenInput || !errorElement) {
      resolve(false);
      return;
    }

    const handler = async (event) => {
      event.preventDefault();
      errorElement.style.display = 'none';
      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: tokenInput.value }),
        });
        if (response.ok) {
          form.removeEventListener('submit', handler);
          document.getElementById('login-overlay')?.classList.add('hidden');
          resolve(true);
          return;
        }
        errorElement.style.display = 'block';
        errorElement.textContent = t('auth.invalid');
      } catch (error) {
        errorElement.style.display = 'block';
        errorElement.textContent = error.message;
      }
    };

    form.addEventListener('submit', handler);
  });
}

function setTheme(theme) {
  const nextTheme = theme === 'light' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', nextTheme);
  try {
    localStorage.setItem('jarvis-theme', nextTheme);
  } catch {
  }
  const themeIcon = document.getElementById('themeToggle')?.querySelector('.theme-icon');
  if (themeIcon) themeIcon.textContent = nextTheme === 'light' ? '☀️' : '🌙';
}

function setupThemeToggle() {
  let savedTheme = 'dark';
  try {
    savedTheme = localStorage.getItem('jarvis-theme') || 'dark';
  } catch {
    savedTheme = 'dark';
  }
  setTheme(savedTheme);
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    setTheme(current === 'light' ? 'dark' : 'light');
  });
}

function setupSidebarToggle() {
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar') || document.getElementById('sidebar');
  if (!sidebarToggle || !sidebar) return;

  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  document.querySelectorAll('.nav-btn, .tab-btn').forEach((button) => {
    button.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.remove('open');
      }
    });
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      sidebar.classList.remove('open');
    }
  });
}

function setLangLabel() {
  const label = document.getElementById('langLabel');
  if (label) label.textContent = getLang() === 'en' ? 'EN' : 'JA';
}

function setupLangToggle() {
  setLangLabel();
  document.getElementById('langToggle')?.addEventListener('click', () => {
    toggleLang();
    setLangLabel();
  });
  window.addEventListener('lang-changed', () => {
    setLangLabel();
    const errorElement = document.getElementById('login-error');
    if (errorElement?.textContent === 'Invalid token' || errorElement?.textContent === 'トークンが無効です') {
      errorElement.textContent = t('auth.invalid');
    }
  });
}

function getView(tabName) {
  return document.getElementById(tabName + '-view');
}

function showLoadingSpinner(view) {
  if (!view) return null;
  const spinner = document.createElement('div');
  spinner.className = 'tab-loading';
  spinner.textContent = t('common.loading');
  view.prepend(spinner);
  return spinner;
}

async function activateTab(tabName) {
  if (activeTab && moduleCache[activeTab]?.onDeactivate) {
    await moduleCache[activeTab].onDeactivate();
  }

  document.querySelectorAll('.view').forEach((view) => {
    view.classList.add('hidden');
    view.classList.remove('active');
  });

  const view = getView(tabName);
  if (view) {
    view.classList.remove('hidden');
    view.classList.add('active');
  }

  document.querySelectorAll('.nav-btn').forEach((button) => button.classList.remove('active'));
  document.querySelector('[data-tab="' + tabName + '"]')?.classList.add('active');

  if (!moduleCache[tabName]) {
    const spinner = showLoadingSpinner(view);
    try {
      const mod = await import('./modules/' + tabName + '.js');
      if (mod.init) await mod.init();
      moduleCache[tabName] = mod;
    } catch (error) {
      console.warn('Module ' + tabName + ' not found, skipping:', error.message);
    } finally {
      spinner?.remove();
    }
  }

  if (moduleCache[tabName]?.onActivate) {
    await moduleCache[tabName].onActivate();
  }
  activeTab = tabName;
}

function bindTabNavigation() {
  document.querySelectorAll('.nav-btn').forEach((button) => {
    button.addEventListener('click', () => {
      activateTab(button.dataset.tab).catch((error) => {
        console.warn('Failed to activate tab ' + button.dataset.tab + ':', error.message);
      });
    });
  });
}

async function initialize() {
  initParticles();
  initI18n();
  registerServiceWorker();
  setupWebSocketStatus();
  setupThemeToggle();
  setupSidebarToggle();
  setupLangToggle();
  bindTabNavigation();
  initKeybinds();
  wsConnect('default');
  await activateTab('chat');
}

await checkAuth();
await initialize();

