# JARVIS Secrets & Security Policy (Phase 11)

## 概要
JARVIS プロジェクトにおける秘密情報の実装・管理、および禁止事項について定義します。

## 1. 秘密情報の定義
以下の情報は「秘密情報」として扱い、コードやログに直接含めてはなりません。
- API キー (NCBI, OpenAI, Google, etc)
- OAuth トークン, GitHub トークン
- パスワード, 秘密鍵
- ユーザーの個人情報 (PII)

## 2. 管理ルール
- すべての秘密情報は環境変数 (`.env` ファイルまたは CI Secrets) を通じて取得してください。
- `jarvis_core/settings.py` を唯一のアクセスポイントとし、検証ロジックを含めてください。
- サンプルファイル (`.env.example`) にはダミー値を記載し、本物の値を含めないでください。

## 3. ログの秘匿化 (Masking)
- 秘密情報を含む可能性のある変数をログ出力する際は、必ず `jarvis_core.security.redaction` を使用してマスキングを行ってください。
- 例: `logger.info(f"Using key: {redact(api_key)}")`

## 4. 禁止関数・パターン
以下の使用は、セキュリティゲートにおいて警告または拒否の対象となります。
- `eval()`, `exec()` の安全でない使用
- 文字列連結による SQL/Shell コマンド構築 (SQL Injection / Command Injection 対策)
- `requests.get(url, verify=False)` (SSL 検証の無効化)

## 5. 監査プロセス
- `scripts/security_gate.py` が PR ごとに実行されます。
- `bandit` による静的解析を実施します。
- `pip-audit` による依存関係の脆弱性診断を実施します。
