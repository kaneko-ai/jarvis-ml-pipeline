> Authority: ROADMAP (Level 5, Non-binding)

# Phase 1: 基盤強化 タスク詳細

**期間**: Week 1-8  
**目標スコア**: 80 → 88/100

---

## Sprint 1-2: テスト・品質基盤 (Week 1-4)

### Task 1.1: E2Eテスト完全実装

**目標**: `test_e2e_offline.py`のskip解除、全パイプラインのE2E検証

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.1.1 | オフラインコーパス拡充 | `tests/e2e/fixtures/offline_corpus.json` | 10論文以上、セクション・図表メタデータ含む | 4h | [ ] |
| 1.1.2 | E2Eテストフィクスチャ作成 | `tests/e2e/conftest.py` | pytest fixture、一時ディレクトリ、モックLLM | 4h | [ ] |
| 1.1.3 | パイプライン統合テスト | `tests/e2e/test_pipeline_integration.py` | 各ステージの入出力検証 | 8h | [ ] |
| 1.1.4 | Bundle契約検証テスト | `tests/e2e/test_bundle_contract.py` | 10ファイル生成確認、スキーマ検証 | 6h | [ ] |
| 1.1.5 | 品質ゲート通過テスト | `tests/e2e/test_quality_gates.py` | citation/locator/断定/PII全ゲート | 6h | [ ] |
| 1.1.6 | 失敗シナリオテスト | `tests/e2e/test_failure_scenarios.py` | 各FailCode発生条件のテスト | 6h | [ ] |
| 1.1.7 | Golden Test Suite作成 | `tests/golden/` | 期待出力との差分検出、回帰テスト | 8h | [ ] |
| 1.1.8 | CI E2E統合 | `.github/workflows/e2e.yml` | E2Eテスト専用ワークフロー | 4h | [ ] |

**完了条件**:
- [ ] 全E2Eテストがskipなしで通過
- [ ] CI通過率100%
- [ ] Golden Test 5ケース以上

**成果物例**:
```python
# tests/e2e/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def offline_corpus():
    corpus_path = Path(__file__).parent / "fixtures" / "offline_corpus.json"
    with open(corpus_path) as f:
        return json.load(f)

@pytest.fixture
def mock_llm():
    """LLM呼び出しをモック化"""
    class MockLLM:
        async def complete(self, prompt: str) -> str:
            return "Mock response with [citation needed]"
    return MockLLM()
```

---

### Task 1.2: 静的解析・型チェック強化

**目標**: Ruff/Black/mypy strictモードでCI必須化

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.2.1 | Ruff設定追加 | `pyproject.toml` | ルールセット選定（I, E, W, F, B, Q） | 2h | [ ] |
| 1.2.2 | Black設定追加 | `pyproject.toml` | line-length=100、target-version | 1h | [ ] |
| 1.2.3 | mypy strict設定 | `pyproject.toml` | strict=true、プラグイン設定 | 2h | [ ] |
| 1.2.4 | 既存コードRuff修正 | `jarvis_core/**/*.py` | 自動修正 + 手動対応 | 8h | [ ] |
| 1.2.5 | 既存コードBlack適用 | `jarvis_core/**/*.py` | フォーマット統一 | 2h | [ ] |
| 1.2.6 | 型アノテーション追加 | `jarvis_core/**/*.py` | 全public関数に型ヒント | 12h | [ ] |
| 1.2.7 | CI lint統合 | `.github/workflows/lint.yml` | Ruff/Black/mypyチェック | 2h | [ ] |
| 1.2.8 | pre-commit設定 | `.pre-commit-config.yaml` | ローカルフック設定 | 2h | [ ] |

**完了条件**:
- [ ] `ruff check .` エラー0
- [ ] `black --check .` 差分0
- [ ] `mypy --strict .` エラー0
- [ ] pre-commit hookが動作

**成果物例**:
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "B", "Q", "UP", "ANN", "S", "C4"]
ignore = ["ANN101", "ANN102", "S101"]

