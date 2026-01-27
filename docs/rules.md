# Rules Engine

The Rules Engine loads global and workspace rule files and composes them into LLM context.

## Global Rules
Global rules live at `~/.gemini/GEMINI.md`. They define baseline expectations for code style,
documentation, and testing across projects.

## Workspace Rules
Workspace rules live inside `<workspace>/.agent/rules/*.md`. These files allow a specific
repository to override or extend the global rules.

## Rule Loading Behavior
- Rules are discovered at startup by the Rules Engine.
- Workspace rules override global rules when the rule name matches.
- All enabled rules are concatenated into a single context string for the LLM.

## Template Files
- `templates/GEMINI.md` provides the default global rules template.
- `templates/workspace_rules/` contains sample workspace rule files.
