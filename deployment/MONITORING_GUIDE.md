# ARK Monitoring and Observability Guide

## Overview

The ARK monitoring system provides comprehensive observability for production deployment with:

- **Prometheus-compatible metrics** for real-time monitoring
- **SLO tracking** with automatic violation detection
- **Trace ID continuity** for end-to-end request correlation
- **Thread-safe collectors** for high-throughput operations
- **HTTP endpoints** for metrics exposition

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ARK Agent Pipeline                       │
│                                                              │
│  Kyle → Joey → HRM → Kenny → Aletheia → ID                  │
│    │      │      │      │        │       │                  │
│    └──────┴──────┴──────┴────────┴───────┘                  │
│                     │                                        │
│                     ▼                                        │
│              Instrumentation                                 │
│              (Auto-tracking)                                 │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────┐
            │   MetricsCollector      │
            │  - Counters             │
            │  - Gauges               │
            │  - Histograms           │
            │  - Trace spans          │
            └─────────────┬───────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
     ┌────────────────┐      ┌──────────────┐
     │ SLO Tracker    │      │ HTTP Server  │
     │ - Availability │      │ :9090        │
     │ - Latency      │      │ /metrics     │
     │ - Ethics drift │      │ /slos        │
     └────────────────┘      └──────────────┘
                                     │
                                     ▼
                            ┌────────────────┐
                            │  Prometheus    │
                            │  / Grafana     │
                            └────────────────┘
```

## Core Metrics

### Latency Metrics (Histograms)

| Metric | Description | SLO Target |
|--------|-------------|------------|
| `ark_pass_latency_ms` | End-to-end decision latency | p95 ≤ 400ms |
| `hrm_eval_latency_ms` | HRM ethics evaluation latency | p95 ≤ 120ms |
| `state_write_latency_ms` | State persistence latency | p95 ≤ 50ms |

**Labels:** `trace_id`, `agent`

### Throughput Metrics (Gauges)

| Metric | Description | Target Range |
|--------|-------------|--------------|
| `kyle_ingest_rate` | Signals ingested per second | 0.8-1.2 Hz |
| `joey_pattern_confidence_avg` | Average pattern confidence | > 0.7 |
| `kenny_exec_success_rate` | Execution success percentage | > 95% |

### Counter Metrics

| Metric | Description | Labels |
|--------|-------------|--------|
| `hrm_denials_total` | Ethics denials by HRM | `rule_id`, `agent` |
| `watchdog_quarantines_total` | Agent quarantine events | `agent`, `reason` |
| `graveyard_validations_total` | Total ethics validations | - |
| `agent_heartbeat_failures` | Failed heartbeats | `agent` |

### System Health (Gauges)

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `redis_stream_depth` | Pending messages in stream | > 5000 |

## Service Level Objectives (SLOs)

### Availability: 99.5%

```python
SLOTarget(
    name="availability_995",
    target=0.995,
    operator=">=",
    metric_name="availability",
    window_seconds=300
)
```

**Calculation:**
```
availability = (total_time - downtime) / total_time
downtime = watchdog_quarantines_total * 5s (heuristic)
```

### P95 Decision Latency: ≤ 400ms

```python
SLOTarget(
    name="p95_decision_latency",
    target=400.0,
    operator="<=",
    metric_name="ark_pass_latency_ms",
    window_seconds=300
)
```

**Measured:** Kyle ingestion → Aletheia completion

### HRM Evaluation: ≤ 120ms

```python
SLOTarget(
    name="hrm_eval_latency",
    target=120.0,
    operator="<=",
    metric_name="hrm_eval_latency_ms",
    window_seconds=300
)
```

**Measured:** HRM tool invocation → Graveyard validation complete

### Ethics Drift: 0

**Enforcement:** Graveyard 444 permissions guarantee zero drift
**Monitoring:** Track `graveyard_validations_total` as sanity check

## Trace ID Continuity

Every request through the ARK pipeline is assigned a unique `trace_id` for end-to-end correlation.

### Pipeline Flow

```
1. Kyle receives signal → trace_id = uuid4()
2. Kyle → Joey: trace_id propagated
3. Joey → HRM: trace_id propagated
4. HRM → Kenny: trace_id propagated
5. Kenny → Aletheia: trace_id propagated
6. Aletheia logs final report: trace_id

