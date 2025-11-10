# ARK Production Deployment

This directory contains all production deployment artifacts, configuration, and operational scripts for the ARK Multi-Agent System.

## Directory Contents

```
deployment/
├── README.md                    # This file
├── config_prod.py              # Production configuration validator
├── run_synthetic_loop.py       # 1 Hz synthetic validation loop
├── start_production.sh         # Production startup orchestration
├── MONITORING_GUIDE.md         # Comprehensive monitoring documentation
└── .env.production             # Production environment template (in parent dir)
```

## Quick Start

### 1. Configure Environment

```bash
# Copy production environment template
cp .env.production.template .env.production

# Edit with actual values
vim .env.production

# IMPORTANT: Replace placeholder secrets!
# - SESSION_SECRET
# - JWT_SECRET
# - ALPACA_API_KEY
# - ALPACA_SECRET_KEY
# - ALPHA_VANTAGE_API_KEY
```

### 2. Validate Configuration

```bash
python3 -m deployment.config_prod validate
```

Expected output:
```
✓ All required environment variables present
✓ Security: All secrets configured (not placeholders)
✓ Directories: /var/lib/ark exists and writable
✓ SQLite WAL mode enabled successfully
✓ Redis: Connected successfully

Production configuration is VALID ✓
```

### 3. Start Production Services

```bash
./deployment/start_production.sh
```

This will:
1. Validate configuration
2. Start metrics server (port 9090)
3. Start Watchdog monitoring
4. Run health checks
5. Execute synthetic validation loop (300s)
6. Display status dashboard

### 4. Monitor System

**Metrics Dashboard:**
```bash
curl http://localhost:9090/metrics
```

**SLO Status:**
```bash
curl http://localhost:9090/slos | jq
```

**System Health:**
```bash
curl http://localhost:9090/healthz | jq
```

## Production Validation

The synthetic validation loop proves system stability with:

- **Throughput:** 1 Hz signal processing
- **Trace Continuity:** Full Kyle→Aletheia pipeline tracking
- **Ethics Enforcement:** Injected violations correctly denied
- **Latency:** p95 ≤ 400ms
- **Zero Errors:** No exceptions or failures

### Running Standalone Validation

```bash
python3 -m deployment.run_synthetic_loop \
    --duration 300 \
    --redis-url redis://localhost:6379/0 \
    --api-url http://localhost:8000
```

Success criteria:
- ✓ Throughput ≥ 1.0 Hz
- ✓ Zero errors
- ✓ p95 latency ≤ 400ms
- ✓ Violations correctly denied

## Monitoring Architecture

### Metrics Collection

```python
from monitoring.metrics import record_latency, increment_counter, set_gauge

# Record latency
record_latency("operation_latency_ms", 125.5, labels={"agent": "Kyle"})

# Increment counter
increment_counter("operations_total", labels={"status": "success"})

# Set gauge
set_gauge("queue_depth", 42)
```

### Agent Instrumentation

```python
from monitoring.instrumentation import instrument_agent_method, with_trace_id

class Kyle(BaseAgent):
    @instrument_agent_method(latency_metric="kyle_process_ms")
    @with_trace_id
    async def process_signal(self, signal: Dict, trace_id: str):
        # Automatically tracked
        return result
```

### SLO Tracking

Default SLOs:
- **Availability:** 99.5% (5-minute window)
- **P95 Latency:** ≤ 400ms
- **HRM Eval:** ≤ 120ms
- **Ethics Drift:** 0 (immutable)

Check status:
```bash
curl http://localhost:9090/slos
```

## Canary Deployment

Start in canary mode (10% traffic, 10-minute monitoring):

```bash
./deployment/start_production.sh --canary
```

### Canary Tripwires

Automatic rollback if:
- HRM denials spike > 3σ baseline
- Watchdog quarantines > 0 in 10 minutes
- p95 latency breach for 3+ consecutive minutes

### Manual Rollback

```bash
# Stop services
pkill -f metrics_server
pkill -f watchdog

# Restore DB snapshot
cp /var/backups/ark/ark_state_backup_*.db /var/lib/ark/ark_state.db

# Restart with previous configuration
git checkout HEAD~1 -- .env.production
./deployment/start_production.sh
```

## Operational Runbooks

### Investigating High Latency

1. **Check metrics:**
   ```bash
   curl http://localhost:9090/metrics/json | jq '.histograms.ark_pass_latency_ms'
   ```

2. **Identify bottleneck:**
   ```bash
   # Check individual agent latencies
   curl http://localhost:9090/metrics | grep '_latency_ms'
   ```

3. **Review trace continuity:**
   ```python
   from monitoring.metrics import validate_trace
   result = validate_trace(trace_id, ["Kyle", "Joey", "HRM", "Kenny", "Aletheia"])
   print(result['missing_agents'])
   ```

### Handling SLO Violations

1. **Identify violation:**
   ```bash
   curl http://localhost:9090/slos | jq '.violations'
   ```

2. **Check root cause:**
   - Availability: Review watchdog quarantines
   - Latency: Check Redis stream depth
   - HRM: Review Graveyard validation performance

3. **Remediation:**
   - Scale resources if needed
   - Review recent changes
   - Check agent logs for errors

### Agent Quarantine Recovery

1. **Identify quarantined agent:**
   ```bash
   curl http://localhost:9090/metrics | grep 'watchdog_quarantines_total'
   ```

2. **Review watchdog logs:**
   ```bash
   tail -f /var/log/ark/watchdog.log
   ```

3. **Manual recovery:**
   ```python
   from monitoring.watchdog import Watchdog
   watchdog = Watchdog()
   await watchdog.release_agent("Kenny")
   ```

## Directory Structure

