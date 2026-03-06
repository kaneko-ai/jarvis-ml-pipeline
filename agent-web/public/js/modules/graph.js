/* global d3 */

let svg;
let simulation;
let container;
let currentNodes = [];
let currentEdges = [];

const colorBySource = {
  pubmed: '#4caf50',
  semantic_scholar: '#2196f3',
  openalex: '#ff9800',
  'bibtex-import': '#9c27b0',
  'ris-import': '#e91e63',
  digest: '#d4af37',
  unknown: '#607d8b',
};

function getColor(source) {
  const key = (source || 'unknown').toLowerCase().replace(/\s+/g, '_');
  return colorBySource[key] || colorBySource.unknown;
}

function getRadius(score) {
  if (!score || score <= 0) return 5;
  return Math.min(4 + score * 1.5, 18);
}

async function fetchGraph(keyword, limit) {
  const params = new URLSearchParams();
  if (keyword) params.set('keyword', keyword);
  params.set('limit', String(limit || 80));
  const res = await fetch('/api/papers/graph?' + params);
  return res.json();
}

async function populateKeywordFilter() {
  try {
    const res = await fetch('/api/papers/stats');
    const stats = await res.json();
    const select = document.getElementById('graph-keyword-filter');
    if (!select) return;

    select.innerHTML = '<option value="">All Keywords</option>';
    for (const kw of Object.keys(stats.byKeyword || {}).sort()) {
      const opt = document.createElement('option');
      opt.value = kw;
      opt.textContent = kw + ' (' + stats.byKeyword[kw] + ')';
      select.appendChild(opt);
    }
  } catch (e) {
    console.warn('[Graph] Failed to load keywords:', e.message);
  }
}

function normalizeEdgeRef(value) {
  if (value && typeof value === 'object') {
    return value.id;
  }
  return value;
}