Metrics collector tracks:
- Which agents processed each trace_id
- Timestamps for each agent
- Total trace latency
- Missing agents (continuity breaks)
```

### Validation

```python
from monitoring.metrics import validate_trace

result = validate_trace(
    trace_id="abc-123",
    expected_agents=["Kyle", "Joey", "HRM", "Kenny", "Aletheia"]
)

# result = {
#     'complete': True/False,
#     'missing_agents': [],
#     'agents_seen': ['Kyle', 'Joey', ...],
#     'latency_ms': 285.3
# }
```

## Agent Instrumentation

### Automatic Instrumentation

Use decorators to automatically track metrics:

```python
from monitoring.instrumentation import (
    instrument_agent_method,
    with_trace_id
)

class Kyle(BaseAgent):
    @instrument_agent_method(
        latency_metric="kyle_process_latency_ms",
        counter_metric="kyle_signals_processed_total"
    )
    @with_trace_id
    async def process_signal(self, signal: Dict, trace_id: str):
        # Latency, throughput, and trace automatically tracked
        self.logger.info(f"Processing signal {trace_id}")
        return result
```

### Manual Instrumentation

For fine-grained control:

```python
from monitoring.metrics import (
    record_latency,
    increment_counter,
    set_gauge,
    record_trace
)
import time

# Record latency
start = time.time()
result = await process()
latency_ms = (time.time() - start) * 1000
record_latency("custom_operation_ms", latency_ms, labels={"agent": "Kyle"})

# Increment counter
increment_counter("operations_total", labels={"status": "success"})

# Set gauge
set_gauge("queue_depth", 42)

# Track trace
record_trace(trace_id, "Kyle")
```

### Context Manager

For automatic error tracking:

```python
from monitoring.instrumentation import MetricsContext

async with MetricsContext(
    operation_name="kyle_signal_ingestion",
    agent_name="Kyle",
    trace_id=trace_id
) as ctx:
    result = await ingest_signal(signal)
    ctx.set_result(result)

# Latency and success/failure automatically recorded
```

## HTTP Endpoints

### Metrics Server

Start the metrics server:

```bash
cd /home/user/webapp
python -m monitoring.metrics_server
```

Or with custom port:

```bash
export METRICS_PORT=9091
python -m monitoring.metrics_server
```

### Endpoints

#### GET /metrics

Prometheus text format exposition:

```bash
curl http://localhost:9090/metrics
```

```
ark_pass_latency_ms_bucket{le="100"} 45
ark_pass_latency_ms_bucket{le="200"} 78
ark_pass_latency_ms_bucket{le="400"} 95
ark_pass_latency_ms_sum 28530.5
ark_pass_latency_ms_count 100

kyle_ingest_rate 1.02
joey_pattern_confidence_avg 0.85
kenny_exec_success_rate 0.97

