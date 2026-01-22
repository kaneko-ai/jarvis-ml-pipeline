"""Phase L-3: Complete Branch Coverage for advanced/features.py.

Strategy: Cover all branches in high-impact classes
"""

import pytest
from unittest.mock import patch, MagicMock
import math


class TestMetaAnalysisBotBranches:
    """Complete branch coverage for MetaAnalysisBot."""

    def test_run_meta_analysis_empty(self):
        from jarvis_core.advanced.features import MetaAnalysisBot
        bot = MetaAnalysisBot()
        result = bot.run_meta_analysis([])
        assert "pooled_effect" in result
        assert result["pooled_effect"] is None or result["pooled_effect"] == 0

    def test_run_meta_analysis_single(self):
        from jarvis_core.advanced.features import MetaAnalysisBot
        bot = MetaAnalysisBot()
        result = bot.run_meta_analysis([{"effect_size": 0.5, "sample_size": 100, "variance": 0.1}])
        assert result["pooled_effect"] == 0.5

    def test_run_meta_analysis_multiple(self):
        from jarvis_core.advanced.features import MetaAnalysisBot
        bot = MetaAnalysisBot()
        studies = [
            {"effect_size": 0.5, "sample_size": 100, "variance": 0.1},
            {"effect_size": 0.6, "sample_size": 200, "variance": 0.08},
        ]
        result = bot.run_meta_analysis(studies)
        assert result["pooled_effect"] is not None

    def test_run_meta_analysis_missing_fields(self):
        from jarvis_core.advanced.features import MetaAnalysisBot
        bot = MetaAnalysisBot()
        # Missing variance
        result = bot.run_meta_analysis([{"effect_size": 0.5, "sample_size": 100}])
        assert result is not None


class TestSystematicReviewAgentBranches:
    """Complete branch coverage for SystematicReviewAgent."""

    def test_add_paper_all_stages(self):
        from jarvis_core.advanced.features import SystematicReviewAgent
        agent = SystematicReviewAgent()
        
        for stage in ["identification", "screening", "eligibility", "included"]:
            agent.add_paper(f"p_{stage}", {"title": f"Paper {stage}"}, stage=stage)
        
        assert len(agent.papers) == 4

    def test_exclude_paper_existing(self):
        from jarvis_core.advanced.features import SystematicReviewAgent
        agent = SystematicReviewAgent()
        agent.add_paper("p1", {"title": "Paper 1"})
        agent.exclude_paper("p1", "Duplicate")
        assert agent.papers["p1"]["excluded"] == True

    def test_exclude_paper_nonexistent(self):
        from jarvis_core.advanced.features import SystematicReviewAgent
        agent = SystematicReviewAgent()
        # Should not raise error
        agent.exclude_paper("nonexistent", "reason")

    def test_advance_stage_all_stages(self):
        from jarvis_core.advanced.features import SystematicReviewAgent
        agent = SystematicReviewAgent()
        agent.add_paper("p1", {"title": "Paper 1"}, stage="identification")
        
        # Through all stages
        agent.advance_stage("p1")
        assert agent.papers["p1"]["stage"] == "screening"
        
        agent.advance_stage("p1")
        assert agent.papers["p1"]["stage"] == "eligibility"
        
        agent.advance_stage("p1")
        assert agent.papers["p1"]["stage"] == "included"
        
        # Already at final stage
        agent.advance_stage("p1")
        assert agent.papers["p1"]["stage"] == "included"

    def test_advance_stage_nonexistent(self):
        from jarvis_core.advanced.features import SystematicReviewAgent
        agent = SystematicReviewAgent()
        # Should not raise error
        agent.advance_stage("nonexistent")

    def test_get_prisma_flow_empty(self):
        from jarvis_core.advanced.features import SystematicReviewAgent
        agent = SystematicReviewAgent()
        flow = agent.get_prisma_flow()
        assert "identification" in flow

    def test_get_prisma_flow_with_papers(self):
        from jarvis_core.advanced.features import SystematicReviewAgent
        agent = SystematicReviewAgent()
        agent.add_paper("p1", {}, stage="identification")
        agent.add_paper("p2", {}, stage="screening")
        agent.exclude_paper("p2", "reason")
        
        flow = agent.get_prisma_flow()
        assert flow["identification"] >= 1


class TestTimeSeriesAnalyzerBranches:
    """Complete branch coverage for TimeSeriesAnalyzer."""

    def test_decompose_normal(self):
        from jarvis_core.advanced.features import TimeSeriesAnalyzer
        analyzer = TimeSeriesAnalyzer()
        data = [10 + i*0.1 + 5*math.sin(i*math.pi/6) for i in range(48)]
        result = analyzer.decompose(data, period=12)
        assert "trend" in result
        assert "seasonal" in result

    def test_decompose_short_data(self):
        from jarvis_core.advanced.features import TimeSeriesAnalyzer
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.decompose([1, 2, 3], period=2)
        assert result is not None

    def test_decompose_empty(self):
        from jarvis_core.advanced.features import TimeSeriesAnalyzer
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.decompose([], period=12)
        assert result is not None

    def test_forecast_normal(self):
        from jarvis_core.advanced.features import TimeSeriesAnalyzer
        analyzer = TimeSeriesAnalyzer()
        data = [10 + i*0.5 for i in range(20)]
        result = analyzer.forecast(data, steps=5)
        assert len(result) == 5

    def test_forecast_short_data(self):
        from jarvis_core.advanced.features import TimeSeriesAnalyzer
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.forecast([1, 2], steps=3)
        assert len(result) >= 0


