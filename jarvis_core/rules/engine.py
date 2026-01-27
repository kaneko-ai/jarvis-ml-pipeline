"""Rules engine for loading global and workspace rules."""

from __future__ import annotations

from pathlib import Path

from jarvis_core.rules.schema import Rule, RuleScope


class RulesEngine:
    """Load and manage rule sets."""

    def __init__(self, workspace_path: Path | None) -> None:
        self.workspace_path = workspace_path
        self._rules: dict[str, Rule] = {}

    def load_rules(self) -> None:
        """Load global and workspace rules."""
        rules: dict[str, Rule] = {}

        global_path = Path.home() / ".gemini" / "GEMINI.md"
        if global_path.exists():
            rules["GEMINI"] = Rule(
                name="GEMINI",
                scope=RuleScope.GLOBAL,
                path=str(global_path),
                content=global_path.read_text(encoding="utf-8"),
                enabled=True,
            )

        if self.workspace_path is not None:
            workspace_rules = self.workspace_path / ".agent" / "rules"
            if workspace_rules.exists():
                for rule_path in workspace_rules.glob("*.md"):
                    name = rule_path.stem
                    rules[name] = Rule(
                        name=name,
                        scope=RuleScope.WORKSPACE,
                        path=str(rule_path),
                        content=rule_path.read_text(encoding="utf-8"),
                        enabled=True,
                    )

        self._rules = rules

    def get_context_for_llm(self) -> str:
        """Return concatenated rule content for LLM context."""
        if not self._rules:
            self.load_rules()
        contents = [rule.content for rule in self._rules.values() if rule.enabled]
        return "\n\n".join(contents)

    def list_rules(self) -> list[dict]:
        """List loaded rules as dictionaries."""
        if not self._rules:
            self.load_rules()
        return [
            {
                "name": rule.name,
                "scope": rule.scope.value,
                "path": rule.path,
                "enabled": rule.enabled,
            }
            for rule in self._rules.values()
        ]

    def get_rule(self, name: str) -> Rule | None:
        """Fetch a rule by name."""
        if not self._rules:
            self.load_rules()
        return self._rules.get(name)
