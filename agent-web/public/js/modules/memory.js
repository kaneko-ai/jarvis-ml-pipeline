import { fetchJson, showToast } from './utils.js';

const memoryState = {
  bindingsApplied: false,
};

function renderFactsList(facts) {
  const list = document.getElementById('facts-list');
  if (!list) return;

  if (!Array.isArray(facts) || !facts.length) {
    list.innerHTML = '<li class="pipeline-empty-row">No facts yet.</li>';
    return;
  }

  list.innerHTML = facts.map((fact) => {
    const key = String(fact?.key || '').trim();
    const value = String(fact?.value || '').trim();
    const category = String(fact?.category || 'general').trim() || 'general';
    const encodedKey = encodeURIComponent(key);
    return '<li class="memory-list-item">' +
      '<div class="memory-item-main">' +
        `<div class="memory-item-key">${key || '-'}</div>` +
        `<div class="memory-item-value">${value || '-'}</div>` +
        `<div class="memory-item-meta">Category: ${category}</div>` +
      '</div>' +
      `<button type="button" class="btn-gold memory-delete-btn" data-delete-fact-key="${encodedKey}">🗑️</button>` +
      '</li>';
  }).join('');
}

function renderPreferencesList(preferences) {
  const list = document.getElementById('prefs-list');
  if (!list) return;

  const entries = Object.entries(preferences || {});
  if (!entries.length) {
    list.innerHTML = '<li class="pipeline-empty-row">No preferences yet.</li>';
    return;
  }

  list.innerHTML = entries.map(([key, value]) => {
    return '<li class="memory-list-item">' +
      '<div class="memory-item-main">' +
        `<div class="memory-item-key">${String(key || '').trim() || '-'}</div>` +
        `<div class="memory-item-value">${String(value || '').trim() || '-'}</div>` +
      '</div>' +
      '</li>';
  }).join('');
}

function renderMemoryContext(contextText) {
  const context = document.getElementById('memory-context');
  if (!context) return;
  const safeContext = String(contextText || '').trim();
  context.textContent = safeContext || 'No context available.';
}

async function fetchMemoryFacts() {
  try {
    return await fetchJson('/api/memory/facts');
  } catch (error) {
    showToast(`Failed to load memory facts: ${error.message || 'unknown'}`);
    return [];
  }
}

async function fetchMemoryPreferences() {
  try {
    return await fetchJson('/api/memory/preferences');
  } catch (error) {
    showToast(`Failed to load preferences: ${error.message || 'unknown'}`);
    return {};
  }
}

async function fetchMemoryContext() {
  try {
    const payload = await fetchJson('/api/memory/context');
    return payload?.context || '';
  } catch (error) {
    showToast(`Failed to load memory context: ${error.message || 'unknown'}`);
    return '';
  }
}

export async function loadMemoryPanel() {
  const facts = document.getElementById('facts-list');
  const prefs = document.getElementById('prefs-list');
  if (facts) facts.innerHTML = '<li class="pipeline-empty-row">Loading facts...</li>';
  if (prefs) prefs.innerHTML = '<li class="pipeline-empty-row">Loading preferences...</li>';
  renderMemoryContext('Loading memory context...');

  const [factsData, prefsData, contextData] = await Promise.all([
    fetchMemoryFacts(),
    fetchMemoryPreferences(),
    fetchMemoryContext(),
  ]);

  renderFactsList(factsData);
  renderPreferencesList(prefsData);
  renderMemoryContext(contextData);
}

async function deleteMemoryFactByKey(key) {
  try {
    await fetchJson(`/api/memory/facts/${encodeURIComponent(key)}`, { method: 'DELETE' });
    return true;
  } catch (error) {
    showToast(`Failed to delete fact: ${error.message || 'unknown'}`);
    return false;
  }
}

async function addMemoryFact(payload) {
  try {
    await fetchJson('/api/memory/facts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return true;
  } catch (error) {
    showToast(`Failed to add fact: ${error.message || 'unknown'}`);
    return false;
  }
}

async function addMemoryPreference(payload) {
  try {
    await fetchJson('/api/memory/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return true;
  } catch (error) {
    showToast(`Failed to add preference: ${error.message || 'unknown'}`);
    return false;
  }
}

async function handleAddFactSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const keyInput = form.querySelector('[name="key"]');
  const valueInput = form.querySelector('[name="value"]');
  const categoryInput = form.querySelector('[name="category"]');
  const payload = {
    key: keyInput ? keyInput.value.trim() : '',
    value: valueInput ? valueInput.value.trim() : '',
    category: categoryInput ? categoryInput.value.trim() : '',
  };

  if (!payload.key || !payload.value) {
    showToast('Fact key and value are required.');
    return;
  }

  const ok = await addMemoryFact(payload);
  if (!ok) return;
  form.reset();
  showToast('Fact added.');
  await loadMemoryPanel();
}

async function handleAddPreferenceSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const keyInput = form.querySelector('[name="key"]');
  const valueInput = form.querySelector('[name="value"]');
  const payload = {
    key: keyInput ? keyInput.value.trim() : '',
    value: valueInput ? valueInput.value.trim() : '',
  };

  if (!payload.key || !payload.value) {
    showToast('Preference key and value are required.');
    return;
  }

  const ok = await addMemoryPreference(payload);
  if (!ok) return;
  form.reset();
  showToast('Preference added.');
  await loadMemoryPanel();
}

function bindMemoryPanelEvents() {
  if (memoryState.bindingsApplied) return;
  memoryState.bindingsApplied = true;

  const factsList = document.getElementById('facts-list');
  if (factsList) {
    factsList.addEventListener('click', async (event) => {
      const button = event.target.closest('[data-delete-fact-key]');
      if (!button) return;
      const ok = await deleteMemoryFactByKey(decodeURIComponent(button.getAttribute('data-delete-fact-key') || ''));
      if (!ok) return;
      showToast('Fact deleted.');
      await loadMemoryPanel();
    });
  }

  document.getElementById('add-fact-form')?.addEventListener('submit', handleAddFactSubmit);
  document.getElementById('add-pref-form')?.addEventListener('submit', handleAddPreferenceSubmit);
}

export async function init() {
  bindMemoryPanelEvents();
}

export async function onActivate() {
  await loadMemoryPanel();
}
