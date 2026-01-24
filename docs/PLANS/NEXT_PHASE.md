# NEXT_PHASE（PR-NEXT-01〜03 実行計画）

> Authority: ROADMAP (Level 2, Non-binding)

## 1. ゴール
- spec-lintをPhase1方式にしてPRが詰まらないようにする。
- 失敗握りつぶし（`|| true` 等）を排除。
- phase1 coverage 85% 到達。

## 2. 非ゴール
- 新機能追加はしない。
- 大規模リファクタはしない。

## 3. 変更範囲
- PR-NEXT-01: `tools/spec_lint.py`, `.github/workflows/spec-lint.yml`, `scripts/ci_coverage.sh`, `pyproject.toml`, `.gitattributes`
- PR-NEXT-02: `jarvis_core/llm_utils.py`, `tests/` (E2E)
- PR-NEXT-03: `coverage.json` 解析スクリプト, `docs/coverage_hotspots.md`

## 4. 受け入れ条件（DoD）
- CI: spec-lint PASS（docs変更時のみ検査）
- CI: phase1 coverage >= 85%（PR-NEXT-03完了時）
- MASTER_SPECの禁止事項（`|| true`等）を品質ゲートから排除。

## 5. 実行コマンド
```bash
python tools/spec_lint.py --paths docs/COVERAGE_POLICY.md
bash scripts/ci_coverage.sh phase1
```

## 6. リスクと回避策
- mock provider が本番ロジックに影響しないよう、環境変数 `LLM_PROVIDER=mock` で分離する。