function renderGraph(data) {
  currentNodes = (data.nodes || []).map((n) => ({ ...n }));
  currentEdges = (data.edges || []).map((e) => ({
    source: normalizeEdgeRef(e.source),
    target: normalizeEdgeRef(e.target),
    weight: e.weight,
  }));

  const svgEl = document.getElementById('graph-svg');
  if (!svgEl) return;

  const containerEl = document.getElementById('graph-container');
  const width = containerEl?.clientWidth || 800;
  const height = containerEl?.clientHeight || 500;

  d3.select(svgEl).selectAll('*').remove();

  svg = d3.select(svgEl)
    .attr('width', width)
    .attr('height', height);

  const zoom = d3.zoom()
    .scaleExtent([0.2, 5])
    .on('zoom', (event) => {
      container.attr('transform', event.transform);
    });
  svg.call(zoom);

  container = svg.append('g');

  const nodeMap = new Map(currentNodes.map((n) => [n.id, n]));
  const validEdges = currentEdges.filter(
    (e) => nodeMap.has(e.source) && nodeMap.has(e.target)
  );
  const simulationEdges = validEdges.map((e) => ({ ...e }));

  simulation = d3.forceSimulation(currentNodes)
    .force('link', d3.forceLink(simulationEdges).id((d) => d.id).distance(80).strength((d) => d.weight * 0.15))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius((d) => getRadius(d.score) + 2));

  const link = container.append('g')
    .selectAll('line')
    .data(simulationEdges)
    .enter()
    .append('line')
    .attr('class', 'graph-edge')
    .attr('stroke-width', (d) => Math.max(0.5, d.weight * 0.4));

  const node = container.append('g')
    .selectAll('circle')
    .data(currentNodes)
    .enter()
    .append('circle')
    .attr('class', 'graph-node')
    .attr('r', (d) => getRadius(d.score))
    .attr('fill', (d) => getColor(d.source))
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));

  const labels = container.append('g')
    .selectAll('text')
    .data(currentNodes.filter((n) => n.score && n.score >= 5))
    .enter()
    .append('text')
    .attr('class', 'graph-label')
    .text((d) => {
      const t = d.title || '';
      return t.length > 30 ? t.substring(0, 28) + '...' : t;
    })
    .attr('font-size', '8px')
    .attr('dx', (d) => getRadius(d.score) + 3)
    .attr('dy', 3);

  const tooltip = document.getElementById('graph-tooltip');
  node.on('mouseover', (event, d) => {
    if (!tooltip) return;
    tooltip.classList.remove('hidden');
    tooltip.innerHTML =
      '<strong>' + (d.title || 'Untitled') + '</strong><br>' +
      (d.authors ? '<em>' + d.authors + '</em><br>' : '') +
      [d.journal, d.year].filter(Boolean).join(', ') +
      (d.score ? '<br>Score: ' + d.score.toFixed(1) : '') +
      (d.doi ? '<br><a href="https://doi.org/' + d.doi + '" target="_blank">DOI</a>' : '') +
      '<br><span style="color:' + getColor(d.source) + '">● ' + (d.source || 'unknown') + '</span>';
    tooltip.style.left = event.pageX + 12 + 'px';
    tooltip.style.top = event.pageY - 20 + 'px';
  });

  node.on('mouseout', () => {
    if (tooltip) tooltip.classList.add('hidden');
  });

  node.on('click', (event, d) => {
    const info = document.getElementById('graph-info');
    if (!info) return;
    info.innerHTML =
      '<h4>' + (d.title || 'Untitled') + '</h4>' +
      '<p>' + (d.authors || '') + '</p>' +
      '<p>' + [d.journal, d.year].filter(Boolean).join(', ') + '</p>' +
      (d.score ? '<p>Score: ' + d.score.toFixed(1) + '</p>' : '') +
      (d.keyword ? '<p>Keyword: <strong>' + d.keyword + '</strong></p>' : '') +
      (d.doi ? '<p><a href="https://doi.org/' + d.doi + '" target="_blank" class="cite-link">DOI: ' + d.doi + '</a></p>' : '') +
      (d.pmid ? '<p><a href="https://pubmed.ncbi.nlm.nih.gov/' + d.pmid + '" target="_blank" class="cite-link">PMID: ' + d.pmid + '</a></p>' : '');
  });

  simulation.on('tick', () => {
    link
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y);
    node
      .attr('cx', (d) => d.x)
      .attr('cy', (d) => d.y);
    labels
      .attr('x', (d) => d.x)
      .attr('y', (d) => d.y);
  });

  const info = document.getElementById('graph-info');
  if (info && currentNodes.length === 0) {
    info.innerHTML = '<p>No papers found. Run a pipeline or import papers first.</p>';
  } else if (info) {
    info.innerHTML = '<p>' + currentNodes.length + ' papers, ' + validEdges.length + ' connections. Click a node for details.</p>';
  }
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(event, d) {
  d.fx = event.x;
  d.fy = event.y;
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

async function loadGraph() {
  const keyword = document.getElementById('graph-keyword-filter')?.value || '';
  const limit = document.getElementById('graph-limit')?.value || 80;
  try {
    const data = await fetchGraph(keyword, limit);
    renderGraph(data);
  } catch (e) {
    console.error('[Graph] Failed to load:', e);
    const info = document.getElementById('graph-info');
    if (info) info.innerHTML = '<p style="color:#f44336;">Error loading graph: ' + e.message + '</p>';
  }
}

export async function init() {
  await populateKeywordFilter();
  document.getElementById('graph-refresh-btn')?.addEventListener('click', loadGraph);
  document.getElementById('graph-keyword-filter')?.addEventListener('change', loadGraph);
  await loadGraph();
}

export async function onActivate() {
  if (currentNodes.length > 0) {
    renderGraph({ nodes: currentNodes, edges: currentEdges });
  } else {
    await loadGraph();
  }
}
