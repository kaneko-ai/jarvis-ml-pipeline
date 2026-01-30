"""Checklist rules for lab submission QA."""

from __future__ import annotations

CHECKLISTS = [
    {
        "id": "no_term_variants",
        "description": "用語揺れゼロ",
        "check": lambda qa: qa.get("counts", {}).get("term_variant", 0) == 0,
    },
    {
        "id": "fcm_format",
        "description": "FCM表現がラボ規約どおり",
        "check": lambda qa: qa.get("counts", {}).get("abbrev_missing", 0) == 0,
    },
    {
        "id": "dose_dependent",
        "description": "濃度依存的表現が統一",
        "check": lambda qa: _dose_dependent_consistent(qa.get("normalized_text", {})),
    },
    {
        "id": "references_present",
        "description": "参考文献根拠が各段落に付与されている",
        "check": lambda qa: qa.get("counts", {}).get("missing_reference", 0) == 0,
    },
    {
        "id": "conclusion_minimum",
        "description": "Conclusion節に最低3文以上",
        "check": lambda qa: qa.get("conclusion_sentences", 0) >= 3,
    },
]


def _dose_dependent_consistent(normalized_text: dict[str, object]) -> bool:
    combined = " ".join(str(value) for value in normalized_text.values())
    if "濃度依存" not in combined:
        return True
    return "濃度依存的" in combined and "濃度依存性" not in combined


def run_checklists(qa_result: dict[str, object]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for item in CHECKLISTS:
        passed = item["check"](qa_result)
        results.append(
            {
                "id": item["id"],
                "description": item["description"],
                "passed": passed,
            }
        )
    return results