hrm_denials_total{rule_id="max_position_size",agent="Kenny"} 3
watchdog_quarantines_total{agent="Kenny",reason="high_failure_rate"} 1
```

#### GET /metrics/json

Structured JSON format:

```bash
curl http://localhost:9090/metrics/json
```

```json
{
  "counters": {
    "hrm_denials_total{rule_id=max_position_size,agent=Kenny}": 3
  },
  "gauges": {
    "kyle_ingest_rate": 1.02,
    "joey_pattern_confidence_avg": 0.85
  },
  "histograms": {
    "ark_pass_latency_ms": {
      "count": 100,
      "sum": 28530.5,
      "avg": 285.3,
      "p50": 275.0,
      "p95": 395.0,
      "p99": 410.0
    }
  },
  "timestamp": 1699632000.123
}
```

#### GET /slos

Current SLO status:

```bash
curl http://localhost:9090/slos
```

```json
{
  "slos": [
    {
      "name": "availability_995",
      "met": true,
      "current_value": 0.998,
      "target": 0.995,
      "operator": ">="
    },
    {
      "name": "p95_decision_latency",
      "met": true,
      "current_value": 385.0,
      "target": 400.0,
      "operator": "<="
    }
  ],
  "total": 4,
  "met": 3,
  "violated": 1,
  "violations": [
    {
      "name": "hrm_eval_latency",
      "met": false,
      "current_value": 135.0,
      "target": 120.0,
      "operator": "<="
    }
  ]
}
```

#### GET /healthz

Health check:

```bash
curl http://localhost:9090/healthz
```

```json
{
  "status": "healthy",
  "timestamp": 1699632000.123,
  "metrics_count": 42
}
```

#### GET /readyz

Readiness check:

```bash
curl http://localhost:9090/readyz
```

```json
{
  "status": "ready",
  "timestamp": 1699632000.123
}
```

## Prometheus Integration

### Scrape Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ark-metrics'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9090']
        labels:
          environment: 'production'
          service: 'ark-multi-agent'
```

### Recording Rules

Create `ark_rules.yml`:

```yaml
groups:
  - name: ark_slo_rules
    interval: 30s
    rules:
      # Availability
      - record: ark:availability:5m
        expr: |
          (1 - (rate(watchdog_quarantines_total[5m]) * 5 / 300))
      
      # P95 latency
      - record: ark:latency:p95:5m
        expr: |
          histogram_quantile(0.95, 
            rate(ark_pass_latency_ms_bucket[5m]))
      
      # SLO compliance
      - record: ark:slo:availability:met
        expr: |
          ark:availability:5m >= 0.995
      
      - record: ark:slo:latency:met
        expr: |
          ark:latency:p95:5m <= 400
```

### Alerting Rules

Create `ark_alerts.yml`:

```yaml
groups:
  - name: ark_alerts
    rules:
      # SLO violations
      - alert: AvailabilitySLOViolation
        expr: ark:availability:5m < 0.995
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "ARK availability below 99.5% SLO"
          description: "Current: {{ $value | humanizePercentage }}"
      
      - alert: LatencySLOViolation
        expr: ark:latency:p95:5m > 400
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "ARK p95 latency exceeds 400ms"
          description: "Current: {{ $value }}ms"
      
      # Agent health
      - alert: AgentQuarantined
        expr: increase(watchdog_quarantines_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Agent quarantined by Watchdog"
          description: "Agent {{ $labels.agent }}: {{ $labels.reason }}"
      
      # Ethics violations
      - alert: EthicsViolationSpike
        expr: rate(hrm_denials_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High rate of ethics violations"
          description: "Rate: {{ $value }}/sec, Rule: {{ $labels.rule_id }}"
```

## Grafana Dashboards

### ARK Overview Dashboard

```json
{
  "dashboard": {
    "title": "ARK Multi-Agent System",
    "panels": [
      {
        "title": "System Health",
        "targets": [
          {
            "expr": "ark:availability:5m",
            "legendFormat": "Availability"
          }
        ],
        "thresholds": [
          {"value": 0.995, "color": "red"},
          {"value": 0.999, "color": "green"}
        ]
      },
      {
        "title": "Decision Latency (p95)",
        "targets": [
          {
            "expr": "ark:latency:p95:5m",
            "legendFormat": "P95 Latency"
          }
        ],
        "thresholds": [
          {"value": 400, "color": "red"}
        ]
      },
      {
        "title": "Throughput",
        "targets": [
          {
            "expr": "kyle_ingest_rate",
            "legendFormat": "Kyle Ingestion"
          }
        ]
      },
      {
        "title": "Ethics Denials by Rule",
        "targets": [
          {
            "expr": "rate(hrm_denials_total[5m])",
            "legendFormat": "{{rule_id}}"
          }
        ]
      }
    ]
  }
}
```

