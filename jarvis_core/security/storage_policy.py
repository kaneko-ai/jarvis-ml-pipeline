"""Storage Policy.

Per V4.2 Sprint 3, this enforces PII storage rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StorageRule(Enum):
    """Storage rules for sensitive data."""

    ALLOW = "allow"  # Can store as-is
    REDACT = "redact"  # Must redact before storing
    HASH = "hash"  # Store hash only
    DENY = "deny"  # Cannot store


@dataclass
class StoragePolicy:
    """Policy for storing sensitive data."""

    # Default rules by PII type
    pii_rules: dict[str, StorageRule] = field(
        default_factory=lambda: {
            "email": StorageRule.REDACT,
            "phone": StorageRule.REDACT,
            "ssn": StorageRule.DENY,
            "credit_card": StorageRule.DENY,
            "name": StorageRule.ALLOW,
            "ip_address": StorageRule.HASH,
        }
    )

    # Fields to always redact
    redact_fields: list[str] = field(
        default_factory=lambda: [
            "api_key",
            "password",
            "token",
            "secret",
        ]
    )

    # Whether to log redactions
    log_redactions: bool = True

    def get_rule(self, pii_type: str) -> StorageRule:
        """Get storage rule for PII type."""
        return self.pii_rules.get(pii_type, StorageRule.REDACT)

    def should_redact_field(self, field_name: str) -> bool:
        """Check if field should be redacted."""
        field_lower = field_name.lower()
        return any(r in field_lower for r in self.redact_fields)


@dataclass
class PolicyCheckResult:
    """Result of policy check."""

    compliant: bool
    violations: list[str]
    actions_taken: list[str]


def check_storage_policy(
    data: dict,
    policy: StoragePolicy = None,
) -> PolicyCheckResult:
    """Check data against storage policy.

    Args:
        data: Data to check.
        policy: Storage policy.

    Returns:
        PolicyCheckResult.
    """
    from .pii_scan import PIIScanner

    policy = policy or StoragePolicy()
    scanner = PIIScanner()

    violations = []
    actions = []

    def check_value(key: str, value: Any, path: str = ""):
        full_path = f"{path}.{key}" if path else key

        # Check if field should be redacted by name
        if policy.should_redact_field(key) and value:
            violations.append(f"Sensitive field not redacted: {full_path}")

        # Check for PII in string values
        if isinstance(value, str):
            matches = scanner.scan(value)
            for match in matches:
                rule = policy.get_rule(match.pii_type.value)
                if rule == StorageRule.DENY:
                    violations.append(f"PII ({match.pii_type.value}) not allowed: {full_path}")
                elif rule != StorageRule.ALLOW:
                    actions.append(f"Should {rule.value} {match.pii_type.value} in {full_path}")

        # Recurse into nested structures
        elif isinstance(value, dict):
            for k, v in value.items():
                check_value(k, v, full_path)

        elif isinstance(value, list):
            for i, item in enumerate(value):
                check_value(f"[{i}]", item, full_path)

    for key, value in data.items():
        check_value(key, value)

    return PolicyCheckResult(
        compliant=len(violations) == 0,
        violations=violations,
        actions_taken=actions,
    )


def apply_storage_policy(
    data: dict,
    policy: StoragePolicy = None,
) -> dict:
    """Apply storage policy to data.

    Args:
        data: Data to process.
        policy: Storage policy.

    Returns:
        Policy-compliant data.
    """
    from .redaction import Redactor

    policy = policy or StoragePolicy()
    redactor = Redactor()

    return redactor.redact_dict(data)
