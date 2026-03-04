// agent-web/src/llm/paper-search.js
// Live paper search: PubMed E-utilities + Semantic Scholar API
// Free tier, no API keys required

const PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils";
const S2_BASE = "https://api.semanticscholar.org/graph/v1";

function fetchWithTimeout(url, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { ...options, signal: controller.signal })
    .finally(() => clearTimeout(timer));
}

// --- PubMed ---
async function searchPubMed(query, maxResults = 5) {
  try {
    // Step 1: ESearch to get PMIDs
    const searchUrl = PUBMED_BASE +
      "/esearch.fcgi?db=pubmed&retmode=json&retmax=" + maxResults +
      "&sort=relevance&term=" + encodeURIComponent(query);
    const searchRes = await fetchWithTimeout(searchUrl);
    if (!searchRes.ok) return [];
    const searchData = await searchRes.json();
    const ids = searchData.esearchresult?.idlist || [];
    if (ids.length === 0) return [];

    // Step 2: ESummary to get paper details
    const summaryUrl = PUBMED_BASE +
      "/esummary.fcgi?db=pubmed&retmode=json&id=" + ids.join(",");
    const summaryRes = await fetchWithTimeout(summaryUrl);
    if (!summaryRes.ok) return [];
    const summaryData = await summaryRes.json();
    const result = summaryData.result || {};

    return ids.map(id => {
      const paper = result[id];
      if (!paper) return null;
      return {
        source: "PubMed",
        pmid: id,
        title: paper.title || "No title",
        authors: (paper.authors || []).map(a => a.name).slice(0, 3).join(", "),
        journal: paper.source || "",
        year: paper.pubdate ? paper.pubdate.substring(0, 4) : "",
        url: "https://pubmed.ncbi.nlm.nih.gov/" + id + "/",
      };
    }).filter(Boolean);
  } catch (e) {
    console.error("PubMed search error:", e.message);
    return [];
  }
}

// --- Semantic Scholar ---
async function searchSemanticScholar(query, maxResults = 5) {
  try {
    const url = S2_BASE + "/paper/search?query=" +
      encodeURIComponent(query) +
      "&limit=" + maxResults +
      "&fields=title,authors,year,journal,citationCount,url,externalIds";
    const headers = { "Accept": "application/json" };
    let res = await fetchWithTimeout(url, { headers });
    if (res.status === 429) {
      console.log("S2 rate limited (429), retrying in 2s...");
      await new Promise(r => setTimeout(r, 2000));
      res = await fetchWithTimeout(url, { headers });
    }
    if (!res.ok) return [];
    const data = await res.json();
    return (data.data || []).map(p => ({
      source: "SemanticScholar",
      title: p.title || "No title",
      authors: (p.authors || []).map(a => a.name).slice(0, 3).join(", "),
      journal: p.journal?.name || "",
      year: p.year ? String(p.year) : "",
      citations: p.citationCount || 0,
      doi: p.externalIds?.DOI || "",
      url: p.url || "",
    }));
  } catch (e) {
    console.error("Semantic Scholar search error:", e.message);
    return [];
  }
}

// --- OpenAlex (free, no key, fallback) ---
async function searchOpenAlex(query, maxResults = 5) {
  try {
    const url = "https://api.openalex.org/works?search=" +
      encodeURIComponent(query) +
      "&per_page=" + maxResults +
      "&sort=publication_date:desc";
    const res = await fetchWithTimeout(url, {
      headers: { "User-Agent": "JARVIS-ResearchOS/1.0 (mailto:jarvis@localhost)" }
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.results || []).map(w => ({
      source: "OpenAlex",
      title: w.title || "No title",
      authors: (w.authorships || []).slice(0, 3).map(a => a.author && a.author.display_name).filter(Boolean).join(", "),
      journal: (w.primary_location && w.primary_location.source && w.primary_location.source.display_name) || "",
      year: w.publication_year ? String(w.publication_year) : "",
      citations: w.cited_by_count || 0,
      url: w.doi ? w.doi : (w.id || "")
    }));
  } catch (e) {
    console.error("OpenAlex search error:", e.message);
    return [];
  }
}

// --- Combined search ---
export async function searchLivePapers(query, maxPerSource = 5) {
  const [pubmedResults, s2Results] = await Promise.all([
    searchPubMed(query, maxPerSource),
    searchSemanticScholar(query, maxPerSource),
  ]);

  let openAlexResults = [];
    if (s2Results.length === 0) {
      console.log('S2 returned 0 results, trying OpenAlex fallback...');
      openAlexResults = await searchOpenAlex(query, maxPerSource);
    }
    return { pubmed: pubmedResults, semanticScholar: s2Results, openAlex: openAlexResults };
}

export function formatPapersForLLM(results) {
  const lines = [];
  const allPapers = [...(results.pubmed||[]), ...(results.semanticScholar||[]), ...(results.openAlex||[])];
  if (allPapers.length === 0) return "";

  lines.push("=== Live Paper Search Results (2023-2026) ===");
  allPapers.forEach((p, i) => {
    lines.push("[" + (i + 1) + "] " + p.title);
    lines.push("    Authors: " + p.authors);
    if (p.journal) lines.push("    Journal: " + p.journal);
    if (p.year) lines.push("    Year: " + p.year);
    if (p.citations) lines.push("    Citations: " + p.citations);
    lines.push("    Source: " + p.source);
    lines.push("    URL: " + p.url);
    lines.push("");
  });
  return lines.join("\n");
}
