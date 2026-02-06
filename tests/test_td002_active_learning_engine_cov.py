from __future__ import annotations

from typing import Any

import pytest

from jarvis_core.active_learning.engine import ALConfig, ALState, ALStats, ActiveLearningEngine


def _instances(n: int = 12) -> dict[str, list[float]]:
    return {f"id{i}": [float(i), float(i % 3)] for i in range(n)}


def test_alstats_to_dict_rounds_values() -> None:
    stats = ALStats(
        total_instances=10,
        labeled_instances=4,
        relevant_found=2,
        iterations=3,
        estimated_recall=0.4567,
    )
    data = stats.to_dict()
    assert data["estimated_recall"] == 0.457
    assert data["label_ratio"] == 0.4


def test_initialize_applies_seed_labels_and_feature_dim() -> None:
    engine = ActiveLearningEngine(ALConfig(initial_samples=2, batch_size=2))
    inst = _instances(6)
    engine.initialize(inst, seed_labels={"id0": 1, "id1": 0, "missing": 1})
    stats = engine.get_stats()
    assert stats.total_instances == 6
    assert stats.labeled_instances == 2
    assert stats.relevant_found == 1
    assert engine.state == ALState.IDLE


def test_get_next_query_returns_initial_samples_and_empty_when_done() -> None:
    engine = ActiveLearningEngine(ALConfig(initial_samples=4, batch_size=3))
    engine.initialize(_instances(4), seed_labels={"id0": 1})
    query = engine.get_next_query()
    assert 1 <= len(query) <= 3
    assert all(q.startswith("id") for q in query)

    # Exhaust unlabeled set
    for q in list(query):
        engine.update(q, 0)
    for q in list(engine.get_next_query(10)):
        engine.update(q, 0)
    assert engine.get_next_query() == []


def test_update_unknown_instance_is_noop() -> None:
    engine = ActiveLearningEngine()
    engine.initialize(_instances(3))
    before = engine.get_stats().labeled_instances
    engine.update("does-not-exist", 1)
    assert engine.get_stats().labeled_instances == before


def test_update_batch_updates_stats_and_iterations() -> None:
    engine = ActiveLearningEngine(ALConfig(initial_samples=2, batch_size=2))
    engine.initialize(_instances(5), seed_labels={"id0": 1})
    engine.update_batch({"id1": 0, "id2": 1})
    stats = engine.get_stats()
    assert stats.labeled_instances >= 3
    assert stats.relevant_found >= 2
    assert stats.iterations == 1


def test_uncertainty_sampling_handles_predict_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ActiveLearningEngine(ALConfig(initial_samples=1, batch_size=2))
    engine.initialize(_instances(4), seed_labels={"id0": 1})
    engine._model = object()

    def _fake_predict(features: list[float]) -> float:
        if features[0] == 2.0:
            raise RuntimeError("predict failed")
        return 0.6

    monkeypatch.setattr(engine, "_predict_proba", _fake_predict)
    picked = engine._uncertainty_sampling(2)
    assert len(picked) == 2


def test_predict_proba_none_and_exception_paths() -> None:
    engine = ActiveLearningEngine()
    assert engine._predict_proba([1.0, 2.0]) == 0.5

    class BadModel:
        def predict_proba(
            self, _x: Any
        ) -> Any:  # pragma: no cover - exercised through exception path
            raise RuntimeError("broken")

    engine._model = BadModel()
    assert engine._predict_proba([1.0, 2.0]) == 0.5


def test_train_model_import_error_path(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ActiveLearningEngine(ALConfig(initial_samples=1, batch_size=1))
    engine.initialize(_instances(3), seed_labels={"id0": 1, "id1": 0})
    engine._labels["id2"] = 0

    original_import = __import__

    def _fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("numpy") or name.startswith("sklearn"):
            raise ImportError("forced import error")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _fake_import)
    engine._train_model()
    assert engine.state == ALState.IDLE


def test_should_stop_by_max_iterations_budget_and_empty() -> None:
    cfg = ALConfig(max_iterations=3, budget_ratio=0.3, initial_samples=1, batch_size=1)
    engine = ActiveLearningEngine(cfg)
    engine.initialize(_instances(10), seed_labels={"id0": 1})

    engine._iteration = 3
    assert engine.should_stop() is True

    engine = ActiveLearningEngine(cfg)
    engine.initialize(_instances(10), seed_labels={"id0": 1, "id1": 0, "id2": 0})
    assert engine.should_stop() is True

    engine = ActiveLearningEngine(cfg)
    engine.initialize({"id0": [0.0]}, seed_labels={"id0": 1})
    assert engine.should_stop() is True


def test_should_stop_on_target_recall_after_min_iterations(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ALConfig(target_recall=0.8, initial_samples=1, batch_size=1, budget_ratio=1.0)
    engine = ActiveLearningEngine(cfg)
    engine.initialize(_instances(4), seed_labels={"id0": 1})
    engine._iteration = 5
    monkeypatch.setattr(engine, "_estimate_recall", lambda: 0.9)
    assert engine.should_stop() is True
    assert engine.state == ALState.STOPPED


def test_estimate_recall_and_predictions_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ActiveLearningEngine(ALConfig(initial_samples=1, batch_size=1))
    engine.initialize(_instances(4), seed_labels={"id0": 1, "id1": 0})
    engine._model = object()
    monkeypatch.setattr(engine, "_predict_proba", lambda _features: 0.75)
    recall = engine._estimate_recall()
    preds = engine.get_predictions()
    assert recall > 0
    assert preds
