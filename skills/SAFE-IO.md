---
name: safe-io
description: 冪等・安全なファイルI/O。テンポラリ→アトミック置換→ロールバック
---

# SAFE-IO

## 手順
1) 書込は path.tmp へ
2) 検証（lint/test/hash/サイズ）
3) mv path.tmp path（アトミック）
4) バックアップと復旧手順を記録

## 原則
- 競合回避/ロック検討
- 追記はジャーナル化、上書きは差分

## 参照
- [VERIFY](VERIFY.md)
- [JOURNAL](JOURNAL.md)
- [RECOVER](RECOVER.md)
