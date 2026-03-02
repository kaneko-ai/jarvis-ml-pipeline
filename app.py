"""JARVIS Research OS - Streamlit Dashboard (B-6 Enhanced)."""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="JARVIS Research OS", page_icon="R", layout="wide")


@st.cache_data
def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_json_files():
    d = Path("logs/search")
    if not d.exists():
        return []
    return [str(f) for f in sorted(d.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)]


def get_pipeline_files():
    d = Path("logs/pipeline")
    if not d.exists():
        return []
    return [str(f) for f in sorted(
        [f for f in d.glob("*.json")
         if not f.stem.endswith("_log")
         and not f.stem.endswith("_contradictions")
         and not f.stem.endswith("_stance")],
        key=lambda f: f.stat().st_mtime, reverse=True)]


def get_pipeline_log_files():
    d = Path("logs/pipeline")
    if not d.exists():
        return []
    return [str(f) for f in sorted(d.glob("*_log.json"), key=lambda f: f.stat().st_mtime, reverse=True)]


def get_note_files():
    d = Path("logs/notes")
    if not d.exists():
        return []
    return [str(f) for f in sorted(d.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)]


def get_prisma_files():
    all_f = []
    for d in [Path("logs/prisma"), Path("logs/pipeline")]:
        if d.exists():
            all_f.extend(d.glob("*_prisma.md"))
            if d.name == "prisma":
                all_f.extend(d.glob("*.md"))
    return [str(f) for f in sorted(set(all_f), key=lambda f: f.stat().st_mtime, reverse=True)]


def get_contradiction_files():
    all_f = []
    for d in [Path("logs/search"), Path("logs/pipeline")]:
        if d.exists():
            all_f.extend(d.glob("*_contradictions.json"))
    return [str(f) for f in sorted(set(all_f), key=lambda f: f.stat().st_mtime, reverse=True)]


def filter_papers(papers, keyword, year_range, sources):
    filtered = []
    for p in papers:
        if keyword:
            kw = keyword.lower()
            searchable = " ".join([
                p.get("title", ""), p.get("abstract", ""),
                p.get("summary_ja", ""), p.get("journal", ""),
                " ".join(p.get("authors", [])),
                " ".join(p.get("keywords", [])),
                " ".join(p.get("mesh_terms", [])),
            ]).lower()
            if kw not in searchable:
                continue
        year = p.get("year")
        if year and isinstance(year, (int, float)):
            if not (year_range[0] <= year <= year_range[1]):
                continue
        if sources and p.get("source", "") not in sources:
            continue
        filtered.append(p)
    return filtered


def make_bibtex_entry(p, index):
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


def evidence_badge(level):
    badges = {
        "1a": "[1a] SR/MA", "1b": "[1b] RCT",
        "2a": "[2a] SR-Cohort", "2b": "[2b] Cohort",
        "3a": "[3a] SR-CC", "3b": "[3b] Case-Control",
        "4": "[4] Case Series", "5": "[5] Basic/Expert",
    }
    return badges.get(str(level), f"[{level}]")


# ==================== Sidebar ====================
st.sidebar.title("JARVIS Research OS")
st.sidebar.markdown("---")

page = st.sidebar.radio("Page", [
    "Papers", "Notes", "Statistics", "PRISMA",
    "Execution Logs", "Contradictions",
])

st.sidebar.markdown("---")
st.sidebar.markdown("**Datasets**")

json_files = get_json_files()
pipeline_files = get_pipeline_files()
all_data_files = pipeline_files + json_files

selected_file = st.sidebar.selectbox(
    "Dataset", all_data_files, format_func=lambda x: Path(x).stem,
) if all_data_files else None


