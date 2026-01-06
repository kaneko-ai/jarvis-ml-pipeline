---
name: finish
description: テスト確認→統合方針提示（Merge/PR/保持/破棄）→実行→清掃。必要に応じ軽量Changelog
---

# FINISH

## 手順
1) 全テスト[VERIFY]
2) ベースブランチ確認
3) 選択肢提示
   - Merge locally / Create PR / Keep / Discard
4) 選択を実行
5) worktree/枝の掃除

## オプション
- 直近コミットから軽量Changelog生成

## 参照
- [REVIEW](REVIEW.md)
- [VERIFY](VERIFY.md)
- [WORKTREE](WORKTREE.md)