[tool.ruff.per-file-ignores]
"tests/**/*.py" = ["S101", "ANN"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["pydantic.mypy"]
warn_return_any = true
warn_unused_configs = true
```

---

### Task 1.3: Property-based Testing導入

**目標**: Hypothesisによるエッジケース自動発見

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.3.1 | Hypothesis依存追加 | `requirements-dev.txt` | hypothesis>=6.0 | 0.5h | [ ] |
| 1.3.2 | カスタムStrategy作成 | `tests/strategies.py` | Paper/Claim/Evidence生成戦略 | 4h | [ ] |
| 1.3.3 | QualityGateVerifierテスト | `tests/property/test_quality_gate_props.py` | 任意入力での不変条件検証 | 4h | [ ] |
| 1.3.4 | BundleAssemblerテスト | `tests/property/test_bundle_props.py` | 成果物契約の不変条件 | 4h | [ ] |
| 1.3.5 | パーサーテスト | `tests/property/test_parser_props.py` | PDF/テキスト解析の堅牢性 | 4h | [ ] |

**成果物例**:
```python
# tests/strategies.py
from hypothesis import strategies as st

@st.composite
def paper_strategy(draw):
    return {
        "paper_id": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N")))),
        "title": draw(st.text(min_size=1, max_size=200)),
        "abstract": draw(st.text(max_size=2000)),
        "year": draw(st.integers(min_value=1900, max_value=2030)),
        "authors": draw(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10)),
    }

@st.composite
def claim_strategy(draw, paper_id=None):
    return {
        "claim_id": draw(st.uuids().map(str)),
        "paper_id": paper_id or draw(st.text(min_size=1, max_size=50)),
        "claim_text": draw(st.text(min_size=10, max_size=500)),
        "section": draw(st.sampled_from(["abstract", "introduction", "methods", "results", "discussion"])),
    }
```

---

### Task 1.4: セキュリティ・依存関係管理

**目標**: Dependabot/CodeQL導入、SBOM生成

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.4.1 | Dependabot設定 | `.github/dependabot.yml` | Python/npm/Actions更新 | 1h | [ ] |
| 1.4.2 | CodeQL設定 | `.github/workflows/codeql.yml` | Python SAST | 2h | [ ] |
| 1.4.3 | SBOM生成スクリプト | `tools/generate_sbom.py` | CycloneDX形式出力 | 3h | [ ] |
| 1.4.4 | 脆弱性スキャン | `.github/workflows/security.yml` | pip-audit/safety統合 | 2h | [ ] |
| 1.4.5 | Secrets検出 | `.github/workflows/secrets.yml` | gitleaks/trufflehog | 2h | [ ] |

**成果物例**:
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "python"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "ci"
```

---

## Sprint 3-4: Multi-LLM・データソース統合 (Week 5-8)

### Task 1.5: LiteLLM完全統合

**目標**: OpenAI/Anthropic/Gemini/Ollama対応

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.5.1 | LiteLLM依存追加 | `requirements.txt` | litellm>=1.0 | 0.5h | [ ] |
| 1.5.2 | LLMClient抽象化 | `jarvis_core/llm/base.py` | Protocol定義、共通インターフェース | 4h | [ ] |
| 1.5.3 | LiteLLMAdapter実装 | `jarvis_core/llm/litellm_adapter.py` | LiteLLMラッパー | 6h | [ ] |
| 1.5.4 | レート制限管理 | `jarvis_core/llm/rate_limiter.py` | プロバイダ別レート制限 | 4h | [ ] |
| 1.5.5 | コスト追跡 | `jarvis_core/llm/cost_tracker.py` | トークン使用量・コスト記録 | 4h | [ ] |
| 1.5.6 | モデル設定Schema | `jarvis_core/llm/config.py` | Pydantic設定モデル | 3h | [ ] |
| 1.5.7 | CLI統合 | `jarvis_cli.py` | `--llm`, `--embedding`オプション | 2h | [ ] |
| 1.5.8 | Ollama統合テスト | `tests/integration/test_ollama.py` | ローカルLLMテスト | 3h | [ ] |
| 1.5.9 | フォールバック機構 | `jarvis_core/llm/fallback.py` | プロバイダ障害時の自動切替 | 4h | [ ] |

**成果物例**:
```python
# jarvis_core/llm/base.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMProvider(Protocol):
    """LLMプロバイダの共通インターフェース"""
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """テキスト生成"""
        ...
    
    async def embed(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        """テキスト埋め込み"""
        ...
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """コスト見積"""
        ...
    
    @property
    def model_name(self) -> str:
        """モデル名"""
        ...
```

```python
# jarvis_core/llm/litellm_adapter.py
import litellm
from .base import LLMProvider

class LiteLLMAdapter(LLMProvider):
    """LiteLLMを使用したマルチプロバイダアダプタ"""
    
    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        rate_limit: dict | None = None,
    ):
        self.model = model
        self._api_key = api_key
        self._rate_limiter = RateLimiter(rate_limit or {})
        self._cost_tracker = CostTracker()
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        await self._rate_limiter.acquire()
        
        response = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        self._cost_tracker.record(
            model=self.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
        
        return response.choices[0].message.content
```

---

### Task 1.6: Semantic Scholar API統合

