"""
Lyra Supervisor Layer - Prompt & Reasoning Supervisor for JARVIS Research OS

Lyra is the Prompt & Reasoning Supervisor that:
- Audits all instructions for ambiguity, testability, and alignment
- Diagnoses worker AI outputs for reasoning depth and specification drift
- Rewrites instructions to eliminate ambiguity and enforce correctness
- Operates in a continuous DECONSTRUCT → DIAGNOSE → DEVELOP → DELIVER loop

Hard Rules:
- Never implement features directly
- Never accept vague success criteria
- If evidence, provenance, or evaluation is missing, flag as failure
- Prefer explicit constraints over assumed intelligence
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class IssueType(Enum):
    """Types of issues Lyra can detect."""

    AMBIGUOUS_SPEC = "ambiguous_specification"
    MISSING_CONSTRAINT = "missing_constraint"
    VAGUE_SUCCESS_CRITERIA = "vague_success_criteria"
    NO_PROVENANCE = "no_provenance"
    NO_EVALUATION = "no_evaluation"
    SPEC_DRIFT = "specification_drift"
    SHALLOW_REASONING = "shallow_reasoning"
    LAZY_IMPLEMENTATION = "lazy_implementation"
    MISSING_TEST = "missing_test"
    IMPLICIT_ASSUMPTION = "implicit_assumption"


class Severity(Enum):
    """Severity levels for detected issues."""

    CRITICAL = "critical"  # Must block
    HIGH = "high"  # Should block
    MEDIUM = "medium"  # Warning
    LOW = "low"  # Info


@dataclass
class Issue:
    """A detected issue in instructions or implementation."""

    type: IssueType
    severity: Severity
    location: str  # file:line or module.function
    description: str
    evidence: str  # What was found
    expected: str  # What should be
    suggestion: str  # How to fix
    confidence: float = 0.0  # 0-1


@dataclass
class DeconstructResult:
    """Result of the DECONSTRUCT phase."""

    core_intent: str
    key_entities: list[str]
    context: dict[str, Any]
    output_requirements: list[str]
    constraints: list[str]
    missing_info: list[str]
    ambiguities: list[str]


@dataclass
class DiagnoseResult:
    """Result of the DIAGNOSE phase."""

    issues: list[Issue]
    clarity_score: float  # 0-1
    completeness_score: float  # 0-1
    specificity_score: float  # 0-1
    structure_score: float  # 0-1
    overall_score: float  # 0-1
    blocks_execution: bool


@dataclass
class DevelopResult:
    """Result of the DEVELOP phase."""

    original_prompt: str
    optimized_prompt: str
    techniques_applied: list[str]
    role_assigned: str
    context_enhanced: bool
    structure_improved: bool
    changes_summary: list[str]


@dataclass
class DeliverResult:
    """Result of the DELIVER phase."""

    task_id: str
    target_worker: str  # antigravity, codex, llm
    prompt: str
    expected_output_format: str
    success_criteria: list[str]
    prohibited_actions: list[str]
    test_requirements: list[str]
    timeout_seconds: int
    priority: int


@dataclass
class SupervisionLog:
    """Audit log entry for Lyra supervision."""

    timestamp: str
    run_id: str
    supervisor: str = "Lyra"
    phase: str = ""
    issue_detected: str | None = None
    action: str | None = None
    confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class LyraSupervisor:
    """
    Lyra: The Prompt & Reasoning Supervisor for JARVIS Research OS.

    Operating Loop: DECONSTRUCT → DIAGNOSE → DEVELOP → DELIVER → repeat
    """

    SYSTEM_PROMPT = """You are Lyra, the Prompt & Reasoning Supervisor for JARVIS Research OS.

Your mission:
- Ensure all instructions are unambiguous, testable, and aligned with the JARVIS Master Spec.
- Continuously audit worker AI outputs for reasoning depth, specification drift, and missing constraints.
- When issues are found, rewrite the instruction or prompt to eliminate ambiguity and enforce correctness.

Hard rules:
- Never implement features yourself.
- Never accept vague success criteria.
- If evidence, provenance, or evaluation is missing, flag it as a failure.
- Prefer explicit constraints over assumed intelligence.

