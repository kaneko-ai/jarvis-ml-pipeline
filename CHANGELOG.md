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

### Changed
- CI migrated from `pip install` to `uv sync --frozen` for reproducibility
- Report generation now requires evidence IDs (no bypass allowed)
- Quality gates enforce 90% support rate minimum

### Fixed
- Phase 2 stage imports (removed TaskContext/Artifacts dependencies)
- pytest marker warnings (added `e2e` marker to pytest.ini)

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