**目標**: 138M+論文へのアクセス

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.6.1 | S2 APIクライアント基盤 | `jarvis_core/api/semantic_scholar.py` | 認証、レート制限、リトライ | 6h | [ ] |
| 1.6.2 | 論文検索エンドポイント | `jarvis_core/api/semantic_scholar.py` | keyword/semantic検索 | 4h | [ ] |
| 1.6.3 | 論文詳細取得 | `jarvis_core/api/semantic_scholar.py` | メタデータ、引用、参照 | 4h | [ ] |
| 1.6.4 | 著者情報取得 | `jarvis_core/api/semantic_scholar.py` | 著者プロファイル、論文リスト | 3h | [ ] |
| 1.6.5 | 引用グラフ取得 | `jarvis_core/api/semantic_scholar.py` | 引用/被引用関係 | 4h | [ ] |
| 1.6.6 | キャッシュ層 | `jarvis_core/api/cache.py` | Redis/SQLiteキャッシュ | 4h | [ ] |
| 1.6.7 | PubMed統合アダプタ | `jarvis_core/api/unified_search.py` | 複数ソース統合検索 | 4h | [ ] |
| 1.6.8 | 統合テスト | `tests/integration/test_semantic_scholar.py` | モック/実APIテスト | 4h | [ ] |

**成果物例**:
```python
# jarvis_core/api/semantic_scholar.py
from pydantic import BaseModel
import httpx

class Paper(BaseModel):
    paper_id: str
    title: str
    abstract: str | None
    year: int | None
    citation_count: int
    authors: list[dict]
    venue: str | None
    url: str | None
    pdf_url: str | None

class SemanticScholarClient:
    """Semantic Scholar API クライアント"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"x-api-key": api_key} if api_key else {}
        )
    
    async def search_papers(
        self,
        query: str,
        fields: list[str] | None = None,
        limit: int = 100,
        year_range: tuple[int, int] | None = None,
        open_access_only: bool = False,
    ) -> list[Paper]:
        """論文検索"""
        default_fields = [
            "paperId", "title", "abstract", "year",
            "citationCount", "authors", "venue", "url", "openAccessPdf"
        ]
        
        params = {
            "query": query,
            "fields": ",".join(fields or default_fields),
            "limit": min(limit, 100),
        }
        
        if year_range:
            params["year"] = f"{year_range[0]}-{year_range[1]}"
        if open_access_only:
            params["openAccessPdf"] = ""
        
        response = await self._client.get(
            f"{self.BASE_URL}/paper/search",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        return [self._to_paper(p) for p in data.get("data", [])]
    
    async def get_paper(self, paper_id: str) -> Paper:
        """論文詳細取得"""
        ...
    
    async def get_citations(self, paper_id: str, limit: int = 100) -> list[Paper]:
        """被引用論文取得"""
        ...
    
    async def get_references(self, paper_id: str, limit: int = 100) -> list[Paper]:
        """参照論文取得"""
        ...
```

---

### Task 1.7: arXiv API統合

**目標**: プレプリントへのアクセス

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.7.1 | arXiv APIクライアント | `jarvis_core/api/arxiv_client.py` | OAI-PMH/REST API対応 | 4h | [ ] |
| 1.7.2 | 検索機能 | `jarvis_core/api/arxiv_client.py` | カテゴリ/日付フィルタ | 3h | [ ] |
| 1.7.3 | PDF取得 | `jarvis_core/api/arxiv_client.py` | PDF自動ダウンロード | 2h | [ ] |
| 1.7.4 | メタデータ正規化 | `jarvis_core/api/arxiv_client.py` | 統一Paperスキーマへ変換 | 2h | [ ] |
| 1.7.5 | 統合検索への組み込み | `jarvis_core/api/unified_search.py` | arXiv追加 | 2h | [ ] |

---

### Task 1.8: OpenAlex統合

**目標**: オープンな学術データベースアクセス

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.8.1 | OpenAlex APIクライアント | `jarvis_core/api/openalex_client.py` | Works/Authors/Venues API | 6h | [ ] |
| 1.8.2 | フィルタリング機能 | `jarvis_core/api/openalex_client.py` | 機関/資金源/OAステータス | 3h | [ ] |
| 1.8.3 | 引用メトリクス取得 | `jarvis_core/api/openalex_client.py` | 被引用数、h-index | 2h | [ ] |
| 1.8.4 | 統合検索への組み込み | `jarvis_core/api/unified_search.py` | OpenAlex追加 | 2h | [ ] |

---

## Sprint 5-6: CLI/UX改善 (Week 9-12)

### Task 1.9: Rich CLI出力

