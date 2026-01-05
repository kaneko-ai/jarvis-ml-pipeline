> Authority: ROADMAP (Level 5, Non-binding)

# Phase 3: 市場制覇 タスク詳細

**期間**: Week 17-24  
**目標スコア**: 103 → 120/100

---

## Sprint 17-18: AI高度化 (Week 33-36)

### Task 3.1: Active Learningスクリーニング

**目標**: ASReview相当の90%時間削減

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.1.1 | ALエンジン基盤 | `jarvis_core/screening/al_engine.py` | 不確実性サンプリング | 6h | [ ] |
| 3.1.2 | 特徴量抽出 | `jarvis_core/screening/features.py` | TF-IDF/BERT埋め込み | 4h | [ ] |
| 3.1.3 | 分類モデル | `jarvis_core/screening/classifier.py` | LightGBM/SVM | 4h | [ ] |
| 3.1.4 | クエリ戦略 | `jarvis_core/screening/query_strategy.py` | Uncertainty/Diversity | 4h | [ ] |
| 3.1.5 | 停止条件 | `jarvis_core/screening/stopping.py` | 安定性/カバレッジ基準 | 3h | [ ] |
| 3.1.6 | インタラクティブUI | `dashboard/screening.html` | ラベリングインターフェース | 8h | [ ] |
| 3.1.7 | CLIモード | `jarvis_cli.py` | `screen-papers` | 3h | [ ] |
| 3.1.8 | 進捗可視化 | `jarvis_core/screening/progress.py` | 推定残り、精度曲線 | 3h | [ ] |

**成果物例**:
```python
# jarvis_core/screening/al_engine.py
from dataclasses import dataclass
from typing import Protocol
import numpy as np

class QueryStrategy(Protocol):
    """クエリ戦略インターフェース"""
    def select_next(
        self,
        unlabeled_indices: list[int],
        probabilities: np.ndarray,
        n_samples: int = 1
    ) -> list[int]:
        ...

class UncertaintySampling(QueryStrategy):
    """不確実性サンプリング"""
    def select_next(
        self,
        unlabeled_indices: list[int],
        probabilities: np.ndarray,
        n_samples: int = 1
    ) -> list[int]:
        # 予測確率が0.5に近いサンプルを優先
        uncertainties = 1 - np.abs(probabilities - 0.5) * 2
        uncertain_indices = np.argsort(uncertainties)[::-1]
        return [unlabeled_indices[i] for i in uncertain_indices[:n_samples]]

@dataclass
class ScreeningState:
    """スクリーニング状態"""
    total_papers: int
    labeled_count: int
    included_count: int
    excluded_count: int
    estimated_remaining: int
    current_precision: float
    current_recall: float

class ActiveLearningEngine:
    """Active Learningスクリーニングエンジン"""
    
    def __init__(
        self,
        query_strategy: QueryStrategy,
        classifier,
        stopping_criterion,
    ):
        self.query_strategy = query_strategy
        self.classifier = classifier
        self.stopping_criterion = stopping_criterion
        self._state = None
    
    def initialize(self, papers: list[dict], features: np.ndarray):
        """初期化"""
        ...
    
    def get_next_papers(self, n: int = 10) -> list[dict]:
        """次にラベリングすべき論文を取得"""
        ...
    
    def label_papers(self, labels: dict[str, bool]):
        """ラベルを記録"""
        ...
    
    def should_stop(self) -> bool:
        """停止条件を確認"""
        ...
    
    def get_state(self) -> ScreeningState:
        """現在の状態を取得"""
        ...
```

---

### Task 3.2: Deep Chat（論文との対話）

**目標**: PubMed.ai相当の対話型QA

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.2.1 | ChatSession管理 | `jarvis_core/chat/session.py` | 会話履歴、コンテキスト | 4h | [ ] |
| 3.2.2 | 論文コンテキストRAG | `jarvis_core/chat/rag.py` | 選択論文ベースの回答 | 6h | [ ] |
| 3.2.3 | フォローアップ質問生成 | `jarvis_core/chat/followup.py` | 関連質問サジェスト | 3h | [ ] |
| 3.2.4 | 引用インライン表示 | `jarvis_core/chat/citation.py` | 回答内引用リンク | 3h | [ ] |
| 3.2.5 | WebSocket API | `jarvis_web/chat_ws.py` | リアルタイム対話 | 4h | [ ] |
| 3.2.6 | Dashboard統合 | `dashboard/chat.html` | チャットUI | 6h | [ ] |
| 3.2.7 | CLIチャットモード | `jarvis_cli.py` | `chat` | 2h | [ ] |

