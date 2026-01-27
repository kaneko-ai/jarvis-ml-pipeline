"""Rules engine for global and workspace rules."""
from __future__ import annotations

import textwrap
from dataclasses import asdict
from pathlib import Path

from .schema import Rule, RuleScope


class RulesEngine:
    """Load and provide rules for LLM context."""

    def __init__(self, workspace_path: Path | None) -> None:
        self.workspace_path = Path(workspace_path) if workspace_path else None
        self._rules: dict[str, Rule] = {}
        self._loaded = False

    def load_rules(self) -> None:
        if self._loaded:
            return
        self._rules.clear()
        global_path = Path("~/.gemini/GEMINI.md").expanduser()
        if global_path.exists():
            rule = Rule(
                name=global_path.stem,
                scope=RuleScope.GLOBAL,
                path=global_path,
                content=global_path.read_text(encoding="utf-8"),
                enabled=True,
            )
            self._rules[rule.name] = rule
        if self.workspace_path:
            workspace_dir = self.workspace_path / ".agent" / "rules"
            if workspace_dir.exists():
                for rule_path in sorted(workspace_dir.glob("*.md")):
                    rule = Rule(
                        name=rule_path.stem,
                        scope=RuleScope.WORKSPACE,
                        path=rule_path,
                        content=rule_path.read_text(encoding="utf-8"),
                        enabled=True,
                    )
                    self._rules[rule.name] = rule
        self._loaded = True

    def get_context_for_llm(self) -> str:
        self.load_rules()
        sections = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            header = f"## Rule: {rule.name} ({rule.scope.value})"
            sections.append("\n".join([header, rule.content.strip()]))
        return textwrap.dedent("\n\n".join(sections)).strip()

    def list_rules(self) -> list[dict]:
        self.load_rules()
        output = []
        for rule in self._rules.values():
            data = asdict(rule)
            data["scope"] = rule.scope.value
            data["path"] = str(rule.path)
            output.append(data)
        return sorted(output, key=lambda item: item.get("name", ""))
