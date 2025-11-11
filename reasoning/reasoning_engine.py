#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReasoningEngine Base Class

Provides a clean 5-stage cognitive pipeline that wraps the IntraAgentReasoner:
1. Perceive - Raw input processing and feature extraction
2. Analyze - Pattern detection and structural analysis
3. Hypothesize - Generate alternative solutions/interpretations
4. Validate - Test hypotheses against evidence and constraints
5. Reflect - Meta-cognitive assessment and confidence scoring

This interface is designed for the intelligent-backend.cjs integration,
providing a standardized API across all agent reasoning chains.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from reasoning.intra_agent_reasoner import (
    IntraAgentReasoner,
    ReasoningDepth,
    IntraAgentDecision,
    CognitiveLevel
)

logger = logging.getLogger(__name__)


class ReasoningStage(Enum):
    """5-stage reasoning pipeline stages"""
    PERCEIVE = "perceive"
    ANALYZE = "analyze"
    HYPOTHESIZE = "hypothesize"
    VALIDATE = "validate"
    REFLECT = "reflect"


@dataclass
class StageResult:
    """Result from a single reasoning stage"""
    stage: ReasoningStage
    input_data: Any
    output_data: Any
    confidence: float
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    traces: List[str] = field(default_factory=list)
    
    def add_trace(self, message: str):
        """Add trace message"""
        self.traces.append(f"[{self.stage.value}] {message}")