**目標**: 美しいターミナルUI

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.9.1 | Rich依存追加 | `requirements.txt` | rich>=13.0, typer>=0.9 | 0.5h | [ ] |
| 1.9.2 | プログレスバー実装 | `jarvis_core/ui/progress.py` | ステージ進捗表示 | 3h | [ ] |
| 1.9.3 | テーブル出力 | `jarvis_core/ui/tables.py` | 論文/Claim/Evidence表示 | 3h | [ ] |
| 1.9.4 | パネル出力 | `jarvis_core/ui/panels.py` | 回答/警告/エラー表示 | 2h | [ ] |
| 1.9.5 | シンタックスハイライト | `jarvis_core/ui/syntax.py` | JSON/YAML/Markdown表示 | 2h | [ ] |
| 1.9.6 | CLI Typer移行 | `jarvis_cli.py` | argparse→Typer | 4h | [ ] |
| 1.9.7 | Tab補完 | `jarvis_cli.py` | --install-completion | 1h | [ ] |
| 1.9.8 | エラーメッセージ改善 | `jarvis_core/ui/errors.py` | 具体的解決策提示 | 3h | [ ] |

**成果物例**:
```python
# jarvis_core/ui/progress.py
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
from contextlib import contextmanager

console = Console()

class PipelineProgress:
    """パイプライン実行の進捗表示"""
    
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        )
        self._tasks: dict[str, int] = {}
    
    @contextmanager
    def track_pipeline(self, stages: list[str]):
        """パイプライン全体の進捗追跡"""
        with self.progress:
            for stage in stages:
                self._tasks[stage] = self.progress.add_task(
                    f"[cyan]{stage}",
                    total=100
                )
            yield self
    
    def update_stage(self, stage: str, progress: int, status: str = ""):
        """ステージ進捗更新"""
        if stage in self._tasks:
            self.progress.update(
                self._tasks[stage],
                completed=progress,
                description=f"[cyan]{stage}" + (f" - {status}" if status else "")
            )
    
    def complete_stage(self, stage: str):
        """ステージ完了"""
        if stage in self._tasks:
            self.progress.update(
                self._tasks[stage],
                completed=100,
                description=f"[green]✓ {stage}"
            )
```

---

### Task 1.10: Interactive Mode

**目標**: 対話式タスク入力

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.10.1 | Prompt Toolkit統合 | `jarvis_core/ui/interactive.py` | 入力補完、履歴 | 4h | [ ] |
| 1.10.2 | ウィザード形式入力 | `jarvis_core/ui/wizard.py` | ステップバイステップ設定 | 4h | [ ] |
| 1.10.3 | 設定プレビュー | `jarvis_core/ui/wizard.py` | 実行前確認画面 | 2h | [ ] |
| 1.10.4 | セッション保存 | `jarvis_core/ui/session.py` | 途中経過の保存/復元 | 3h | [ ] |

---

## Sprint 7-8: ドキュメント・配布 (Week 13-16)

### Task 1.11: API Reference自動生成

**目標**: mkdocs + mkdocstrings

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.11.1 | mkdocs設定 | `mkdocs.yml` | Material theme設定 | 2h | [ ] |
| 1.11.2 | mkdocstrings設定 | `mkdocs.yml` | Python autodoc | 2h | [ ] |
| 1.11.3 | APIリファレンス生成 | `docs/api/` | 全モジュールドキュメント | 4h | [ ] |
| 1.11.4 | チュートリアル作成 | `docs/tutorials/` | 5本以上のガイド | 8h | [ ] |
| 1.11.5 | アーキテクチャ図 | `docs/architecture/` | Mermaid図10枚以上 | 4h | [ ] |
| 1.11.6 | GitHub Pages設定 | `.github/workflows/docs.yml` | 自動デプロイ | 2h | [ ] |
| 1.11.7 | CHANGELOG自動生成 | `.github/workflows/release.yml` | semantic-release | 3h | [ ] |

**成果物例**:
```yaml
# mkdocs.yml
site_name: JARVIS Research OS
site_url: https://kaneko-ai.github.io/jarvis-ml-pipeline/
repo_url: https://github.com/kaneko-ai/jarvis-ml-pipeline
repo_name: kaneko-ai/jarvis-ml-pipeline

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - search.highlight
    - content.code.copy

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            show_root_heading: true
            heading_level: 2

nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quickstart: getting-started/quickstart.md
    - Configuration: getting-started/configuration.md
  - Tutorials:
    - Basic Usage: tutorials/basic-usage.md
    - Literature Review: tutorials/literature-review.md
    - Systematic Review: tutorials/systematic-review.md
  - API Reference:
    - Core: api/core.md
    - LLM: api/llm.md
    - Evidence: api/evidence.md
    - Pipeline: api/pipeline.md
  - Development:
    - Contributing: development/contributing.md
    - Architecture: development/architecture.md
```

