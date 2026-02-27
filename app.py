"""JARVIS Research OS - Streamlit Dashboard (Phase 4)."""

import json
import streamlit as st
from pathlib import Path


# --- Page config ---
st.set_page_config(
    page_title="JARVIS Research OS",
    page_icon="🔬",
    layout="wide",
)


# --- Helper functions ---
@st.cache_data
def load_papers(json_path):
    """Load papers from a JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_json_files():
    """Find all JSON files in logs/search/."""
    search_dir = Path("logs/search")
    if not search_dir.exists():
        return []
    files = sorted(search_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [str(f) for f in files]


def get_note_files():
    """Find all note files in logs/notes/."""
    notes_dir = Path("logs/notes")
    if not notes_dir.exists():
        return []
    files = sorted(notes_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [str(f) for f in files]


def filter_papers(papers, keyword, year_range, sources):
    """Filter papers by keyword, year range, and source."""
    filtered = []
    for p in papers:
        # Keyword filter
        if keyword:
            kw = keyword.lower()
            searchable = " ".join([
                p.get("title", ""),
                p.get("abstract", ""),
                p.get("summary_ja", ""),
                p.get("journal", ""),
                " ".join(p.get("authors", [])),
                " ".join(p.get("keywords", [])),
                " ".join(p.get("mesh_terms", [])),
            ]).lower()
            if kw not in searchable:
                continue

        # Year filter
        year = p.get("year")
        if year and isinstance(year, (int, float)):
            if not (year_range[0] <= year <= year_range[1]):
                continue

        # Source filter
        if sources and p.get("source", "") not in sources:
            continue

        filtered.append(p)
    return filtered


def make_bibtex_entry(p, index):
    """Generate a single BibTeX entry."""
    authors = " and ".join(p.get("authors", ["Unknown"])[:5])
    title = p.get("title", "Untitled")
    journal = p.get("journal", "")
    year = p.get("year", "n.d.")
    doi = p.get("doi", "")
    pmid = p.get("pmid", "")

    key = f"paper{index}_{year}"
    lines = [f"@article{{{key},"]
    lines.append(f"  author = {{{authors}}},")
    lines.append(f"  title = {{{title}}},")
    if journal:
        lines.append(f"  journal = {{{journal}}},")
    lines.append(f"  year = {{{year}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    if pmid:
        lines.append(f"  pmid = {{{pmid}}},")
    lines.append("}")
    return "\n".join(lines)


# --- Sidebar ---
st.sidebar.title("JARVIS Research OS")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "ページ選択",
    ["📚 論文データベース", "📝 研究ノート", "📊 統計情報"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**収集済みデータ**")

json_files = get_json_files()
note_files = get_note_files()

# Show dataset selector in sidebar
selected_file = st.sidebar.selectbox(
    "データセット",
    json_files,
    format_func=lambda x: Path(x).stem,
) if json_files else None


# --- Main content ---

if page == "📚 論文データベース":
    st.title("📚 論文データベース")

    if not selected_file:
        st.warning("データがありません。まず論文を検索してください。")
        st.code('python -m jarvis_cli search "PD-1" --max 20 --json', language="powershell")
        st.stop()

    papers = load_papers(selected_file)
    st.info(f"**{Path(selected_file).stem}** — {len(papers)} 件の論文")

    # --- Filters ---
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        keyword = st.text_input("🔍 キーワード検索", placeholder="例: immunotherapy, autophagy")

    with col2:
        years = [p.get("year", 2024) for p in papers if isinstance(p.get("year"), (int, float))]
        if years:
            min_year, max_year = int(min(years)), int(max(years))
        else:
            min_year, max_year = 2000, 2026
        year_range = st.slider("📅 年代", min_year, max_year, (min_year, max_year))

    with col3:
        all_sources = sorted(set(p.get("source", "unknown") for p in papers))
        sources = st.multiselect("📁 ソース", all_sources, default=all_sources)

    # Apply filters
    filtered = filter_papers(papers, keyword, year_range, sources)
    st.markdown(f"**表示中: {len(filtered)} / {len(papers)} 件**")

    # --- BibTeX download ---
    if filtered:
        all_bib = "\n\n".join(make_bibtex_entry(p, i) for i, p in enumerate(filtered, 1))
        st.download_button(
            "📥 BibTeX ダウンロード",
            data=all_bib,
            file_name=f"{Path(selected_file).stem}.bib",
            mime="text/plain",
        )

    # --- Paper list ---
    st.markdown("---")

    for i, p in enumerate(filtered, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "n.d.")
        journal = p.get("journal", "")
        authors = p.get("authors", [])
        source = p.get("source", "")
        doi = p.get("doi", "")
        pmid = p.get("pmid", "")
        url = p.get("url", "")
        evidence = p.get("evidence_level", "")
        summary = p.get("summary_ja", "")
        abstract = p.get("abstract", "")

        # Author string
        a_str = ", ".join(authors[:3])
        if len(authors) > 3:
            a_str += f" et al. ({len(authors)} authors)"

        # Paper card
        with st.expander(f"**[{i}] {title}** ({year}) — {journal}"):
            if a_str:
                st.markdown(f"**著者:** {a_str}")
            st.markdown(f"**年:** {year} | **ソース:** {source}")
            if evidence and evidence != "N/A":
                st.markdown(f"**CEBM エビデンスレベル:** {evidence}")

            # Links
            links = []
            if url:
                links.append(f"[論文リンク]({url})")
            if doi:
                links.append(f"[DOI](https://doi.org/{doi})")
            if pmid:
                links.append(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
            if links:
                st.markdown(" | ".join(links))

            if summary and not summary.startswith("（"):
                st.markdown("**日本語要約:**")
                st.markdown(summary)

            if abstract:
                st.markdown("**Abstract:**")
                st.markdown(f"<details><summary>Click to expand</summary>{abstract}</details>", unsafe_allow_html=True)


elif page == "📝 研究ノート":
    st.title("📝 研究ノート")

    if not note_files:
        st.warning("研究ノートがありません。まず生成してください。")
        st.code('python -m jarvis_cli note logs/search/PD-1_final.json --provider gemini', language="powershell")
        st.stop()

    selected_note = st.selectbox(
        "研究ノートを選択",
        note_files,
        format_func=lambda x: Path(x).stem,
    )

    if selected_note:
        content = Path(selected_note).read_text(encoding="utf-8")
        st.markdown(content)

        st.download_button(
            "📥 Markdown ダウンロード",
            data=content,
            file_name=Path(selected_note).name,
            mime="text/markdown",
        )


elif page == "📊 統計情報":
    st.title("📊 統計情報")

    if not selected_file:
        st.warning("データがありません。")
        st.stop()

    papers = load_papers(selected_file)

    col1, col2, col3 = st.columns(3)
    col1.metric("総論文数", len(papers))

    has_summary = sum(1 for p in papers if p.get("summary_ja") and not p["summary_ja"].startswith("（"))
    col2.metric("要約あり", has_summary)

    has_doi = sum(1 for p in papers if p.get("doi"))
    col3.metric("DOI あり", has_doi)

    # Year distribution
    st.markdown("### 年代分布")
    years = [p.get("year") for p in papers if isinstance(p.get("year"), (int, float))]
    if years:
        year_counts = {}
        for y in years:
            y = int(y)
            year_counts[y] = year_counts.get(y, 0) + 1
        sorted_years = sorted(year_counts.items())
        st.bar_chart(dict(sorted_years))

    # Source distribution
    st.markdown("### ソース分布")
    source_counts = {}
    for p in papers:
        s = p.get("source", "unknown")
        source_counts[s] = source_counts.get(s, 0) + 1
    st.bar_chart(source_counts)

    # Journal distribution (top 10)
    st.markdown("### ジャーナル分布（上位10）")
    journal_counts = {}
    for p in papers:
        j = p.get("journal", "")
        if j:
            journal_counts[j] = journal_counts.get(j, 0) + 1
    if journal_counts:
        top_journals = sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        st.bar_chart(dict(top_journals))

    # Evidence level distribution
    st.markdown("### エビデンスレベル分布")
    evidence_counts = {}
    for p in papers:
        ev = p.get("evidence_level", "N/A")
        if ev:
            evidence_counts[ev] = evidence_counts.get(ev, 0) + 1
    if evidence_counts:
        st.bar_chart(evidence_counts)
