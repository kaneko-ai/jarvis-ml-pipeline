"""Prompt Registry.

Per RP-28, provides versioned prompt management.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PromptEntry:
    """A registered prompt."""

    prompt_id: str
    version: str
    template: str
    description: str = ""

    @property
    def prompt_hash(self) -> str:
        """Compute hash of template."""
        return hashlib.sha256(self.template.encode()).hexdigest()[:16]


class PromptRegistry:
    """Central registry for prompts."""

    def __init__(self):
        self._prompts: Dict[str, PromptEntry] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default prompts."""
        self.register(PromptEntry(
            prompt_id="paper_survey_retrieve",
            version="1.0",
            template="""You are a research assistant. Based on the query, identify key entities and concepts.

Query: {query}

Extract:
1. Main entities (genes, proteins, diseases)
2. Key relationships
3. Relevant search terms""",
            description="Paper survey retrieval prompt",
        ))

        self.register(PromptEntry(
            prompt_id="paper_survey_generate",
            version="1.0",
            template="""Based on the following evidence, generate a structured summary.

Evidence:
{evidence}

Requirements:
1. Each claim must cite its source
2. Distinguish facts from inferences
3. Note any gaps in evidence

Output as a structured list of claims.""",
            description="Paper survey generation prompt",
        ))

        self.register(PromptEntry(
            prompt_id="claim_check",
            version="1.0",
            template="""Verify if the following claim is supported by the evidence.

Claim: {claim}

Evidence:
{evidence}

Output: SUPPORTS, NOT_ENOUGH, or REFUTES with brief reason.""",
            description="Claim verification prompt",
        ))

    def register(self, entry: PromptEntry) -> None:
        """Register a prompt."""
        key = f"{entry.prompt_id}:{entry.version}"
        self._prompts[key] = entry

    def get(self, prompt_id: str, version: str = "1.0") -> PromptEntry:
        """Get a prompt by ID and version."""
        key = f"{prompt_id}:{version}"
        if key not in self._prompts:
            raise KeyError(f"Prompt not found: {key}")
        return self._prompts[key]

    def get_latest(self, prompt_id: str) -> PromptEntry:
        """Get latest version of a prompt."""
        matching = [k for k in self._prompts if k.startswith(f"{prompt_id}:")]
        if not matching:
            raise KeyError(f"Prompt not found: {prompt_id}")
        # Sort by version and get latest
        matching.sort(reverse=True)
        return self._prompts[matching[0]]

    def render(self, prompt_id: str, version: str = "1.0", **kwargs) -> str:
        """Render a prompt with variables."""
        entry = self.get(prompt_id, version)
        return entry.template.format(**kwargs)

    def list_all(self) -> list[str]:
        """List all registered prompt IDs."""
        return list(self._prompts.keys())


# Global registry
_registry: Optional[PromptRegistry] = None


def get_registry() -> PromptRegistry:
    """Get global prompt registry."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry
