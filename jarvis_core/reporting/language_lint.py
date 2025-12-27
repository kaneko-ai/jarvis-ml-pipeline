"""Language Lint for Report Quality (Phase 2-ΩΩ).

Checks report text for forbidden language patterns and enforces
hedging requirements based on uncertainty levels.
"""
from pathlib import Path
from typing import List, Dict, Any
import yaml
import logging

logger = logging.getLogger(__name__)


class LanguageLinter:
    """Lint report language for quality violations."""
    
    def __init__(self, rules_path: Path = None):
        """Initialize linter with language rules.
        
        Args:
            rules_path: Path to LANGUAGE_RULES.yaml
        """
        if rules_path is None:
            rules_path = Path(__file__).parent.parent.parent / "docs" / "LANGUAGE_RULES.yaml"
        
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)
    
    def lint_text(self, text: str) -> List[Dict[str, Any]]:
        """Lint text for language violations.
        
        Args:
            text: Text to lint
            
        Returns:
            List of violation dicts
        """
        violations = []
        text_lower = text.lower()
        
        # Check forbidden terms (English)
        forbidden = self.rules.get("forbidden", [])
        for term in forbidden:
            if term.lower() in text_lower:
                violations.append({
                    "code": "LANGUAGE_VIOLATION",
                    "severity": "error",
                    "term": term,
                    "message": f"Forbidden causal term: '{term}'"
                })
        
        # Check forbidden terms (Japanese)
        forbidden_ja = self.rules.get("forbidden_ja", [])
        for term in forbidden_ja:
            if term in text:
                violations.append({
                    "code": "LANGUAGE_VIOLATION",
                    "severity": "error",
                    "term": term,
                    "message": f"禁止された断定表現: '{term}'"
                })
        
        return violations
    
    def check_hedging_required(
        self,
        text: str,
        uncertainty_label: str
    ) -> List[Dict[str, Any]]:
        """Check if hedging is required and present.
        
        Args:
            text: Text to check
            uncertainty_label: Uncertainty label
            
        Returns:
            List of violation dicts
        """
        violations = []
        
        # If uncertainty is high, hedging is required
        if uncertainty_label in ["要注意", "推測"]:
            hedging_terms = self.rules.get("conditional_required", []) + \
                           self.rules.get("conditional_required_ja", [])
            
            has_hedging = any(term in text.lower() for term in hedging_terms)
            
            if not has_hedging:
                violations.append({
                    "code": "HEDGING_REQUIRED",
                    "severity": "warning",
                    "message": f"Uncertainty={uncertainty_label} requires hedging language"
                })
        
        return violations
    
    def lint_report(self, report_path: Path) -> List[Dict[str, Any]]:
        """Lint an entire report file.
        
        Args:
            report_path: Path to report.md
            
        Returns:
            List of all violations
        """
        with open(report_path, "r", encoding="utf-8") as f:
            report_text = f.read()
        
        violations = self.lint_text(report_text)
        
        logger.info(f"Report lint: {len(violations)} violations found")
        
        return violations


def lint_report_fail_on_error(report_path: Path) -> bool:
    """Lint report and fail if errors found.
    
    Args:
        report_path: Path to report
        
    Returns:
        True if passed, False if failed
    """
    linter = LanguageLinter()
    violations = linter.lint_report(report_path)
    
    errors = [v for v in violations if v["severity"] == "error"]
    
    if errors:
        print(f"LANGUAGE LINT FAILED: {len(errors)} errors")
        for error in errors:
            print(f"  - {error['message']}")
        return False
    else:
        warnings = [v for v in violations if v["severity"] == "warning"]
        if warnings:
            print(f"LANGUAGE LINT PASSED with {len(warnings)} warnings")
        else:
            print("LANGUAGE LINT PASSED")
        return True
