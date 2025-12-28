"""Prompt Registry (P-01).

Per RP-28 and 100% Plan, provides versioned prompt management.
- YAMLテンプレート読み込み
- prompts_used.json記録
- 用途別プロンプト資産化
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PromptEntry:
    """A registered prompt."""

    prompt_id: str
    version: str
    template: str
    description: str = ""
    category: str = "general"  # search, extract, rank, summarize, verify

    @property
    def prompt_hash(self) -> str:
        """Compute hash of template."""
        return hashlib.sha256(self.template.encode()).hexdigest()[:16]
    
    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "hash": self.prompt_hash,
            "description": self.description,
            "category": self.category,
        }


@dataclass
class PromptUsage:
    """Record of prompt usage in a run."""
    prompt_id: str
    version: str
    prompt_hash: str
    timestamp: str
    input_tokens: int = 0
    output_tokens: int = 0
    
    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "hash": self.prompt_hash,
            "timestamp": self.timestamp,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


class PromptRegistry:
    """Central registry for prompts."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self._prompts: Dict[str, PromptEntry] = {}
        self._usage_log: List[PromptUsage] = []
        self._templates_dir = templates_dir
        self._register_defaults()
        if templates_dir and templates_dir.exists():
            self._load_templates(templates_dir)

    def _register_defaults(self) -> None:
        """Register default prompts for all categories."""
        
        # === Search Category ===
        self.register(PromptEntry(
            prompt_id="search_composer",
            version="1.0",
            category="search",
            template="""You are a biomedical search expert. Generate an optimized PubMed search query.

Query: {query}
Domain: {domain}

Requirements:
1. Include MeSH terms where applicable
2. Add synonyms for key concepts
3. Include year filter if relevant
4. Output both:
   - pubmed_query: The actual PubMed query string
   - reasoning: Why this query structure

Output JSON format:
{{
  "pubmed_query": "...",
  "mesh_terms": [...],
  "synonyms_used": [...],
  "filters": {{...}},
  "reasoning": "..."
}}""",
            description="Generate optimized PubMed search query with MeSH terms",
        ))

        # === Retrieve Category ===
        self.register(PromptEntry(
            prompt_id="paper_survey_retrieve",
            version="1.0",
            category="search",
            template="""You are a research assistant. Based on the query, identify key entities and concepts.

Query: {query}

Extract:
1. Main entities (genes, proteins, diseases)
2. Key relationships
3. Relevant search terms""",
            description="Paper survey retrieval prompt",
        ))

        self.register(PromptEntry(
            prompt_id="paper_selector",
            version="1.0",
            category="search",
            template="""You are a paper selection expert for immuno-oncology research.

Query: {query}
Paper candidates (title, abstract, year):
{papers}

Selection criteria:
1. Relevance to query (0-10)
2. Evidence quality (methodology, sample size)
3. Recency (prefer recent unless historical context needed)
4. Avoid review articles unless synthesis needed

For each paper, output:
- paper_id
- relevance_score (0-10)
- include (true/false)
- reason (brief)

Output as JSON array.""",
            description="Select most relevant papers for analysis",
        ))

        # === Extract Category ===
        self.register(PromptEntry(
            prompt_id="claim_extractor",
            version="1.0",
            category="extract",
            template="""You are extracting scientific claims from a paper.

Paper: {paper_title}
Text: {text}

For each claim, provide:
1. claim_text: The exact claim
2. claim_type: fact|hypothesis|result|conclusion|methodology
3. confidence: 0.0-1.0
4. evidence_required: true/false

Rules:
- Only extract verifiable claims
- Mark hypotheses clearly
- Include methodology claims if relevant

Output as JSON array of claims.""",
            description="Extract structured claims from paper text",
        ))

        self.register(PromptEntry(
            prompt_id="evidence_extractor",
            version="1.0",
            category="extract",
            template="""You are linking claims to evidence within a paper.

Claim: {claim_text}
Available text chunks:
{chunks}

For each relevant chunk:
1. Identify supporting text (exact quote)
2. Provide locator (section, paragraph)
3. Rate support strength: strong|moderate|weak

Rules:
- Quote exact text, don't paraphrase
- If no evidence found, output empty array
- Include negative evidence if contradicts

Output JSON:
{{
  "claim_id": "{claim_id}",
  "evidence": [
    {{
      "text": "...",
      "locator": {{"section": "...", "paragraph": N}},
      "strength": "strong|moderate|weak"
    }}
  ]
}}""",
            description="Link claims to supporting evidence with locators",
        ))

        # === Rank Category ===
        self.register(PromptEntry(
            prompt_id="ranker",
            version="1.0",
            category="rank",
            template="""You are ranking papers and claims by importance.

Query: {query}
Items to rank:
{items}

Ranking criteria (weighted):
- Relevance to query: {relevance_weight}
- Evidence strength: {evidence_weight}
- Recency: {recency_weight}
- Methodology quality: {methodology_weight}

For each item, provide:
- item_id
- score (0-100)
- rank
- factors: which criteria contributed

Output as JSON array sorted by rank.""",
            description="Rank papers/claims by configurable criteria",
        ))

        # === Summarize Category ===
        self.register(PromptEntry(
            prompt_id="summarizer_300",
            version="1.0",
            category="summarize",
            template="""Create a 300-character Japanese summary.

Topic: {topic}
Key claims with evidence:
{claims}

Requirements:
1. 300文字以内
2. 最重要の発見を最初に
3. 根拠の数を明示（例：「3論文の根拠」）
4. 不確実な点は「〜の可能性」で表現

Output the summary only, no explanation.""",
            description="Generate 300-char Japanese summary",
        ))

        self.register(PromptEntry(
            prompt_id="summarizer_detailed",
            version="1.0",
            category="summarize",
            template="""Create a detailed Japanese summary with structure.

Topic: {topic}
Claims with evidence:
{claims}

Required sections:
1. 背景（1-2文）
2. 新規性/主要発見（箇条書き）
3. 主要メカニズム/データ
4. 限界と未解決点
5. 次の問い

Rules:
- Each claim must cite paper_id
- Distinguish facts from interpretations
- List unknowns explicitly""",
            description="Generate detailed structured summary",
        ))

        self.register(PromptEntry(
            prompt_id="summarizer_notebooklm",
            version="1.0",
            category="summarize",
            template="""Create a NotebookLM-style conversational script.

Topic: {topic}
Claims with evidence:
{claims}

Format:
- 2人の研究者の対話形式
- Aが質問/疑問を投げかける
- Bが根拠とともに説明
- 専門用語は補足説明
- 3-5分で読める長さ

Include:
- 冒頭の導入
- 核心の解説
- 意外な発見
- 今後の研究への示唆""",
            description="Generate NotebookLM conversational script",
        ))

        # === Verify Category ===
        self.register(PromptEntry(
            prompt_id="paper_survey_generate",
            version="1.0",
            category="verify",
            template="""Based on the following evidence, generate a structured summary.

Evidence:
{evidence}

Requirements:
1. Each claim must cite its source
2. Distinguish facts from inferences
3. Note any gaps in evidence

Output as a structured list of claims.""",
            description="Paper survey generation prompt",
        ))

        self.register(PromptEntry(
            prompt_id="claim_check",
            version="1.0",
            category="verify",
            template="""Verify if the following claim is supported by the evidence.

Claim: {claim}

Evidence:
{evidence}

Output: SUPPORTS, NOT_ENOUGH, or REFUTES with brief reason.""",
            description="Claim verification prompt",
        ))

        self.register(PromptEntry(
            prompt_id="no_hallucination_check",
            version="1.0",
            category="verify",
            template="""Check if the answer contains unsupported claims.

Answer: {answer}

Available evidence:
{evidence}

For each statement in the answer:
1. Is it supported by the evidence? (yes/no/partial)
2. If not, what's missing?

Output JSON:
{{
  "has_unsupported": true/false,
  "unsupported_claims": [...],
  "suggestions": [...]
}}""",
            description="Check for hallucinations in generated answers",
        ))

    def _load_templates(self, templates_dir: Path) -> None:
        """Load prompt templates from YAML files."""
        try:
            import yaml
        except ImportError:
            return
        
        for yaml_file in templates_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    self.register(PromptEntry(
                        prompt_id=data.get("prompt_id", yaml_file.stem),
                        version=data.get("version", "1.0"),
                        template=data.get("template", ""),
                        description=data.get("description", ""),
                        category=data.get("category", "general"),
                    ))
            except Exception:
                pass

    def register(self, entry: PromptEntry) -> None:
        """Register a prompt."""
        key = f"{entry.prompt_id}:{entry.version}"
        self._prompts[key] = entry

    def get(self, prompt_id: str, version: str = "1.0") -> PromptEntry:
        """Get a prompt by ID and version."""
        key = f"{prompt_id}:{version}"
        if key not in self._prompts:
            raise KeyError(f"Prompt not found: {key}")
        return self._prompts[key]

    def get_latest(self, prompt_id: str) -> PromptEntry:
        """Get latest version of a prompt."""
        matching = [k for k in self._prompts if k.startswith(f"{prompt_id}:")]
        if not matching:
            raise KeyError(f"Prompt not found: {prompt_id}")
        # Sort by version and get latest
        matching.sort(reverse=True)
        return self._prompts[matching[0]]

    def render(
        self,
        prompt_id: str,
        version: str = "1.0",
        record_usage: bool = True,
        **kwargs
    ) -> str:
        """Render a prompt with variables."""
        entry = self.get(prompt_id, version)
        
        if record_usage:
            self._usage_log.append(PromptUsage(
                prompt_id=prompt_id,
                version=version,
                prompt_hash=entry.prompt_hash,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
        
        return entry.template.format(**kwargs)

    def list_all(self) -> list[str]:
        """List all registered prompt IDs."""
        return list(self._prompts.keys())
    
    def list_by_category(self, category: str) -> list[PromptEntry]:
        """List prompts by category."""
        return [p for p in self._prompts.values() if p.category == category]
    
    def get_usage_log(self) -> List[PromptUsage]:
        """Get usage log."""
        return self._usage_log
    
    def save_usage_log(self, filepath: Path) -> None:
        """Save usage log to prompts_used.json."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                [u.to_dict() for u in self._usage_log],
                f,
                indent=2,
                ensure_ascii=False
            )
    
    def clear_usage_log(self) -> None:
        """Clear usage log for new run."""
        self._usage_log = []
    
    def export_catalog(self) -> Dict[str, Any]:
        """Export all prompts as catalog."""
        return {
            key: entry.to_dict()
            for key, entry in self._prompts.items()
        }


# Global registry
_registry: Optional[PromptRegistry] = None


def get_registry() -> PromptRegistry:
    """Get global prompt registry."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry

