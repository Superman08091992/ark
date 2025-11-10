"""
ARK Monitoring Metrics System

Provides Prometheus-compatible metrics collection and SLO tracking for production deployment.
Implements trace_id continuity across agent pipeline for full log correlation.

Key Metrics:
- ark_pass_latency_ms: End-to-end decision latency (histogram)
- kyle_ingest_rate: Signal ingestion throughput (gauge)
- joey_pattern_confidence_avg: Average pattern confidence (gauge)
- kenny_exec_success_rate: Execution success rate (gauge)
- hrm_denials_total: Total ethics denials by rule (counter)
- watchdog_quarantines_total: Agent quarantine events (counter)
- state_write_latency_ms: State persistence latency (histogram)

SLO Tracking:
- Availability: 99.5% uptime
- P95 Decision Latency: ≤ 400ms
- HRM Evaluation: ≤ 120ms
- Ethics Drift: 0 (immutable)

Author: ARK System
Created: 2025-11-10
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Single metric observation"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class SLOTarget:
    """Service Level Objective definition"""
    name: str
    target: float  # Target value (e.g., 0.995 for 99.5% availability)
    operator: str  # ">=", "<=", "=="
    metric_name: str
    window_seconds: int = 300  # 5 minute rolling window


class MetricsCollector:
    """
    Thread-safe metrics collector with Prometheus-compatible exposition.
    
    Supports:
    - Counter: Monotonically increasing value
    - Gauge: Point-in-time value that can go up/down
    - Histogram: Distribution of values with configurable buckets
    - Summary: Similar to histogram but with quantiles (p50, p95, p99)
    """
    
    def __init__(self, retention_seconds: int = 3600):
        """
        Initialize metrics collector.
        
        Args:
            retention_seconds: How long to keep raw observations (default 1 hour)
        """
        self.retention_seconds = retention_seconds
        self._lock = threading.RLock()
        
        # Metric storage
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[MetricValue]] = defaultdict(list)
        self._summaries: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        
        # Histogram buckets (milliseconds for latency metrics)
        self._histogram_buckets = [10, 25, 50, 75, 100, 150, 200, 300, 400, 500, 750, 1000, 2000, 5000]
        
        # Metric metadata
        self._metric_metadata: Dict[str, Dict[str, str]] = {}
        
        # Trace ID tracking for continuity validation
        self._trace_spans: Dict[str, Dict[str, float]] = {}  # trace_id -> {agent: timestamp}
        
        # SLO tracking
        self._slo_targets: List[SLOTarget] = []
        self._slo_violations: List[Dict[str, Any]] = []
        
        logger.info(f"MetricsCollector initialized with {retention_seconds}s retention")
    
    
    def register_metric(self, name: str, metric_type: str, help_text: str, labels: Optional[List[str]] = None):
        """
        Register a metric with metadata.
        
        Args:
            name: Metric name (e.g., "ark_pass_latency_ms")
            metric_type: "counter", "gauge", "histogram", or "summary"
            help_text: Human-readable description
            labels: Optional list of label names
        """
        with self._lock:
            self._metric_metadata[name] = {
                "type": metric_type,
                "help": help_text,
                "labels": labels or []
            }
            logger.debug(f"Registered metric: {name} ({metric_type})")
    
    
    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
    
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric to specific value."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
    
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record an observation for histogram metric."""
        with self._lock:
            key = self._make_key(name, labels)
            observation = MetricValue(
                timestamp=time.time(),
                value=value,
                labels=labels or {}
            )
            self._histograms[key].append(observation)
            
            # Cleanup old observations
            self._cleanup_old_observations(self._histograms[key])
    
    
    def observe_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record an observation for summary metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._summaries[key].append((time.time(), value))
    
    
    def record_trace_span(self, trace_id: str, agent_name: str, timestamp: Optional[float] = None):
        """
        Record agent participation in a trace for continuity validation.
        
        Args:
            trace_id: Unique trace identifier
            agent_name: Name of agent processing this trace
            timestamp: Event timestamp (default: now)
        """
        with self._lock:
            if trace_id not in self._trace_spans:
                self._trace_spans[trace_id] = {}
            
            self._trace_spans[trace_id][agent_name] = timestamp or time.time()
            
            # Cleanup old traces (keep last hour)
            cutoff = time.time() - self.retention_seconds
            to_remove = [
                tid for tid, spans in self._trace_spans.items()
                if all(ts < cutoff for ts in spans.values())
            ]
            for tid in to_remove:
                del self._trace_spans[tid]
    
    
    def validate_trace_continuity(self, trace_id: str, expected_agents: List[str]) -> Dict[str, Any]:
        """
        Validate that a trace passed through all expected agents.
        
        Args:
            trace_id: Trace to validate
            expected_agents: List of agent names that should have processed this trace
        
        Returns:
            {
                'complete': bool,
                'missing_agents': List[str],
                'agents_seen': List[str],
                'latency_ms': float  # Total trace duration
            }
        """
        with self._lock:
            if trace_id not in self._trace_spans:
                return {
                    'complete': False,
                    'missing_agents': expected_agents,
                    'agents_seen': [],
                    'latency_ms': 0.0
                }
            
            spans = self._trace_spans[trace_id]
            seen = list(spans.keys())
            missing = [a for a in expected_agents if a not in seen]
            
            # Calculate total latency
            if spans:
                timestamps = list(spans.values())
                latency_ms = (max(timestamps) - min(timestamps)) * 1000
            else:
                latency_ms = 0.0
            
            return {
                'complete': len(missing) == 0,
                'missing_agents': missing,
                'agents_seen': seen,
                'latency_ms': latency_ms
            }
    
    
    def register_slo(self, slo: SLOTarget):
        """Register a Service Level Objective for tracking."""
        with self._lock:
            self._slo_targets.append(slo)
            logger.info(f"Registered SLO: {slo.name} ({slo.metric_name} {slo.operator} {slo.target})")
    
    
    def check_slos(self) -> Dict[str, Any]:
        """
        Check all registered SLOs against current metric values.
        
        Returns:
            {
                'slos': [
                    {
                        'name': str,
                        'met': bool,
                        'current_value': float,
                        'target': float,
                        'operator': str
                    },
                    ...
                ],
                'total': int,
                'met': int,
                'violated': int,
                'violations': List[Dict]
            }
        """
        with self._lock:
            results = []
            violations = []
            
            for slo in self._slo_targets:
                # Get current metric value
                current_value = self._get_metric_value(slo.metric_name, slo.window_seconds)
                
                # Check against target
                if slo.operator == ">=":
                    met = current_value >= slo.target
                elif slo.operator == "<=":
                    met = current_value <= slo.target
                elif slo.operator == "==":
                    met = abs(current_value - slo.target) < 0.001
                else:
                    met = False
                
                result = {
                    'name': slo.name,
                    'met': met,
                    'current_value': current_value,
                    'target': slo.target,
                    'operator': slo.operator
                }
                results.append(result)
                
                if not met:
                    violation = result.copy()
                    violation['timestamp'] = time.time()
                    violations.append(violation)
                    self._slo_violations.append(violation)
            
            return {
                'slos': results,
                'total': len(results),
                'met': sum(1 for r in results if r['met']),
                'violated': sum(1 for r in results if not r['met']),
                'violations': violations
            }
    
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Calculate histogram statistics (count, sum, quantiles).
        
        Returns:
            {
                'count': int,
                'sum': float,
                'avg': float,
                'p50': float,
                'p95': float,
                'p99': float,
                'min': float,
                'max': float
            }
        """
        with self._lock:
            key = self._make_key(name, labels)
            observations = self._histograms.get(key, [])
            
            if not observations:
                return {
                    'count': 0,
                    'sum': 0.0,
                    'avg': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0,
                    'min': 0.0,
                    'max': 0.0
                }
            
            values = sorted([obs.value for obs in observations])
            count = len(values)
            total = sum(values)
            
            return {
                'count': count,
                'sum': total,
                'avg': total / count,
                'p50': self._percentile(values, 50),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99),
                'min': values[0],
                'max': values[-1]
            }
    
    
    def export_prometheus(self) -> str:
        """
        Export all metrics in Prometheus text exposition format.
        
        Returns:
            Multi-line string in Prometheus format
        """
        with self._lock:
            lines = []
            
            # Export counters
            for key, value in self._counters.items():
                name, labels_str = self._parse_key(key)
                lines.append(f"{name}{labels_str} {value}")
            
            # Export gauges
            for key, value in self._gauges.items():
                name, labels_str = self._parse_key(key)
                lines.append(f"{name}{labels_str} {value}")
            
            # Export histograms
            for key in self._histograms.keys():
                name, labels_str = self._parse_key(key)
                stats = self.get_histogram_stats(name)
                
                # Histogram buckets
                for bucket in self._histogram_buckets:
                    count = sum(1 for obs in self._histograms[key] if obs.value <= bucket)
                    if labels_str != "":
                        bucket_labels = f'{labels_str[:-1]},le="{bucket}"}}'
                    else:
                        bucket_labels = '{{le="{}"}}'.format(bucket)
                    lines.append(f"{name}_bucket{bucket_labels} {count}")
                
                # +Inf bucket
                if labels_str != "":
                    bucket_labels = f'{labels_str[:-1]},le="+Inf"}}'
                else:
                    bucket_labels = '{le="+Inf"}'
                lines.append(f"{name}_bucket{bucket_labels} {stats['count']}")
                
                # Sum and count
                lines.append(f"{name}_sum{labels_str} {stats['sum']}")
                lines.append(f"{name}_count{labels_str} {stats['count']}")
            
            return "\n".join(lines) + "\n"
    
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in structured format.
        
        Returns:
            {
                'counters': {...},
                'gauges': {...},
                'histograms': {...},
                'timestamp': float
            }
        """
        with self._lock:
            histograms = {}
            for key in self._histograms.keys():
                name, _ = self._parse_key(key)
                histograms[key] = self.get_histogram_stats(name)
            
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': histograms,
                'timestamp': time.time()
            }
    
    
    # Private helper methods
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create unique key for metric with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    
    def _parse_key(self, key: str) -> tuple[str, str]:
        """Parse metric key into name and label string."""
        if "{" not in key:
            return key, ""
        
        name = key.split("{")[0]
        labels = "{" + key.split("{")[1]
        return name, labels
    
    
    def _cleanup_old_observations(self, observations: List[MetricValue]):
        """Remove observations older than retention window."""
        cutoff = time.time() - self.retention_seconds
        while observations and observations[0].timestamp < cutoff:
            observations.pop(0)
    
    
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        
        k = (len(sorted_values) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1
        
        if c >= len(sorted_values):
            return sorted_values[-1]
        
        d0 = sorted_values[f] * (c - k)
        d1 = sorted_values[c] * (k - f)
        return d0 + d1
    
    
    def _get_metric_value(self, metric_name: str, window_seconds: int) -> float:
        """
        Get current value for a metric over specified time window.
        Used for SLO checking.
        """
        cutoff = time.time() - window_seconds
        
        # Check gauge first
        if metric_name in self._gauges:
            return self._gauges[metric_name]
        
        # Check counter
        if metric_name in self._counters:
            return self._counters[metric_name]
        
        # Check histogram (return p95)
        if metric_name in self._histograms:
            stats = self.get_histogram_stats(metric_name)
            return stats.get('p95', 0.0)
        
        # Check if it's a derived metric
        if metric_name == "availability":
            return self._calculate_availability(window_seconds)
        
        return 0.0
    
    
    def _calculate_availability(self, window_seconds: int) -> float:
        """
        Calculate system availability over time window.
        
        Availability = (total_time - downtime) / total_time
        
        Downtime is determined by watchdog quarantine events.
        """
        quarantines = self._counters.get("watchdog_quarantines_total", 0)
        
        # If no quarantines, assume 100% availability
        if quarantines == 0:
            return 1.0
        
        # Simple heuristic: each quarantine = 5 seconds downtime
        downtime_seconds = quarantines * 5
        uptime_seconds = window_seconds - downtime_seconds
        
        return max(0.0, uptime_seconds / window_seconds)


# Global singleton instance
_metrics_collector: Optional[MetricsCollector] = None
_metrics_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector instance."""
    global _metrics_collector
    
    if _metrics_collector is None:
        with _metrics_lock:
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
                _register_default_metrics(_metrics_collector)
                _register_default_slos(_metrics_collector)
    
    return _metrics_collector


def _register_default_metrics(collector: MetricsCollector):
    """Register all ARK system metrics."""
    
    # Core latency metrics
    collector.register_metric(
        "ark_pass_latency_ms",
        "histogram",
        "End-to-end decision latency from Kyle ingestion to completion",
        labels=["trace_id"]
    )
    
    collector.register_metric(
        "hrm_eval_latency_ms",
        "histogram",
        "HRM ethics evaluation latency including Graveyard validation"
    )
    
    collector.register_metric(
        "state_write_latency_ms",
        "histogram",
        "Mutable Core state persistence latency"
    )
    
    # Throughput metrics
    collector.register_metric(
        "kyle_ingest_rate",
        "gauge",
        "Number of signals ingested per second by Kyle"
    )
    
    collector.register_metric(
        "joey_pattern_confidence_avg",
        "gauge",
        "Average pattern confidence score from Joey analysis"
    )
    
    collector.register_metric(
        "kenny_exec_success_rate",
        "gauge",
        "Percentage of successful Kenny executions"
    )
    
    # Counter metrics
    collector.register_metric(
        "hrm_denials_total",
        "counter",
        "Total number of ethics denials by HRM",
        labels=["rule_id", "agent"]
    )
    
    collector.register_metric(
        "watchdog_quarantines_total",
        "counter",
        "Total number of agent quarantine events",
        labels=["agent", "reason"]
    )
    
    collector.register_metric(
        "graveyard_validations_total",
        "counter",
        "Total number of Graveyard ethics validations"
    )
    
    # System health
    collector.register_metric(
        "agent_heartbeat_failures",
        "counter",
        "Failed heartbeats by agent",
        labels=["agent"]
    )
    
    collector.register_metric(
        "redis_stream_depth",
        "gauge",
        "Number of pending messages in Redis stream",
        labels=["stream"]
    )
    
    logger.info("Registered default ARK metrics")


def _register_default_slos(collector: MetricsCollector):
    """Register production SLO targets."""
    
    # Availability: 99.5% uptime
    collector.register_slo(SLOTarget(
        name="availability_995",
        target=0.995,
        operator=">=",
        metric_name="availability",
        window_seconds=300
    ))
    
    # P95 decision latency: ≤ 400ms
    collector.register_slo(SLOTarget(
        name="p95_decision_latency",
        target=400.0,
        operator="<=",
        metric_name="ark_pass_latency_ms",
        window_seconds=300
    ))
    
    # HRM evaluation: ≤ 120ms
    collector.register_slo(SLOTarget(
        name="hrm_eval_latency",
        target=120.0,
        operator="<=",
        metric_name="hrm_eval_latency_ms",
        window_seconds=300
    ))
    
    # Ethics drift: 0 (immutable)
    # This is implicitly guaranteed by Graveyard 444 permissions
    # We track violations as a counter that should never increment
    
    logger.info("Registered production SLO targets")


# Convenience functions for agent instrumentation

def record_latency(metric_name: str, latency_ms: float, labels: Optional[Dict[str, str]] = None):
    """Record latency observation."""
    collector = get_metrics_collector()
    collector.observe_histogram(metric_name, latency_ms, labels)


def increment_counter(metric_name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
    """Increment counter metric."""
    collector = get_metrics_collector()
    collector.inc_counter(metric_name, value, labels)


def set_gauge(metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Set gauge metric."""
    collector = get_metrics_collector()
    collector.set_gauge(metric_name, value, labels)


def record_trace(trace_id: str, agent_name: str):
    """Record agent participation in trace."""
    collector = get_metrics_collector()
    collector.record_trace_span(trace_id, agent_name)


def validate_trace(trace_id: str, expected_agents: List[str]) -> Dict[str, Any]:
    """Validate trace continuity."""
    collector = get_metrics_collector()
    return collector.validate_trace_continuity(trace_id, expected_agents)


def check_slos() -> Dict[str, Any]:
    """Check all SLO targets."""
    collector = get_metrics_collector()
    return collector.check_slos()


def export_prometheus() -> str:
    """Export metrics in Prometheus format."""
    collector = get_metrics_collector()
    return collector.export_prometheus()


def get_all_metrics() -> Dict[str, Any]:
    """Get all metrics in structured format."""
    collector = get_metrics_collector()
    return collector.get_all_metrics()


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    collector = get_metrics_collector()
    
    # Simulate some metrics
    print("Simulating metrics...")
    
    # Record some latencies
    for i in range(100):
        record_latency("ark_pass_latency_ms", 150 + i * 2)
        record_latency("hrm_eval_latency_ms", 50 + i * 0.5)
    
    # Increment counters
    increment_counter("hrm_denials_total", labels={"rule_id": "max_position_size", "agent": "Kenny"})
    increment_counter("graveyard_validations_total")
    
    # Set gauges
    set_gauge("kyle_ingest_rate", 1.0)
    set_gauge("joey_pattern_confidence_avg", 0.85)
    set_gauge("kenny_exec_success_rate", 0.95)
    
    # Simulate trace continuity
    trace_id = "test-trace-001"
    for agent in ["Kyle", "Joey", "HRM", "Kenny", "Aletheia"]:
        record_trace(trace_id, agent)
        time.sleep(0.05)
    
    continuity = validate_trace(trace_id, ["Kyle", "Joey", "HRM", "Kenny", "Aletheia"])
    print(f"\nTrace continuity: {json.dumps(continuity, indent=2)}")
    
    # Get histogram stats
    stats = collector.get_histogram_stats("ark_pass_latency_ms")
    print(f"\nLatency stats: {json.dumps(stats, indent=2)}")
    
    # Check SLOs
    slo_status = check_slos()
    print(f"\nSLO status: {json.dumps(slo_status, indent=2)}")
    
    # Export Prometheus format
    print("\n--- Prometheus Export ---")
    print(export_prometheus())