---

## Sprint 19-20: レポート・統合 (Week 37-40)

### Task 3.3: 自動レポート生成

**目標**: PubMed.ai相当の成果物化

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.3.1 | レポートテンプレート | `jarvis_core/report/templates/` | Jinja2テンプレート | 4h | [ ] |
| 3.3.2 | Markdown生成 | `jarvis_core/report/markdown.py` | 構造化Markdown | 3h | [ ] |
| 3.3.3 | PDF生成 | `jarvis_core/report/pdf.py` | WeasyPrint/ReportLab | 4h | [ ] |
| 3.3.4 | Word生成 | `jarvis_core/report/docx.py` | python-docx | 3h | [ ] |
| 3.3.5 | PowerPoint生成 | `jarvis_core/report/pptx.py` | python-pptx | 3h | [ ] |
| 3.3.6 | 引用フォーマット | `jarvis_core/report/citation_format.py` | APA/AMA/Vancouver | 3h | [ ] |
| 3.3.7 | CLIコマンド | `jarvis_cli.py` | `export-report` | 2h | [ ] |

---

### Task 3.4: Cross-Study Insight Mapping

**目標**: 複数論文の洞察統合

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.4.1 | テーマ抽出 | `jarvis_core/insight/theme_extractor.py` | LLMによるテーマ識別 | 4h | [ ] |
| 3.4.2 | コンセンサス検出 | `jarvis_core/insight/consensus.py` | 一致点の特定 | 4h | [ ] |
| 3.4.3 | 論争点検出 | `jarvis_core/insight/controversy.py` | 不一致点の特定 | 4h | [ ] |
| 3.4.4 | ギャップ分析 | `jarvis_core/insight/gap_analysis.py` | 研究ギャップの特定 | 4h | [ ] |
| 3.4.5 | インサイトマップ生成 | `jarvis_core/insight/map_generator.py` | 可視化データ出力 | 3h | [ ] |
| 3.4.6 | Bundle統合 | `jarvis_core/bundle/assembler.py` | insights.json追加 | 2h | [ ] |

---

### Task 3.5: Zotero/Mendeley連携

**目標**: 既存ワークフロー統合

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.5.1 | Zotero API統合 | `jarvis_core/integrations/zotero.py` | pyzotero | 4h | [ ] |
| 3.5.2 | Mendeley API統合 | `jarvis_core/integrations/mendeley.py` | mendeley-client | 4h | [ ] |
| 3.5.3 | RIS/BibTeX入出力 | `jarvis_core/integrations/bibliography.py` | 標準形式対応 | 3h | [ ] |
| 3.5.4 | 同期機能 | `jarvis_core/integrations/sync.py` | 双方向同期 | 4h | [ ] |
| 3.5.5 | CLIコマンド | `jarvis_cli.py` | `sync-zotero`, `sync-mendeley` | 2h | [ ] |

---

## Sprint 21-22: 運用・監視 (Week 41-44)

### Task 3.6: OpenTelemetry統合

**目標**: 分散トレーシング

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.6.1 | OTEL依存追加 | `requirements.txt` | opentelemetry-* | 1h | [ ] |
| 3.6.2 | Tracer設定 | `jarvis_core/telemetry/otel.py` | トレース初期化 | 3h | [ ] |
| 3.6.3 | スパン計装 | `jarvis_core/telemetry/instrumentation.py` | 各ステージのスパン | 4h | [ ] |
| 3.6.4 | メトリクス | `jarvis_core/telemetry/metrics.py` | カスタムメトリクス | 3h | [ ] |
| 3.6.5 | Jaeger統合 | `docker-compose.yml` | トレース可視化 | 2h | [ ] |
| 3.6.6 | Prometheus統合 | `docker-compose.yml` | メトリクス収集 | 2h | [ ] |
| 3.6.7 | Grafanaダッシュボード | `deploy/grafana/` | 可視化 | 4h | [ ] |

