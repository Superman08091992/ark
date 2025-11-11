#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK ID Growth System - Comprehensive Demonstration

Demonstrates adaptive behavioral modeling with confidence-weighted learning:
1. Initialize agent identity models
2. Extract features from reasoning traces
3. Apply EWMA updates with confidence weighting
4. Track learning curves and adaptation
5. Link reflections to behavioral evolution
6. Display statistics and growth metrics
"""

import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from id.model import IDModel
from id.features import FeatureExtractor, update_from_reflections


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
    
    print_section("ARK ID Growth System - Comprehensive Demonstration")
    
    print("This demonstration showcases adaptive behavioral modeling with")
    print("confidence-weighted learning curves that link reflection insights")
    print("to agent identity evolution.")
    
    # Initialize components
    print_subsection("1. Initializing ID System")
    
    db_path = 'data/demo_memory.db'
    
    if not Path(db_path).exists():
        print(f"⚠️  Memory database not found: {db_path}")
        print("Please run demo_memory_engine.py first.")
        return
    
    model = IDModel(db_path=db_path)
    extractor = FeatureExtractor()
    
    print(f"✓ ID Model initialized")
    print(f"✓ Feature Extractor initialized")
    print(f"✓ Database: {db_path}")
    
    # Show learning parameters
    print(f"\nLearning Parameters:")
    print(f"  Base alpha (learning rate): {model.base_alpha}")
    print(f"  Min alpha: {model.min_alpha}")
    print(f"  Max alpha: {model.max_alpha}")
    print(f"  Algorithm: EWMA with confidence weighting")
    
    # Initialize test agents
    print_subsection("2. Initializing Agent Identities")
    
    test_agents = ['Aletheia', 'Corpus', 'Joey']
    
    for agent in test_agents:
        state = model.get_state(agent)
        if not state:
            state_id = model.initialize_agent(agent)
            print(f"✓ Initialized {agent} (ID: {state_id[:8]}...)")
        else:
            print(f"✓ {agent} already initialized ({state['update_count']} updates)")
    
    # Feature extraction demo
    print_subsection("3. Feature Extraction from Traces")
    
    print("Extracting behavioral features from reasoning traces...")
    
    # Load sample traces from database
    import sqlite3
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM reasoning_log
        WHERE agent IN ('Aletheia', 'Corpus')
        LIMIT 10
    """)
    
    traces = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    if traces:
        features = extractor.extract_from_traces(traces)
        
        print(f"\n✓ Extracted {len(features)} behavioral features")
        print(f"\nSample Features:")
        
        categories = {
            'Performance': ['avg_confidence', 'task_completion_rate'],
            'Behavioral': ['risk_score', 'caution_score', 'thoroughness_score'],
            'Learning': ['pattern_recognition_rate', 'adaptation_speed'],
            'Ethical': ['hrm_compliance_rate', 'security_awareness'],
            'Communication': ['output_clarity', 'structured_thinking']
        }
        
        for category, feature_names in categories.items():
            print(f"\n  {category}:")
            for name in feature_names:
                if name in features:
                    print(f"    {name}: {features[name]:.3f}")
    else:
        print("  ⚠️  No traces found for demonstration")
    
    # Simulate learning curve
    print_subsection("4. Confidence-Weighted Learning Demonstration")
    
    print("Simulating agent learning with varying confidence levels...")
    
    agent = 'Aletheia'
    
    # Initial state
    state = model.get_state(agent)
    if state:
        initial_features = state.get('behavior_features', {})
        print(f"\nInitial state for {agent}:")
        print(f"  Update count: {state['update_count']}")
        if initial_features:
            print(f"  Sample features:")
            for i, (name, value) in enumerate(list(initial_features.items())[:3]):
                print(f"    {name}: {value:.3f}")
    
    # Simulate 3 updates with different confidence levels
    print(f"\nSimulating learning updates:")
    
    updates = [
        {
            'features': {
                'avg_confidence': 0.85,
                'risk_score': 0.7,
                'pattern_recognition_rate': 0.65,
                'hrm_compliance_rate': 0.9
            },
            'confidence': 0.95,
            'description': "High-confidence reflection (excellent reasoning quality)"
        },
        {
            'features': {
                'avg_confidence': 0.78,
                'risk_score': 0.65,
                'pattern_recognition_rate': 0.7,
                'hrm_compliance_rate': 0.85
            },
            'confidence': 0.70,
            'description': "Medium-confidence reflection (good quality)"
        },
        {
            'features': {
                'avg_confidence': 0.95,
                'risk_score': 0.9,
                'pattern_recognition_rate': 0.85,
                'hrm_compliance_rate': 0.95
            },
            'confidence': 0.35,
            'description': "Low-confidence reflection (uncertain, less impact)"
        }
    ]
    
    for i, update_spec in enumerate(updates, 1):
        result = model.update(
            agent=agent,
            observed_features=update_spec['features'],
            confidence=update_spec['confidence'],
            metadata={'simulation': True, 'round': i}
        )
        
        print(f"\nUpdate {i}: {update_spec['description']}")
        print(f"  Confidence: {update_spec['confidence']:.2f}")
        print(f"  Alpha used: {result['alpha_used']:.3f}")
        print(f"  Avg change: {result['avg_change']:.4f}")
        print(f"  Learning phase: {result['learning_phase']}")
        print(f"  Stability: {result['stability_score']:.3f}")
    
    # Show final state
    print_subsection("5. Final Agent State After Learning")
    
    state = model.get_state(agent)
    if state:
        print(f"Agent: {agent}")
        print(f"Update count: {state['update_count']}")
        
        learning_curve = state.get('learning_curve', {})
        print(f"\nLearning Curve:")
        print(f"  Current alpha: {learning_curve.get('current_alpha', 0):.3f}")
        print(f"  Learning phase: {learning_curve.get('learning_phase', 'unknown')}")
        print(f"  Stability score: {learning_curve.get('stability_score', 0):.3f}")
        
        features = state.get('behavior_features', {})
        if features:
            print(f"\nBehavioral Features (sample):")
            for i, (name, value) in enumerate(list(features.items())[:8]):
                print(f"  {name}: {value:.3f}")
    
    # Update from reflections
    print_subsection("6. Updating from Reflection Insights")
    
    print("Linking reflection insights to behavioral evolution...")
    
    # Update all test agents from reflections
    for agent in test_agents:
        result = update_from_reflections(
            agent=agent,
            lookback_days=30
        )
        
        print(f"\n{agent}:")
        print(f"  Traces analyzed: {result['traces_analyzed']}")
        print(f"  Reflections used: {result['reflections_used']}")
        print(f"  Features extracted: {result['features_extracted']}")
        
        if result['update_result']:
            ur = result['update_result']
            print(f"  Alpha used: {ur.get('alpha_used', 0):.3f}")
            print(f"  Learning phase: {ur.get('learning_phase', 'N/A')}")
    
    # Show update history
    print_subsection("7. Update History and Provenance")
    
    agent = 'Aletheia'
    history = model.get_update_history(agent, limit=5)
    
    print(f"Recent updates for {agent}:")
    
    for i, update in enumerate(history, 1):
        print(f"\nUpdate {i}:")
        print(f"  Timestamp: {update['ts']}")
        print(f"  Alpha: {update['alpha_used']:.3f}")
        print(f"  Confidence: {update['confidence_weight']:.3f}")
        print(f"  Features updated: {update['reflection_count']}")
        
        # Show feature changes
        if update.get('features_before') and update.get('features_after'):
            before = update['features_before']
            after = update['features_after']
            
            print(f"  Sample changes:")
            for name in list(after.keys())[:3]:
                if name in before:
                    change = after[name] - before[name]
                    print(f"    {name}: {before[name]:.3f} → {after[name]:.3f} ({change:+.3f})")
    
    # System statistics
    print_subsection("8. ID System Statistics")
    
    stats = model.get_stats()
    
    print(f"Total agents: {stats['total_agents']}")
    print(f"Total updates: {stats['total_updates']}")
    print(f"Avg updates per agent: {stats['avg_updates_per_agent']}")
    
    if stats['top_agents']:
        print(f"\nMost active agents:")
        for agent, count in stats['top_agents']:
            print(f"  {agent}: {count} updates")
    
    # Learning curve visualization (text-based)
    print_subsection("9. Learning Curve Visualization")
    
    print(f"Learning progression for {test_agents[0]}:")
    
    history = model.get_update_history(test_agents[0], limit=10)
    
    if history:
        print("\nAlpha (learning rate) over time:")
        for i, update in enumerate(reversed(history), 1):
            alpha = update['alpha_used']
            bar_len = int(alpha * 50)
            bar = '█' * bar_len
            print(f"  {i:2d}. [{bar:<50}] {alpha:.3f}")
        
        print("\nNote: Alpha adapts based on confidence and stability")
        print("  • High alpha = Fast learning (new/uncertain)")
        print("  • Low alpha = Slow learning (stable/confident)")
    
    # Summary
    print_subsection("Demonstration Summary")
    
    print("✓ ID Growth System successfully demonstrated:")
    print("  • Agent identity initialization")
    print("  • Behavioral feature extraction (17 features)")
    print("  • EWMA learning with confidence weighting")
    print("  • Adaptive alpha based on experience and stability")
    print("  • Reflection-to-behavior linking")
    print("  • Update history and provenance tracking")
    print("  • Learning curve visualization")
    print("  • System-wide statistics")
    
    print("\n✓ Key Learning Mechanisms:")
    print("  • High-confidence reflections → Higher impact (alpha)")
    print("  • New agents → Faster learning (higher alpha)")
    print("  • Stable agents → Slower learning (lower alpha)")
    print("  • EWMA smoothing → Gradual adaptation")
    print("  • Quadratic confidence weighting → Emphasize quality")
    
    print("\n✓ ID Growth System is READY for autonomous evolution!")
    
    print_section("Demonstration Complete")
    
    # Cleanup
    model.close()
    print(f"\n✓ Database connection closed")
    print(f"\nID state preserved in: {db_path}")
    print("You can query with: sqlite3 data/demo_memory.db")
    print("\nTo view ID state:")
    print("  SELECT * FROM id_state;")
    print("  SELECT * FROM id_updates ORDER BY ts DESC LIMIT 10;")


if __name__ == '__main__':
    main()
