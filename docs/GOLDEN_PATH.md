> Authority: GATE (Level 3, Binding)

# JARVIS Golden Path

唯一の正しい実行方法。これ以外は禁止。

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

## 禁止事項

- ❌ main.py からの本番実行
- ❌ jarvis_core.app.run_task() の直接呼び出し（テスト以外）
- ❌ ログディレクトリの手動作成
- ❌ 成果物ファイルの手動編集

---

*JARVIS Golden Path - これ以外のやり方は存在しない*
