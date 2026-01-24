from jarvis_core.eval.drift import (
    entity_distribution,
    kl_divergence,
    js_divergence,
    detect_drift,
    format_drift_report,
)


def test_entity_distribution():
    entities = ["A", "B", "A", "C"]
    dist = entity_distribution(entities)
    assert dist["A"] == 0.5
    assert dist["B"] == 0.25
    assert dist["C"] == 0.25
    assert entity_distribution([]) == {}


def test_kl_divergence():
    p = {"A": 0.5, "B": 0.5}
    q = {"A": 0.5, "B": 0.5}
    assert kl_divergence(p, q) == 0.0

    q2 = {"A": 0.9, "B": 0.1}
    assert kl_divergence(p, q2) > 0.0

    # Smooth handling
    assert kl_divergence(p, {}) == 0.0


def test_js_divergence():
    p = {"A": 1.0}
    q = {"B": 1.0}
    res = js_divergence(p, q)
    assert 0.6 < res < 0.8  # approx log(2)
    assert js_divergence(p, p) == 0.0


def test_detect_drift():
    baseline = ["Apple", "Apple", "Banana"]
    current = ["Apple", "Orange", "Orange"]

    res = detect_drift(current, baseline, threshold=0.01)
    assert res.drifted is True
    assert len(res.top_gains) > 0
    assert any(item[0] == "Orange" for item in res.top_gains)
    assert any(item[0] == "Banana" for item in res.top_losses)


def test_format_drift_report():
    baseline = ["A"]
    current = ["B"]
    res = detect_drift(current, baseline)
    report = format_drift_report(res)
    assert "# Drift Report" in report
    assert "KL Divergence" in report

    # Test top losses in report
    assert "Top Losses" in report
    assert "A:" in report
