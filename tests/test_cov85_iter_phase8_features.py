from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.iter.phase8_features import (
    EntityNormalizer,
    ExperimentProposer,
    FigureFirstSummarizer,
    FinalResilienceChecker,
    MultiStepReasoner,
    ObsidianExporter,
    PerformanceObserver,
    UncertaintyCalibrator,
    calibrate_uncertainty,
    check_final_resilience,
    normalize_entity,
)


def test_entity_normalizer_handles_canonical_synonym_and_fallback() -> None:
    n = EntityNormalizer()

    canonical = n.normalize("CD73", entity_type="gene")
    assert canonical.normalized == "CD73"

    synonym = n.normalize("Keytruda", entity_type="drug")
    assert synonym.normalized == "PEMBROLIZUMAB"
    assert "mk-3475" in synonym.synonyms

    fallback_gene = n.normalize("novel1", entity_type="gene")
    assert fallback_gene.normalized == "NOVEL1"

    fallback_drug = n.normalize("new compound", entity_type="drug")
    assert fallback_drug.normalized == "New Compound"


def test_uncertainty_calibrator_detects_hedges_negation_and_clamps() -> None:
    c = UncertaintyCalibrator()
    out = c.calibrate("This might possibly not work", raw_confidence=0.9)
    assert out.calibrated_confidence < 0.9
    assert "negation" in out.uncertainty_sources
    assert any(s.startswith("hedge_word:") for s in out.uncertainty_sources)

    low = c.calibrate("might no", raw_confidence=0.01)
    assert low.calibrated_confidence == 0.0

    high = c.calibrate("clear statement", raw_confidence=1.5)
    assert high.calibrated_confidence == 1.0


def test_performance_observer_persists_jsonl(tmp_path: Path) -> None:
    log_path = tmp_path / "perf" / "obs.jsonl"
    observer = PerformanceObserver(log_path=log_path)
    point = observer.observe({"latency_ms": 123.4})

    assert point.metrics["latency_ms"] == 123.4
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    payload = json.loads(lines[0])
    assert payload["metrics"]["latency_ms"] == 123.4


def test_figure_first_summarizer_limits_figures_and_claims() -> None:
    claims = [{"claim_text": f"claim-{i}"} for i in range(10)]
    figures = [{"caption": f"caption-{i}"} for i in range(5)]
    summary = FigureFirstSummarizer().summarize(claims=claims, figures=figures)

    assert "## Figure 1" in summary
    assert "## Figure 3" in summary
    assert "## Figure 4" not in summary
    assert "- claim-4" in summary
    assert "- claim-5" not in summary


def test_multi_step_reasoner_creates_steps_for_each_evidence() -> None:
    evidence = ["evidence-a", "evidence-b", "evidence-c"]
    steps = MultiStepReasoner().trace("claim", evidence)

    assert len(steps) == 3
    assert steps[0].step_id == 1
    assert steps[1].inference.startswith("ステップ2")
    assert steps[2].confidence == 0.8


def test_experiment_proposer_uses_limit_and_templates() -> None:
    proposals = ExperimentProposer().propose(["A", "B", "C", "D"], context="ignored")
    assert len(proposals) == 6  # up to 3 unknowns * first 2 templates
    assert all(("A" in p) or ("B" in p) or ("C" in p) for p in proposals)


def test_obsidian_exporter_creates_markdown_note(tmp_path: Path) -> None:
    run_data = {
        "run_id": "run-xyz",
        "timestamp": "2026-02-11T00:00:00Z",
        "query": "Cancer biomarkers",
        "answer": "Summary text",
        "citations": ["paper-1", "paper-2"],
    }
    exporter = ObsidianExporter()
    files = exporter.export_run(run_data, output_dir=tmp_path)

    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "# Cancer biomarkers" in content
    assert "- [[paper-1]]" in content
    assert "- [[paper-2]]" in content


def test_final_resilience_checker_and_wrapper() -> None:
    checker = FinalResilienceChecker()

    ready_input = {
        "contract_valid": True,
        "metrics": {"evidence_coverage": 0.97, "locator_rate": 0.99},
    }
    result = checker.check(ready_input)
    assert result["contract_valid"] is True
    assert result["evidence_coverage"] is True
    assert result["locator_rate"] is True
    assert result["no_hallucination"] is True
    assert result["regression_passed"] is True
    assert checker.is_ready(ready_input) is True
    assert check_final_resilience(ready_input) is True

    not_ready = {
        "contract_valid": False,
        "metrics": {"evidence_coverage": 0.9, "locator_rate": 0.97},
    }
    assert checker.is_ready(not_ready) is False


def test_convenience_wrappers_delegate() -> None:
    e = normalize_entity("nt5e", "gene")
    assert e.normalized == "CD73"

    u = calibrate_uncertainty("likely no effect", 0.8)
    assert u.calibrated_confidence < 0.8
