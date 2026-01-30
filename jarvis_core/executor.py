"""Lightweight execution engine for sequencing subtasks."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .budget import BudgetPolicy, BudgetSpec, BudgetTracker
from .evidence import EvidenceStore
from .planner import Planner
from .retry import RetryPolicy
from .task import Task, TaskStatus
from .validation import EvaluationResult

logger = logging.getLogger("jarvis_core.executor")

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .router import Router


class ExecutionEngine:
    """Coordinate planning and sequential execution via the router.

    This engine is the final arbiter of AgentResult status.
    Per JARVIS_MASTER.md Section 5.4.1, the ExecutionEngine:
    - Normalizes agent-provided status based on quality rules
    - Validates citations against EvidenceStore per Section 5.4.2
    - Ensures status accurately reflects output quality
    - Is the single source of truth for evidence (EvidenceStore)
    """

    def __init__(
        self,
        planner: Planner,
        router: Router,
        retry_policy: RetryPolicy | None = None,
        validator: Callable[[object], EvaluationResult] | None = None,
        evidence_store: EvidenceStore | None = None,
        budget_spec: BudgetSpec | None = None,
    ) -> None:
        self.planner = planner
        self.router = router
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=1)
        self.validator = validator
        self.evidence_store = evidence_store or EvidenceStore()
        self.budget_spec = budget_spec or BudgetSpec()
        self.budget_policy = BudgetPolicy()
        self._current_tracker: BudgetTracker | None = None

    def run(self, root_task: Task) -> list[Task]:
        """Plan and execute a root task, returning executed subtasks."""
        # Budget tracker initialization
        self._current_tracker = BudgetTracker()
        self._current_tracker.log("run_start", task_id=root_task.task_id)

        subtasks = self.planner.plan(root_task)
        executed: list[Task] = []

        for subtask in subtasks:
            if subtask.status == TaskStatus.PENDING:
                subtask.status = TaskStatus.RUNNING
            subtask.history.append({"event": "start", "status": subtask.status})

            result, evaluation, attempts = self._execute_with_retry(subtask)
            subtask.result = result

            # Normalize AgentResult status per quality rules
            normalized_status, quality_warnings = self._normalize_agent_result(result)

            final_status = TaskStatus.DONE
            if normalized_status == "fail":
                final_status = TaskStatus.FAILED
            elif evaluation and not evaluation.ok:
                final_status = TaskStatus.FAILED

            subtask.history.append(
                {
                    "event": "complete",
                    "status": final_status,
                    "agent_status": normalized_status,
                    "result": getattr(result, "answer", None),
                    "citations": [
                        c.__dict__ if hasattr(c, "__dict__") else str(c)
                        for c in getattr(result, "citations", [])
                    ],
                    "quality_warnings": quality_warnings if quality_warnings else None,
                    "attempts": attempts,
                }
            )
            subtask.status = final_status
            executed.append(subtask)

            if final_status == TaskStatus.FAILED:
                err_msg = (
                    evaluation.errors[0]
                    if evaluation and evaluation.errors
                    else "Subtask failed without specific error"
                )
                raise RuntimeError(err_msg)

        return executed

    def _normalize_agent_result(self, result: Any) -> tuple[str, list[str]]:
        """Normalize AgentResult status per JARVIS_MASTER.md Section 5.4.1.

        This is the final arbiter of status. Agent-provided status is a suggestion;
        the ExecutionEngine enforces quality rules.

        Args:
            result: The AgentResult from an agent.

        Returns:
            Tuple of (normalized_status, quality_warnings).
        """
        warnings: list[str] = []

        # Get raw values
        answer = getattr(result, "answer", None) or ""
        citations = getattr(result, "citations", []) or []
        agent_status = getattr(result, "status", "success")

        # Rule 1: No answer = fail
        if not answer.strip():
            return "fail", ["empty_answer"]

        # Rule 2: Validate citations
        valid_citations, citation_warnings = self._validate_citations(citations)
        warnings.extend(citation_warnings)

        # Update the result with validated citations from EvidenceStore
        if hasattr(result, "citations"):
            result.citations = valid_citations

        # Rule 3: Answer exists but no valid citations = partial
        # Per Section 5.4.2: citations required for fact claims
        if not valid_citations:
            if agent_status == "success":
                warnings.append("no_valid_citations")
            return "partial", warnings

        # Rule 4: Check citation-answer relevance (RP10)
        # Verify that citations are actually relevant to the answer
        relevance_ok, relevance_warnings = self._check_citation_relevance(answer, valid_citations)
        warnings.extend(relevance_warnings)

        if not relevance_ok:
            return "partial", warnings

        # Rule 5: All checks pass = success
        if agent_status == "fail":
            # Agent explicitly failed but we have valid output
            warnings.append("agent_reported_fail_but_output_valid")
            return "partial", warnings

        return "success", warnings

    def _validate_citations(self, citations: list[Any]) -> tuple[list[Any], list[str]]:
        """Validate citations against EvidenceStore per JARVIS_MASTER.md Section 5.4.2.

        This method:
        1. Checks required fields on each citation
        2. Validates chunk_id exists in EvidenceStore
        3. Regenerates quote from EvidenceStore (agent quotes are not trusted)

        Args:
            citations: List of Citation objects from agent.

        Returns:
            Tuple of (valid_citations, warnings).
        """
        from .agents import Citation

        valid: list[Any] = []
        warnings: list[str] = []

        for i, citation in enumerate(citations):
            # Check required fields
            chunk_id = getattr(citation, "chunk_id", None) or ""

            # If no chunk_id, cannot validate against EvidenceStore
            if not chunk_id.strip():
                warnings.append(f"citation[{i}]_missing_chunk_id")
                continue

            # Validate chunk exists in EvidenceStore
            chunk = self.evidence_store.get_chunk(chunk_id)
            if not chunk:
                warnings.append(f"citation[{i}]_chunk_not_in_evidence_store")
                continue

            # Generate authoritative quote from EvidenceStore
            # Agent-provided quote is NOT trusted
            authoritative_quote = self.evidence_store.get_quote(chunk_id)

            # Create validated citation with authoritative values
            validated_citation = Citation(
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                locator=chunk.locator,
                quote=authoritative_quote,
            )
            valid.append(validated_citation)

        return valid, warnings

    def _check_citation_relevance(
        self,
        answer: str,
        valid_citations: list[Any],
        min_token_overlap: int = 2,
    ) -> tuple[bool, list[str]]:
        """Check that citations are relevant to the answer (RP10).

        This performs a minimal token overlap check to ensure that
        cited evidence is actually reflected in the answer.

        Args:
            answer: The answer text from agent.
            valid_citations: List of validated Citation objects.
            min_token_overlap: Minimum token overlap required per citation.

        Returns:
            Tuple of (relevance_ok, warnings).
        """
        from .retriever import tokenize

        warnings: list[str] = []
        answer_tokens = set(tokenize(answer))

        if not answer_tokens:
            return True, []  # Can't check empty answer

        total_overlap = 0
        citations_with_overlap = 0

        for i, citation in enumerate(valid_citations):
            chunk_id = getattr(citation, "chunk_id", "")
            chunk = self.evidence_store.get_chunk(chunk_id)

            if not chunk:
                continue

            chunk_tokens = set(tokenize(chunk.text))
            overlap = answer_tokens & chunk_tokens

            if len(overlap) >= min_token_overlap:
                citations_with_overlap += 1
                total_overlap += len(overlap)
            else:
                warnings.append(f"citation[{i}]_low_relevance_overlap:{len(overlap)}")

        # At least one citation must have sufficient overlap
        if citations_with_overlap == 0:
            warnings.append("no_citations_with_sufficient_relevance")
            return False, warnings

        return True, warnings

    def run_and_get_answer(self, root_task: Task) -> str:
        """Execute a root task and return the final answer as a string.

        This is a thin convenience wrapper around :meth:`run` that extracts
        the answer from the last executed subtask. It simplifies call sites
        that only need the final textual result.

        Args:
            root_task: The root task to execute.

        Returns:
            The answer string from the last subtask, or an empty string
            if no answer was produced.
        """
        executed = self.run(root_task)
        if not executed:
            return ""

        last_task = executed[-1]
        answer = ""
        for event in reversed(last_task.history):
            if event.get("event") == "complete" and event.get("result"):
                answer = str(event["result"])
                break

        # Budget: append budget summary if degraded
        if self._current_tracker and self._current_tracker.degraded:
            budget_info = self._current_tracker.to_summary(self.budget_spec)
            answer += (
                f"\n\n---\n**Budget**: {budget_info['tool_calls']} tool calls, "
                f"degraded due to: {', '.join(budget_info['degrade_reasons'] or [])}"
            )

        return answer

    def _execute_with_retry(
        self,
        subtask: Task,
    ) -> tuple[object | None, EvaluationResult | None, int]:
        """Execute a subtask with optional validation and retry policy."""

        attempt = 1
        last_result: object | None = None
        last_evaluation: EvaluationResult | None = None

        while True:
            # Budget: record tool call
            if self._current_tracker:
                self._current_tracker.record_tool_call()

            try:
                last_result = self.router.run(subtask)

                # Use provided validator or fallback to status-based check (RP-02)
                if self.validator:
                    last_evaluation = self.validator(last_result)
                else:
                    # Check status if available (e.g. AgentResult)
                    status = getattr(last_result, "status", "success")
                    is_ok = status != "fail"
                    errors = []
                    if not is_ok:
                        meta = getattr(last_result, "meta", {}) or {}
                        # Extract detailed warnings from agent meta
                        errors = meta.get("warnings", ["agent_reported_fail"])

                    last_evaluation = EvaluationResult(ok=is_ok, errors=errors)

            except Exception as e:
                logger.warning("Execution error at attempt %d: %s", attempt, e)
                last_result = None
                last_evaluation = EvaluationResult(ok=False, errors=[str(e)])

            decision = self.retry_policy.decide(last_evaluation, attempt=attempt)

            # Budget: check if retry is allowed
            budget_allows_retry = True
            if self._current_tracker:
                budget_decision = self.budget_policy.decide(self.budget_spec, self._current_tracker)
                budget_allows_retry = budget_decision.allow_retry
                if not budget_allows_retry:
                    self._current_tracker.record_degrade("budget_retry_blocked")
                    logger.info(
                        "Budget blocked retry for task %s: %s",
                        subtask.id,
                        budget_decision.degrade_reason,
                    )

            if not decision.should_retry or not budget_allows_retry:
                return last_result, last_evaluation, attempt

            # Budget: record retry
            if self._current_tracker:
                self._current_tracker.record_retry()

            attempt += 1