### Logs

```
/var/log/ark/
├── metrics_server.log    # Metrics HTTP server
├── watchdog.log          # Watchdog monitoring
├── kyle.log             # Kyle agent
├── joey.log             # Joey agent
├── hrm.log              # HRM agent
├── kenny.log            # Kenny agent
└── aletheia.log         # Aletheia agent
```

### Data

```
/var/lib/ark/
├── ark_state.db         # Mutable Core SQLite database
├── ark_state.db-wal     # Write-Ahead Log
└── ark_state.db-shm     # Shared memory file
```

### Backups

```
/var/backups/ark/
├── ark_state_backup_2025-11-10T10:00:00Z.db
├── ark_state_backup_2025-11-10T11:00:00Z.db
└── ...
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
```

### Alerting Rules

Add to `alerts.yml`:

```yaml
groups:
  - name: ark_slo_alerts
    rules:
      - alert: ARKAvailabilityLow
        expr: ark_availability < 0.995
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "ARK availability below SLO"
```

## Environment Variables

### Critical Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ARK_ENV` | Environment identifier | `prod` |
| `ARK_STATE_DB` | State database path | `/var/lib/ark/ark_state.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `METRICS_PORT` | Metrics server port | `9090` |

### Monitoring Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `METRICS_SERVER_ENABLED` | Enable metrics server | `true` |
| `METRICS_RETENTION_SECONDS` | Metric retention window | `3600` |
| `SLO_AVAILABILITY_TARGET` | Availability SLO | `0.995` |
| `SLO_P95_LATENCY_MS` | Latency SLO | `400` |
| `TRACE_ID_ENABLED` | Enable trace tracking | `true` |

### Watchdog Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `WATCHDOG_ENABLED` | Enable monitoring | `true` |
| `WATCHDOG_QUARANTINE_ENABLED` | Auto-quarantine | `true` |
| `WATCHDOG_MAX_LATENCY_MS` | Latency threshold | `5000` |
| `WATCHDOG_MAX_FAILURE_RATE` | Failure rate threshold | `0.20` |

## Security Considerations

### Secrets Management

**DO NOT commit secrets to version control!**

Production secrets should be:
1. Generated with sufficient entropy (32+ characters)
2. Stored in secure secret management (HashiCorp Vault, AWS Secrets Manager)
3. Injected at runtime via environment variables
4. Rotated regularly (quarterly minimum)

### Network Security

- Metrics server binds to `0.0.0.0` (all interfaces)
- **DO NOT expose port 9090 to public internet**
- Use internal load balancer or VPN
- Enable TLS for Prometheus scraping in production

### File Permissions

```bash
# State database: Read/write for service account only
chmod 600 /var/lib/ark/ark_state.db

# Graveyard rules: Read-only (immutable)
chmod 444 /home/user/webapp/graveyard/ethics.py

# Logs: Read/write for service account
chmod 750 /var/log/ark/
```

## Performance Tuning

### High-Throughput Scenarios (>10 Hz)

1. **Increase metric retention:**
   ```bash
   export METRICS_RETENTION_SECONDS=1800  # 30 minutes
   ```

2. **Enable Redis pipelining:**
   ```bash
   export REDIS_POOL_SIZE=50
   ```

3. **Optimize SQLite:**
   ```bash
   export ARK_DB_CHECKPOINT_INTERVAL=60  # More frequent checkpoints
   ```

### Low-Latency Requirements (<100ms p95)

1. **Profile bottlenecks:**
   ```bash
   py-spy top --pid $(cat /var/run/ark/kyle.pid)
   ```

2. **Enable memory mode for state:**
   ```python
   # In mutable_core/state_manager.py
   StateManager(db_path=":memory:")
   ```

3. **Optimize Graveyard validation:**
   - Pre-compile rule matchers
   - Cache validation results

## Troubleshooting

### Metrics Server Won't Start

**Symptom:** `curl http://localhost:9090/healthz` times out

**Investigation:**
```bash
tail -f /var/log/ark/metrics_server.log
```

**Common Causes:**
- Port 9090 already in use
- Missing `aiohttp` dependency
- Permission denied on log directory

**Fix:**
```bash
# Check port
lsof -i :9090

# Install dependencies
pip install aiohttp

# Fix permissions
sudo chown -R $USER /var/log/ark
```

### Synthetic Validation Fails

**Symptom:** `run_synthetic_loop.py` exits with error

**Investigation:**
```bash
python3 -m deployment.run_synthetic_loop --duration 60 --debug
```

**Common Causes:**
- Redis not running
- API server not started
- Rate limiting active

**Fix:**
```bash
# Start Redis
redis-server --daemonize yes

# Check API health
curl http://localhost:8000/healthz
```

### SLO Violations

**Symptom:** `/slos` endpoint shows violations

**Investigation:**
```bash
curl http://localhost:9090/slos | jq '.violations'
```

**Remediation:**
1. Review specific SLO that's violated
2. Check recent deployments or changes
3. Verify no agent quarantines
4. Review application logs
5. Consider scaling if load increased

## Support and Documentation

- **Monitoring Guide:** [MONITORING_GUIDE.md](./MONITORING_GUIDE.md)
- **Graveyard Rules:** [../graveyard/ethics.py](../graveyard/ethics.py)
- **Watchdog Configuration:** [../monitoring/watchdog.py](../monitoring/watchdog.py)
- **State Management:** [../mutable_core/state_manager.py](../mutable_core/state_manager.py)

## Version History

- **1.0.0** (2025-11-10): Initial production release
  - Metrics collection and SLO tracking
  - Synthetic validation loop
  - Watchdog monitoring
  - Graveyard immutable ethics
  - Mutable Core state management
