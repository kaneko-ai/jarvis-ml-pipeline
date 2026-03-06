const shortcuts = [
  { key: 'k', ctrl: true, action: 'focus-chat', desc: 'Focus chat input' },
  { key: '1', ctrl: true, action: 'tab-chat', desc: 'Switch to Chat' },
  { key: '2', ctrl: true, action: 'tab-pipeline', desc: 'Switch to Pipeline' },
  { key: '3', ctrl: true, action: 'tab-monitor', desc: 'Switch to Monitor' },
  { key: '4', ctrl: true, action: 'tab-dashboard', desc: 'Switch to Dashboard' },
  { key: '5', ctrl: true, action: 'tab-memory', desc: 'Switch to Memory' },
  { key: '6', ctrl: true, action: 'tab-search', desc: 'Switch to Search' },
  { key: 'n', ctrl: true, shift: true, action: 'new-session', desc: 'New chat session' },
  { key: 'l', ctrl: true, shift: true, action: 'toggle-lang', desc: 'Toggle language' },
  { key: 't', ctrl: true, shift: true, action: 'toggle-theme', desc: 'Toggle theme' },
  { key: '/', ctrl: false, action: 'focus-search', desc: 'Focus search (when not in input)' },
  { key: '?', ctrl: false, shift: true, action: 'show-help', desc: 'Show shortcuts help' },
];

let helpOverlayVisible = false;

export function init() {
  document.addEventListener('keydown', (e) => {
    const target = e.target;
    const tag = target?.tagName;
    const inInput = tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable;

    for (const s of shortcuts) {
      const ctrlMatch = s.ctrl ? (e.ctrlKey || e.metaKey) : !(e.ctrlKey || e.metaKey);
      const shiftMatch = s.shift ? e.shiftKey : !s.shift ? true : false;
      if (!s.ctrl && inInput) continue;

      if (e.key.toLowerCase() === s.key && ctrlMatch && shiftMatch) {
        e.preventDefault();
        executeAction(s.action);
        return;
      }
    }
  });
}

function executeAction(action) {
  switch (action) {
    case 'focus-chat': {
      document.querySelector('[data-tab="chat"]')?.click();
      setTimeout(() => {
        document.getElementById('user-input')?.focus()
          || document.getElementById('chat-input')?.focus();
      }, 100);
      break;
    }
    case 'tab-chat':
    case 'tab-pipeline':
    case 'tab-monitor':
    case 'tab-dashboard':
    case 'tab-memory':
    case 'tab-search': {
      const tab = action.replace('tab-', '');
      document.querySelector(`[data-tab="${tab}"]`)?.click();
      break;
    }
    case 'new-session': {
      document.getElementById('new-session-btn')?.click()
        || document.querySelector('.new-session')?.click();
      break;
    }
    case 'toggle-lang': {
      document.getElementById('langToggle')?.click();
      break;
    }
    case 'toggle-theme': {
      document.getElementById('themeToggle')?.click();
      break;
    }
    case 'focus-search': {
      document.querySelector('[data-tab="search"]')?.click();
      setTimeout(() => {
        document.getElementById('search-query')?.focus();
      }, 100);
      break;
    }
    case 'show-help': {
      toggleHelp();
      break;
    }
  }
}

function toggleHelp() {
  let overlay = document.getElementById('keybinds-help');
  if (overlay) {
    overlay.classList.toggle('hidden');
    helpOverlayVisible = !helpOverlayVisible;
    return;
  }

  overlay = document.createElement('div');
  overlay.id = 'keybinds-help';
  overlay.className = 'keybinds-overlay';
  overlay.innerHTML = `
    <div class="keybinds-card">
      <h3>Keyboard Shortcuts</h3>
      <div class="keybinds-list">
        ${shortcuts.map((s) => `
          <div class="keybind-row">
            <kbd>${s.ctrl ? 'Ctrl+' : ''}${s.shift ? 'Shift+' : ''}${s.key.toUpperCase()}</kbd>
            <span>${s.desc}</span>
          </div>
        `).join('')}
      </div>
      <p class="keybinds-close-hint">Press <kbd>?</kbd> or <kbd>Esc</kbd> to close</p>
    </div>
  `;
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.classList.add('hidden');
      helpOverlayVisible = false;
    }
  });
  document.body.appendChild(overlay);
  helpOverlayVisible = true;

  document.addEventListener('keydown', function escHandler(e) {
    if (e.key === 'Escape' && helpOverlayVisible) {
      overlay.classList.add('hidden');
      helpOverlayVisible = false;
    }
  });
}
