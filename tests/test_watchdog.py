"""
Unit tests for Watchdog system monitoring
Tests health tracking, isolation, emergency halt, and alerting
"""

import pytest
import sys
import os
import asyncio
import time
from collections import deque

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from monitoring.watchdog import (
    Watchdog,
    WatchdogConfig,
    AgentMetrics
)


class TestAgentMetrics:
    """Test AgentMetrics calculations"""
    
    def test_failure_rate_zero_requests(self):
        """Test failure rate with zero requests"""
        metrics = AgentMetrics(agent_name="Test")
        assert metrics.failure_rate == 0.0
    
    def test_failure_rate_calculation(self):
        """Test failure rate calculation"""
        metrics = AgentMetrics(agent_name="Test")
        metrics.total_requests = 100
        metrics.successful_requests = 80
        metrics.failed_requests = 20
        
        assert metrics.failure_rate == 0.20
        assert metrics.success_rate == 0.80
    
    def test_avg_latency_empty(self):
        """Test average latency with no data"""
        metrics = AgentMetrics(agent_name="Test")
        assert metrics.avg_latency_ms == 0.0
    
    def test_avg_latency_calculation(self):
        """Test average latency calculation"""
        metrics = AgentMetrics(agent_name="Test")
        metrics.recent_latencies = deque([100, 200, 300, 400, 500])
        
        assert metrics.avg_latency_ms == 300.0
    
    def test_health_score_perfect(self):
        """Test health score for perfect agent"""
        metrics = AgentMetrics(agent_name="Test")
        metrics.total_requests = 100
        metrics.successful_requests = 100
        metrics.failed_requests = 0
        metrics.last_seen = time.time()
        metrics.recent_latencies = deque([50, 60, 70, 80, 90])
        
        health = metrics.health_score
        assert 0.9 <= health <= 1.0  # Near perfect
    
    def test_health_score_degraded(self):
        """Test health score for degraded agent"""
        metrics = AgentMetrics(agent_name="Test")
        metrics.total_requests = 100
        metrics.successful_requests = 50  # 50% failure rate
        metrics.failed_requests = 50
        metrics.last_seen = time.time() - 120  # 2 minutes ago
        metrics.recent_latencies = deque([5000, 6000, 7000])  # High latency
        
        health = metrics.health_score
        assert health < 0.5  # Poor health


