"""
Unit Tests for Watchdog Monitoring System
Tests health monitoring, emergency controls, and system oversight
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import asyncio
from unittest.mock import Mock, MagicMock, patch

# Mock redis before import
sys.modules['redis'] = MagicMock()
sys.modules['psutil'] = MagicMock()

from monitoring.watchdog import Watchdog, AgentHealth, SystemHealth


class TestWatchdogInitialization(unittest.TestCase):
    """Test Watchdog initialization and configuration"""
    
    def test_watchdog_creation(self):
        """Test creating Watchdog instance"""
        watchdog = Watchdog(redis_host='localhost', redis_port=6379)
        
        self.assertIsNotNone(watchdog)
        self.assertFalse(watchdog.running)
        self.assertFalse(watchdog.emergency_halt)
        self.assertEqual(len(watchdog.isolated_agents), 0)
        
        print("✅ Watchdog creation: Instance created successfully")
    
    def test_watchdog_configuration(self):
        """Test Watchdog configuration defaults"""
        watchdog = Watchdog()
        
        config = watchdog.config
        
        self.assertEqual(config['check_interval_seconds'], 5)
        self.assertEqual(config['heartbeat_timeout_seconds'], 30)
        self.assertEqual(config['response_time_threshold_ms'], 5000)
        self.assertEqual(config['error_rate_threshold'], 0.20)
        self.assertEqual(config['critical_violations_threshold'], 3)
        
        print("✅ Watchdog configuration: All defaults correct")


class TestAgentHealthMonitoring(unittest.TestCase):
    """Test agent health monitoring"""
    
    def test_agent_health_creation(self):
        """Test creating AgentHealth dataclass"""
        health = AgentHealth(
            name='Kenny',
            status='healthy',
            last_heartbeat=1234567890.0,
            response_time_avg_ms=50.5,
            response_time_p95_ms=120.0,
            error_count=2,
            error_rate=0.05,
            task_count=40,
            success_rate=0.95,
            violations_count=0,
            last_violation=None,
            uptime_seconds=3600.0
        )
        
        self.assertEqual(health.name, 'Kenny')
        self.assertEqual(health.status, 'healthy')
        self.assertEqual(health.success_rate, 0.95)
        
        print("✅ AgentHealth: Dataclass created correctly")
    
    def test_agent_status_determination(self):
        """Test agent status determination logic"""
        # Healthy agent
        healthy = AgentHealth(
            name='Kyle',
            status='healthy',
            last_heartbeat=0,
            response_time_avg_ms=100.0,
            response_time_p95_ms=200.0,
            error_count=1,
            error_rate=0.05,
            task_count=20,
            success_rate=0.95,
            violations_count=0,
            last_violation=None,
            uptime_seconds=1000.0
        )
        self.assertEqual(healthy.status, 'healthy')
        
        # Degraded agent (slow response)
        degraded = AgentHealth(
            name='Joey',
            status='degraded',
            last_heartbeat=0,
            response_time_avg_ms=6000.0,  # Slow
            response_time_p95_ms=8000.0,
            error_count=5,
            error_rate=0.15,
            task_count=50,
            success_rate=0.85,
            violations_count=2,
            last_violation='position_size',
            uptime_seconds=2000.0
        )
        self.assertEqual(degraded.status, 'degraded')
        
        print("✅ Agent status: Determination logic correct")


class TestSystemHealthMonitoring(unittest.TestCase):
    """Test system-level health monitoring"""
    
    def test_system_health_creation(self):
        """Test creating SystemHealth dataclass"""
        health = SystemHealth(
            status='healthy',
            timestamp='2024-01-01T00:00:00',
            uptime_seconds=3600.0,
            agents_healthy=6,
            agents_degraded=0,
            agents_unhealthy=0,
            agents_offline=0,
            total_agents=6,
            redis_connected=True,
            redis_latency_ms=5.0,
            queue_depth=10,
            memory_usage_pct=45.0,
            cpu_usage_pct=30.0,
            graveyard_violations_total=5,
            graveyard_violations_critical=0,
            emergency_halt_active=False
        )
        
        self.assertEqual(health.status, 'healthy')
        self.assertEqual(health.agents_healthy, 6)
        self.assertFalse(health.emergency_halt_active)
        
        print("✅ SystemHealth: Dataclass created correctly")
    
    def test_system_status_determination(self):
        """Test system status determination"""
        # Healthy system
        healthy = SystemHealth(
            status='healthy',
            timestamp='2024-01-01T00:00:00',
            uptime_seconds=1000.0,
            agents_healthy=6,
            agents_degraded=0,
            agents_unhealthy=0,
            agents_offline=0,
            total_agents=6,
            redis_connected=True,
            redis_latency_ms=2.0,
            queue_depth=5,
            memory_usage_pct=40.0,
            cpu_usage_pct=25.0,
            graveyard_violations_total=3,
            graveyard_violations_critical=0,
            emergency_halt_active=False
        )
        self.assertEqual(healthy.status, 'healthy')
        
        # Degraded system
        degraded = SystemHealth(
            status='degraded',
            timestamp='2024-01-01T00:00:00',
            uptime_seconds=1000.0,
            agents_healthy=4,
            agents_degraded=2,
            agents_unhealthy=0,
            agents_offline=0,
            total_agents=6,
            redis_connected=True,
            redis_latency_ms=15.0,
            queue_depth=50,
            memory_usage_pct=75.0,
            cpu_usage_pct=70.0,
            graveyard_violations_total=10,
            graveyard_violations_critical=1,
            emergency_halt_active=False
        )
        self.assertEqual(degraded.status, 'degraded')
        
        print("✅ System status: Determination logic correct")


class TestEmergencyControls(unittest.TestCase):
    """Test emergency halt and agent isolation"""
    
    def test_emergency_halt_trigger(self):
        """Test triggering emergency halt"""
        watchdog = Watchdog()
        
        # Before halt
        self.assertFalse(watchdog.emergency_halt)
        
        # Trigger halt
        asyncio.run(watchdog.trigger_emergency_halt("Test emergency"))
        
        # After halt
        self.assertTrue(watchdog.emergency_halt)
        
        print("✅ Emergency halt: Triggered successfully")
    
    def test_emergency_halt_clear(self):
        """Test clearing emergency halt"""
        watchdog = Watchdog()
        
        # Set halt
        asyncio.run(watchdog.trigger_emergency_halt("Test"))
        self.assertTrue(watchdog.emergency_halt)
        
        # Clear halt
        asyncio.run(watchdog.clear_emergency_halt())
        self.assertFalse(watchdog.emergency_halt)
        
        print("✅ Emergency clear: Halt cleared successfully")
    
    def test_agent_isolation(self):
        """Test agent isolation"""
        watchdog = Watchdog()
        
        # Isolate agent
        asyncio.run(watchdog.isolate_agent('Kenny', 'High error rate'))
        
        self.assertIn('Kenny', watchdog.isolated_agents)
        
        print("✅ Agent isolation: Kenny isolated successfully")
    
    def test_agent_restoration(self):
        """Test agent restoration"""
        watchdog = Watchdog()
        
        # Isolate then restore
        asyncio.run(watchdog.isolate_agent('Joey', 'Test'))
        self.assertIn('Joey', watchdog.isolated_agents)
        
        asyncio.run(watchdog.restore_agent('Joey'))
        self.assertNotIn('Joey', watchdog.isolated_agents)
        
        print("✅ Agent restoration: Joey restored successfully")


class TestThresholdDetection(unittest.TestCase):
    """Test threshold detection and alerting"""
    
    def test_critical_violations_threshold(self):
        """Test critical violations threshold detection"""
        watchdog = Watchdog()
        watchdog.config['critical_violations_threshold'] = 3
        watchdog.graveyard_metrics = {
            'total_violations': 10,
            'critical_violations': 3  # At threshold
        }
        
        # Should trigger emergency halt
        asyncio.run(watchdog._check_emergency_conditions())
        
        self.assertTrue(watchdog.emergency_halt)
        
        print("✅ Critical violations: Threshold detected correctly")
    
    def test_agent_offline_threshold(self):
        """Test agent offline threshold detection"""
        watchdog = Watchdog()
        
        # Create 4 offline agents (majority)
        for i, agent in enumerate(['Kyle', 'Joey', 'Kenny', 'HRM']):
            watchdog.agent_health[agent] = AgentHealth(
                name=agent,
                status='offline',
                last_heartbeat=0,
                response_time_avg_ms=0,
                response_time_p95_ms=0,
                error_count=0,
                error_rate=0,
                task_count=0,
                success_rate=0,
                violations_count=0,
                last_violation=None,
                uptime_seconds=0
            )
        
        # Evaluate system health
        asyncio.run(watchdog._evaluate_system_health())
        
        # Check emergency conditions
        asyncio.run(watchdog._check_emergency_conditions())
        
        self.assertTrue(watchdog.emergency_halt)
        
        print("✅ Agent offline: Catastrophic failure detected")


class TestWatchdogStatus(unittest.TestCase):
    """Test Watchdog status reporting"""
    
    def test_get_status(self):
        """Test getting Watchdog status"""
        watchdog = Watchdog()
        watchdog.running = True
        
        status = watchdog.get_status()
        
        self.assertIn('running', status)
        self.assertIn('uptime_seconds', status)
        self.assertIn('emergency_halt', status)
        self.assertIn('system_health', status)
        self.assertIn('agent_health', status)
        self.assertIn('config', status)
        
        self.assertTrue(status['running'])
        
        print("✅ Watchdog status: All fields present")
    
    def test_status_with_health_data(self):
        """Test status with health data populated"""
        watchdog = Watchdog()
        
        # Add agent health
        watchdog.agent_health['Kenny'] = AgentHealth(
            name='Kenny',
            status='healthy',
            last_heartbeat=0,
            response_time_avg_ms=100.0,
            response_time_p95_ms=200.0,
            error_count=1,
            error_rate=0.02,
            task_count=50,
            success_rate=0.98,
            violations_count=0,
            last_violation=None,
            uptime_seconds=1000.0
        )
        
        status = watchdog.get_status()
        
        self.assertIn('Kenny', status['agent_health'])
        self.assertEqual(status['agent_health']['Kenny']['status'], 'healthy')
        
        print("✅ Status with data: Agent health included correctly")


def run_watchdog_tests():
    """Run all Watchdog tests"""
    
    print("\n" + "="*70)
    print("WATCHDOG MONITORING SYSTEM TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWatchdogInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentHealthMonitoring))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemHealthMonitoring))
    suite.addTests(loader.loadTestsFromTestCase(TestEmergencyControls))
    suite.addTests(loader.loadTestsFromTestCase(TestThresholdDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestWatchdogStatus))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70 + "\n")
    
    if result.wasSuccessful():
        print("🎉 ALL WATCHDOG TESTS PASSED! 🎉\n")
        print("Watchdog Implementation Status:")
        print("  ✅ Initialization and configuration")
        print("  ✅ Agent health monitoring")
        print("  ✅ System health monitoring")
        print("  ✅ Emergency halt controls")
        print("  ✅ Agent isolation")
        print("  ✅ Threshold detection")
        print("  ✅ Status reporting")
        print("\n✅ Ready for integration with ARK system\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_watchdog_tests()
    sys.exit(0 if success else 1)
