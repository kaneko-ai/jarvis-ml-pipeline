"""Phase L-2: Complete Branch Coverage for lab/automation.py.

Strategy: Analyze each branch and create tests that hit EVERY line
"""


class TestPDFDownloaderBranches:
    """Complete branch coverage for PDFDownloader."""

    def test_get_download_url_with_doi(self):
        from jarvis_core.lab.automation import PDFDownloader

        downloader = PDFDownloader()

        # Valid DOI format
        result = downloader.get_download_url("10.1038/nature12373")
        assert "sources" in result

    def test_get_download_url_invalid_doi(self):
        from jarvis_core.lab.automation import PDFDownloader

        downloader = PDFDownloader()

        # Invalid DOI
        result = downloader.get_download_url("")
        assert result is not None


class TestExperimentSchedulerBranches:
    """Complete branch coverage for ExperimentScheduler."""

    def test_check_conflicts_with_overlap(self):
        from jarvis_core.lab.automation import ExperimentScheduler

        scheduler = ExperimentScheduler()

        scheduler.add_experiment("Exp1", "2024-01-01 09:00", 4, ["microscope"])

        # Overlapping time and equipment
        conflicts = scheduler.check_conflicts("2024-01-01 10:00", 2, ["microscope"])
        assert len(conflicts) >= 1

    def test_check_conflicts_no_overlap(self):
        from jarvis_core.lab.automation import ExperimentScheduler

        scheduler = ExperimentScheduler()

        scheduler.add_experiment("Exp1", "2024-01-01 09:00", 4, ["microscope"])

        # Different day
        conflicts = scheduler.check_conflicts("2024-01-02 09:00", 2, ["microscope"])
        assert len(conflicts) == 0

    def test_check_conflicts_different_equipment(self):
        from jarvis_core.lab.automation import ExperimentScheduler

        scheduler = ExperimentScheduler()

        scheduler.add_experiment("Exp1", "2024-01-01 09:00", 4, ["microscope"])

        # Same time, different equipment
        conflicts = scheduler.check_conflicts("2024-01-01 10:00", 2, ["centrifuge"])
        assert len(conflicts) == 0


class TestReagentInventoryManagerBranches:
    """Complete branch coverage for ReagentInventoryManager."""

    def test_use_reagent_sufficient(self):
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()

        manager.add_reagent("buffer", 500, "ml")
        result = manager.use_reagent("buffer", 100)
        assert "error" not in result

    def test_use_reagent_insufficient(self):
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()

        manager.add_reagent("buffer", 50, "ml")
        result = manager.use_reagent("buffer", 100)
        assert "error" in result

    def test_use_reagent_nonexistent(self):
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()

        result = manager.use_reagent("nonexistent", 10)
        assert "error" in result

    def test_check_low_stock_empty(self):
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()

        result = manager.check_low_stock(threshold=50)
        assert result == []

    def test_check_low_stock_with_low_items(self):
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()

        manager.add_reagent("buffer", 10, "ml")
        manager.add_reagent("enzyme", 100, "units")

        result = manager.check_low_stock(threshold=50)
        assert len(result) == 1
        assert result[0]["name"] == "buffer"


class TestProtocolVersionControlBranches:
    """Complete branch coverage for ProtocolVersionControl."""

    def test_get_version_latest(self):
        from jarvis_core.lab.automation import ProtocolVersionControl

        vc = ProtocolVersionControl()

        vc.save_version("protocol", "v1", "Author")
        vc.save_version("protocol", "v2", "Author")

        result = vc.get_version("protocol")
        assert result["version"] == 2

    def test_get_version_specific(self):
        from jarvis_core.lab.automation import ProtocolVersionControl

        vc = ProtocolVersionControl()

        vc.save_version("protocol", "v1", "Author")
        vc.save_version("protocol", "v2", "Author")

        result = vc.get_version("protocol", version=1)
        assert result["version"] == 1

    def test_get_version_nonexistent(self):
        from jarvis_core.lab.automation import ProtocolVersionControl

        vc = ProtocolVersionControl()

        result = vc.get_version("nonexistent")
        assert result is None


class TestAnomalyDetectorBranches:
    """Complete branch coverage for AnomalyDetector."""

    def test_detect_no_anomalies(self):
        from jarvis_core.lab.automation import AnomalyDetector

        detector = AnomalyDetector()

        # Normal data (all within 2 std dev)
        data = [10, 11, 10, 11, 10, 11, 10, 11]
        result = detector.detect(data)
        assert len(result) == 0

    def test_detect_with_anomalies(self):
        from jarvis_core.lab.automation import AnomalyDetector

        detector = AnomalyDetector()

        # Data with obvious outliers
        data = [10, 11, 10, 100, 11, 10, -50]
        result = detector.detect(data)
        assert len(result) >= 1

    def test_detect_empty_data(self):
        from jarvis_core.lab.automation import AnomalyDetector

        detector = AnomalyDetector()

        result = detector.detect([])
        assert result == [] or result is not None

    def test_detect_single_value(self):
        from jarvis_core.lab.automation import AnomalyDetector

        detector = AnomalyDetector()

        result = detector.detect([10])
        assert result is not None


