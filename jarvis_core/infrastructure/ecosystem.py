"""JARVIS Infrastructure & Ecosystem - Phase 6-7 Features (76-100)"""

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


# ============================================
# 76. EDGE ML INFERENCE
# ============================================
class EdgeMLInference:
    """Browser-based ML inference."""

    def __init__(self):
        self.models: dict[str, dict] = {}
        self.cache: dict[str, Any] = {}

    def register_model(self, name: str, model_config: dict):
        """Register a model for edge inference."""
        self.models[name] = {
            "config": model_config,
            "loaded": False,
            "size_mb": model_config.get("size_mb", 10),
        }

    def infer(self, model_name: str, input_data: dict) -> dict:
        """Run inference (placeholder for actual ONNX/TF.js)."""
        if model_name not in self.models:
            return {"error": "Model not found"}

        # Generate cache key
        cache_key = hashlib.md5(
            f"{model_name}_{json.dumps(input_data)}".encode(), usedforsecurity=False
        ).hexdigest()

        if cache_key in self.cache:
            return {"result": self.cache[cache_key], "cached": True}

        # Placeholder inference
        result = {"prediction": 0.85, "confidence": 0.92, "model": model_name}
        self.cache[cache_key] = result

        return {"result": result, "cached": False}

    def get_model_status(self) -> dict:
        """Get status of all models."""
        return {
            name: {"loaded": m["loaded"], "size_mb": m["size_mb"]}
            for name, m in self.models.items()
        }


# ============================================
# 77. DISTRIBUTED PROCESSING
# ============================================
@dataclass
class ProcessingJob:
    """Distributed processing job."""

    id: str
    task_type: str
    input_data: dict
    status: str = "queued"
    progress: int = 0
    result: dict | None = None
    worker_id: str | None = None


class DistributedProcessor:
    """Manage distributed processing jobs."""

    def __init__(self):
        self.jobs: dict[str, ProcessingJob] = {}
        self.workers: dict[str, dict] = {}

    def register_worker(self, worker_id: str, capabilities: list[str]):
        """Register a worker node."""
        self.workers[worker_id] = {
            "capabilities": capabilities,
            "status": "idle",
            "jobs_completed": 0,
        }

    def submit_job(self, task_type: str, input_data: dict) -> str:
        """Submit a processing job."""
        job_id = f"job_{len(self.jobs)}_{int(time.time())}"
        job = ProcessingJob(id=job_id, task_type=task_type, input_data=input_data)
        self.jobs[job_id] = job

        # Assign to available worker
        for worker_id, worker in self.workers.items():
            if worker["status"] == "idle" and task_type in worker["capabilities"]:
                job.worker_id = worker_id
                job.status = "assigned"
                worker["status"] = "busy"
                break

        return job_id

    def get_job_status(self, job_id: str) -> dict | None:
        """Get job status."""
        if job_id not in self.jobs:
            return None

        job = self.jobs[job_id]
        return {
            "id": job.id,
            "status": job.status,
            "progress": job.progress,
            "worker": job.worker_id,
        }

    def complete_job(self, job_id: str, result: dict):
        """Mark job as complete."""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = "completed"
            job.progress = 100
            job.result = result

            if job.worker_id and job.worker_id in self.workers:
                self.workers[job.worker_id]["status"] = "idle"
                self.workers[job.worker_id]["jobs_completed"] += 1


# ============================================
# 78. INTELLIGENT CACHING
# ============================================
class IntelligentCache:
    """Predictive caching system."""

    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, dict] = {}
        self._access_patterns: dict[str, list[str]] = defaultdict(list)
        self._max_size = max_size

    def get(self, key: str, user_id: str = None) -> Any | None:
        """Get cached value."""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.fromisoformat(entry["expires"]) > datetime.now():
                entry["hits"] += 1
                if user_id:
                    self._access_patterns[user_id].append(key)
                return entry["value"]
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_minutes: int = 60):
        """Set cached value."""
        if len(self._cache) >= self._max_size:
            # Evict least accessed
            min_hits = min(e["hits"] for e in self._cache.values())
            for k, v in list(self._cache.items()):
                if v["hits"] == min_hits:
                    del self._cache[k]
                    break

        self._cache[key] = {
            "value": value,
            "expires": (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat(),
            "hits": 0,
            "created": datetime.now().isoformat(),
        }

    def predict_prefetch(self, user_id: str) -> list[str]:
        """Predict what to prefetch based on access patterns."""
        history = self._access_patterns.get(user_id, [])[-10:]
        if not history:
            return []

        # Simple frequency-based prediction
        freq = defaultdict(int)
        for key in history:
            freq[key] += 1

        return [k for k, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]]