@dataclass
class ReasoningResult:
    """Complete reasoning pipeline result"""
    agent_name: str
    query: str
    final_output: Any
    overall_confidence: float
    stages: List[StageResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses"""
        return {
            'agent_name': self.agent_name,
            'query': self.query,
            'final_output': self.final_output,
            'overall_confidence': self.overall_confidence,
            'stages': [
                {
                    'stage': s.stage.value,
                    'confidence': s.confidence,
                    'duration_ms': s.duration_ms,
                    'traces': s.traces,
                    'metadata': s.metadata
                }
                for s in self.stages
            ],
            'total_duration_ms': self.total_duration_ms,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class ReasoningEngine:
    """
    Base reasoning engine that provides the 5-stage pipeline interface.
    
    This wraps the IntraAgentReasoner's 5 cognitive levels and maps them
    to the explicit perceive → analyze → hypothesize → validate → reflect
    stages for clean API exposure.
    """
    
    def __init__(
        self,
        agent_name: str,
        intra_reasoner: IntraAgentReasoner,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP
    ):
        """
        Initialize reasoning engine
        
        Args:
            agent_name: Name of the agent using this engine
            intra_reasoner: The specialized IntraAgentReasoner instance
            default_depth: Default reasoning depth
        """
        self.agent_name = agent_name
        self.intra_reasoner = intra_reasoner
        self.default_depth = default_depth
        
        logger.info(f"Initialized ReasoningEngine for {agent_name} with depth={default_depth.name}")
    
    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        depth: Optional[ReasoningDepth] = None
    ) -> ReasoningResult:
        """
        Execute the complete 5-stage reasoning pipeline
        
        Args:
            query: The input query/request to reason about
            context: Optional context information
            depth: Optional reasoning depth override
            
        Returns:
            ReasoningResult with all stage outputs
        """
        start_time = time.time()
        reasoning_depth = depth or self.default_depth
        context = context or {}
        
        logger.info(f"[{self.agent_name}] Starting reasoning pipeline for query: {query[:100]}")
        
        stages: List[StageResult] = []
        
        try:
            # Stage 1: PERCEIVE - Raw input processing
            perceive_result = await self._perceive(query, context, reasoning_depth)
            stages.append(perceive_result)
            
            # Stage 2: ANALYZE - Pattern detection and structural analysis
            analyze_result = await self._analyze(
                perceive_result.output_data,
                context,
                reasoning_depth
            )
            stages.append(analyze_result)
            
            # Stage 3: HYPOTHESIZE - Generate alternative solutions
            hypothesize_result = await self._hypothesize(
                analyze_result.output_data,
                context,
                reasoning_depth
            )
            stages.append(hypothesize_result)
            
            # Stage 4: VALIDATE - Test hypotheses against evidence
            validate_result = await self._validate(
                hypothesize_result.output_data,
                context,
                reasoning_depth
            )
            stages.append(validate_result)
            
            # Stage 5: REFLECT - Meta-cognitive assessment
            reflect_result = await self._reflect(
                validate_result.output_data,
                stages,
                context,
                reasoning_depth
            )
            stages.append(reflect_result)
            
            # Calculate overall metrics
            total_duration_ms = (time.time() - start_time) * 1000
            overall_confidence = self._calculate_overall_confidence(stages)
            
            result = ReasoningResult(
                agent_name=self.agent_name,
                query=query,
                final_output=reflect_result.output_data,
                overall_confidence=overall_confidence,
                stages=stages,
                total_duration_ms=total_duration_ms,
                metadata={
                    'reasoning_depth': reasoning_depth.name,
                    'context': context
                }
            )
            
            logger.info(
                f"[{self.agent_name}] Reasoning complete: "
                f"confidence={overall_confidence:.3f}, duration={total_duration_ms:.1f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Reasoning pipeline failed: {e}", exc_info=True)
            raise
    
    async def _perceive(
        self,
        query: str,
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> StageResult:
        """
        Stage 1: PERCEIVE - Process raw input and extract features
        
        Maps to IntraAgentReasoner Level 1 (Perception)
        """
        start_time = time.time()
        stage_result = StageResult(
            stage=ReasoningStage.PERCEIVE,
            input_data=query,
            output_data=None,
            confidence=0.0,
            duration_ms=0.0
        )
        
        stage_result.add_trace("Starting perception stage")
        
        # Delegate to intra-reasoner's perception level
        # We'll extract just the Level 1 processing
        input_data = {'query': query, 'context': context}
        
        # Use intra-reasoner's Level 1 perception
        level1 = await self.intra_reasoner._level1_perception(
            input_data,
            context,
            depth
        )
        
        stage_result.output_data = level1.output_data
        stage_result.confidence = level1.confidence
        stage_result.duration_ms = (time.time() - start_time) * 1000
        stage_result.traces.extend(level1.reasoning_trace)
        stage_result.metadata = {
            'features_extracted': level1.output_data.get('features', {}),
            'branches_explored': level1.branches_explored
        }
        
        return stage_result
    
    async def _analyze(
        self,
        perception_data: Any,
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> StageResult:
        """
        Stage 2: ANALYZE - Detect patterns and analyze structure
        
        Maps to IntraAgentReasoner Level 2 (Analysis)
        """
        start_time = time.time()
        stage_result = StageResult(
            stage=ReasoningStage.ANALYZE,
            input_data=perception_data,
            output_data=None,
            confidence=0.0,
            duration_ms=0.0
        )
        
        stage_result.add_trace("Starting analysis stage")
        
        # Delegate to intra-reasoner's analysis level
        level2 = await self.intra_reasoner._level2_analysis(
            perception_data,
            context,
            depth
        )
        
        stage_result.output_data = level2.output_data
        stage_result.confidence = level2.confidence
        stage_result.duration_ms = (time.time() - start_time) * 1000
        stage_result.traces.extend(level2.reasoning_trace)
        stage_result.metadata = {
            'patterns_detected': level2.output_data.get('patterns', []),
            'alternatives': len(level2.alternatives),
            'branches_explored': level2.branches_explored
        }
        
        return stage_result
    
    async def _hypothesize(
        self,
        analysis_data: Any,
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> StageResult:
        """
        Stage 3: HYPOTHESIZE - Generate alternative solutions/interpretations
        
        Maps to IntraAgentReasoner Level 3 (Synthesis) with emphasis on
        exploring alternative solution paths
        """
        start_time = time.time()
        stage_result = StageResult(
            stage=ReasoningStage.HYPOTHESIZE,
            input_data=analysis_data,
            output_data=None,
            confidence=0.0,
            duration_ms=0.0
        )
        
        stage_result.add_trace("Starting hypothesis generation stage")
        
        # Generate alternatives from Level 2
        alternatives = await self._generate_alternatives(analysis_data, depth)
        
        # Delegate to intra-reasoner's synthesis level
        level3 = await self.intra_reasoner._level3_synthesis(
            analysis_data,
            alternatives,
            context,
            depth
        )
        
        stage_result.output_data = level3.output_data
        stage_result.confidence = level3.confidence
        stage_result.duration_ms = (time.time() - start_time) * 1000
        stage_result.traces.extend(level3.reasoning_trace)
        stage_result.metadata = {
            'hypotheses_generated': len(alternatives),
            'synthesis_approach': level3.output_data.get('synthesis_approach'),
            'branches_explored': level3.branches_explored
        }
        
        return stage_result
    
    async def _validate(
        self,
        hypotheses_data: Any,
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> StageResult:
        """
        Stage 4: VALIDATE - Test hypotheses against evidence and constraints
        
        Maps to IntraAgentReasoner Level 4 (Evaluation)
        """
        start_time = time.time()
        stage_result = StageResult(
            stage=ReasoningStage.VALIDATE,
            input_data=hypotheses_data,
            output_data=None,
            confidence=0.0,
            duration_ms=0.0
        )
        
        stage_result.add_trace("Starting validation stage")
        
        # Collect all alternatives for evaluation
        all_alternatives = hypotheses_data.get('alternatives', [])
        
        # Delegate to intra-reasoner's evaluation level
        level4 = await self.intra_reasoner._level4_evaluation(
            hypotheses_data,
            all_alternatives,
            context,
            depth
        )
        
        stage_result.output_data = level4.output_data
        stage_result.confidence = level4.confidence
        stage_result.duration_ms = (time.time() - start_time) * 1000
        stage_result.traces.extend(level4.reasoning_trace)
        stage_result.metadata = {
            'validation_results': level4.output_data.get('validation_results', []),
            'risks_identified': level4.output_data.get('risks', []),
            'branches_explored': level4.branches_explored
        }
        
        return stage_result
    
    async def _reflect(
        self,
        validation_data: Any,
        all_stages: List[StageResult],
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> StageResult:
        """
        Stage 5: REFLECT - Meta-cognitive assessment and final decision
        
        Maps to IntraAgentReasoner Level 5 (Decision) with added
        meta-cognitive reflection on the entire reasoning process
        """
        start_time = time.time()
        stage_result = StageResult(
            stage=ReasoningStage.REFLECT,
            input_data=validation_data,
            output_data=None,
            confidence=0.0,
            duration_ms=0.0
        )
        
        stage_result.add_trace("Starting reflection stage")
        
        # Calculate cumulative confidence from all stages
        stage_confidences = [s.confidence for s in all_stages]
        cumulative_confidence = sum(stage_confidences) / len(stage_confidences)
        
        # Delegate to intra-reasoner's decision level
        level5 = await self.intra_reasoner._level5_decision(
            validation_data,
            cumulative_confidence,
            context,
            depth
        )
        
        # Add meta-cognitive reflection
        reflection = await self._meta_reflection(all_stages, level5)
        
        stage_result.output_data = {
            **level5.output_data,
            'meta_reflection': reflection
        }
        stage_result.confidence = level5.confidence
        stage_result.duration_ms = (time.time() - start_time) * 1000
        stage_result.traces.extend(level5.reasoning_trace)
        stage_result.traces.append(f"Meta-reflection: {reflection['summary']}")
        stage_result.metadata = {
            'final_decision': level5.output_data.get('decision'),
            'reflection': reflection,
            'branches_explored': level5.branches_explored
        }
        
        return stage_result
    
    async def _generate_alternatives(
        self,
        analysis_data: Any,
        depth: ReasoningDepth
    ) -> List[Dict[str, Any]]:
        """Generate alternative hypotheses based on analysis"""
        # This is agent-specific, delegate to intra-reasoner
        patterns = analysis_data.get('patterns', [])
        alternatives = []
        
        # Generate alternatives based on detected patterns
        for i, pattern in enumerate(patterns[:depth.value]):
            alternatives.append({
                'id': f"alt_{i}",
                'pattern': pattern,
                'hypothesis': f"Hypothesis based on {pattern.get('type')}",
                'confidence': pattern.get('confidence', 0.5)
            })
        
        return alternatives
    
    async def _meta_reflection(
        self,
        all_stages: List[StageResult],
        final_level: CognitiveLevel
    ) -> Dict[str, Any]:
        """
        Perform meta-cognitive reflection on the entire reasoning process
        
        This analyzes:
        - Consistency across stages
        - Confidence trajectory
        - Potential biases or blind spots
        - Alternative paths not taken
        """
        # Calculate confidence trajectory
        confidences = [s.confidence for s in all_stages]
        confidence_trend = "increasing" if confidences[-1] > confidences[0] else "decreasing"
        confidence_variance = max(confidences) - min(confidences)
        
        # Identify potential issues
        issues = []
        if confidence_variance > 0.3:
            issues.append("High confidence variance across stages")
        if confidences[-1] < 0.5:
            issues.append("Low final confidence")
        
        # Calculate total branches explored
        total_branches = sum(s.metadata.get('branches_explored', 0) for s in all_stages)
        
        reflection = {
            'summary': f"Reasoning complete with {confidence_trend} confidence",
            'confidence_trajectory': confidences,
            'confidence_trend': confidence_trend,
            'confidence_variance': confidence_variance,
            'total_branches_explored': total_branches,
            'potential_issues': issues,
            'recommendation': (
                "High confidence decision" if confidences[-1] > 0.7 else
                "Moderate confidence - consider additional validation"
            )
        }
        
        return reflection
    
    def _calculate_overall_confidence(self, stages: List[StageResult]) -> float:
        """
        Calculate overall confidence from all stages
        
        Uses weighted average with emphasis on later stages
        """
        if not stages:
            return 0.0
        
        # Weights: later stages have more influence
        weights = [1.0, 1.2, 1.4, 1.6, 2.0]  # 5 stages
        
        weighted_sum = sum(
            stage.confidence * weights[i]
            for i, stage in enumerate(stages)
        )
        total_weight = sum(weights[:len(stages)])
        
        return weighted_sum / total_weight
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reasoning statistics from underlying intra-reasoner"""
        return self.intra_reasoner.get_statistics()
    
    async def set_depth(self, depth: ReasoningDepth):
        """Update default reasoning depth"""
        self.default_depth = depth
        logger.info(f"[{self.agent_name}] Reasoning depth updated to {depth.name}")


class AgentReasoningEngine(ReasoningEngine):
    """
    Specialized reasoning engine that integrates with agent methods.
    
    This version knows how to call agent-specific tool methods and
    integrate their results with the reasoning pipeline.
    """
    
    def __init__(
        self,
        agent_name: str,
        intra_reasoner: IntraAgentReasoner,
        agent_instance: Any,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP
    ):
        """
        Initialize agent-specific reasoning engine
        
        Args:
            agent_name: Name of the agent
            intra_reasoner: The specialized IntraAgentReasoner
            agent_instance: The actual agent instance for method calls
            default_depth: Default reasoning depth
        """
        super().__init__(agent_name, intra_reasoner, default_depth)
        self.agent = agent_instance
    
    async def reason_with_tool(
        self,
        tool_name: str,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        depth: Optional[ReasoningDepth] = None
    ) -> ReasoningResult:
        """
        Execute reasoning pipeline integrated with agent tool execution
        
        Args:
            tool_name: Name of the agent tool method to call
            query: The input query
            context: Optional context
            depth: Optional reasoning depth override
            
        Returns:
            ReasoningResult with tool execution integrated
        """
        # Add tool execution to context
        context = context or {}
        context['tool_name'] = tool_name
        context['agent_method'] = getattr(self.agent, tool_name, None)
        
        # Execute standard reasoning pipeline
        result = await self.reason(query, context, depth)
        
        # Enhance with tool-specific metadata
        result.metadata['tool_executed'] = tool_name
        
        return result
