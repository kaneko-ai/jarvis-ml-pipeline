---
name: spec
description: 実装前に2–5分粒度の手順へ分解。正確なパス/コマンド/期待出力を確定する
---

# SPEC

## 目的
- "誰でも実行できる"最小・明確な実装計画

## トリガ
- BRAIN合意後/改修の前

## 要件
- 各タスクは2–5分
- 正確なパス・行範囲・完全なスニペット
- コマンドと期待出力
- TDD前提（see [TDD]）

## 構成
- Goal/Arch/Stack（各1–3行）
- Task N: Files/Steps/Verify/Commit
- リスク/代替/中止条件（短文）

## 出力
- docs/plans/YYYY-MM-DD-<topic>.md

## 参照
- [ORCH](ORCH.md)
- [WORKTREE](WORKTREE.md)
- [VERIFY](VERIFY.md)
- [TOKEN](TOKEN.md)
