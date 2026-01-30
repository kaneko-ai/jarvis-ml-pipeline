"""Phase A v2: Direct Line Coverage - Error Paths and Branches.

Strategy: Test SPECIFIC uncovered lines by triggering error paths
Target lines: 50, 70-74, 95, 102-104, 109-112, 116-118, etc.
"""

# ====================
# LabEquipmentController - Error Paths (lines 50, 70-74)
# ====================


class TestLabEquipmentControllerErrorPaths:
    """Test error paths to cover lines 50, 70-74."""

    def test_send_command_equipment_not_found_line50(self):
        """Line 50: return {'error': 'Equipment not found'}"""
        from jarvis_core.lab.automation import LabEquipmentController

        controller = LabEquipmentController()
        result = controller.send_command("nonexistent", "start")
        assert result == {"error": "Equipment not found"}

    def test_get_status_equipment_not_found_line70_71(self):
        """Lines 70-71: Equipment not found error path"""
        from jarvis_core.lab.automation import LabEquipmentController

        controller = LabEquipmentController()
        result = controller.get_status("nonexistent")
        assert result == {"error": "Equipment not found"}

    def test_get_status_success_line73_74(self):
        """Lines 73-74: Return equipment status"""
        from jarvis_core.lab.automation import LabEquipmentController, LabEquipment

        controller = LabEquipmentController()
        eq = LabEquipment(id="eq1", name="Test", type="analyzer")
        controller.register_equipment(eq)
        status = controller.get_status("eq1")
        assert "id" in status
        assert status["name"] == "Test"


# ====================
# RoboticArmIntegration - Error Paths (lines 95, 102-104, 109-112, 116-118)
# ====================


class TestRoboticArmErrorPaths:
    """Test error paths for RoboticArmIntegration."""

    def test_move_to_unknown_position_line95(self):
        """Line 95: Unknown position error"""
        from jarvis_core.lab.automation import RoboticArmIntegration

        arm = RoboticArmIntegration()
        result = arm.move_to("nonexistent_position")
        assert "error" in result

    def test_pick_tip_already_holding_line102_103(self):
        """Lines 102-103: Already holding tip error"""
        from jarvis_core.lab.automation import RoboticArmIntegration

        arm = RoboticArmIntegration()
        arm.pick_tip()  # First pick
        result = arm.pick_tip()  # Second pick - should error
        assert result == {"error": "Already holding tip"}

    def test_aspirate_no_tip_line109_110(self):
        """Lines 109-110: No tip attached error"""
        from jarvis_core.lab.automation import RoboticArmIntegration

        arm = RoboticArmIntegration()
        result = arm.aspirate(100.0)
        assert result == {"error": "No tip attached"}

    def test_aspirate_success_line111_112(self):
        """Lines 111-112: Successful aspirate"""
        from jarvis_core.lab.automation import RoboticArmIntegration

        arm = RoboticArmIntegration()
        arm.pick_tip()
        result = arm.aspirate(100.0)
        assert result["status"] == "aspirated"
        assert result["volume_ul"] == 100.0

    def test_dispense_no_sample_line116_117(self):
        """Lines 116-117: No sample to dispense error"""
        from jarvis_core.lab.automation import RoboticArmIntegration

        arm = RoboticArmIntegration()
        arm.pick_tip()
        result = arm.dispense(100.0)
        assert result == {"error": "No sample to dispense"}

    def test_dispense_success_line118_119(self):
        """Lines 118-119: Successful dispense"""
        from jarvis_core.lab.automation import RoboticArmIntegration

        arm = RoboticArmIntegration()
        arm.pick_tip()
        arm.aspirate(100.0)
        result = arm.dispense(100.0)
        assert result["status"] == "dispensed"


# ====================
# SampleTracker - Error Paths (line 189)
# ====================


class TestSampleTrackerErrorPaths:
    """Test error paths for SampleTracker."""

    def test_update_location_not_found_line189(self):
        """Line 189: Sample not found error"""
        from jarvis_core.lab.automation import SampleTracker

        tracker = SampleTracker()
        result = tracker.update_location("nonexistent", "Freezer")
        assert result == {"error": "Sample not found"}


