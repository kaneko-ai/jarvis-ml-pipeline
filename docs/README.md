> Authority: REFERENCE (Level 4, Non-binding)

# JARVIS Research OS Documentation

このリポジトリのドキュメントは、運用しやすさを優先して以下の 5 ファイルに集約しています。

## Canonical Docs (5 files)

1. `docs/README.md` (このファイル): 全体ガイド/運用メモ/評価仕様の要点
2. `docs/QUICKSTART.md`: セットアップと最短実行手順
3. `docs/API_REFERENCE.md`: CLI/SDK/Web API の参照
4. `docs/MASTER_SPEC.md`: 実装拘束の最上位仕様（Binding）
5. `docs/HUMAN_TASKS_PLAYBOOK_2026-02-12.md`: 人手タスクと実行履歴

## Landing Page & Demo API

- ランディングページ (`docs/index.html`) は静的ホスト前提
- Demo セクションは `API Base URL` を設定するとバックエンドAPI連携で動作
- API未接続時はブラウザ内 fallback ロジックで継続動作
- バックエンド想定エンドポイント:
  - `GET /api/demo/health`
  - `POST /api/demo/evidence/grade`
  - `POST /api/demo/citation/analyze`
  - `POST /api/demo/contradiction/detect`

## Evaluation Metrics Spec (condensed)

最低限の評価軸（契約チェック用の簡易版）:

- `evidence_coverage`
- `locator_rate`
- `provenance_rate`
- `citation_precision`
- `contract_compliance`
- `gate_pass_rate`

## State Baseline (condensed)

```yaml
core_test_collected: 6859
baseline_date: 2026-02-13
```

## Notes

- 詳細は上記 Canonical Docs の各ファイルを参照
- 追加ドキュメントを作る場合は、原則としてこの5ファイルへ統合して拡張する
