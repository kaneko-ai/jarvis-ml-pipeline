"""
JARVIS Design Plugin - Experiment Design Assistant

ギャップ分析、次実験提案、プロトコルドラフト、統計設計支援。
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, Claim, EvidenceLink, RuntimeConfig, TaskContext
)


@dataclass
class Gap:
    """研究ギャップ."""
    gap_id: str
    description: str
    type: str  # knowledge, methodology, population, outcome
    priority: str  # high, medium, low
    related_claims: List[str] = field(default_factory=list)
    evidence: List[EvidenceLink] = field(default_factory=list)


@dataclass
class ExperimentProposal:
    """実験提案."""
    proposal_id: str
    title: str
    objective: str
    hypothesis: str
    design_type: str  # RCT, cohort, in_vitro, in_vivo
    sample_size_estimate: int
    key_variables: Dict[str, str] = field(default_factory=dict)
    expected_outcomes: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    gaps_addressed: List[str] = field(default_factory=list)


@dataclass
class Protocol:
    """実験プロトコル."""
    protocol_id: str
    title: str
    sections: Dict[str, str] = field(default_factory=dict)
    materials: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)
    analysis_plan: str = ""


@dataclass
class StatisticalDesign:
    """統計設計."""
    design_id: str
    primary_outcome: str
    analysis_type: str
    sample_size: int
    power: float
    alpha: float
    effect_size: float
    assumptions: List[str] = field(default_factory=list)
    formula: str = ""


class GapAnalyzer:
    """
    ギャップ分析器.
    
    既存研究から研究ギャップを特定。
    """
    
    GAP_INDICATORS = {
        "knowledge": [
            "unknown", "unclear", "remains to be", "not well understood",
            "limited knowledge", "further research needed"
        ],
        "methodology": [
            "methodological limitation", "small sample", "lack of control",
            "bias", "not randomized"
        ],
        "population": [
            "underrepresented", "excluded", "specific population",
            "generalizability", "diverse population"
        ],
        "outcome": [
            "long-term effects", "clinical outcomes", "patient-reported",
            "survival", "quality of life"
        ]
    }
    
    def analyze(self, claims: List[Claim], 
                sections: Dict[str, str]) -> List[Gap]:
        """ギャップを分析."""
        gaps = []
        
        # Analyze discussion/limitation sections
        for section_name, section_text in sections.items():
            if any(s in section_name.lower() for s in ["discussion", "limitation", "future"]):
                for gap_type, indicators in self.GAP_INDICATORS.items():
                    for indicator in indicators:
                        if indicator in section_text.lower():
                            # Find the sentence
                            sentences = re.split(r'[.!?]', section_text)
                            for sent in sentences:
                                if indicator in sent.lower():
                                    gaps.append(Gap(
                                        gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                                        description=sent.strip()[:300],
                                        type=gap_type,
                                        priority=self._prioritize(gap_type, sent),
                                        evidence=[EvidenceLink(
                                            doc_id="source",
                                            section=section_name,
                                            chunk_id=f"gap_{gap_type}",
                                            start=0,
                                            end=len(sent),
                                            confidence=0.75
                                        )]
                                    ))
                                    break
        
        return gaps[:10]  # Limit
    
    def _prioritize(self, gap_type: str, text: str) -> str:
        """ギャップの優先度を決定."""
        high_priority = ["urgent", "critical", "essential", "crucial", "immediate"]
        low_priority = ["minor", "potential", "may", "might", "could"]
        
        text_lower = text.lower()
        
        if any(h in text_lower for h in high_priority):
            return "high"
        elif any(l in text_lower for l in low_priority):
            return "low"
        else:
            return "medium"


class ExperimentDesigner:
    """
    実験設計器.
    
    ギャップに基づいて実験を提案。
    """
    
    DESIGN_TEMPLATES = {
        "knowledge": {
            "design_type": "exploratory",
            "sample_size": 50,
            "expected_outcomes": ["characterization", "mechanism elucidation"]
        },
        "methodology": {
            "design_type": "RCT",
            "sample_size": 100,
            "expected_outcomes": ["validation", "replication"]
        },
        "population": {
            "design_type": "cohort",
            "sample_size": 200,
            "expected_outcomes": ["generalizability", "subgroup analysis"]
        },
        "outcome": {
            "design_type": "longitudinal",
            "sample_size": 150,
            "expected_outcomes": ["long-term effects", "survival analysis"]
        }
    }
    
    def design_from_gap(self, gap: Gap, context: TaskContext) -> ExperimentProposal:
        """ギャップから実験を設計."""
        template = self.DESIGN_TEMPLATES.get(gap.type, self.DESIGN_TEMPLATES["knowledge"])
        
        return ExperimentProposal(
            proposal_id=f"exp-{uuid.uuid4().hex[:8]}",
            title=f"Investigation of: {gap.description[:100]}",
            objective=f"To address the {gap.type} gap: {gap.description[:200]}",
            hypothesis=self._generate_hypothesis(gap, context),
            design_type=template["design_type"],
            sample_size_estimate=template["sample_size"],
            key_variables={
                "independent": "treatment/intervention",
                "dependent": "primary outcome measure",
                "confounders": "to be identified"
            },
            expected_outcomes=template["expected_outcomes"],
            limitations=[
                "Resource constraints",
                "Time limitations",
                "Potential selection bias"
            ],
            gaps_addressed=[gap.gap_id]
        )
    
    def _generate_hypothesis(self, gap: Gap, context: TaskContext) -> str:
        """仮説を生成."""
        domain = context.domain
        return f"In the context of {domain}, addressing {gap.type} gap will reveal " \
               f"new insights related to: {gap.description[:100]}"


class ProtocolGenerator:
    """
    プロトコル生成器.
    
    実験提案からプロトコルを生成。
    """
    
    def generate(self, proposal: ExperimentProposal) -> Protocol:
        """プロトコルを生成."""
        steps = []
        materials = []
        controls = []
        
        # Design-specific steps
        if proposal.design_type == "RCT":
            steps = [
                "1. Obtain ethical approval",
                "2. Recruit participants (n={})".format(proposal.sample_size_estimate),
                "3. Randomize to treatment/control groups",
                "4. Administer intervention",
                "5. Collect outcome data at specified timepoints",
                "6. Analyze data using pre-specified statistical plan"
            ]
            controls = ["Placebo or standard care control", "Blinding of assessors"]
            
        elif proposal.design_type == "cohort":
            steps = [
                "1. Define eligible population",
                "2. Recruit cohort (n={})".format(proposal.sample_size_estimate),
                "3. Collect baseline data",
                "4. Follow-up at defined intervals",
                "5. Document exposures and outcomes",
                "6. Conduct survival/regression analysis"
            ]
            controls = ["Matched controls", "Adjustment for confounders"]
            
        elif proposal.design_type in ["in_vitro", "exploratory"]:
            steps = [
                "1. Prepare cell lines/samples",
                "2. Apply experimental conditions",
                "3. Collect samples at timepoints",
                "4. Perform assays (Western, PCR, etc.)",
                "5. Analyze and quantify results",
                "6. Statistical comparison"
            ]
            materials = ["Cell culture media", "Reagents", "Antibodies"]
            controls = ["Negative control", "Positive control", "Technical replicates"]
        
        return Protocol(
            protocol_id=f"prot-{uuid.uuid4().hex[:8]}",
            title=proposal.title,
            sections={
                "objective": proposal.objective,
                "hypothesis": proposal.hypothesis,
                "design": proposal.design_type,
                "sample_size": str(proposal.sample_size_estimate)
            },
            materials=materials,
            steps=steps,
            controls=controls,
            analysis_plan=f"Analysis for {proposal.expected_outcomes}"
        )


class StatisticalDesigner:
    """
    統計設計支援.
    
    検出力分析、サンプルサイズ計算。
    """
    
    def calculate_sample_size(self, 
                              effect_size: float = 0.5,
                              alpha: float = 0.05,
                              power: float = 0.8,
                              analysis_type: str = "t-test") -> StatisticalDesign:
        """サンプルサイズを計算."""
        import math
        
        # Simplified calculation for t-test
        if analysis_type == "t-test":
            # n per group = 2 * ((z_alpha + z_beta) / d)^2
            # Using approximations
            z_alpha = 1.96 if alpha == 0.05 else 2.58
            z_beta = 0.84 if power == 0.8 else 1.28
            
            n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            total_n = int(math.ceil(n_per_group * 2))
            
        elif analysis_type == "chi-square":
            n_per_group = 4 / (effect_size ** 2)
            total_n = int(math.ceil(n_per_group * 2))
            
        else:
            total_n = 100  # Default
        
        return StatisticalDesign(
            design_id=f"stat-{uuid.uuid4().hex[:8]}",
            primary_outcome="To be specified",
            analysis_type=analysis_type,
            sample_size=total_n,
            power=power,
            alpha=alpha,
            effect_size=effect_size,
            assumptions=[
                "Normal distribution",
                "Equal variance",
                f"Effect size d = {effect_size}",
                f"Alpha = {alpha}",
                f"Power = {power}"
            ],
            formula=f"n = 2 * ((z_α + z_β) / d)² = {total_n}"
        )


class RiskDiagnoser:
    """
    リスク診断器.
    
    研究設計のリスクを評価。
    """
    
    def diagnose(self, proposal: ExperimentProposal) -> Dict[str, Any]:
        """設計リスクを診断."""
        risks = []
        
        # Sample size
        if proposal.sample_size_estimate < 30:
            risks.append({
                "type": "underpowered",
                "severity": "high",
                "message": "Sample size may be too small for meaningful results"
            })
        
        # Design type
        if proposal.design_type not in ["RCT", "randomized"]:
            risks.append({
                "type": "bias",
                "severity": "medium",
                "message": "Non-randomized design may introduce selection bias"
            })
        
        # Limitations count
        if len(proposal.limitations) > 3:
            risks.append({
                "type": "complexity",
                "severity": "medium",
                "message": "Multiple known limitations may affect validity"
            })
        
        return {
            "overall_risk": "high" if any(r["severity"] == "high" for r in risks) else "medium",
            "risks": risks,
            "recommendation": "Consider addressing high-severity risks before proceeding"
        }


class DesignPlugin:
    """Design統合プラグイン."""
    
    def __init__(self):
        self.gap_analyzer = GapAnalyzer()
        self.designer = ExperimentDesigner()
        self.protocol_gen = ProtocolGenerator()
        self.stat_designer = StatisticalDesigner()
        self.risk_diagnoser = RiskDiagnoser()
        self.is_active = False
    
    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        self.is_active = True
    
    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """実験設計を実行."""
        delta: ArtifactsDelta = {
            "gaps": [],
            "proposals": [],
            "protocols": [],
            "statistical_designs": [],
            "risk_assessments": []
        }
        
        # Analyze gaps from all papers
        all_gaps = []
        for paper in artifacts.papers:
            gaps = self.gap_analyzer.analyze(artifacts.claims, paper.sections)
            all_gaps.extend(gaps)
        
        # Design experiments for top gaps
        for gap in all_gaps[:5]:
            delta["gaps"].append({
                "gap_id": gap.gap_id,
                "description": gap.description,
                "type": gap.type,
                "priority": gap.priority
            })
            
            # Generate proposal
            proposal = self.designer.design_from_gap(gap, context)
            delta["proposals"].append({
                "proposal_id": proposal.proposal_id,
                "title": proposal.title,
                "objective": proposal.objective,
                "design_type": proposal.design_type,
                "sample_size": proposal.sample_size_estimate
            })
            
            # Generate protocol
            protocol = self.protocol_gen.generate(proposal)
            delta["protocols"].append({
                "protocol_id": protocol.protocol_id,
                "title": protocol.title,
                "steps": protocol.steps,
                "controls": protocol.controls
            })
            
            # Statistical design
            stat = self.stat_designer.calculate_sample_size()
            delta["statistical_designs"].append({
                "design_id": stat.design_id,
                "analysis_type": stat.analysis_type,
                "sample_size": stat.sample_size,
                "power": stat.power
            })
            
            # Risk assessment
            risk = self.risk_diagnoser.diagnose(proposal)
            delta["risk_assessments"].append({
                "proposal_id": proposal.proposal_id,
                "overall_risk": risk["overall_risk"],
                "risks": risk["risks"]
            })
            
            # Store in artifacts
            artifacts.designs.append({
                "gap": gap.gap_id,
                "proposal": proposal.proposal_id,
                "protocol": protocol.protocol_id
            })
        
        return delta
    
    def deactivate(self) -> None:
        self.is_active = False


def get_design_plugin() -> DesignPlugin:
    return DesignPlugin()
