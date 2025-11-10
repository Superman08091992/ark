#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hierarchical Reasoning Module for ARK

Implements multi-level reasoning framework with inter-agent consultation.
Designed for minimal system disruption - adds zero latency to individual agents
by making HRM the orchestrator of hierarchical reasoning when needed.

Architecture:
- Level 1: Graveyard validation (immutable rules) - FAST, always executed
- Level 2: Contextual analysis (Joey memory retrieval) - OPTIONAL, triggered on edge cases
- Level 3: Truth verification (Aletheia fact-check) - OPTIONAL, triggered on uncertainty
- Level 4: Risk assessment (Kenny execution analysis) - OPTIONAL, triggered on high-stakes
- Level 5: Synthesis (HRM weighted decision) - ALWAYS executed

Usage:
    from reasoning.hierarchical_reasoner import HierarchicalReasoner
    
    reasoner = HierarchicalReasoner(hrm_agent)
    decision = await reasoner.reason(action, trigger_levels=[1,2,5])
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Graveyard for Level 1
from graveyard.ethics import validate_against_graveyard

logger = logging.getLogger(__name__)


@dataclass
class ReasoningLevel:
    """Represents one level of hierarchical reasoning"""
    level: int
    name: str
    agent: Optional[str]  # Which agent handles this level
    executed: bool = False
    result: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    triggered: bool = False
    
    
@dataclass
class HierarchicalDecision:
    """Complete hierarchical reasoning decision with all levels"""
    action: Dict[str, Any]
    agent_name: str
    final_decision: str  # 'approved', 'denied', 'escalate'
    confidence: float
    levels_executed: List[ReasoningLevel] = field(default_factory=list)
    total_duration_ms: float = 0.0
    reasoning_path: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            'action': self.action,
            'agent_name': self.agent_name,
            'final_decision': self.final_decision,
            'confidence': self.confidence,
            'levels_executed': [
                {
                    'level': lvl.level,
                    'name': lvl.name,
                    'agent': lvl.agent,
                    'executed': lvl.executed,
                    'triggered': lvl.triggered,
                    'duration_ms': lvl.duration_ms
                }
                for lvl in self.levels_executed
            ],
            'total_duration_ms': self.total_duration_ms,
            'reasoning_path': self.reasoning_path,
            'warnings': self.warnings,
            'timestamp': self.timestamp
        }


