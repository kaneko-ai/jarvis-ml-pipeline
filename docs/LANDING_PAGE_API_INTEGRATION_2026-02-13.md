> Authority: GUIDE (Level 3, Non-binding)

# Landing Page API Integration Summary (2026-02-13)

## Scope
- Static landing page (`docs/index.html`) からバックエンドAPIを呼び出せる構成を追加
- API接続不可のときは既存ブラウザ内ロジックへ自動で戻る動作を維持
- 変更内容と検証結果を文書化

## Implemented
### Backend
- 新規ルーター: `jarvis_web/routes/demo.py`
- 追加エンドポイント:
  - `GET /api/demo/health`
  - `POST /api/demo/evidence/grade`
  - `POST /api/demo/citation/analyze`
  - `POST /api/demo/contradiction/detect`
- `jarvis_web/app.py` で `demo_router` を登録

### Frontend
- 新規設定ファイル: `docs/config.js`
  - `window.JARVIS_SITE_CONFIG.apiBaseUrl` を外部API接続先として利用
- `docs/index.html`
  - Demoセクションに API Base URL 入力UI と接続状態表示を追加
  - `config.js` を `script.js` より先に読み込むよう更新
- `docs/script.js`
  - API接続処理（timeout付き fetch）を追加
  - 3つのデモ関数を API 優先 + fallback 方式へ変更
  - 接続状態バッジ（online/testing/offline/mock）更新処理を追加
- `docs/styles.css`
  - API設定パネルと接続状態バッジのスタイルを追加
  - `output-status` に `fallback` / `error` 表示を追加

## API Request/Response Shape
### Evidence
- Request:
  - `title`, `abstract`, `full_text` (任意)
- Response `data`:
  - `level`, `description`, `confidence`, `quality_rating`, `classifier_source`, `source`

### Citation
- Request:
  - `text`, `paper_id` (任意)
- Response `data`:
  - `citations[]` (`id`, `author`, `year`, `stance`, `context`, `confidence`, `evidence`)
  - `summary` (`total`, `support`, `contrast`, `mention`)
  - `source`

### Contradiction
- Request:
  - `claim_a`, `claim_b`
- Response `data`:
  - `isContradictory`, `confidence`, `contradictionType`, `explanation`, `claimA`, `claimB`, `source`

## Operation Notes
- GitHub Pagesで利用する場合:
  - Demoセクションの `API Base URL` にバックエンドURLを入力
  - `Save` で `localStorage` に保存
  - `Test` で接続確認
- API未設定または接続不可の場合:
  - デモは fallback ロジックで継続動作

## Validation
- 追加テスト:
  - `tests/test_demo_api.py`
- 実行結果:
  - `python tools/spec_lint.py --paths docs/HUMAN_TASKS_PLAYBOOK_2026-02-12.md docs/LANDING_PAGE_DEPLOYMENT.md docs/LANDING_PAGE_API_INTEGRATION_2026-02-13.md` -> PASS
  - `uv run ruff check jarvis_core tests` -> PASS
  - `uv run black --check jarvis_core tests` -> PASS
  - `uv run mypy --explicit-package-bases --follow-imports=skip jarvis_core/evidence/ jarvis_core/contradiction/ jarvis_core/citation/ jarvis_core/sources/ --ignore-missing-imports` -> PASS
  - `uv run pytest -q` -> `6392 passed, 468 skipped`
  - `uv build` -> PASS

## Changed Files
- `jarvis_web/routes/demo.py`
- `jarvis_web/app.py`
- `tests/test_demo_api.py`
- `docs/config.js`
- `docs/index.html`
- `docs/script.js`
- `docs/styles.css`
