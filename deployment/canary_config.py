"""
ARK Canary Deployment Configuration

Implements controlled rollout with automatic tripwires and rollback.

Canary Strategy:
- Route 10% of traffic to canary deployment
- Monitor for 10 minutes with tripwires
- Automatic rollback if tripwires triggered
- Gradual ramp if successful (10% → 25% → 50% → 100%)

Tripwires:
1. HRM denials spike >3σ baseline
2. Watchdog quarantine count >0 in 10 minutes
3. P95 latency breach for 3+ consecutive minutes

Author: ARK System
Created: 2025-11-10
"""

import time
import logging
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CanaryConfig:
    """Canary deployment configuration"""
    
    # Traffic routing
    canary_percentage: int = 10  # Start with 10%
    ramp_intervals: List[int] = field(default_factory=lambda: [10, 25, 50, 100])
    ramp_duration_minutes: int = 10  # Duration at each percentage
    
    # Monitoring
    monitoring_interval_seconds: int = 30  # Check tripwires every 30s
    baseline_window_minutes: int = 60  # Use 1 hour baseline
    
    # Tripwires
    hrm_denials_sigma_threshold: float = 3.0  # >3σ triggers rollback
    watchdog_quarantine_max: int = 0  # Any quarantine triggers rollback
    latency_breach_threshold_ms: float = 400.0  # P95 latency threshold
    latency_breach_consecutive_checks: int = 6  # 3 minutes (6 × 30s)
    
    # Rollback
    auto_rollback_enabled: bool = True
    rollback_to_version: str = "stable"
    
    # Metadata
    deployment_id: str = ""
    started_at: Optional[datetime] = None
    canary_version: str = "canary"


@dataclass
class TripwireStatus:
    """Status of canary deployment tripwires"""
    
    # HRM denials tripwire
    hrm_denials_triggered: bool = False
    hrm_denials_baseline_mean: float = 0.0
    hrm_denials_baseline_stddev: float = 0.0
    hrm_denials_canary_rate: float = 0.0
    hrm_denials_sigma: float = 0.0
    
    # Watchdog quarantine tripwire
    watchdog_quarantine_triggered: bool = False
    watchdog_quarantine_count: int = 0
    
    # Latency tripwire
    latency_breach_triggered: bool = False
    latency_p95_current: float = 0.0
    latency_breach_consecutive: int = 0
    
    # Overall status
    any_triggered: bool = False
    triggered_reasons: List[str] = field(default_factory=list)
    
    def update_overall_status(self):
        """Update overall status based on individual tripwires"""
        self.any_triggered = (
            self.hrm_denials_triggered or
            self.watchdog_quarantine_triggered or
            self.latency_breach_triggered
        )
        
        self.triggered_reasons = []
        if self.hrm_denials_triggered:
            self.triggered_reasons.append(
                f"HRM denials spike: {self.hrm_denials_sigma:.2f}σ above baseline"
            )
        if self.watchdog_quarantine_triggered:
            self.triggered_reasons.append(
                f"Watchdog quarantine: {self.watchdog_quarantine_count} events"
            )
        if self.latency_breach_triggered:
            self.triggered_reasons.append(
                f"Latency breach: {self.latency_p95_current:.2f}ms for {self.latency_breach_consecutive} checks"
            )


