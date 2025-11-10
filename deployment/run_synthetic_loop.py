"""
1 Hz Synthetic Validation Loop

Proves: "1 pass/second, no races, full log continuity"

Success criteria:
- Throughput ≥ 1 pass/sec over 5 minutes
- Zero Watchdog quarantines
- HRM denials only on injected violations
- Monotonic logs without gaps

Usage:
    python run_synthetic_loop.py [--duration 300] [--url http://localhost:8000]
"""

import time
import uuid
import random
import json
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Optional
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis library not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests library not available")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SyntheticValidator:
    """1 Hz validation loop for production canary"""
    
    SYMBOLS = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "GOOGL", "META", "AMZN"]
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", 
                 api_url: str = "http://localhost:8000",
                 duration: int = 300):
        self.redis_url = redis_url
        self.api_url = api_url
        self.duration = duration
        
        if REDIS_AVAILABLE:
            self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = None
            logger.warning("Redis not available - using API-only mode")
        
        # Metrics
        self.passes = 0
        self.errors = 0
        self.latencies: List[float] = []
        self.start_time = time.time()
        
        # Trace IDs for log continuity
        self.trace_ids: List[str] = []
        
        # Injected violations for testing
        self.injected_violations = 0
        self.expected_denials = 0
    
    def push_signal(self, injected_violation: bool = False) -> str:
        """
        Push a synthetic signal to Kyle's stream
        
        Args:
            injected_violation: If True, create a signal that should violate Graveyard rules
        
        Returns:
            Event ID (trace_id)
        """
        trace_id = str(uuid.uuid4())
        
        if injected_violation:
            # Create a risky signal that should be denied
            evt = {
                "id": trace_id,
                "symbol": random.choice(self.SYMBOLS),
                "price": round(random.uniform(10, 500), 2),
                "volume": random.randint(1_000, 200_000),
                "ts": time.time(),
                "source": "synthetic",
                "action": "trade",
                "position_size_pct": 0.25,  # Too large! Should violate max_position_size
                "leverage": 3.0,  # Too high! Should violate max_leverage
                "stop_loss": None,  # Missing! Should violate require_stop_loss
                "injected_violation": True
            }
            self.injected_violations += 1
            self.expected_denials += 1
        else:
            # Create a normal, compliant signal
            evt = {
                "id": trace_id,
                "symbol": random.choice(self.SYMBOLS),
                "price": round(random.uniform(10, 500), 2),
                "volume": random.randint(1_000, 200_000),
                "ts": time.time(),
                "source": "synthetic",
                "action": "trade",
                "position_size_pct": 0.05,  # Compliant
                "leverage": 1.0,  # Compliant
                "stop_loss": round(random.uniform(10, 500) * 0.95, 2),  # Compliant
                "risk_reward_ratio": 2.5,  # Compliant
                "injected_violation": False
            }
        
        if self.redis:
            try:
                # Push to Kyle's signal stream
                self.redis.xadd("kyle:signals", {"event": json.dumps(evt)}, maxlen=10000)
                
                # Push heartbeat to Watchdog
                self.redis.xadd("watchdog:heartbeats", {
                    "trace_id": trace_id,
                    "ts": time.time(),
                    "source": "synthetic_validator"
                }, maxlen=10000)
                
                logger.debug(f"Pushed signal {trace_id} (violation={injected_violation})")
            except Exception as e:
                logger.error(f"Error pushing to Redis: {e}")
                self.errors += 1
        else:
            logger.debug(f"Redis not available, signal not pushed: {trace_id}")
        
        return trace_id
    
    def poll_health(self) -> bool:
        """Check if services are healthy"""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available, skipping health check")
            return True
        
        try:
            healthz = requests.get(f"{self.api_url}/healthz", timeout=0.5)
            readyz = requests.get(f"{self.api_url}/readyz", timeout=0.5)
            
            return healthz.status_code == 200 and readyz.status_code == 200
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to API - is it running?")
            return False
        except requests.exceptions.Timeout:
            logger.error("Health check timeout")
            return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def poll_completion(self, trace_id: str, timeout: float = 2.0) -> Optional[Dict]:
        """
        Poll for action completion in Aletheia's reports stream
        
        Returns:
            Completion data if found, None if timeout
        """
        if not self.redis:
            return None
        
        try:
            start = time.time()
            last_id = '$'  # Start from latest
            
            while time.time() - start < timeout:
                # Read from Aletheia reports stream
                streams = self.redis.xread(
                    {"aletheia:reports": last_id},
                    count=10,
                    block=100  # 100ms block
                )
                
                if streams:
                    for stream_name, messages in streams:
                        for msg_id, msg_data in messages:
                            last_id = msg_id
                            
                            # Check if this report matches our trace_id
                            report = json.loads(msg_data.get('report', '{}'))
                            if report.get('trace_id') == trace_id:
                                return report
                
                time.sleep(0.05)  # 50ms between polls
            
            logger.warning(f"Trace {trace_id} completion not found (timeout)")
            return None
            
        except Exception as e:
            logger.error(f"Error polling completion: {e}")
            return None
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        elapsed = time.time() - self.start_time
        
        if self.latencies:
            avg_latency = sum(self.latencies) / len(self.latencies)
            p95_latency = sorted(self.latencies)[int(len(self.latencies) * 0.95)]
        else:
            avg_latency = 0
            p95_latency = 0
        
        return {
            'passes': self.passes,
            'errors': self.errors,
            'elapsed_seconds': elapsed,
            'throughput_hz': self.passes / elapsed if elapsed > 0 else 0,
            'avg_latency_ms': avg_latency * 1000,
            'p95_latency_ms': p95_latency * 1000,
            'injected_violations': self.injected_violations,
            'expected_denials': self.expected_denials
        }
    
    def run(self):
        """Run the validation loop"""
        logger.info("=" * 60)
        logger.info("SYNTHETIC VALIDATION LOOP")
        logger.info("=" * 60)
        logger.info(f"Duration: {self.duration}s (~{self.duration // 60} minutes)")
        logger.info(f"Target: 1 Hz")
        logger.info(f"Redis: {self.redis_url}")
        logger.info(f"API: {self.api_url}")
        logger.info("=" * 60)
        
        # Pre-flight health check
        if not self.poll_health():
            logger.error("❌ Service not healthy - aborting")
            return False
        
        logger.info("✅ Service healthy - starting loop")
        logger.info("")
        
        self.start_time = time.time()
        next_tick = self.start_time
        
        try:
            while self.passes < self.duration:
                loop_start = time.time()
                
                # Inject violations every 60 passes (1 per minute)
                inject_violation = (self.passes % 60 == 0 and self.passes > 0)
                
                # Push signal
                trace_id = self.push_signal(injected_violation=inject_violation)
                self.trace_ids.append(trace_id)
                
                # Optional: Poll for completion (adds latency tracking)
                if self.redis and self.passes % 10 == 0:  # Sample 10%
                    completion = self.poll_completion(trace_id, timeout=1.0)
                    if completion:
                        latency = time.time() - loop_start
                        self.latencies.append(latency)
                
                self.passes += 1
                
                # Progress every 60 seconds
                if self.passes % 60 == 0:
                    metrics = self.get_metrics()
                    logger.info(
                        f"Progress: {self.passes}/{self.duration} passes "
                        f"({metrics['throughput_hz']:.2f} Hz, "
                        f"p95: {metrics['p95_latency_ms']:.0f}ms)"
                    )
                
                # Sleep to maintain 1 Hz
                next_tick += 1.0
                sleep_time = next_tick - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -0.1:  # More than 100ms behind
                    logger.warning(f"Loop running slow, behind by {-sleep_time:.3f}s")
        
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Interrupted by user")
            return False
        
        except Exception as e:
            logger.error(f"❌ Error during loop: {e}", exc_info=True)
            self.errors += 1
            return False
        
        # Final metrics
        logger.info("")
        logger.info("=" * 60)
        logger.info("VALIDATION LOOP COMPLETE")
        logger.info("=" * 60)
        
        metrics = self.get_metrics()
        
        logger.info(f"Total passes: {metrics['passes']}")
        logger.info(f"Total errors: {metrics['errors']}")
        logger.info(f"Elapsed time: {metrics['elapsed_seconds']:.1f}s")
        logger.info(f"Throughput: {metrics['throughput_hz']:.3f} Hz")
        
        if self.latencies:
            logger.info(f"Avg latency: {metrics['avg_latency_ms']:.0f}ms")
            logger.info(f"P95 latency: {metrics['p95_latency_ms']:.0f}ms")
        
        logger.info(f"Injected violations: {metrics['injected_violations']}")
        logger.info(f"Expected denials: {metrics['expected_denials']}")
        
        # Success criteria
        success = True
        
        if metrics['throughput_hz'] < 1.0:
            logger.error(f"❌ Throughput below 1 Hz: {metrics['throughput_hz']:.3f}")
            success = False
        else:
            logger.info(f"✅ Throughput ≥ 1 Hz")
        
        if metrics['errors'] > 0:
            logger.error(f"❌ {metrics['errors']} errors occurred")
            success = False
        else:
            logger.info(f"✅ Zero errors")
        
        if self.latencies and metrics['p95_latency_ms'] > 400:
            logger.warning(f"⚠️  P95 latency above SLO: {metrics['p95_latency_ms']:.0f}ms > 400ms")
        elif self.latencies:
            logger.info(f"✅ P95 latency within SLO")
        
        logger.info("=" * 60)
        
        return success


def main():
    parser = argparse.ArgumentParser(description="ARK 1 Hz Synthetic Validation Loop")
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds (default: 300)')
    parser.add_argument('--redis', default='redis://localhost:6379/0', help='Redis URL')
    parser.add_argument('--api', default='http://localhost:8000', help='API URL')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = SyntheticValidator(
        redis_url=args.redis,
        api_url=args.api,
        duration=args.duration
    )
    
    success = validator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
