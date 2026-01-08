"""Bundle Assembler - 10ファイル契約を必ず満たす (AG-02).

BUNDLE_CONTRACT.md準拠:
- 成功時: 10ファイル全て生成
- 失敗時: FAILURE_REQUIREDファイルは必ず生成
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class BundleAssembler:
    """10ファイル契約を必ず満たすBundle生成器.
    
    使用法:
        assembler = BundleAssembler(store)
        assembler.build(context, artifacts)  # 成功時
        assembler.build_failure(context, error, partial)  # 失敗時
    """

    # 必須10ファイル（BUNDLE_CONTRACT.md準拠）
    REQUIRED_ARTIFACTS = [
        "input.json",
        "run_config.json",
        "papers.jsonl",
        "claims.jsonl",
        "evidence.jsonl",
        "scores.json",
        "result.json",
        "eval_summary.json",
        "warnings.jsonl",
        "report.md",
    ]

    # 失敗時必須ファイル
    FAILURE_REQUIRED = [
        "result.json",
        "eval_summary.json",
        "warnings.jsonl",
        "report.md",
    ]

    def __init__(self, run_dir: Path):
        """初期化.
        
        Args:
            run_dir: runの出力ディレクトリ (logs/runs/{run_id}/)
        """
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        context: dict,
        artifacts: dict,
        quality_report: dict | None = None,
    ) -> list[str]:
        """成功時のBundle生成（10ファイル全て）.
        
        Args:
            context: 実行コンテキスト
                - run_id: str
                - goal: str
                - query: str
                - pipeline: str
                - timestamp: str
            artifacts: 収集された成果物
                - papers: list[dict]
                - claims: list[dict]
                - evidence: list[dict]
                - answer: str
                - citations: list[dict]
                - warnings: list[dict]
            quality_report: 品質評価結果（オプション）
                
        Returns:
            生成されたファイルのリスト
        """
        generated = []

        # 1. input.json
        self._save_json("input.json", {
            "goal": context.get("goal", ""),
            "query": context.get("query", context.get("goal", "")),
            "constraints": context.get("constraints", {}),
            "timestamp": context.get("timestamp", datetime.now(timezone.utc).isoformat()),
        })
        generated.append("input.json")

        # 2. run_config.json
        self._save_json("run_config.json", {
            "run_id": context.get("run_id", "unknown"),
            "pipeline": context.get("pipeline", "default"),
            "timestamp": context.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "seed": context.get("seed", 42),
            "model": context.get("model", "unknown"),
        })
        generated.append("run_config.json")

        # 3. papers.jsonl
        papers = artifacts.get("papers", [])
        self._save_jsonl("papers.jsonl", self._ensure_paper_schema(papers))
        generated.append("papers.jsonl")

        # 4. claims.jsonl
        claims = artifacts.get("claims", [])
        self._save_jsonl("claims.jsonl", self._ensure_claim_schema(claims))
        generated.append("claims.jsonl")

        # 5. evidence.jsonl
        evidence = artifacts.get("evidence", [])
        self._save_jsonl("evidence.jsonl", self._ensure_evidence_schema(evidence))
        generated.append("evidence.jsonl")

        # 6. scores.json
        scores = artifacts.get("scores", {})
        self._save_json("scores.json", self._ensure_scores_schema(scores))
        generated.append("scores.json")

        # 7. result.json
        result = self._build_result(context, artifacts)
        self._save_json("result.json", result)
        generated.append("result.json")

        # 8. eval_summary.json
        eval_summary = self._build_eval_summary(context, artifacts, quality_report)
        self._save_json("eval_summary.json", eval_summary)
        generated.append("eval_summary.json")

        # 9. warnings.jsonl
        warnings = artifacts.get("warnings", [])
        self._save_jsonl("warnings.jsonl", self._ensure_warning_schema(warnings))
        generated.append("warnings.jsonl")

        # 10. report.md
        report = self._build_report(context, artifacts, eval_summary)
        self._save_text("report.md", report)
        generated.append("report.md")

        return generated

    def build_failure(
        self,
        context: dict,
        error: str,
        partial_artifacts: dict | None = None,
        fail_reasons: list[dict] | None = None,
    ) -> list[str]:
        """失敗時のBundle生成（FAILURE_REQUIREDのみ）.
        
        Args:
            context: 実行コンテキスト
            error: エラーメッセージ
            partial_artifacts: 途中まで収集された成果物
            fail_reasons: 失敗理由のリスト
                
        Returns:
            生成されたファイルのリスト
        """
        generated = []
        partial = partial_artifacts or {}

        # input.json（あれば生成）
        if context.get("goal") or context.get("query"):
            self._save_json("input.json", {
                "goal": context.get("goal", ""),
                "query": context.get("query", context.get("goal", "")),
                "constraints": context.get("constraints", {}),
                "timestamp": context.get("timestamp", datetime.now(timezone.utc).isoformat()),
            })
            generated.append("input.json")

        # run_config.json（最低限）
        self._save_json("run_config.json", {
            "run_id": context.get("run_id", "unknown"),
            "pipeline": context.get("pipeline", "default"),
            "timestamp": context.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "status": "failed",
        })
        generated.append("run_config.json")

        # result.json（FAILURE_REQUIRED）
        result = {
            "run_id": context.get("run_id", "unknown"),
            "task_id": context.get("task_id", "unknown"),
            "status": "failed",
            "answer": "",
            "citations": [],
            "warnings": [{"code": "EXECUTION_ERROR", "message": error, "severity": "error"}],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._save_json("result.json", result)
        generated.append("result.json")

        # eval_summary.json（FAILURE_REQUIRED）
        reasons = fail_reasons or [{"code": "EXECUTION_ERROR", "msg": error}]
        eval_summary = {
            "run_id": context.get("run_id", "unknown"),
            "status": "fail",
            "gate_passed": False,
            "fail_reasons": reasons,
            "metrics": {
                "citation_count": 0,
                "evidence_coverage": 0.0,
                "warning_count": 1,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._save_json("eval_summary.json", eval_summary)
        generated.append("eval_summary.json")

        # warnings.jsonl（FAILURE_REQUIRED）
        warnings = partial.get("warnings", [])
        warnings.append({
            "code": "EXECUTION_ERROR",
            "message": error,
            "severity": "error",
        })
        self._save_jsonl("warnings.jsonl", self._ensure_warning_schema(warnings))
        generated.append("warnings.jsonl")

        # report.md（FAILURE_REQUIRED）
        report = self._build_failure_report(context, error, reasons)
        self._save_text("report.md", report)
        generated.append("report.md")

        return generated

    # === Schema Enforcers ===

    def _ensure_paper_schema(self, papers: list) -> list:
        """papers.jsonlの必須キーを保証."""
        result = []
        for i, p in enumerate(papers):
            result.append({
                "paper_id": p.get("paper_id", f"paper_{i}"),
                "title": p.get("title", "Untitled"),
                "year": p.get("year", 0),
                **{k: v for k, v in p.items() if k not in ["paper_id", "title", "year"]}
            })
        return result

    def _ensure_claim_schema(self, claims: list) -> list:
        """claims.jsonlの必須キーを保証."""
        result = []
        for i, c in enumerate(claims):
            result.append({
                "claim_id": c.get("claim_id", f"claim_{i}"),
                "paper_id": c.get("paper_id", "unknown"),
                "claim_text": c.get("claim_text", c.get("text", "")),
                **{k: v for k, v in c.items() if k not in ["claim_id", "paper_id", "claim_text"]}
            })
        return result

    def _ensure_evidence_schema(self, evidence: list) -> list:
        """evidence.jsonlの必須キーを保証."""
        result = []
        for i, e in enumerate(evidence):
            locator = e.get("locator", {})
            if isinstance(locator, str):
                locator = {"section": locator, "paragraph": 0}
            result.append({
                "claim_id": e.get("claim_id", f"claim_{i}"),
                "paper_id": e.get("paper_id", "unknown"),
                "evidence_text": e.get("evidence_text", e.get("text", "")),
                "locator": locator,
                **{k: v for k, v in e.items() if k not in ["claim_id", "paper_id", "evidence_text", "locator"]}
            })
        return result

    def _ensure_scores_schema(self, scores: dict) -> dict:
        """scores.jsonの必須キーを保証."""
        return {
            "features": scores.get("features", {}),
            "rankings": scores.get("rankings", []),
            **{k: v for k, v in scores.items() if k not in ["features", "rankings"]}
        }

    def _ensure_warning_schema(self, warnings: list) -> list:
        """warnings.jsonlの必須キーを保証."""
        result = []
        for w in warnings:
            if isinstance(w, str):
                w = {"code": "GENERAL", "message": w, "severity": "warning"}
            result.append({
                "code": w.get("code", "GENERAL"),
                "message": w.get("message", str(w)),
                "severity": w.get("severity", "warning"),
            })
        return result

    # === Builders ===

    def _build_result(self, context: dict, artifacts: dict) -> dict:
        """result.jsonを構築."""
        return {
            "run_id": context.get("run_id", "unknown"),
            "task_id": context.get("task_id", context.get("run_id", "unknown")),
            "status": "success",
            "answer": artifacts.get("answer", ""),
            "citations": artifacts.get("citations", []),
            "warnings": [w.get("message", str(w)) if isinstance(w, dict) else w
                        for w in artifacts.get("warnings", [])],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _build_eval_summary(
        self,
        context: dict,
        artifacts: dict,
        quality_report: dict | None,
    ) -> dict:
        """eval_summary.jsonを構築."""
        citations = artifacts.get("citations", [])
        evidence = artifacts.get("evidence", [])
        warnings = artifacts.get("warnings", [])
        feedback_risk = artifacts.get("feedback_risk") or {}

        # メトリクス計算
        citation_count = len(citations)
        evidence_count = len(evidence)
        warning_count = len(warnings)

        # locator欠落チェック
        locator_missing = sum(
            1 for e in evidence
            if not e.get("locator") or (isinstance(e.get("locator"), dict) and not e["locator"].get("section"))
        )

        # 品質ゲート判定
        gate_passed = True
        fail_reasons = []

        if citation_count == 0:
            gate_passed = False
            fail_reasons.append({"code": "CITATION_MISSING", "msg": "引用がゼロ"})

        if locator_missing > 0:
            gate_passed = False
            fail_reasons.append({"code": "LOCATOR_MISSING", "msg": f"根拠位置情報がない: {locator_missing}件"})

        # 外部品質レポートがあれば統合
        if quality_report:
            if not quality_report.get("gate_passed", True):
                gate_passed = False
            fail_reasons.extend(quality_report.get("fail_reasons", []))

        feedback_summary = feedback_risk.get("summary") if isinstance(feedback_risk, dict) else None
        ready_to_submit = True
        ready_with_risk = False
        if feedback_summary:
            ready_to_submit = feedback_summary.get("ready_to_submit", True)
            ready_with_risk = feedback_summary.get("ready_with_risk", False)

        return {
            "run_id": context.get("run_id", "unknown"),
            "status": "pass" if gate_passed else "fail",
            "gate_passed": gate_passed,
            "fail_reasons": fail_reasons,
            "ready_to_submit": ready_to_submit,
            "ready_with_risk": ready_with_risk,
            "feedback_risk": feedback_summary,
            "metrics": {
                "citation_count": citation_count,
                "evidence_count": evidence_count,
                "evidence_coverage": evidence_count / max(citation_count, 1),
                "warning_count": warning_count,
                "locator_missing": locator_missing,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _build_report(self, context: dict, artifacts: dict, eval_summary: dict) -> str:
        """report.mdを構築."""
        lines = [
            f"# Run Report: {context.get('run_id', 'unknown')}",
            "",
            f"**Goal:** {context.get('goal', 'N/A')}",
            "",
            f"**Status:** {eval_summary.get('status', 'unknown')}",
            "",
            f"**Gate Passed:** {'✅' if eval_summary.get('gate_passed') else '❌'}",
            "",
            "---",
            "",
            "## Metrics",
            "",
        ]

        metrics = eval_summary.get("metrics", {})
        for key, value in metrics.items():
            lines.append(f"- **{key}:** {value}")

        feedback_summary = eval_summary.get("feedback_risk")
        if feedback_summary:
            lines.extend(["", "## Feedback Risk Summary", ""])
            lines.append(f"- **High:** {feedback_summary.get('high', 0)}")
            lines.append(f"- **Medium:** {feedback_summary.get('medium', 0)}")
            lines.append(f"- **Low:** {feedback_summary.get('low', 0)}")
            top_categories = ", ".join(feedback_summary.get("top_categories", []))
            lines.append(f"- **Top Categories:** {top_categories or 'N/A'}")
            lines.append(f"- **Ready to Submit:** {eval_summary.get('ready_to_submit', True)}")

        lines.extend(["", "---", "", "## Answer", "", artifacts.get("answer", "(no answer)"), ""])

        # Fail reasons
        fail_reasons = eval_summary.get("fail_reasons", [])
        if fail_reasons:
            lines.extend(["", "## ⚠️ Issues", ""])
            for fr in fail_reasons:
                code = fr.get("code", "UNKNOWN")
                msg = fr.get("msg", str(fr))
                lines.append(f"- **{code}:** {msg}")

        lines.extend(["", "---", "", f"*Generated at {datetime.now(timezone.utc).isoformat()}*"])

        return "\n".join(lines)

    def _build_failure_report(self, context: dict, error: str, reasons: list) -> str:
        """失敗時のreport.mdを構築."""
        lines = [
            f"# Run Report: {context.get('run_id', 'unknown')} (FAILED)",
            "",
            f"**Goal:** {context.get('goal', 'N/A')}",
            "",
            "**Status:** ❌ FAILED",
            "",
            "---",
            "",
            "## Error",
            "",
            f"```\n{error}\n```",
            "",
            "## Fail Reasons",
            "",
        ]

        for fr in reasons:
            code = fr.get("code", "UNKNOWN")
            msg = fr.get("msg", str(fr))
            lines.append(f"- **{code}:** {msg}")

        lines.extend(["", "---", "", f"*Generated at {datetime.now(timezone.utc).isoformat()}*"])

        return "\n".join(lines)

    # === I/O ===

    def _save_json(self, filename: str, data: dict) -> None:
        """JSONファイルを保存."""
        filepath = self.run_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_jsonl(self, filename: str, items: list) -> None:
        """JSONLファイルを保存."""
        filepath = self.run_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def _save_text(self, filename: str, content: str) -> None:
        """テキストファイルを保存."""
        filepath = self.run_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


def _safe_filename(name: str, max_len: int = 50) -> str:
    """
    ファイル名を安全な形式に変換.
    
    Args:
        name: 元のファイル名
        max_len: 最大長
        
    Returns:
        安全なファイル名
    """
    # 危険な文字を置換
    safe = str(name)
    for char in '<>:"/\\|?*':
        safe = safe.replace(char, "_")

    # 長さ制限
    if len(safe) > max_len:
        safe = safe[:max_len]

    return safe


def export_evidence_bundle(
    result,
    store,
    output_dir: str,
    ref_style: str = "vancouver",
) -> str:
    """
    Evidence Bundle をエクスポート.

    必須出力:
    - bundle.json（references/claims/exports/metrics を含む）
    - references.md
    - references.bib
    - references.ris
    - claims.md（claimsがある場合）
    """
    from ..bibtex import export_bibtex
    from ..claim_export import (
        export_claims_json,
        export_claims_markdown,
        export_claims_pptx_outline,
    )
    from ..integrations.notebooklm import export_notebooklm
    from ..integrations.notion import export_notion
    from ..integrations.obsidian import export_obsidian
    from ..reference import extract_references
    from ..reference_formatter import format_references_markdown
    from ..ris import export_ris

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    references = extract_references(result.citations, store)
    claims = result.claims if getattr(result, "claims", None) is not None else None

    style = "apa" if ref_style.lower() == "apa" else "vancouver"
    exports: dict[str, str] = {}

    metrics = {
        "citations": len(result.citations),
        "references": len(references),
        "claims": len(claims.claims) if claims and hasattr(claims, "claims") else 0,
        "chunks_used": len(result.chunks_used),
    }

    # 1. bundle.json を作成
    bundle_data = result.to_dict()
    bundle_data["references"] = [r.to_dict() for r in references]
    bundle_data["claims"] = claims.to_dict() if hasattr(claims, "to_dict") else claims
    bundle_data["exports"] = exports
    bundle_data["metrics"] = metrics
    bundle_path = output_path / "bundle.json"
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle_data, f, indent=2, ensure_ascii=False)
    exports["bundle_json"] = "bundle.json"

    # 2. evidence/*.txt ファイルを作成
    evidence_dir = output_path / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    for chunk_id in result.chunks_used:
        chunk = store.get_chunk(chunk_id)
        if chunk:
            filename = _safe_filename(f"{chunk_id}.txt")
            evidence_file = evidence_dir / filename
            with open(evidence_file, "w", encoding="utf-8") as f:
                content = f"# Chunk: {chunk_id}\n"
                content += f"Source: {chunk.source}\n"
                content += f"Locator: {chunk.locator}\n"
                content += f"\n---\n\n{chunk.text}"
                f.write(content)
    exports["evidence_dir"] = "evidence/"

    # 3. citations.md を作成
    citations_md = _generate_citations_md(result, store)
    citations_path = output_path / "citations.md"
    with open(citations_path, "w", encoding="utf-8") as f:
        f.write(citations_md)
    exports["citations_md"] = "citations.md"

    # 4. references.md を作成
    refs_md = format_references_markdown(references, style=style)
    refs_path = output_path / "references.md"
    with open(refs_path, "w", encoding="utf-8") as f:
        f.write(refs_md)
    exports["references_md"] = "references.md"

    # 5. references.bib を作成
    bibtex_content = export_bibtex(references)
    bibtex_path = output_path / "references.bib"
    with open(bibtex_path, "w", encoding="utf-8") as f:
        f.write(bibtex_content)
    exports["references_bib"] = "references.bib"

    # 6. references.ris を作成
    ris_content = export_ris(references)
    ris_path = output_path / "references.ris"
    with open(ris_path, "w", encoding="utf-8") as f:
        f.write(ris_content)
    exports["references_ris"] = "references.ris"

    # 7. Claims 出力
    if claims is not None:
        claims_md = export_claims_markdown(claims, references)
        claims_md_path = output_path / "claims.md"
        with open(claims_md_path, "w", encoding="utf-8") as f:
            f.write(claims_md)
        exports["claims_md"] = "claims.md"

        claims_json = export_claims_json(claims, references)
        claims_json_path = output_path / "claims.json"
        with open(claims_json_path, "w", encoding="utf-8") as f:
            f.write(claims_json)
        exports["claims_json"] = "claims.json"

        slides_outline = export_claims_pptx_outline(claims, references, title=result.query)
        slides_path = output_path / "slides_outline.txt"
        with open(slides_path, "w", encoding="utf-8") as f:
            f.write(slides_outline)
        exports["slides_outline"] = "slides_outline.txt"

    # 8. Knowledge Tool Integrations
    notebooklm_content = export_notebooklm(result, references, store)
    notebooklm_path = output_path / "notebooklm.md"
    with open(notebooklm_path, "w", encoding="utf-8") as f:
        f.write(notebooklm_content)
    exports["notebooklm_md"] = "notebooklm.md"

    obsidian_dir = output_path / "obsidian"
    export_obsidian(result, references, str(obsidian_dir))
    exports["obsidian_dir"] = "obsidian/"

    notion_content = export_notion(result, references)
    notion_path = output_path / "notion.json"
    with open(notion_path, "w", encoding="utf-8") as f:
        f.write(notion_content)
    exports["notion_json"] = "notion.json"

    # bundle.json の exports/metrics 更新
    bundle_data["exports"] = exports
    bundle_data["metrics"] = metrics
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle_data, f, indent=2, ensure_ascii=False)

    return str(output_path)


def _generate_citations_md(result, store) -> str:
    """Generate human-readable citations markdown."""
    lines = [
        "# Citations",
        "",
        f"**Query:** {result.query}",
        "",
        f"**Status:** {result.status}",
        "",
        "---",
        "",
        "## Answer",
        "",
        result.answer,
        "",
        "---",
        "",
    ]

    if result.claims is not None and hasattr(result.claims, "claims"):
        lines.append("## Claims")
        lines.append("")

        for i, claim in enumerate(result.claims.claims, 1):
            status_mark = "✓" if claim.valid else "✗"
            lines.append(f"### {status_mark} Claim {i}")
            lines.append("")
            lines.append(f"**Text:** {claim.text}")
            lines.append("")
            lines.append(f"**Citations:** {', '.join(claim.citations) or '(none)'}")
            lines.append("")
            if not claim.valid and claim.validation_notes:
                lines.append(f"**Notes:** {', '.join(claim.validation_notes)}")
                lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("## Evidence Used")
    lines.append("")

    for i, citation in enumerate(result.citations, 1):
        chunk = store.get_chunk(citation.chunk_id)
        quote = citation.quote if citation.quote else "(quote not available)"

        lines.append(f"### [{i}] {citation.locator}")
        lines.append("")
        lines.append(f"**Chunk ID:** `{citation.chunk_id}`")
        lines.append("")
        lines.append(f"**Source:** {citation.source}")
        lines.append("")
        lines.append(f"**Quote:** {quote}")
        lines.append("")
        if chunk:
            preview = chunk.text[:200]
            if len(chunk.text) > 200:
                preview += "..."
            lines.append(f"**Context:** {preview}")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Inputs")
    lines.append("")
    for inp in result.inputs:
        lines.append(f"- {inp}")
    lines.append("")

    lines.append("## Metadata")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(result.meta, indent=2, ensure_ascii=False))
    lines.append("```")

    return "\n".join(lines)
