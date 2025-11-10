#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kyle Intra-Agent Hierarchical Reasoning Demonstration

This demo showcases Kyle's enhanced cognitive processing with 5-level
hierarchical reasoning and Tree-of-Selfs exploration.

With no speed constraints, Kyle can afford comprehensive multi-level
analysis for superior signal detection quality.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reasoning.kyle_reasoner import KyleReasoner
from reasoning.intra_agent_reasoner import ReasoningDepth


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def print_cognitive_path(decision):
    """Print the cognitive processing path"""
    print("🧠 Cognitive Processing Path:")
    print("-" * 80)
    for level in decision.cognitive_levels:
        status = "✓" if level.confidence > 0.6 else "⚠" if level.confidence > 0.3 else "✗"
        print(f"{status} Level {level.level}: {level.name:<12} | "
              f"Confidence: {level.confidence:.2f} | "
              f"Branches: {level.branches_explored} | "
              f"Duration: {level.duration_ms:.1f}ms")
        
        # Show key reasoning traces
        if level.reasoning_trace:
            for trace in level.reasoning_trace[:2]:  # Show first 2 traces
                print(f"   → {trace}")
    print("-" * 80)


def print_thought_tree(decision, max_branches: int = 10):
    """Print Tree-of-Selfs structure"""
    if not decision.thought_tree:
        return
    
    print("\n🌳 Tree-of-Selfs (Thought Exploration):")
    print("-" * 80)
    
    # Group by level
    by_level = {}
    for branch in decision.thought_tree[:max_branches]:
        level = branch.depth
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(branch)
    
    for level in sorted(by_level.keys()):
        branches = by_level[level]
        main = [b for b in branches if 'main' in b.branch_id]
        alts = [b for b in branches if 'main' not in b.branch_id]
        
        if main:
            b = main[0]
            print(f"\nLevel {level}: {b.hypothesis}")
            print(f"  Confidence: {b.confidence:.2f} | Children: {len(b.children)}")
        
        if alts and len(alts) <= 3:
            print(f"  Alternatives explored: {len(alts)}")
            for alt in alts[:2]:
                print(f"    • {alt.hypothesis} (conf: {alt.confidence:.2f})")
    print("-" * 80)


def print_decision_summary(decision):
    """Print final decision summary"""
    print("\n📊 Decision Summary:")
    print("-" * 80)
    print(f"Final Decision: {json.dumps(decision.final_decision, indent=2)}")
    print(f"\nOverall Confidence: {decision.confidence:.2f}")
    print(f"Reasoning Depth: {decision.reasoning_depth.name}")
    print(f"Alternatives Considered: {decision.alternatives_considered}")
    print(f"Total Processing Time: {decision.total_duration_ms:.1f}ms")
    print("-" * 80)


async def demo_scenario_1_strong_breakout():
    """Demo 1: Strong breakout signal with high confidence"""
    print_header("SCENARIO 1: Strong Breakout Signal")
    
    signal_data = {
        'symbol': 'TSLA',
        'price_change': 0.06,  # 6% price surge
        'volume_surge': 2.8,   # Nearly 3x volume
        'sentiment_score': 0.75,  # Strong bullish sentiment
        'timestamp': datetime.now().isoformat()
    }
    
    context = {
        'agent_role': 'market_scanner',
        'threshold': 0.7,
        'historical_patterns': [],
        'market_sentiment': 'bullish'
    }
    
    print("📈 Input Signal Data:")
    print(json.dumps(signal_data, indent=2))
    print(f"\n⚙️  Processing with DEEP reasoning (no speed constraints)...")
    
    reasoner = KyleReasoner(
        default_depth=ReasoningDepth.DEEP,
        enable_tree_of_selfs=True,
        max_branches_per_level=5
    )
    
    decision = await reasoner.reason(
        input_data=signal_data,
        depth=ReasoningDepth.DEEP,
        context=context
    )
    
    print_cognitive_path(decision)
    print_thought_tree(decision)
    print_decision_summary(decision)
    
    # Extract and display signal details
    if isinstance(decision.final_decision, dict):
        selected = decision.final_decision.get('selected_option', {})
        print(f"\n🎯 Kyle's Signal: {selected.get('action', 'unknown').upper()}")
        print(f"   Signal Strength: {selected.get('signal_strength', 0.0):.2f}")
        print(f"   Description: {selected.get('description', 'N/A')}")


