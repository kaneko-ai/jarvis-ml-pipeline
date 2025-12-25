"""
JARVIS Extraction Plugin - Claim & Evidence Extractor

論文からClaim、Evidence、Numeric情報を抽出。
全出力にevidence_linksを付与。
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from jarvis_core.contracts.types import (
    Artifacts, ArtifactsDelta, Claim, EvidenceLink, RuntimeConfig, TaskContext
)
from jarvis_core.provenance import get_provenance_linker


@dataclass
class NumericExtraction:
    """数値抽出結果."""
    value: str
    type: str  # n, p, CI, effect_size, percentage
    context: str
    evidence: Optional[EvidenceLink] = None


@dataclass
class MethodExtraction:
    """Methods抽出結果."""
    method_name: str
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)
    evidence: Optional[EvidenceLink] = None


@dataclass
class LimitationExtraction:
    """Limitation抽出結果."""
    limitation: str
    severity: str  # minor, moderate, major
    evidence: Optional[EvidenceLink] = None


class ClaimExtractor:
    """
    Claim抽出器.
    
    論文テキストから主張を抽出し、根拠を紐付ける。
    """
    
    # Claim indicator patterns
    CLAIM_PATTERNS = [
        r"(?:we|this study|our results?|the results?)\s+(?:show|demonstrate|suggest|indicate|reveal|confirm|found)\s+that\s+([^.]+\.)",
        r"(?:these|our|the)\s+(?:findings?|data|results?|observations?)\s+(?:show|suggest|indicate|demonstrate)\s+(?:that\s+)?([^.]+\.)",
        r"(?:in conclusion|we conclude|overall|taken together)[,\s]+([^.]+\.)",
        r"(?:importantly|significantly|notably|interestingly)[,\s]+([^.]+\.)",
    ]
    
    def __init__(self):
        self.linker = get_provenance_linker(strict=True)
    
    def extract_claims(self, doc_id: str, text: str, 
                       section: str = "unknown") -> List[Claim]:
        """
        テキストからClaimを抽出.
        
        Args:
            doc_id: ドキュメントID
            text: テキスト
            section: セクション名
        
        Returns:
            Claimリスト（evidence_links付き）
        """
        claims = []
        
        # Register text as chunks
        self.linker.register_chunks_from_document(doc_id, {section: text})
        
        # Extract claims using patterns
        for pattern in self.CLAIM_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claim_text = match.group(1) if match.groups() else match.group(0)
                claim_text = claim_text.strip()
                
                if len(claim_text) < 20:  # Too short
                    continue
                
                claim_id = f"c-{uuid.uuid4().hex[:8]}"
                
                # Find evidence
                evidence = self.linker.find_evidence(claim_text, threshold=0.3)
                
                # Create claim
                claim = Claim(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    evidence=evidence[:3],  # Top 3 evidence
                    claim_type="fact" if evidence else "hypothesis",
                    confidence=sum(e.confidence for e in evidence[:3]) / 3 if evidence else 0.0
                )
                
                claims.append(claim)
        
        return claims
    
    def extract_from_sections(self, doc_id: str, 
                              sections: Dict[str, str]) -> List[Claim]:
        """複数セクションからClaim抽出."""
        all_claims = []
        
        for section_name, section_text in sections.items():
            claims = self.extract_claims(doc_id, section_text, section_name)
            all_claims.extend(claims)
        
        return all_claims


class NumericExtractor:
    """
    数値抽出器.
    
    n, p値, CI, 効果量などを抽出。
    """
    
    PATTERNS = {
        "sample_size": r"n\s*=\s*(\d+)",
        "p_value": r"p\s*[<>=]\s*([0-9.]+)",
        "confidence_interval": r"(?:95%?\s*)?CI\s*[:=]?\s*\[?([0-9.\-–]+)\s*[,to\-–]\s*([0-9.\-–]+)\]?",
        "effect_size": r"(?:effect size|Cohen['']?s? d|η²?|Hedges['']? g)\s*[=:]\s*([0-9.\-–]+)",
        "percentage": r"(\d+(?:\.\d+)?)\s*%",
        "hazard_ratio": r"(?:HR|hazard ratio)\s*[=:]\s*([0-9.]+)",
        "odds_ratio": r"(?:OR|odds ratio)\s*[=:]\s*([0-9.]+)",
        "mean_sd": r"(?:mean|M)\s*[=:]\s*([0-9.]+)\s*±\s*([0-9.]+)",
    }
    
    def extract(self, text: str, doc_id: str = "", 
                section: str = "") -> List[NumericExtraction]:
        """数値を抽出."""
        results = []
        
        for num_type, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.groups() else match.group(0)
                
                # Get context (surrounding text)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # Create evidence link
                evidence = EvidenceLink(
                    doc_id=doc_id,
                    section=section,
                    chunk_id=f"{doc_id}_{section}",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9,
                    text=match.group(0)
                )
                
                results.append(NumericExtraction(
                    value=value,
                    type=num_type,
                    context=context,
                    evidence=evidence
                ))
        
        return results


class MethodExtractor:
    """Methods抽出器."""
    
    METHOD_KEYWORDS = [
        "western blot", "PCR", "qPCR", "RNA-seq", "ELISA",
        "flow cytometry", "immunofluorescence", "microscopy",
        "cell culture", "transfection", "knockout", "knockdown",
        "statistical analysis", "t-test", "ANOVA", "regression",
        "machine learning", "deep learning", "neural network"
    ]
    
    def extract(self, text: str, doc_id: str = "",
                section: str = "Methods") -> List[MethodExtraction]:
        """Methods情報を抽出."""
        results = []
        
        for method in self.METHOD_KEYWORDS:
            if method.lower() in text.lower():
                # Find the sentence containing the method
                sentences = re.split(r'[.!?]', text)
                for sent in sentences:
                    if method.lower() in sent.lower():
                        results.append(MethodExtraction(
                            method_name=method,
                            description=sent.strip()[:200],
                            evidence=EvidenceLink(
                                doc_id=doc_id,
                                section=section,
                                chunk_id=f"{doc_id}_{section}",
                                start=0,
                                end=len(sent),
                                confidence=0.85
                            )
                        ))
                        break
        
        return results


class LimitationExtractor:
    """Limitation抽出器."""
    
    LIMITATION_PATTERNS = [
        (r"(?:limitation|drawback|weakness)[s]?\s+(?:of|in)\s+(?:this|our|the)\s+study[^.]*include[s]?\s+([^.]+\.)", "major"),
        (r"(?:however|nonetheless|nevertheless)[,\s]+([^.]*(?:limit|restrict|constrain)[^.]+\.)", "moderate"),
        (r"(?:future\s+(?:studies?|research|work)\s+(?:should|could|may)[^.]+\.)", "minor"),
        (r"(?:small\s+sample\s+size|limited\s+(?:sample|data|scope))[^.]*\.", "major"),
    ]
    
    def extract(self, text: str, doc_id: str = "",
                section: str = "Discussion") -> List[LimitationExtraction]:
        """Limitationを抽出."""
        results = []
        
        for pattern, severity in self.LIMITATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                limitation_text = match.group(1) if match.groups() else match.group(0)
                
                results.append(LimitationExtraction(
                    limitation=limitation_text.strip()[:300],
                    severity=severity,
                    evidence=EvidenceLink(
                        doc_id=doc_id,
                        section=section,
                        chunk_id=f"{doc_id}_{section}",
                        start=match.start(),
                        end=match.end(),
                        confidence=0.8
                    )
                ))
        
        return results


class ExtractionPlugin:
    """Extraction統合プラグイン."""
    
    def __init__(self):
        self.claim_extractor = ClaimExtractor()
        self.numeric_extractor = NumericExtractor()
        self.method_extractor = MethodExtractor()
        self.limitation_extractor = LimitationExtractor()
        self.is_active = False
    
    def activate(self, runtime: RuntimeConfig, config: Dict[str, Any]) -> None:
        self.is_active = True
    
    def run(self, context: TaskContext, artifacts: Artifacts) -> ArtifactsDelta:
        """抽出を実行."""
        delta: ArtifactsDelta = {
            "claims": [],
            "numerics": [],
            "methods": [],
            "limitations": []
        }
        
        for paper in artifacts.papers:
            # Extract claims
            claims = self.claim_extractor.extract_from_sections(
                paper.doc_id, 
                paper.sections
            )
            
            for claim in claims:
                artifacts.add_claim(claim)
                delta["claims"].append(claim.to_dict())
            
            # Extract numerics from Results/Abstract
            for section in ["Results", "Abstract", "results", "abstract"]:
                if section in paper.sections:
                    numerics = self.numeric_extractor.extract(
                        paper.sections[section], paper.doc_id, section
                    )
                    for n in numerics:
                        delta["numerics"].append({
                            "value": n.value,
                            "type": n.type,
                            "context": n.context,
                            "evidence": n.evidence.to_dict() if n.evidence else None
                        })
            
            # Extract methods
            for section in ["Methods", "Materials and Methods", "methods"]:
                if section in paper.sections:
                    methods = self.method_extractor.extract(
                        paper.sections[section], paper.doc_id, section
                    )
                    for m in methods:
                        delta["methods"].append({
                            "method": m.method_name,
                            "description": m.description,
                            "evidence": m.evidence.to_dict() if m.evidence else None
                        })
            
            # Extract limitations
            for section in ["Discussion", "Limitations", "discussion"]:
                if section in paper.sections:
                    limitations = self.limitation_extractor.extract(
                        paper.sections[section], paper.doc_id, section
                    )
                    for lim in limitations:
                        delta["limitations"].append({
                            "limitation": lim.limitation,
                            "severity": lim.severity,
                            "evidence": lim.evidence.to_dict() if lim.evidence else None
                        })
        
        return delta
    
    def deactivate(self) -> None:
        self.is_active = False


def get_extraction_plugin() -> ExtractionPlugin:
    return ExtractionPlugin()