## Production Deployment Checklist

### Pre-Deployment

- [ ] Metrics server starts successfully on port 9090
- [ ] All metrics endpoints respond (GET /metrics, /slos, /healthz)
- [ ] SLO targets registered correctly
- [ ] Prometheus scrape configuration updated
- [ ] Grafana dashboards imported
- [ ] Alert rules configured and tested
- [ ] Log aggregation includes trace_id field

### During Deployment

- [ ] Synthetic validation loop shows 1 Hz throughput
- [ ] Trace continuity validation passes for all agents
- [ ] All SLOs met during warm-up period (5 minutes)
- [ ] No unexpected ethics denials
- [ ] No agent quarantines

### Post-Deployment

- [ ] Continuous SLO compliance for 30 minutes
- [ ] Prometheus scraping successfully (check /targets)
- [ ] Grafana dashboards display live data
- [ ] Alert routes tested (send test alert)
- [ ] Runbook procedures documented and accessible

## Troubleshooting

### High Latency

**Symptom:** `ark_pass_latency_ms` p95 > 400ms

**Investigation:**
1. Check individual agent latencies:
   ```promql
   histogram_quantile(0.95, 
     rate(hrm_eval_latency_ms_bucket[5m]))
   ```
2. Check Redis stream depth:
   ```promql
   redis_stream_depth
   ```
3. Review trace continuity for stuck traces:
   ```python
   validate_trace(trace_id, expected_agents)
   ```

**Remediation:**
- Scale Redis if stream depth > 5000
- Check HRM Graveyard validation performance
- Review SQLite WAL checkpoint frequency

### SLO Violations

**Symptom:** `check_slos()` returns violations

**Investigation:**
```bash
curl http://localhost:9090/slos | jq '.violations'
```

**Remediation:**
- Review specific SLO violation details
- Check for agent quarantines
- Verify no configuration drift
- Review recent deployments/changes

### Missing Trace Spans

**Symptom:** `validate_trace()` shows incomplete traces

**Investigation:**
1. Check which agents are missing:
   ```python
   result = validate_trace(trace_id, expected_agents)
   print(result['missing_agents'])
   ```
2. Check agent heartbeats:
   ```promql
   increase(agent_heartbeat_failures[5m])
   ```

**Remediation:**
- Verify all agents running
- Check Redis pub/sub connectivity
- Review agent error logs for exceptions

### Metrics Not Updating

**Symptom:** `/metrics` endpoint returns stale data

**Investigation:**
```bash
curl http://localhost:9090/healthz
```

**Remediation:**
- Restart metrics server
- Verify agent instrumentation decorators applied
- Check for threading issues in metrics collector

## Performance Tuning

### High-Throughput Scenarios

For throughput > 10 Hz:

1. **Increase histogram retention:**
   ```python
   MetricsCollector(retention_seconds=1800)  # 30 minutes
   ```

2. **Enable batch updates:**
   ```python
   # Record multiple observations at once
   for value in batch_values:
       collector.observe_histogram("metric", value)
   ```

3. **Use sampling for trace validation:**
   ```python
   # Only validate 10% of traces
   if random.random() < 0.1:
       validate_trace(trace_id, expected_agents)
   ```

### Low-Latency Requirements

For p95 < 100ms target:

1. **Optimize Graveyard validation**
2. **Enable SQLite memory mode for Mutable Core**
3. **Use Redis pipelining for bulk operations**
4. **Profile agent code paths with py-spy**

## References

- Prometheus Text Format: https://prometheus.io/docs/instrumenting/exposition_formats/
- SLO Best Practices: https://sre.google/workbook/implementing-slos/
- Distributed Tracing: https://opentelemetry.io/docs/concepts/signals/traces/
