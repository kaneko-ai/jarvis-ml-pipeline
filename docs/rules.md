# Rules Engine

The Rules Engine loads global and workspace-specific rules that guide the behavior of agents
and other tooling.

## File Locations
- **Global rules:** `~/.gemini/GEMINI.md`
- **Workspace rules:** `<workspace>/.agent/rules/*.md`

## Scope and Precedence
Workspace rules override global rules when names collide. Use clear file names to define
distinct rule sets.

## LLM Context
The engine concatenates enabled rules into a single string that can be injected into LLM
prompts or system messages.
