# JARVIS Research OS API リファレンス

> JARVIS_LOCALFIRST_ROADMAP に基づくローカルファースト研究OS

## 概要

JARVIS Research OSは、学術研究のためのローカルファースト・プライバシー重視の研究支援システムです。

## インストール

```bash
# 基本インストール
pip install -e .

# 開発用インストール
pip install -e ".[dev]"

# 全機能インストール
pip install -e ".[all]"
```

## クイックスタート

```python
from jarvis_core.sources import UnifiedSourceClient
from jarvis_core.analysis.grade_system import EnsembleGrader

# 文献検索
client = UnifiedSourceClient(email="your@email.com")
papers = client.search("machine learning healthcare", max_results=10)

# 証拠グレーディング
grader = EnsembleGrader(use_llm=False)
assessment = grader.grade(
    evidence_id="e1",
    claim_id="c1", 
    claim_text="ML improves diagnosis",
    evidence_text="RCT showed 30% improvement..."
)
```

---

## モジュール一覧

### 1. LLM統合 (`jarvis_core.llm`)

#### OllamaAdapter

ローカルOllamaサーバーとの統合。

```python
from jarvis_core.llm import OllamaAdapter

adapter = OllamaAdapter(base_url="http://localhost:11434")

# テキスト生成
response = adapter.generate("Explain quantum computing", max_tokens=500)

# ストリーミング生成
for chunk in adapter.generate_stream("Explain AI"):
    print(chunk, end="")

# 埋め込み生成
embeddings = adapter.embed(["text1", "text2"])
```

#### LlamaCppAdapter

llama.cppフォールバック用アダプター。

```python
from jarvis_core.llm import LlamaCppAdapter

adapter = LlamaCppAdapter(model_path="/path/to/model.gguf")
response = adapter.generate("Hello", max_tokens=100)
```

#### ModelRouter

タスクに基づく自動ルーティング。

```python
from jarvis_core.llm import get_router, TaskType

router = get_router()
decision = router.route(TaskType.GENERATION, complexity="high")
print(f"Provider: {decision.provider}, Model: {decision.model}")
```

---

### 2. 文献検索 (`jarvis_core.sources`)

#### UnifiedSourceClient

複数ソースの統合検索。

```python
from jarvis_core.sources import UnifiedSourceClient, SourceType

client = UnifiedSourceClient(email="user@example.com")

# 全ソース検索
papers = client.search("cancer immunotherapy", max_results=20)

# 特定ソースのみ
papers = client.search(
    "CRISPR", 
    sources=[SourceType.PUBMED, SourceType.OPENALEX]
)

# DOIで取得
paper = client.get_by_doi("10.1038/s41586-020-2649-2")
```

#### 個別クライアント

```python
from jarvis_core.sources import PubMedClient, SemanticScholarClient, OpenAlexClient

# PubMed
pubmed = PubMedClient(email="user@example.com")
pmids = pubmed.search("COVID-19 vaccine", max_results=50)
articles = pubmed.fetch(pmids)

# Semantic Scholar
s2 = SemanticScholarClient()
papers = s2.search("transformer architecture", limit=20)
citations = s2.get_citations(papers[0].paper_id)

# OpenAlex
openalex = OpenAlexClient(email="user@example.com")
works = openalex.search("climate change", filter_open_access=True)
```

---

### 3. 証拠分析 (`jarvis_core.analysis`)

#### GRADEシステム

```python
from jarvis_core.analysis.grade_system import (
    EnsembleGrader,
    grade_evidence_with_grade,
    GRADELevel
)

# 単一証拠のグレーディング
grader = EnsembleGrader(use_llm=True)
assessment = grader.grade(
    evidence_id="e1",
    claim_id="c1",
    claim_text="Drug X reduces mortality",
    evidence_text="RCT with 500 patients showed...",
)

print(f"Level: {assessment.final_level.value}")  # high/moderate/low/very_low
print(f"Confidence: {assessment.confidence_score}")

# バッチグレーディング
assessments, stats = grade_evidence_with_grade(evidence_list, claims)
```

