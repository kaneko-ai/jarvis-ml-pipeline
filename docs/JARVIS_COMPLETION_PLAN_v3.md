# JARVIS Research OS 完遂計画書 v3.0
## 47.2% → 100% (120点達成) ロードマップ

> **Authority**: ROADMAP (Level 5, Non-binding)  
> **Repository**: https://github.com/kaneko-ai/jarvis-ml-pipeline  
> **作成日**: 2026-01-06  
> **現在達成率**: 47.2% (875/1000点 = 87.5点)  
> **目標**: 120点 (1200/1000点)  
> **残り期間**: 12週間（Sprint 13-24）

---

## 目次

1. [エグゼクティブサマリー](#1-エグゼクティブサマリー)
2. [現状分析と残タスク](#2-現状分析と残タスク)
3. [Sprint計画（週次）](#3-sprint計画週次)
4. [タスク詳細仕様](#4-タスク詳細仕様)
5. [ファイル作成計画](#5-ファイル作成計画)
6. [テスト計画](#6-テスト計画)
7. [品質ゲート](#7-品質ゲート)
8. [リスクと対策](#8-リスクと対策)
9. [Skills連携フロー](#9-skills連携フロー)
10. [完了判定基準](#10-完了判定基準)

---

## 1. エグゼクティブサマリー

### 1.1 達成状況サマリー

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           現状 → 目標                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  達成率:     47.2%  ━━━━━━━━━━━━━━━━━━━▶  100%                              ║
║  スコア:     87.5点 ━━━━━━━━━━━━━━━━━━━▶  120点                             ║
║  残り期間:   12週間                                                          ║
║  残りタスク: 29タスク / 156サブタスク                                        ║
║  残り工数:   約507時間                                                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 1.2 完遂までの道筋

```
Week 1-2:   Phase 1 残り完了        → 68% → 85%  (+17%)
Week 3-6:   Phase 2 差別化機能      → 85% → 92%  (+7%)
Week 7-10:  Phase 2 完了 + Phase 3  → 92% → 97%  (+5%)
Week 11-12: 最終統合・最適化        → 97% → 100% (+3%)
```

### 1.3 主要マイルストーン

| マイルストーン | 週 | 達成基準 | スコア目標 |
|---------------|-----|---------|-----------|
| M1.5: Phase 1完了 | Week 2 | オフライン基本動作 | 92点 |
| M2: 差別化機能MVP | Week 6 | 証拠グレーディング動作 | 102点 |
| M2.5: Phase 2完了 | Week 10 | 全差別化機能動作 | 112点 |
| M3: v1.0リリース | Week 12 | 120点達成・PyPI公開 | 120点 |

---

## 2. 現状分析と残タスク

### 2.1 Phase別残タスク一覧

```yaml
phase_1_remaining:  # 残り 32% (102h)
  task_1_1:  # ローカルLLM - 残り 15%
    - 1.1.4: 既存コード置換完了 (残30%)
    - 1.1.5: モデル管理CLI (未着手)
    
  task_1_2:  # ローカル埋め込み - 残り 60%
    - 1.2.1: Sentence Transformers統合 (残50%)
    - 1.2.2: BM25スパース埋め込み (未着手)
    - 1.2.3: ハイブリッド検索 (未着手)
    - 1.2.4: ベクトルストア改良 (残80%)
    - 1.2.5: 既存埋め込み置換 (残70%)
    
  task_1_3:  # キャッシュ - 残り 20%
    - 1.3.2: FTS5専用モジュール (残40%)
    - 1.3.4: キャッシュ管理CLI (未着手)
    
  task_1_4:  # 無料API - 残り 25%
    - 1.4.4: arXivクライアント (残70%)
    - 1.4.5: Crossref/Unpaywall (残80%)
    
  task_1_5:  # オフラインモード - 残り 50%
    - 1.5.1: ネットワーク検出 (残70%)
    - 1.5.2: オフライン設定 (残60%)
    - 1.5.3: CLIオプション (未着手)
    - 1.5.4: グレースフルデグラデーション (残50%)
    - 1.5.5: 同期キュー (未着手)
    - 1.5.6: オンライン復帰同期 (未着手)

phase_2_remaining:  # 残り 80% (224h)
  task_2_1:  # 証拠グレーディング - 残り 75%
  task_2_2:  # 引用分析 - 残り 85%
  task_2_3:  # 矛盾検出 - 残り 90%
  task_2_4:  # PRISMA - 残り 85%
  task_2_5:  # Active Learning - 残り 70%

phase_3_remaining:  # 残り 85% (255h)
  task_3_1:  # プラグイン - 残り 90%
  task_3_2:  # 外部連携 - 残り 95%
  task_3_3:  # ドキュメント - 残り 60%
  task_3_4:  # 配布 - 残り 70%
  task_3_5:  # 最適化 - 残り 80%
```

### 2.2 残タスク優先度マトリックス

```
                    影響度
              低         中         高
         ┌─────────┬─────────┬─────────┐
    高   │ 3.2     │ 2.3     │ 1.2     │  ← 即座に着手
         │ 外部連携 │ 矛盾検出 │ 埋め込み │
 緊 ├─────────┼─────────┼─────────┤
 急 中   │ 3.1     │ 2.4     │ 1.5     │  ← 次Sprint
 度      │ プラグイン│ PRISMA  │ オフライン│
    ├─────────┼─────────┼─────────┤
    低   │ 1.3.4   │ 3.3     │ 2.1,2.2 │  ← 計画的に
         │ cache CLI│ ドキュメント│ 差別化  │
         └─────────┴─────────┴─────────┘
```

---

## 3. Sprint計画（週次）

### 3.1 Sprint 13-14: Phase 1 完了（Week 1-2）

```yaml
sprint_13:  # Week 1
  goal: "ローカル埋め込み・ハイブリッド検索完成"
  duration: "5 days"
  capacity: "40h"
  
  tasks:
    day_1_2:  # 月-火
      - id: 1.2.1-complete
        name: "Sentence Transformers専用モジュール"
        effort: "8h"
        
      - id: 1.2.2
        name: "BM25スパース埋め込み"
        effort: "6h"
        
    day_3_4:  # 水-木
      - id: 1.2.3
        name: "ハイブリッド検索"
        effort: "8h"
        
      - id: 1.2.4-complete
        name: "ベクトルストア改良"
        effort: "6h"
        
    day_5:  # 金
      - id: 1.2.5
        name: "既存埋め込み呼び出し置換"
        effort: "6h"
        
      - id: review
        name: "Sprint Review & テスト"
        effort: "4h"

  deliverables:
    - jarvis_core/embeddings/ 完全版
    - ハイブリッド検索動作確認
    - テストカバレッジ 85%+


sprint_14:  # Week 2
  goal: "オフラインモード完成・無料API完了"
  duration: "5 days"
  capacity: "40h"
  
  tasks:
    day_1:  # 月
      - id: 1.4.4
        name: "arXivクライアント完成"
        effort: "4h"
        
      - id: 1.4.5
        name: "Crossref/Unpaywallクライアント"
        effort: "4h"
        
    day_2_3:  # 火-水
      - id: 1.5.1-1.5.2
        name: "ネットワーク検出・オフライン設定"
        effort: "6h"
        
      - id: 1.5.3
        name: "CLIオフラインオプション"
        effort: "4h"
        
      - id: 1.5.4
        name: "グレースフルデグラデーション"
        effort: "6h"
        
    day_4:  # 木
      - id: 1.5.5
        name: "同期キュー実装"
        effort: "6h"
        
      - id: 1.5.6
        name: "オンライン復帰同期"
        effort: "4h"
        
    day_5:  # 金
      - id: 1.1.5
        name: "モデル管理CLI"
        effort: "4h"
        
      - id: 1.3.4
        name: "キャッシュ管理CLI"
        effort: "2h"
        
      - id: m1_5_gate
        name: "M1.5ゲート検証"
        effort: "4h"

  gate_criteria:
    - "jarvis run --offline --goal 'test' が動作"
    - "pytest tests/ -v 全パス"
    - "スコア 92点以上"
```

### 3.2 Sprint 15-18: Phase 2 差別化機能（Week 3-6）

```yaml
sprint_15:  # Week 3
  goal: "証拠グレーディング基盤"
  capacity: "40h"
  tasks:
    - 証拠グレードスキーマ定義
    - ルールベース分類器
    - LLMベース分類器
    - アンサンブル統合


sprint_16:  # Week 4
  goal: "引用分析（Support/Contrast）"
  capacity: "40h"
  tasks:
    - 引用コンテキスト抽出
    - Support/Contrast/Mention分類
    - 引用グラフ構築
    - 引用統計計算
    - 可視化コンポーネント


sprint_17:  # Week 5
  goal: "矛盾検出・PICO抽出"
  capacity: "40h"
  tasks:
    - 主張正規化
    - 類似主張検出
    - 矛盾判定器
    - 矛盾レポート生成
    - PICO抽出


sprint_18:  # Week 6
  goal: "PRISMA・Active Learning・M2ゲート"
  capacity: "40h"
  tasks:
    - PRISMAデータモデル
    - フローチャートジェネレータ
    - PDF/SVG出力
    - ALエンジン基盤
    - クエリ戦略・停止条件
    - M2ゲート検証

  gate_criteria:
    - "証拠グレーディング精度 85%+"
    - "Support/Contrast分類動作"
    - "PRISMA SVG生成可能"
    - "スコア 102点以上"
```

### 3.3 Sprint 19-22: Phase 2完了 + Phase 3（Week 7-10）

```yaml
sprint_19:  # Week 7
  goal: "Active Learning UI・Phase 2仕上げ"
  tasks:
    - AL CLI統合
    - AL Web UI
    - 証拠グレード可視化
    - Phase 2統合テスト
    - Phase 2ドキュメント


sprint_20:  # Week 8
  goal: "プラグインシステム・外部連携"
  tasks:
    - プラグインインターフェース
    - プラグインローダー
    - サンプルプラグイン
    - Zotero APIクライアント
    - RIS/BibTeXインポート/エクスポート


sprint_21:  # Week 9
  goal: "ドキュメント完全整備"
  tasks:
    - APIリファレンス自動生成
    - ユーザーガイド
    - チュートリアル
    - トラブルシューティング
    - 日本語ドキュメント


sprint_22:  # Week 10
  goal: "配布パッケージング・M2.5ゲート"
  tasks:
    - PyPIパッケージ
    - Dockerイメージ最適化
    - ワンライナーインストール
    - プラグインドキュメント
    - Phase 2完了統合テスト

  gate_criteria:
    - "pip install jarvis-research 動作"
    - "docker run jarvis-research 動作"
    - "全差別化機能動作確認"
    - "スコア 112点以上"
```

### 3.4 Sprint 23-24: 最終統合・v1.0リリース（Week 11-12）

```yaml
sprint_23:  # Week 11
  goal: "パフォーマンス最適化"
  tasks:
    - プロファイリング・ボトルネック特定
    - LLM推論最適化
    - 埋め込み計算最適化
    - メモリ使用量削減
    - 並列処理強化
    - 負荷テスト


sprint_24:  # Week 12 - FINAL
  goal: "v1.0 リリース・120点達成"
  tasks:
    - 最終統合テスト
    - セキュリティ監査
    - リリースドキュメント
    - PyPI公開
    - Docker Hub公開
    - GitHub Release作成
    - M3ゲート・120点検証

  gate_criteria:
    - "全テスト通過"
    - "ドキュメント完備"
    - "PyPI公開完了"
    - "Docker公開完了"
    - "スコア 120点達成"
```

---

## 4. タスク詳細仕様

### 4.1 Task 1.2: ローカル埋め込み

```yaml
task_1_2_1:
  name: "Sentence Transformers専用モジュール"
  priority: P0
  effort: "8h"
  
  class_design:
    SentenceTransformerEmbedding:
      attributes:
        - model_name: str
        - device: str  # cpu, cuda, mps
        - batch_size: int
      methods:
        - encode(texts) -> np.ndarray
        - dimension() -> int
        - is_available() -> bool
  
  recommended_models:
    general: "all-MiniLM-L6-v2"
    scientific: "allenai/specter2"


task_1_2_2:
  name: "BM25スパース埋め込み"
  priority: P0
  effort: "6h"
  
  class_design:
    BM25Index:
      methods:
        - build(corpus) -> None
        - search(query, top_k) -> List[Tuple[int, float]]
        - save(path) -> None
        - load(path) -> BM25Index


task_1_2_3:
  name: "ハイブリッド検索"
  priority: P0
  effort: "8h"
  
  class_design:
    HybridSearch:
      attributes:
        - dense_model: SentenceTransformerEmbedding
        - sparse_index: BM25Index
        - fusion_method: str  # "rrf" or "linear"
      methods:
        - index(corpus, ids) -> None
        - search(query, top_k) -> List[SearchResult]
```

### 4.2 Task 1.5: オフラインモード

```yaml
task_1_5_1:
  name: "ネットワーク状態検出"
  priority: P0
  
  class_design:
    NetworkDetector:
      methods:
        - is_online() -> bool
        - check_endpoint(url) -> bool
        - get_status() -> NetworkStatus


task_1_5_3:
  name: "CLIオフラインオプション"
  priority: P0
  
  new_options:
    run:
      - "--offline": "オフラインモードで実行"
      - "--no-network": "ネットワーク通信を完全無効化"
      - "--local-llm": "ローカルLLMバックエンド指定"


task_1_5_5:
  name: "同期キュー実装"
  priority: P1
  
  class_design:
    SyncQueue:
      storage: "SQLite"
      methods:
        - enqueue(item) -> str
        - dequeue() -> Optional[SyncItem]
        - mark_complete(item_id) -> None
        - stats() -> QueueStats
```

### 4.3 Task 2.1: 証拠グレーディング

```yaml
task_2_1:
  name: "証拠グレーディングシステム"
  total_effort: "40h"
  
  schema:
    EvidenceLevel:
      LEVEL_1A: "系統的レビュー（均質なRCT）"
      LEVEL_1B: "個別のRCT"
      LEVEL_2A: "系統的レビュー（均質なコホート）"
      LEVEL_2B: "個別のコホート研究"
      LEVEL_3A: "系統的レビュー（症例対照）"
      LEVEL_3B: "個別の症例対照研究"
      LEVEL_4: "症例シリーズ"
      LEVEL_5: "専門家意見"
  
  ensemble_strategies:
    weighted_average:
      rule_weight: 0.4
      llm_weight: 0.6
    voting:
      require_agreement: true
    confidence_based:
      threshold: 0.8
```

---

## 5. ファイル作成計画

### 5.1 新規作成ファイル一覧

```yaml
phase_1_files:  # 25 files
  jarvis_core/embeddings/:
    - __init__.py
    - sentence_transformer.py
    - bm25.py
    - hybrid.py
  
  jarvis_core/network/:
    - __init__.py
    - detector.py
  
  jarvis_core/sync/:
    - __init__.py
    - queue.py
    - worker.py
    - reconciler.py
  
  jarvis_core/sources/:
    - arxiv_client.py
    - crossref_client.py
    - unpaywall_client.py

phase_2_files:  # 35 files
  jarvis_core/evidence/:
    - __init__.py
    - schema.py
    - rule_classifier.py
    - llm_classifier.py
    - ensemble.py
  
  jarvis_core/citation/:
    - __init__.py
    - context_extractor.py
    - stance_classifier.py
    - graph.py
  
  jarvis_core/contradiction/:
    - __init__.py
    - normalizer.py
    - detector.py
  
  jarvis_core/prisma/:
    - __init__.py
    - model.py
    - flowchart.py
    - export.py
  
  jarvis_core/al/:
    - __init__.py
    - engine.py
    - classifier.py
    - query_strategy.py

phase_3_files:  # 30 files
  jarvis_core/plugins/:
    - interface.py
    - loader.py
    - registry.py
  
  jarvis_core/integrations/:
    - zotero.py
    - sync_manager.py
  
  docs/:
    - guides/*.md
    - tutorials/*.md
    - troubleshooting/*.md
```

---

## 6. テスト計画

### 6.1 テストカバレッジ目標

```yaml
coverage_targets:
  overall: 85%
  
  by_module:
    jarvis_core/llm/: 90%
    jarvis_core/embeddings/: 90%
    jarvis_core/sources/: 85%
    jarvis_core/evidence/: 85%
    jarvis_core/citation/: 85%
```

### 6.2 Golden Test Sets

```yaml
golden_sets:
  evidence_grading:
    file: "tests/fixtures/evidence_golden.jsonl"
    size: 100
    accuracy_target: 85%
  
  citation_stance:
    file: "tests/fixtures/citation_golden.jsonl"
    size: 200
    accuracy_target: 80%
  
  contradiction:
    file: "tests/fixtures/contradiction_golden.jsonl"
    size: 50
    accuracy_target: 75%
```

---

## 7. 品質ゲート

### 7.1 マイルストーンゲート

```yaml
milestone_gates:
  M1_5:
    name: "Phase 1完了"
    criteria:
      - "jarvis run --offline --goal 'test' 成功"
      - "8種無料API動作確認"
      - "ハイブリッド検索F1 > 0.75"
      - "テストカバレッジ 80%+"
      - "スコア 92点以上"
  
  M2:
    name: "差別化機能MVP"
    criteria:
      - "証拠グレーディング精度 85%+"
      - "Support/Contrast分類動作"
      - "PRISMA SVG出力可能"
      - "スコア 102点以上"
  
  M2_5:
    name: "Phase 2完了"
    criteria:
      - "全差別化機能動作"
      - "pip install jarvis-research 成功"
      - "スコア 112点以上"
  
  M3:
    name: "v1.0リリース"
    criteria:
      - "全テスト通過"
      - "ドキュメント完備"
      - "PyPI/Docker公開"
      - "スコア 120点達成"
```

---

## 8. リスクと対策

### 8.1 リスクマトリックス

```yaml
risks:
  high_probability_high_impact:
    - id: R1
      name: "ローカルLLM精度不足"
      mitigation:
        - 複数モデル比較テスト
        - プロンプト最適化
        - フォールバックチェーン
      contingency:
        - Groq無料枠をフォールバックに
    
    - id: R2
      name: "開発遅延"
      mitigation:
        - 週次進捗確認
        - バッファ期間確保
      contingency:
        - Phase 3の一部を次バージョンへ
```

---

## 9. Skills連携フロー

### 9.1 Sprint内作業フロー

```
Day 1 (月): [JOURNAL] → [BRAIN] → [SPEC] → [WORKTREE]
Day 2-4:   [ORCH(TDD)] → [VERIFY] → [JOURNAL]
Day 5 (金): [REVIEW] → [VERIFY] → [FINISH] → [JOURNAL]
```

### 9.2 タスク種別ごとのパターン

```yaml
skill_patterns:
  new_module:
    flow: "BRAIN → SPEC → WORKTREE → ORCH(TDD) → VERIFY → REVIEW → FINISH"
  
  feature_addition:
    flow: "SPEC → WORKTREE → ORCH(TDD) → VERIFY → REVIEW → FINISH"
  
  bug_fix:
    flow: "DBG → TDD → VERIFY → REVIEW → FINISH"
```

---

## 10. 完了判定基準

### 10.1 v1.0 リリース判定基準

```yaml
release_criteria:
  mandatory:
    - "全テスト通過"
    - "テストカバレッジ 85%+"
    - "型チェック: mypy 0 errors"
    - "オフラインモード動作"
    - "証拠グレーディング精度 85%+"
    - "ドキュメント完備"
    - "PyPI/Docker公開"
    - "スコア 120点以上"
```

### 10.2 120点達成の内訳

```yaml
score_breakdown:
  current: 875  # 87.5点
  target: 1200  # 120点
  gap: 325
  
  improvement_plan:
    code_quality: "+17点"
    functionality: "+25点"
    offline_support: "+37点"
    differentiation: "+40点"
    ecosystem: "+32点"
    bonus: "+127点"
```

---

## 付録

### A. 環境変数一覧

```yaml
environment_variables:
  OLLAMA_BASE_URL: "http://127.0.0.1:11434"
  OLLAMA_MODEL: "llama3.2"
  JARVIS_OFFLINE: "false"
  JARVIS_LOCAL_FIRST: "true"
  JARVIS_CACHE_DIR: "~/.jarvis/cache"
```

### B. コマンドリファレンス（完成版）

```bash
# 基本実行
jarvis run --goal "CD73 immunotherapy survey"
jarvis run --offline --goal "test query"

# モデル管理
jarvis model list
jarvis model pull llama3.2

# キャッシュ管理
jarvis cache stats
jarvis cache clear

# Active Learning
jarvis screen --input papers.jsonl --output screened.jsonl

# 外部連携
jarvis import --format ris --input refs.ris
jarvis export --format bibtex --output refs.bib
```

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|------------|----------|
| 2026-01-06 | 3.0.0 | 初版作成（47.2%→100%計画） |

---

**作成者**: antigravity  
**計画書終了**