class CanaryDeployment:
    """
    Manages canary deployment with automatic tripwire monitoring.
    
    Workflow:
    1. Deploy canary version alongside stable
    2. Route configured percentage to canary
    3. Monitor tripwires continuously
    4. Auto-rollback if tripwires triggered
    5. Gradual ramp if successful
    """
    
    def __init__(self, config: CanaryConfig, metrics_collector=None):
        """
        Initialize canary deployment manager.
        
        Args:
            config: Canary configuration
            metrics_collector: Optional metrics collector for monitoring
        """
        self.config = config
        self.metrics_collector = metrics_collector
        
        # State
        self.current_percentage = config.canary_percentage
        self.started_at = datetime.utcnow()
        self.status = TripwireStatus()
        
        # Baseline data
        self.baseline_hrm_denials: List[float] = []
        self.latency_breach_count = 0
        
        # Deployment state
        self.is_active = False
        self.is_rolled_back = False
        self.rollback_reason = None
        
        logger.info(f"CanaryDeployment initialized: {config.canary_percentage}% traffic")
    
    
    def start(self):
        """Start canary deployment"""
        self.is_active = True
        self.started_at = datetime.utcnow()
        self.config.started_at = self.started_at
        
        logger.info(f"Canary deployment started at {self.started_at}")
        logger.info(f"Initial traffic: {self.current_percentage}%")
        logger.info(f"Monitoring for tripwires every {self.config.monitoring_interval_seconds}s")
    
    
    def collect_baseline_metrics(self) -> Dict[str, Any]:
        """
        Collect baseline metrics from stable deployment.
        
        Returns:
            Baseline metrics dictionary
        """
        logger.info("Collecting baseline metrics from stable deployment...")
        
        if not self.metrics_collector:
            logger.warning("No metrics collector - using mock baseline")
            return {
                'hrm_denials_rate': 0.02,  # 0.02/sec baseline
                'hrm_denials_samples': [0.015, 0.020, 0.025, 0.018, 0.022]
            }
        
        # Get HRM denials rate over baseline window
        # This would query Prometheus or metrics collector
        baseline_data = self._query_baseline_hrm_denials()
        
        self.baseline_hrm_denials = baseline_data
        
        if len(baseline_data) > 1:
            mean = statistics.mean(baseline_data)
            stddev = statistics.stdev(baseline_data)
        else:
            mean = baseline_data[0] if baseline_data else 0.0
            stddev = 0.0
        
        self.status.hrm_denials_baseline_mean = mean
        self.status.hrm_denials_baseline_stddev = stddev
        
        logger.info(f"Baseline HRM denials: μ={mean:.4f}, σ={stddev:.4f}")
        
        return {
            'hrm_denials_mean': mean,
            'hrm_denials_stddev': stddev,
            'samples': len(baseline_data)
        }
    
    
    def check_tripwires(self) -> TripwireStatus:
        """
        Check all canary tripwires.
        
        Returns:
            TripwireStatus with current state
        """
        logger.debug("Checking canary tripwires...")
        
        # 1. Check HRM denials spike
        self._check_hrm_denials_tripwire()
        
        # 2. Check Watchdog quarantines
        self._check_watchdog_tripwire()
        
        # 3. Check latency breach
        self._check_latency_tripwire()
        
        # Update overall status
        self.status.update_overall_status()
        
        if self.status.any_triggered:
            logger.warning(f"Tripwires triggered: {self.status.triggered_reasons}")
        else:
            logger.debug("All tripwires OK")
        
        return self.status
    
    
    def _check_hrm_denials_tripwire(self):
        """Check if HRM denials spiked in canary"""
        # Get current canary HRM denial rate
        canary_rate = self._query_canary_hrm_denials()
        
        self.status.hrm_denials_canary_rate = canary_rate
        
        # Calculate sigma deviation
        if self.status.hrm_denials_baseline_stddev > 0:
            sigma = (
                (canary_rate - self.status.hrm_denials_baseline_mean) /
                self.status.hrm_denials_baseline_stddev
            )
        else:
            sigma = 0.0
        
        self.status.hrm_denials_sigma = sigma
        
        # Check threshold
        if sigma > self.config.hrm_denials_sigma_threshold:
            self.status.hrm_denials_triggered = True
            logger.warning(
                f"HRM denials tripwire triggered: {sigma:.2f}σ > "
                f"{self.config.hrm_denials_sigma_threshold}σ threshold"
            )
    
    
    def _check_watchdog_tripwire(self):
        """Check if Watchdog quarantined any agents in canary"""
        # Get quarantine count for canary deployment
        quarantine_count = self._query_watchdog_quarantines()
        
        self.status.watchdog_quarantine_count = quarantine_count
        
        # Check threshold
        if quarantine_count > self.config.watchdog_quarantine_max:
            self.status.watchdog_quarantine_triggered = True
            logger.warning(
                f"Watchdog quarantine tripwire triggered: {quarantine_count} events > "
                f"{self.config.watchdog_quarantine_max} threshold"
            )
    
    
    def _check_latency_tripwire(self):
        """Check if P95 latency breached threshold consecutively"""
        # Get current P95 latency
        p95_latency = self._query_p95_latency()
        
        self.status.latency_p95_current = p95_latency
        
        # Check if breached
        if p95_latency > self.config.latency_breach_threshold_ms:
            self.latency_breach_count += 1
            logger.warning(
                f"Latency breach detected: {p95_latency:.2f}ms > "
                f"{self.config.latency_breach_threshold_ms}ms "
                f"(consecutive: {self.latency_breach_count})"
            )
        else:
            # Reset counter if latency is OK
            self.latency_breach_count = 0
        
        self.status.latency_breach_consecutive = self.latency_breach_count
        
        # Check threshold
        if self.latency_breach_count >= self.config.latency_breach_consecutive_checks:
            self.status.latency_breach_triggered = True
            logger.error(
                f"Latency tripwire triggered: {self.latency_breach_count} consecutive breaches"
            )
    
    
    def rollback(self, reason: str):
        """
        Execute rollback to stable deployment.
        
        Args:
            reason: Reason for rollback
        """
        if self.is_rolled_back:
            logger.warning("Already rolled back, skipping")
            return
        
        logger.error(f"ROLLBACK TRIGGERED: {reason}")
        
        self.is_rolled_back = True
        self.rollback_reason = reason
        self.is_active = False
        
        # Execute rollback steps
        self._execute_rollback()
        
        logger.info("Rollback complete")
    
    
    def _execute_rollback(self):
        """Execute rollback procedures"""
        logger.info("Executing rollback procedures...")
        
        # 1. Route 100% traffic to stable
        logger.info("Routing 100% traffic to stable deployment")
        self._update_traffic_routing(canary_percentage=0, stable_percentage=100)
        
        # 2. Stop canary containers
        logger.info("Stopping canary containers")
        # This would call docker-compose down for canary
        
        # 3. Restore database if needed
        # This would be handled by rollback automation (Task 6)
        
        # 4. Clear canary metrics
        logger.info("Clearing canary metrics")
        
        # 5. Send rollback alert
        logger.info("Sending rollback alert")
        self._send_rollback_alert()
    
    
    def ramp_traffic(self, new_percentage: int):
        """
        Ramp traffic to canary deployment.
        
        Args:
            new_percentage: New percentage for canary (0-100)
        """
        if not self.is_active:
            logger.error("Cannot ramp - deployment not active")
            return
        
        if self.is_rolled_back:
            logger.error("Cannot ramp - deployment rolled back")
            return
        
        old_percentage = self.current_percentage
        self.current_percentage = new_percentage
        
        logger.info(f"Ramping traffic: {old_percentage}% → {new_percentage}%")
        
        # Update traffic routing
        self._update_traffic_routing(
            canary_percentage=new_percentage,
            stable_percentage=100 - new_percentage
        )
    
    
    def monitor(self, duration_minutes: int = 10) -> bool:
        """
        Monitor canary deployment for specified duration.
        
        Args:
            duration_minutes: How long to monitor
        
        Returns:
            True if successful (no tripwires), False if rolled back
        """
        logger.info(f"Monitoring canary for {duration_minutes} minutes...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        check_count = 0
        
        while time.time() < end_time:
            check_count += 1
            elapsed_minutes = (time.time() - start_time) / 60
            
            logger.info(
                f"Check {check_count} at {elapsed_minutes:.1f} minutes "
                f"({self.current_percentage}% canary traffic)"
            )
            
            # Check tripwires
            status = self.check_tripwires()
            
            if status.any_triggered and self.config.auto_rollback_enabled:
                reason = "; ".join(status.triggered_reasons)
                self.rollback(reason)
                return False
            
            # Wait for next check
            time.sleep(self.config.monitoring_interval_seconds)
        
        logger.info(f"Monitoring complete - {check_count} checks, all clear")
        return True
    
    
    def execute_gradual_rollout(self) -> bool:
        """
        Execute full gradual rollout: 10% → 25% → 50% → 100%
        
        Returns:
            True if successful, False if rolled back
        """
        logger.info("Starting gradual rollout...")
        
        # Collect baseline first
        self.collect_baseline_metrics()
        
        # Start deployment
        self.start()
        
        # Iterate through ramp intervals
        for percentage in self.config.ramp_intervals:
            logger.info(f"=== Ramping to {percentage}% ===")
            
            # Ramp traffic
            self.ramp_traffic(percentage)
            
            # Monitor at this level
            success = self.monitor(self.config.ramp_duration_minutes)
            
            if not success:
                logger.error(f"Rollout failed at {percentage}%")
                return False
            
            logger.info(f"✅ {percentage}% successful")
        
        logger.info("🎉 Gradual rollout complete - canary is now production")
        return True
    
    
    # Query methods (would integrate with actual metrics)
    
    def _query_baseline_hrm_denials(self) -> List[float]:
        """Query baseline HRM denial rates"""
        # Mock implementation - would query Prometheus
        # Example: rate(hrm_denials_total{deployment="stable"}[5m])
        return [0.015, 0.020, 0.025, 0.018, 0.022, 0.019, 0.021]
    
    
    def _query_canary_hrm_denials(self) -> float:
        """Query current canary HRM denial rate"""
        # Mock implementation - would query Prometheus
        # Example: rate(hrm_denials_total{deployment="canary"}[5m])
        return 0.020  # Normal rate
    
    
    def _query_watchdog_quarantines(self) -> int:
        """Query Watchdog quarantine count for canary"""
        # Mock implementation - would query Prometheus
        # Example: increase(watchdog_quarantines_total{deployment="canary"}[10m])
        return 0  # No quarantines
    
    
    def _query_p95_latency(self) -> float:
        """Query P95 latency for canary"""
        # Mock implementation - would query Prometheus
        # Example: histogram_quantile(0.95, rate(ark_pass_latency_ms_bucket{deployment="canary"}[5m]))
        return 285.0  # Normal latency
    
    
    def _update_traffic_routing(self, canary_percentage: int, stable_percentage: int):
        """Update traffic routing configuration"""
        logger.info(f"Traffic routing: {stable_percentage}% stable, {canary_percentage}% canary")
        # This would update load balancer, ingress, or service mesh configuration
    
    
    def _send_rollback_alert(self):
        """Send alert about rollback"""
        logger.info("Sending rollback alert to notification channels")
        # This would send to Slack, PagerDuty, etc.
    
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current deployment status.
        
        Returns:
            Status dictionary
        """
        return {
            'is_active': self.is_active,
            'is_rolled_back': self.is_rolled_back,
            'rollback_reason': self.rollback_reason,
            'current_percentage': self.current_percentage,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'uptime_minutes': (
                (datetime.utcnow() - self.started_at).total_seconds() / 60
                if self.started_at else 0
            ),
            'tripwires': {
                'hrm_denials': {
                    'triggered': self.status.hrm_denials_triggered,
                    'sigma': self.status.hrm_denials_sigma,
                    'canary_rate': self.status.hrm_denials_canary_rate,
                    'baseline_mean': self.status.hrm_denials_baseline_mean
                },
                'watchdog_quarantine': {
                    'triggered': self.status.watchdog_quarantine_triggered,
                    'count': self.status.watchdog_quarantine_count
                },
                'latency': {
                    'triggered': self.status.latency_breach_triggered,
                    'p95_current': self.status.latency_p95_current,
                    'consecutive_breaches': self.status.latency_breach_consecutive
                }
            }
        }


if __name__ == "__main__":
    # Demo canary deployment
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    # Create configuration
    config = CanaryConfig(
        canary_percentage=10,
        ramp_intervals=[10, 25, 50, 100],
        ramp_duration_minutes=2,  # Short for demo
        monitoring_interval_seconds=10  # Frequent checks for demo
    )
    
    # Create deployment
    deployment = CanaryDeployment(config)
    
    # Execute gradual rollout
    print("\n" + "="*80)
    print("DEMO: Canary Deployment with Gradual Rollout")
    print("="*80 + "\n")
    
    success = deployment.execute_gradual_rollout()
    
    print("\n" + "="*80)
    if success:
        print("✅ DEPLOYMENT SUCCESSFUL")
    else:
        print("❌ DEPLOYMENT ROLLED BACK")
    print("="*80 + "\n")
    
    # Show final status
    import json
    status = deployment.get_status()
    print("Final Status:")
    print(json.dumps(status, indent=2))