#### 引用スタンス分析

```python
from jarvis_core.analysis.citation_stance import (
    analyze_citations,
    CitationStance
)

results, stats = analyze_citations(claims, evidence_list)

for r in results:
    if r.stance == CitationStance.CONTRADICTS:
        print(f"矛盾発見: {r.evidence_id} → {r.claim_id}")
```

#### 矛盾検出

```python
from jarvis_core.analysis.contradiction_detector import detect_contradictions

contradictions, stats = detect_contradictions(
    claims, evidence_list, stance_results
)

print(f"矛盾数: {stats['total_contradictions']}")
print(f"高重要度: {stats['high_severity']}")
```

---

### 4. PRISMA生成 (`jarvis_core.reporting`)

```python
from jarvis_core.reporting.prisma_generator import generate_prisma, PRISMAGenerator

# 簡易生成
markdown = generate_prisma(
    search_results=all_papers,
    screened_results=screened,
    included_results=included,
    title="My Systematic Review"
)

# 詳細制御
generator = PRISMAGenerator()
diagram = generator.from_pipeline_results(search, screened, included)
mermaid = generator.to_mermaid(diagram)
```

---

### 5. Active Learning (`jarvis_core.learning`)

```python
from jarvis_core.learning.active_learning import (
    create_active_learner,
    Label
)

# 学習ループ作成
learner = create_active_learner(
    samples=[{"id": str(i), "text": abstracts[i]} for i in range(len(abstracts))],
    strategy="combined",
    batch_size=10
)

# ラベリングループ
while learner.should_continue():
    batch = learner.get_next_batch()
    
    # ユーザーからラベル取得
    labels = [(s.sample_id, Label.INCLUDE, "Good") for s in batch]
    learner.submit_labels(labels)

included, excluded = learner.get_labeled_samples()
```

---

### 6. プラグインシステム (`jarvis_core.plugins`)

#### プラグイン作成

```python
from jarvis_core.plugins.plugin_system import (
    AnalyzerPlugin,
    PluginType,
    register_plugin
)

@register_plugin
class MyAnalyzer(AnalyzerPlugin):
    NAME = "my_analyzer"
    VERSION = "1.0.0"
    DESCRIPTION = "Custom analysis"
    
    def initialize(self):
        return True
    
    def analyze(self, data, **kwargs):
        return {"result": "analyzed"}
```

#### プラグイン使用

```python
from jarvis_core.plugins.plugin_system import get_registry

registry = get_registry()
plugin = registry.get_plugin("bibtex_exporter")
bibtex = plugin.export(papers)
```

---

### 7. キャッシュ (`jarvis_core.cache`)

```python
from jarvis_core.cache.sqlite_cache import SQLiteCache

cache = SQLiteCache(
    db_path="./cache.db",
    max_size_mb=100,
    default_ttl=3600  # 1時間
)

# 使用
cache.set("key", {"data": "value"}, namespace="api")
data = cache.get("key", namespace="api")

# 統計
stats = cache.stats()
print(f"ヒット率: {stats['hit_rate']:.1%}")
```

---

### 8. オフラインモード (`jarvis_core.runtime`)

```python
from jarvis_core.runtime.offline_manager import OfflineManager

manager = OfflineManager()

if manager.is_online:
    # オンライン処理
    result = api_call()
else:
    # オフラインフォールバック
    result = manager.get_cached_or_queue(operation)
```

---

## 環境変数

| 変数 | 説明 | デフォルト |
|------|------|------------|
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | デフォルトモデル | `llama3.1:8b` |
| `LLAMACPP_MODEL_PATH` | GGUFモデルパス | - |
| `ZOTERO_API_KEY` | Zotero APIキー | - |
| `ZOTERO_USER_ID` | ZoteroユーザーID | - |
| `JARVIS_OFFLINE` | オフライン強制 | `false` |

---

## ライセンス

MIT License
