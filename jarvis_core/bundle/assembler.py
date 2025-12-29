"""Bundle Assembler - 10ファイル契約を必ず満たす (AG-02).

BUNDLE_CONTRACT.md準拠:
- 成功時: 10ファイル全て生成
- 失敗時: FAILURE_REQUIREDファイルは必ず生成
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List


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
        quality_report: Optional[dict] = None,
    ) -> List[str]:
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
        partial_artifacts: Optional[dict] = None,
        fail_reasons: Optional[List[dict]] = None,
    ) -> List[str]:
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
        quality_report: Optional[dict],
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


def export_evidence_bundle(result, store, output_dir: str) -> None:
    """
    Evidence Bundle をエクスポート.
    
    Args:
        result: EvidenceQAResult インスタンス
        store: EvidenceStore インスタンス
        output_dir: 出力ディレクトリパス
    """
    from ..integrations.notebooklm import export_notebooklm
    from ..integrations.obsidian import export_obsidian
    from ..integrations.notion import export_notion
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. bundle.json を作成
    bundle_data = result.to_dict()
    bundle_path = output_path / "bundle.json"
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle_data, f, indent=2, ensure_ascii=False)
    
    # 2. evidence/*.txt ファイルを作成
    evidence_dir = output_path / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    for citation in result.citations:
        chunk_id = citation.chunk_id
        # EvidenceStoreから実際のテキストを取得
        chunk = store.get_chunk(chunk_id)
        if chunk:
            # ファイル名を安全に生成
            filename = _safe_filename(f"{chunk_id}.txt")
            evidence_file = evidence_dir / filename
            
            # チャンクテキストを保存
            with open(evidence_file, "w", encoding="utf-8") as f:
                f.write(chunk.text)
    
    # 3. citations.md を作成
    citations_lines = [
        f"# Citations for Query: {result.query}",
        "",
        "## Answer",
        "",
        result.answer,
        "",
        "## Evidence",
        "",
    ]
    
    for i, citation in enumerate(result.citations, 1):
        chunk = store.get_chunk(citation.chunk_id)
        citations_lines.extend([
            f"### [{i}] {citation.source} - {citation.locator}",
            "",
            f"> {citation.quote}",
            "",
        ])
        if chunk:
            citations_lines.extend([
                "**Full Text:**",
                "",
                chunk.text,
                "",
            ])
    
    citations_path = output_path / "citations.md"
    with open(citations_path, "w", encoding="utf-8") as f:
        f.write("\n".join(citations_lines))
    
    # 4. notebooklm.md を作成
    references = []  # 空のreferencesリストを使用
    notebooklm_content = export_notebooklm(result, references, store)
    notebooklm_path = output_path / "notebooklm.md"
    with open(notebooklm_path, "w", encoding="utf-8") as f:
        f.write(notebooklm_content)
    
    # 5. obsidian/ ディレクトリを作成
    obsidian_dir = output_path / "obsidian"
    export_obsidian(result, references, str(obsidian_dir))
    
    # 6. notion.json を作成
    notion_content = export_notion(result, references)
    notion_path = output_path / "notion.json"
    with open(notion_path, "w", encoding="utf-8") as f:
        f.write(notion_content)
