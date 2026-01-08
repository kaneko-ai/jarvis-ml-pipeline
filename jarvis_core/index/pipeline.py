"""Index Pipeline.

Per V4.2 Sprint 2, this provides staged indexing: ingest→normalize→chunk→index.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PipelineStage(Enum):
    """Index pipeline stages."""

    INGEST = "ingest"
    NORMALIZE = "normalize"
    CHUNK = "chunk"
    INDEX = "index"


@dataclass
class StageResult:
    """Result of a pipeline stage."""

    stage: PipelineStage
    input_count: int
    output_count: int
    skipped_count: int
    duration_ms: float
    outputs: list[Any] = field(default_factory=list)


class IndexPipeline:
    """Staged indexing pipeline with incremental support."""

    def __init__(self):
        self.stages: dict[PipelineStage, Callable] = {}
        self.results: dict[PipelineStage, StageResult] = {}

    def register_stage(
        self,
        stage: PipelineStage,
        fn: Callable[[list[Any]], list[Any]],
    ) -> None:
        """Register a stage processor."""
        self.stages[stage] = fn

    def run_stage(
        self,
        stage: PipelineStage,
        inputs: list[Any],
        state: IncrementalState | None = None,
    ) -> StageResult:
        """Run a single stage.

        Args:
            stage: Stage to run.
            inputs: Input items.
            state: Optional incremental state for skipping.

        Returns:
            StageResult with outputs.
        """
        import time

        from ..perf.trace_spans import end_span, start_span

        span_id = start_span(f"index:{stage.value}")
        start_time = time.time()

        # Filter already processed items if state provided
        to_process = inputs
        skipped = []

        if state:
            to_process = []
            for item in inputs:
                item_hash = state.compute_item_hash(item)
                if state.is_processed(stage.value, item_hash):
                    skipped.append(item)
                else:
                    to_process.append(item)

        # Run stage processor
        if stage in self.stages and to_process:
            outputs = self.stages[stage](to_process)
        else:
            outputs = to_process

        # Mark as processed
        if state:
            for item in to_process:
                item_hash = state.compute_item_hash(item)
                state.mark_processed(stage.value, item_hash)

        duration = (time.time() - start_time) * 1000
        end_span(span_id, item_count=len(outputs))

        result = StageResult(
            stage=stage,
            input_count=len(inputs),
            output_count=len(outputs),
            skipped_count=len(skipped),
            duration_ms=duration,
            outputs=outputs,
        )

        self.results[stage] = result
        return result

    def run_all(
        self,
        inputs: list[Any],
        state: IncrementalState | None = None,
    ) -> dict[PipelineStage, StageResult]:
        """Run all stages in order.

        Args:
            inputs: Initial inputs.
            state: Optional incremental state.

        Returns:
            Dict of stage -> result.
        """
        current = inputs

        for stage in [PipelineStage.INGEST, PipelineStage.NORMALIZE,
                      PipelineStage.CHUNK, PipelineStage.INDEX]:
            result = self.run_stage(stage, current, state)
            current = result.outputs

        return self.results

    def get_summary(self) -> dict:
        """Get pipeline summary."""
        summary = {}
        for stage, result in self.results.items():
            summary[stage.value] = {
                "input": result.input_count,
                "output": result.output_count,
                "skipped": result.skipped_count,
                "duration_ms": round(result.duration_ms, 2),
            }
        return summary


# Default stage processors
def default_ingest(items: list[Any]) -> list[Any]:
    """Default ingest: pass through."""
    return items


def default_normalize(items: list[Any]) -> list[Any]:
    """Default normalize: lowercase text."""
    results = []
    for item in items:
        if isinstance(item, str):
            results.append(item.lower())
        elif isinstance(item, dict) and "text" in item:
            item["text"] = item["text"].lower()
            results.append(item)
        else:
            results.append(item)
    return results


def default_chunk(items: list[Any], chunk_size: int = 500) -> list[Any]:
    """Default chunk: split text into chunks."""
    chunks = []
    for item in items:
        text = item if isinstance(item, str) else item.get("text", str(item))
        words = text.split()

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunks.append({"text": " ".join(chunk_words), "source": str(item)[:50]})

    return chunks


def create_default_pipeline() -> IndexPipeline:
    """Create pipeline with default processors."""
    pipeline = IndexPipeline()
    pipeline.register_stage(PipelineStage.INGEST, default_ingest)
    pipeline.register_stage(PipelineStage.NORMALIZE, default_normalize)
    pipeline.register_stage(PipelineStage.CHUNK, default_chunk)
    return pipeline
