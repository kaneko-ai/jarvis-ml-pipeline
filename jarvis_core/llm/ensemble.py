"""Multi-Model Ensemble.

Per RP-355, combines multiple LLM outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import hashlib


class EnsembleStrategy(Enum):
    """Ensemble combination strategies."""
    
    VOTING = "voting"
    WEIGHTED = "weighted"
    BEST_OF_N = "best_of_n"
    CONSENSUS = "consensus"


@dataclass
class ModelOutput:
    """Output from a single model."""
    
    model_name: str
    text: str
    confidence: float
    latency_ms: float
    metadata: Dict[str, Any]


@dataclass
class EnsembleResult:
    """Combined ensemble result."""
    
    final_text: str
    strategy: EnsembleStrategy
    model_outputs: List[ModelOutput]
    agreement_score: float
    selected_model: Optional[str]


class MultiModelEnsemble:
    """Combines outputs from multiple LLMs.
    
    Per RP-355:
    - Parallel calls to Gemini + GPT-4 + Claude
    - Answer integration/voting
    - Model-specific routing
    """
    
    def __init__(
        self,
        models: Dict[str, Callable[[str], str]] = None,
        weights: Dict[str, float] = None,
        strategy: EnsembleStrategy = EnsembleStrategy.WEIGHTED,
    ):
        self.models = models or {}
        self.weights = weights or {}
        self.strategy = strategy
    
    def add_model(
        self,
        name: str,
        generator: Callable[[str], str],
        weight: float = 1.0,
    ) -> None:
        """Add a model to the ensemble."""
        self.models[name] = generator
        self.weights[name] = weight
    
    def generate(
        self,
        prompt: str,
        strategy: Optional[EnsembleStrategy] = None,
    ) -> EnsembleResult:
        """Generate with ensemble.
        
        Args:
            prompt: The prompt to generate from.
            strategy: Override ensemble strategy.
            
        Returns:
            EnsembleResult with combined output.
        """
        strategy = strategy or self.strategy
        
        # Collect outputs from all models
        outputs = self._collect_outputs(prompt)
        
        if not outputs:
            return EnsembleResult(
                final_text="",
                strategy=strategy,
                model_outputs=[],
                agreement_score=0.0,
                selected_model=None,
            )
        
        # Combine based on strategy
        if strategy == EnsembleStrategy.VOTING:
            return self._voting_combine(outputs)
        elif strategy == EnsembleStrategy.WEIGHTED:
            return self._weighted_combine(outputs)
        elif strategy == EnsembleStrategy.BEST_OF_N:
            return self._best_of_n(outputs)
        else:
            return self._consensus_combine(outputs)
    
    def _collect_outputs(self, prompt: str) -> List[ModelOutput]:
        """Collect outputs from all models."""
        import time
        
        outputs = []
        for name, generator in self.models.items():
            try:
                start = time.time()
                text = generator(prompt)
                latency = (time.time() - start) * 1000
                
                outputs.append(ModelOutput(
                    model_name=name,
                    text=text,
                    confidence=self.weights.get(name, 1.0),
                    latency_ms=latency,
                    metadata={},
                ))
            except Exception as e:
                outputs.append(ModelOutput(
                    model_name=name,
                    text="",
                    confidence=0.0,
                    latency_ms=0.0,
                    metadata={"error": str(e)},
                ))
        
        return outputs
    
    def _voting_combine(self, outputs: List[ModelOutput]) -> EnsembleResult:
        """Combine by voting on similarity."""
        # Simple: pick the output most similar to others
        if len(outputs) == 1:
            return EnsembleResult(
                final_text=outputs[0].text,
                strategy=EnsembleStrategy.VOTING,
                model_outputs=outputs,
                agreement_score=1.0,
                selected_model=outputs[0].model_name,
            )
        
        # Calculate pairwise similarity
        scores = {}
        for i, out1 in enumerate(outputs):
            total_sim = 0.0
            for j, out2 in enumerate(outputs):
                if i != j:
                    total_sim += self._text_similarity(out1.text, out2.text)
            scores[i] = total_sim
        
        # Select highest scoring
        best_idx = max(scores, key=scores.get)
        best = outputs[best_idx]
        
        return EnsembleResult(
            final_text=best.text,
            strategy=EnsembleStrategy.VOTING,
            model_outputs=outputs,
            agreement_score=scores[best_idx] / (len(outputs) - 1) if len(outputs) > 1 else 1.0,
            selected_model=best.model_name,
        )
    
    def _weighted_combine(self, outputs: List[ModelOutput]) -> EnsembleResult:
        """Combine with weighted selection."""
        valid_outputs = [o for o in outputs if o.text and o.confidence > 0]
        
        if not valid_outputs:
            return EnsembleResult(
                final_text="",
                strategy=EnsembleStrategy.WEIGHTED,
                model_outputs=outputs,
                agreement_score=0.0,
                selected_model=None,
            )
        
        # Select by highest weight
        best = max(valid_outputs, key=lambda x: x.confidence)
        
        return EnsembleResult(
            final_text=best.text,
            strategy=EnsembleStrategy.WEIGHTED,
            model_outputs=outputs,
            agreement_score=self._calculate_agreement(outputs),
            selected_model=best.model_name,
        )
    
    def _best_of_n(self, outputs: List[ModelOutput]) -> EnsembleResult:
        """Select best of N outputs."""
        # Use confidence as quality proxy
        valid = [o for o in outputs if o.text]
        if not valid:
            return EnsembleResult(
                final_text="",
                strategy=EnsembleStrategy.BEST_OF_N,
                model_outputs=outputs,
                agreement_score=0.0,
                selected_model=None,
            )
        
        best = max(valid, key=lambda x: x.confidence)
        
        return EnsembleResult(
            final_text=best.text,
            strategy=EnsembleStrategy.BEST_OF_N,
            model_outputs=outputs,
            agreement_score=self._calculate_agreement(outputs),
            selected_model=best.model_name,
        )
    
    def _consensus_combine(self, outputs: List[ModelOutput]) -> EnsembleResult:
        """Combine by finding consensus."""
        # For now, same as voting
        return self._voting_combine(outputs)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_agreement(self, outputs: List[ModelOutput]) -> float:
        """Calculate agreement score among outputs."""
        valid = [o for o in outputs if o.text]
        if len(valid) < 2:
            return 1.0
        
        total_sim = 0.0
        pairs = 0
        
        for i in range(len(valid)):
            for j in range(i + 1, len(valid)):
                total_sim += self._text_similarity(valid[i].text, valid[j].text)
                pairs += 1
        
        return total_sim / pairs if pairs > 0 else 0.0
