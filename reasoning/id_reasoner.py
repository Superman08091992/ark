#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID-Specific Hierarchical Reasoning

Extends IntraAgentReasoner with domain-specific logic for identity verification,
authentication, and pattern learning from user interactions.

ID's cognitive process:
- L1 Perception: Extract identity features and interaction patterns
- L2 Analysis: Detect behavioral patterns, consistency checks
- L3 Synthesis: Build evolving user model and personality profile
- L4 Evaluation: Assess authentication confidence and identity drift
- L5 Decision: Generate identity verdict and learning updates
"""

import logging
from typing import Any, Dict, List, Optional
from reasoning.intra_agent_reasoner import IntraAgentReasoner, ReasoningDepth
import time

logger = logging.getLogger(__name__)


class IDReasoner(IntraAgentReasoner):
    """ID-specific hierarchical reasoner for identity and authentication"""
    
    def __init__(
        self,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP,
        enable_tree_of_selfs: bool = True,
        max_branches_per_level: int = 5
    ):
        super().__init__(
            agent_name="ID",
            default_depth=default_depth,
            enable_tree_of_selfs=enable_tree_of_selfs,
            max_branches_per_level=max_branches_per_level
        )
    
    def _extract_features(self, input_data: Any) -> Dict[str, Any]:
        """ID-specific feature extraction for identity and patterns"""
        if not isinstance(input_data, dict):
            return super()._extract_features(input_data)
        
        features = {
            'type': 'identity_verification',
            'interaction_type': input_data.get('interaction_type', 'unknown'),
            'timestamp': input_data.get('timestamp')
        }
        
        # Behavioral patterns
        if 'behavior' in input_data:
            behavior = input_data['behavior']
            features['behavior_metrics'] = behavior
            features['has_behavior'] = True
        
        # Historical consistency
        if 'historical_patterns' in input_data:
            patterns = input_data['historical_patterns']
            features['num_historical_patterns'] = len(patterns) if isinstance(patterns, list) else 0
            features['has_history'] = features['num_historical_patterns'] > 0
        
        # Personality traits
        if 'personality_traits' in input_data:
            traits = input_data['personality_traits']
            features['personality_traits'] = traits
            features['num_traits'] = len(traits) if isinstance(traits, dict) else 0
        
        # Authentication credentials
        if 'credentials' in input_data:
            features['has_credentials'] = True
            features['credential_type'] = input_data.get('credential_type', 'unknown')
        
        # Learning signals
        if 'learning_signals' in input_data:
            signals = input_data['learning_signals']
            features['num_learning_signals'] = len(signals) if isinstance(signals, list) else 0
            features['has_learning'] = features['num_learning_signals'] > 0
        
        # Identity drift detection
        if 'baseline_model' in input_data and 'current_model' in input_data:
            features['identity_drift'] = self._calculate_drift(
                input_data['baseline_model'],
                input_data['current_model']
            )
        
        features['complexity'] = self._calculate_identity_complexity(features)
        
        return features
    
    def _calculate_drift(self, baseline: Any, current: Any) -> float:
        """Calculate identity drift"""
        if isinstance(baseline, dict) and isinstance(current, dict):
            # Simple drift calculation based on key differences
            all_keys = set(baseline.keys()) | set(current.keys())
            if not all_keys:
                return 0.0
            
            differences = 0
            for key in all_keys:
                if baseline.get(key) != current.get(key):
                    differences += 1
            
            return min(1.0, differences / len(all_keys))
        return 0.0
    
    def _calculate_identity_complexity(self, features: Dict[str, Any]) -> int:
        """Calculate complexity of identity verification"""
        complexity = 2
        complexity += features.get('num_historical_patterns', 0)
        complexity += features.get('num_traits', 0)
        complexity += features.get('num_learning_signals', 0)
        if features.get('identity_drift', 0) > 0.3:
            complexity += 2
        if not features.get('has_credentials', False):
            complexity += 1
        return min(complexity, 10)
    
    def _detect_patterns(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ID-specific pattern detection"""
        patterns = []
        
        # Consistent behavior pattern
        if features.get('has_history', False) and features.get('identity_drift', 0) < 0.2:
            patterns.append({
                'type': 'consistent_behavior',
                'confidence': 0.9,
                'description': 'Behavioral patterns consistent with historical baseline',
                'parameters': {'drift': features.get('identity_drift', 0)}
            })
        
        # Identity evolution pattern
        if features.get('identity_drift', 0) > 0.2 and features.get('identity_drift', 0) < 0.5:
            patterns.append({
                'type': 'identity_evolution',
                'confidence': 0.8,
                'description': 'Gradual identity evolution detected (natural growth)',
                'parameters': {'drift_rate': features.get('identity_drift', 0)}
            })
        
        # Identity anomaly pattern
        if features.get('identity_drift', 0) > 0.5:
            patterns.append({
                'type': 'identity_anomaly',
                'confidence': 0.85,
                'description': 'Significant deviation from baseline identity',
                'parameters': {
                    'drift_rate': features.get('identity_drift', 0),
                    'severity': 'high' if features['identity_drift'] > 0.7 else 'moderate'
                }
            })
        
        # Learning and adaptation pattern
        if features.get('has_learning', False):
            patterns.append({
                'type': 'active_learning',
                'confidence': 0.9,
                'description': 'Active learning from user interactions',
                'parameters': {'signals': features.get('num_learning_signals', 0)}
            })
        
        # Strong authentication pattern
        if features.get('has_credentials', False):
            patterns.append({
                'type': 'authenticated_access',
                'confidence': 0.95,
                'description': 'Strong authentication credentials present',
                'parameters': {'type': features.get('credential_type', 'unknown')}
            })
        
        # Personality trait pattern
        if features.get('num_traits', 0) >= 3:
            patterns.append({
                'type': 'rich_personality_profile',
                'confidence': 0.85,
                'description': 'Well-defined personality trait profile',
                'parameters': {'trait_count': features.get('num_traits', 0)}
            })
        
        return patterns
    
    def _analyze_structure(self, features: Dict[str, Any], patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ID-specific structural analysis"""
        # Identity verification structure
        has_credentials = features.get('has_credentials', False)
        has_history = features.get('has_history', False)
        drift = features.get('identity_drift', 0)
        
        if has_credentials and drift < 0.2:
            verification_structure = 'strong_authentication'
        elif has_history and drift < 0.4:
            verification_structure = 'behavioral_match'
        elif drift > 0.5:
            verification_structure = 'anomalous_identity'
        else:
            verification_structure = 'weak_verification'
        
        # Learning structure
        has_learning = features.get('has_learning', False)
        if has_learning:
            learning_structure = 'active_adaptation'
        elif has_history:
            learning_structure = 'passive_observation'
        else:
            learning_structure = 'initial_phase'
        
        # Dominant pattern
        dominant_pattern = None
        max_confidence = 0.0
        for pattern in patterns:
            if pattern['confidence'] > max_confidence:
                max_confidence = pattern['confidence']
                dominant_pattern = pattern['type']
        
        return {
            'type': 'identity_structure',
            'verification_structure': verification_structure,
            'learning_structure': learning_structure,
            'dominant_pattern': dominant_pattern,
            'pattern_count': len(patterns),
            'complexity_level': 'high' if features.get('complexity', 0) > 6 else 'moderate',
            'identity_drift': drift,
            'authenticated': has_credentials
        }
    
    def _detect_anomalies(self, features: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ID-specific anomaly detection"""
        anomalies = []
        
        # High identity drift
        drift = features.get('identity_drift', 0)
        if drift > 0.7:
            anomalies.append({
                'type': 'extreme_identity_drift',
                'severity': 'high',
                'description': f'Identity drift {drift:.1%} exceeds safe threshold - possible impersonation'
            })
        elif drift > 0.5:
            anomalies.append({
                'type': 'significant_drift',
                'severity': 'medium',
                'description': f'Identity drift {drift:.1%} indicates substantial change'
            })
        
        # Missing credentials
        if not features.get('has_credentials', False) and features.get('has_history', False):
            anomalies.append({
                'type': 'missing_authentication',
                'severity': 'medium',
                'description': 'Historical user but no authentication credentials'
            })
        
        # No historical data
        if not features.get('has_history', False):
            anomalies.append({
                'type': 'no_baseline',
                'severity': 'low',
                'description': 'No historical baseline for comparison'
            })
        
        # Behavioral inconsistency with stored patterns
        expected_behavior = context.get('expected_behavior')
        if expected_behavior and features.get('has_behavior', False):
            # In production, would do actual behavioral comparison
            anomalies.append({
                'type': 'behavioral_anomaly',
                'severity': 'low',
                'description': 'Behavioral patterns differ from expectations'
            })
        
        return anomalies
    
    def _integrate_with_context(self, patterns: List[Dict[str, Any]], structure: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """ID-specific context integration"""
        # Get identity context
        evolution_stage = context.get('evolution_stage', 'awakening')
        user_interactions = context.get('user_interactions', 0)
        reflection_depth = context.get('reflection_depth', 0.3)
        
        # Calculate authentication confidence
        auth_confidence = 0.5
        if structure.get('authenticated', False):
            auth_confidence += 0.3
        if structure.get('verification_structure') == 'strong_authentication':
            auth_confidence += 0.2
        elif structure.get('verification_structure') == 'behavioral_match':
            auth_confidence += 0.15
        auth_confidence = min(1.0, auth_confidence)
        
        # Calculate learning readiness
        learning_readiness = 0.5
        if structure.get('learning_structure') == 'active_adaptation':
            learning_readiness += 0.3
        if user_interactions > 10:
            learning_readiness += 0.2
        learning_readiness = min(1.0, learning_readiness)
        
        return {
            'patterns': patterns,
            'structure': structure,
            'authentication_confidence': auth_confidence,
            'learning_readiness': learning_readiness,
            'evolution_stage': evolution_stage,
            'user_interactions': user_interactions,
            'reflection_depth': reflection_depth,
            'context_applied': True,
            'integration_quality': (auth_confidence + learning_readiness) / 2
        }
    
    def _build_narrative(self, integrated: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """ID-specific narrative construction"""
        structure = integrated.get('structure', {})
        auth_confidence = integrated.get('authentication_confidence', 0.5)
        learning_readiness = integrated.get('learning_readiness', 0.5)
        
        # Build identity narrative
        verification_structure = structure.get('verification_structure', 'unknown')
        if verification_structure == 'strong_authentication':
            theme = 'authenticated_known_identity'
            coherence = 0.95
        elif verification_structure == 'behavioral_match':
            theme = 'recognized_behavioral_identity'
            coherence = 0.8
        elif verification_structure == 'anomalous_identity':
            theme = 'anomalous_identity_requires_verification'
            coherence = 0.4
        else:
            theme = 'unverified_identity'
            coherence = 0.5
        
        # Assess completeness
        has_auth = structure.get('authenticated', False)
        has_patterns = structure.get('pattern_count', 0) > 0
        low_drift = structure.get('identity_drift', 1.0) < 0.3
        completeness = sum([has_auth, has_patterns, low_drift]) / 3.0
        
        return {
            'theme': theme,
            'coherence': coherence,
            'completeness': completeness,
            'verification_status': verification_structure,
            'learning_stage': structure.get('learning_structure', 'unknown'),
            'identity_quality': (auth_confidence + coherence + completeness) / 3
        }
    
    def _identify_implications(self, integrated: Dict[str, Any], narrative: Dict[str, Any]) -> List[str]:
        """ID-specific implication identification"""
        implications = []
        
        patterns = integrated.get('patterns', [])
        auth_confidence = integrated.get('authentication_confidence', 0.5)
        structure = integrated.get('structure', {})
        
        # Pattern-specific implications
        for pattern in patterns:
            ptype = pattern['type']
            
            if ptype == 'consistent_behavior':
                implications.append("✓ Behavioral patterns match baseline - identity verified")
            elif ptype == 'identity_evolution':
                implications.append("Identity evolving naturally - update baseline model")
            elif ptype == 'identity_anomaly':
                severity = pattern.get('parameters', {}).get('severity', 'unknown')
                implications.append(f"⚠️ {severity.capitalize()} identity anomaly - requires additional verification")
            elif ptype == 'active_learning':
                implications.append("Learning actively from interactions - model improving")
            elif ptype == 'authenticated_access':
                implications.append("✓ Strong authentication - high confidence in identity")
            elif ptype == 'rich_personality_profile':
                implications.append("Well-defined personality model enables accurate prediction")
        
        # Authentication implications
        if auth_confidence < 0.4:
            implications.append("⚠️ Low authentication confidence - verify identity before proceeding")
        elif auth_confidence > 0.8:
            implications.append("✓ High authentication confidence - identity strongly verified")
        
        # Drift implications
        drift = structure.get('identity_drift', 0)
        if drift > 0.5:
            implications.append("⚠️ Significant identity drift - may indicate impersonation or major life changes")
        
        if not implications:
            implications.append("Standard identity verification applicable")
        
        return implications
    
    def _assess_quality(self, synthesis_output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """ID-specific quality assessment"""
        narrative = synthesis_output.get('narrative', {})
        integrated = synthesis_output.get('integrated', {})
        
        coherence = narrative.get('coherence', 0.5)
        completeness = narrative.get('completeness', 0.5)
        auth_confidence = integrated.get('authentication_confidence', 0.5)
        learning_readiness = integrated.get('learning_readiness', 0.5)
        
        quality = (
            coherence * 0.25 +
            completeness * 0.25 +
            auth_confidence * 0.35 +
            learning_readiness * 0.15
        )
        
        return min(0.95, max(0.1, quality))
    
    def _assess_risks(self, implications: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ID-specific risk assessment"""
        risks = []
        
        if any('identity anomaly' in imp.lower() or 'impersonation' in imp.lower() for imp in implications):
            risks.append({
                'type': 'impersonation_risk',
                'severity': 'high',
                'description': 'Identity anomaly may indicate impersonation attempt'
            })
        
        if any('low authentication confidence' in imp.lower() for imp in implications):
            risks.append({
                'type': 'weak_verification_risk',
                'severity': 'high',
                'description': 'Insufficient authentication for confident verification'
            })
        
        if any('significant identity drift' in imp.lower() for imp in implications):
            risks.append({
                'type': 'identity_drift_risk',
                'severity': 'medium',
                'description': 'Identity changing significantly from baseline'
            })
        
        if any('verify identity before proceeding' in imp.lower() for imp in implications):
            risks.append({
                'type': 'unverified_access_risk',
                'severity': 'medium',
                'description': 'Access without proper verification'
            })
        
        return risks
    
    def _generate_decision_options(self, evaluation_output: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ID-specific decision option generation"""
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        options = []
        
        # Identity verified option
        if quality > 0.7 and len([r for r in risks if r.get('severity') == 'high']) == 0:
            options.append({
                'action': 'identity_verified',
                'confidence': min(0.95, quality),
                'description': 'Identity strongly verified - grant access',
                'access_level': 'full',
                'priority': 1
            })
        
        # Provisional access option
        if quality > 0.5:
            options.append({
                'action': 'provisional_access',
                'confidence': quality * 0.85,
                'description': 'Identity partially verified - grant limited access',
                'access_level': 'limited',
                'priority': 2,
                'monitoring': 'enhanced'
            })
        
        # Additional verification required
        if quality > 0.3:
            options.append({
                'action': 'require_additional_verification',
                'confidence': quality * 0.7,
                'description': 'Insufficient verification - request additional credentials',
                'access_level': 'none',
                'priority': 3,
                'verification_needed': ['credentials', 'behavioral_check']
            })
        
        # Deny access option
        options.append({
            'action': 'deny_access',
            'confidence': 0.0,
            'description': 'Identity cannot be verified - deny access',
            'access_level': 'none',
            'priority': 4,
            'reason': 'verification_failed'
        })
        
        return sorted(options, key=lambda x: x['priority'])
    
    def _select_best_option(self, options: List[Dict[str, Any]], quality: float, risks: List[Dict[str, Any]], confidence: float) -> Dict[str, Any]:
        """ID-specific option selection"""
        if not options:
            return {
                'action': 'deny_access',
                'confidence': 0.0,
                'access_level': 'none'
            }
        
        high_risks = [r for r in risks if r.get('severity') == 'high']
        
        if high_risks and any(r['type'] == 'impersonation_risk' for r in high_risks):
            # Potential impersonation = deny
            return [o for o in options if o['action'] == 'deny_access'][0]
        
        if high_risks:
            # High risks = require additional verification
            verification = [o for o in options if o['action'] == 'require_additional_verification']
            return verification[0] if verification else options[0]
        
        return options[0]
    
    def _calculate_commitment(self, confidence: float, risks: List[Dict[str, Any]]) -> float:
        """ID-specific commitment calculation"""
        commitment = confidence
        
        for risk in risks:
            severity = risk.get('severity', 'low')
            if severity == 'high':
                commitment *= 0.3
            elif severity == 'medium':
                commitment *= 0.6
            else:
                commitment *= 0.85
        
        return max(0.1, min(0.95, commitment))
    
    def _generate_rationale(self, selected_option: Dict[str, Any], evaluation_output: Dict[str, Any], confidence: float) -> str:
        """ID-specific rationale generation"""
        action = selected_option.get('action', 'unknown')
        access_level = selected_option.get('access_level', 'none')
        description = selected_option.get('description', '')
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        rationale = f"ID's Identity Verification: {description}\n"
        rationale += f"Decision: {action.upper()}\n"
        rationale += f"Access Level: {access_level.upper()}\n"
        rationale += f"Confidence: {confidence:.2f}\n"
        rationale += f"Quality Score: {quality:.2f}\n"
        
        if risks:
            rationale += f"\nRisks Identified: {len(risks)}\n"
            for risk in risks:
                rationale += f"  - {risk.get('type', 'unknown')}: {risk.get('description', '')}\n"
        
        if 'monitoring' in selected_option:
            rationale += f"\nMonitoring: {selected_option['monitoring']}\n"
        
        if 'verification_needed' in selected_option:
            rationale += f"\nAdditional Verification Required:\n"
            for item in selected_option['verification_needed']:
                rationale += f"  • {item}\n"
        
        if 'reason' in selected_option:
            rationale += f"\nReason: {selected_option['reason']}\n"
        
        return rationale
