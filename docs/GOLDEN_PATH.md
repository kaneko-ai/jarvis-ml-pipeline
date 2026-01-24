# JARVIS Golden Path (v1.2)

> Authority: REFERENCE (Level 2, Non-binding)


> Authority: DEC-006, MASTER_SPEC v1.2

唯一の正しい実行方法。これ以外は「開発用」または「非推奨」。

---

## 1. 実行 (Production / E2E)

```bash
# 基本実行 (Golden Pipeline)
# 必ず e2e_oa10.yml を使用すること（Phase 1完了時点の標準）
python jarvis_cli.py run --goal "your research question" --pipeline configs/pipelines/e2e_oa10.yml

# オフライン実行 (動作確認用)
python jarvis_cli.py run --goal "test" --pipeline configs/pipelines/e2e_offline.yml
```

> **Note**: `--pipeline` を省略した場合もデフォルトで `e2e_oa10.yml` が使用されるが、明示推奨。

---

## 2. 成果物の場所 (10ファイル契約)

すべてのRunは以下のディレクトリに**必ず10ファイル**を生成する。

```
logs/runs/{run_id}/
├── input.json
├── run_config.json
├── papers.jsonl
├── claims.jsonl
├── evidence.jsonl
├── scores.json
├── result.json
├── eval_summary.json
├── warnings.jsonl
└── report.md
```

欠損がある場合、そのRunは `Contract Violation` で失敗扱いとなる。

---

## 3. 結果確認

```bash
# 最新runの確認（fail理由・欠損ファイルも表示）
python jarvis_cli.py show-run

# 特定runの確認
python jarvis_cli.py show-run --run-id {run_id}
```

### 判定基準
- **Success**: `status: success` AND `gate_passed: true` AND `contract_valid: true`
- **Failed**: 上記以外

---

## 4. 品質保証 (Quality Gate)

以下の項目が1つでもNGなら `Failed` となる。

| 項目 | 基準 |
|------|------|
| Provenance Rate | 95%以上 (文単位の根拠) |
| Facts w/o Evidence | 0件 |
| Artifacts | 10ファイル完備 |

---

## 非推奨事項

- ❌ `main.py` からの本番実行（あれはデモ用）
- ❌ `python run_pipeline.py` の使用（旧実装）
- ❌ `jarvis_core.app` を直接importして実行（CLI経由のみ許可）
- ❌ `artifacts/` ディレクトリへの出力（`logs/runs/` に統一済み）

---

*JARVIS Golden Path - v1.2*

唯一の正しい実行方法。これ以外は非推奨。

---

## 1. CLI最小実行

```bash
# 最小実行コマンド
python jarvis_cli.py run --goal "your research question"

# JSON出力
python jarvis_cli.py run --goal "your research question" --json

# タスクファイルから実行
python jarvis_cli.py run --task-file task.json
```

---

## 2. 成果物の場所

```
logs/runs/{run_id}/
├── run_config.json    # 実行設定
├── result.json        # 実行結果
├── eval_summary.json  # 評価結果（gate_passed含む）
└── events.jsonl       # 監査ログ
```

---

## 3. 成功/失敗の判定

### 成功 (success)
```json
{
  "status": "success",
  "gate_passed": true
}
```

### 失敗 (failed)
```json
{
  "status": "failed",
  "gate_passed": false,
  "fail_reasons": [
    {"code": "CITATION_MISSING", "msg": "..."}
  ]
}
```

---

## 4. 結果確認

```bash
# 最新runの確認
python jarvis_cli.py show-run

# 特定runの確認
python jarvis_cli.py show-run --run-id {run_id}

# JSON出力
python jarvis_cli.py show-run --json
```

---

## 非推奨事項

- ❌ main.py からの本番実行
- ❌ jarvis_core.app.run_task() の直接呼び出し（テスト以外）
- ❌ ログディレクトリの手動作成
- ❌ 成果物ファイルの手動編集

---

*JARVIS Golden Path - これ以外のやり方は存在避ける*
