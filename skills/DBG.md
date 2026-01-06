---
name: dbg
description: 修正前に根因を確定。再現→差分→仮説→最小検証の4相で進める
---

# DBG (Systematic Debugging)

## 原則
- 根因未特定の修正は禁止

## 4相
1) 再現/ログ精読/直近変更確認
2) 動く例との比較で差分抽出
3) 単一仮説→単変量で検証
4) テスト化→単一修正→再検証

## 赤旗
- 「様子見パッチ」「たぶん動く」

## 参照
- [TDD](TDD.md)
- [VERIFY](VERIFY.md)
- [RECOVER](RECOVER.md)
