#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Reflection Scheduler

Schedules nightly reflection cycles using APScheduler.
Mimics biological "sleep" for autonomous learning.

Architecture:
- BackgroundScheduler: Runs reflection jobs in background thread
- CronTrigger: Midnight runs (configurable via policy)
- ReflectionEngine: Performs actual reflection analysis
"""

import logging
import sys
from pathlib import Path

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logging.warning("APScheduler not available - manual triggering only")

from reflection.reflection_engine import ReflectionEngine

logger = logging.getLogger(__name__)


class ReflectionScheduler:
    """
    Scheduler for nightly reflection cycles
    
    Runs reflection engine at scheduled times (default: midnight UTC)
    """
    
    def __init__(
        self,
        db_path: str = "data/demo_memory.db",
        policy_path: str = "reflection/reflection_policies.yaml"
    ):
        """
        Initialize reflection scheduler
        
        Args:
            db_path: Path to SQLite database
            policy_path: Path to reflection policies
        """
        self.db_path = db_path
        self.policy_path = policy_path
        self.scheduler = None
        self.engine = None
        
        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not available - scheduler cannot start")
            return
        
        # Initialize engine
        self.engine = ReflectionEngine(db_path, policy_path)
        
        # Load schedule from policy
        policy = self.engine.policy
        schedule = policy.get('schedule', '0 0 * * *')  # Default: midnight
        timezone = policy.get('timezone', 'UTC')
        
        # Parse cron schedule (minute hour day month day_of_week)
        parts = schedule.split()
        if len(parts) != 5:
            logger.error(f"Invalid cron schedule: {schedule}")
            return
        
        minute, hour, day, month, day_of_week = parts
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler(timezone=timezone)
        
        # Add reflection job
        self.scheduler.add_job(
            self._run_reflection_cycle,
            CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=timezone
            ),
            id='reflection_cycle',
            name='Nightly Reflection Cycle',
            replace_existing=True
        )
        
        logger.info(f"Reflection scheduler initialized: {schedule} {timezone}")
    
    def _run_reflection_cycle(self):
        """Run reflection cycle (called by scheduler)"""
        logger.info("🌙 Starting nightly reflection cycle...")
        
        try:
            result = self.engine.generate_reflections()
            logger.info(f"✅ Reflection cycle complete: {result}")
            
            # Notify if enabled
            if self.engine.policy.get('notify_on_completion', False):
                self._notify_completion(result)
        
        except Exception as e:
            logger.error(f"❌ Reflection cycle failed: {e}", exc_info=True)
    
    def _notify_completion(self, result: dict):
        """Send notification about reflection completion"""
        # TODO: Implement notification system (email, webhook, etc.)
        logger.info(f"📬 Notification: Reflection cycle completed - {result['reflections_stored']} reflections stored")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            logger.error("Scheduler not initialized - cannot start")
            return False
        
        if self.scheduler.running:
            logger.warning("Scheduler already running")
            return True
        
        self.scheduler.start()
        logger.info("🕛 Reflection scheduler started (sleep cycle active)")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        if not self.scheduler:
            return
        
        if not self.scheduler.running:
            logger.warning("Scheduler not running")
            return
        
        self.scheduler.shutdown()
        logger.info("Reflection scheduler stopped")
    
    def trigger_manual(self):
        """Manually trigger a reflection cycle"""
        logger.info("🔧 Manual reflection trigger")
        self._run_reflection_cycle()
    
    def get_next_run_time(self):
        """Get next scheduled run time"""
        if not self.scheduler:
            return None
        
        job = self.scheduler.get_job('reflection_cycle')
        if job:
            return job.next_run_time
        return None


def start_reflection_scheduler(
    db_path: str = "data/demo_memory.db",
    policy_path: str = "reflection/reflection_policies.yaml"
) -> ReflectionScheduler:
    """
    Start reflection scheduler (convenience function)
    
    Args:
        db_path: Path to SQLite database
        policy_path: Path to reflection policies
        
    Returns:
        ReflectionScheduler instance
    """
    scheduler = ReflectionScheduler(db_path, policy_path)
    scheduler.start()
    
    next_run = scheduler.get_next_run_time()
    if next_run:
        print(f"🕛 Reflection sleep cycle active (next run: {next_run})")
    else:
        print("⚠️  Reflection scheduler started but no next run scheduled")
    
    return scheduler


if __name__ == '__main__':
    # Test scheduler
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("ARK Reflection Scheduler - Test Suite")
    print("=" * 60)
    
    # Initialize scheduler
    scheduler = ReflectionScheduler(
        db_path='data/demo_memory.db',
        policy_path='reflection/reflection_policies.yaml'
    )
    
    print("\n1. Starting scheduler...")
    scheduler.start()
    
    print("\n2. Checking next run time...")
    next_run = scheduler.get_next_run_time()
    print(f"Next scheduled run: {next_run}")
    
    print("\n3. Triggering manual reflection cycle...")
    scheduler.trigger_manual()
    
    print("\n4. Waiting 5 seconds...")
    import time
    time.sleep(5)
    
    print("\n5. Stopping scheduler...")
    scheduler.stop()
    
    print("\n" + "=" * 60)
    print("Scheduler test complete!")
    print("=" * 60)
