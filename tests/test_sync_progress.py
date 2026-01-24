"""Tests for sync.progress module."""

from jarvis_core.sync.progress import SyncProgressReporter


class TestSyncProgressReporter:
    def test_init(self):
        reporter = SyncProgressReporter()
        assert reporter._callbacks == []

    def test_add_callback(self):
        reporter = SyncProgressReporter()
        callback = lambda completed, total: None

        reporter.add_callback(callback)

        assert len(reporter._callbacks) == 1

    def test_report_calls_callbacks(self):
        reporter = SyncProgressReporter()
        results = []

        def callback(completed, total):
            results.append((completed, total))

        reporter.add_callback(callback)
        reporter.report(5, 10)

        assert results == [(5, 10)]

    def test_report_multiple_callbacks(self):
        reporter = SyncProgressReporter()
        results1 = []
        results2 = []

        reporter.add_callback(lambda c, t: results1.append((c, t)))
        reporter.add_callback(lambda c, t: results2.append((c, t)))

        reporter.report(3, 5)

        assert results1 == [(3, 5)]
        assert results2 == [(3, 5)]

    def test_report_without_callbacks(self):
        reporter = SyncProgressReporter()
        # Should not raise error
        reporter.report(1, 1)
