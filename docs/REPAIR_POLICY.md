# RepairPolicy Documentation

Per RP-183, this documents the RepairPolicy configuration contract.

## Overview

RepairPolicy defines the behavior of the automatic repair loop. It controls:
- Maximum retry attempts
- Time and resource limits
- Allowed repair actions
- Stop conditions

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | int | 3 | Maximum repair attempts (must be ≥1) |
| `max_wall_time_sec` | float | 300.0 | Maximum wall clock time in seconds (must be >0) |
| `max_tool_calls` | int | 50 | Maximum tool calls across all attempts (must be ≥1) |
| `allowed_actions` | list[str] | [see below] | List of allowed action IDs |
| `stop_on` | dict | {} | Stop conditions |
| `budget_overrides` | dict|None | None | Optional budget overrides |

## Default Allowed Actions

```python
[
    "SWITCH_FETCH_ADAPTER",
    "INCREASE_TOP_K",
    "TIGHTEN_MMR",
    "CITATION_FIRST_PROMPT",
    "BUDGET_REBALANCE",
    "MODEL_ROUTER_SAFE_SWITCH",
]
```

## Stop Conditions

| Key | Default | Description |
|-----|---------|-------------|
| `consecutive_no_improvement` | 2 | Stop after N attempts with no improvement |
| `same_failure_repeated` | 3 | Stop after same failure N times |

## Safe Limits (Recommended)

> [!IMPORTANT]
> These limits prevent runaway execution:

- `max_attempts`: 3-5 (never >10)
- `max_wall_time_sec`: 300-600 (never >1800)
- `max_tool_calls`: 50-100 (never >200)

## Usage Example

```python
from jarvis_core.runtime.repair_policy import RepairPolicy

# Strict policy
policy = RepairPolicy(
    max_attempts=3,
    max_wall_time_sec=180.0,
    allowed_actions=["INCREASE_TOP_K", "TIGHTEN_MMR"],
)

# Serialize
json_str = policy.to_json()

# Deserialize
restored = RepairPolicy.from_json(json_str)
```

## CLI Usage

```bash
jarvis run --repair --max-attempts 3 --max-wall-time 300
```