Operating loop:
DECONSTRUCT → DIAGNOSE → DEVELOP → DELIVER → repeat."""

    def __init__(self, audit_dir: Path | None = None):
        self.audit_dir = audit_dir or Path("artifacts/lyra_audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.logs: list[SupervisionLog] = []
        self.run_id = self._generate_run_id()

    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        now = datetime.utcnow().isoformat()
        return hashlib.sha256(now.encode()).hexdigest()[:12]

    def _log(
        self,
        phase: str,
        issue: str | None = None,
        action: str | None = None,
        confidence: float = 0.0,
        details: dict | None = None,
    ) -> None:
        """Add entry to audit log."""
        log = SupervisionLog(
            timestamp=datetime.utcnow().isoformat(),
            run_id=self.run_id,
            phase=phase,
            issue_detected=issue,
            action=action,
            confidence=confidence,
            details=details or {},
        )
        self.logs.append(log)

        # Append to audit.jsonl
        log_file = self.audit_dir / f"audit_{self.run_id}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log.__dict__, ensure_ascii=False) + "\n")

    # =========================================================================
    # PHASE 1: DECONSTRUCT
    # =========================================================================

    def deconstruct(self, instruction: str, context: dict | None = None) -> DeconstructResult:
        """
        DECONSTRUCT phase: Extract core intent, entities, and identify gaps.

        Args:
            instruction: The instruction/prompt to analyze
            context: Additional context (EPIC info, prior tasks, etc.)

        Returns:
            DeconstructResult with extracted information
        """
        context = context or {}

        # Extract core components
        core_intent = self._extract_core_intent(instruction)
        entities = self._extract_entities(instruction)
        output_reqs = self._extract_output_requirements(instruction)
        constraints = self._extract_constraints(instruction)
        missing = self._identify_missing_info(instruction, context)
        ambiguities = self._identify_ambiguities(instruction)

        result = DeconstructResult(
            core_intent=core_intent,
            key_entities=entities,
            context=context,
            output_requirements=output_reqs,
            constraints=constraints,
            missing_info=missing,
            ambiguities=ambiguities,
        )

        self._log(
            "DECONSTRUCT",
            f"Found {len(ambiguities)} ambiguities, {len(missing)} missing items",
            "Analysis complete",
            confidence=0.85,
            details={"entities": len(entities), "constraints": len(constraints)},
        )

        return result

    def _extract_core_intent(self, instruction: str) -> str:
        """Extract the core intent from instruction."""
        # Simple heuristic: first sentence or line
        lines = instruction.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                return line[:200]
        return instruction[:200]

    def _extract_entities(self, instruction: str) -> list[str]:
        """Extract key entities from instruction."""
        entities = []

        # Technical terms patterns
        keywords = [
            "plugin",
            "module",
            "function",
            "class",
            "API",
            "endpoint",
            "model",
            "pipeline",
            "config",
            "schema",
            "contract",
            "provenance",
            "evidence",
            "claim",
            "embedding",
            "rerank",
            "extraction",
            "summarization",
            "scoring",
            "evaluation",
        ]

        instruction_lower = instruction.lower()
        for kw in keywords:
            if kw.lower() in instruction_lower:
                entities.append(kw)

        return list(set(entities))

    def _extract_output_requirements(self, instruction: str) -> list[str]:
        """Extract output requirements."""
        requirements = []

        patterns = [
            ("必ず", "mandatory requirement"),
            ("返す", "return value"),
            ("出力", "output"),
            ("形式", "format"),
            ("JSON", "JSON format"),
            ("YAML", "YAML format"),
            ("スキーマ", "schema compliance"),
            ("evidence_links", "provenance required"),
        ]

        for pattern, req in patterns:
            if pattern in instruction:
                requirements.append(req)

        return requirements

    def _extract_constraints(self, instruction: str) -> list[str]:
        """Extract constraints from instruction."""
        constraints = []

        patterns = [
            ("禁止", "prohibition"),
            ("してはならない", "must not"),
            ("必須", "required"),
            ("閾値", "threshold"),
            ("タイムアウト", "timeout"),
            ("≥", "minimum threshold"),
            ("≤", "maximum threshold"),
        ]

        for pattern, constraint in patterns:
            if pattern in instruction:
                constraints.append(constraint)

        return constraints

    def _identify_missing_info(self, instruction: str, context: dict) -> list[str]:
        """Identify missing information."""
        missing = []

        # Check for essential elements
        checks = [
            (
                "success_criteria" not in instruction.lower() and "成功条件" not in instruction,
                "Success criteria not specified",
            ),
            (
                "test" not in instruction.lower() and "テスト" not in instruction,
                "Test requirements not specified",
            ),
            (
                "timeout" not in instruction.lower() and "タイムアウト" not in instruction,
                "Timeout not specified",
            ),
            (
                "error" not in instruction.lower() and "エラー" not in instruction,
                "Error handling not specified",
            ),
        ]

        for condition, msg in checks:
            if condition:
                missing.append(msg)

        return missing

    def _identify_ambiguities(self, instruction: str) -> list[str]:
        """Identify ambiguous phrases."""
        ambiguities = []

        vague_phrases = [
            ("適切に", "What does '適切に' mean specifically?"),
            ("必要に応じて", "When is it '必要'? Define conditions."),
            ("など", "What else is included in 'など'?"),
            ("etc", "What else is included?"),
            ("appropriate", "Define 'appropriate' explicitly"),
            ("as needed", "When is it needed? Define trigger"),
            ("properly", "Define 'properly' with measurable criteria"),
            ("good", "Define quality metrics"),
            ("better", "Define comparison baseline"),
        ]

        instruction_lower = instruction.lower()
        for phrase, question in vague_phrases:
            if phrase.lower() in instruction_lower:
                ambiguities.append(question)

        return ambiguities

    # =========================================================================
    # PHASE 2: DIAGNOSE
    # =========================================================================

    def diagnose(
        self, deconstruct_result: DeconstructResult, implementation: str | None = None
    ) -> DiagnoseResult:
        """
        DIAGNOSE phase: Audit for clarity gaps, ambiguity, and completeness.

        Args:
            deconstruct_result: Result from DECONSTRUCT phase
            implementation: Optional code/output to check against spec

        Returns:
            DiagnoseResult with issues and scores
        """
        issues: list[Issue] = []

        # Check for ambiguities
        for amb in deconstruct_result.ambiguities:
            issues.append(
                Issue(
                    type=IssueType.AMBIGUOUS_SPEC,
                    severity=Severity.HIGH,
                    location="instruction",
                    description=amb,
                    evidence="Vague phrase detected",
                    expected="Explicit, measurable criteria",
                    suggestion="Replace with specific definition",
                    confidence=0.85,
                )
            )

        # Check for missing info
        for missing in deconstruct_result.missing_info:
            issues.append(
                Issue(
                    type=IssueType.MISSING_CONSTRAINT,
                    severity=Severity.MEDIUM,
                    location="instruction",
                    description=missing,
                    evidence="Required information not found",
                    expected="Explicit specification",
                    suggestion="Add the missing specification",
                    confidence=0.80,
                )
            )

        # Check provenance requirement
        if "evidence" not in str(deconstruct_result.output_requirements).lower():
            issues.append(
                Issue(
                    type=IssueType.NO_PROVENANCE,
                    severity=Severity.CRITICAL,
                    location="instruction",
                    description="No provenance/evidence requirement",
                    evidence="evidence_links not mentioned",
                    expected="All outputs must include evidence_links",
                    suggestion="Add: 'Output must include evidence_links with doc_id, section, chunk_id, span'",
                    confidence=0.95,
                )
            )

        # Calculate scores
        clarity = 1.0 - (len(deconstruct_result.ambiguities) * 0.15)
        completeness = 1.0 - (len(deconstruct_result.missing_info) * 0.1)
        specificity = len(deconstruct_result.constraints) * 0.1
        structure = 0.7 if len(deconstruct_result.output_requirements) > 0 else 0.3

        clarity = max(0, min(1, clarity))
        completeness = max(0, min(1, completeness))
        specificity = max(0, min(1, specificity))

        overall = (clarity + completeness + specificity + structure) / 4

        # Determine if execution should be blocked
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        high_issues = [i for i in issues if i.severity == Severity.HIGH]
        blocks = len(critical_issues) > 0 or len(high_issues) >= 3

        result = DiagnoseResult(
            issues=issues,
            clarity_score=clarity,
            completeness_score=completeness,
            specificity_score=specificity,
            structure_score=structure,
            overall_score=overall,
            blocks_execution=blocks,
        )

        self._log(
            "DIAGNOSE",
            f"{len(issues)} issues found, {len(critical_issues)} critical",
            "Blocks execution" if blocks else "Passes with warnings",
            confidence=overall,
            details={"clarity": clarity, "completeness": completeness},
        )

        return result

    # =========================================================================
    # PHASE 3: DEVELOP
    # =========================================================================

    def develop(
        self, original_prompt: str, diagnose_result: DiagnoseResult, task_type: str = "technical"
    ) -> DevelopResult:
        """
        DEVELOP phase: Optimize the prompt based on diagnosis.

        Args:
            original_prompt: Original instruction/prompt
            diagnose_result: Result from DIAGNOSE phase
            task_type: "creative", "technical", "educational", "complex"

        Returns:
            DevelopResult with optimized prompt
        """
        techniques = []
        changes = []

        # Start with original
        optimized = original_prompt

        # Apply techniques based on task type
        if task_type == "technical":
            techniques.extend(["constraint-based", "precision-focus"])
            role = "expert software architect with domain expertise"
        elif task_type == "creative":
            techniques.extend(["multi-perspective", "tone-emphasis"])
            role = "creative specialist with analytical skills"
        elif task_type == "educational":
            techniques.extend(["few-shot-examples", "clear-structure"])
            role = "expert educator and technical writer"
        else:  # complex
            techniques.extend(["chain-of-thought", "systematic-framework"])
            role = "systems architect with holistic perspective"

        # Add role assignment if missing
        if "あなたは" not in optimized and "You are" not in optimized:
            role_prefix = f"You are a {role}.\n\n"
            optimized = role_prefix + optimized
            changes.append("Added role assignment")

        # Add provenance requirement if missing
        if "evidence_links" not in optimized:
            provenance_section = """

