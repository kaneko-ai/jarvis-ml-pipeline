import { t } from './i18n.js';
import { escapeHtml, fetchPipelineResultFile } from './utils.js';

const searchState = {
  bound: false,
};

function normalizeSearchAuthors(rawAuthors) {
  if (Array.isArray(rawAuthors)) return rawAuthors.join(', ');
  if (rawAuthors === null || rawAuthors === undefined) return 'Unknown authors';
  const text = String(rawAuthors).trim();
  return text || 'Unknown authors';
}

function getSearchAbstractExcerpt(rawAbstract) {
  const text = String(rawAbstract || '').trim();
  if (!text) return '';
  return text.length > 250 ? `${text.slice(0, 250)}...` : text;
}

function renderTagsForCard(section, tags) {
  const list = section.querySelector('.paper-tags-list');
  if (!list) return;

  list.innerHTML = (tags || []).map((tItem) => {
    const safeTag = escapeHtml(tItem.tag || '');
    const safeColor = escapeHtml(tItem.color || '#d4af37');
    return `<span class="paper-tag" style="background:${safeColor}20;border-color:${safeColor};color:${safeColor}">
      ${safeTag}
      <button class="tag-remove-btn" data-tag="${safeTag}" data-paper-id="${escapeHtml(section.dataset.paperId || '')}">&times;</button>
    </span>`;
  }).join('');

  list.querySelectorAll('.tag-remove-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const paperId = btn.dataset.paperId;
      const tag = btn.dataset.tag;
      if (!paperId || !tag) return;
      await fetch(`/api/papers/${paperId}/tags/${encodeURIComponent(tag)}`, { method: 'DELETE' });
      btn.closest('.paper-tag')?.remove();
    });
  });
}