# ============================================
# 79. API RATE OPTIMIZER
# ============================================
class APIRateOptimizer:
    """Optimize API usage across providers."""

    def __init__(self):
        self.providers: dict[str, dict] = {}
        self.usage: dict[str, list[datetime]] = defaultdict(list)

    def register_provider(self, name: str, rate_limit: int, window_seconds: int = 60):
        """Register API provider."""
        self.providers[name] = {
            "rate_limit": rate_limit,
            "window_seconds": window_seconds,
            "cost_per_call": 0.001,
        }

    def can_call(self, provider: str) -> bool:
        """Check if we can make an API call."""
        if provider not in self.providers:
            return True

        config = self.providers[provider]
        window_start = datetime.now() - timedelta(seconds=config["window_seconds"])
        recent_calls = [t for t in self.usage[provider] if t > window_start]

        return len(recent_calls) < config["rate_limit"]

    def record_call(self, provider: str):
        """Record an API call."""
        self.usage[provider].append(datetime.now())

        # Clean old entries
        window_start = datetime.now() - timedelta(seconds=3600)
        self.usage[provider] = [t for t in self.usage[provider] if t > window_start]

    def get_best_provider(self, capability: str, providers: list[str]) -> str | None:
        """Get best available provider for capability."""
        available = [p for p in providers if self.can_call(p)]
        if not available:
            return None

        # Return one with lowest cost
        return min(available, key=lambda p: self.providers.get(p, {}).get("cost_per_call", 0))


# ============================================
# 80. REAL-TIME SYNC ENGINE
# ============================================
class RealTimeSyncEngine:
    """Multi-device synchronization."""

    def __init__(self):
        self.devices: dict[str, dict] = {}
        self.pending_changes: dict[str, list[dict]] = defaultdict(list)
        self.version: int = 0

    def register_device(self, device_id: str, user_id: str):
        """Register a device."""
        self.devices[device_id] = {
            "user_id": user_id,
            "last_sync": datetime.now().isoformat(),
            "version": self.version,
        }

    def push_change(self, device_id: str, change: dict):
        """Push a change from device."""
        self.version += 1
        change["version"] = self.version
        change["device_id"] = device_id
        change["timestamp"] = datetime.now().isoformat()

        # Queue for other devices
        user_id = self.devices.get(device_id, {}).get("user_id")
        for did, device in self.devices.items():
            if did != device_id and device["user_id"] == user_id:
                self.pending_changes[did].append(change)

    def pull_changes(self, device_id: str) -> list[dict]:
        """Pull pending changes for device."""
        changes = self.pending_changes.get(device_id, [])
        self.pending_changes[device_id] = []

        if device_id in self.devices:
            self.devices[device_id]["last_sync"] = datetime.now().isoformat()
            self.devices[device_id]["version"] = self.version

        return changes

    def resolve_conflict(self, changes: list[dict]) -> dict:
        """Resolve conflicting changes (last-write-wins)."""
        if not changes:
            return {}
        return max(changes, key=lambda c: c.get("timestamp", ""))


# ============================================
# 81-85: Infrastructure Features
# ============================================


class ObservabilityDashboard:
    """System observability."""

    def __init__(self):
        self.metrics: dict[str, list[dict]] = defaultdict(list)
        self.errors: list[dict] = []

    def record_metric(self, name: str, value: float, tags: dict = None):
        """Record a metric."""
        self.metrics[name].append(
            {"value": value, "timestamp": datetime.now().isoformat(), "tags": tags or {}}
        )

    def record_error(self, error: str, context: dict = None):
        """Record an error."""
        self.errors.append(
            {"error": error, "context": context or {}, "timestamp": datetime.now().isoformat()}
        )

    def get_summary(self) -> dict:
        """Get observability summary."""
        summary = {"metrics": {}, "error_count": len(self.errors)}

        for name, values in self.metrics.items():
            if values:
                recent = values[-100:]
                summary["metrics"][name] = {
                    "count": len(recent),
                    "avg": sum(v["value"] for v in recent) / len(recent),
                    "max": max(v["value"] for v in recent),
                    "min": min(v["value"] for v in recent),
                }

        return summary