# ==================== Papers ====================
if page == "Papers":
    st.title("Papers Database")
    if not selected_file:
        st.warning("No data. Run pipeline first.")
        st.stop()

    papers = load_json(selected_file)
    if not isinstance(papers, list):
        st.error("Not a paper list.")
        st.stop()

    st.info(f"**{Path(selected_file).stem}** - {len(papers)} papers")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        keyword = st.text_input("Keyword", placeholder="e.g. immunotherapy")
    with col2:
        years = [p.get("year", 2024) for p in papers if isinstance(p.get("year"), (int, float))]
        min_y = int(min(years)) if years else 2000
        max_y = int(max(years)) if years else 2026
        year_range = st.slider("Year", min_y, max_y, (min_y, max_y))
    with col3:
        all_sources = sorted(set(p.get("source", "unknown") for p in papers))
        sources = st.multiselect("Source", all_sources, default=all_sources)

    filtered = filter_papers(papers, keyword, year_range, sources)
    st.markdown(f"**Showing: {len(filtered)} / {len(papers)}**")

    if filtered:
        bib = "\n\n".join(make_bibtex_entry(p, i) for i, p in enumerate(filtered, 1))
        st.download_button("BibTeX Download", data=bib, file_name=f"{Path(selected_file).stem}.bib", mime="text/plain")

    st.markdown("---")
    st.markdown("### Paper Table")
    table_data = []
    for i, p in enumerate(filtered, 1):
        table_data.append({
            "#": i,
            "Title": p.get("title", "Untitled")[:80],
            "Year": p.get("year", ""),
            "Evidence": p.get("evidence_level", ""),
            "Grade": p.get("paper_grade", p.get("grade", "")),
            "Source": p.get("source", ""),
            "Citations": p.get("citation_count", 0),
        })
    if table_data:
        st.dataframe(table_data, use_container_width=True, height=400)

    st.markdown("---")
    st.markdown("### Paper Details")
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
        study_type = p.get("study_type", "")
        summary = p.get("summary_ja", "")
        abstract = p.get("abstract", "")
        grade_val = p.get("paper_grade", p.get("grade", ""))
        score_val = p.get("paper_score", p.get("score", ""))

        a_str = ", ".join(authors[:3])
        if len(authors) > 3:
            a_str += " et al."

        with st.expander(f"[{i}] {title} ({year}) - {journal}"):
            bc = st.columns(4)
            if evidence and evidence not in ("N/A", "unknown"):
                bc[0].markdown(f"**Evidence:** {evidence_badge(evidence)}")
            if study_type and study_type != "unknown":
                bc[1].markdown(f"**Study:** {study_type}")
            if grade_val:
                bc[2].markdown(f"**Grade:** {grade_val}")
            if score_val:
                bc[3].markdown(f"**Score:** {score_val}")
            if a_str:
                st.markdown(f"**Authors:** {a_str}")
            st.markdown(f"**Year:** {year} | **Source:** {source}")
            links = []
            if url:
                links.append(f"[Link]({url})")
            if doi:
                links.append(f"[DOI](https://doi.org/{doi})")
            if pmid:
                links.append(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
            if links:
                st.markdown(" | ".join(links))
            if summary:
                st.markdown("**Japanese Summary:**")
                st.markdown(summary)
            if abstract:
                st.markdown("**Abstract:**")
                st.markdown(
                    f"<details><summary>Click to expand</summary>{abstract}</details>",
                    unsafe_allow_html=True,
                )


# ==================== Notes ====================
elif page == "Notes":
    st.title("Research Notes")
    note_files = get_note_files()
    if not note_files:
        st.warning("No notes found.")
        st.stop()
    selected_note = st.selectbox("Select note", note_files, format_func=lambda x: Path(x).stem)
    if selected_note:
        content = Path(selected_note).read_text(encoding="utf-8")
        st.markdown(content)
        st.download_button("Download", data=content, file_name=Path(selected_note).name, mime="text/markdown")


# ==================== Statistics ====================
elif page == "Statistics":
    st.title("Statistics")
    if not selected_file:
        st.warning("No data.")
        st.stop()
    papers = load_json(selected_file)
    if not isinstance(papers, list):
        st.error("Not a paper list.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Papers", len(papers))
    has_sum = sum(1 for p in papers if p.get("summary_ja"))
    c2.metric("With Summary", has_sum)
    has_doi = sum(1 for p in papers if p.get("doi"))
    c3.metric("With DOI", has_doi)
    has_score = sum(1 for p in papers if p.get("paper_score") or p.get("score"))
    c4.metric("With Score", has_score)

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.markdown("### Evidence Level Distribution")
        ev_counts = {}
        for p in papers:
            ev = p.get("evidence_level", "N/A")
            if ev:
                ev_counts[ev] = ev_counts.get(ev, 0) + 1
        if ev_counts:
            order = ["1a", "1b", "2a", "2b", "3a", "3b", "4", "5", "unknown", "N/A"]
            sorted_ev = {}
            for lv in order:
                if lv in ev_counts:
                    sorted_ev[lv] = ev_counts[lv]
            for lv in ev_counts:
                if lv not in sorted_ev:
                    sorted_ev[lv] = ev_counts[lv]
            st.bar_chart(sorted_ev)
        else:
            st.info("No evidence data.")

    with right:
        st.markdown("### Paper Grade Distribution")
        gr_counts = {}
        for p in papers:
            g = p.get("paper_grade", p.get("grade", "N/A"))
            if g:
                gr_counts[str(g)] = gr_counts.get(str(g), 0) + 1
        if gr_counts:
            g_order = ["A", "B", "C", "D", "F", "N/A"]
            sorted_gr = {}
            for g in g_order:
                if g in gr_counts:
                    sorted_gr[g] = gr_counts[g]
            for g in gr_counts:
                if g not in sorted_gr:
                    sorted_gr[g] = gr_counts[g]
            st.bar_chart(sorted_gr)
        else:
            st.info("No grade data.")

    st.markdown("---")
    st.markdown("### Year Distribution")
    years = [p.get("year") for p in papers if isinstance(p.get("year"), (int, float))]
    if years:
        yc = {}
        for y in years:
            y = int(y)
            yc[y] = yc.get(y, 0) + 1
        st.bar_chart(dict(sorted(yc.items())))

    left2, right2 = st.columns(2)
    with left2:
        st.markdown("### Source Distribution")
        sc = {}
        for p in papers:
            s = p.get("source", "unknown")
            sc[s] = sc.get(s, 0) + 1
        st.bar_chart(sc)

    with right2:
        st.markdown("### Top 10 Journals")
        jc = {}
        for p in papers:
            j = p.get("journal", "")
            if j:
                jc[j] = jc.get(j, 0) + 1
        if jc:
            top = sorted(jc.items(), key=lambda x: x[1], reverse=True)[:10]
            st.bar_chart(dict(top))

    st.markdown("### Study Type Distribution")
    stc = {}
    for p in papers:
        t = p.get("study_type", "unknown")
        if t:
            stc[t] = stc.get(t, 0) + 1
    if stc:
        st.bar_chart(stc)


# ==================== PRISMA ====================
elif page == "PRISMA":
    st.title("PRISMA 2020 Flow Diagram")
    prisma_files = get_prisma_files()
    if not prisma_files:
        st.warning("No PRISMA diagrams.")
        st.stop()
    sel = st.selectbox("Select PRISMA", prisma_files, format_func=lambda x: Path(x).stem)
    if sel:
        content = Path(sel).read_text(encoding="utf-8")
        mermaid_path = Path(sel).with_suffix(".mmd")
        if mermaid_path.exists():
            mc = mermaid_path.read_text(encoding="utf-8")
            st.markdown("### Flow Diagram (Mermaid code)")
            st.code(mc, language="text")
            try:
                import streamlit.components.v1 as components
                html_str = '<div class="mermaid">\n' + mc + '\n</div>\n'
                html_str += '<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>\n'
                html_str += "<script>mermaid.initialize({startOnLoad:true});</script>\n"
                components.html(html_str, height=500, scrolling=True)
            except Exception:
                st.info("Paste code at mermaid.live to view diagram.")
        st.markdown("---")
        st.markdown(content)
        st.download_button("Download PRISMA", data=content, file_name=Path(sel).name, mime="text/markdown")


# ==================== Execution Logs (B-6 NEW) ====================
elif page == "Execution Logs":
    st.title("Pipeline Execution Logs")
    log_files = get_pipeline_log_files()
    if not log_files:
        st.warning("No logs. Run pipeline first.")
        st.stop()

    st.markdown(f"**{len(log_files)} execution logs**")
    st.markdown("---")

    for lf in log_files:
        try:
            ld = load_json(lf)
        except Exception:
            continue
        eid = ld.get("execution_id", "?")
        ts = ld.get("timestamp", "")
        query = ld.get("query", "")
        dur = ld.get("duration_seconds", 0)
        total = ld.get("total_retrieved", 0)
        dedup = ld.get("after_dedup", 0)
        ev = ld.get("evidence_grading", {})
        scount = ld.get("llm_summary", 0)
        prov = ld.get("llm_provider", "none")
        obs_n = ld.get("obsidian_export", 0)
        zot_n = ld.get("zotero_sync", 0)
        prisma_p = ld.get("prisma_diagram", "")
        bib_p = ld.get("bibtex_file", "")
        out = ld.get("output_file", "")

        try:
            ts_d = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts_d = ts

        with st.expander(f'{ts_d} - "{query}" ({dedup} papers, {dur}s)'):
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Retrieved", total)
            mc2.metric("After Dedup", dedup)
            mc3.metric("Summaries", scount)
            mc4.metric("Duration", f"{dur}s")
            st.markdown(f"**ID:** `{eid}` | **Provider:** {prov}")
            if ev:
                st.markdown("**Evidence Distribution:**")
                st.bar_chart(ev)
            flags = []
            if obs_n:
                flags.append(f"Obsidian: {obs_n}")
            if zot_n:
                flags.append(f"Zotero: {zot_n}")
            if prisma_p:
                flags.append(f"PRISMA: {Path(prisma_p).name}")
            if bib_p:
                flags.append(f"BibTeX: {Path(bib_p).name}")
            if flags:
                st.markdown("**Outputs:** " + " | ".join(flags))
            if out:
                st.markdown(f"**Result:** `{out}`")


# ==================== Contradictions (B-6 NEW) ====================
elif page == "Contradictions":
    st.title("Contradiction Network")
    cf = get_contradiction_files()
    if not cf:
        st.warning("No contradiction data. Run: python -m jarvis_cli contradict <file.json>")
        st.stop()

    sel_c = st.selectbox("Select data", cf, format_func=lambda x: Path(x).stem)
    if sel_c:
        try:
            contras = load_json(sel_c)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

        if not contras:
            st.info("No contradictions detected (normal for same-topic papers).")
            st.stop()

        st.markdown(f"**{len(contras)} contradictions detected**")
        st.markdown("---")

        nodes = set()
        edges = []
        for c in contras:
            a = c.get("paper_a", "A")[:50]
            b = c.get("paper_b", "B")[:50]
            sc = c.get("score", 0)
            nodes.add(a)
            nodes.add(b)
            edges.append((a, b, sc))

        if nodes and edges:
            st.markdown("### Contradiction Graph (Mermaid)")
            mlines = ["graph LR"]
            nmap = {}
            for idx, nd in enumerate(sorted(nodes)):
                nid = f"N{idx}"
                safe = nd.replace('"', " ")
                mlines.append(f'    {nid}["{safe}"]')
                nmap[nd] = nid
            for a, b, sc in edges:
                ai = nmap.get(a, "N0")
                bi = nmap.get(b, "N0")
                mlines.append(f"    {ai} -- {sc} --> {bi}")
            mcode = "\n".join(mlines)
            st.code(mcode, language="text")
            try:
                import streamlit.components.v1 as components
                html_s = '<div class="mermaid">\n' + mcode + '\n</div>\n'
                html_s += '<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>\n'
                html_s += "<script>mermaid.initialize({startOnLoad:true});</script>\n"
                components.html(html_s, height=400, scrolling=True)
            except Exception:
                pass

        st.markdown("---")
        st.markdown("### Contradiction Pairs")
        for idx, c in enumerate(contras, 1):
            ta = c.get("paper_a", "?")
            tb = c.get("paper_b", "?")
            sc = c.get("score", 0)
            ct = c.get("type", "")
            det = c.get("details", "")
            with st.expander(f"#{idx} (score: {sc}) - {ta[:60]} vs {tb[:60]}"):
                st.markdown(f"**Paper A:** {ta}")
                st.markdown(f"**Paper B:** {tb}")
                st.markdown(f"**Score:** {sc}")
                if ct:
                    st.markdown(f"**Type:** {ct}")
                if det:
                    st.markdown(f"**Details:** {det}")

        st.download_button(
            "Download JSON",
            data=json.dumps(contras, ensure_ascii=False, indent=2),
            file_name=Path(sel_c).name,
            mime="application/json",
        )