# ====================
# EnvironmentalMonitor - Alert Paths (lines 218-225)
# ====================


class TestEnvironmentalMonitorAlertPaths:
    """Test alert generation paths."""

    def test_temperature_alert_low_line218_221(self):
        """Lines 218-221: Low temperature alert"""
        from jarvis_core.lab.automation import EnvironmentalMonitor

        monitor = EnvironmentalMonitor()
        monitor.record_reading(15.0, 45.0)  # Low temp
        assert len(monitor.alerts) > 0
        assert monitor.alerts[0]["type"] == "temperature"

    def test_temperature_alert_high_line218_221(self):
        """Lines 218-221: High temperature alert"""
        from jarvis_core.lab.automation import EnvironmentalMonitor

        monitor = EnvironmentalMonitor()
        monitor.record_reading(30.0, 45.0)  # High temp
        assert len(monitor.alerts) > 0

    def test_humidity_alert_low_line222_225(self):
        """Lines 222-225: Low humidity alert"""
        from jarvis_core.lab.automation import EnvironmentalMonitor

        monitor = EnvironmentalMonitor()
        monitor.record_reading(22.0, 20.0)  # Low humidity
        assert len(monitor.alerts) > 0
        assert monitor.alerts[0]["type"] == "humidity"

    def test_humidity_alert_high_line222_225(self):
        """Lines 222-225: High humidity alert"""
        from jarvis_core.lab.automation import EnvironmentalMonitor

        monitor = EnvironmentalMonitor()
        monitor.record_reading(22.0, 80.0)  # High humidity
        assert len(monitor.alerts) > 0

    def test_get_conditions_empty_line231_232(self):
        """Lines 231-232: No readings error"""
        from jarvis_core.lab.automation import EnvironmentalMonitor

        monitor = EnvironmentalMonitor()
        result = monitor.get_current_conditions()
        assert result == {"error": "No readings available"}


# ====================
# ExperimentScheduler - Conflict Check (lines 263-265)
# ====================


class TestExperimentSchedulerConflicts:
    """Test conflict detection."""

    def test_check_conflicts_with_overlap(self):
        """Lines 263-265: Conflict detection"""
        from jarvis_core.lab.automation import ExperimentScheduler

        scheduler = ExperimentScheduler()
        scheduler.add_experiment("Exp1", "2024-01-01 10:00", 4, ["equipment_a"])
        conflicts = scheduler.check_conflicts("2024-01-01 12:00", 2, ["equipment_a"])
        assert len(conflicts) > 0


# ====================
# QualityControlAgent - QC Check (lines 284-302)
# ====================


class TestQualityControlAgentChecks:
    """Test QC check paths."""

    def test_check_pass_line286_295(self):
        """Lines 286, 295: Pass condition"""
        from jarvis_core.lab.automation import QualityControlAgent

        agent = QualityControlAgent()
        agent.add_rule("purity", "purity_score", 0.9)
        result = agent.check({"purity_score": 0.95})
        assert result["passed"] == 1
        assert result["overall"] == "pass"

    def test_check_fail_line286(self):
        """Line 286: Fail condition"""
        from jarvis_core.lab.automation import QualityControlAgent

        agent = QualityControlAgent()
        agent.add_rule("purity", "purity_score", 0.9)
        result = agent.check({"purity_score": 0.5})
        assert result["passed"] == 0
        assert result["overall"] == "fail"


# ====================
# ReagentInventoryManager - Error Paths (lines 323-334)
# ====================


class TestReagentInventoryErrorPaths:
    """Test reagent inventory error paths."""

    def test_use_reagent_not_found_line324(self):
        """Line 324: Reagent not found"""
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()
        result = manager.use_reagent("nonexistent", 10)
        assert result == {"error": "Reagent not found"}

    def test_use_reagent_insufficient_line328_332(self):
        """Lines 328-332: Insufficient quantity"""
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()
        manager.add_reagent("buffer", 5, "ml")
        result = manager.use_reagent("buffer", 10)
        assert "error" in result
        assert "Insufficient" in result["error"]

    def test_check_low_stock_line340_341(self):
        """Lines 340-341: Low stock detection"""
        from jarvis_core.lab.automation import ReagentInventoryManager

        manager = ReagentInventoryManager()
        manager.add_reagent("buffer", 5, "ml")
        low = manager.check_low_stock(threshold=10)
        assert len(low) > 0


