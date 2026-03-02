"""jarvis mcp - MCP Hub management and tool invocation (C-1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def run_mcp(args) -> int:
    """CLI entry point for the mcp command."""
    from jarvis_core.mcp.hub import MCPHub

    action = args.action
    hub = MCPHub()
    hub.register_builtin_servers()

    config_path = getattr(args, "config", None)
    if config_path:
        try:
            hub.register_from_config(config_path)
        except Exception as e:
            print(f"  Warning: Could not load config {config_path}: {e}")

    if action == "servers":
        servers = hub.list_servers()
        if not servers:
            print("No MCP servers registered.")
            return 0
        print(f"\n  MCP Servers ({len(servers)} registered)")
        print(f"  {'='*60}")
        for s in servers:
            print(f"\n  [{s['name']}]")
            print(f"    URL    : {s['server_url']}")
            print(f"    Type   : {s['server_type']}")
            print(f"    Status : {s['status']}")
            print(f"    Tools  : {s['tool_count']}")
        print()
        return 0

    elif action == "tools":
        tools = hub.list_all_tools()
        if not tools:
            print("No MCP tools registered.")
            return 0
        print(f"\n  MCP Tools ({len(tools)} available)")
        print(f"  {'='*60}")
        for t in tools:
            enabled = "ON" if t["enabled"] else "OFF"
            params = ", ".join(t.get("required_params", []))
            print(f"  [{t['server']}] {t['tool']}  ({enabled})")
            print(f"    {t['description']}")
            if params:
                print(f"    Required: {params}")
        print()
        return 0

    elif action == "invoke":
        tool_name = getattr(args, "tool", None)
        if not tool_name:
            print("Error: --tool is required for invoke.", file=sys.stderr)
            return 1

        # Load params: --params-file takes priority, then --params, then default
        params = {}
        params_file = getattr(args, "params_file", None)
        params_str = getattr(args, "params", None)
        if params_file:
            pf = Path(params_file)
            if not pf.exists():
                print(f"Error: Params file not found: {params_file}", file=sys.stderr)
                return 1
            try:
                params = json.loads(pf.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in {params_file}: {e}", file=sys.stderr)
                return 1
        elif params_str:
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON params: {e}", file=sys.stderr)
                return 1

        print(f"\n  Invoking: {tool_name}")
        print(f"  Params: {json.dumps(params, ensure_ascii=False)}")
        print(f"  {'='*60}")

        result = hub.invoke_tool_sync(tool_name, params)

        if result.success:
            print(f"  Status  : SUCCESS")
            print(f"  Server  : {result.server_name}")
            print(f"  Latency : {result.latency_ms:.1f} ms")
            print(f"  Data:")
            print(json.dumps(result.data, ensure_ascii=False, indent=2))
        else:
            print(f"  Status  : FAILED")
            print(f"  Server  : {result.server_name}")
            print(f"  Error   : {result.error}")

        print()
        return 0 if result.success else 1

    elif action == "status":
        servers = hub.list_servers()
        tools = hub.list_all_tools()
        print(f"\n  MCP Hub Status")
        print(f"  {'='*40}")
        print(f"  Servers : {len(servers)}")
        print(f"  Tools   : {len(tools)}")
        enabled_count = sum(1 for t in tools if t["enabled"])
        print(f"  Enabled : {enabled_count}")
        print(f"  Disabled: {len(tools) - enabled_count}")
        print()
        return 0

    else:
        print(f"Unknown action: {action}. Use: servers, tools, invoke, status")
        return 1
