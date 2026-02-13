from jarvis_core.ops_extract.contracts import OpsExtractThresholds
from jarvis_core.ops_extract.needs_ocr import decide_needs_ocr, unicode_category_distribution


def test_needs_ocr_when_total_chars_below_threshold():
    decision = decide_needs_ocr(
        total_chars_extracted=799,
        chars_per_page_mean=300.0,
        empty_page_ratio=0.0,
    )
    assert decision.needs_ocr is True
    assert decision.reason == "total_chars_below_threshold"


def test_needs_ocr_when_low_chars_and_high_empty_pages():
    decision = decide_needs_ocr(
        total_chars_extracted=2000,
        chars_per_page_mean=150.0,
        empty_page_ratio=0.8,
    )
    assert decision.needs_ocr is True
    assert decision.reason == "low_chars_and_high_empty_pages"


def test_needs_ocr_when_parser_exception_detected():
    thresholds = OpsExtractThresholds(
        min_total_chars=10,
        min_chars_per_page=1,
        empty_page_ratio_threshold=1.0,
    )
    decision = decide_needs_ocr(
        total_chars_extracted=100,
        chars_per_page_mean=100.0,
        empty_page_ratio=0.0,
        exceptions_in_text_extract=[{"category": "parser", "message": "extract failed"}],
        thresholds=thresholds,
    )
    assert decision.needs_ocr is True
    assert decision.reason == "extraction_exception_detected"


def test_needs_ocr_when_encoding_exception_detected():
    thresholds = OpsExtractThresholds(
        min_total_chars=10,
        min_chars_per_page=1,
        empty_page_ratio_threshold=1.0,
    )
    decision = decide_needs_ocr(
        total_chars_extracted=100,
        chars_per_page_mean=100.0,
        empty_page_ratio=0.0,
        exceptions_in_text_extract=[{"category": "encoding", "message": "unicode decode failed"}],
        thresholds=thresholds,
    )
    assert decision.needs_ocr is True
    assert decision.reason == "extraction_exception_detected"


def test_needs_ocr_when_unicode_distribution_is_anomalous():
    thresholds = OpsExtractThresholds(
        min_total_chars=10,
        min_chars_per_page=1,
        empty_page_ratio_threshold=1.0,
    )
    decision = decide_needs_ocr(
        total_chars_extracted=120,
        chars_per_page_mean=120.0,
        empty_page_ratio=0.0,
        unicode_distribution={
            "han": 0.0,
            "kana": 0.0,
            "latin": 0.0,
            "digit": 0.05,
            "other": 0.95,
        },
        thresholds=thresholds,
    )
    assert decision.needs_ocr is True
    assert decision.reason == "unicode_distribution_anomaly"


def test_needs_ocr_not_needed_when_metrics_good():
    decision = decide_needs_ocr(
        total_chars_extracted=5000,
        chars_per_page_mean=1000.0,
        empty_page_ratio=0.1,
    )
    assert decision.needs_ocr is False
    assert decision.reason == "not_needed"


def test_unicode_category_distribution_has_expected_keys():
    dist = unicode_category_distribution("漢字かなABC123")
    assert set(dist) == {"han", "kana", "latin", "digit", "other"}
