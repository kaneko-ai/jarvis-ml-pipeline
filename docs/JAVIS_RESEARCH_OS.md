# JARVIS Research OS 設計ドキュメント

## 概要

Javis は **Research OS（Research Operating System）** として、以下を運用可能な形で回す:

1. 情報収集
2. 評価
3. 記憶
4. 改善提案
5. 疑似自己進化

---

## 思想的定義

### Javisは何か

- **Research OS**: 論文・技術・実装・作業ログを統合的に扱う
- **Human-in-the-loop前提**: 自動化は「提案」まで
- **疑似自己進化**: 情報収集 → 評価 → 改善提案 → 採否ログ化

### Javisは何ではないか

- 「論文を自動で読み、勝手に賢くなるAI」ではない
- 人間の研究判断を、記憶し、再利用し、改善提案を洗練させるOS

---

## アーキテクチャ

```
[External Sources]
   |  (arXiv / PubMed / Zenn / DAIR / alphaXiv)
   v
[Connectors] → [Normalizer] → [Dedupe]
   v
[Trend / Paper Pool]
   v
[Ranker (Rule → LTR)]
   v
[Evaluator (Multi-Judge + Counterfactual)]
   v
[Issues with DoD]
   v
[Human Decision]
   v
[Memory (Hindsight)]
   v
[Next Iteration]
```

---

## 主要モジュール

### 1. Provider Switch (`jarvis_core/providers/`)

API / Local / Hybrid 切替の抽象化。

```yaml
runtime:
  llm_provider: api        # api | local
  embed_provider: local    # api | local
local:
  llm:
    backend: ollama
    model: qwen2.5
```

### 2. Trend Watcher (`jarvis_core/trend/`)

論文・技術トレンドの定期収集。

- **ソース**: arXiv, PubMed, Zenn, DAIR.AI
- **出力**: 週次トレンドレポート, 改善Issue

### 3. BibTeX Fetcher (`jarvis_core/bibtex/`)

全件自動取得: arXiv / DOI / Crossref / PubMed

### 4. Hindsight Memory (`jarvis_core/memory/`)

| タイプ | 説明 |
|-------|------|
| **World** | 検証済み事実（evidence必須） |
| **Experience** | 実行・失敗・手動判断 |
| **Observation** | 未検証メモ |
| **Opinion** | 好み・仮説（隔離） |

**禁止**: Opinion が World に混入すること

### 5. Multi-Judge Evaluator (`jarvis_core/evaluation/multi_judge.py`)

| Judge | 役割 |
|-------|------|
| 厳格査読者 | 学術的正確性 |
| 実務PM | 実用性・コスト |
| 反証役 | 反例・弱点 |

**失格条件**: 根拠なき断言、出典不明、再現性なし

---

## 絶対ルール

### PDF取得

| 状況 | 可否 |
|------|------|
| arXiv | ✅ 自動取得可 |
| PMC OA | ✅ 自動取得可 |
| Unpaywall OA | ✅ 自動取得可 |
| 有料購読VPN経由 | ❌ **禁止** |
| 大量DL | ❌ **禁止** |
| 非OA | メタデータ+要旨まで |

### API遵守

- PubMed API レート遵守
- TDMが必要なら図書館に正式相談

---

## 将来導入予定

- ultrascale-playbook
- 分子探索 × 獲得関数
- Layered-GGUF（ローカル画像）
- Screenpipe（作業ログ知識化）
