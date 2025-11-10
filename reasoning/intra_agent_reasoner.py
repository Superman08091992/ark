#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intra-Agent Hierarchical Reasoning

Implements hierarchical reasoning WITHIN each agent, not just between agents.
Each agent now has multi-level cognitive processing for enhanced decision quality.

With no speed constraints, we can afford comprehensive reasoning at every level.

Architecture (per agent):
- Level 1: Perception (raw input processing)
- Level 2: Analysis (pattern detection, feature extraction)
- Level 3: Synthesis (integration, context building)
- Level 4: Evaluation (quality assessment, confidence scoring)
- Level 5: Decision (final action selection)

Each level can branch (Tree-of-Selfs) to explore alternatives.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningDepth(Enum):
    """Reasoning depth levels"""
    SHALLOW = 1  # Quick pass, minimal branching
    MODERATE = 3  # Balanced reasoning with some exploration
    DEEP = 5  # Full comprehensive reasoning with extensive branching
    EXHAUSTIVE = 10  # Explore every possibility (research mode)


@dataclass
class CognitiveLevel:
    """Represents one cognitive processing level"""
    level: int
    name: str
    input_data: Any
    output_data: Optional[Any] = None
    alternatives: List[Any] = field(default_factory=list)
    confidence: float = 0.0
    duration_ms: float = 0.0
    branches_explored: int = 0
    reasoning_trace: List[str] = field(default_factory=list)
    
    def add_trace(self, message: str):
        """Add reasoning trace"""
        self.reasoning_trace.append(f"[L{self.level}] {message}")


@dataclass
class ThoughtBranch:
    """Represents a branching thought path (Tree-of-Selfs)"""
    branch_id: str
    parent_id: Optional[str]
    depth: int
    hypothesis: str
    evidence: List[str]
    confidence: float
    consequences: List[str]
    children: List[str] = field(default_factory=list)


@dataclass
class IntraAgentDecision:
    """Complete intra-agent reasoning result"""
    agent_name: str
    input_data: Any
    final_decision: Any
    confidence: float
    reasoning_depth: ReasoningDepth
    cognitive_levels: List[CognitiveLevel] = field(default_factory=list)
    thought_tree: List[ThoughtBranch] = field(default_factory=list)
    total_duration_ms: float = 0.0
    alternatives_considered: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            'agent_name': self.agent_name,
            'final_decision': self.final_decision,
            'confidence': self.confidence,
            'reasoning_depth': self.reasoning_depth.name,
            'cognitive_levels': [
                {
                    'level': cl.level,
                    'name': cl.name,
                    'confidence': cl.confidence,
                    'duration_ms': cl.duration_ms,
                    'branches_explored': cl.branches_explored,
                    'reasoning_trace': cl.reasoning_trace
                }
                for cl in self.cognitive_levels
            ],
            'thought_tree_size': len(self.thought_tree),
            'total_duration_ms': self.total_duration_ms,
            'alternatives_considered': self.alternatives_considered,
            'timestamp': self.timestamp
        }


