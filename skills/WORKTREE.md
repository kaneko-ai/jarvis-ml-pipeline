---
name: worktree
description: git worktreeで隔離ワークスペースを安全作成。ignore検証→作成→初期テスト
---

# WORKTREE

## 目的
- 同一repoで並行作業しつつ汚染回避

## 手順
1) .worktrees など既存/推奨dir確認
2) git check-ignoreで無視設定検証
   - 未設定なら.gitignore追加→コミット
3) 新ブランチでworktree作成
4) 依存インストール/初期テスト
5) 場所報告

## 注意
- 失敗テストのまま作業を進めない

## 参照
- [SPEC](SPEC.md)
- [VERIFY](VERIFY.md)
- [FINISH](FINISH.md)
