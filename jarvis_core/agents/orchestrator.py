"""JARVIS Agentic AI System - Phase 2 Features (16-30)"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================
# 16. MULTI-AGENT ORCHESTRATOR
# ============================================
class AgentRole(Enum):
    SEARCH = "search"
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    WRITE = "write"
    REVIEW = "review"
    CODE = "code"


@dataclass
class AgentTask:
    """Task for an agent."""

    id: str
    role: AgentRole
    input_data: dict
    status: str = "pending"
    output: dict | None = None
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Agent:
    """Agent definition."""

    id: str
    role: AgentRole
    capabilities: list[str]

    def execute(self, task: AgentTask) -> dict:
        """Execute a task (to be overridden)."""
        return {"status": "completed", "result": f"Executed {task.id}"}


class MultiAgentOrchestrator:
    """Orchestrate multiple AI agents."""

    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, AgentTask] = {}
        self.execution_history: list[dict] = []

    def register_agent(self, agent: Agent):
        """Register an agent."""
        self.agents[agent.id] = agent

    def create_task(self, role: AgentRole, input_data: dict, dependencies: list[str] = None) -> str:
        """Create a new task."""
        task_id = f"task_{len(self.tasks)}_{role.value}"
        task = AgentTask(
            id=task_id, role=role, input_data=input_data, dependencies=dependencies or []
        )
        self.tasks[task_id] = task
        return task_id

    def execute_task(self, task_id: str) -> dict:
        """Execute a single task."""
        if task_id not in self.tasks:
            return {"error": "Task not found"}

        task = self.tasks[task_id]

        # Check dependencies
        for dep_id in task.dependencies:
            if dep_id in self.tasks and self.tasks[dep_id].status != "completed":
                return {"error": f"Dependency {dep_id} not completed"}

        # Find suitable agent
        suitable_agents = [a for a in self.agents.values() if a.role == task.role]
        if not suitable_agents:
            return {"error": f"No agent for role {task.role}"}

        agent = suitable_agents[0]
        result = agent.execute(task)

        task.status = "completed"
        task.output = result

        self.execution_history.append(
            {
                "task_id": task_id,
                "agent_id": agent.id,
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }
        )

        return result

    def execute_pipeline(self, task_ids: list[str]) -> list[dict]:
        """Execute multiple tasks in dependency order."""
        results = []
        for task_id in task_ids:
            result = self.execute_task(task_id)
            results.append({"task_id": task_id, "result": result})
        return results

    def decompose_task(self, complex_task: str) -> list[AgentTask]:
        """Decompose complex task into subtasks."""
        subtasks = []

        # Simple rule-based decomposition
        if "literature review" in complex_task.lower():
            subtasks.append(self.create_task(AgentRole.SEARCH, {"query": complex_task}))
            subtasks.append(self.create_task(AgentRole.ANALYZE, {"type": "papers"}))
            subtasks.append(self.create_task(AgentRole.SUMMARIZE, {"format": "review"}))
        elif "write paper" in complex_task.lower():
            subtasks.append(self.create_task(AgentRole.SEARCH, {"query": complex_task}))
            subtasks.append(self.create_task(AgentRole.ANALYZE, {"type": "synthesis"}))
            subtasks.append(self.create_task(AgentRole.WRITE, {"format": "paper"}))
            subtasks.append(self.create_task(AgentRole.REVIEW, {"type": "self"}))
        else:
            subtasks.append(self.create_task(AgentRole.SEARCH, {"query": complex_task}))
            subtasks.append(self.create_task(AgentRole.SUMMARIZE, {"format": "brief"}))

        return subtasks


# ============================================
# 17-30: SPECIALIZED AGENTS
# ============================================


class SearchAgent(Agent):
    """Agent for paper search."""

    def __init__(self):
        super().__init__("search_agent", AgentRole.SEARCH, ["pubmed", "arxiv", "semantic_scholar"])

    def execute(self, task: AgentTask) -> dict:
        query = task.input_data.get("query", "")
        return {
            "status": "completed",
            "papers_found": 10,
            "query": query,
            "sources": self.capabilities,
        }


class AnalysisAgent(Agent):
    """Agent for paper analysis."""

    def __init__(self):
        super().__init__(
            "analysis_agent", AgentRole.ANALYZE, ["comparison", "meta_analysis", "gap_analysis"]
        )

    def execute(self, task: AgentTask) -> dict:
        return {
            "status": "completed",
            "analysis_type": task.input_data.get("type", "general"),
            "insights": ["Finding 1", "Finding 2", "Finding 3"],
        }


class SummarizeAgent(Agent):
    """Agent for summarization."""

    def __init__(self):
        super().__init__(
            "summarize_agent", AgentRole.SUMMARIZE, ["abstract", "full_text", "multi_paper"]
        )

    def execute(self, task: AgentTask) -> dict:
        return {
            "status": "completed",
            "format": task.input_data.get("format", "brief"),
            "summary": "This is a generated summary of the research findings...",
        }


class WritingAgent(Agent):
    """Agent for writing assistance."""

    SECTION_TEMPLATES = {
        "introduction": "This paper presents...",
        "methods": "We conducted...",
        "results": "Our analysis revealed...",
        "discussion": "These findings suggest...",
        "conclusion": "In conclusion...",
    }

    def __init__(self):
        super().__init__("writing_agent", AgentRole.WRITE, ["draft", "edit", "format"])

    def execute(self, task: AgentTask) -> dict:
        section = task.input_data.get("section", "general")
        template = self.SECTION_TEMPLATES.get(section, "Content for this section...")
        return {"status": "completed", "section": section, "draft": template}

    def generate_draft(self, section: str, context: dict) -> str:
        """Generate section draft."""
        base = self.SECTION_TEMPLATES.get(section, "")
        return f"{base}\n\nBased on: {json.dumps(context)[:100]}..."


class ReviewAgent(Agent):
    """Agent for peer review simulation."""

    REVIEW_CRITERIA = ["novelty", "methodology", "clarity", "significance", "reproducibility"]

    def __init__(self):
        super().__init__("review_agent", AgentRole.REVIEW, ["self_review", "peer_review"])

    def execute(self, task: AgentTask) -> dict:
        return {
            "status": "completed",
            "review_type": task.input_data.get("type", "general"),
            "scores": dict.fromkeys(self.REVIEW_CRITERIA, 7),
            "comments": [
                "Consider expanding the methodology section",
                "Add more recent references",
            ],
        }

    def simulate_review(self, paper: dict) -> dict:
        """Simulate peer review."""
        comments = []

        # Check abstract length
        abstract = paper.get("abstract", "")
        if len(abstract) < 150:
            comments.append("Abstract may be too short. Consider expanding.")

        # Check for missing sections
        for section in ["methods", "results", "discussion"]:
            if section not in str(paper).lower():
                comments.append(f"Consider adding a {section} section.")

        return {
            "recommendation": "minor_revision" if len(comments) < 3 else "major_revision",
            "comments": comments,
            "scores": {c: 6 + (hash(c) % 4) for c in self.REVIEW_CRITERIA},
        }


class CodeAgent(Agent):
    """Agent for code generation."""

    TEMPLATES = {
        "python_analysis": """
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('{filename}')