---

### Task 1.12: Docker公式イメージ

**目標**: Docker Hub公開、簡単デプロイ

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.12.1 | Dockerfile最適化 | `Dockerfile` | マルチステージビルド | 3h | [ ] |
| 1.12.2 | docker-compose作成 | `docker-compose.yml` | 開発/本番環境 | 2h | [ ] |
| 1.12.3 | Docker Hub自動プッシュ | `.github/workflows/docker.yml` | タグ時自動ビルド | 2h | [ ] |
| 1.12.4 | devcontainer設定 | `.devcontainer/` | VSCode開発環境 | 2h | [ ] |
| 1.12.5 | Helmチャート | `deploy/helm/` | Kubernetes対応 | 4h | [ ] |

**成果物例**:
```dockerfile
# Dockerfile
# ===== Builder Stage =====
FROM python:3.11-slim as builder

WORKDIR /app

# 依存関係のインストール
COPY requirements.lock .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.lock

# ===== Runtime Stage =====
FROM python:3.11-slim

WORKDIR /app

# 非rootユーザー作成
RUN useradd --create-home --shell /bin/bash jarvis

# wheelからインストール
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# アプリケーションコピー
COPY --chown=jarvis:jarvis . .

USER jarvis

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import jarvis_core; print('OK')" || exit 1

ENTRYPOINT ["python", "jarvis_cli.py"]
CMD ["--help"]
```

---

### Task 1.13: PyPI公開

**目標**: `pip install jarvis-research-os`

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 1.13.1 | pyproject.toml整備 | `pyproject.toml` | メタデータ、依存関係 | 2h | [ ] |
| 1.13.2 | エントリーポイント設定 | `pyproject.toml` | CLI/API公開 | 1h | [ ] |
| 1.13.3 | バージョニング | `jarvis_core/__version__.py` | CalVer採用 | 1h | [ ] |
| 1.13.4 | PyPI自動公開 | `.github/workflows/pypi.yml` | タグ時自動公開 | 2h | [ ] |
| 1.13.5 | TestPyPI検証 | - | 公開前テスト | 1h | [ ] |

**成果物例**:
```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "jarvis-research-os"
dynamic = ["version"]
description = "AI-powered scientific research assistant with reproducible pipelines"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "Kaneko AI", email = "kaneko@example.com" }
]
keywords = [
    "research",
    "ai",
    "llm",
    "scientific-literature",
    "systematic-review",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "litellm>=1.0",
    "pydantic>=2.0",
    "httpx>=0.25",
    "rich>=13.0",
    "typer>=0.9",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "hypothesis>=6.0",
    "ruff>=0.1",
    "black>=23.0",
    "mypy>=1.0",
]
docs = [
    "mkdocs>=1.5",
    "mkdocs-material>=9.0",
    "mkdocstrings[python]>=0.24",
]

[project.scripts]
jarvis = "jarvis_core.cli:app"

[project.urls]
Homepage = "https://github.com/kaneko-ai/jarvis-ml-pipeline"
Documentation = "https://kaneko-ai.github.io/jarvis-ml-pipeline/"
Repository = "https://github.com/kaneko-ai/jarvis-ml-pipeline"
Issues = "https://github.com/kaneko-ai/jarvis-ml-pipeline/issues"

[tool.hatch.version]
path = "jarvis_core/__version__.py"
```

---

## Phase 1 完了チェックリスト

- [ ] Task 1.1: E2Eテスト完全実装
- [ ] Task 1.2: 静的解析・型チェック強化
- [ ] Task 1.3: Property-based Testing導入
- [ ] Task 1.4: セキュリティ・依存関係管理
- [ ] Task 1.5: LiteLLM完全統合
- [ ] Task 1.6: Semantic Scholar API統合
- [ ] Task 1.7: arXiv API統合
- [ ] Task 1.8: OpenAlex統合
- [ ] Task 1.9: Rich CLI出力
- [ ] Task 1.10: Interactive Mode
- [ ] Task 1.11: API Reference自動生成
- [ ] Task 1.12: Docker公式イメージ
- [ ] Task 1.13: PyPI公開

**Phase 1 完了基準**:
- E2Eテスト通過率100%
- lint/type check CI通過
- 3データソース（PubMed/S2/arXiv）統合完了
- ドキュメントサイト公開
- Docker Hub/PyPI公開