---

### Task 3.7: Cost Dashboard

**目標**: LLM API使用量可視化

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.7.1 | コスト記録 | `jarvis_core/cost/recorder.py` | run別コスト | 3h | [ ] |
| 3.7.2 | 予算管理 | `jarvis_core/cost/budget.py` | 上限設定・アラート | 3h | [ ] |
| 3.7.3 | レポート生成 | `jarvis_core/cost/report.py` | 日次/月次レポート | 3h | [ ] |
| 3.7.4 | Dashboard統合 | `dashboard/finance.html` | コスト可視化 | 4h | [ ] |
| 3.7.5 | CLIコマンド | `jarvis_cli.py` | `cost-report` | 2h | [ ] |

---

## Sprint 23-24: コラボレーション・最終統合 (Week 45-48)

### Task 3.8: チームコラボレーション

**目標**: Rayyan/Covidence相当の協調作業

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.8.1 | ユーザー管理 | `jarvis_core/auth/user.py` | 認証・認可 | 6h | [ ] |
| 3.8.2 | チーム管理 | `jarvis_core/auth/team.py` | チーム作成・招待 | 4h | [ ] |
| 3.8.3 | 権限管理 | `jarvis_core/auth/permissions.py` | Owner/Editor/Viewer | 4h | [ ] |
| 3.8.4 | レビュー割り当て | `jarvis_core/collab/assignment.py` | タスク分配 | 4h | [ ] |
| 3.8.5 | コンフリクト解決 | `jarvis_core/collab/conflict.py` | スクリーニング不一致処理 | 4h | [ ] |
| 3.8.6 | コメント機能 | `jarvis_core/collab/comments.py` | 論文/Claimへのコメント | 4h | [ ] |
| 3.8.7 | Dashboard統合 | `dashboard/team.html` | チームUI | 6h | [ ] |
| 3.8.8 | WebSocket通知 | `jarvis_web/notifications.py` | リアルタイム通知 | 4h | [ ] |

---

### Task 3.9: 最終統合・最適化

**目標**: 全機能の統合テスト・パフォーマンス最適化

| ID | サブタスク | ファイル | 詳細 | 見積 | 状態 |
|----|-----------|---------|------|------|------|
| 3.9.1 | 統合E2Eテスト | `tests/e2e/test_full_workflow.py` | 全機能通しテスト | 8h | [ ] |
| 3.9.2 | パフォーマンスプロファイリング | `tools/profiler.py` | ボトルネック特定 | 4h | [ ] |
| 3.9.3 | キャッシュ最適化 | `jarvis_core/cache/` | Redis/メモリキャッシュ | 4h | [ ] |
| 3.9.4 | 並列処理最適化 | `jarvis_core/parallel/` | asyncio/multiprocessing | 4h | [ ] |
| 3.9.5 | メモリ最適化 | - | 大規模データ処理 | 4h | [ ] |
| 3.9.6 | ドキュメント最終化 | `docs/` | 全ドキュメント更新 | 8h | [ ] |
| 3.9.7 | リリースノート | `CHANGELOG.md` | v1.0.0リリース | 2h | [ ] |

---

## Phase 3 完了チェックリスト

- [ ] Task 3.1: Active Learningスクリーニング
- [ ] Task 3.2: Deep Chat
- [ ] Task 3.3: 自動レポート生成
- [ ] Task 3.4: Cross-Study Insight Mapping
- [ ] Task 3.5: Zotero/Mendeley連携
- [ ] Task 3.6: OpenTelemetry統合
- [ ] Task 3.7: Cost Dashboard
- [ ] Task 3.8: チームコラボレーション
- [ ] Task 3.9: 最終統合・最適化

**Phase 3 完了基準**:
- Active Learningで90%時間削減達成
- チャット機能がWebSocket対応
- 複数フォーマットでレポート出力
- Grafanaダッシュボード稼働
- チームコラボレーション機能稼働
- v1.0.0リリース完了
