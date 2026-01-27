from jarvis_core.ops.metrics import PipelineMetrics


def test_metrics_counter():
    metrics = PipelineMetrics()
    metrics.inc_counter("request_total", {"status": "200"})
    metrics.inc_counter("request_total", {"status": "200"})
    metrics.inc_counter("request_total", {"status": "500"})

    output = metrics.generate_prometheus_output()
    assert 'request_total{status="200"} 2.0' in output
    assert 'request_total{status="500"} 1.0' in output
    assert "# TYPE request_total counter" in output


def test_metrics_gauge():
    metrics = PipelineMetrics()
    metrics.set_gauge("queue_size", 10, {"priority": "high"})
    metrics.set_gauge("queue_size", 5, {"priority": "low"})

    # Overwrite
    metrics.set_gauge("queue_size", 12, {"priority": "high"})

    output = metrics.generate_prometheus_output()
    assert 'queue_size{priority="high"} 12' in output
    assert 'queue_size{priority="low"} 5' in output
    assert "# TYPE queue_size gauge" in output


def test_metrics_histogram():
    metrics = PipelineMetrics()
    metrics.observe("latency", 0.1)
    metrics.observe("latency", 0.5)

    output = metrics.generate_prometheus_output()
    assert "latency_count{latency, } 2" in output or "latency_count{} 2" in output
    assert "latency_sum{latency, } 0.6" in output or "latency_sum{} 0.6" in output
