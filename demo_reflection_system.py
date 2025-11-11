#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Reflection System - Comprehensive Demonstration

Demonstrates the nightly "sleep mode" autonomous learning system:
1. Initialize reflection engine
2. Generate reflections from memory chunks
3. Analyze reflection types and insights
4. View confidence improvements
5. Test scheduler functionality
6. Display statistics
"""

import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from reflection.reflection_engine import ReflectionEngine
from reflection.reflection_scheduler import ReflectionScheduler


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Print formatted subsection header"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80 + "\n")


def main():
    """Run comprehensive demonstration"""
    
    print_section("ARK Reflection System - Comprehensive Demonstration")
    
    print("This demonstration showcases the nightly 'sleep mode' autonomous learning system.")
    print("The reflection engine analyzes reasoning traces and generates insights for")
    print("continuous self-improvement.")
    
    # Initialize engine
    print_subsection("1. Initializing Reflection Engine")
    
    db_path = 'data/demo_memory.db'
    policy_path = 'reflection/reflection_policies.yaml'
    
    # Check if memory database exists
    if not Path(db_path).exists():
        print(f"⚠️  Memory database not found: {db_path}")
        print("Please run demo_memory_engine.py first to create sample data.")
        return
    
    engine = ReflectionEngine(db_path=db_path, policy_path=policy_path)
    print(f"✓ Reflection engine initialized")
    print(f"✓ Database: {db_path}")
    print(f"✓ Policies: {policy_path}")
    
    # Load policies
    print_subsection("2. Reflection Policies")
    
    policy = engine.policy
    print(f"Mode: {policy.get('mode', 'N/A')}")
    print(f"Schedule: {policy.get('schedule', 'N/A')} {policy.get('timezone', 'UTC')}")
    print(f"Max chunks per cycle: {policy.get('max_chunks_per_cycle', 'N/A')}")
    print(f"Min confidence delta: {policy.get('min_confidence_delta', 'N/A')}")
    print(f"Trust tier weighting: {policy.get('trust_tier_weighting', 'N/A')}")
    print(f"HRM signature required: {policy.get('require_hrm_signature', 'N/A')}")
    print(f"Quarantine violations: {policy.get('quarantine_violations', 'N/A')}")
    
    # Check for existing reflections
    print_subsection("3. Pre-Reflection Statistics")
    
    stats_before = engine.get_stats()
    print(f"Existing reflections: {stats_before['total_reflections']}")
    if stats_before['reflections_by_type']:
        print(f"By type:")
        for rtype, count in stats_before['reflections_by_type'].items():
            print(f"  • {rtype}: {count}")
    
    # Run reflection cycle
    print_subsection("4. Running Reflection Cycle")
    print("Analyzing memory chunks and generating insights...")
    
    result = engine.generate_reflections()
    
    print(f"\n✓ Reflection cycle complete!")
    print(f"  • Status: {result['status']}")
    print(f"  • Chunks processed: {result['chunks_processed']}")
    print(f"  • Reflections generated: {result['reflections_generated']}")
    print(f"  • Reflections stored: {result['reflections_stored']}")
    print(f"  • Duration: {result['duration_seconds']}s")
    
    # Show post-reflection statistics
    print_subsection("5. Post-Reflection Statistics")
    
    stats_after = engine.get_stats()
    print(f"Total reflections: {stats_after['total_reflections']}")
    print(f"Recent (24h): {stats_after['recent_24h']}")
    print(f"Average confidence delta: {stats_after['avg_confidence_delta']:.4f}")
    
    if stats_after['reflections_by_type']:
        print(f"\nReflections by type:")
        for rtype, count in sorted(stats_after['reflections_by_type'].items(), 
                                   key=lambda x: x[1], reverse=True):
            print(f"  • {rtype}: {count}")
    
    # Show sample reflections
    print_subsection("6. Sample Reflections")
    
    cursor = engine.db.cursor()
    cursor.execute("""
        SELECT 
            reflection_id,
            timestamp,
            reflection_type,
            insight,
            confidence,
            confidence_delta,
            tier
        FROM reflections
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    
    reflections = cursor.fetchall()
    
    if reflections:
        for i, row in enumerate(reflections, 1):
            print(f"\nReflection {i}:")
            print(f"  ID: {row[0]}")
            print(f"  Timestamp: {row[1]}")
            print(f"  Type: {row[2]}")
            print(f"  Insight: {row[3][:120]}...")
            print(f"  Confidence: {row[4]:.2f} (Δ {row[5]:+.2f})")
            print(f"  Trust Tier: {row[6]}")
    else:
        print("No reflections generated (memory chunks may already be reflected upon)")
    
    # Analyze reflection types
    print_subsection("7. Reflection Type Analysis")
    
    cursor.execute("""
        SELECT 
            reflection_type,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence,
            AVG(confidence_delta) as avg_delta
        FROM reflections
        GROUP BY reflection_type
        ORDER BY count DESC
    """)
    
    type_analysis = cursor.fetchall()
    
    if type_analysis:
        print("Type Distribution:")
        for row in type_analysis:
            print(f"\n  {row[0]}:")
            print(f"    Count: {row[1]}")
            print(f"    Avg Confidence: {row[2]:.2f}")
            print(f"    Avg Delta: {row[3]:+.4f}")
    
    # Test scheduler (without actually starting it)
    print_subsection("8. Scheduler Configuration")
    
    try:
        scheduler = ReflectionScheduler(db_path=db_path, policy_path=policy_path)
        
        if scheduler.scheduler:
            print("✓ Scheduler initialized successfully")
            print(f"  Schedule: {policy.get('schedule', 'N/A')}")
            print(f"  Timezone: {policy.get('timezone', 'UTC')}")
            print(f"  Mode: Nightly 'sleep mode' autonomous learning")
            
            # Note: Not starting scheduler in demo to avoid background thread
            print("\n  (Scheduler not started in demo mode)")
        else:
            print("⚠️  Scheduler initialization failed (APScheduler may not be installed)")
    
    except Exception as e:
        print(f"⚠️  Scheduler test failed: {e}")
    
    # Show audit log
    print_subsection("9. Audit Log")
    
    audit_path = policy.get('audit_log_path', 'logs/reflection_audit.log')
    
    if Path(audit_path).exists():
        print(f"Audit log: {audit_path}")
        print("\nRecent entries:")
        with open(audit_path, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(f"  {line.strip()}")
    else:
        print(f"No audit log found at: {audit_path}")
    
    # Summary
    print_subsection("Demonstration Summary")
    
    print("✓ Reflection System successfully demonstrated:")
    print("  • Engine initialization and policy loading")
    print("  • Nightly reflection cycle execution")
    print("  • Insight generation from memory chunks")
    print("  • Confidence improvement tracking")
    print("  • Reflection type categorization")
    print("  • Statistics and analytics")
    print("  • Scheduler configuration")
    print("  • Audit logging")
    
    print("\n✓ The Reflection System mimics biological 'sleep' for AI learning:")
    print("  • Consolidates daily experiences (memory chunks)")
    print("  • Extracts patterns and insights")
    print("  • Improves confidence calibration")
    print("  • Validates ethical alignment")
    print("  • Enables continuous self-improvement")
    
    print("\n✓ Reflection System is READY for autonomous learning!")
    
    print_section("Demonstration Complete")
    
    # Cleanup
    engine.close()
    print(f"\n✓ Database connection closed")
    print(f"\nReflection database preserved at: {db_path}")
    print("You can inspect it with: sqlite3 data/demo_memory.db")
    print("\nTo view reflections:")
    print("  SELECT * FROM reflections ORDER BY timestamp DESC LIMIT 10;")


if __name__ == '__main__':
    main()
