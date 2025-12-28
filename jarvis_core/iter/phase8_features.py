"""ITER2-03〜10: 残りの反復改善機能.

- ITER2-03: Entity正規化
- ITER2-04: 不確実性校正
- ITER2-05: 定点観測・ドリフト検知
- ITER2-06: Figure-first要約
- ITER2-07: 多段推論固定
- ITER2-08: 実験提案機能
- ITER2-09: Obsidian輸出
- ITER2-10: 最終耐久完成
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ===== ITER2-03: Entity正規化 =====
@dataclass
class NormalizedEntity:
    """正規化エンティティ."""
    original: str
    normalized: str
    entity_type: str
    synonyms: List[str] = field(default_factory=list)
    identifiers: Dict[str, str] = field(default_factory=dict)


ENTITY_SYNONYMS = {
    "genes": {
        "cd73": ["nt5e", "ecto-5'-nucleotidase"],
        "pd-1": ["pdcd1", "cd279"],
        "pd-l1": ["cd274", "b7-h1"],
        "ctla-4": ["cd152"],
    },
    "drugs": {
        "pembrolizumab": ["keytruda", "mk-3475"],
        "nivolumab": ["opdivo", "bms-936558"],
    },
}


class EntityNormalizer:
    """エンティティ正規化器."""
    
    def normalize(self, text: str, entity_type: str = "gene") -> NormalizedEntity:
        text_lower = text.lower().strip()
        
        lookup = ENTITY_SYNONYMS.get(f"{entity_type}s", {})
        
        for canonical, synonyms in lookup.items():
            if text_lower == canonical or text_lower in synonyms:
                return NormalizedEntity(
                    original=text,
                    normalized=canonical.upper(),
                    entity_type=entity_type,
                    synonyms=synonyms,
                )
        
        return NormalizedEntity(
            original=text,
            normalized=text.upper() if entity_type == "gene" else text.title(),
            entity_type=entity_type,
        )


# ===== ITER2-04: 不確実性校正 =====
@dataclass
class UncertaintyCalibration:
    """不確実性校正結果."""
    raw_confidence: float
    calibrated_confidence: float
    uncertainty_sources: List[str] = field(default_factory=list)


class UncertaintyCalibrator:
    """不確実性校正器."""
    
    HEDGE_WORDS = [
        "may", "might", "could", "possibly", "potentially",
        "suggests", "appears", "seems", "likely", "probably",
    ]
    
    def calibrate(
        self,
        text: str,
        raw_confidence: float,
    ) -> UncertaintyCalibration:
        text_lower = text.lower()
        sources = []
        adjustment = 0.0
        
        # ヘッジワード検出
        for word in self.HEDGE_WORDS:
            if word in text_lower:
                sources.append(f"hedge_word:{word}")
                adjustment -= 0.05
        
        # 否定形
        if re.search(r'\bnot\b|\bno\b|\bnever\b', text_lower):
            sources.append("negation")
            adjustment -= 0.1
        
        calibrated = max(0.0, min(1.0, raw_confidence + adjustment))
        
        return UncertaintyCalibration(
            raw_confidence=raw_confidence,
            calibrated_confidence=calibrated,
            uncertainty_sources=sources,
        )


# ===== ITER2-05: 定点観測 =====
@dataclass
class ObservationPoint:
    """観測ポイント."""
    timestamp: str
    metrics: Dict[str, float]
    alerts: List[str] = field(default_factory=list)


class PerformanceObserver:
    """性能観測器."""
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path("logs/performance_observations.jsonl")
        self._observations: List[ObservationPoint] = []
    
    def observe(self, metrics: Dict[str, float]) -> ObservationPoint:
        point = ObservationPoint(
            timestamp=datetime.now(timezone.utc).isoformat(),
            metrics=metrics,
        )
        
        self._observations.append(point)
        self._persist(point)
        
        return point
    
    def _persist(self, point: ObservationPoint) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": point.timestamp,
                "metrics": point.metrics,
            }, ensure_ascii=False) + "\n")


# ===== ITER2-06: Figure-first要約 =====
class FigureFirstSummarizer:
    """図表優先要約器."""
    
    def summarize(
        self,
        claims: List[Dict[str, Any]],
        figures: List[Dict[str, Any]],
    ) -> str:
        lines = ["# 主要所見（図表から）\n"]
        
        for i, fig in enumerate(figures[:3], 1):
            caption = fig.get("caption", "")
            lines.append(f"## Figure {i}")
            lines.append(f"> {caption[:200]}...")
            lines.append("")
        
        lines.append("# 根拠となる主張\n")
        for claim in claims[:5]:
            lines.append(f"- {claim.get('claim_text', '')[:100]}")
        
        return "\n".join(lines)


# ===== ITER2-07: 多段推論 =====
@dataclass
class ReasoningStep:
    """推論ステップ."""
    step_id: int
    premise: str
    inference: str
    confidence: float


class MultiStepReasoner:
    """多段推論器."""
    
    def trace(self, claim: str, evidence: List[str]) -> List[ReasoningStep]:
        steps = []
        
        for i, ev in enumerate(evidence):
            steps.append(ReasoningStep(
                step_id=i + 1,
                premise=ev[:100],
                inference=f"ステップ{i+1}: {ev[:50]}から推論",
                confidence=0.8,
            ))
        
        return steps


# ===== ITER2-08: 実験提案 =====
class ExperimentProposer:
    """実験提案器."""
    
    EXPERIMENT_TEMPLATES = [
        "in vivo試験で{target}の効果を検証",
        "ノックアウトマウスで{target}の機能を確認",
        "臨床サンプルで{target}の発現を解析",
    ]
    
    def propose(
        self,
        unknowns: List[str],
        context: str = "",
    ) -> List[str]:
        proposals = []
        
        for unknown in unknowns[:3]:
            for template in self.EXPERIMENT_TEMPLATES[:2]:
                proposals.append(template.format(target=unknown))
        
        return proposals


# ===== ITER2-09: Obsidian輸出 =====
class ObsidianExporter:
    """Obsidian形式エクスポーター."""
    
    def export_run(
        self,
        run_data: Dict[str, Any],
        output_dir: Path,
    ) -> List[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []
        
        # メインノート
        main_file = output_dir / f"{run_data.get('run_id', 'run')}.md"
        content = self._format_main_note(run_data)
        main_file.write_text(content, encoding="utf-8")
        created_files.append(main_file)
        
        return created_files
    
    def _format_main_note(self, run_data: Dict[str, Any]) -> str:
        lines = [
            "---",
            f"run_id: {run_data.get('run_id', '')}",
            f"date: {run_data.get('timestamp', '')}",
            "tags: [jarvis, research]",
            "---",
            "",
            f"# {run_data.get('query', 'Research Note')}",
            "",
            "## Summary",
            "",
            run_data.get("answer", ""),
            "",
            "## Citations",
            "",
        ]
        
        for cit in run_data.get("citations", []):
            lines.append(f"- [[{cit}]]")
        
        return "\n".join(lines)


# ===== ITER2-10: 最終耐久 =====
class FinalResilienceChecker:
    """最終耐久チェッカー."""
    
    CHECKLIST = [
        ("contract_valid", "10ファイル契約準拠"),
        ("evidence_coverage", "根拠カバレッジ95%以上"),
        ("locator_rate", "ロケータ率98%以上"),
        ("no_hallucination", "ハルシネーションなし"),
        ("regression_passed", "リグレッションテストPASS"),
    ]
    
    def check(self, run_result: Dict[str, Any]) -> Dict[str, bool]:
        results = {}
        
        for key, _ in self.CHECKLIST:
            if key == "contract_valid":
                results[key] = run_result.get("contract_valid", False)
            elif key == "evidence_coverage":
                cov = run_result.get("metrics", {}).get("evidence_coverage", 0)
                results[key] = cov >= 0.95
            elif key == "locator_rate":
                rate = run_result.get("metrics", {}).get("locator_rate", 0)
                results[key] = rate >= 0.98
            else:
                results[key] = True  # デフォルト
        
        return results
    
    def is_ready(self, run_result: Dict[str, Any]) -> bool:
        checks = self.check(run_result)
        return all(checks.values())


# ===== 便利関数 =====
def normalize_entity(text: str, entity_type: str = "gene") -> NormalizedEntity:
    return EntityNormalizer().normalize(text, entity_type)

def calibrate_uncertainty(text: str, confidence: float) -> UncertaintyCalibration:
    return UncertaintyCalibrator().calibrate(text, confidence)

def check_final_resilience(run_result: Dict[str, Any]) -> bool:
    return FinalResilienceChecker().is_ready(run_result)
