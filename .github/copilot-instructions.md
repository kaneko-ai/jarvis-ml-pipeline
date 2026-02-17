# Copilot Instructions（jarvis-ml-pipeline）

## 1) 目的（非交渉）
- `RUNBOOK.md` を唯一の実行経路（One True Path）として厳守する。
- 「テストが通るだけのゴミコード」を禁止する。
- 変更は最小・局所に限定し、必ず根拠（ログ/テスト/再現手順）を残す。

## 2) 変更時の必須ゲート（手順固定）
- 変更前に現状のテスト/ビルド確認コマンドを実行し、基準状態を記録する。
- 変更後は次の順序を固定し、実行コマンドと結果を必ず貼付・記録する。
  1. `python -m pytest -q`（または妥当な指定テスト）
  2. `JARVIS_TEST_BLOCK_NETWORK=1` の unit gate（`network` / `integration` / `e2e` 除外）
- 外部API依存テストには `@pytest.mark.network` を付与し、デフォルトCIから除外する。

## 3) S2（semantic scholar）の運用ルール
- `429` / `5xx` / `timeout` は retry/backoff/jitter を適用し、`Retry-After` を尊重する。
- `400` / `401` / `403` / `404` は retry しない。
- 取得系はキャッシュ方針を厳守し、テストは mocked を原則とする。

## 4) 出力/成果物の契約
- `jarvis_cli.py papers tree` の out/run 成果物（`input.json`, `result.json`, `tree.md` 等）を破壊しない。
- `paperId` 正規化と空IDガードを維持し、`/paper//references` を再発させない。

## 5) PR/コミット規約（最小）
- 変更理由、影響範囲、検証コマンド、結果を必ず残す。
- 既存設計（`RUNBOOK`・CI 2-tier）に逆行する変更を禁止する。
