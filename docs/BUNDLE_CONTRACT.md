> Authority: CONTRACT (Level 3, Binding)
> Canonical: YES
> Purpose: 1 run が必ず生成する成果物の「最低保証」を固定し、監査可能性を担保する

# BUNDLE CONTRACT（成果物契約）v1

## 1. 定義
- “Run” とは、JARVISが1回の実行単位として入力（query/config）を受け取り、処理し、成果物を出力すること。
- 成功/失敗に関わらず、Runは監査可能でなければならない。

## 2. 保存先（固定）
- すべての成果物は `logs/runs/{run_id}/` に保存する。
- `{run_id}` は一意で、再実行時は別run_idを採番する（上書き禁止）。

## 3. 必須10ファイル（成功/失敗を問わず必須）
以下10ファイルは欠損してはならない。欠損はシステムエラー。

1) `run.json`
- run_id, timestamps, status, gate_passed, input_summary, toolchain_versions

2) `config_snapshot.yaml`
- 実行に使った設定（YAML）。後で同条件再実行できること。

3) `sources.jsonl`
- 取得した文献・URL・IDの一覧（最低限：id, title, year, source, retrieval_time）

4) `claims.jsonl`
- 抽出された主張（最低限：claim_id, text, paper_id, confidence）

5) `evidence.jsonl`
- 根拠（最低限：evidence_id, claim_id, paper_id, locator, quote_or_span, strength）

6) `scores.json`
- 文献スコア（最低限：paper_id → score と feature）

7) `contradictions.jsonl`
- 矛盾候補（最低限：pair_id, claim_a, claim_b, type, rationale）

8) `prisma.json`
- PRISMAの集計（最低限：identified, screened, included, excluded_reasons）

9) `report.md`
- 人間が読める最終レポート（必ず引用・根拠リンクを含む）

10) `audit.json`
- ゲート結果（fail_reasons含む）、根拠カバレッジ、検証結果

## 4. 追加成果物（任意）
- 可視化、HTML、図表等は `logs/runs/{run_id}/artifacts/` に置く。
- ただし「必須10ファイル」を侵食してはならない。

## 5. 成功判定（絶対条件）
- `status == "success" ⇔ gate_passed == true`
- gate_passed が false の run は成功と主張してはならない。

## 6. 互換性
- 将来ファイルを追加することは可。
- 既存10ファイルの削除・意味変更は破壊的変更であり、docs/DECISIONS.md に理由と移行策を記録すること。

## 7. 禁止
- “後で作る” を理由に必須10ファイルを欠損させること
- 根拠ロケータ無しの evidence（locator が空）
