---
name: webtest
description: Playwrightでnetworkidle待機→DOM偵察→操作の順にWebを検証
---

# WEBTEST

## 決まり
- 動的アプリは networkidle 待機が必須

## 手順
1) サーバ起動（必要なら scripts/with_server.py）
2) page.wait_for_load_state('networkidle')
3) スクリーンショット/DOM観察→セレクタ確定
4) アクション→期待結果検証

## 出力
- 再現性あるテストスクリプトとログ

## 参照
- [VERIFY](VERIFY.md)
- [SPEC](SPEC.md)
- [RECOVER](RECOVER.md)
