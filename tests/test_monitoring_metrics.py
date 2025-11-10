"""
Test suite for ARK Monitoring Metrics System

Tests:
- Metrics collection (counter, gauge, histogram)
- SLO tracking and violation detection
- Trace ID continuity validation
- Prometheus export format
- Thread safety
- Performance under load

Author: ARK System
Created: 2025-11-10
"""

import pytest
import time
import threading
from typing import Dict, Any

from monitoring.metrics import (
    MetricsCollector,
    SLOTarget,
    record_latency,
    increment_counter,
    set_gauge,
    record_trace,
    validate_trace,
    check_slos,
    export_prometheus,
    get_all_metrics
)


class TestMetricsCollector:
    """Test MetricsCollector core functionality."""
    
    def setup_method(self):
        """Setup fresh collector for each test."""
        self.collector = MetricsCollector(retention_seconds=60)
    
    
    def test_counter_increment(self):
        """Test counter increments correctly."""
        self.collector.inc_counter("test_counter", 1.0)
        self.collector.inc_counter("test_counter", 2.0)
        self.collector.inc_counter("test_counter", 3.0)
        
        metrics = self.collector.get_all_metrics()
        assert metrics["counters"]["test_counter"] == 6.0
    
    
    def test_counter_with_labels(self):
        """Test counters with label dimensions."""
        self.collector.inc_counter("test_counter", 1.0, labels={"agent": "Kyle"})
        self.collector.inc_counter("test_counter", 2.0, labels={"agent": "Joey"})
        self.collector.inc_counter("test_counter", 3.0, labels={"agent": "Kyle"})
        
        metrics = self.collector.get_all_metrics()
        
        # Should have separate counters per label
        assert metrics["counters"]['test_counter{agent=Kyle}'] == 4.0
        assert metrics["counters"]['test_counter{agent=Joey}'] == 2.0
    
    
    def test_gauge_set(self):
        """Test gauge sets to specific value."""
        self.collector.set_gauge("test_gauge", 10.0)
        self.collector.set_gauge("test_gauge", 20.0)
        self.collector.set_gauge("test_gauge", 15.0)
        
        metrics = self.collector.get_all_metrics()
        assert metrics["gauges"]["test_gauge"] == 15.0
    
    
    def test_histogram_observations(self):
        """Test histogram records observations correctly."""
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        for v in values:
            self.collector.observe_histogram("test_histogram", v)
        
        stats = self.collector.get_histogram_stats("test_histogram")
        
        assert stats["count"] == 10
        assert stats["sum"] == 550
        assert stats["avg"] == 55.0
        assert stats["min"] == 10
        assert stats["max"] == 100
        assert 40 <= stats["p50"] <= 60  # Median around 50
        assert 90 <= stats["p95"] <= 100  # 95th percentile near 100
    
    
    def test_histogram_retention(self):
        """Test histogram observations are cleaned up after retention period."""
        collector = MetricsCollector(retention_seconds=1)
        
        # Add observations
        collector.observe_histogram("test_histogram", 100)
        
        stats1 = collector.get_histogram_stats("test_histogram")
        assert stats1["count"] == 1
        
        # Wait for retention period
        time.sleep(1.5)
        
        # Add new observation to trigger cleanup
        collector.observe_histogram("test_histogram", 200)
        
        stats2 = collector.get_histogram_stats("test_histogram")
        assert stats2["count"] == 1  # Old observation cleaned up
        assert stats2["avg"] == 200  # Only new observation remains
    
    
    def test_trace_continuity_complete(self):
        """Test trace continuity validation with complete trace."""
        trace_id = "test-trace-001"
        agents = ["Kyle", "Joey", "HRM", "Kenny", "Aletheia"]
        
        for agent in agents:
            self.collector.record_trace_span(trace_id, agent)
            time.sleep(0.01)
        
        result = self.collector.validate_trace_continuity(trace_id, agents)
        
        assert result["complete"] is True
        assert len(result["missing_agents"]) == 0
        assert set(result["agents_seen"]) == set(agents)
        assert result["latency_ms"] > 0
    
    
    def test_trace_continuity_incomplete(self):
        """Test trace continuity validation with missing agents."""
        trace_id = "test-trace-002"
        expected = ["Kyle", "Joey", "HRM", "Kenny", "Aletheia"]
        actual = ["Kyle", "Joey", "Kenny"]  # Missing HRM and Aletheia
        
        for agent in actual:
            self.collector.record_trace_span(trace_id, agent)
        
        result = self.collector.validate_trace_continuity(trace_id, expected)
        
        assert result["complete"] is False
        assert set(result["missing_agents"]) == {"HRM", "Aletheia"}
        assert set(result["agents_seen"]) == set(actual)
    
    
    def test_slo_tracking_met(self):
        """Test SLO tracking when target is met."""
        # Register SLO
        slo = SLOTarget(
            name="test_availability",
            target=0.99,
            operator=">=",
            metric_name="availability",
            window_seconds=60
        )
        self.collector.register_slo(slo)
        
        # Set gauge to meet SLO
        self.collector.set_gauge("availability", 0.995)
        
        # Check SLOs
        result = self.collector.check_slos()
        
        assert result["total"] == 1
        assert result["met"] == 1
        assert result["violated"] == 0
        assert result["slos"][0]["met"] is True
        assert result["slos"][0]["current_value"] == 0.995
    
    
    def test_slo_tracking_violated(self):
        """Test SLO tracking when target is violated."""
        # Register SLO for latency
        slo = SLOTarget(
            name="test_latency",
            target=100.0,
            operator="<=",
            metric_name="test_latency_ms",
            window_seconds=60
        )
        self.collector.register_slo(slo)
        
        # Record high latencies
        for _ in range(10):
            self.collector.observe_histogram("test_latency_ms", 150)
        
        # Check SLOs
        result = self.collector.check_slos()
        
        assert result["total"] == 1
        assert result["violated"] == 1
        assert result["met"] == 0
        assert len(result["violations"]) == 1
        assert result["slos"][0]["met"] is False
    
    
    def test_prometheus_export_format(self):
        """Test Prometheus text format export."""
        self.collector.inc_counter("test_counter", 5.0)
        self.collector.set_gauge("test_gauge", 42.0)
        self.collector.observe_histogram("test_histogram", 100)
        self.collector.observe_histogram("test_histogram", 200)
        
        export = self.collector.export_prometheus()
        
        # Check format
        assert "test_counter " in export
        assert "test_gauge " in export
        assert "test_histogram_bucket" in export
        assert "test_histogram_sum" in export
        assert "test_histogram_count" in export
        
        # Check values
        assert "test_counter 5" in export or "test_counter 5.0" in export
        assert "test_gauge 42" in export or "test_gauge 42.0" in export
    
    
    def test_thread_safety_counters(self):
        """Test thread-safe counter increments."""
        counter_name = "thread_test_counter"
        iterations = 100
        num_threads = 10
        
        def increment():
            for _ in range(iterations):
                self.collector.inc_counter(counter_name, 1.0)
        
        threads = [threading.Thread(target=increment) for _ in range(num_threads)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        metrics = self.collector.get_all_metrics()
        expected = iterations * num_threads
        assert metrics["counters"][counter_name] == expected
    
    
    def test_thread_safety_histograms(self):
        """Test thread-safe histogram observations."""
        histogram_name = "thread_test_histogram"
        iterations = 50
        num_threads = 5
        
        def observe():
            for i in range(iterations):
                self.collector.observe_histogram(histogram_name, float(i))
        
        threads = [threading.Thread(target=observe) for _ in range(num_threads)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        stats = self.collector.get_histogram_stats(histogram_name)
        expected_count = iterations * num_threads
        assert stats["count"] == expected_count


class TestConvenienceFunctions:
    """Test convenience functions for metrics recording."""
    
    def test_record_latency(self):
        """Test record_latency convenience function."""
        record_latency("test_latency_ms", 123.45)
        
        metrics = get_all_metrics()
        assert "test_latency_ms" in str(metrics["histograms"])
    
    
    def test_increment_counter(self):
        """Test increment_counter convenience function."""
        increment_counter("test_counter", 1.0, labels={"agent": "Test"})
        
        metrics = get_all_metrics()
        assert 'test_counter{agent=Test}' in metrics["counters"]
    
    
    def test_set_gauge(self):
        """Test set_gauge convenience function."""
        set_gauge("test_gauge", 99.9)
        
        metrics = get_all_metrics()
        assert metrics["gauges"]["test_gauge"] == 99.9
    
    
    def test_record_and_validate_trace(self):
        """Test trace recording and validation."""
        trace_id = "test-trace-func-001"
        
        record_trace(trace_id, "Kyle")
        record_trace(trace_id, "Joey")
        record_trace(trace_id, "HRM")
        
        result = validate_trace(trace_id, ["Kyle", "Joey", "HRM"])
        
        assert result["complete"] is True
        assert len(result["missing_agents"]) == 0


class TestSLOTracking:
    """Test SLO tracking and violation detection."""
    
    def test_availability_slo(self):
        """Test availability SLO calculation."""
        collector = MetricsCollector()
        
        # Register availability SLO
        slo = SLOTarget(
            name="availability_99",
            target=0.99,
            operator=">=",
            metric_name="availability",
            window_seconds=300
        )
        collector.register_slo(slo)
        
        # No quarantines = 100% availability
        result = collector.check_slos()
        
        assert result["slos"][0]["met"] is True
        assert result["slos"][0]["current_value"] == 1.0
    
    
    def test_latency_slo_violation(self):
        """Test latency SLO violation detection."""
        collector = MetricsCollector()
        
        # Register latency SLO
        slo = SLOTarget(
            name="p95_latency_400ms",
            target=400.0,
            operator="<=",
            metric_name="ark_pass_latency_ms",
            window_seconds=300
        )
        collector.register_slo(slo)
        
        # Record high latencies that violate SLO
        for _ in range(100):
            collector.observe_histogram("ark_pass_latency_ms", 500)
        
        result = collector.check_slos()
        
        assert result["violated"] > 0
        assert len(result["violations"]) > 0
        assert result["slos"][0]["current_value"] > 400.0


class TestMetricsPerformance:
    """Test metrics system performance under load."""
    
    def test_high_volume_counters(self):
        """Test counter performance with high volume."""
        collector = MetricsCollector()
        
        start = time.time()
        
        for i in range(10000):
            collector.inc_counter("perf_counter", 1.0)
        
        duration = time.time() - start
        
        # Should complete in reasonable time (<1 second)
        assert duration < 1.0
        
        metrics = collector.get_all_metrics()
        assert metrics["counters"]["perf_counter"] == 10000
    
    
    def test_high_volume_histograms(self):
        """Test histogram performance with many observations."""
        collector = MetricsCollector()
        
        start = time.time()
        
        for i in range(1000):
            collector.observe_histogram("perf_histogram", float(i % 100))
        
        duration = time.time() - start
        
        # Should complete in reasonable time (<1 second)
        assert duration < 1.0
        
        stats = collector.get_histogram_stats("perf_histogram")
        assert stats["count"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
