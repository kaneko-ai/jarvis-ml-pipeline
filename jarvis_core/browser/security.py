"""Security policy handling for browser automation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from jarvis_core.browser.schema import SecurityPolicy

_DEFAULT_ALLOW_LIST = [
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "arxiv.org",
    "doi.org",
    "europepmc.org",
    "semanticscholar.org",
]


@dataclass
class BrowserSecurityManager:
    """Manage browser security policies."""

    policy: SecurityPolicy

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BrowserSecurityManager":
        data = {}
        if path:
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        policy = SecurityPolicy(
            js_execution=bool(data.get("js_execution", False)),
            url_allow_list=list(data.get("url_allow_list", _DEFAULT_ALLOW_LIST)),
            url_deny_list=list(data.get("url_deny_list", [])),
        )
        return cls(policy=policy)

    def check_url(self, url: str) -> bool:
        """Return True when URL is allowed."""
        for denied in self.policy.url_deny_list:
            if denied and denied in url:
                return False
        if not self.policy.url_allow_list:
            return True
        return any(allowed in url for allowed in self.policy.url_allow_list)

    def check_js_execution(self, script: str) -> tuple[bool, str]:
        """Return whether JS execution is allowed and message."""
        if not self.policy.js_execution:
            return False, "JavaScript execution disabled by security policy."
        if self._contains_blocked_patterns(
            script, ["document.cookie", "localStorage", "sessionStorage"]
        ):
            return False, "Script contains blocked storage access patterns."
        return True, "Allowed"

    @staticmethod
    def _contains_blocked_patterns(script: str, patterns: Iterable[str]) -> bool:
        script_lower = script.lower()
        return any(pattern.lower() in script_lower for pattern in patterns)