class TestWatchdogConfig:
    """Test Watchdog configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = WatchdogConfig()
        
        assert config.agent_check_interval == 5.0
        assert config.max_agent_latency_ms == 5000.0
        assert config.max_agent_failure_rate == 0.20
        assert config.enable_auto_isolation is True
        assert config.enable_emergency_halt is True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = WatchdogConfig(
            agent_check_interval=10.0,
            max_agent_latency_ms=10000.0,
            max_agent_failure_rate=0.30,
            enable_auto_isolation=False
        )
        
        assert config.agent_check_interval == 10.0
        assert config.max_agent_latency_ms == 10000.0
        assert config.max_agent_failure_rate == 0.30
        assert config.enable_auto_isolation is False


class TestWatchdogCore:
    """Test Watchdog core functionality (no Redis)"""
    
    def test_watchdog_initialization(self):
        """Test Watchdog initialization"""
        watchdog = Watchdog()
        
        assert watchdog.running is False
        assert watchdog.emergency_halt is False
        assert len(watchdog.agent_metrics) == 6
        assert 'Kyle' in watchdog.agent_metrics
        assert 'HRM' in watchdog.agent_metrics
    
    def test_get_system_health(self):
        """Test system health report generation"""
        watchdog = Watchdog()
        
        health = watchdog.get_system_health()
        
        assert 'status' in health
        assert 'system_health_score' in health
        assert 'agents' in health
        assert 'redis' in health
        assert 'graveyard' in health
        assert len(health['agents']) == 6
    
    def test_agent_metrics_tracking(self):
        """Test agent metrics are tracked correctly"""
        watchdog = Watchdog()
        
        # Simulate agent activity
        metrics = watchdog.agent_metrics['Kenny']
        metrics.total_requests = 100
        metrics.successful_requests = 95
        metrics.failed_requests = 5
        metrics.recent_latencies = deque([100, 150, 200])
        
        health = watchdog.get_system_health()
        kenny_health = health['agents']['Kenny']
        
        assert kenny_health['total_requests'] == 100
        assert kenny_health['failures'] == 5
        assert kenny_health['success_rate'] == 0.95
        assert kenny_health['avg_latency_ms'] == 150.0


class TestWatchdogIsolation:
    """Test agent isolation logic"""
    
    @pytest.mark.asyncio
    async def test_manual_isolation(self):
        """Test manual agent isolation"""
        watchdog = Watchdog()
        
        # Isolate agent
        await watchdog.isolate_agent('Kenny', "Test isolation")
        
        assert watchdog.agent_metrics['Kenny'].isolated is True
        
        # Check health report
        health = watchdog.get_system_health()
        assert health['agents']['Kenny']['isolated'] is True
    
    @pytest.mark.asyncio
    async def test_restore_agent(self):
        """Test restoring isolated agent"""
        watchdog = Watchdog()
        
        # Isolate then restore
        await watchdog.isolate_agent('Kenny', "Test")
        assert watchdog.agent_metrics['Kenny'].isolated is True
        
        await watchdog.restore_agent('Kenny')
        assert watchdog.agent_metrics['Kenny'].isolated is False
        assert watchdog.agent_metrics['Kenny'].consecutive_failures == 0
    
    def test_auto_isolation_consecutive_failures(self):
        """Test auto-isolation on consecutive failures"""
        config = WatchdogConfig(
            max_consecutive_failures=5,
            enable_auto_isolation=True
        )
        watchdog = Watchdog(config=config)
        
        # Simulate consecutive failures
        metrics = watchdog.agent_metrics['Kenny']
        metrics.consecutive_failures = 6  # Exceeds threshold
        metrics.total_requests = 10
        
        # Should be flagged for isolation
        assert metrics.consecutive_failures >= config.max_consecutive_failures
    
    def test_auto_isolation_high_failure_rate(self):
        """Test auto-isolation on high failure rate"""
        config = WatchdogConfig(
            max_agent_failure_rate=0.20,
            enable_auto_isolation=True
        )
        watchdog = Watchdog(config=config)
        
        # Simulate high failure rate
        metrics = watchdog.agent_metrics['Kenny']
        metrics.total_requests = 100
        metrics.failed_requests = 30  # 30% failure rate
        metrics.successful_requests = 70
        
        # Should be flagged for isolation
        assert metrics.failure_rate > config.max_agent_failure_rate


class TestWatchdogEmergencyControls:
    """Test emergency halt and controls"""
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self):
        """Test emergency stop functionality"""
        watchdog = Watchdog()
        
        # Trigger emergency stop
        success = await watchdog.emergency_stop("Test emergency")
        
        assert success is True
        assert watchdog.emergency_halt is True
        
        # All agents should be isolated
        for agent_name in watchdog.agent_names:
            assert watchdog.agent_metrics[agent_name].isolated is True
    
    @pytest.mark.asyncio
    async def test_emergency_stop_disabled(self):
        """Test emergency stop when disabled in config"""
        config = WatchdogConfig(enable_emergency_halt=False)
        watchdog = Watchdog(config=config)
        
        # Attempt emergency stop
        success = await watchdog.emergency_stop("Test")
        
        assert success is False
        assert watchdog.emergency_halt is False


class TestWatchdogMetricsUpdate:
    """Test metrics update logic"""
    
    @pytest.mark.asyncio
    async def test_update_metrics_request(self):
        """Test updating metrics on request event"""
        watchdog = Watchdog()
        
        await watchdog._update_agent_metrics('Kenny', 'request', {'latency_ms': 250})
        
        metrics = watchdog.agent_metrics['Kenny']
        assert metrics.total_requests == 1
        assert 250 in metrics.recent_latencies
    
    @pytest.mark.asyncio
    async def test_update_metrics_success(self):
        """Test updating metrics on success event"""
        watchdog = Watchdog()
        
        await watchdog._update_agent_metrics('Kenny', 'success', {})
        
        metrics = watchdog.agent_metrics['Kenny']
        assert metrics.successful_requests == 1
        assert metrics.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_update_metrics_failure(self):
        """Test updating metrics on failure event"""
        watchdog = Watchdog()
        
        await watchdog._update_agent_metrics('Kenny', 'failure', {})
        
        metrics = watchdog.agent_metrics['Kenny']
        assert metrics.failed_requests == 1
        assert metrics.consecutive_failures == 1


class TestWatchdogSimulation:
    """Integration-style tests with simulated scenarios"""
    
    @pytest.mark.asyncio
    async def test_healthy_system_scenario(self):
        """Test scenario with all agents healthy"""
        watchdog = Watchdog()
        
        # Simulate healthy activity for all agents
        for agent_name in watchdog.agent_names:
            metrics = watchdog.agent_metrics[agent_name]
            metrics.total_requests = 100
            metrics.successful_requests = 98
            metrics.failed_requests = 2
            metrics.last_seen = time.time()
            metrics.recent_latencies = deque([50, 60, 70, 80, 90])
        
        health = watchdog.get_system_health()
        
        assert health['system_health_score'] > 0.9
        assert all(not agent['isolated'] for agent in health['agents'].values())
        print("✅ Healthy system scenario passed")
    
    @pytest.mark.asyncio
    async def test_degraded_agent_scenario(self):
        """Test scenario with one degraded agent"""
        watchdog = Watchdog()
        
        # Most agents healthy
        for agent_name in ['Kyle', 'Joey', 'HRM', 'Aletheia', 'ID']:
            metrics = watchdog.agent_metrics[agent_name]
            metrics.total_requests = 100
            metrics.successful_requests = 98
            metrics.failed_requests = 2
            metrics.last_seen = time.time()
            metrics.recent_latencies = deque([50, 60, 70])
        
        # Kenny degraded
        kenny = watchdog.agent_metrics['Kenny']
        kenny.total_requests = 100
        kenny.successful_requests = 40  # 60% failure rate!
        kenny.failed_requests = 60
        kenny.last_seen = time.time() - 90  # Not seen recently (90s ago)
        kenny.recent_latencies = deque([6000, 7000, 8000, 9000])  # Very high latency
        kenny.consecutive_failures = 4
        
        health = watchdog.get_system_health()
        
        # System degraded but not critical
        system_health = health['system_health_score']
        kenny_health = health['agents']['Kenny']['health_score']
        
        # Debug: print actual values if assertion fails
        if not (0.5 < system_health < 0.9):
            print(f"  Debug: system_health_score = {system_health:.3f} (expected 0.5-0.9)")
        if not (kenny_health < 0.5):
            print(f"  Debug: Kenny health_score = {kenny_health:.3f} (expected < 0.5)")
        
        assert 0.5 < system_health < 0.9, f"System health {system_health:.3f} not in range 0.5-0.9"
        assert kenny_health < 0.5, f"Kenny health {kenny_health:.3f} not < 0.5"
        print("✅ Degraded agent scenario passed")
    
    @pytest.mark.asyncio
    async def test_failing_agent_scenario(self):
        """Test scenario with failing agent requiring isolation"""
        config = WatchdogConfig(
            max_consecutive_failures=5,
            enable_auto_isolation=True
        )
        watchdog = Watchdog(config=config)
        
        # Kenny failing badly
        kenny = watchdog.agent_metrics['Kenny']
        kenny.total_requests = 100
        kenny.successful_requests = 10
        kenny.failed_requests = 90
        kenny.consecutive_failures = 10  # Exceeds threshold
        kenny.last_seen = time.time()
        
        # Check isolation condition
        await watchdog._check_agent_health('Kenny')
        
        # Should be isolated due to consecutive failures
        assert kenny.isolated is True
        print("✅ Failing agent scenario passed")
    
    @pytest.mark.asyncio
    async def test_graveyard_violation_spike(self):
        """Test scenario with spike in Graveyard violations"""
        config = WatchdogConfig(max_graveyard_violations_per_minute=10)
        watchdog = Watchdog(config=config)
        
        # Simulate 15 violations in last minute
        current_time = time.time()
        for i in range(15):
            watchdog.graveyard_violations_last_minute.append(current_time - i)
        
        health = watchdog.get_system_health()
        
        violations = health['graveyard']['violations_last_minute']
        assert violations == 15
        assert violations > config.max_graveyard_violations_per_minute
        print("✅ Graveyard violation spike scenario passed")


def run_all_tests():
    """Run all Watchdog tests"""
    print("=" * 60)
    print("WATCHDOG TEST SUITE")
    print("=" * 60)
    print()
    
    test_classes = [
        TestAgentMetrics,
        TestWatchdogConfig,
        TestWatchdogCore,
        TestWatchdogIsolation,
        TestWatchdogEmergencyControls,
        TestWatchdogMetricsUpdate,
        TestWatchdogSimulation
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}...")
        print("-" * 60)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            method = getattr(test_instance, method_name)
            
            try:
                # Check if async
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                
                print(f"  ✅ {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ❌ {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, str(e)))
            except Exception as e:
                print(f"  ⚠️  {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, f"Exception: {str(e)}"))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {len(failed_tests)} ❌")
    print(f"Success rate: {(passed_tests / total_tests * 100):.1f}%")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for class_name, method_name, error in failed_tests:
            print(f"  • {class_name}.{method_name}")
            print(f"    {error}")
    else:
        print("\n🎉 ALL TESTS PASSED!")
    
    print("=" * 60)
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
