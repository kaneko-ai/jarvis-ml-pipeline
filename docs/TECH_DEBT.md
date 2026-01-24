# Technical Debt Registry

> Authority: REFERENCE (Level 2, Non-binding)


現在の既知の技術負債と修正計画。

## カテゴリ

| カテゴリ | 説明 |
|---------|------|
| A | 環境依存（PDF抽出/ファイルパス/OS差） |
| B | ネットワーク依存（外部API） |
| C | モック不備（fixture壊れ） |
| D | 実装バグ（修正可能） |
| E | テストが古い（仕様不整合） |

---

## 既知の失敗テスト

| テスト | カテゴリ | 再現条件 | 想定原因 | 修正方針 | 機会費用 |
|--------|----------|----------|----------|----------|----------|
| `test_pdf_extractor.py::*` | A | Windows環境 | pymupdf FileDateError | PDF削除/mock化 | PDF抽出の回帰検出不可 |
| `test_web_fetcher.py::*` | B | ネットワーク無 | 外部URL fetch | VCR/mock化 | URL取得の回帰検出不可 |
| `test_planner.py::*` | C | - | mock不一致 | fixture更新 | プランナー回帰検出不可 |
| `test_retry_policy.py::*` | C | - | 古いAPI | テスト更新 | リトライ回帰検出不可 |
| `test_quality_gate.py::*` | C | - | 古いスキーマ | テスト更新 | 品質ゲート回帰検出不可 |
| `test_reference.py::*` | C | - | mock不一致 | fixture更新 | 参照解決の回帰検出不可 |
| `test_execution_engine_retry.py::*` | C | - | API変更 | テスト更新 | 実行エンジン回帰検出不可 |
| `test_executor.py::*` | C | - | API変更 | テスト更新 | Executor回帰検出不可 |

---

## CI構成

### Blocking (PRで必要)
- `pytest -m "not legacy"` or 明示的リスト
- コアテスト: `test_v4*.py`, `test_telemetry*.py`, `test_rp*.py`
- 回帰テスト: `eval_regression.yml`

### Non-blocking (結果表示のみ)
- legacy/環境依存テスト
- ネットワーク依存テスト

---

## 修正優先度

1. **高**: カテゴリD（実装バグ）- 即座に修正
2. **中**: カテゴリC（モック不備）- fixture更新で対応
3. **低**: カテゴリA/B（環境依存）- 長期的にmock化

---

## Phase 1 残存負債 (2024-12-27)

### 構造的二重性 (Structural Duplication)
以下の旧実装は **Deprecated (非推奨)** であり、将来的に削除される。

| 対象 | 代替（Golden Path） | 扱い |
|------|--------------------|------|
| `main.py` | `jarvis_cli.py` run | デモ専用として残存（本番非推奨） |
| `run_pipeline.py` | `jarvis_cli.py` run | **使用非推奨**（CI/CDからも削除済み） |
| `jarvis_core.app` (旧) | `jarvis_core.pipelines.executor` | 互換性維持のため残存するが非推奨 |
| `artifacts/` ディレクトリ | `logs/runs/{run_id}/` | **廃止**（10ファイル契約に違反） |

### 今後の方針
- 新規コードはすべて `jarvis_cli.py` および `pipelines` モジュールを使用する。
- 旧実装への依存は `docs/TECH_DEBT.md` に記載し、段階的に解消する。

---

*Last updated: 2024-12-27*
