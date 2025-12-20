# Jarvis Vision（正本）
Last Updated: 2025-12-20

このファイルは本リポジトリにおける **Jarvis（javis）の正本（Master）** である。  
設計・仕様・運用ルールの「正」は必ずここに集約する（他docsは補助）。

---

## 1. システム全体像（レイヤ構造）

Jarvis 全体のレイヤ構造は以下の通りとする。

```text
[UI層]
  ChatGPT / MyGPT / antigravity / 将来Dashboard

        ↓（自然言語 + 最小メタ）

[Jarvis Core（このrepoの担当範囲）]
  Planner（分解）
    → Router / Registry（呼び分け）
      → Execution（実行管理）
        → Validation / Retry（自己評価と再試行）
          → Logging / Progress（追跡可能性）

        ↓（疎結合）

[Tools/Services層（別repo/別モジュール可）]
  paper_pipeline（PubMed/PMC取得・抽出・索引）
  retrieval（keyword+vector+rerank）
  mygpt-paper-analyzer（Next.js+FastAPI+FAISS 等）
  OCR / 図抽出 / ES支援 / ニュース監視 など

        ↓

[データ層]
  PDF / メタデータ（BibTeX・citation）
  チャンク / 索引 / ベクトルDB（FAISS等）
  Obsidian Vault（ノート・要約）
  GitHub（コード・設定）