# Analysis
{analysis_code}

# Visualization
plt.figure(figsize=(10, 6))
{plot_code}
plt.savefig('output.png')
""",
        "r_analysis": """
library(ggplot2)
data <- read.csv("{filename}")

# Analysis
{analysis_code}

# Plot
ggplot(data, aes(x=x, y=y)) + geom_point()
ggsave("output.png")
""",
    }

    def __init__(self):
        super().__init__("code_agent", AgentRole.CODE, ["python", "r", "jupyter"])

    def execute(self, task: AgentTask) -> dict:
        lang = task.input_data.get("language", "python")
        template = self.TEMPLATES.get(f"{lang}_analysis", "# Code here")
        return {
            "status": "completed",
            "language": lang,
            "code": template.format(
                filename="data.csv",
                analysis_code="result = df.describe()",
                plot_code="plt.plot(df['x'], df['y'])",
            ),
        }


class ExperimentDesignAgent(Agent):
    """Agent for experiment design."""

    def __init__(self):
        super().__init__(
            "experiment_agent", AgentRole.ANALYZE, ["design", "power_analysis", "sample_size"]
        )

    def design_experiment(self, hypothesis: str, variables: dict) -> dict:
        """Design an experiment based on hypothesis."""
        return {
            "hypothesis": hypothesis,
            "study_type": "randomized_controlled_trial",
            "independent_variables": list(variables.keys()),
            "dependent_variables": ["outcome_1", "outcome_2"],
            "sample_size_estimate": self._power_analysis(variables),
            "control_conditions": ["placebo", "standard_care"],
            "statistical_tests": ["t_test", "anova", "regression"],
        }

    def _power_analysis(self, variables: dict) -> int:
        """Simple power analysis for sample size."""
        effect_size = variables.get("expected_effect_size", 0.5)
        power = variables.get("power", 0.8)
        alpha = variables.get("alpha", 0.05)

        # Simplified formula
        n = int(16 / (effect_size**2))  # Approximation
        return max(n, 30)


class GrantProposalAgent(Agent):
    """Agent for grant proposal writing."""

    SECTIONS = ["specific_aims", "significance", "innovation", "approach", "timeline", "budget"]

    def __init__(self):
        super().__init__("grant_agent", AgentRole.WRITE, ["nih", "nsf", "private"])

    def generate_proposal(self, project: dict) -> dict:
        """Generate grant proposal structure."""
        return {
            "title": project.get("title", "Research Project"),
            "sections": {
                "specific_aims": self._generate_aims(project),
                "significance": "This research addresses a critical gap...",
                "innovation": "Our approach is innovative because...",
                "approach": self._generate_approach(project),
                "timeline": self._generate_timeline(project),
                "budget": self._estimate_budget(project),
            },
        }

    def _generate_aims(self, project: dict) -> str:
        return (
            f"Aim 1: {project.get('aim1', 'Primary objective')}\n"
            f"Aim 2: {project.get('aim2', 'Secondary objective')}"
        )

    def _generate_approach(self, project: dict) -> str:
        return f"We will employ {project.get('method', 'advanced techniques')}..."

    def _generate_timeline(self, project: dict) -> dict:
        years = project.get("duration_years", 3)
        return {f"Year {i+1}": f"Phase {i+1} activities" for i in range(years)}

    def _estimate_budget(self, project: dict) -> dict:
        return {
            "personnel": 150000,
            "equipment": 50000,
            "supplies": 25000,
            "travel": 10000,
            "indirect": 75000,
            "total": 310000,
        }


class ProjectMemorySystem:
    """Long-term memory for research projects."""

    def __init__(self):
        self.memories: dict[str, list[dict]] = {}
        self.context_window: list[dict] = []
        self.max_context = 50

    def store(self, project_id: str, memory: dict):
        """Store a memory."""
        if project_id not in self.memories:
            self.memories[project_id] = []

        memory["timestamp"] = datetime.now().isoformat()
        self.memories[project_id].append(memory)
        self.context_window.append(memory)

        # Trim context window
        if len(self.context_window) > self.max_context:
            self.context_window = self.context_window[-self.max_context :]

    def retrieve(self, project_id: str, query: str = None, n: int = 10) -> list[dict]:
        """Retrieve memories."""
        if project_id not in self.memories:
            return []

        memories = self.memories[project_id]

        if query:
            # Simple keyword matching
            query_words = set(query.lower().split())
            scored = []
            for m in memories:
                text = str(m).lower()
                score = sum(1 for w in query_words if w in text)
                scored.append((m, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [m for m, _ in scored[:n]]

        return memories[-n:]

    def get_context(self) -> list[dict]:
        """Get current context window."""
        return self.context_window


class SelfImprovingAgent:
    """Agent that learns from feedback."""

    def __init__(self):
        self.feedback_history: list[dict] = []
        self.performance_metrics: dict[str, list[float]] = {}
        self.learned_patterns: dict[str, Any] = {}

    def record_feedback(self, action: str, feedback: dict):
        """Record user feedback."""
        self.feedback_history.append(
            {"action": action, "feedback": feedback, "timestamp": datetime.now().isoformat()}
        )

        # Update performance metrics
        score = feedback.get("score", 0.5)
        if action not in self.performance_metrics:
            self.performance_metrics[action] = []
        self.performance_metrics[action].append(score)

    def get_improvement_suggestions(self) -> list[str]:
        """Analyze feedback and suggest improvements."""
        suggestions = []

        for action, scores in self.performance_metrics.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            if avg_score < 0.6:
                suggestions.append(f"Improve {action}: avg score {avg_score:.2f}")

        return suggestions

    def should_adjust(self, action: str) -> bool:
        """Check if action needs adjustment."""
        scores = self.performance_metrics.get(action, [])
        if len(scores) < 3:
            return False
        return sum(scores[-3:]) / 3 < 0.5


class CollaborationFinder:
    """Find potential collaborators."""

    def __init__(self):
        self.researcher_profiles: dict[str, dict] = {}

    def add_profile(self, researcher_id: str, profile: dict):
        """Add researcher profile."""
        self.researcher_profiles[researcher_id] = profile

    def find_matches(
        self, interests: list[str], location: str = None, institution_type: str = None
    ) -> list[dict]:
        """Find matching collaborators."""
        matches = []

        for rid, profile in self.researcher_profiles.items():
            score = 0

            # Interest overlap
            profile_interests = set(profile.get("interests", []))
            overlap = len(set(interests) & profile_interests)
            score += overlap * 2

            # Location match
            if location and profile.get("location") == location:
                score += 1

            # Institution type match
            if institution_type and profile.get("institution_type") == institution_type:
                score += 1

            if score > 0:
                matches.append(
                    {
                        "researcher_id": rid,
                        "name": profile.get("name", "Unknown"),
                        "match_score": score,
                        "interests": list(profile_interests),
                    }
                )

        return sorted(matches, key=lambda x: x["match_score"], reverse=True)


# ============================================
# FACTORY FUNCTIONS
# ============================================
def create_agent_pool() -> MultiAgentOrchestrator:
    """Create a pool of all agents."""
    orchestrator = MultiAgentOrchestrator()

    orchestrator.register_agent(SearchAgent())
    orchestrator.register_agent(AnalysisAgent())
    orchestrator.register_agent(SummarizeAgent())
    orchestrator.register_agent(WritingAgent())
    orchestrator.register_agent(ReviewAgent())
    orchestrator.register_agent(CodeAgent())

    return orchestrator


def get_memory_system() -> ProjectMemorySystem:
    return ProjectMemorySystem()


def get_collaboration_finder() -> CollaborationFinder:
    return CollaborationFinder()


if __name__ == "__main__":
    print("=== Multi-Agent Orchestrator Demo ===")
    orchestrator = create_agent_pool()

    # Create and execute tasks
    task1 = orchestrator.create_task(AgentRole.SEARCH, {"query": "COVID treatment"})
    task2 = orchestrator.create_task(AgentRole.SUMMARIZE, {"format": "brief"}, [task1])

    results = orchestrator.execute_pipeline([task1, task2])
    print(f"Executed {len(results)} tasks")

    print("\n=== Writing Agent Demo ===")
    writer = WritingAgent()
    draft = writer.generate_draft("introduction", {"topic": "AI in medicine"})
    print(f"Draft: {draft[:100]}...")

    print("\n=== Review Agent Demo ===")
    reviewer = ReviewAgent()
    review = reviewer.simulate_review({"abstract": "Short abstract."})
    print(f"Recommendation: {review['recommendation']}")