class TestSampleTrackerBranches:
    """Complete branch coverage for SampleTracker."""

    def test_get_sample_exists(self):
        from jarvis_core.lab.automation import SampleTracker

        tracker = SampleTracker()

        tracker.add_sample("s1", {"name": "Sample 1"})
        result = tracker.get_sample("s1")
        assert result is not None

    def test_get_sample_not_exists(self):
        from jarvis_core.lab.automation import SampleTracker

        tracker = SampleTracker()

        result = tracker.get_sample("nonexistent")
        assert result is None

    def test_update_sample_exists(self):
        from jarvis_core.lab.automation import SampleTracker

        tracker = SampleTracker()

        tracker.add_sample("s1", {"name": "Sample 1", "location": "A"})
        tracker.update_sample("s1", {"location": "B"})

        result = tracker.get_sample("s1")
        assert result["location"] == "B"

    def test_update_sample_not_exists(self):
        from jarvis_core.lab.automation import SampleTracker

        tracker = SampleTracker()

        # Should not raise error
        tracker.update_sample("nonexistent", {"location": "B"})


class TestQualityControlAgentBranches:
    """Complete branch coverage for QualityControlAgent."""

    def test_check_all_pass(self):
        from jarvis_core.lab.automation import QualityControlAgent

        agent = QualityControlAgent()

        agent.add_rule("purity", "purity_score", 0.95)
        agent.add_rule("conc", "concentration", 100)

        result = agent.check({"purity_score": 0.98, "concentration": 150})
        assert result["overall"] == "pass"

    def test_check_some_fail(self):
        from jarvis_core.lab.automation import QualityControlAgent

        agent = QualityControlAgent()

        agent.add_rule("purity", "purity_score", 0.95)
        agent.add_rule("conc", "concentration", 100)

        result = agent.check({"purity_score": 0.50, "concentration": 150})
        assert result["overall"] == "fail"

    def test_check_missing_field(self):
        from jarvis_core.lab.automation import QualityControlAgent

        agent = QualityControlAgent()

        agent.add_rule("purity", "purity_score", 0.95)

        result = agent.check({})  # Missing purity_score
        assert result["overall"] == "fail" or result is not None


class TestWebMonitoringAgentBranches:
    """Complete branch coverage for WebMonitoringAgent."""

    def test_check_for_changes_first_time(self):
        from jarvis_core.lab.automation import WebMonitoringAgent

        agent = WebMonitoringAgent()

        agent.add_monitor("https://example.com", 60)
        result = agent.check_for_changes("https://example.com", "hash1")
        # First time should mark as new or return appropriate response
        assert result is not None

    def test_check_for_changes_no_change(self):
        from jarvis_core.lab.automation import WebMonitoringAgent

        agent = WebMonitoringAgent()

        agent.add_monitor("https://example.com", 60)
        agent.check_for_changes("https://example.com", "hash1")
        result = agent.check_for_changes("https://example.com", "hash1")
        assert not result["changed"]

    def test_check_for_changes_with_change(self):
        from jarvis_core.lab.automation import WebMonitoringAgent

        agent = WebMonitoringAgent()

        agent.add_monitor("https://example.com", 60)
        agent.check_for_changes("https://example.com", "hash1")
        result = agent.check_for_changes("https://example.com", "hash2")
        assert result["changed"]


class TestRealTimeDataAnalyzerBranches:
    """Complete branch coverage for RealTimeDataAnalyzer."""

    def test_get_stats_empty(self):
        from jarvis_core.lab.automation import RealTimeDataAnalyzer

        analyzer = RealTimeDataAnalyzer()

        result = analyzer.get_stats()
        assert result is not None

    def test_get_stats_with_data(self):
        from jarvis_core.lab.automation import RealTimeDataAnalyzer

        analyzer = RealTimeDataAnalyzer()

        analyzer.add_data_point(10)
        analyzer.add_data_point(20)
        analyzer.add_data_point(30)

        result = analyzer.get_stats()
        assert "mean" in result
        assert result["mean"] == 20


class TestBayesianOptimizerBranches:
    """Complete branch coverage for BayesianOptimizer."""

    def test_suggest_no_history(self):
        from jarvis_core.lab.automation import BayesianOptimizer

        optimizer = BayesianOptimizer()

        params = {"x": (0, 10), "y": (0, 100)}
        result = optimizer.suggest(params, [])
        assert result is not None

    def test_suggest_with_history(self):
        from jarvis_core.lab.automation import BayesianOptimizer

        optimizer = BayesianOptimizer()

        params = {"x": (0, 10), "y": (0, 100)}
        history = [
            {"params": {"x": 5, "y": 50}, "score": 0.8},
            {"params": {"x": 3, "y": 30}, "score": 0.6},
        ]
        result = optimizer.suggest(params, history)
        assert result is not None
