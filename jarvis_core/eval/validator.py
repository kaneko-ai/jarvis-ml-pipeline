"""Validator (Q-02).

品質検証ツール群:
- スキーマ検証
- 根拠カバレッジ検証
- ハルシネーション検出
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """検証結果."""
    passed: bool = True
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, code: str, message: str, **kwargs):
        self.passed = False
        self.errors.append({"code": code, "message": message, **kwargs})
    
    def add_warning(self, code: str, message: str, **kwargs):
        self.warnings.append({"code": code, "message": message, **kwargs})
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


class SchemaValidator:
    """スキーマ検証器.
    
    Bundle契約のスキーマを検証。
    """
    
    # 必須キー定義（BUNDLE_CONTRACT.md準拠）
    REQUIRED_KEYS = {
        "input.json": ["goal", "query", "constraints"],
        "run_config.json": ["run_id", "pipeline", "timestamp"],
        "papers.jsonl": ["paper_id", "title", "year"],
        "claims.jsonl": ["claim_id", "paper_id", "claim_text"],
        "evidence.jsonl": ["claim_id", "paper_id", "evidence_text", "locator"],
        "scores.json": ["features", "rankings"],
        "result.json": ["run_id", "status", "answer", "citations"],
        "eval_summary.json": ["gate_passed", "fail_reasons", "metrics"],
        "warnings.jsonl": ["code", "message", "severity"],
    }
    
    def validate_file(self, filepath: Path) -> ValidationResult:
        """単一ファイルのスキーマを検証."""
        result = ValidationResult()
        filename = filepath.name
        
        if not filepath.exists():
            result.add_error("FILE_MISSING", f"File not found: {filename}")
            return result
        
        if filename not in self.REQUIRED_KEYS:
            # スキーマ定義なし（report.md等）
            return result
        
        required = self.REQUIRED_KEYS[filename]
        
        try:
            if filename.endswith(".jsonl"):
                with open(filepath, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if not first_line:
                        result.add_warning("EMPTY_FILE", f"File is empty: {filename}")
                        return result
                    data = json.loads(first_line)
            else:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            
            missing = [k for k in required if k not in data]
            if missing:
                result.add_error(
                    "MISSING_KEYS",
                    f"Missing required keys in {filename}: {missing}",
                    filename=filename,
                    missing_keys=missing,
                )
        except json.JSONDecodeError as e:
            result.add_error("INVALID_JSON", f"Invalid JSON in {filename}: {e}")
        except Exception as e:
            result.add_error("READ_ERROR", f"Error reading {filename}: {e}")
        
        return result
    
    def validate_bundle(self, run_dir: Path) -> ValidationResult:
        """Bundleディレクトリ全体を検証."""
        result = ValidationResult()
        
        for filename in self.REQUIRED_KEYS:
            file_result = self.validate_file(run_dir / filename)
            result.errors.extend(file_result.errors)
            result.warnings.extend(file_result.warnings)
            if not file_result.passed:
                result.passed = False
        
        return result


class EvidenceCoverageValidator:
    """根拠カバレッジ検証器.
    
    主張に対する根拠のカバレッジを検証。
    """
    
    def __init__(self, min_coverage: float = 0.95):
        self.min_coverage = min_coverage
    
    def validate(
        self,
        claims: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> ValidationResult:
        """カバレッジを検証."""
        result = ValidationResult()
        
        if not claims:
            result.add_warning("NO_CLAIMS", "No claims to validate")
            return result
        
        # 各主張に対する根拠を集計
        evidence_by_claim = {}
        for ev in evidence:
            claim_id = ev.get("claim_id", "")
            if claim_id not in evidence_by_claim:
                evidence_by_claim[claim_id] = []
            evidence_by_claim[claim_id].append(ev)
        
        # カバレッジ計算
        covered = 0
        uncovered_claims = []
        
        for claim in claims:
            claim_id = claim.get("claim_id", "")
            if claim_id in evidence_by_claim and len(evidence_by_claim[claim_id]) > 0:
                covered += 1
            else:
                uncovered_claims.append(claim_id)
        
        coverage = covered / len(claims) if claims else 0
        
        result.metrics = {
            "total_claims": len(claims),
            "covered_claims": covered,
            "coverage": coverage,
            "uncovered_claims": uncovered_claims[:5],  # 最大5件
        }
        
        if coverage < self.min_coverage:
            result.add_error(
                "LOW_COVERAGE",
                f"Evidence coverage {coverage:.2%} < {self.min_coverage:.2%}",
                coverage=coverage,
                threshold=self.min_coverage,
            )
        
        return result


class LocatorValidator:
    """Locator検証器.
    
    根拠のlocator（位置情報）を検証。
    """
    
    def validate(self, evidence: List[Dict[str, Any]]) -> ValidationResult:
        """Locatorを検証."""
        result = ValidationResult()
        
        if not evidence:
            return result
        
        missing_locator = 0
        invalid_locator = 0
        
        for ev in evidence:
            locator = ev.get("locator")
            
            if not locator:
                missing_locator += 1
            elif isinstance(locator, dict):
                if not locator.get("section"):
                    invalid_locator += 1
            else:
                invalid_locator += 1
        
        result.metrics = {
            "total_evidence": len(evidence),
            "missing_locator": missing_locator,
            "invalid_locator": invalid_locator,
        }
        
        if missing_locator > 0:
            result.add_error(
                "LOCATOR_MISSING",
                f"{missing_locator}/{len(evidence)} evidence missing locator",
            )
        
        if invalid_locator > 0:
            result.add_warning(
                "LOCATOR_INVALID",
                f"{invalid_locator}/{len(evidence)} evidence have invalid locator",
            )
        
        return result


class HallucinationValidator:
    """ハルシネーション検証器.
    
    回答内の主張が根拠に裏付けられているか検証。
    """
    
    def validate(
        self,
        answer: str,
        evidence: List[Dict[str, Any]],
        claims: List[Dict[str, Any]],
    ) -> ValidationResult:
        """ハルシネーションを検証."""
        result = ValidationResult()
        
        if not answer:
            return result
        
        # 簡易的な検証：回答に含まれるキーワードが根拠にあるか
        # 本番では LLM を使用した検証が必要
        
        evidence_texts = " ".join([e.get("evidence_text", "") for e in evidence])
        claim_texts = " ".join([c.get("claim_text", "") for c in claims])
        all_context = evidence_texts + " " + claim_texts
        
        # 回答から断言的な文を抽出
        import re
        assertions = re.findall(r'[^.!?]*(?:is|are|was|were|has|have|show|demonstrate)[^.!?]*[.!?]', answer.lower())
        
        unsupported = []
        for assertion in assertions[:10]:  # 最大10件チェック
            # キーワード抽出
            words = re.findall(r'\b[a-z]{4,}\b', assertion)
            key_words = [w for w in words if w not in {'this', 'that', 'these', 'those', 'have', 'does', 'were', 'there', 'their', 'which'}]
            
            # 根拠でカバーされているか
            covered = sum(1 for w in key_words if w in all_context.lower())
            if key_words and covered / len(key_words) < 0.3:
                unsupported.append(assertion[:100])
        
        result.metrics = {
            "assertions_checked": len(assertions),
            "unsupported_count": len(unsupported),
        }
        
        if unsupported:
            result.add_warning(
                "POTENTIAL_HALLUCINATION",
                f"{len(unsupported)} assertions may lack evidence support",
                examples=unsupported[:3],
            )
        
        return result


class GoldenSetValidator:
    """Golden Set検証器.
    
    Golden Setに対する品質を検証。
    """
    
    def __init__(self, golden_path: Path):
        self.golden_path = golden_path
        self._load_golden()
    
    def _load_golden(self):
        """Golden Setを読み込み."""
        self.golden = {}
        if self.golden_path.exists():
            try:
                with open(self.golden_path, "r", encoding="utf-8") as f:
                    self.golden = json.load(f)
            except:
                pass
    
    def validate_run(
        self,
        run_result: Dict[str, Any],
        question_id: str,
    ) -> ValidationResult:
        """runをGolden Setに対して検証."""
        result = ValidationResult()
        
        questions = self.golden.get("questions", [])
        question = next((q for q in questions if q.get("id") == question_id), None)
        
        if not question:
            result.add_warning("QUESTION_NOT_FOUND", f"Question {question_id} not in golden set")
            return result
        
        # 必須用語チェック
        must_include = question.get("must_include_terms", [])
        answer = run_result.get("answer", "").lower()
        
        missing_terms = [t for t in must_include if t.lower() not in answer]
        if missing_terms:
            result.add_warning(
                "MISSING_TERMS",
                f"Answer missing required terms: {missing_terms}",
            )
        
        # 引用数チェック
        min_citations = question.get("min_citations", 0)
        citations = run_result.get("citations", [])
        if len(citations) < min_citations:
            result.add_error(
                "INSUFFICIENT_CITATIONS",
                f"Citations {len(citations)} < required {min_citations}",
            )
        
        # 根拠率チェック
        min_evidence_rate = question.get("min_evidence_rate", 0.9)
        metrics = run_result.get("metrics", {})
        coverage = metrics.get("evidence_coverage", 0)
        if coverage < min_evidence_rate:
            result.add_error(
                "LOW_EVIDENCE_RATE",
                f"Evidence rate {coverage:.2%} < required {min_evidence_rate:.2%}",
            )
        
        return result


def validate_bundle(run_dir: Path) -> ValidationResult:
    """便利関数: Bundle全体を検証."""
    schema = SchemaValidator()
    return schema.validate_bundle(run_dir)


def validate_evidence_coverage(
    claims: List[Dict[str, Any]],
    evidence: List[Dict[str, Any]],
    min_coverage: float = 0.95,
) -> ValidationResult:
    """便利関数: 根拠カバレッジを検証."""
    validator = EvidenceCoverageValidator(min_coverage)
    return validator.validate(claims, evidence)
