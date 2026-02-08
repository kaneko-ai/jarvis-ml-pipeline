# Changelog

All notable changes to JARVIS will be documented in this file.

## [Unreleased] - Phase 2-ΩΩ (2025-12-28)

### Added
- **Evidence ID enforcement**: All conclusions must reference evidence IDs
- **Uncertainty labels**: Automatic determination (確定/高信頼/要注意/推測)
- **Cost tracking**: `cost_report.json` with tokens/time/API calls per stage
- **Subscores display**: All ranked papers show subscore breakdown
- **Ranking explanation**: Automatic strength/weakness analysis
- **Trick sets CI**: no_evidence/overclaim/contradiction evaluation gates
- **Evidence locator verification**: Quote span matching (threshold 0.8)
- **Language lint**: Forbidden causal terms, hedging requirements
- **uv + lock**: Docker-free reproducibility with `uv.lock` (62 packages)
- **RUNBOOK.md**: Operational procedures and troubleshooting guide
- **TD-002 tests**: Added `tests/test_td002_atomic_pii_trend_cov.py` to recover low-coverage branches
- **Bundle contract validator**: Added `scripts/validate_bundle.py` and `tests/test_validate_bundle.py`
- **Bundle contract doc**: Added canonical `docs/contracts/BUNDLE_CONTRACT.md`
- **Unified quality gate tests**: Added `tests/test_quality_gate_script.py` for CI/legacy script paths
- **TD-006 report**: Added `td006_flaky_report.md` with consecutive-run reproducibility records
- **Coverage test expansion**: Added `tests/test_td002_skills_engine_cov.py` for `jarvis_core.skills`

### Changed
- CI migrated from `pip install` to `uv sync --frozen` for reproducibility
- Report generation now requires evidence IDs (no bypass allowed)
- Quality gates enforce 90% support rate minimum
- `scripts/quality_gate.py` now supports both legacy `--run-dir` and integrated `--ci` mode
- CI `contract_and_unit` now runs bundle contract schema validation
- CI adds `quality_gate` job for unified required/optional checks
- CI lint workflow no longer carries stale TD-029 TODO note in mypy step
- Dashboard E2E jobs (`dashboard_e2e_mock`, `dashboard_e2e_real`) are now blocking in CI (removed `continue-on-error` and `|| true`)
- Auth compatibility updated for smoke/contract behavior when token env vars are missing

### Fixed
- Phase 2 stage imports (removed TaskContext/Artifacts dependencies)
- pytest marker warnings (added `e2e` marker to pytest.ini)
- TD-001 stability fixes for legacy compatibility surfaces (`arxiv`, `claim_set`, `automation`, `zotero`, `unpaywall`)
- Hybrid fallback embedding behavior tuned to satisfy ranking and similarity invariants in non-ML environments
- Added missing compatibility modules for `jarvis_core.cache` and `jarvis_core.evaluation` import contracts
- Windows command compatibility in terminal security execution (`pwd` alias handling)
- `tests/test_figure_extractor.py` now uses a stable PNG payload compatible with current PyMuPDF
- API contract/smoke regression: `/api/capabilities` restored to unauthenticated behavior when no web token is configured
- Dashboard mock API + UI integration regressions fixed for Playwright:
  - `tests/mock_server/app.py` now handles `/api/capabilities` query params and CORS correctly
  - `dashboard/runs.html` now uses safe API response handling for `/api/runs`
  - `dashboard/assets/app.js` now includes default API map fallback when `window.api_map_v1` is absent
  - E2E specs updated to current dashboard DOM (`tests/e2e/dashboard.spec.ts`, `tests/e2e/public-dashboard.spec.ts`)

---

## [v5.3.0] - 2025-01-15

### Added
- Task 061-065: MCP/Browser/Skills/Multi-Agent/Terminal Security ドキュメントを追加
- Task 066-069: MCP/Browser/Multi-Agent の統合テストと Systematic Review E2E を追加
- Task 070-075: MCP ベンチマークと Integration/E2E/Docs ワークフローを追加
- Task 076-085: PDF パーサー、表/図抽出、統計検証、撤回/プレプリント照合、資金源/COI、Synthesis Agent、Living Review を追加
- Task 086-089: PII 検出、匿名化、Injection Guard、監査ログを追加
- Task 094-095: コメント/メンション、バージョン履歴管理を追加

### Changed
- Task 090-093: HIPAA チェッカー、Team Workspace、Activity Feed、RBAC を刷新
- Task 096: 依存グループを更新しバージョンを 5.3.0 に更新

### Fixed
- Task 097: CHANGELOG 構成の整理とタスク番号付与

### Deprecated
- なし

---

## [v5.0.0] - 2024-12-23

### 🚀 Major Release: 300 Features Implementation

#### New Modules

- **scientist/coscientist.py** - AI Co-Scientist (20 features)
  - HypothesisGenerator, ResearchQuestionDecomposer, LiteratureGapAnalyzer
  - ExperimentDesignerPro, HypothesisDebateSystem, FundingOpportunityMatcher
  
- **protein/biomolecule.py** - Protein AI (20 features)
  - AlphaFoldIntegration, BindingAffinityPredictor, ProteinSequenceDesigner
  - ADMETPredictor, ToxicityScreener, PathwayEnrichmentAnalyzer

- **lab/automation.py** - Lab Automation (60 features)
  - LabEquipmentController, RoboticArmIntegration, SampleTracker
  - WebScraper, MCPServerManager, ToolChainBuilder

- **advanced/features.py** - Advanced Features (100 features)
  - MetaAnalysisBot, BayesianStatsEngine, CausalInferenceAgent
  - HIPAAComplianceChecker, TeamWorkspace, ActivityFeed

#### Dashboard V2

- 7 new tabs: Dashboard, AI Co-Scientist, Protein Lab, Self-Driving Lab, Meta-Analysis, Compliance, Pipelines
- Multi-theme support (dark/light/ocean/forest/sunset)
- Keyboard shortcuts (Cmd+K, 1-7 for tabs)
- Accessibility improvements (high contrast, font size)

#### New Pipelines

- `research-pipelines.yml` with 5 new pipelines:
  - hypothesis-pipeline
  - protein-pipeline
  - meta-analysis-pipeline
  - grant-pipeline
  - lab-automation-pipeline

#### Tests

- `test_features_300.py` - 60+ tests covering all new features

### 📖 Documentation

- `FEATURES_300.md` - Complete guide for all 300 features
- `QUICKSTART.md` - 5-minute getting started guide

---

## [v4.3.0] - 2024-12-22

### Previous Features (100)

- GraphRAG Engine, Multi-Agent Orchestrator
- Multimodal Scientific Analysis
- Workflow Automation
- Infrastructure & Ecosystem Integration

---

## [v4.2.0] - 2024-12-21

### Dashboard Features (50)

- Glassmorphism UI
- Chart.js integration
- PWA support
- PubMed API integration
- Added CLI regression tests for MCP and Skills commands (`tests/cli/test_mcp_skills_cli.py`).
- Added TD-012 browser behavior tests (`tests/test_browser_subagent_td012.py`).
- BrowserSubagent now supports bounded action execution via `action_timeout_s` and returns explicit timeout errors.
- Verified TD-014..TD-017 suites on current implementation (orchestrator/plugins/zotero/export): all green.
- Hardened API smoke tests to self-host local API when unavailable, reducing skip-only outcomes (`tests/smoke_api_v1.py`).

- Verified packaging preflight via `uv --with build --with twine` (sdist/wheel build + twine check).
