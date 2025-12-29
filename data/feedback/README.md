# Feedback Intelligence (P8)

このフォルダは、過去指摘の履歴とリスクモデル設定を管理します。

## ファイル

- `history.jsonl`: 指摘履歴（`jarvis_core/feedback/schema.py` の正規スキーマに準拠）
- `risk_model.yaml`: ルール重み・閾値の設定

## 運用フロー

1. 先生の指摘メールやコメントを `collector.parse_text` に貼り付ける
2. 生成されたエントリを確認・修正する（UIまたは手動）
3. `history.jsonl` に追記する

```python
from jarvis_core.feedback.collector import FeedbackCollector

collector = FeedbackCollector()
entries = collector.parse_text(raw_text, reviewer="kato_prof")
collector.save_entries(entries)
```

## リスク推定

- `risk_model.yaml` の重みを調整して、指摘確率と説明理由を改善できます。
- ブラックボックスモデルは禁止。理由は `reasons` に必ず表示します。
