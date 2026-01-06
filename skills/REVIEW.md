---
name: review
description: 実装後に仕様適合とコード品質を標準化レビュー。SHA範囲と要件を必ず添付
---

# REVIEW

## いつ
- ORCH各タスク後/主要機能完了/マージ前

## 手順
1) BASE_SHA/HEAD_SHA取得
2) 何を作ったか/満たす要件を要約
3) レビュアへ渡す（仕様→品質の順）

## 扱い
- Criticalは即修正、Importantはマージ前、Minorはメモ

## 参照
- [ORCH](ORCH.md)
- [VERIFY](VERIFY.md)
- [FINISH](FINISH.md)
- [JOURNAL](JOURNAL.md)
