import sys
import time
sys.path.insert(0, ".")

from jarvis_core.mcp.hub import MCPHub

hub = MCPHub()
hub.register_builtin_servers()

tests = [
    ("openalex_search", {"query": "spermidine autophagy", "max_results": 3}),
    ("s2_search", {"query": "PD-1 immunotherapy", "limit": 3}),
]

passed = 0
for tool_name, params in tests:
    print(f"\n{'='*50}")
    print(f"Testing: {tool_name}")
    result = hub.invoke_tool_sync(tool_name, params)
    if result.success:
        count = result.data.get("count", 0)
        print(f"  OK: {count} results in {result.latency_ms:.0f}ms")
        if result.data.get("results"):
            for r in result.data["results"][:2]:
                print(f"    - {r.get('title', '?')[:70]}")
        passed += 1
    else:
        print(f"  FAIL: {result.error}")
    time.sleep(2)

print(f"\n{'='*50}")
print(f"Results: {passed}/{len(tests)} passed")