class ABTestingFramework:
    """A/B testing for features."""

    def __init__(self):
        self.experiments: dict[str, dict] = {}
        self.assignments: dict[str, dict[str, str]] = {}  # user_id -> {exp_id: variant}

    def create_experiment(self, exp_id: str, variants: list[str], weights: list[float] = None):
        """Create an experiment."""
        self.experiments[exp_id] = {
            "variants": variants,
            "weights": weights or [1.0 / len(variants)] * len(variants),
            "created": datetime.now().isoformat(),
            "results": {v: {"count": 0, "conversions": 0} for v in variants},
        }

    def get_variant(self, exp_id: str, user_id: str) -> str:
        """Get variant for user."""
        if user_id not in self.assignments:
            self.assignments[user_id] = {}

        if exp_id in self.assignments[user_id]:
            return self.assignments[user_id][exp_id]

        if exp_id not in self.experiments:
            return "control"

        # Deterministic assignment based on hash
        exp = self.experiments[exp_id]
        h = hash(f"{user_id}_{exp_id}") % 100 / 100.0

        cumulative = 0
        for variant, weight in zip(exp["variants"], exp["weights"]):
            cumulative += weight
            if h < cumulative:
                self.assignments[user_id][exp_id] = variant
                exp["results"][variant]["count"] += 1
                return variant

        return exp["variants"][-1]

    def record_conversion(self, exp_id: str, user_id: str):
        """Record a conversion."""
        if exp_id in self.experiments and user_id in self.assignments:
            variant = self.assignments[user_id].get(exp_id)
            if variant:
                self.experiments[exp_id]["results"][variant]["conversions"] += 1


