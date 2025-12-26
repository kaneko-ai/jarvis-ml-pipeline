"""
JARVIS PICO Consistency Checker

M3: メタ分析完備のためのPICO整合性検証
- claim-evidenceのPICO一致検証
- 効果方向の整合性チェック
- 数値ズレ検出
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ConsistencyLevel(Enum):
    """整合性レベル."""
    CONSISTENT = "consistent"
    PARTIAL = "partial"
    INCONSISTENT = "inconsistent"
    UNKNOWN = "unknown"


class EffectDirection(Enum):
    """効果方向."""
    BENEFICIAL = "beneficial"
    HARMFUL = "harmful"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class PICOElement:
    """PICO要素."""
    description: str
    keywords: List[str] = field(default_factory=list)
    provenance: Optional[Dict[str, Any]] = None
    
    def extract_keywords(self) -> List[str]:
        """キーワードを抽出."""
        if self.keywords:
            return self.keywords
        
        # 簡易キーワード抽出
        text = self.description.lower()
        # 単語分割
        words = re.findall(r'\b[a-z]{3,}\b', text)
        # ストップワード除去
        stopwords = {'the', 'and', 'for', 'with', 'from', 'were', 'was', 'are', 'has', 'have'}
        return [w for w in words if w not in stopwords]


@dataclass
class PICOProfile:
    """PICOプロファイル."""
    population: Optional[PICOElement] = None
    intervention: Optional[PICOElement] = None
    comparator: Optional[PICOElement] = None
    outcome: Optional[PICOElement] = None
    
    def is_complete(self) -> bool:
        """必須要素が揃っているか."""
        return all([
            self.population and self.population.description,
            self.intervention and self.intervention.description,
            self.outcome and self.outcome.description
        ])
    
    def missing_elements(self) -> List[str]:
        """欠損要素のリスト."""
        missing = []
        if not self.population or not self.population.description:
            missing.append("population")
        if not self.intervention or not self.intervention.description:
            missing.append("intervention")
        if not self.outcome or not self.outcome.description:
            missing.append("outcome")
        return missing


@dataclass
class ConsistencyResult:
    """整合性チェック結果."""
    level: ConsistencyLevel
    score: float  # 0.0 - 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """ゲート通過判定."""
        return self.level in [ConsistencyLevel.CONSISTENT, ConsistencyLevel.PARTIAL]


class PICOConsistencyChecker:
    """PICO整合性チェッカー."""
    
    def __init__(self, strict_mode: bool = False):
        """
        初期化.
        
        Args:
            strict_mode: 厳格モード（PARTIAL=不合格）
        """
        self.strict_mode = strict_mode
    
    def check_population_consistency(
        self, 
        claim_population: PICOElement, 
        evidence_population: PICOElement
    ) -> ConsistencyResult:
        """
        Population一致チェック.
        
        Args:
            claim_population: Claimの対象集団
            evidence_population: Evidenceの対象集団
        
        Returns:
            整合性結果
        """
        claim_kw = set(claim_population.extract_keywords())
        evidence_kw = set(evidence_population.extract_keywords())
        
        if not claim_kw or not evidence_kw:
            return ConsistencyResult(
                level=ConsistencyLevel.UNKNOWN,
                score=0.5,
                issues=["Insufficient keywords for comparison"]
            )
        
        # Jaccard類似度
        intersection = claim_kw & evidence_kw
        union = claim_kw | evidence_kw
        jaccard = len(intersection) / len(union) if union else 0
        
        if jaccard >= 0.5:
            level = ConsistencyLevel.CONSISTENT
        elif jaccard >= 0.2:
            level = ConsistencyLevel.PARTIAL
        else:
            level = ConsistencyLevel.INCONSISTENT
        
        return ConsistencyResult(
            level=level,
            score=jaccard,
            details={
                "claim_keywords": list(claim_kw),
                "evidence_keywords": list(evidence_kw),
                "common_keywords": list(intersection),
                "jaccard": jaccard
            }
        )
    
    def check_intervention_consistency(
        self,
        claim_intervention: PICOElement,
        evidence_intervention: PICOElement
    ) -> ConsistencyResult:
        """Intervention一致チェック."""
        return self.check_population_consistency(claim_intervention, evidence_intervention)
    
    def check_outcome_consistency(
        self,
        claim_outcome: PICOElement,
        evidence_outcome: PICOElement
    ) -> ConsistencyResult:
        """Outcome一致チェック."""
        return self.check_population_consistency(claim_outcome, evidence_outcome)
    
    def check_effect_direction(
        self,
        claim_direction: EffectDirection,
        evidence_direction: EffectDirection
    ) -> ConsistencyResult:
        """
        効果方向一致チェック.
        
        Args:
            claim_direction: Claimの効果方向
            evidence_direction: Evidenceの効果方向
        
        Returns:
            整合性結果
        """
        if claim_direction == EffectDirection.UNKNOWN or evidence_direction == EffectDirection.UNKNOWN:
            return ConsistencyResult(
                level=ConsistencyLevel.UNKNOWN,
                score=0.5,
                issues=["Effect direction unknown"]
            )
        
        if claim_direction == evidence_direction:
            return ConsistencyResult(
                level=ConsistencyLevel.CONSISTENT,
                score=1.0,
                details={"direction": claim_direction.value}
            )
        
        return ConsistencyResult(
            level=ConsistencyLevel.INCONSISTENT,
            score=0.0,
            issues=[f"Direction mismatch: claim={claim_direction.value}, evidence={evidence_direction.value}"]
        )
    
    def check_numeric_consistency(
        self,
        claim_value: float,
        evidence_value: float,
        tolerance: float = 0.01
    ) -> ConsistencyResult:
        """
        数値一致チェック.
        
        Args:
            claim_value: Claimの数値
            evidence_value: Evidenceの数値
            tolerance: 許容誤差（相対）
        
        Returns:
            整合性結果
        """
        if evidence_value == 0:
            if claim_value == 0:
                return ConsistencyResult(level=ConsistencyLevel.CONSISTENT, score=1.0)
            return ConsistencyResult(
                level=ConsistencyLevel.INCONSISTENT,
                score=0.0,
                issues=["Division by zero in comparison"]
            )
        
        relative_diff = abs(claim_value - evidence_value) / abs(evidence_value)
        
        if relative_diff <= tolerance:
            return ConsistencyResult(
                level=ConsistencyLevel.CONSISTENT,
                score=1.0 - relative_diff,
                details={"relative_diff": relative_diff}
            )
        elif relative_diff <= tolerance * 5:
            return ConsistencyResult(
                level=ConsistencyLevel.PARTIAL,
                score=1.0 - relative_diff,
                issues=[f"Numeric difference: {relative_diff:.2%}"],
                details={"relative_diff": relative_diff}
            )
        else:
            return ConsistencyResult(
                level=ConsistencyLevel.INCONSISTENT,
                score=0.0,
                issues=[f"Large numeric difference: claim={claim_value}, evidence={evidence_value}"]
            )
    
    def check_full_pico_consistency(
        self,
        claim_pico: PICOProfile,
        evidence_pico: PICOProfile
    ) -> ConsistencyResult:
        """
        PICO全体の整合性チェック.
        
        Args:
            claim_pico: ClaimのPICOプロファイル
            evidence_pico: EvidenceのPICOプロファイル
        
        Returns:
            総合整合性結果
        """
        results = []
        issues = []
        
        # Population
        if claim_pico.population and evidence_pico.population:
            pop_result = self.check_population_consistency(
                claim_pico.population, evidence_pico.population
            )
            results.append(("population", pop_result))
            issues.extend(pop_result.issues)
        
        # Intervention
        if claim_pico.intervention and evidence_pico.intervention:
            int_result = self.check_intervention_consistency(
                claim_pico.intervention, evidence_pico.intervention
            )
            results.append(("intervention", int_result))
            issues.extend(int_result.issues)
        
        # Comparator（オプション）
        if claim_pico.comparator and evidence_pico.comparator:
            comp_result = self.check_population_consistency(
                claim_pico.comparator, evidence_pico.comparator
            )
            results.append(("comparator", comp_result))
            issues.extend(comp_result.issues)
        
        # Outcome
        if claim_pico.outcome and evidence_pico.outcome:
            out_result = self.check_outcome_consistency(
                claim_pico.outcome, evidence_pico.outcome
            )
            results.append(("outcome", out_result))
            issues.extend(out_result.issues)
        
        if not results:
            return ConsistencyResult(
                level=ConsistencyLevel.UNKNOWN,
                score=0.0,
                issues=["No PICO elements to compare"]
            )
        
        # 総合スコア（加重平均）
        weights = {"population": 0.3, "intervention": 0.3, "outcome": 0.3, "comparator": 0.1}
        total_weight = sum(weights.get(name, 0.25) for name, _ in results)
        avg_score = sum(
            weights.get(name, 0.25) * r.score 
            for name, r in results
        ) / total_weight if total_weight > 0 else 0
        
        # 総合レベル判定
        inconsistent_count = sum(1 for _, r in results if r.level == ConsistencyLevel.INCONSISTENT)
        
        if inconsistent_count == 0 and avg_score >= 0.6:
            level = ConsistencyLevel.CONSISTENT
        elif inconsistent_count <= 1 and avg_score >= 0.3:
            level = ConsistencyLevel.PARTIAL
        else:
            level = ConsistencyLevel.INCONSISTENT
        
        return ConsistencyResult(
            level=level,
            score=avg_score,
            details={
                "element_results": {name: {"level": r.level.value, "score": r.score} for name, r in results}
            },
            issues=issues
        )


def check_pico_gate(
    claim_pico: Dict[str, Any],
    evidence_pico: Dict[str, Any],
    strict: bool = False
) -> Tuple[bool, ConsistencyResult]:
    """
    PICOゲート関数（便利関数）.
    
    Args:
        claim_pico: Claimの PICO辞書
        evidence_pico: EvidenceのPICO辞書
        strict: 厳格モード
    
    Returns:
        (passed, result)
    """
    def to_profile(data: Dict[str, Any]) -> PICOProfile:
        profile = PICOProfile()
        if data.get("population"):
            profile.population = PICOElement(description=data["population"].get("description", ""))
        if data.get("intervention"):
            profile.intervention = PICOElement(description=data["intervention"].get("description", ""))
        if data.get("comparator"):
            profile.comparator = PICOElement(description=data["comparator"].get("description", ""))
        if data.get("outcome"):
            profile.outcome = PICOElement(description=data["outcome"].get("description", ""))
        return profile
    
    checker = PICOConsistencyChecker(strict_mode=strict)
    claim_profile = to_profile(claim_pico)
    evidence_profile = to_profile(evidence_pico)
    
    result = checker.check_full_pico_consistency(claim_profile, evidence_profile)
    
    if strict:
        passed = result.level == ConsistencyLevel.CONSISTENT
    else:
        passed = result.passed
    
    return passed, result