class HierarchicalReasoner:
    """
    Hierarchical reasoning orchestrator for ARK agents.
    
    Implements adaptive multi-level reasoning:
    - Always executes Level 1 (Graveyard) and Level 5 (Synthesis)
    - Conditionally triggers Levels 2-4 based on edge case detection
    - Zero latency impact when only L1+L5 execute (fast path)
    - Full reasoning when edge cases detected (comprehensive path)
    """
    
    def __init__(self, hrm_agent, enable_adaptive_triggering: bool = True):
        """
        Initialize hierarchical reasoner.
        
        Args:
            hrm_agent: HRM agent instance for accessing other agents
            enable_adaptive_triggering: If True, conditionally trigger L2-L4
        """
        self.hrm = hrm_agent
        self.adaptive = enable_adaptive_triggering
        
        # Reference to other agents (will be injected by agent loader)
        self.agent_registry = {}
        
        # Performance tracking
        self.reasoning_history: List[HierarchicalDecision] = []
        self.fast_path_count = 0
        self.full_path_count = 0
        
        logger.info("HierarchicalReasoner initialized (adaptive=%s)", enable_adaptive_triggering)
    
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """Register an agent for inter-agent consultation"""
        self.agent_registry[agent_name] = agent_instance
        logger.info(f"Registered agent: {agent_name}")
    
    async def reason(
        self,
        action: Dict[str, Any],
        agent_name: str = "Unknown",
        force_levels: Optional[List[int]] = None
    ) -> HierarchicalDecision:
        """
        Execute hierarchical reasoning on an action.
        
        Args:
            action: Action to validate (must have 'action_type' and params)
            agent_name: Name of agent proposing the action
            force_levels: If provided, force execute these levels (bypasses adaptive)
        
        Returns:
            HierarchicalDecision with complete reasoning chain
        """
        start_time = time.time()
        
        # Initialize decision structure
        decision = HierarchicalDecision(
            action=action,
            agent_name=agent_name,
            final_decision='pending',
            confidence=0.0
        )
        
        try:
            # LEVEL 1: Graveyard Validation (ALWAYS EXECUTE - FAST)
            level1 = await self._execute_level1_graveyard(action, agent_name)
            decision.levels_executed.append(level1)
            decision.reasoning_path.append(f"L1: Graveyard validation")
            
            # Fast path: If Graveyard approves and no edge cases, skip to synthesis
            if level1.result['approved'] and not self._detect_edge_case(level1.result, action):
                decision.reasoning_path.append("Fast path: No edge cases detected")
                self.fast_path_count += 1
                
                # Jump to Level 5 (Synthesis)
                level5 = await self._execute_level5_synthesis(decision, [level1])
                decision.levels_executed.append(level5)
                decision.reasoning_path.append(f"L5: Synthesis (fast path)")
                
                decision.final_decision = level5.result['decision']
                decision.confidence = level5.result['confidence']
                decision.total_duration_ms = (time.time() - start_time) * 1000
                
                logger.info(f"Fast path reasoning: {decision.total_duration_ms:.1f}ms")
                self.reasoning_history.append(decision)
                return decision
            
            # Full path: Edge cases or Graveyard denial detected
            self.full_path_count += 1
            decision.reasoning_path.append("Full path: Edge cases or violations detected")
            
            # Determine which levels to trigger
            if force_levels:
                trigger_levels = force_levels
            elif self.adaptive:
                trigger_levels = self._determine_trigger_levels(level1.result, action)
            else:
                trigger_levels = [2, 3, 4]  # Trigger all optional levels
            
            # LEVEL 2: Contextual Analysis (OPTIONAL - via Joey)
            if 2 in trigger_levels:
                level2 = await self._execute_level2_context(action, agent_name)
                decision.levels_executed.append(level2)
                decision.reasoning_path.append(f"L2: Contextual analysis")
            
            # LEVEL 3: Truth Verification (OPTIONAL - via Aletheia)
            if 3 in trigger_levels:
                level3 = await self._execute_level3_truth(action, agent_name)
                decision.levels_executed.append(level3)
                decision.reasoning_path.append(f"L3: Truth verification")
            
            # LEVEL 4: Risk Assessment (OPTIONAL - via Kenny)
            if 4 in trigger_levels:
                level4 = await self._execute_level4_risk(action, agent_name)
                decision.levels_executed.append(level4)
                decision.reasoning_path.append(f"L4: Risk assessment")
            
            # LEVEL 5: Synthesis (ALWAYS EXECUTE)
            executed_levels = [lvl for lvl in decision.levels_executed if lvl.executed]
            level5 = await self._execute_level5_synthesis(decision, executed_levels)
            decision.levels_executed.append(level5)
            decision.reasoning_path.append(f"L5: Synthesis (full path)")
            
            # Final decision
            decision.final_decision = level5.result['decision']
            decision.confidence = level5.result['confidence']
            decision.warnings = level5.result.get('warnings', [])
            decision.total_duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Full path reasoning: {decision.total_duration_ms:.1f}ms "
                f"(levels: {[lvl.level for lvl in executed_levels]})"
            )
            
            self.reasoning_history.append(decision)
            return decision
            
        except Exception as e:
            logger.error(f"Hierarchical reasoning error: {e}")
            decision.final_decision = 'error'
            decision.confidence = 0.0
            decision.warnings.append(f"Reasoning error: {str(e)}")
            decision.total_duration_ms = (time.time() - start_time) * 1000
            return decision
    
    async def _execute_level1_graveyard(
        self,
        action: Dict[str, Any],
        agent_name: str
    ) -> ReasoningLevel:
        """Level 1: Validate against immutable Graveyard rules"""
        start = time.time()
        level = ReasoningLevel(level=1, name="Graveyard Validation", agent="Graveyard")
        
        try:
            result = validate_against_graveyard(action, agent_name)
            level.result = result
            level.executed = True
            level.triggered = True  # L1 always triggered
            level.duration_ms = (time.time() - start) * 1000
            
            logger.debug(f"L1 Graveyard: approved={result['approved']}, "
                        f"violations={len(result['violations'])}, "
                        f"duration={level.duration_ms:.1f}ms")
            
        except Exception as e:
            logger.error(f"L1 Graveyard error: {e}")
            level.result = {'approved': False, 'violations': [], 'error': str(e)}
            level.executed = False
        
        return level
    
    async def _execute_level2_context(
        self,
        action: Dict[str, Any],
        agent_name: str
    ) -> ReasoningLevel:
        """Level 2: Retrieve contextual memory via Joey"""
        start = time.time()
        level = ReasoningLevel(level=2, name="Contextual Analysis", agent="Joey")
        
        try:
            joey = self.agent_registry.get('Joey')
            if not joey:
                logger.warning("Joey not registered, skipping L2")
                level.triggered = False
                return level
            
            level.triggered = True
            
            # Query Joey for relevant context
            query = f"Context for {action.get('action_type', 'action')} by {agent_name}"
            
            # Joey may have a method like retrieve_context or get_memory_context
            if hasattr(joey, 'retrieve_context'):
                context_result = await joey.retrieve_context(query)
            elif hasattr(joey, 'get_memory'):
                # Fallback to basic memory retrieval
                memory = joey.get_memory()
                context_result = {
                    'relevant_memories': [],
                    'context_score': 0.5,
                    'historical_precedents': []
                }
            else:
                context_result = {'available': False}
            
            level.result = context_result
            level.executed = True
            level.duration_ms = (time.time() - start) * 1000
            
            logger.debug(f"L2 Context: score={context_result.get('context_score', 0):.2f}, "
                        f"duration={level.duration_ms:.1f}ms")
            
        except Exception as e:
            logger.error(f"L2 Context error: {e}")
            level.result = {'error': str(e)}
            level.executed = False
        
        return level
    
    async def _execute_level3_truth(
        self,
        action: Dict[str, Any],
        agent_name: str
    ) -> ReasoningLevel:
        """Level 3: Verify truth/facts via Aletheia"""
        start = time.time()
        level = ReasoningLevel(level=3, name="Truth Verification", agent="Aletheia")
        
        try:
            aletheia = self.agent_registry.get('Aletheia')
            if not aletheia:
                logger.warning("Aletheia not registered, skipping L3")
                level.triggered = False
                return level
            
            level.triggered = True
            
            # Extract claims from action for verification
            claims = self._extract_claims(action)
            
            # Aletheia may have verify_claim or check_truth method
            if hasattr(aletheia, 'verify_claim') and claims:
                truth_result = await aletheia.verify_claim(claims[0])
            else:
                # Minimal truth check
                truth_result = {
                    'truth_score': 0.8,  # Default: assume truthful unless proven otherwise
                    'confidence': 0.7,
                    'verified': True
                }
            
            level.result = truth_result
            level.executed = True
            level.duration_ms = (time.time() - start) * 1000
            
            logger.debug(f"L3 Truth: score={truth_result.get('truth_score', 0):.2f}, "
                        f"duration={level.duration_ms:.1f}ms")
            
        except Exception as e:
            logger.error(f"L3 Truth error: {e}")
            level.result = {'error': str(e)}
            level.executed = False
        
        return level
    
    async def _execute_level4_risk(
        self,
        action: Dict[str, Any],
        agent_name: str
    ) -> ReasoningLevel:
        """Level 4: Assess execution risk via Kenny"""
        start = time.time()
        level = ReasoningLevel(level=4, name="Risk Assessment", agent="Kenny")
        
        try:
            kenny = self.agent_registry.get('Kenny')
            if not kenny:
                logger.warning("Kenny not registered, skipping L4")
                level.triggered = False
                return level
            
            level.triggered = True
            
            # Kenny may have assess_risk or evaluate_execution method
            if hasattr(kenny, 'assess_risk'):
                risk_result = await kenny.assess_risk(action)
            else:
                # Simplified risk assessment
                risk_result = {
                    'risk_level': 'medium',
                    'risk_score': 0.5,
                    'execution_feasible': True,
                    'warnings': []
                }
            
            level.result = risk_result
            level.executed = True
            level.duration_ms = (time.time() - start) * 1000
            
            logger.debug(f"L4 Risk: level={risk_result.get('risk_level')}, "
                        f"score={risk_result.get('risk_score', 0):.2f}, "
                        f"duration={level.duration_ms:.1f}ms")
            
        except Exception as e:
            logger.error(f"L4 Risk error: {e}")
            level.result = {'error': str(e)}
            level.executed = False
        
        return level
    
    async def _execute_level5_synthesis(
        self,
        decision: HierarchicalDecision,
        executed_levels: List[ReasoningLevel]
    ) -> ReasoningLevel:
        """Level 5: Synthesize all levels into final decision"""
        start = time.time()
        level = ReasoningLevel(level=5, name="Decision Synthesis", agent="HRM")
        level.triggered = True  # L5 always triggered
        
        try:
            # Weighted decision synthesis
            weights = {
                1: 1.0,   # Graveyard is absolute (highest weight)
                2: 0.3,   # Context is informative
                3: 0.5,   # Truth is important
                4: 0.7,   # Risk is critical
            }
            
            total_weight = 0.0
            weighted_approval = 0.0
            warnings = []
            
            for lvl in executed_levels:
                if not lvl.executed or not lvl.result:
                    continue
                
                weight = weights.get(lvl.level, 0.5)
                total_weight += weight
                
                # Level 1: Graveyard
                if lvl.level == 1:
                    if lvl.result['approved']:
                        weighted_approval += weight
                    else:
                        # Graveyard denial is absolute
                        level.result = {
                            'decision': 'denied',
                            'confidence': 1.0,
                            'reason': 'Graveyard violation',
                            'violations': lvl.result['violations'],
                            'warnings': warnings
                        }
                        level.executed = True
                        level.duration_ms = (time.time() - start) * 1000
                        return level
                
                # Level 2: Context
                elif lvl.level == 2:
                    context_score = lvl.result.get('context_score', 0.5)
                    weighted_approval += weight * context_score
                    if context_score < 0.3:
                        warnings.append("Low context relevance")
                
                # Level 3: Truth
                elif lvl.level == 3:
                    truth_score = lvl.result.get('truth_score', 0.8)
                    weighted_approval += weight * truth_score
                    if truth_score < 0.6:
                        warnings.append("Truth verification concerns")
                
                # Level 4: Risk
                elif lvl.level == 4:
                    risk_score = lvl.result.get('risk_score', 0.5)
                    # Lower risk score means safer (invert for approval)
                    weighted_approval += weight * (1.0 - risk_score)
                    if risk_score > 0.7:
                        warnings.append("High execution risk")
            
            # Calculate final confidence
            confidence = weighted_approval / total_weight if total_weight > 0 else 0.5
            
            # Decision threshold
            if confidence >= 0.7:
                final_decision = 'approved'
            elif confidence >= 0.4:
                final_decision = 'escalate'  # Human review
                warnings.append("Borderline decision - escalate to human")
            else:
                final_decision = 'denied'
            
            level.result = {
                'decision': final_decision,
                'confidence': confidence,
                'reason': f"Synthesized from {len(executed_levels)} levels",
                'warnings': warnings,
                'levels_considered': [lvl.level for lvl in executed_levels]
            }
            level.executed = True
            level.duration_ms = (time.time() - start) * 1000
            
            logger.info(
                f"L5 Synthesis: decision={final_decision}, "
                f"confidence={confidence:.2f}, "
                f"duration={level.duration_ms:.1f}ms"
            )
            
        except Exception as e:
            logger.error(f"L5 Synthesis error: {e}")
            level.result = {
                'decision': 'error',
                'confidence': 0.0,
                'error': str(e),
                'warnings': ['Synthesis failed']
            }
            level.executed = False
        
        return level
    
    def _detect_edge_case(
        self,
        graveyard_result: Dict[str, Any],
        action: Dict[str, Any]
    ) -> bool:
        """Detect if action represents an edge case requiring full reasoning"""
        
        # Edge case indicators
        edge_cases = [
            # Close to threshold violations
            len(graveyard_result.get('warnings', [])) > 0,
            
            # Compliance score borderline (90-95%)
            0.90 <= graveyard_result.get('compliance_score', 1.0) <= 0.95,
            
            # Novel action types
            action.get('action_type', '').lower() not in [
                'read', 'query', 'analyze', 'report'
            ],
            
            # High-stakes actions
            action.get('action_type', '').lower() in [
                'trade', 'execute', 'delete', 'transfer', 'modify'
            ],
            
            # Multiple rules triggered
            len(graveyard_result.get('rules_checked', [])) > 5
        ]
        
        return any(edge_cases)
    
    def _determine_trigger_levels(
        self,
        graveyard_result: Dict[str, Any],
        action: Dict[str, Any]
    ) -> List[int]:
        """Determine which optional levels (2-4) to trigger"""
        triggers = []
        
        # Level 2 (Context): Trigger if action type is complex or novel
        if action.get('action_type', '').lower() in [
            'trade', 'strategic_decision', 'policy_change'
        ]:
            triggers.append(2)
        
        # Level 3 (Truth): Trigger if action contains claims or data
        if self._contains_factual_claims(action):
            triggers.append(3)
        
        # Level 4 (Risk): Trigger if Graveyard has warnings or high-stakes action
        if (graveyard_result.get('warnings') or 
            action.get('action_type', '').lower() in ['trade', 'execute', 'delete']):
            triggers.append(4)
        
        return triggers
    
    def _contains_factual_claims(self, action: Dict[str, Any]) -> bool:
        """Check if action contains factual claims requiring verification"""
        # Simple heuristic: check for claim indicators
        params = action.get('parameters', {})
        description = params.get('description', '')
        
        claim_indicators = ['shows', 'proves', 'demonstrates', 'indicates', 'confirms']
        return any(indicator in description.lower() for indicator in claim_indicators)
    
    def _extract_claims(self, action: Dict[str, Any]) -> List[str]:
        """Extract factual claims from action for verification"""
        params = action.get('parameters', {})
        description = params.get('description', '')
        
        # Simple extraction: split by sentences
        claims = [s.strip() for s in description.split('.') if s.strip()]
        return claims[:3]  # Limit to first 3 claims
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reasoning performance statistics"""
        total = self.fast_path_count + self.full_path_count
        
        if not self.reasoning_history:
            return {
                'total_decisions': 0,
                'fast_path_count': 0,
                'full_path_count': 0,
                'fast_path_percentage': 0.0,
                'avg_duration_ms': 0.0
            }
        
        avg_duration = sum(d.total_duration_ms for d in self.reasoning_history) / len(self.reasoning_history)
        
        return {
            'total_decisions': total,
            'fast_path_count': self.fast_path_count,
            'full_path_count': self.full_path_count,
            'fast_path_percentage': (self.fast_path_count / total * 100) if total > 0 else 0.0,
            'avg_duration_ms': avg_duration,
            'decisions_history_size': len(self.reasoning_history)
        }