function renderSearchResults(papers, container, statusElement, query) {
  const results = Array.isArray(papers) ? papers : [];
  if (statusElement) {
    statusElement.innerHTML = `${t('search.found')} <strong>${results.length}</strong> ${t('search.papersFor')} "<em>${escapeHtml(query || '')}</em>"`;
  }

  if (!container) return;
  if (!results.length) {
    container.innerHTML = `<p class="no-results">${t('search.noResults')}</p>`;
    document.getElementById('compare-bar')?.classList.add('hidden');
    return;
  }

  container.innerHTML = results.map((paper, index) => {
    const score = Number.isFinite(Number(paper?.score)) ? Number(paper.score).toFixed(1) : '-';
    const title = escapeHtml(paper?.title ? String(paper.title) : t('common.untitled'));
    const authors = escapeHtml(normalizeSearchAuthors(paper?.authors));
    const journalMeta = escapeHtml([paper?.journal, paper?.year].filter(Boolean).join(', '));
    const abstract = getSearchAbstractExcerpt(paper?.abstract);
    const links = [];

    if (paper?.doi) {
      links.push(`<a href="https://doi.org/${encodeURIComponent(String(paper.doi).trim())}" class="cite-link" target="_blank" rel="noreferrer noopener">DOI</a>`);
    }
    if (paper?.pmid) {
      links.push(`<a href="https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(String(paper.pmid).trim())}" class="cite-link" target="_blank" rel="noreferrer noopener">PMID</a>`);
    }
    if (paper?.source) {
      links.push(`<span class="paper-source">${escapeHtml(String(paper.source))}</span>`);
    }

    return '<div class="paper-card" style="animation-delay: ' + String(index * 60) + 'ms">' +
      `<div class="paper-score">${escapeHtml(score)}</div>` +
      '<div class="paper-content">' +
        `<h4 class="paper-title">${title}</h4>` +
        `<p class="paper-authors">${authors}</p>` +
        `<p class="paper-journal">${journalMeta}</p>` +
        (abstract ? `<p class="paper-abstract">${escapeHtml(abstract)}</p>` : '') +
        `<div class="paper-links">${links.join('')}</div>` +
        `<div class="paper-compare-checkbox">
          <label><input type="checkbox" class="compare-check" data-paper-id="${paper?.id || ''}" /> Compare</label>
        </div>` +
        `<div class="paper-tags-section" data-paper-id="${paper?.id ? escapeHtml(String(paper.id)) : ''}">
          <div class="paper-tags-list"></div>
          ${paper?.id ? `
            <div class="paper-tag-add">
              <input type="text" class="tag-input" placeholder="Add tag..."
                maxlength="30">
              <input type="color" class="tag-color-picker" value="#d4af37">
              <button class="tag-add-btn" title="Add tag">+</button>
            </div>
          ` : ''}
        </div>` +
      '</div>' +
    '</div>';
  }).join('');

  container.querySelectorAll('.tag-add-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const section = btn.closest('.paper-tags-section');
      const paperId = section?.dataset.paperId;
      if (!paperId) return;
      const input = section.querySelector('.tag-input');
      const colorPicker = section.querySelector('.tag-color-picker');
      const tag = input?.value?.trim();
      if (!tag) return;
      try {
        const res = await fetch(`/api/papers/${paperId}/tags`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tag, color: colorPicker?.value }),
        });
        const data = await res.json();
        if (res.ok) {
          input.value = '';
          renderTagsForCard(section, data.tags);
        }
      } catch (e) {
        console.warn('Tag add failed:', e);
      }
    });
  });

  container.querySelectorAll('.paper-tags-section[data-paper-id]').forEach(async (section) => {
    const paperId = section.dataset.paperId;
    if (!paperId) return;
    try {
      const res = await fetch(`/api/papers/${paperId}/tags`);
      const tags = await res.json();
      renderTagsForCard(section, tags);
    } catch {
    }
  });

  let compareBar = document.getElementById('compare-bar');
  if (!compareBar) {
    compareBar = document.createElement('div');
    compareBar.id = 'compare-bar';
    compareBar.className = 'compare-bar hidden';
    compareBar.innerHTML = '<span id="compare-count">0 selected</span> <button id="compare-btn" class="btn-gold">Compare Selected</button>';
    container.parentElement?.appendChild(compareBar);
  }

  function updateCompareBar() {
    const checked = container.querySelectorAll('.compare-check:checked');
    const bar = document.getElementById('compare-bar');
    const countEl = document.getElementById('compare-count');
    if (bar) bar.classList.toggle('hidden', checked.length < 2);
    if (countEl) countEl.textContent = `${checked.length} selected`;
  }

  container.querySelectorAll('.compare-check').forEach((checkbox) => {
    checkbox.addEventListener('change', updateCompareBar);
  });

  const compareButton = document.getElementById('compare-btn');
  if (compareButton) {
    compareButton.onclick = async () => {
      const ids = Array.from(container.querySelectorAll('.compare-check:checked'))
        .map((checkbox) => Number(checkbox.dataset.paperId))
        .filter(Boolean);
      if (ids.length < 2) return;
      try {
        const res = await fetch('/api/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ paperIds: ids }),
        });
        const data = await res.json();
        if (data.markdown) {
          const win = window.open('', '_blank');
          if (win) {
            win.document.write(`<pre style="font-family:monospace;padding:2rem;">${data.markdown.replace(/</g, '&lt;')}</pre>`);
            win.document.title = 'Paper Comparison';
          }
        }
      } catch (e) {
        console.warn('Compare failed:', e);
      }
    };
  }

  updateCompareBar();
}