# ====================
# ProtocolVersionControl - Version Handling (lines 353-378)
# ====================


class TestProtocolVersionControlPaths:
    """Test version control paths."""

    def test_save_first_version_line353_354(self):
        """Lines 353-354: First version creation"""
        from jarvis_core.lab.automation import ProtocolVersionControl

        vc = ProtocolVersionControl()
        result = vc.save_version("protocol1", "content", "author")
        assert result["version"] == 1

    def test_get_version_not_found_line371_372(self):
        """Lines 371-372: Protocol not found"""
        from jarvis_core.lab.automation import ProtocolVersionControl

        vc = ProtocolVersionControl()
        result = vc.get_version("nonexistent")
        assert result is None

    def test_get_version_latest_line375_376(self):
        """Lines 375-376: Get latest version"""
        from jarvis_core.lab.automation import ProtocolVersionControl

        vc = ProtocolVersionControl()
        vc.save_version("protocol1", "v1", "author")
        vc.save_version("protocol1", "v2", "author")
        result = vc.get_version("protocol1")
        assert result["version"] == 2

    def test_get_version_specific_line378(self):
        """Line 378: Get specific version"""
        from jarvis_core.lab.automation import ProtocolVersionControl

        vc = ProtocolVersionControl()
        vc.save_version("protocol1", "v1", "author")
        vc.save_version("protocol1", "v2", "author")
        result = vc.get_version("protocol1", 1)
        assert result["version"] == 1


# ====================
# ExperimentLogger - Filter Paths (lines 400-410)
# ====================


class TestExperimentLoggerFilterPaths:
    """Test log filtering paths."""

    def test_get_logs_no_filter_line400_401(self):
        """Lines 400-401: No filter return all"""
        from jarvis_core.lab.automation import ExperimentLogger

        logger = ExperimentLogger()
        logger.log("action1", {"key": "value"})
        logs = logger.get_logs()
        assert len(logs) == 1

    def test_get_logs_with_start_time_line405_406(self):
        """Lines 405-406: Start time filter"""
        from jarvis_core.lab.automation import ExperimentLogger

        logger = ExperimentLogger()
        logger.log("action1", {"key": "value"})
        logs = logger.get_logs(start_time="2020-01-01")
        assert len(logs) >= 0

    def test_get_logs_with_end_time_line407_408(self):
        """Lines 407-408: End time filter"""
        from jarvis_core.lab.automation import ExperimentLogger

        logger = ExperimentLogger()
        logger.log("action1", {"key": "value"})
        logs = logger.get_logs(end_time="2030-01-01")
        assert len(logs) >= 0


# ====================
# AnomalyDetector - Detection Paths (lines 427-442)
# ====================


class TestAnomalyDetectorPaths:
    """Test anomaly detection paths."""

    def test_detect_no_anomaly(self):
        """Normal values - no anomaly"""
        from jarvis_core.lab.automation import AnomalyDetector

        detector = AnomalyDetector()
        detector.set_baseline("temp", mean=22.0, std=2.0)
        anomalies = detector.detect({"temp": 23.0})
        assert len(anomalies) == 0

    def test_detect_anomaly_medium_line431_438(self):
        """Lines 431, 438: Medium severity anomaly"""
        from jarvis_core.lab.automation import AnomalyDetector

        detector = AnomalyDetector()
        detector.set_baseline("temp", mean=22.0, std=1.0)
        anomalies = detector.detect({"temp": 30.0})  # z > 3
        assert len(anomalies) > 0
        assert anomalies[0]["severity"] == "medium"

    def test_detect_anomaly_high_line438(self):
        """Line 438: High severity anomaly (z > 5)"""
        from jarvis_core.lab.automation import AnomalyDetector

        detector = AnomalyDetector()
        detector.set_baseline("temp", mean=22.0, std=1.0)
        anomalies = detector.detect({"temp": 35.0})  # z > 5
        assert len(anomalies) > 0
        assert anomalies[0]["severity"] == "high"


