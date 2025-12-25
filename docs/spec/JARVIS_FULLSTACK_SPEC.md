# JARVIS Deep Learning Full-Stack Integration 仕様書
# Version: 1.0.0
# Status: Active

## 0. 目的（非交渉のゴール）

1. 再現可能な文献探索〜要約〜比較評価〜設計提案を、同一入力で同一出力（または差分が説明可能）にする
2. すべての要約・評価・提案に **根拠（原文の箇所、図表、段落）**を紐づける
3. 依存関係（torch等）を本体から隔離し、プラグイン単位で導入・無効化可能にする
4. CIで品質ゲートに落ちたらマージ不可（曖昧な「動いた」は禁止）

---

## 1. アーキテクチャ方針

### 1.1 「本体」と「モデル」を分離

- **Jarvis本体**: オーケストレーション、設定、ログ、キャッシュ、評価、UI
- **深層学習**: `plugins/` 配下に隔離（モデルごとに独立パッケージ）

### 1.2 全機能は「パイプライン契約」で統一

全モジュールは共通I/O契約を守る:

**共通入力:**
- TaskContext: goal, domain, constraints, seed, timestamp, run_id
- Artifacts: papers, chunks, embeddings, claims, evidence_links, scores, graphs, designs
- Runtime: cpu/gpu, device_map, batch, timeout, cache_policy

**共通出力:**
- ResultBundle: outputs + provenance（根拠）+ metrics + logs + diffs

### 1.3 すべての出力に Provenance（根拠）を強制

- 文章出力には、必ず `evidence_links[]` を付与
- `evidence_links` は原文の断片（doc_id, section, paragraph_id, char_span）を指すこと
- 根拠が取れない場合は「不明」と明示し、スコアを下げる（捏造禁止）

---

## 2. ディレクトリ構造

```
jarvis_core/
  contracts/          # I/O契約、型、スキーマ
  runtime/            # device, batch, timeout, cache
  provenance/         # 根拠付けユーティリティ
  evaluation/         # 品質ゲート・メトリクス
  pipelines/          # 統一パイプライン定義
  storage/            # cache, artifact store
  supervisor/         # Lyra Supervisor Layer

plugins/
  retrieval_st/       # SentenceTransformer embedder
  rerank_ce/          # CrossEncoder rerank
  extractor_claims/   # claim/evidence extractor
  summarizer/         # summarizer plugin
  scorer_confidence/  # claim confidence scorer
  scorer_roi/         # learning ROI scorer
  knowledge_graph/    # KG/GraphRAG plugin
  design_assistant/   # experiment design plugin

configs/
  profiles/           # cpu-only / gpu / hybrid
  pipelines/          # pipeline構成YAML
  plugins/            # plugin有効化YAML

tests/
  contract/           # 契約テスト
  integration/        # 統合テスト
  golden/             # ゴールデンテスト
```

---

## 3. Lyra Supervisor Integration

### 3.1 役割定義

Lyra is the Prompt & Reasoning Supervisor for JARVIS Research OS.
- Lyra does NOT implement features
- Lyra audits, optimizes, and reissues instructions to worker AIs

### 3.2 Lyraの責務

**DECONSTRUCT:** 核心目的、暗黙の前提、曖昧な判断点を抽出
**DIAGNOSE:** 仕様とのズレ、根拠欠如、曖昧性をチェック
**DEVELOP:** 再指示プロンプトを生成（期待出力/禁止事項/成功条件/テスト観点）
**DELIVER:** 作業指示として配布

### 3.3 Lyraが拒否すべき実装

- 「とりあえず動く」実装
- 根拠なしの要約
- 評価指標なしのモデル追加
- 「あとで直す」前提のPR
- 仕様に書かれていない推測

---

## 4. 品質ゲート

| メトリクス | 閾値 |
|-----------|------|
| 根拠付与率 | ≥ 95% |
| 断言のうち根拠なし | 0件 |
| パイプライン完走率 | 100% |
| 再現性 (Top10一致率) | ≥ 90% |

---

## 5. Provenance仕様

```json
{
  "claim_id": "c-001",
  "claim_text": "...",
  "evidence": [
    {
      "doc_id": "pmid:123",
      "section": "Results",
      "chunk_id": "r-12",
      "start": 120,
      "end": 260,
      "confidence": 0.82
    }
  ]
}
```

---

## 6. 受け入れ基準

1. fullstack pipeline がエラーなく完走
2. 主要出力（要約・ランキング・設計提案）に根拠が紐付く
3. seed固定での再実行で大きく崩れない
4. CPU-only でも縮退運転として動く
5. 監査ログが run ごとに出て、意思決定の説明が可能