class IntraAgentReasoner:
    """
    Intra-agent hierarchical reasoning engine.
    
    Implements 5-level cognitive processing within a single agent:
    L1: Perception → L2: Analysis → L3: Synthesis → L4: Evaluation → L5: Decision
    
    Each level can branch to explore alternatives (Tree-of-Selfs).
    No speed constraints - quality is paramount.
    """
    
    def __init__(
        self,
        agent_name: str,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP,
        enable_tree_of_selfs: bool = True,
        max_branches_per_level: int = 5
    ):
        """
        Initialize intra-agent reasoner.
        
        Args:
            agent_name: Name of the agent using this reasoner
            default_depth: Default reasoning depth
            enable_tree_of_selfs: Enable branching thought exploration
            max_branches_per_level: Maximum branches to explore per level
        """
        self.agent_name = agent_name
        self.default_depth = default_depth
        self.enable_tree_of_selfs = enable_tree_of_selfs
        self.max_branches = max_branches_per_level
        
        # Reasoning history for learning
        self.reasoning_history: List[IntraAgentDecision] = []
        
        # Performance tracking (but we don't care about speed!)
        self.total_decisions = 0
        self.total_reasoning_time = 0.0
        
        logger.info(
            f"IntraAgentReasoner initialized for {agent_name} "
            f"(depth={default_depth.name}, tree_of_selfs={enable_tree_of_selfs})"
        )
    
    async def reason(
        self,
        input_data: Any,
        depth: Optional[ReasoningDepth] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> IntraAgentDecision:
        """
        Execute complete hierarchical reasoning process.
        
        Args:
            input_data: Input to reason about
            depth: Reasoning depth (None = use default)
            context: Additional context for reasoning
        
        Returns:
            IntraAgentDecision with complete reasoning chain
        """
        start_time = time.time()
        depth = depth or self.default_depth
        context = context or {}
        
        decision = IntraAgentDecision(
            agent_name=self.agent_name,
            input_data=input_data,
            final_decision=None,
            confidence=0.0,
            reasoning_depth=depth
        )
        
        try:
            logger.info(f"{self.agent_name} starting {depth.name} reasoning...")
            
            # LEVEL 1: PERCEPTION
            level1 = await self._level1_perception(input_data, context, depth)
            decision.cognitive_levels.append(level1)
            
            # LEVEL 2: ANALYSIS
            level2 = await self._level2_analysis(level1.output_data, context, depth)
            decision.cognitive_levels.append(level2)
            
            # LEVEL 3: SYNTHESIS
            level3 = await self._level3_synthesis(
                level2.output_data,
                alternatives=level2.alternatives,
                context=context,
                depth=depth
            )
            decision.cognitive_levels.append(level3)
            
            # LEVEL 4: EVALUATION
            level4 = await self._level4_evaluation(
                level3.output_data,
                all_alternatives=[lvl.alternatives for lvl in [level1, level2, level3]],
                context=context,
                depth=depth
            )
            decision.cognitive_levels.append(level4)
            
            # LEVEL 5: DECISION
            level5 = await self._level5_decision(
                level4.output_data,
                confidence=level4.confidence,
                context=context,
                depth=depth
            )
            decision.cognitive_levels.append(level5)
            
            # Build thought tree if enabled
            if self.enable_tree_of_selfs:
                decision.thought_tree = await self._build_thought_tree(
                    decision.cognitive_levels,
                    depth
                )
            
            # Finalize decision
            decision.final_decision = level5.output_data
            decision.confidence = level5.confidence
            decision.alternatives_considered = sum(
                len(lvl.alternatives) for lvl in decision.cognitive_levels
            )
            decision.total_duration_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self.total_decisions += 1
            self.total_reasoning_time += decision.total_duration_ms
            self.reasoning_history.append(decision)
            
            logger.info(
                f"{self.agent_name} completed {depth.name} reasoning: "
                f"decision={decision.final_decision}, "
                f"confidence={decision.confidence:.2f}, "
                f"duration={decision.total_duration_ms:.1f}ms, "
                f"alternatives={decision.alternatives_considered}"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"{self.agent_name} reasoning error: {e}", exc_info=True)
            decision.final_decision = None
            decision.confidence = 0.0
            decision.total_duration_ms = (time.time() - start_time) * 1000
            return decision
    
    async def _level1_perception(
        self,
        input_data: Any,
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> CognitiveLevel:
        """
        Level 1: Perception - Raw input processing and feature extraction.
        
        Extracts basic features, identifies patterns, normalizes input.
        Branches to consider alternative interpretations of input.
        """
        start = time.time()
        level = CognitiveLevel(level=1, name="Perception", input_data=input_data)
        
        level.add_trace("Beginning perceptual processing")
        
        # Basic feature extraction
        features = self._extract_features(input_data)
        level.add_trace(f"Extracted {len(features)} base features")
        
        # Generate alternative interpretations
        if depth.value >= ReasoningDepth.MODERATE.value:
            alternatives = await self._generate_perception_alternatives(
                input_data,
                features,
                max_alternatives=min(self.max_branches, depth.value)
            )
            level.alternatives = alternatives
            level.branches_explored = len(alternatives)
            level.add_trace(f"Explored {len(alternatives)} alternative interpretations")
        
        # Select primary interpretation
        level.output_data = {
            'features': features,
            'primary_interpretation': features.get('primary', input_data),
            'alternatives': level.alternatives,
            'perceptual_confidence': 0.8  # Base confidence
        }
        
        level.confidence = level.output_data['perceptual_confidence']
        level.duration_ms = (time.time() - start) * 1000
        level.add_trace(f"Perception complete (confidence: {level.confidence:.2f})")
        
        return level
    
    async def _level2_analysis(
        self,
        perception_output: Dict[str, Any],
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> CognitiveLevel:
        """
        Level 2: Analysis - Pattern detection and structural analysis.
        
        Identifies patterns, relationships, anomalies.
        Branches to explore alternative analytical frameworks.
        """
        start = time.time()
        level = CognitiveLevel(level=2, name="Analysis", input_data=perception_output)
        
        level.add_trace("Beginning analytical processing")
        
        features = perception_output['features']
        
        # Pattern detection
        patterns = self._detect_patterns(features)
        level.add_trace(f"Detected {len(patterns)} patterns")
        
        # Structural analysis
        structure = self._analyze_structure(features, patterns)
        level.add_trace(f"Analyzed structure: {structure.get('type', 'unknown')}")
        
        # Anomaly detection
        anomalies = self._detect_anomalies(features, context)
        if anomalies:
            level.add_trace(f"⚠️ Detected {len(anomalies)} anomalies")
        
        # Generate alternative analyses
        if depth.value >= ReasoningDepth.MODERATE.value:
            alternatives = await self._generate_analysis_alternatives(
                features,
                patterns,
                structure,
                max_alternatives=min(self.max_branches, depth.value)
            )
            level.alternatives = alternatives
            level.branches_explored = len(alternatives)
            level.add_trace(f"Explored {len(alternatives)} alternative analyses")
        
        # Confidence based on pattern clarity and anomaly presence
        analysis_confidence = 0.7
        if len(patterns) > 3:
            analysis_confidence += 0.1
        if anomalies:
            analysis_confidence -= 0.1 * len(anomalies)
        analysis_confidence = max(0.1, min(0.95, analysis_confidence))
        
        level.output_data = {
            'patterns': patterns,
            'structure': structure,
            'anomalies': anomalies,
            'alternatives': level.alternatives,
            'analysis_confidence': analysis_confidence
        }
        
        level.confidence = analysis_confidence
        level.duration_ms = (time.time() - start) * 1000
        level.add_trace(f"Analysis complete (confidence: {level.confidence:.2f})")
        
        return level
    
    async def _level3_synthesis(
        self,
        analysis_output: Dict[str, Any],
        alternatives: List[Any],
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> CognitiveLevel:
        """
        Level 3: Synthesis - Integration and context building.
        
        Combines analysis with context, builds coherent understanding.
        Branches to explore alternative synthetic frameworks.
        """
        start = time.time()
        level = CognitiveLevel(level=3, name="Synthesis", input_data=analysis_output)
        
        level.add_trace("Beginning synthesis processing")
        
        patterns = analysis_output['patterns']
        structure = analysis_output['structure']
        
        # Integrate with context
        integrated = self._integrate_with_context(patterns, structure, context)
        level.add_trace(f"Integrated {len(patterns)} patterns with context")
        
        # Build coherent narrative
        narrative = self._build_narrative(integrated, context)
        level.add_trace(f"Constructed narrative: {narrative.get('theme', 'complex')}")
        
        # Identify implications
        implications = self._identify_implications(integrated, narrative)
        level.add_trace(f"Identified {len(implications)} implications")
        
        # Generate alternative syntheses
        if depth.value >= ReasoningDepth.DEEP.value:
            alt_syntheses = await self._generate_synthesis_alternatives(
                integrated,
                narrative,
                implications,
                max_alternatives=min(self.max_branches, depth.value)
            )
            level.alternatives = alt_syntheses
            level.branches_explored = len(alt_syntheses)
            level.add_trace(f"Explored {len(alt_syntheses)} alternative syntheses")
        
        # Confidence based on coherence and completeness
        synthesis_confidence = 0.75
        if narrative.get('coherence', 0) > 0.7:
            synthesis_confidence += 0.1
        if len(implications) > 2:
            synthesis_confidence += 0.05
        synthesis_confidence = max(0.1, min(0.95, synthesis_confidence))
        
        level.output_data = {
            'integrated_understanding': integrated,
            'narrative': narrative,
            'implications': implications,
            'alternatives': level.alternatives,
            'synthesis_confidence': synthesis_confidence
        }
        
        level.confidence = synthesis_confidence
        level.duration_ms = (time.time() - start) * 1000
        level.add_trace(f"Synthesis complete (confidence: {level.confidence:.2f})")
        
        return level
    
    async def _level4_evaluation(
        self,
        synthesis_output: Dict[str, Any],
        all_alternatives: List[List[Any]],
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> CognitiveLevel:
        """
        Level 4: Evaluation - Quality assessment and confidence scoring.
        
        Evaluates synthesis quality, compares alternatives, assesses risks.
        Branches to consider alternative evaluation criteria.
        """
        start = time.time()
        level = CognitiveLevel(level=4, name="Evaluation", input_data=synthesis_output)
        
        level.add_trace("Beginning evaluation processing")
        
        narrative = synthesis_output['narrative']
        implications = synthesis_output['implications']
        
        # Quality assessment
        quality = self._assess_quality(synthesis_output, context)
        level.add_trace(f"Quality score: {quality:.2f}")
        
        # Risk assessment
        risks = self._assess_risks(implications, context)
        level.add_trace(f"Identified {len(risks)} risk factors")
        
        # Compare alternatives
        if depth.value >= ReasoningDepth.DEEP.value and all_alternatives:
            comparison = await self._compare_alternatives(
                synthesis_output,
                all_alternatives,
                quality,
                risks
            )
            level.alternatives = comparison['ranked_alternatives']
            level.branches_explored = len(level.alternatives)
            level.add_trace(f"Compared {len(level.alternatives)} alternative paths")
        
        # Uncertainty quantification
        uncertainty = self._quantify_uncertainty(
            synthesis_output,
            risks,
            all_alternatives
        )
        level.add_trace(f"Uncertainty quantified: {uncertainty:.2f}")
        
        # Final confidence calculation
        evaluation_confidence = quality * (1 - uncertainty * 0.5)
        if risks:
            evaluation_confidence *= 0.9  # Penalize for risks
        evaluation_confidence = max(0.1, min(0.95, evaluation_confidence))
        
        level.output_data = {
            'quality_score': quality,
            'risks': risks,
            'uncertainty': uncertainty,
            'alternative_comparison': level.alternatives,
            'evaluation_confidence': evaluation_confidence,
            'recommendation': 'proceed' if evaluation_confidence > 0.6 else 'reconsider'
        }
        
        level.confidence = evaluation_confidence
        level.duration_ms = (time.time() - start) * 1000
        level.add_trace(f"Evaluation complete (confidence: {level.confidence:.2f})")
        
        return level
    
    async def _level5_decision(
        self,
        evaluation_output: Dict[str, Any],
        confidence: float,
        context: Dict[str, Any],
        depth: ReasoningDepth
    ) -> CognitiveLevel:
        """
        Level 5: Decision - Final action selection and commitment.
        
        Makes final decision based on all previous levels.
        Branches to explore decision consequences (what-if analysis).
        """
        start = time.time()
        level = CognitiveLevel(level=5, name="Decision", input_data=evaluation_output)
        
        level.add_trace("Beginning decision processing")
        
        recommendation = evaluation_output['recommendation']
        quality = evaluation_output['quality_score']
        risks = evaluation_output['risks']
        
        # Generate decision options
        options = self._generate_decision_options(
            evaluation_output,
            context
        )
        level.add_trace(f"Generated {len(options)} decision options")
        
        # Select best option
        best_option = self._select_best_option(options, quality, risks, confidence)
        level.add_trace(f"Selected option: {best_option.get('action', 'unknown')}")
        
        # What-if analysis (consequences)
        if depth.value >= ReasoningDepth.DEEP.value:
            consequences = await self._analyze_consequences(
                best_option,
                options,
                max_scenarios=min(self.max_branches, depth.value)
            )
            level.alternatives = consequences
            level.branches_explored = len(consequences)
            level.add_trace(f"Analyzed {len(consequences)} consequence scenarios")
        
        # Commitment level
        commitment = self._calculate_commitment(confidence, risks)
        level.add_trace(f"Commitment level: {commitment:.2f}")
        
        # Final decision confidence
        decision_confidence = confidence * commitment
        decision_confidence = max(0.1, min(0.95, decision_confidence))
        
        level.output_data = {
            'selected_option': best_option,
            'all_options': options,
            'consequences': level.alternatives,
            'commitment_level': commitment,
            'decision_confidence': decision_confidence,
            'rationale': self._generate_rationale(
                best_option,
                evaluation_output,
                decision_confidence
            )
        }
        
        level.confidence = decision_confidence
        level.duration_ms = (time.time() - start) * 1000
        level.add_trace(f"Decision finalized (confidence: {level.confidence:.2f})")
        
        return level
    
    async def _build_thought_tree(
        self,
        cognitive_levels: List[CognitiveLevel],
        depth: ReasoningDepth
    ) -> List[ThoughtBranch]:
        """
        Build Tree-of-Selfs from cognitive levels.
        
        Each alternative explored becomes a branch in the thought tree.
        """
        thought_tree: List[ThoughtBranch] = []
        branch_counter = 0
        
        for level in cognitive_levels:
            parent_id = f"L{level.level}_main"
            
            # Main branch
            main_branch = ThoughtBranch(
                branch_id=parent_id,
                parent_id=None if level.level == 1 else f"L{level.level-1}_main",
                depth=level.level,
                hypothesis=f"Level {level.level} main path",
                evidence=level.reasoning_trace,
                confidence=level.confidence,
                consequences=[]
            )
            thought_tree.append(main_branch)
            
            # Alternative branches
            for i, alt in enumerate(level.alternatives):
                branch_id = f"L{level.level}_alt{i}"
                alt_branch = ThoughtBranch(
                    branch_id=branch_id,
                    parent_id=parent_id,
                    depth=level.level,
                    hypothesis=f"Level {level.level} alternative {i+1}",
                    evidence=[f"Alternative interpretation: {alt}"],
                    confidence=level.confidence * 0.8,  # Slightly lower for alternatives
                    consequences=[]
                )
                thought_tree.append(alt_branch)
                main_branch.children.append(branch_id)
                branch_counter += 1
        
        logger.debug(f"Built thought tree with {len(thought_tree)} branches")
        return thought_tree
    
    # Helper methods for cognitive processing
    
    def _extract_features(self, input_data: Any) -> Dict[str, Any]:
        """Extract basic features from input"""
        if isinstance(input_data, dict):
            return {
                'primary': input_data,
                'keys': list(input_data.keys()),
                'complexity': len(input_data),
                'type': 'structured'
            }
        elif isinstance(input_data, str):
            return {
                'primary': input_data,
                'length': len(input_data),
                'words': len(input_data.split()),
                'type': 'text'
            }
        else:
            return {
                'primary': input_data,
                'type': type(input_data).__name__,
                'complexity': 1
            }
    
    async def _generate_perception_alternatives(
        self,
        input_data: Any,
        features: Dict[str, Any],
        max_alternatives: int
    ) -> List[Any]:
        """Generate alternative perceptual interpretations"""
        alternatives = []
        
        # Alternative 1: Conservative interpretation
        if max_alternatives >= 1:
            alternatives.append({
                'interpretation': 'conservative',
                'features': features,
                'emphasis': 'risk_minimization'
            })
        
        # Alternative 2: Optimistic interpretation
        if max_alternatives >= 2:
            alternatives.append({
                'interpretation': 'optimistic',
                'features': features,
                'emphasis': 'opportunity_maximization'
            })
        
        # Alternative 3: Neutral/analytical
        if max_alternatives >= 3:
            alternatives.append({
                'interpretation': 'neutral',
                'features': features,
                'emphasis': 'objective_analysis'
            })
        
        return alternatives[:max_alternatives]
    
    def _detect_patterns(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect patterns in features"""
        patterns = []
        
        # Simple pattern detection
        if features.get('complexity', 0) > 5:
            patterns.append({'type': 'high_complexity', 'confidence': 0.8})
        
        if features.get('type') == 'structured':
            patterns.append({'type': 'structured_data', 'confidence': 0.9})
        
        return patterns
    
    def _analyze_structure(
        self,
        features: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze structural properties"""
        return {
            'type': features.get('type', 'unknown'),
            'complexity_level': 'high' if features.get('complexity', 0) > 5 else 'low',
            'pattern_count': len(patterns)
        }
    
    def _detect_anomalies(
        self,
        features: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies"""
        anomalies = []
        
        # Simple anomaly detection
        expected_type = context.get('expected_type')
        if expected_type and features.get('type') != expected_type:
            anomalies.append({
                'type': 'type_mismatch',
                'expected': expected_type,
                'actual': features.get('type')
            })
        
        return anomalies
    
    async def _generate_analysis_alternatives(
        self,
        features: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        structure: Dict[str, Any],
        max_alternatives: int
    ) -> List[Any]:
        """Generate alternative analytical frameworks"""
        alternatives = []
        
        for i in range(min(max_alternatives, 3)):
            alternatives.append({
                'framework': f'analytical_framework_{i+1}',
                'focus': ['patterns', 'structure', 'anomalies'][i % 3],
                'emphasis': ['precision', 'breadth', 'depth'][i % 3]
            })
        
        return alternatives
    
    def _integrate_with_context(
        self,
        patterns: List[Dict[str, Any]],
        structure: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate analysis with context"""
        return {
            'patterns': patterns,
            'structure': structure,
            'context_applied': True,
            'integration_quality': 0.75
        }
    
    def _build_narrative(
        self,
        integrated: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build coherent narrative"""
        return {
            'theme': 'analytical_synthesis',
            'coherence': 0.8,
            'completeness': 0.7
        }
    
    def _identify_implications(
        self,
        integrated: Dict[str, Any],
        narrative: Dict[str, Any]
    ) -> List[str]:
        """Identify implications"""
        return [
            'Primary implication identified',
            'Secondary effect noted',
            'Long-term consequence projected'
        ]
    
    async def _generate_synthesis_alternatives(
        self,
        integrated: Dict[str, Any],
        narrative: Dict[str, Any],
        implications: List[str],
        max_alternatives: int
    ) -> List[Any]:
        """Generate alternative syntheses"""
        alternatives = []
        
        for i in range(min(max_alternatives, 3)):
            alternatives.append({
                'synthesis_approach': f'approach_{i+1}',
                'narrative_emphasis': ['causal', 'correlational', 'emergent'][i % 3],
                'implication_focus': implications[i % len(implications)] if implications else 'general'
            })
        
        return alternatives
    
    def _assess_quality(
        self,
        synthesis_output: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Assess synthesis quality"""
        narrative = synthesis_output.get('narrative', {})
        coherence = narrative.get('coherence', 0.5)
        completeness = narrative.get('completeness', 0.5)
        
        return (coherence + completeness) / 2
    
    def _assess_risks(
        self,
        implications: List[str],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assess risks"""
        risks = []
        
        if len(implications) > 3:
            risks.append({
                'type': 'complexity_risk',
                'severity': 'medium',
                'description': 'Multiple implications increase uncertainty'
            })
        
        return risks
    
    async def _compare_alternatives(
        self,
        synthesis_output: Dict[str, Any],
        all_alternatives: List[List[Any]],
        quality: float,
        risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare alternative reasoning paths"""
        # Flatten alternatives
        flat_alternatives = []
        for alt_list in all_alternatives:
            flat_alternatives.extend(alt_list)
        
        # Rank by quality and risk
        ranked = sorted(
            flat_alternatives,
            key=lambda x: (quality - len(risks) * 0.1),
            reverse=True
        )
        
        return {
            'ranked_alternatives': ranked[:5],  # Top 5
            'comparison_basis': 'quality_and_risk'
        }
    
    def _quantify_uncertainty(
        self,
        synthesis_output: Dict[str, Any],
        risks: List[Dict[str, Any]],
        all_alternatives: List[List[Any]]
    ) -> float:
        """Quantify uncertainty"""
        base_uncertainty = 0.2
        
        # More alternatives = more uncertainty
        total_alternatives = sum(len(alts) for alts in all_alternatives)
        uncertainty = base_uncertainty + (total_alternatives * 0.02)
        
        # Risks increase uncertainty
        uncertainty += len(risks) * 0.05
        
        return min(0.9, uncertainty)
    
    def _generate_decision_options(
        self,
        evaluation_output: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate decision options"""
        recommendation = evaluation_output['recommendation']
        
        options = [
            {
                'action': 'proceed',
                'rationale': 'Evaluation supports proceeding',
                'priority': 1 if recommendation == 'proceed' else 2
            },
            {
                'action': 'proceed_with_caution',
                'rationale': 'Proceed but monitor closely',
                'priority': 2
            },
            {
                'action': 'defer',
                'rationale': 'Gather more information',
                'priority': 2 if recommendation == 'reconsider' else 3
            }
        ]
        
        return sorted(options, key=lambda x: x['priority'])
    
    def _select_best_option(
        self,
        options: List[Dict[str, Any]],
        quality: float,
        risks: List[Dict[str, Any]],
        confidence: float
    ) -> Dict[str, Any]:
        """Select best decision option"""
        # Simple selection: first option (highest priority)
        best = options[0] if options else {'action': 'unknown'}
        
        # Adjust based on risks
        if risks and best['action'] == 'proceed':
            best = options[1] if len(options) > 1 else best
        
        return best
    
    async def _analyze_consequences(
        self,
        selected_option: Dict[str, Any],
        all_options: List[Dict[str, Any]],
        max_scenarios: int
    ) -> List[Dict[str, Any]]:
        """Analyze decision consequences (what-if)"""
        consequences = []
        
        for i in range(min(max_scenarios, 3)):
            consequences.append({
                'scenario': f'consequence_scenario_{i+1}',
                'likelihood': 0.7 - (i * 0.1),
                'impact': ['positive', 'neutral', 'negative'][i % 3],
                'description': f"Potential outcome path {i+1}"
            })
        
        return consequences
    
    def _calculate_commitment(self, confidence: float, risks: List[Dict[str, Any]]) -> float:
        """Calculate commitment level"""
        commitment = confidence
        
        # Reduce commitment for each risk
        commitment -= len(risks) * 0.05
        
        return max(0.1, min(0.95, commitment))
    
    def _generate_rationale(
        self,
        selected_option: Dict[str, Any],
        evaluation_output: Dict[str, Any],
        confidence: float
    ) -> str:
        """Generate decision rationale"""
        action = selected_option.get('action', 'unknown')
        quality = evaluation_output.get('quality_score', 0)
        
        return (
            f"Selected '{action}' based on quality score of {quality:.2f} "
            f"and confidence of {confidence:.2f}"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reasoning statistics"""
        if not self.reasoning_history:
            return {
                'total_decisions': 0,
                'avg_duration_ms': 0.0,
                'avg_confidence': 0.0,
                'avg_alternatives': 0.0
            }
        
        avg_duration = self.total_reasoning_time / self.total_decisions
        avg_confidence = sum(d.confidence for d in self.reasoning_history) / len(self.reasoning_history)
        avg_alternatives = sum(d.alternatives_considered for d in self.reasoning_history) / len(self.reasoning_history)
        
        return {
            'total_decisions': self.total_decisions,
            'avg_duration_ms': avg_duration,
            'avg_confidence': avg_confidence,
            'avg_alternatives': avg_alternatives,
            'history_size': len(self.reasoning_history)
        }
