# Agent Registry & Router Guide

This guide explains how to configure and use the AgentRegistry and Router components that power Jarvis Core task routing. It complements `docs/jarvis_vision.md` and focuses on practical setup.

## Configuration format (YAML)
Agent definitions live in a YAML file such as `configs/agents.yaml` (or `configs/agents.example.yaml` as a starter). The file has two top-level keys:

- `agents`: map of agent name → definition
  - `category`: logical TaskCategory the agent serves (e.g., `paper_survey`, `thesis`, `job_hunting`, `generic`).
  - `entrypoint`: Python import path in `module:ClassName` form.
  - `description`: human-friendly text for documentation.
  - `capabilities`: list of strings describing what the agent can do.
- `categories`: map of category → config
  - `default_agent`: fallback agent name for the category.
  - `agents`: ordered list of available agent names for that category.

Example (see `configs/agents.example.yaml` for a complete, commented file):
```yaml
agents:
  paper_fetcher:
    category: paper_survey
    entrypoint: "jarvis_core.agents:PaperFetcherAgent"
    description: "Fetches and triages papers (stub)"
    capabilities: ["search_pubmed", "download_pdf"]
  mygpt_paper_analyzer:
    category: paper_survey
    entrypoint: "jarvis_core.agents:MyGPTPaperAnalyzerAgent"
    description: "Analyzes PDFs (stub)"
    capabilities: ["summarize", "rank_relevance"]
  job_assistant:
    category: job_hunting
    entrypoint: "jarvis_core.agents:JobAssistantAgent"
    description: "Job-hunting helper (stub)"
    capabilities: ["draft_es", "interview_prep"]
  misc:
    category: generic
    entrypoint: "jarvis_core.agents:MiscAgent"
    description: "Generic fallback agent"
    capabilities: ["generic_answer"]

categories:
  paper_survey:
    default_agent: paper_fetcher
    agents: [paper_fetcher, mygpt_paper_analyzer]
  job_hunting:
    default_agent: job_assistant
    agents: [job_assistant]
  generic:
    default_agent: misc
    agents: [misc]
```

## Loading the registry
```python
from pathlib import Path
from jarvis_core.registry import AgentRegistry

config_path = Path("configs/agents.yaml")
registry = AgentRegistry.from_file(config_path)
```
`AgentRegistry.from_file` accepts an optional `overrides` dict to merge on top of the base YAML. This makes it easy to swap entrypoints or change defaults in different environments without editing the file directly.

## How routing works
- **String input**: `Router.run("goal text")` uses simple keyword heuristics to detect a category, then picks the category default agent (or `misc` as fallback) and calls `agent.run_single(...)`.
- **Task input**: `Router.run(task: Task)` respects `task.category` and checks `task.inputs.get("agent_hint")` first. If an `agent_hint` is present and known, it is used. Otherwise the category default agent is selected.
- Task context (`goal`, optional `inputs.query`/`inputs.context`) is rendered into text and passed to the agent.

## Swapping in real tools
The registry decouples configuration from code. To replace a stub with a real implementation:
1. Implement the agent class with a `run_single(self, llm, task: str) -> AgentResult` method (see `jarvis_core.agents.BaseAgent`).
2. Update the relevant `entrypoint` in your config file to point to the new class (e.g., `"my_pkg.real_agents:PaperFetcherAgent"`).
3. (Optional) Add capabilities or adjust defaults in `categories` to favor the new tool.

## Minimal end-to-end usage
```python
from jarvis_core.registry import AgentRegistry
from jarvis_core.router import Router
from jarvis_core.task import Task, TaskCategory

class DummyLLM:
    def chat(self, messages):
        return "dummy response"

registry = AgentRegistry.from_file("configs/agents.yaml")
router = Router(llm=DummyLLM(), registry=registry)

task = Task(
    id="demo-1",
    category=TaskCategory.PAPER_SURVEY,
    goal="Find papers about CRISPR quality control",
    inputs={"query": "CRISPR quality control"},
)
result = router.run(task)
print(result.answer)
```

This sample uses stub agents that do not call external services, so it runs without API keys. For LLM-backed agents, supply a real `LLMClient` (requires `GEMINI_API_KEY` or `GOOGLE_API_KEY`).
