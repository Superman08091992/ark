#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kyle-Specific Hierarchical Reasoning

Extends IntraAgentReasoner with domain-specific logic for market signal analysis.
Kyle's cognitive process:
- L1 Perception: Extract market features (price, volume, sentiment)
- L2 Analysis: Detect technical patterns, identify trends
- L3 Synthesis: Integrate with historical context, build narrative
- L4 Evaluation: Assess signal quality, quantify risk
- L5 Decision: Generate actionable signal with confidence
"""

import logging
from typing import Any, Dict, List, Optional
from reasoning.intra_agent_reasoner import IntraAgentReasoner, CognitiveLevel, ReasoningDepth
import time

logger = logging.getLogger(__name__)


class KyleReasoner(IntraAgentReasoner):
    """Kyle-specific hierarchical reasoner for market signal analysis"""
    
    def __init__(
        self,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP,
        enable_tree_of_selfs: bool = True,
        max_branches_per_level: int = 5
    ):
        super().__init__(
            agent_name="Kyle",
            default_depth=default_depth,
            enable_tree_of_selfs=enable_tree_of_selfs,
            max_branches_per_level=max_branches_per_level
        )
    
    def _extract_features(self, input_data: Any) -> Dict[str, Any]:
        """Kyle-specific feature extraction for market data"""
        if not isinstance(input_data, dict):
            return super()._extract_features(input_data)
        
        # Extract market-specific features
        features = {
            'type': 'market_signal',
            'symbol': input_data.get('symbol', 'UNKNOWN'),
            'price_change': input_data.get('price_change', 0.0),
            'volume_surge': input_data.get('volume_surge', 1.0),
            'sentiment_score': input_data.get('sentiment_score', 0.0),
            'timestamp': input_data.get('timestamp'),
            'complexity': 4  # Market signals have moderate complexity
        }
        
        # Calculate derived features
        features['price_direction'] = 'bullish' if features['price_change'] > 0 else 'bearish'
        features['volume_category'] = self._categorize_volume(features['volume_surge'])
        features['sentiment_category'] = self._categorize_sentiment(features['sentiment_score'])
        features['volatility_indicator'] = abs(features['price_change'])
        
        return features
    
    def _categorize_volume(self, volume_surge: float) -> str:
        """Categorize volume surge"""
        if volume_surge < 0.8:
            return 'low'
        elif volume_surge < 1.2:
            return 'normal'
        elif volume_surge < 1.8:
            return 'elevated'
        else:
            return 'surge'
    
    def _categorize_sentiment(self, sentiment_score: float) -> str:
        """Categorize sentiment score"""
        if sentiment_score < -0.6:
            return 'very_bearish'
        elif sentiment_score < -0.2:
            return 'bearish'
        elif sentiment_score < 0.2:
            return 'neutral'
        elif sentiment_score < 0.6:
            return 'bullish'
        else:
            return 'very_bullish'
    
    def _detect_patterns(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Kyle-specific pattern detection"""
        patterns = []
        
        price_change = features.get('price_change', 0.0)
        volume_surge = features.get('volume_surge', 1.0)
        sentiment_score = features.get('sentiment_score', 0.0)
        
        # Breakout pattern
        if abs(price_change) > 0.03 and volume_surge > 1.5:
            patterns.append({
                'type': 'breakout',
                'confidence': min(0.95, abs(price_change) * 10 + volume_surge * 0.2),
                'direction': 'upward' if price_change > 0 else 'downward',
                'strength': 'strong' if volume_surge > 2.0 else 'moderate'
            })
        
        # Momentum pattern
        if abs(price_change) > 0.02 and abs(sentiment_score) > 0.5:
            # Check if sentiment aligns with price
            sentiment_aligned = (price_change > 0 and sentiment_score > 0) or \
                              (price_change < 0 and sentiment_score < 0)
            patterns.append({
                'type': 'momentum',
                'confidence': 0.7 if sentiment_aligned else 0.4,
                'alignment': 'confirmed' if sentiment_aligned else 'divergent',
                'strength': 'high' if abs(sentiment_score) > 0.7 else 'moderate'
            })
        
        # Reversal pattern (divergence between price and sentiment)
        if abs(price_change) > 0.02:
            divergence = (price_change > 0 and sentiment_score < -0.3) or \
                        (price_change < 0 and sentiment_score > 0.3)
            if divergence:
                patterns.append({
                    'type': 'reversal',
                    'confidence': 0.6,
                    'signal': 'potential_reversal',
                    'risk': 'high'
                })
        
        # Consolidation pattern (low volatility)
        if abs(price_change) < 0.01 and volume_surge < 1.2:
            patterns.append({
                'type': 'consolidation',
                'confidence': 0.8,
                'state': 'accumulation' if volume_surge > 0.9 else 'distribution'
            })
        
        # Volume anomaly pattern
        if volume_surge > 2.0:
            patterns.append({
                'type': 'volume_anomaly',
                'confidence': min(0.95, volume_surge / 3.0),
                'significance': 'high' if volume_surge > 2.5 else 'moderate'
            })
        
        return patterns
    
    def _analyze_structure(
        self,
        features: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Kyle-specific structural analysis"""
        # Determine dominant pattern
        dominant_pattern = None
        max_confidence = 0.0
        for pattern in patterns:
            if pattern['confidence'] > max_confidence:
                max_confidence = pattern['confidence']
                dominant_pattern = pattern['type']
        
        # Market state assessment
        volatility = features.get('volatility_indicator', 0.0)
        if volatility > 0.05:
            market_state = 'high_volatility'
        elif volatility > 0.02:
            market_state = 'moderate_volatility'
        else:
            market_state = 'low_volatility'
        
        return {
            'type': 'technical_analysis',
            'dominant_pattern': dominant_pattern,
            'pattern_count': len(patterns),
            'pattern_diversity': len(set(p['type'] for p in patterns)),
            'market_state': market_state,
            'signal_clarity': 'high' if len(patterns) <= 2 else 'complex',
            'complexity_level': 'high' if len(patterns) > 3 else 'moderate'
        }
    
    def _detect_anomalies(
        self,
        features: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Kyle-specific anomaly detection"""
        anomalies = []
        
        # Check for extreme price moves
        price_change = abs(features.get('price_change', 0.0))
        if price_change > 0.10:  # >10% move
            anomalies.append({
                'type': 'extreme_price_movement',
                'severity': 'high',
                'value': price_change,
                'description': f'Unusual price move: {price_change:.1%}'
            })
        
        # Check for volume spikes without price change
        volume_surge = features.get('volume_surge', 1.0)
        if volume_surge > 2.5 and price_change < 0.01:
            anomalies.append({
                'type': 'volume_price_divergence',
                'severity': 'medium',
                'description': 'High volume without price movement'
            })
        
        # Check historical pattern consistency
        historical_patterns = context.get('historical_patterns', [])
        if historical_patterns:
            # Check if current signal aligns with recent patterns
            recent_successes = sum(1 for p in historical_patterns if p.get('outcome') == 'success')
            if len(historical_patterns) >= 3 and recent_successes / len(historical_patterns) < 0.3:
                anomalies.append({
                    'type': 'pattern_inconsistency',
                    'severity': 'medium',
                    'description': 'Current pattern has low historical success rate'
                })
        
        return anomalies
    
    def _integrate_with_context(
        self,
        patterns: List[Dict[str, Any]],
        structure: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kyle-specific context integration"""
        # Get market sentiment from context
        market_sentiment = context.get('market_sentiment', 'neutral')
        historical_patterns = context.get('historical_patterns', [])
        threshold = context.get('threshold', 0.7)
        
        # Calculate pattern alignment with historical success
        pattern_confidence_adjustment = 0.0
        if historical_patterns:
            for pattern in patterns:
                similar_historical = [
                    hp for hp in historical_patterns
                    if hp.get('symbol') == pattern.get('type')
                ]
                if similar_historical:
                    success_rate = sum(
                        1 for hp in similar_historical
                        if hp.get('signal_strength', 0) > threshold
                    ) / len(similar_historical)
                    pattern_confidence_adjustment += success_rate * 0.1
        
        return {
            'patterns': patterns,
            'structure': structure,
            'market_sentiment': market_sentiment,
            'historical_alignment': pattern_confidence_adjustment,
            'context_applied': True,
            'integration_quality': 0.8 + pattern_confidence_adjustment,
            'threshold': threshold
        }
    
    def _build_narrative(
        self,
        integrated: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kyle-specific narrative construction"""
        patterns = integrated.get('patterns', [])
        structure = integrated.get('structure', {})
        market_sentiment = integrated.get('market_sentiment', 'neutral')
        
        # Build coherent signal narrative
        if not patterns:
            theme = 'no_clear_signal'
            coherence = 0.3
        elif len(patterns) == 1:
            theme = f"clear_{patterns[0]['type']}_signal"
            coherence = 0.9
        elif structure.get('dominant_pattern'):
            theme = f"dominant_{structure['dominant_pattern']}_pattern"
            coherence = 0.7
        else:
            theme = 'complex_mixed_signals'
            coherence = 0.5
        
        # Assess completeness
        has_price = 'price_change' in integrated.get('structure', {})
        has_volume = any('volume' in p['type'] for p in patterns)
        has_sentiment = market_sentiment != 'neutral'
        completeness = sum([has_price, has_volume, has_sentiment]) / 3.0
        
        return {
            'theme': theme,
            'coherence': coherence,
            'completeness': completeness,
            'primary_signal': structure.get('dominant_pattern', 'unclear'),
            'market_context': market_sentiment
        }
    
    def _identify_implications(
        self,
        integrated: Dict[str, Any],
        narrative: Dict[str, Any]
    ) -> List[str]:
        """Kyle-specific implication identification"""
        implications = []
        
        patterns = integrated.get('patterns', [])
        theme = narrative.get('theme', '')
        
        # Pattern-specific implications
        for pattern in patterns:
            ptype = pattern['type']
            confidence = pattern['confidence']
            
            if ptype == 'breakout' and confidence > 0.7:
                direction = pattern.get('direction', 'unknown')
                implications.append(f"Strong {direction} breakout potential (conf: {confidence:.2f})")
            
            elif ptype == 'momentum' and pattern.get('alignment') == 'confirmed':
                implications.append(f"Momentum confirmed by sentiment alignment")
            
            elif ptype == 'reversal':
                implications.append(f"⚠️ Potential trend reversal - monitor closely")
            
            elif ptype == 'volume_anomaly':
                implications.append(f"Unusual institutional activity detected")
        
        # Market state implications
        structure = integrated.get('structure', {})
        market_state = structure.get('market_state')
        if market_state == 'high_volatility':
            implications.append("High volatility - increased risk and opportunity")
        
        if not implications:
            implications.append("Normal market behavior - no significant implications")
        
        return implications
    
    def _assess_quality(
        self,
        synthesis_output: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Kyle-specific quality assessment"""
        narrative = synthesis_output.get('narrative', {})
        coherence = narrative.get('coherence', 0.5)
        completeness = narrative.get('completeness', 0.5)
        integration_quality = synthesis_output.get('integrated', {}).get('integration_quality', 0.5)
        
        # Weight factors for signal quality
        quality = (
            coherence * 0.4 +
            completeness * 0.3 +
            integration_quality * 0.3
        )
        
        return min(0.95, max(0.1, quality))
    
    def _assess_risks(
        self,
        implications: List[str],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Kyle-specific risk assessment"""
        risks = []
        
        # Check for reversal warnings
        if any('reversal' in imp.lower() for imp in implications):
            risks.append({
                'type': 'reversal_risk',
                'severity': 'high',
                'description': 'Potential trend reversal detected'
            })
        
        # Check for high volatility
        if any('volatility' in imp.lower() for imp in implications):
            risks.append({
                'type': 'volatility_risk',
                'severity': 'medium',
                'description': 'Market volatility elevated'
            })
        
        # Check for signal complexity
        if len(implications) > 4:
            risks.append({
                'type': 'complexity_risk',
                'severity': 'medium',
                'description': 'Multiple conflicting signals'
            })
        
        # Historical pattern risk
        historical_patterns = context.get('historical_patterns', [])
        if historical_patterns and len(historical_patterns) >= 3:
            recent_failures = sum(
                1 for hp in historical_patterns[-5:]
                if hp.get('signal_strength', 0) < context.get('threshold', 0.7)
            )
            if recent_failures >= 3:
                risks.append({
                    'type': 'historical_performance_risk',
                    'severity': 'medium',
                    'description': 'Recent pattern has poor track record'
                })
        
        return risks
    
    def _generate_decision_options(
        self,
        evaluation_output: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Kyle-specific decision option generation"""
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        recommendation = evaluation_output.get('recommendation', 'defer')
        
        threshold = context.get('threshold', 0.7)
        
        options = []
        
        # Strong signal option
        if quality > threshold and len(risks) <= 1:
            options.append({
                'action': 'strong_signal',
                'signal_strength': min(0.95, quality),
                'description': 'Clear actionable signal detected',
                'priority': 1,
                'patterns': []  # Will be populated
            })
        
        # Moderate signal option
        if quality > threshold * 0.7:
            options.append({
                'action': 'moderate_signal',
                'signal_strength': quality * 0.8,
                'description': 'Moderate signal - proceed with caution',
                'priority': 2,
                'patterns': []
            })
        
        # Weak signal option
        if quality > threshold * 0.5:
            options.append({
                'action': 'weak_signal',
                'signal_strength': quality * 0.6,
                'description': 'Weak signal - monitoring recommended',
                'priority': 3,
                'patterns': []
            })
        
        # No signal option
        options.append({
            'action': 'no_signal',
            'signal_strength': 0.0,
            'description': 'No actionable signal - normal market behavior',
            'priority': 4,
            'patterns': []
        })
        
        return sorted(options, key=lambda x: x['priority'])
    
    def _select_best_option(
        self,
        options: List[Dict[str, Any]],
        quality: float,
        risks: List[Dict[str, Any]],
        confidence: float
    ) -> Dict[str, Any]:
        """Kyle-specific option selection"""
        if not options:
            return {
                'action': 'no_signal',
                'signal_strength': 0.0,
                'description': 'No options available',
                'patterns': []
            }
        
        # Select based on quality and risk tolerance
        if risks:
            high_severity_risks = [r for r in risks if r.get('severity') == 'high']
            if high_severity_risks:
                # High risk - downgrade to more conservative option
                conservative_options = [o for o in options if o['priority'] >= 2]
                return conservative_options[0] if conservative_options else options[0]
        
        # No high risks - select highest priority (best) option
        return options[0]
    
    def _calculate_commitment(
        self,
        confidence: float,
        risks: List[Dict[str, Any]]
    ) -> float:
        """Kyle-specific commitment calculation"""
        commitment = confidence
        
        # Reduce commitment based on risk severity
        for risk in risks:
            severity = risk.get('severity', 'low')
            if severity == 'high':
                commitment *= 0.7
            elif severity == 'medium':
                commitment *= 0.85
            else:
                commitment *= 0.95
        
        return max(0.1, min(0.95, commitment))
    
    def _generate_rationale(
        self,
        selected_option: Dict[str, Any],
        evaluation_output: Dict[str, Any],
        confidence: float
    ) -> str:
        """Kyle-specific rationale generation"""
        action = selected_option.get('action', 'unknown')
        signal_strength = selected_option.get('signal_strength', 0.0)
        description = selected_option.get('description', '')
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        rationale = f"Kyle's Analysis: {description}\n"
        rationale += f"Signal Strength: {signal_strength:.2f}\n"
        rationale += f"Analysis Quality: {quality:.2f}\n"
        rationale += f"Overall Confidence: {confidence:.2f}\n"
        
        if risks:
            rationale += f"Risks Identified: {len(risks)}\n"
            for risk in risks:
                rationale += f"  - {risk.get('type', 'unknown')}: {risk.get('description', '')}\n"
        
        return rationale
