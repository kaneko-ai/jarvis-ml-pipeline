# API キー管理・バックアップガイド

このドキュメントは JARVIS Research OS の運用者（kaneko yu）向けの内部ガイドです。

## 1. API キー管理

### 保管場所
- API キーは `.env` ファイルに保存する（Git 追跡対象外）
- `.env` は `.gitignore` に含まれており、GitHub には絶対にアップロードされない

### 現在使用中の API キー

| 変数名 | 用途 | 無料枠 |
|--------|------|--------|
| `GEMINI_API_KEY` | Gemini API（LLM 要約） | 1,500 req/日, 15 RPM |
| `ZOTERO_API_KEY` | Zotero Web API（文献管理）| 無制限（Week 3 で追加予定） |
| `ZOTERO_USER_ID` | Zotero ユーザー ID | —（Week 3 で追加予定） |

### キーのローテーション手順（3ヶ月に1回推奨）

**Gemini API キー:**
1. https://aistudio.google.com/app/apikey にアクセス
2. 既存キーを削除（「Delete API key」）
3. 新しいキーを生成（「Create API key」）
4. `.env` の `GEMINI_API_KEY` を新しいキーに更新
5. 動作確認: `python -m jarvis_cli search "test" --max 1 --no-summary`

**Zotero API キー（設定後）:**
1. https://www.zotero.org/settings/keys にアクセス
2. 既存キーを削除し新規作成
3. `.env` の `ZOTERO_API_KEY` を更新

### 漏洩時の対応
キーが漏洩した（または疑われる）場合は、即座に上記手順でローテーションを行うこと。

## 2. バックアップ

### 実行方法
```powershell
.\backup.ps1
