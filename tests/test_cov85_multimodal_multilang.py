from __future__ import annotations

from jarvis_core.multimodal.multilang import Language, MultiLanguageSupport, MultilingualPaper


def test_detect_language_heuristics() -> None:
    support = MultiLanguageSupport()
    assert support.detect_language("これはテストです") == Language.JAPANESE
    assert support.detect_language("中文测试") == Language.CHINESE
    assert support.detect_language("한국어 테스트") == Language.KOREAN
    assert support.detect_language("plain english") == Language.ENGLISH


def test_translate_paths_with_and_without_translator() -> None:
    support = MultiLanguageSupport()

    same = support.translate("hello", source=Language.ENGLISH, target=Language.ENGLISH)
    assert same.translated_text == "hello"
    assert same.confidence == 1.0

    placeholder = support.translate("bonjour", source=Language.FRENCH, target=Language.ENGLISH)
    assert placeholder.translated_text.startswith("[Translation of:")
    assert placeholder.confidence == 0.5

    def _translator(text: str, source: str, target: str) -> str:
        return f"{source}->{target}:{text}"

    support2 = MultiLanguageSupport(translator=_translator)
    translated = support2.translate("hola", source=Language.SPANISH, target=Language.ENGLISH)
    assert translated.translated_text == "es->en:hola"
    assert translated.confidence == 0.9


def test_process_paper_and_cross_language_search() -> None:
    support = MultiLanguageSupport()

    paper = support.process_paper("p1", "日本語タイトル", "日本語要約")
    assert paper.primary_language == Language.JAPANESE
    assert Language.ENGLISH in paper.available_languages

    en_paper = MultilingualPaper(
        paper_id="p2",
        title={Language.ENGLISH: "Cancer Immunity"},
        abstract={Language.ENGLISH: "Tumor microenvironment study"},
        primary_language=Language.ENGLISH,
        available_languages=[Language.ENGLISH],
    )

    results = support.cross_language_search("tumor", [paper, en_paper])
    assert [p.paper_id for p in results] == ["p2"]

    ja_results = support.cross_language_search("日本語", [paper], target_language=Language.JAPANESE)
    assert [p.paper_id for p in ja_results] == ["p1"]
