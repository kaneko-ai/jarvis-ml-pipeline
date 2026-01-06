---
name: env
description: antigravity/codex環境を検出し、パス/ポート/起動方法を分岐。未確定は質問
---

# ENV

## 目的
- 実行環境差異を吸収し、設定の決め打ちを避ける

## 検出例
- 環境変数/既知の作業ディレクトリ/ポートの占有
- ツール存在確認（node/python/git 等）

## 手順
1) 既知フラグの読取
2) 典型パス/ポートの提示（選択肢）
3) 不明点は1問1答で確定
4) 設定を[JOURNAL]へ保存

## 参照
- [WORKTREE](WORKTREE.md)
- [TOKEN](TOKEN.md)
- [RECOVER](RECOVER.md)
