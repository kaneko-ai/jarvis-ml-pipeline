> Authority: REFERENCE (Level 4, Non-binding)

# JARVIS Guide (Simple)

JARVISを素早く動かすためのシンプルなガイド。

---

## Quickstart (CLI only)

```bash
# 1. 環境構築
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.lock
pip install -e .

# 2. 環境設定
cp .env.example .env
# .envを編集してAPIキーを設定

# 3. 実行
python jarvis_cli.py run --goal "CD73 immunotherapy survey"

# 4. 結果確認
python jarvis_cli.py show-run --run-id <run_id>
```

---

## 入口について

| 入口 | 用途 | 推奨 |
|------|------|------|
| `jarvis_cli.py` | 本番・運用 | ✅ 推奨 |
| `main.py` | デモ・開発 | ⚠️ デモのみ |

---

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `run --goal "..."` | タスク実行 |
| `show-run --run-id ID` | run結果表示 |
| `build-index --path DIR` | 索引構築 |

---

## 成果物

runが成功すると `logs/runs/{run_id}/` に以下が生成されます：

- `result.json` - 実行結果
- `eval_summary.json` - 評価結果
- `papers.jsonl` - 論文メタ
- `claims.jsonl` - 主張
- `evidence.jsonl` - 根拠
- `report.md` - レポート

詳細: [BUNDLE_CONTRACT.md](BUNDLE_CONTRACT.md)
