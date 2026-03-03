"""JARVIS Research OS - Streamlit Dashboard (v1.3.0).

Launch: streamlit run jarvis_web/streamlit_app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import yaml


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

@st.cache_data(ttl=60)
def load_config():
    cfg_path = PROJECT_ROOT / "config.yaml"
    if cfg_path.exists():
        return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    return {}


def get_log_files(subdir: str) -> list[Path]:
    cfg = load_config()
    logs_dir = Path(cfg.get("storage", {}).get("logs_dir", "logs"))
    local_dir = PROJECT_ROOT / "logs"
    files = []
    for d in [logs_dir / subdir, local_dir / subdir]:
        if d.exists():
            files.extend(sorted(d.glob("*.json"), reverse=True))
    return files


def load_json(path: Path) -> list | dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ #
# Page config
# ------------------------------------------------------------------ #

st.set_page_config(
    page_title="JARVIS Research OS",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
# Sidebar
# ------------------------------------------------------------------ #

st.sidebar.title("JARVIS Research OS")
st.sidebar.caption("v1.3.0 — Systematic Literature Review")

page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Search Results", "Citation Network", "ChromaDB", "Storage"],
)

# ------------------------------------------------------------------ #
# Page: Overview
# ------------------------------------------------------------------ #

if page == "Overview":
    st.title("JARVIS Research OS Dashboard")
    st.markdown("Automated Systematic Literature Review system with 22 CLI commands.")

    col1, col2, col3, col4 = st.columns(4)

    # CLI commands count
    col1.metric("CLI Commands", "22")

    # ChromaDB count
    try:
        from jarvis_core.embeddings.paper_store import PaperStore
        store = PaperStore()
        col2.metric("ChromaDB Papers", store.count())
    except Exception:
        col2.metric("ChromaDB Papers", "N/A")

    # Log file counts
    pipeline_logs = get_log_files("pipeline")
    col3.metric("Pipeline Runs", len(pipeline_logs))

    orchestrate_logs = get_log_files("orchestrate")
    col4.metric("Orchestrate Runs", len(orchestrate_logs))

    st.divider()

    # Recent activity
    st.subheader("Recent Activity")
    all_logs = []
    for sub in ["pipeline", "orchestrate", "deep_research"]:
        for f in get_log_files(sub)[:3]:
            all_logs.append({"type": sub, "file": f.name, "path": str(f)})
    if all_logs:
        for log in all_logs[:10]:
            st.text(f"[{log['type']}] {log['file']}")
    else:
        st.info("No runs found yet. Use CLI commands to generate data.")

# ------------------------------------------------------------------ #
# Page: Search Results
# ------------------------------------------------------------------ #

elif page == "Search Results":
    st.title("Search Results Viewer")

    log_type = st.selectbox("Result type", ["pipeline", "orchestrate", "deep_research"])
    files = get_log_files(log_type)

    if not files:
        st.warning(f"No {log_type} results found.")
    else:
        selected = st.selectbox("Select file", files, format_func=lambda x: x.name)
        if selected:
            data = load_json(selected)
            papers = data if isinstance(data, list) else data.get("papers", [])

            st.metric("Papers", len(papers))

            if papers:
                for i, p in enumerate(papers):
                    with st.expander(f"{i+1}. {p.get('title', 'No title')[:80]}"):
                        c1, c2 = st.columns(2)
                        c1.write(f"**Year:** {p.get('year', 'N/A')}")
                        c1.write(f"**Source:** {p.get('source', 'N/A')}")
                        c2.write(f"**DOI:** {p.get('doi', 'N/A')}")
                        c2.write(f"**Evidence:** {p.get('evidence_level', 'N/A')}")
                        authors = p.get("authors", "")
                        if isinstance(authors, list):
                            authors = ", ".join(authors)
                        st.write(f"**Authors:** {authors}")
                        abstract = p.get("abstract", "No abstract")
                        if len(abstract) > 500:
                            abstract = abstract[:500] + "..."
                        st.write(abstract)

# ------------------------------------------------------------------ #
# Page: Citation Network
# ------------------------------------------------------------------ #

elif page == "Citation Network":
    st.title("Citation Network Viewer")

    cfg = load_config()
    logs_dir = Path(cfg.get("storage", {}).get("logs_dir", "logs"))
    cg_dir = logs_dir / "citation_graph"
    local_cg = PROJECT_ROOT / "logs" / "citation_graph"

    md_files = []
    for d in [cg_dir, local_cg]:
        if d.exists():
            md_files.extend(d.glob("*.md"))

    stats_files = []
    for d in [cg_dir, local_cg]:
        if d.exists():
            stats_files.extend(d.glob("*_stats.json"))

    # Show stats
    if stats_files:
        stats = load_json(stats_files[0])
        c1, c2, c3 = st.columns(3)
        c1.metric("Nodes", stats.get("nodes", 0))
        c2.metric("Edges", stats.get("edges", 0))
        c3.metric("Components", stats.get("components", "N/A"))

        # Top cited
        top_cited = stats.get("top_cited", [])
        if top_cited:
            st.subheader("Most Cited Papers")
            for tc in top_cited:
                st.write(f"- **{tc.get('title', 'N/A')}** ({tc.get('citations', 0)} citations)")

        # Top citers
        top_citers = stats.get("top_citers", [])
        if top_citers:
            st.subheader("Top Citing Papers")
            for tc in top_citers:
                st.write(f"- **{tc.get('title', 'N/A')}** ({tc.get('refs', 0)} references)")
    else:
        st.info("No citation network data. Run: jarvis citation-graph <file.json>")

    # Show mermaid
    mmd_files = []
    for d in [cg_dir, local_cg]:
        if d.exists():
            mmd_files.extend(d.glob("*.mmd"))
    if mmd_files:
        st.subheader("Network Diagram (Mermaid)")
        mmd_content = mmd_files[0].read_text(encoding="utf-8")
        st.code(mmd_content, language="mermaid")

# ------------------------------------------------------------------ #
# Page: ChromaDB
# ------------------------------------------------------------------ #

elif page == "ChromaDB":
    st.title("ChromaDB Semantic Search")

    try:
        from jarvis_core.embeddings.paper_store import PaperStore
        store = PaperStore()
        st.metric("Total Papers Indexed", store.count())
    except Exception as e:
        st.error(f"ChromaDB error: {e}")
        store = None

    if store and store.count() > 0:
        query = st.text_input("Search query", placeholder="e.g. PD-1 resistance mechanisms")
        top_k = st.slider("Results", 1, 20, 5)

        if query:
            results = store.search(query, top_k=top_k)
            st.write(f"Found {len(results)} results")
            for i, r in enumerate(results):
                meta = r.get("metadata", {})
                score = r.get("score", 0)
                with st.expander(f"{i+1}. {meta.get('title', 'N/A')[:80]} (score: {score:.3f})"):
                    st.write(f"**Year:** {meta.get('year', 'N/A')}")
                    st.write(f"**Source:** {meta.get('source', 'N/A')}")
    elif store:
        st.info("ChromaDB is empty. Index papers with: jarvis semantic-search --db file.json --index-only")

# ------------------------------------------------------------------ #
# Page: Storage
# ------------------------------------------------------------------ #

elif page == "Storage":
    st.title("Storage Status")

    cfg = load_config()
    storage = cfg.get("storage", {})
    obsidian = cfg.get("obsidian", {})

    st.subheader("Configuration")
    st.json({
        "logs_dir": storage.get("logs_dir", "logs"),
        "exports_dir": storage.get("exports_dir", "exports"),
        "pdf_archive_dir": storage.get("pdf_archive_dir", "pdf-archive"),
        "obsidian_vault": obsidian.get("vault_path", "N/A"),
    })

    st.subheader("Directory Status")
    dirs_to_check = {
        "Logs": storage.get("logs_dir", "logs"),
        "Exports": storage.get("exports_dir", "exports"),
        "PDF Archive": storage.get("pdf_archive_dir", "pdf-archive"),
        "Obsidian Vault": obsidian.get("vault_path", ""),
    }

    for name, dirpath in dirs_to_check.items():
        p = Path(dirpath)
        if p.exists():
            file_count = sum(1 for _ in p.rglob("*") if _.is_file())
            st.success(f"{name}: {dirpath} ({file_count} files)")
        else:
            st.warning(f"{name}: {dirpath} (not found)")

    # ChromaDB status
    st.subheader("ChromaDB")
    try:
        from jarvis_core.embeddings.paper_store import PaperStore
        store = PaperStore()
        chroma_path = PROJECT_ROOT / ".chroma"
        st.write(f"Collection: jarvis_papers")
        st.write(f"Papers: {store.count()}")
        st.write(f"Path: {chroma_path}")
        st.write(f"Exists: {chroma_path.exists()}")
    except Exception as e:
        st.error(f"ChromaDB: {e}")