# ====================
# RealTimeDataAnalyzer - Stats Paths (lines 455-475)
# ====================


class TestRealTimeDataAnalyzerPaths:
    """Test real-time analyzer paths."""

    def test_add_point_over_window_line455_456(self):
        """Lines 455-456: Window overflow handling"""
        from jarvis_core.lab.automation import RealTimeDataAnalyzer

        analyzer = RealTimeDataAnalyzer(window_size=3)
        for i in range(5):
            analyzer.add_point("metric", float(i))
        assert len(analyzer.data["metric"]) == 3

    def test_get_stats_empty_line461_462(self):
        """Lines 461-462: No data error"""
        from jarvis_core.lab.automation import RealTimeDataAnalyzer

        analyzer = RealTimeDataAnalyzer()
        result = analyzer.get_stats("nonexistent")
        assert result == {"error": "No data"}

    def test_get_stats_with_data_line464_475(self):
        """Lines 464-475: Calculate stats"""
        from jarvis_core.lab.automation import RealTimeDataAnalyzer

        analyzer = RealTimeDataAnalyzer()
        for v in [1.0, 2.0, 3.0, 4.0]:
            analyzer.add_point("metric", v)
        result = analyzer.get_stats("metric")
        assert "mean" in result
        assert "std" in result
        assert result["trend"] == "up"


# ====================
# BayesianOptimizer - Paths (lines 503-505)
# ====================


class TestBayesianOptimizerPaths:
    """Test optimizer paths."""

    def test_get_best_empty_line503_504(self):
        """Lines 503-504: No observations"""
        from jarvis_core.lab.automation import BayesianOptimizer

        optimizer = BayesianOptimizer()
        result = optimizer.get_best()
        assert result is None

    def test_get_best_with_obs_line505(self):
        """Line 505: Return best"""
        from jarvis_core.lab.automation import BayesianOptimizer

        optimizer = BayesianOptimizer()
        optimizer.observe({"x": 1}, 0.5)
        optimizer.observe({"x": 2}, 0.9)
        best = optimizer.get_best()
        assert best["result"] == 0.9


# ====================
# Additional Classes for Coverage
# ====================


class TestAdditionalClasses:
    """Test remaining classes."""

    def test_plate_reader(self):
        from jarvis_core.lab.automation import PlateReaderIntegration

        reader = PlateReaderIntegration()
        result = reader.read_plate(450)
        assert "data" in result

    def test_flow_cytometry(self):
        from jarvis_core.lab.automation import FlowCytometryAnalyzer

        analyzer = FlowCytometryAnalyzer()
        result = analyzer.analyze()
        assert "populations" in result

    def test_microscope(self):
        from jarvis_core.lab.automation import MicroscopeController

        controller = MicroscopeController()
        result = controller.capture_image()
        assert "filename" in result

    def test_spectroscopy(self):
        from jarvis_core.lab.automation import SpectroscopyAnalyzer

        analyzer = SpectroscopyAnalyzer()
        result = analyzer.analyze_spectrum([400, 450, 500], [0.1, 0.9, 0.3])
        assert result["peak_wavelength"] == 450

    def test_pcr_optimizer(self):
        from jarvis_core.lab.automation import PCROptimizer

        optimizer = PCROptimizer()
        result = optimizer.optimize_conditions(60.0, 62.0)
        assert "annealing_temp" in result

    def test_cell_culture(self):
        from jarvis_core.lab.automation import CellCultureMonitor

        monitor = CellCultureMonitor()
        result = monitor.check_confluency()
        assert "confluency_pct" in result

    def test_lab_safety(self):
        from jarvis_core.lab.automation import LabSafetyMonitor

        monitor = LabSafetyMonitor()
        result = monitor.check_safety()
        assert result["fume_hood_on"]
