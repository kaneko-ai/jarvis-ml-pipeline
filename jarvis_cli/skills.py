"""jarvis skills - Skill discovery, matching, and execution (C-3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def run_skills(args) -> int:
    """CLI entry point for the skills command."""
    from jarvis_core.skills.engine import SkillsEngine

    action = args.action
    engine = SkillsEngine(workspace_path=Path.cwd())

    if action == "list":
        skills = engine.list_all_skills()
        if not skills:
            print("No skills found.")
            return 0
        print(f"\n  JARVIS Skills ({len(skills)} registered)")
        print(f"  {'='*56}")
        for s in skills:
            triggers = ", ".join(s.get("triggers", []))
            deps = ", ".join(s.get("dependencies", []))
            print(f"\n  [{s['name']}]")
            print(f"    Description : {s.get('description', '(none)')}")
            print(f"    Scope       : {s.get('scope', '?')}")
            print(f"    Triggers    : {triggers or '(none)'}")
            if deps:
                print(f"    Dependencies: {deps}")
        print()
        return 0

    elif action == "match":
        query = getattr(args, "query", None)
        if not query:
            print("Error: --query is required for 'match' action.", file=sys.stderr)
            return 1
        matches = engine.match_skills(query)
        if not matches:
            print(f"  No skills matched for: \"{query}\"")
            return 0
        print(f"\n  Skills matching \"{query}\":")
        for name in matches:
            skill = engine.get_skill(name)
            desc = skill.metadata.description if skill else ""
            print(f"    - {name}: {desc}")
        print()
        return 0

    elif action == "show":
        name = getattr(args, "name", None)
        if not name:
            print("Error: --name is required for 'show' action.", file=sys.stderr)
            return 1
        skill = engine.get_skill(name)
        if not skill:
            print(f"  Skill not found: {name}")
            return 1
        print(f"\n  Skill: {skill.metadata.name}")
        print(f"  Description: {skill.metadata.description}")
        print(f"  Scope: {skill.scope.value}")
        print(f"  Path: {skill.path}")
        print(f"  Triggers: {', '.join(skill.metadata.triggers)}")
        print(f"  Dependencies: {', '.join(skill.metadata.dependencies)}")
        if skill.instructions:
            print(f"\n  --- Instructions ---")
            print(skill.instructions)
        if skill.resources:
            print(f"\n  --- Resources ({len(skill.resources)}) ---")
            for rname in skill.resources:
                print(f"    - {rname}")
        print()
        return 0

    elif action == "context":
        query = getattr(args, "query", None)
        if not query:
            print("Error: --query is required for 'context' action.", file=sys.stderr)
            return 1
        matches = engine.match_skills(query)
        if not matches:
            print(f"  No skills matched for: \"{query}\"")
            return 0
        context = engine.get_context_for_llm(matches)
        print(context)
        return 0

    elif action == "execute":
        name = getattr(args, "name", None)
        if not name:
            print("Error: --name is required for 'execute' action.", file=sys.stderr)
            return 1
        result = engine.execute_skill(name, context={"execute": True})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("success") else 1

    else:
        print(f"Unknown action: {action}. Use: list, match, show, context, execute")
        return 1
