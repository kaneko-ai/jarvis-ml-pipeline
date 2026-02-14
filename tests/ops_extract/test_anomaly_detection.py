from __future__ import annotations

from pathlib import Path

from jarvis_core.ops_extract.scoreboard import detect_anomalies


def test_anomaly_detection_triggers_on_low_scores():
    anomalies = detect_anomalies(runs=[Path("r1")], ops_score=70.0, extract_score=72.0)
    assert "OPS_SCORE_BELOW_85" in anomalies
    assert "EXTRACT_SCORE_BELOW_85" in anomalies