async function handleSearchSubmit(event) {
  event.preventDefault();

  const queryInput = document.getElementById('search-query');
  const limitInput = document.getElementById('search-limit');
  const yearFromInput = document.getElementById('search-year-from');
  const yearToInput = document.getElementById('search-year-to');
  const statusElement = document.getElementById('search-status');
  const resultsElement = document.getElementById('search-results');
  const searchType = document.querySelector('input[name="searchType"]:checked')?.value || 'keyword';
  const sources = Array.from(document.querySelectorAll('input[name="source"]:checked')).map((checkbox) => checkbox.value);
  const query = queryInput ? queryInput.value.trim() : '';
  const limit = limitInput ? limitInput.value : '10';
  const yearFrom = yearFromInput ? yearFromInput.value : '';
  const yearTo = yearToInput ? yearToInput.value : '';

  if (!query) {
    if (statusElement) statusElement.innerHTML = '<span class="health-err">Query is required.</span>';
    return;
  }

  if (searchType !== 'semantic' && !sources.length) {
    if (statusElement) statusElement.innerHTML = '<span class="health-err">Select at least one source.</span>';
    return;
  }

  if (searchType === 'semantic') {
    if (statusElement) statusElement.innerHTML = '<span class="activity-dot running"></span> Semantic searching (ChromaDB)...';
    if (resultsElement) resultsElement.innerHTML = '';

    try {
      const params = new URLSearchParams({ query, limit: String(limit) });
      const response = await fetch(`/api/semantic-search?${params.toString()}`);
      const data = await response.json();

      if (data.error) {
        console.warn('[SemanticSearch] Server note:', data.error);
      }

      const papers = (data.results || []).map((result) => ({
        title: result.title || result.text?.slice(0, 80) || 'Untitled',
        authors: result.authors || 'Unknown',
        year: result.year || '',
        doi: result.doi || '',
        source: result.source || 'chromadb',
        score: result.similarity != null ? (result.similarity * 100).toFixed(1) : '-',
        abstract: result.text || '',
      }));

      renderSearchResults(papers, resultsElement, statusElement, query);
      if (data.error && statusElement) {
        statusElement.innerHTML += ` <span class="health-warn">(${escapeHtml(data.hint || data.error)})</span>`;
      }
    } catch (error) {
      if (statusElement) {
        statusElement.innerHTML = `<span class="health-err">Error: ${escapeHtml(error.message || 'unknown')}</span>`;
      }
    }

    return;
  }

  if (statusElement) statusElement.innerHTML = '<span class="activity-dot running"></span> Searching...';
  if (resultsElement) resultsElement.innerHTML = '';

  try {
    const params = new URLSearchParams({
      query,
      limit: String(limit),
      sources: sources.join(','),
    });
    if (yearFrom) params.set('yearFrom', yearFrom);
    if (yearTo) params.set('yearTo', yearTo);

    const response = await fetch(`/api/pipeline/run?${params.toString()}`, {
      headers: { Accept: 'text/event-stream, application/json' },
    });

    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }

    let papers = [];
    let finalPayload = null;
    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('text/event-stream')) {
      if (!response.body) {
        throw new Error('Readable stream is not available.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;

        buffer += decoder.decode(chunk.value, { stream: true });
        const lines = buffer.split(/\r?\n/);
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'papers' || Array.isArray(data.papers)) {
              papers = data.papers || data.results || [];
            }
            if (data.results && Array.isArray(data.results.papers)) {
              papers = data.results.papers;
            }
            if (data.type === 'step' || data.step) {
              if (statusElement) {
                statusElement.innerHTML = `<span class="activity-dot running"></span> ${escapeHtml(data.step || data.message || 'Processing...')}`;
              }
            }
            if (data.type === 'complete' || data.type === 'done' || data.done) {
              finalPayload = data;
              if (Array.isArray(data.papers)) {
                papers = data.papers;
              } else if (data.results && Array.isArray(data.results.papers)) {
                papers = data.results.papers;
              }
            }
          } catch {
          }
        }
      }

      if (!papers.length && finalPayload?.file) {
        try {
          const resultFile = await fetchPipelineResultFile(finalPayload.file);
          papers = Array.isArray(resultFile.papers) ? resultFile.papers : [];
        } catch {
        }
      }
    } else {
      const data = await response.json();
      finalPayload = data;
      if (Array.isArray(data.papers)) {
        papers = data.papers;
      } else if (data.results && Array.isArray(data.results.papers)) {
        papers = data.results.papers;
      } else if (Array.isArray(data.results)) {
        papers = data.results;
      }

      if (!papers.length && data.file) {
        try {
          const resultFile = await fetchPipelineResultFile(data.file);
          papers = Array.isArray(resultFile.papers) ? resultFile.papers : [];
        } catch {
        }
      }
    }

    renderSearchResults(papers, resultsElement, statusElement, query);
  } catch (error) {
    if (statusElement) {
      statusElement.innerHTML = `<span class="health-err">Error: ${escapeHtml(error.message || 'unknown')}</span>`;
    }
  }
}

export async function init() {
  if (searchState.bound) return;
  searchState.bound = true;
  document.getElementById('search-form')?.addEventListener('submit', handleSearchSubmit);
}

export async function onActivate() {
  document.getElementById('search-query')?.focus();
}