async def demo_scenario_2_reversal_risk():
    """Demo 2: Price-sentiment divergence (reversal warning)"""
    print_header("SCENARIO 2: Reversal Risk Detection")
    
    signal_data = {
        'symbol': 'SPY',
        'price_change': 0.04,   # Price up 4%
        'volume_surge': 1.6,
        'sentiment_score': -0.5,  # But sentiment bearish (divergence!)
        'timestamp': datetime.now().isoformat()
    }
    
    context = {
        'agent_role': 'market_scanner',
        'threshold': 0.7,
        'historical_patterns': [],
        'market_sentiment': 'mixed'
    }
    
    print("⚠️  Input Signal Data (Note divergence):")
    print(json.dumps(signal_data, indent=2))
    print(f"\n⚙️  Processing with DEEP reasoning...")
    
    reasoner = KyleReasoner(
        default_depth=ReasoningDepth.DEEP,
        enable_tree_of_selfs=True,
        max_branches_per_level=5
    )
    
    decision = await reasoner.reason(
        input_data=signal_data,
        depth=ReasoningDepth.DEEP,
        context=context
    )
    
    print_cognitive_path(decision)
    
    # Highlight risk detection
    level4 = decision.cognitive_levels[3]  # Evaluation level
    risks = level4.output_data.get('risks', [])
    if risks:
        print("\n⚠️  Risks Identified:")
        print("-" * 80)
        for risk in risks:
            print(f"  • {risk['type']}: {risk.get('description', 'N/A')} [{risk.get('severity', 'unknown')}]")
        print("-" * 80)
    
    print_decision_summary(decision)


async def demo_scenario_3_consolidation():
    """Demo 3: Low volatility consolidation pattern"""
    print_header("SCENARIO 3: Consolidation Detection")
    
    signal_data = {
        'symbol': 'QQQ',
        'price_change': 0.005,  # 0.5% - minimal movement
        'volume_surge': 1.05,   # Normal volume
        'sentiment_score': 0.1,  # Neutral sentiment
        'timestamp': datetime.now().isoformat()
    }
    
    context = {
        'agent_role': 'market_scanner',
        'threshold': 0.7,
        'historical_patterns': [],
        'market_sentiment': 'neutral'
    }
    
    print("📊 Input Signal Data (Low volatility):")
    print(json.dumps(signal_data, indent=2))
    print(f"\n⚙️  Processing with DEEP reasoning...")
    
    reasoner = KyleReasoner(
        default_depth=ReasoningDepth.DEEP,
        enable_tree_of_selfs=True,
        max_branches_per_level=5
    )
    
    decision = await reasoner.reason(
        input_data=signal_data,
        depth=ReasoningDepth.DEEP,
        context=context
    )
    
    print_cognitive_path(decision)
    print_decision_summary(decision)


async def demo_scenario_4_depth_comparison():
    """Demo 4: Compare reasoning depths"""
    print_header("SCENARIO 4: Reasoning Depth Comparison")
    
    signal_data = {
        'symbol': 'NVDA',
        'price_change': 0.03,
        'volume_surge': 1.7,
        'sentiment_score': 0.6,
        'timestamp': datetime.now().isoformat()
    }
    
    context = {
        'agent_role': 'market_scanner',
        'threshold': 0.7,
        'historical_patterns': [],
        'market_sentiment': 'bullish'
    }
    
    print("📈 Input Signal Data:")
    print(json.dumps(signal_data, indent=2))
    
    depths = [ReasoningDepth.SHALLOW, ReasoningDepth.MODERATE, ReasoningDepth.DEEP]
    
    reasoner = KyleReasoner(
        default_depth=ReasoningDepth.DEEP,
        enable_tree_of_selfs=True,
        max_branches_per_level=5
    )
    
    results = []
    for depth in depths:
        print(f"\n⚙️  Processing with {depth.name} reasoning...")
        decision = await reasoner.reason(
            input_data=signal_data,
            depth=depth,
            context=context
        )
        results.append((depth.name, decision))
    
    print("\n📊 Depth Comparison Results:")
    print("-" * 80)
    print(f"{'Depth':<12} | {'Confidence':<12} | {'Alternatives':<14} | {'Duration':<12} | {'Tree Branches':<12}")
    print("-" * 80)
    for depth_name, decision in results:
        print(f"{depth_name:<12} | {decision.confidence:<12.2f} | "
              f"{decision.alternatives_considered:<14} | "
              f"{decision.total_duration_ms:<12.1f}ms | "
              f"{len(decision.thought_tree):<12}")
    print("-" * 80)
    
    print("\n💡 Insight: With no speed constraints, DEEP reasoning provides:")
    print("   • More alternatives explored (higher confidence in decision)")
    print("   • More comprehensive thought tree (better understanding)")
    print("   • Slightly longer processing time (but quality matters more!)")


