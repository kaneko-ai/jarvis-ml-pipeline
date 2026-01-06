---
name: orch
description: タスクごとに新鮮サブエージェントで実装→仕様審査→品質審査の二段ゲートを回す
---

# ORCH (Orchestration)

## トリガ
- SPECがあり、同一セッションで実行

## 原則
- タスクごと新規エージェント
- 仕様適合レビュー→品質レビュー（順不同は禁止）
- ゲート: [TDD]→[VERIFY]→レビュー

## 手順
1) SPECからTodo化
2) 実装サブエージェント
3) 仕様レビュア（要件充足のみ判定）
4) 品質レビュア（設計/可読/安全/性能）
5) 失敗は局所修正→再審査

## 出力
- 各タスクの変更/検証ログ/判断

## 参照
- [PARA](PARA.md)
- [REVIEW](REVIEW.md)
- [VERIFY](VERIFY.md)
- [RECOVER](RECOVER.md)