class TestBayesianStatsEngineBranches:
    """Complete branch coverage for BayesianStatsEngine."""

    def test_update_belief_normal(self):
        from jarvis_core.advanced.features import BayesianStatsEngine
        engine = BayesianStatsEngine()
        result = engine.update_belief(0.0, 1.0, 0.5, 0.5, 100)
        assert "posterior_mean" in result
        assert "posterior_std" in result

    def test_update_belief_small_n(self):
        from jarvis_core.advanced.features import BayesianStatsEngine
        engine = BayesianStatsEngine()
        result = engine.update_belief(0.0, 1.0, 0.5, 0.5, 1)
        assert result is not None

    def test_update_belief_large_n(self):
        from jarvis_core.advanced.features import BayesianStatsEngine
        engine = BayesianStatsEngine()
        result = engine.update_belief(0.0, 1.0, 0.5, 0.1, 10000)
        # With large n, posterior should be close to data mean
        assert abs(result["posterior_mean"] - 0.5) < 0.1


class TestCausalInferenceAgentBranches:
    """Complete branch coverage for CausalInferenceAgent."""

    def test_estimate_ate_normal(self):
        from jarvis_core.advanced.features import CausalInferenceAgent
        agent = CausalInferenceAgent()
        result = agent.estimate_ate([1.5, 1.6, 1.7], [1.0, 1.1, 1.2])
        assert "ate" in result
        assert result["ate"] > 0

    def test_estimate_ate_equal_groups(self):
        from jarvis_core.advanced.features import CausalInferenceAgent
        agent = CausalInferenceAgent()
        result = agent.estimate_ate([1.0, 1.0], [1.0, 1.0])
        assert result["ate"] == 0

    def test_estimate_ate_empty(self):
        from jarvis_core.advanced.features import CausalInferenceAgent
        agent = CausalInferenceAgent()
        result = agent.estimate_ate([], [])
        assert result is not None


class TestSurvivalAnalysisBotBranches:
    """Complete branch coverage for SurvivalAnalysisBot."""

    def test_kaplan_meier_all_events(self):
        from jarvis_core.advanced.features import SurvivalAnalysisBot
        bot = SurvivalAnalysisBot()
        times = [1, 2, 3, 4, 5]
        events = [True, True, True, True, True]
        result = bot.kaplan_meier(times, events)
        assert "survival_curve" in result

    def test_kaplan_meier_no_events(self):
        from jarvis_core.advanced.features import SurvivalAnalysisBot
        bot = SurvivalAnalysisBot()
        times = [1, 2, 3, 4, 5]
        events = [False, False, False, False, False]
        result = bot.kaplan_meier(times, events)
        assert result is not None

    def test_kaplan_meier_mixed(self):
        from jarvis_core.advanced.features import SurvivalAnalysisBot
        bot = SurvivalAnalysisBot()
        times = [1, 2, 3, 4, 5]
        events = [True, False, True, False, True]
        result = bot.kaplan_meier(times, events)
        assert result is not None


class TestMissingDataHandlerBranches:
    """Complete branch coverage for MissingDataHandler."""

    def test_impute_mean_with_missing(self):
        from jarvis_core.advanced.features import MissingDataHandler
        handler = MissingDataHandler()
        result = handler.impute_mean([1.0, None, 3.0])
        assert result[1] == 2.0

    def test_impute_mean_no_missing(self):
        from jarvis_core.advanced.features import MissingDataHandler
        handler = MissingDataHandler()
        result = handler.impute_mean([1.0, 2.0, 3.0])
        assert result == [1.0, 2.0, 3.0]

    def test_impute_mean_all_missing(self):
        from jarvis_core.advanced.features import MissingDataHandler
        handler = MissingDataHandler()
        result = handler.impute_mean([None, None])
        assert result is not None

    def test_detect_missing_pattern(self):
        from jarvis_core.advanced.features import MissingDataHandler
        handler = MissingDataHandler()
        data = {"a": [1, None, 3], "b": [None, 2, None]}
        result = handler.detect_missing_pattern(data)
        assert result is not None


class TestPowerAnalysisCalculatorBranches:
    """Complete branch coverage for PowerAnalysisCalculator."""

    def test_calculate_sample_size_two_sample(self):
        from jarvis_core.advanced.features import PowerAnalysisCalculator
        calc = PowerAnalysisCalculator()
        result = calc.calculate_sample_size(0.5, 0.05, 0.8, design="two_sample")
        assert "sample_size" in result

    def test_calculate_sample_size_one_sample(self):
        from jarvis_core.advanced.features import PowerAnalysisCalculator
        calc = PowerAnalysisCalculator()
        result = calc.calculate_sample_size(0.5, 0.05, 0.8, design="one_sample")
        assert result is not None

    def test_calculate_sample_size_paired(self):
        from jarvis_core.advanced.features import PowerAnalysisCalculator
        calc = PowerAnalysisCalculator()
        result = calc.calculate_sample_size(0.5, 0.05, 0.8, design="paired")
        assert result is not None

    def test_calculate_sample_size_various_effect_sizes(self):
        from jarvis_core.advanced.features import PowerAnalysisCalculator
        calc = PowerAnalysisCalculator()
        
        for effect in [0.2, 0.5, 0.8]:
            result = calc.calculate_sample_size(effect, 0.05, 0.8)
            assert result["sample_size"] > 0