async def demo_scenario_5_extreme_anomaly():
    """Demo 5: Extreme price movement anomaly"""
    print_header("SCENARIO 5: Extreme Anomaly Detection")
    
    signal_data = {
        'symbol': 'GME',
        'price_change': 0.18,  # 18% surge (extreme!)
        'volume_surge': 4.5,   # 4.5x volume (massive!)
        'sentiment_score': 0.9,  # Very bullish
        'timestamp': datetime.now().isoformat()
    }
    
    context = {
        'agent_role': 'market_scanner',
        'threshold': 0.7,
        'historical_patterns': [],
        'market_sentiment': 'euphoric'
    }
    
    print("🚀 Input Signal Data (EXTREME VALUES!):")
    print(json.dumps(signal_data, indent=2))
    print(f"\n⚙️  Processing with EXHAUSTIVE reasoning (research mode)...")
    
    reasoner = KyleReasoner(
        default_depth=ReasoningDepth.EXHAUSTIVE,
        enable_tree_of_selfs=True,
        max_branches_per_level=10  # More branches for exhaustive
    )
    
    decision = await reasoner.reason(
        input_data=signal_data,
        depth=ReasoningDepth.EXHAUSTIVE,
        context=context
    )
    
    print_cognitive_path(decision)
    
    # Highlight anomalies
    level2 = decision.cognitive_levels[1]  # Analysis level
    anomalies = level2.output_data.get('anomalies', [])
    if anomalies:
        print("\n🔍 Anomalies Detected:")
        print("-" * 80)
        for anomaly in anomalies:
            print(f"  • {anomaly['type']}: {anomaly.get('description', 'N/A')} [{anomaly.get('severity', 'unknown')}]")
        print("-" * 80)
    
    print_thought_tree(decision, max_branches=15)
    print_decision_summary(decision)
    
    print("\n⚠️  Note: Extreme movements may indicate manipulation or news events.")
    print("   Kyle's hierarchical reasoning helps identify these edge cases.")


async def main():
    """Run all demonstration scenarios"""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  KYLE'S INTRA-AGENT HIERARCHICAL REASONING DEMONSTRATION".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" + "  With no speed constraints, quality and depth are paramount".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    scenarios = [
        ("Strong Breakout Signal", demo_scenario_1_strong_breakout),
        ("Reversal Risk Detection", demo_scenario_2_reversal_risk),
        ("Consolidation Detection", demo_scenario_3_consolidation),
        ("Reasoning Depth Comparison", demo_scenario_4_depth_comparison),
        ("Extreme Anomaly Detection", demo_scenario_5_extreme_anomaly),
    ]
    
    for i, (name, scenario_func) in enumerate(scenarios, 1):
        try:
            await scenario_func()
        except Exception as e:
            print(f"\n❌ Error in scenario {i}: {str(e)}")
        
        if i < len(scenarios):
            input(f"\n\n{'▶' * 40}\nPress Enter to continue to next scenario...\n{'▶' * 40}\n")
    
    print("\n" + "=" * 80)
    print(" DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\n💡 Key Takeaways:")
    print("   1. Kyle now processes signals through 5 cognitive levels")
    print("   2. Tree-of-Selfs enables exploration of alternative interpretations")
    print("   3. Pattern detection identifies breakouts, reversals, consolidations")
    print("   4. Anomaly detection catches extreme movements and divergences")
    print("   5. Risk assessment provides early warnings for potential reversals")
    print("   6. With no speed constraints, we prioritize quality over latency")
    print("\n🎯 Next Steps:")
    print("   • Extend to other agents (Joey, Kenny, Aletheia, ID)")
    print("   • Enable inter-agent reasoning with HRM orchestration")
    print("   • Add psychological profiling and behavioral consistency checks")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    print("\n🚀 Starting Kyle Intra-Agent Reasoning Demo...\n")
    asyncio.run(main())
