"""Test that all key JARVIS modules can be imported without error."""
import pytest


class TestCoreImports:
    def test_litellm_client(self):
        from jarvis_core.llm.litellm_client import completion, completion_structured
        assert callable(completion)
        assert callable(completion_structured)

    def test_structured_models(self):
        from jarvis_core.llm.structured_models import (
            EvidenceGradeLLM, PaperSummaryLLM, ContradictionResultLLM, CitationStanceLLM,
        )
        assert EvidenceGradeLLM is not None

    def test_paper_store(self):
        from jarvis_core.embeddings.paper_store import PaperStore
        assert PaperStore is not None

    def test_citation_graph(self):
        from jarvis_core.rag.citation_graph import CitationGraph
        assert CitationGraph is not None

    def test_citation_enricher(self):
        from jarvis_core.rag.citation_enricher import build_enriched_graph
        assert callable(build_enriched_graph)

    def test_lightrag_engine(self):
        from jarvis_core.rag.lightrag_engine import JarvisLightRAG
        assert JarvisLightRAG is not None

    def test_pdf_client(self):
        from jarvis_core.pdf.mineru_client import MinerUClient
        assert MinerUClient is not None

    def test_storage_utils(self):
        from jarvis_core.storage_utils import get_logs_dir, get_exports_dir, get_pdf_archive_dir
        assert callable(get_logs_dir)

    def test_evidence(self):
        from jarvis_core.evidence import grade_evidence
        assert callable(grade_evidence)

    def test_mcp_hub(self):
        from jarvis_core.mcp.hub import MCPHub
        assert MCPHub is not None

    def test_skills_engine(self):
        from jarvis_core.skills.engine import SkillsEngine
        assert SkillsEngine is not None

    def test_unified_source(self):
        from jarvis_core.sources.unified_source_client import UnifiedSourceClient
        assert UnifiedSourceClient is not None


class TestCLIImports:
    def test_cli_main(self):
        from jarvis_cli import main
        assert callable(main)

    def test_browse(self):
        from jarvis_cli.browse import run_browse
        assert callable(run_browse)

    def test_orchestrate(self):
        from jarvis_cli.orchestrate import run_orchestrate
        assert callable(run_orchestrate)

    def test_deep_research(self):
        from jarvis_cli.deep_research import run_deep_research
        assert callable(run_deep_research)

    def test_pipeline(self):
        from jarvis_cli.pipeline import run_pipeline
        assert callable(run_pipeline)

    def test_citation_graph_cli(self):
        from jarvis_cli.citation_graph import run
        assert callable(run)

    def test_semantic_search(self):
        from jarvis_cli.semantic_search import run_semantic_search
        assert callable(run_semantic_search)
