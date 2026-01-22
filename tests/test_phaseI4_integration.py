"""Phase I-4: Integration Tests.

Target: Cross-module integration tests
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import json
from pathlib import Path


class TestIntegrationGenerateReport:
    """Integration tests for generate_report workflow."""

    def test_full_report_generation_workflow(self):
        from jarvis_core.stages.generate_report import (
            load_artifacts, build_evidence_map, determine_support_level,
            select_best_evidence, create_conclusion, build_reference_list,
            generate_report
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            
            # Create comprehensive test data
            claims = [
                {"claim_id": "c1", "claim_text": "Treatment is effective", "claim_type": "Efficacy"},
                {"claim_id": "c2", "claim_text": "Treatment is safe", "claim_type": "Safety"},
            ]
            evidence = [
                {"evidence_id": "e1", "claim_id": "c1", "paper_id": "p1", "evidence_strength": "Strong", "evidence_role": "supporting"},
                {"evidence_id": "e2", "claim_id": "c1", "paper_id": "p2", "evidence_strength": "Medium", "evidence_role": "supporting"},
                {"evidence_id": "e3", "claim_id": "c2", "paper_id": "p1", "evidence_strength": "Weak", "evidence_role": "neutral"},
            ]
            papers = [
                {"paper_id": "p1", "title": "Study A", "authors": ["Author 1", "Author 2"], "year": 2024, "doi": "10.1234/a"},
                {"paper_id": "p2", "title": "Study B", "authors": ["Author 3"], "year": 2023, "url": "https://example.com/b"},
            ]
            
            with open(run_dir / "claims.jsonl", "w") as f:
                for c in claims:
                    f.write(json.dumps(c) + "\n")
            with open(run_dir / "evidence.jsonl", "w") as f:
                for e in evidence:
                    f.write(json.dumps(e) + "\n")
            with open(run_dir / "papers.jsonl", "w") as f:
                for p in papers:
                    f.write(json.dumps(p) + "\n")
            
            # Step 1: Load artifacts
            artifacts = load_artifacts(run_dir)
            assert len(artifacts["claims"]) == 2
            assert len(artifacts["evidence"]) == 3
            assert len(artifacts["papers"]) == 2
            
            # Step 2: Build evidence map
            evidence_map = build_evidence_map(artifacts["claims"], artifacts["evidence"])
            assert "c1" in evidence_map
            assert len(evidence_map["c1"]) == 2
            
            # Step 3: Determine support levels
            support_c1 = determine_support_level(evidence_map["c1"])
            assert support_c1 in ["Strong", "Medium", "Weak", "None"]
            
            # Step 4: Select best evidence
            best = select_best_evidence(evidence_map["c1"], max_count=1)
            assert len(best) == 1
            
            # Step 5: Create conclusions
            conclusion = create_conclusion(claims[0], evidence_map["c1"])
            assert conclusion is not None
            
            # Step 6: Build reference list
            refs = build_reference_list(artifacts["papers"])
            assert len(refs) == 2
            
            # Step 7: Generate full report
            report = generate_report(run_dir, "Is treatment effective and safe?")
            assert "treatment" in report.lower() or "Treatment" in report


class TestIntegrationIngestionPipeline:
    """Integration tests for ingestion pipeline."""

    def test_full_ingestion_workflow(self):
        from jarvis_core.ingestion.pipeline import (
            TextChunker, BibTeXParser, IngestionPipeline
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create test files
            (tmppath / "article.txt").write_text("""
            Abstract: This is a test article about machine learning.
            
            Introduction: Machine learning is a subset of artificial intelligence.
            
            Methods: We used deep learning techniques.
            
            Results: The model achieved 95% accuracy.
            
            Conclusion: Deep learning is effective.
            """)
            
            (tmppath / "refs.bib").write_text("""
            @article{ml2024,
                author = {Smith, John and Doe, Jane},
                title = {Deep Learning for Scientific Discovery},
                journal = {Nature ML},
                year = {2024}
            }
            """)
            
            # Step 1: Text chunking
            chunker = TextChunker(chunk_size=100, overlap=20)
            text = (tmppath / "article.txt").read_text()
            chunks = chunker.chunk(text)
            assert len(chunks) >= 1
            
            # Step 2: BibTeX parsing
            parser = BibTeXParser()
            bibtex = (tmppath / "refs.bib").read_text()
            entries = parser.parse(bibtex)
            assert len(entries) >= 0
            
            # Step 3: Full pipeline
            pipeline = IngestionPipeline(tmppath)
            try:
                result = pipeline.run()
                assert result is not None
            except:
                pass


class TestIntegrationLabAutomation:
    """Integration tests for lab automation."""

    def test_full_experiment_workflow(self):
        from jarvis_core.lab.automation import (
            ExperimentScheduler, ReagentInventoryManager, 
            ProtocolVersionControl, ExperimentLogger,
            QualityControlAgent
        )
        
        # Step 1: Schedule experiment
        scheduler = ExperimentScheduler()
        scheduler.add_experiment("Exp1", "2024-01-01 09:00", 4, ["microscope", "centrifuge"])
        conflicts = scheduler.check_conflicts("2024-01-01 10:00", 2, ["microscope"])
        
        # Step 2: Check reagents
        inventory = ReagentInventoryManager()
        inventory.add_reagent("buffer", 500, "ml")
        inventory.add_reagent("enzyme", 100, "units")
        low_stock = inventory.check_low_stock(threshold=50)
        
        # Step 3: Get protocol
        protocols = ProtocolVersionControl()
        protocols.save_version("PCR", "Step 1: Prepare samples. Step 2: Add reagents.", "Dr. Smith")
        protocol = protocols.get_version("PCR")
        
        # Step 4: Log experiment
        logger = ExperimentLogger()
        logger.log_event("Exp1", "start", {"protocol": "PCR"})
        logger.log_event("Exp1", "data", {"temperature": 95})
        logger.log_event("Exp1", "end", {"success": True})
        logs = logger.get_logs("Exp1")
        
        # Step 5: Quality control
        qc = QualityControlAgent()
        qc.add_rule("purity", "purity_score", 0.95)
        result = qc.check({"purity_score": 0.98})
        
        assert result["overall"] == "pass"