class AutoScaler:
    """Auto-scaling infrastructure."""

    def __init__(self, min_instances: int = 1, max_instances: int = 10):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.current_instances = min_instances
        self.metrics_history: list[dict] = []

    def record_metrics(self, cpu_usage: float, memory_usage: float, request_count: int):
        """Record current metrics."""
        self.metrics_history.append(
            {
                "cpu": cpu_usage,
                "memory": memory_usage,
                "requests": request_count,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep last 100 entries
        self.metrics_history = self.metrics_history[-100:]

    def calculate_desired_instances(self) -> int:
        """Calculate desired instance count."""
        if not self.metrics_history:
            return self.current_instances

        recent = self.metrics_history[-10:]
        avg_cpu = sum(m["cpu"] for m in recent) / len(recent)

        # Scale based on CPU
        if avg_cpu > 80:
            return min(self.current_instances + 2, self.max_instances)
        elif avg_cpu > 60:
            return min(self.current_instances + 1, self.max_instances)
        elif avg_cpu < 20 and self.current_instances > self.min_instances:
            return max(self.current_instances - 1, self.min_instances)

        return self.current_instances

    def scale(self) -> dict:
        """Perform scaling."""
        desired = self.calculate_desired_instances()
        action = (
            "scale_up"
            if desired > self.current_instances
            else "scale_down" if desired < self.current_instances else "no_change"
        )

        old = self.current_instances
        self.current_instances = desired

        return {"action": action, "from": old, "to": desired}


class SecurityHardening:
    """Security features."""

    def __init__(self):
        self.rate_limits: dict[str, int] = {}
        self.blocked_ips: set = set()
        self.audit_log: list[dict] = []

    def check_rate_limit(self, ip: str, limit: int = 100) -> bool:
        """Check if IP is within rate limit."""
        if ip in self.blocked_ips:
            return False

        key = f"{ip}_{datetime.now().strftime('%Y%m%d%H%M')}"
        self.rate_limits[key] = self.rate_limits.get(key, 0) + 1

        return self.rate_limits[key] <= limit

    def block_ip(self, ip: str, reason: str):
        """Block an IP address."""
        self.blocked_ips.add(ip)
        self.audit_log.append(
            {
                "action": "block_ip",
                "ip": ip,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def validate_input(self, data: str) -> dict:
        """Validate input for security issues."""
        issues = []

        dangerous_patterns = ["<script>", "DROP TABLE", "'; --", "eval(", "exec("]
        for pattern in dangerous_patterns:
            if pattern.lower() in data.lower():
                issues.append(f"Potential injection: {pattern}")

        return {"safe": len(issues) == 0, "issues": issues}


# ============================================
# 86-100: ECOSYSTEM INTEGRATIONS
# ============================================


class VSCodeExtensionAPI:
    """VS Code extension integration."""

    def search_papers(self, query: str) -> dict:
        """Search papers from VS Code."""
        return {"command": "jarvis.search", "query": query, "results_format": "quickpick"}

    def insert_citation(self, paper: dict, format: str = "bibtex") -> str:
        """Generate citation for insertion."""
        if format == "bibtex":
            return f"@article{{{paper.get('pmid', 'unknown')},title={{{paper.get('title', '')}}}}}"
        return f"[{paper.get('title', 'Unknown')}]"

    def get_commands(self) -> list[dict]:
        """Get available commands."""
        return [
            {"command": "jarvis.search", "title": "JARVIS: Search Papers"},
            {"command": "jarvis.cite", "title": "JARVIS: Insert Citation"},
            {"command": "jarvis.summarize", "title": "JARVIS: Summarize Selection"},
            {"command": "jarvis.related", "title": "JARVIS: Find Related Work"},
        ]


class JupyterIntegration:
    """Jupyter notebook integration."""

    def search_magic(self, line: str) -> str:
        """Handle %jarvis magic command."""
        parts = line.split(maxsplit=1)
        command = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        if command == "search":
            return f"# Searching for: {args}\nimport jarvis; jarvis.search('{args}')"
        elif command == "cite":
            return f"# Citation for: {args}\n# [Insert citation here]"

        return "# Unknown JARVIS command"

    def to_markdown_cell(self, paper: dict) -> str:
        """Convert paper to markdown cell."""
        return f"""## {paper.get('title', 'Unknown')}

**Authors:** {paper.get('authors', 'Unknown')}  
**Journal:** {paper.get('journal', 'Unknown')} ({paper.get('year', 'Unknown')})  
**PMID:** {paper.get('pmid', 'Unknown')}

### Abstract
{paper.get('abstract', 'No abstract available.')}
"""


class BrowserExtensionAPI:
    """Browser extension API."""

    def save_page(self, url: str, title: str, content: str) -> dict:
        """Save page to JARVIS."""
        return {
            "action": "save",
            "url": url,
            "title": title,
            "content_length": len(content),
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_page(self, content: str) -> dict:
        """Analyze page content."""
        # Extract potential paper info
        has_doi = "doi" in content.lower()
        has_pmid = "pmid" in content.lower()

        return {
            "is_paper": has_doi or has_pmid,
            "has_doi": has_doi,
            "has_pmid": has_pmid,
            "word_count": len(content.split()),
        }

    def get_context_menu_items(self) -> list[dict]:
        """Get context menu items."""
        return [
            {"id": "save-to-jarvis", "title": "Save to JARVIS"},
            {"id": "search-jarvis", "title": "Search JARVIS for '%s'"},
            {"id": "cite-this", "title": "Generate Citation"},
        ]


class ReadwiseIntegration:
    """Readwise integration for highlights."""

    def __init__(self):
        self.highlights: list[dict] = []

    def sync_highlights(self, readwise_data: list[dict]) -> int:
        """Sync highlights from Readwise."""
        new_count = 0
        for highlight in readwise_data:
            if highlight not in self.highlights:
                self.highlights.append(highlight)
                new_count += 1
        return new_count

    def export_to_readwise(self, highlights: list[dict]) -> dict:
        """Export highlights to Readwise format."""
        return {
            "highlights": [
                {
                    "text": h.get("text", ""),
                    "title": h.get("paper_title", ""),
                    "source_url": h.get("url", ""),
                    "highlighted_at": h.get("timestamp", datetime.now().isoformat()),
                }
                for h in highlights
            ]
        }


class PKMIntegration:
    """Personal Knowledge Management integration (Roam/Logseq/Obsidian)."""

    def to_roam_format(self, paper: dict, notes: list[str] = None) -> str:
        """Convert to Roam Research format."""
        roam = f"- [[{paper.get('title', 'Unknown')}]]\n"
        roam += "  - #paper #research\n"
        roam += f"  - Authors:: {paper.get('authors', 'Unknown')}\n"
        roam += f"  - Year:: [[{paper.get('year', 'Unknown')}]]\n"
        roam += f"  - Journal:: [[{paper.get('journal', 'Unknown')}]]\n"
        roam += f"  - PMID:: {paper.get('pmid', '')}\n"

        if notes:
            roam += "  - Notes::\n"
            for note in notes:
                roam += f"    - {note}\n"

        return roam

    def to_logseq_format(self, paper: dict) -> str:
        """Convert to Logseq format."""
        return f"""- {paper.get('title', 'Unknown')}
  type:: paper
  authors:: {paper.get('authors', 'Unknown')}
  year:: {paper.get('year', 'Unknown')}
  journal:: {paper.get('journal', 'Unknown')}
  pmid:: {paper.get('pmid', '')}
  - ## Abstract
    - {paper.get('abstract', 'No abstract.')}
"""


class WebhookManager:
    """Webhook management for integrations."""

    def __init__(self):
        self.webhooks: dict[str, dict] = {}

    def register_webhook(self, name: str, url: str, events: list[str]):
        """Register a webhook."""
        self.webhooks[name] = {
            "url": url,
            "events": events,
            "created": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
        }

    def trigger(self, event: str, data: dict) -> list[dict]:
        """Trigger webhooks for event."""
        triggered = []

        for name, webhook in self.webhooks.items():
            if event in webhook["events"]:
                # Would make HTTP request in production
                webhook["last_triggered"] = datetime.now().isoformat()
                webhook["trigger_count"] += 1
                triggered.append(
                    {"webhook": name, "url": webhook["url"], "event": event, "status": "sent"}
                )

        return triggered

    def get_payload(self, event: str, data: dict) -> dict:
        """Format webhook payload."""
        return {"event": event, "timestamp": datetime.now().isoformat(), "data": data}


class OpenProtocol:
    """Open protocol for paper metadata exchange."""

    VERSION = "1.0.0"

    def serialize_paper(self, paper: dict) -> dict:
        """Serialize paper to standard format."""
        return {
            "protocol_version": self.VERSION,
            "type": "paper",
            "id": {
                "pmid": paper.get("pmid"),
                "doi": paper.get("doi"),
                "arxiv": paper.get("arxiv_id"),
            },
            "metadata": {
                "title": paper.get("title"),
                "authors": paper.get("authors"),
                "year": paper.get("year"),
                "journal": paper.get("journal"),
                "abstract": paper.get("abstract"),
            },
            "exported_at": datetime.now().isoformat(),
        }

    def deserialize_paper(self, data: dict) -> dict:
        """Deserialize from standard format."""
        if data.get("protocol_version") != self.VERSION:
            # Handle version migration
            pass

        ids = data.get("id", {})
        meta = data.get("metadata", {})

        return {
            "pmid": ids.get("pmid"),
            "doi": ids.get("doi"),
            "arxiv_id": ids.get("arxiv"),
            **meta,
        }


# ============================================
# FACTORY FUNCTIONS
# ============================================
def get_edge_ml() -> EdgeMLInference:
    return EdgeMLInference()


def get_distributed_processor() -> DistributedProcessor:
    return DistributedProcessor()


def get_intelligent_cache() -> IntelligentCache:
    return IntelligentCache()


def get_api_optimizer() -> APIRateOptimizer:
    return APIRateOptimizer()


def get_sync_engine() -> RealTimeSyncEngine:
    return RealTimeSyncEngine()


def get_vscode_api() -> VSCodeExtensionAPI:
    return VSCodeExtensionAPI()


def get_jupyter_integration() -> JupyterIntegration:
    return JupyterIntegration()


def get_browser_api() -> BrowserExtensionAPI:
    return BrowserExtensionAPI()


def get_webhook_manager() -> WebhookManager:
    return WebhookManager()


if __name__ == "__main__":
    print("=== Edge ML Demo ===")
    edge = EdgeMLInference()
    edge.register_model("classifier", {"size_mb": 5})
    result = edge.infer("classifier", {"text": "sample"})
    print(f"Inference result: {result}")

    print("\n=== Distributed Processor Demo ===")
    dp = DistributedProcessor()
    dp.register_worker("w1", ["search", "analyze"])
    job_id = dp.submit_job("search", {"query": "test"})
    print(f"Job submitted: {job_id}")

    print("\n=== PKM Integration Demo ===")
    pkm = PKMIntegration()
    paper = {"title": "Test Paper", "authors": "Smith J", "year": 2024}
    roam = pkm.to_roam_format(paper, ["Important finding"])
    print(f"Roam format:\n{roam[:100]}...")
