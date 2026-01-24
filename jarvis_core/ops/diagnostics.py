"""Diagnostics Module (Phase 33).

Analyzes failed runs to determine root causes and suggest recovery actions.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DiagnosticResult:
    """Result of a diagnostic analysis."""
    run_id: str
    error_type: str
    root_cause: str
    suggested_action: str
    is_recoverable: bool

class RunDiagnostics:
    """Analyzer for failed pipeline runs."""

    def analyze(self, summary: Dict[str, Any], checkpoint: Optional[Dict[str, Any]] = None) -> DiagnosticResult:
        """Analyze run artifacts to diagnose failure."""
        run_id = summary.get("run_id", "unknown")
        errors = summary.get("errors", [])
        
        if not errors:
            return DiagnosticResult(
                run_id=run_id,
                error_type="None",
                root_cause="No errors reported in summary",
                suggested_action="Check logs for silent failures",
                is_recoverable=False
            )

        # Naive first error analysis
        # In real world, we'd parse traceback or multiple errors
        primary_error = errors[0]
        
        return self._classify_error(run_id, primary_error, checkpoint)

    def _classify_error(self, run_id: str, error_msg: str, checkpoint: Optional[Dict]) -> DiagnosticResult:
        """Heuristic error classification."""
        error_msg_lower = error_msg.lower()
        
        if "timeout" in error_msg_lower or "gateway timeout" in error_msg_lower:
            return DiagnosticResult(
                run_id=run_id,
                error_type="NetworkTimeout",
                root_cause="External API or Network timed out",
                suggested_action="Retry with exponential backoff",
                is_recoverable=True
            )
            
        if "ratelimit" in error_msg_lower or "429" in error_msg_lower:
            return DiagnosticResult(
                run_id=run_id,
                error_type="RateLimit",
                root_cause="API Rate limit exceeded",
                suggested_action="Wait and retry (check quota)",
                is_recoverable=True
            )
            
        if "jsondecodeerror" in error_msg_lower:
            return DiagnosticResult(
                run_id=run_id,
                error_type="DataFormatError",
                root_cause="Invalid JSON response or file",
                suggested_action="Check input data source integrity",
                is_recoverable=False # Usually requires code fix or data fix
            )
            
        if "filenotfound" in error_msg_lower:
             return DiagnosticResult(
                run_id=run_id,
                error_type="MissingResource",
                root_cause="Required file not found",
                suggested_action="Verify file paths and permissions",
                is_recoverable=False
            )

        # Default fallback
        return DiagnosticResult(
            run_id=run_id,
            error_type="UnknownError",
            root_cause=f"Unclassified: {error_msg[:100]}...",
            suggested_action="Manual investigation required",
            is_recoverable=False
        )