## Provenance Requirement (MANDATORY)
All outputs MUST include evidence_links in the following format:
```json
{
  "claim_id": "c-XXX",
  "claim_text": "...",
  "evidence": [
    {"doc_id": "...", "section": "...", "chunk_id": "...", "start": N, "end": N, "confidence": 0.X}
  ]
}
```
Outputs without evidence_links will be REJECTED.
"""
            optimized += provenance_section
            changes.append("Added provenance requirement")
            techniques.append("provenance-enforcement")

        # Add success criteria if missing
        if "成功条件" not in optimized and "success criteria" not in optimized.lower():
            success_section = """

## Success Criteria (MANDATORY)
1. All outputs must be verifiable against source documents
2. No assertions without evidence_links
3. All code must pass type checking
4. All functions must have docstrings
5. Tests must cover the happy path and edge cases
"""
            optimized += success_section
            changes.append("Added success criteria")
            techniques.append("explicit-success-criteria")

        # Add prohibited actions
        if "禁止" not in optimized and "prohibited" not in optimized.lower():
            prohibited_section = """

## Prohibited Actions
- Making assertions without evidence
- Using vague terms like "適切に", "必要に応じて", "etc"
- Implementing without tests
- Skipping error handling
- Assuming implicit requirements
"""
            optimized += prohibited_section
            changes.append("Added prohibited actions")

        result = DevelopResult(
            original_prompt=original_prompt,
            optimized_prompt=optimized,
            techniques_applied=techniques,
            role_assigned=role,
            context_enhanced=True,
            structure_improved=len(changes) > 0,
            changes_summary=changes,
        )

        self._log(
            "DEVELOP",
            None,
            f"Applied {len(techniques)} techniques, made {len(changes)} changes",
            confidence=0.90,
            details={"techniques": techniques, "changes": changes},
        )

        return result

    # =========================================================================
    # PHASE 4: DELIVER
    # =========================================================================

    def deliver(
        self,
        develop_result: DevelopResult,
        target_worker: str = "antigravity",
        priority: int = 1,
        timeout: int = 300,
    ) -> DeliverResult:
        """
        DELIVER phase: Construct and deliver the optimized task.

        Args:
            develop_result: Result from DEVELOP phase
            target_worker: Target AI (antigravity, codex, llm)
            priority: Task priority (1=highest)
            timeout: Timeout in seconds

        Returns:
            DeliverResult ready for execution
        """
        task_id = f"task-{self.run_id}-{datetime.utcnow().strftime('%H%M%S')}"

        result = DeliverResult(
            task_id=task_id,
            target_worker=target_worker,
            prompt=develop_result.optimized_prompt,
            expected_output_format="JSON with evidence_links",
            success_criteria=[
                "All outputs include evidence_links",
                "No vague assertions",
                "Code passes all tests",
                "Documentation is complete",
            ],
            prohibited_actions=[
                "Making claims without evidence",
                "Using vague language",
                "Skipping tests",
                "Ignoring error cases",
            ],
            test_requirements=[
                "Unit tests for all functions",
                "Contract tests for I/O",
                "Golden tests for reproducibility",
            ],
            timeout_seconds=timeout,
            priority=priority,
        )

        self._log(
            "DELIVER",
            None,
            f"Task {task_id} dispatched to {target_worker}",
            confidence=0.95,
            details={"task_id": task_id, "priority": priority},
        )

        return result

    # =========================================================================
    # FULL LOOP
    # =========================================================================

    def supervise(
        self,
        instruction: str,
        context: dict | None = None,
        target_worker: str = "antigravity",
        task_type: str = "technical",
    ) -> DeliverResult:
        """
        Run the full supervision loop: DECONSTRUCT → DIAGNOSE → DEVELOP → DELIVER

        Args:
            instruction: The original instruction
            context: Additional context
            target_worker: Target AI worker
            task_type: Type of task

        Returns:
            DeliverResult ready for execution
        """
        # Phase 1: DECONSTRUCT
        deconstruct = self.deconstruct(instruction, context)

        # Phase 2: DIAGNOSE
        diagnose = self.diagnose(deconstruct)

        # If critical issues, raise before developing
        if diagnose.blocks_execution:
            critical = [i for i in diagnose.issues if i.severity == Severity.CRITICAL]
            self._log(
                "BLOCKED",
                f"Execution blocked due to {len(critical)} critical issues",
                "Requires human intervention",
                confidence=0.99,
            )
            # Still develop a corrected version

        # Phase 3: DEVELOP
        develop = self.develop(instruction, diagnose, task_type)

        # Phase 4: DELIVER
        deliver = self.deliver(develop, target_worker)

        return deliver

    def get_audit_summary(self) -> dict[str, Any]:
        """Get summary of all supervision logs."""
        return {
            "run_id": self.run_id,
            "total_logs": len(self.logs),
            "phases": {
                "DECONSTRUCT": len([l for l in self.logs if l.phase == "DECONSTRUCT"]),
                "DIAGNOSE": len([l for l in self.logs if l.phase == "DIAGNOSE"]),
                "DEVELOP": len([l for l in self.logs if l.phase == "DEVELOP"]),
                "DELIVER": len([l for l in self.logs if l.phase == "DELIVER"]),
                "BLOCKED": len([l for l in self.logs if l.phase == "BLOCKED"]),
            },
            "issues_detected": len([l for l in self.logs if l.issue_detected]),
            "avg_confidence": (
                sum(l.confidence for l in self.logs) / len(self.logs) if self.logs else 0
            ),
        }


# Factory function
def get_lyra_supervisor(audit_dir: Path | None = None) -> LyraSupervisor:
    """Get Lyra supervisor instance."""
    return LyraSupervisor(audit_dir)


# Singleton for global access
_lyra_instance: LyraSupervisor | None = None


def get_lyra() -> LyraSupervisor:
    """Get global Lyra supervisor instance."""
    global _lyra_instance
    if _lyra_instance is None:
        _lyra_instance = LyraSupervisor()
    return _lyra_instance