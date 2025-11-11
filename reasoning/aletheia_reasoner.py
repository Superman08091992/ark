#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aletheia-Specific Hierarchical Reasoning

Extends IntraAgentReasoner with domain-specific logic for truth verification,
ethical analysis, and philosophical reasoning.

Aletheia's cognitive process:
- L1 Perception: Extract claims, values, and ethical dimensions
- L2 Analysis: Verify facts, detect contradictions, assess consistency
- L3 Synthesis: Integrate with ethical framework and philosophical principles
- L4 Evaluation: Assess truth value, ethical alignment, wisdom quality
- L5 Decision: Generate truth verdict and ethical guidance
"""

import logging
from typing import Any, Dict, List, Optional
from reasoning.intra_agent_reasoner import IntraAgentReasoner, ReasoningDepth
import time

logger = logging.getLogger(__name__)


class AletheiaReasoner(IntraAgentReasoner):
    """Aletheia-specific hierarchical reasoner for truth and ethics"""
    
    def __init__(
        self,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP,
        enable_tree_of_selfs: bool = True,
        max_branches_per_level: int = 5
    ):
        super().__init__(
            agent_name="Aletheia",
            default_depth=default_depth,
            enable_tree_of_selfs=enable_tree_of_selfs,
            max_branches_per_level=max_branches_per_level
        )
    
    def _extract_features(self, input_data: Any) -> Dict[str, Any]:
        """Aletheia-specific feature extraction for truth and ethics"""
        if not isinstance(input_data, dict):
            return super()._extract_features(input_data)
        
        features = {
            'type': 'truth_claim',
            'claim_type': input_data.get('claim_type', 'unknown'),
            'timestamp': input_data.get('timestamp')
        }
        
        # Extract claims
        if 'claims' in input_data:
            claims = input_data['claims']
            features['num_claims'] = len(claims) if isinstance(claims, list) else 1
            features['has_claims'] = True
        
        # Extract evidence
        if 'evidence' in input_data:
            evidence = input_data['evidence']
            features['num_evidence'] = len(evidence) if isinstance(evidence, list) else 0
            features['has_evidence'] = features['num_evidence'] > 0
            features['evidence_strength'] = self._assess_evidence_strength(evidence)
        
        # Ethical dimensions
        if 'ethical_dimensions' in input_data:
            features['ethical_dimensions'] = input_data['ethical_dimensions']
            features['num_ethical_aspects'] = len(input_data['ethical_dimensions']) if isinstance(input_data['ethical_dimensions'], list) else 0
        
        # Contradictions
        if 'contradictions' in input_data:
            features['has_contradictions'] = True
            features['num_contradictions'] = len(input_data['contradictions']) if isinstance(input_data['contradictions'], list) else 0
        
        # Values alignment
        if 'values' in input_data:
            features['values'] = input_data['values']
            features['num_values'] = len(input_data['values']) if isinstance(input_data['values'], list) else 0
        
        features['complexity'] = self._calculate_truth_complexity(features)
        
        return features
    
    def _assess_evidence_strength(self, evidence: Any) -> float:
        """Assess strength of evidence"""
        if isinstance(evidence, list):
            return min(1.0, len(evidence) * 0.2)
        return 0.5
    
    def _calculate_truth_complexity(self, features: Dict[str, Any]) -> int:
        """Calculate complexity of truth verification"""
        complexity = 2
        complexity += features.get('num_claims', 0)
        complexity += features.get('num_ethical_aspects', 0)
        if features.get('has_contradictions', False):
            complexity += 3
        if not features.get('has_evidence', False):
            complexity += 2
        return min(complexity, 10)
    
    def _detect_patterns(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aletheia-specific pattern detection"""
        patterns = []
        
        # Well-supported claim pattern
        if features.get('has_evidence', False) and features.get('evidence_strength', 0) > 0.6:
            patterns.append({
                'type': 'well_supported_claim',
                'confidence': features['evidence_strength'],
                'description': 'Claim has strong evidentiary support',
                'parameters': {'evidence_count': features.get('num_evidence', 0)}
            })
        
        # Unsupported assertion pattern
        if features.get('has_claims', False) and not features.get('has_evidence', False):
            patterns.append({
                'type': 'unsupported_assertion',
                'confidence': 0.9,
                'description': 'Claims made without evidence',
                'parameters': {'verification_needed': True}
            })
        
        # Contradiction pattern
        if features.get('has_contradictions', False):
            patterns.append({
                'type': 'logical_contradiction',
                'confidence': 0.95,
                'description': 'Internal contradictions detected',
                'parameters': {'contradiction_count': features.get('num_contradictions', 0)}
            })
        
        # Ethical complexity pattern
        if features.get('num_ethical_aspects', 0) > 3:
            patterns.append({
                'type': 'ethical_complexity',
                'confidence': 0.8,
                'description': 'Multiple ethical dimensions require consideration',
                'parameters': {'dimensions': features.get('num_ethical_aspects', 0)}
            })
        
        # Value alignment pattern
        if features.get('num_values', 0) > 0:
            patterns.append({
                'type': 'value_based_reasoning',
                'confidence': 0.85,
                'description': 'Reasoning grounded in explicit values',
                'parameters': {'values': features.get('values', [])}
            })
        
        return patterns
    
    def _analyze_structure(self, features: Dict[str, Any], patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aletheia-specific structural analysis"""
        # Truth assessment structure
        has_evidence = features.get('has_evidence', False)
        has_contradictions = features.get('has_contradictions', False)
        
        if has_contradictions:
            truth_structure = 'contradictory'
        elif has_evidence:
            truth_structure = 'evidential'
        else:
            truth_structure = 'speculative'
        
        # Ethical framework
        num_ethical = features.get('num_ethical_aspects', 0)
        if num_ethical > 3:
            ethical_framework = 'complex_multi_value'
        elif num_ethical > 0:
            ethical_framework = 'simple_value_based'
        else:
            ethical_framework = 'value_neutral'
        
        # Dominant pattern
        dominant_pattern = None
        max_confidence = 0.0
        for pattern in patterns:
            if pattern['confidence'] > max_confidence:
                max_confidence = pattern['confidence']
                dominant_pattern = pattern['type']
        
        return {
            'type': 'truth_and_ethics_structure',
            'truth_structure': truth_structure,
            'ethical_framework': ethical_framework,
            'dominant_pattern': dominant_pattern,
            'pattern_count': len(patterns),
            'complexity_level': 'high' if features.get('complexity', 0) > 6 else 'moderate',
            'has_contradictions': has_contradictions,
            'evidence_based': has_evidence
        }
    
    def _detect_anomalies(self, features: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aletheia-specific anomaly detection"""
        anomalies = []
        
        # Claims without evidence
        if features.get('has_claims', False) and not features.get('has_evidence', False):
            anomalies.append({
                'type': 'missing_evidence',
                'severity': 'high',
                'description': 'Claims require evidential support for verification'
            })
        
        # Contradictions
        if features.get('has_contradictions', False):
            anomalies.append({
                'type': 'logical_inconsistency',
                'severity': 'high',
                'description': f'{features["num_contradictions"]} contradictions undermine truth claims'
            })
        
        # Value conflict
        core_values = context.get('core_values', [])
        claim_values = features.get('values', [])
        if core_values and claim_values:
            conflicts = [v for v in claim_values if v not in core_values]
            if conflicts:
                anomalies.append({
                    'type': 'value_conflict',
                    'severity': 'medium',
                    'description': f'Values {conflicts} conflict with core principles'
                })
        
        # Weak evidence
        if features.get('has_evidence', False) and features.get('evidence_strength', 0) < 0.3:
            anomalies.append({
                'type': 'weak_evidence',
                'severity': 'medium',
                'description': 'Evidence insufficient for strong truth claims'
            })
        
        return anomalies
    
    def _integrate_with_context(self, patterns: List[Dict[str, Any]], structure: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Aletheia-specific context integration"""
        # Get philosophical context
        philosophical_framework = context.get('philosophical_framework', 'rational_empiricism')
        core_values = context.get('core_values', [])
        truth_revelations = context.get('truth_revelations', [])
        
        # Truth verification score
        truth_score = 0.5
        if structure.get('evidence_based', False):
            truth_score += 0.3
        if not structure.get('has_contradictions', False):
            truth_score += 0.2
        truth_score = min(1.0, truth_score)
        
        # Ethical alignment score
        ethical_score = 0.5
        if structure.get('ethical_framework') != 'value_neutral':
            ethical_score += 0.2
        if core_values:
            ethical_score += 0.3
        ethical_score = min(1.0, ethical_score)
        
        return {
            'patterns': patterns,
            'structure': structure,
            'truth_score': truth_score,
            'ethical_alignment': ethical_score,
            'philosophical_framework': philosophical_framework,
            'core_values': core_values,
            'context_applied': True,
            'integration_quality': (truth_score + ethical_score) / 2
        }
    
    def _build_narrative(self, integrated: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Aletheia-specific narrative construction"""
        structure = integrated.get('structure', {})
        truth_score = integrated.get('truth_score', 0.5)
        ethical_score = integrated.get('ethical_alignment', 0.5)
        
        # Build truth narrative
        truth_structure = structure.get('truth_structure', 'unknown')
        if truth_structure == 'contradictory':
            theme = 'contradictory_claims_require_resolution'
            coherence = 0.3
        elif truth_structure == 'evidential':
            theme = 'evidence_based_truth_verification'
            coherence = 0.9
        elif truth_structure == 'speculative':
            theme = 'speculative_claims_need_evidence'
            coherence = 0.5
        else:
            theme = 'unclear_truth_status'
            coherence = 0.4
        
        # Assess completeness
        has_evidence = structure.get('evidence_based', False)
        no_contradictions = not structure.get('has_contradictions', False)
        has_ethics = structure.get('ethical_framework') != 'value_neutral'
        completeness = sum([has_evidence, no_contradictions, has_ethics]) / 3.0
        
        return {
            'theme': theme,
            'coherence': coherence,
            'completeness': completeness,
            'truth_status': truth_structure,
            'ethical_framework': structure.get('ethical_framework', 'unknown'),
            'wisdom_quality': (truth_score + ethical_score + coherence) / 3
        }
    
    def _identify_implications(self, integrated: Dict[str, Any], narrative: Dict[str, Any]) -> List[str]:
        """Aletheia-specific implication identification"""
        implications = []
        
        patterns = integrated.get('patterns', [])
        truth_score = integrated.get('truth_score', 0.5)
        ethical_score = integrated.get('ethical_alignment', 0.5)
        
        # Pattern-specific implications
        for pattern in patterns:
            ptype = pattern['type']
            
            if ptype == 'well_supported_claim':
                implications.append("✓ Claims well-supported by evidence - truth verification strong")
            elif ptype == 'unsupported_assertion':
                implications.append("⚠️ Assertions lack evidence - verification impossible without proof")
            elif ptype == 'logical_contradiction':
                implications.append("⚠️ Contradictions detected - claims cannot all be true simultaneously")
            elif ptype == 'ethical_complexity':
                implications.append("Multiple ethical dimensions require careful value-based reasoning")
            elif ptype == 'value_based_reasoning':
                implications.append("Reasoning grounded in explicit values enables ethical evaluation")
        
        # Truth implications
        if truth_score < 0.4:
            implications.append("⚠️ Low truth confidence - claims require substantial verification")
        elif truth_score > 0.8:
            implications.append("✓ High truth confidence - claims well-verified")
        
        # Ethical implications
        if ethical_score < 0.4:
            implications.append("⚠️ Weak ethical alignment - may conflict with core values")
        elif ethical_score > 0.8:
            implications.append("✓ Strong ethical alignment - consistent with core principles")
        
        if not implications:
            implications.append("Standard truth verification applicable")
        
        return implications
    
    def _assess_quality(self, synthesis_output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Aletheia-specific quality assessment"""
        narrative = synthesis_output.get('narrative', {})
        integrated = synthesis_output.get('integrated', {})
        
        coherence = narrative.get('coherence', 0.5)
        completeness = narrative.get('completeness', 0.5)
        truth_score = integrated.get('truth_score', 0.5)
        ethical_alignment = integrated.get('ethical_alignment', 0.5)
        
        quality = (
            coherence * 0.2 +
            completeness * 0.2 +
            truth_score * 0.3 +
            ethical_alignment * 0.3
        )
        
        return min(0.95, max(0.1, quality))
    
    def _assess_risks(self, implications: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aletheia-specific risk assessment"""
        risks = []
        
        if any('contradictions' in imp.lower() for imp in implications):
            risks.append({
                'type': 'logical_inconsistency_risk',
                'severity': 'high',
                'description': 'Contradictions undermine truth claims'
            })
        
        if any('lack evidence' in imp.lower() or 'verification impossible' in imp.lower() for imp in implications):
            risks.append({
                'type': 'unverifiable_claims_risk',
                'severity': 'high',
                'description': 'Claims cannot be verified without evidence'
            })
        
        if any('weak ethical alignment' in imp.lower() or 'conflict with core values' in imp.lower() for imp in implications):
            risks.append({
                'type': 'ethical_misalignment_risk',
                'severity': 'medium',
                'description': 'Ethical conflicts with core principles'
            })
        
        if any('low truth confidence' in imp.lower() for imp in implications):
            risks.append({
                'type': 'truth_uncertainty_risk',
                'severity': 'medium',
                'description': 'Truth status uncertain or weak'
            })
        
        return risks
    
    def _generate_decision_options(self, evaluation_output: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aletheia-specific decision option generation"""
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        options = []
        
        # Truth verified option
        if quality > 0.7 and len([r for r in risks if r.get('severity') == 'high']) == 0:
            options.append({
                'action': 'truth_verified',
                'confidence': min(0.95, quality),
                'description': 'Claims verified and ethically aligned',
                'verdict': 'TRUE',
                'priority': 1
            })
        
        # Partially verified option
        if quality > 0.5:
            options.append({
                'action': 'partially_verified',
                'confidence': quality * 0.85,
                'description': 'Some verification possible, caveats apply',
                'verdict': 'CONDITIONAL',
                'priority': 2,
                'caveats': ['Limited evidence', 'Requires additional verification']
            })
        
        # Unverified option
        if quality > 0.3:
            options.append({
                'action': 'unverified',
                'confidence': quality * 0.7,
                'description': 'Insufficient evidence for verification',
                'verdict': 'UNVERIFIED',
                'priority': 3,
                'recommendations': ['Gather evidence', 'Resolve contradictions']
            })
        
        # False/contradictory option
        options.append({
            'action': 'contradictory_or_false',
            'confidence': 0.0,
            'description': 'Claims contradictory or demonstrably false',
            'verdict': 'FALSE',
            'priority': 4
        })
        
        return sorted(options, key=lambda x: x['priority'])
    
    def _select_best_option(self, options: List[Dict[str, Any]], quality: float, risks: List[Dict[str, Any]], confidence: float) -> Dict[str, Any]:
        """Aletheia-specific option selection"""
        if not options:
            return {
                'action': 'unverified',
                'confidence': 0.0,
                'verdict': 'UNVERIFIED'
            }
        
        high_risks = [r for r in risks if r.get('severity') == 'high']
        
        if high_risks and any(r['type'] == 'logical_inconsistency_risk' for r in high_risks):
            # Contradictions = false
            return [o for o in options if o['action'] == 'contradictory_or_false'][0]
        
        if high_risks:
            # High risks = conservative verdict
            conservative = [o for o in options if o['priority'] >= 3]
            return conservative[0] if conservative else options[0]
        
        return options[0]
    
    def _calculate_commitment(self, confidence: float, risks: List[Dict[str, Any]]) -> float:
        """Aletheia-specific commitment calculation"""
        commitment = confidence
        
        for risk in risks:
            severity = risk.get('severity', 'low')
            if severity == 'high':
                commitment *= 0.4
            elif severity == 'medium':
                commitment *= 0.7
            else:
                commitment *= 0.9
        
        return max(0.1, min(0.95, commitment))
    
    def _generate_rationale(self, selected_option: Dict[str, Any], evaluation_output: Dict[str, Any], confidence: float) -> str:
        """Aletheia-specific rationale generation"""
        action = selected_option.get('action', 'unknown')
        verdict = selected_option.get('verdict', 'UNKNOWN')
        description = selected_option.get('description', '')
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        rationale = f"Aletheia's Truth Verification: {description}\n"
        rationale += f"Verdict: {verdict}\n"
        rationale += f"Confidence: {confidence:.2f}\n"
        rationale += f"Quality Score: {quality:.2f}\n"
        
        if risks:
            rationale += f"\nRisks Identified: {len(risks)}\n"
            for risk in risks:
                rationale += f"  - {risk.get('type', 'unknown')}: {risk.get('description', '')}\n"
        
        if 'caveats' in selected_option:
            rationale += f"\nCaveats:\n"
            for caveat in selected_option['caveats']:
                rationale += f"  • {caveat}\n"
        
        if 'recommendations' in selected_option:
            rationale += f"\nRecommendations:\n"
            for rec in selected_option['recommendations']:
                rationale += f"  • {rec}\n"
        
        return rationale
