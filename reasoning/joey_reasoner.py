#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Joey-Specific Hierarchical Reasoning

Extends IntraAgentReasoner with domain-specific logic for pattern analysis,
anomaly detection, and statistical reasoning.

Joey's cognitive process:
- L1 Perception: Extract statistical features and data properties
- L2 Analysis: Detect patterns, correlations, anomalies
- L3 Synthesis: Integrate patterns into coherent narrative
- L4 Evaluation: Assess pattern quality, statistical significance
- L5 Decision: Generate analytical insights and recommendations
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional
from reasoning.intra_agent_reasoner import IntraAgentReasoner, CognitiveLevel, ReasoningDepth
import time

logger = logging.getLogger(__name__)


class JoeyReasoner(IntraAgentReasoner):
    """Joey-specific hierarchical reasoner for pattern analysis and statistics"""
    
    def __init__(
        self,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP,
        enable_tree_of_selfs: bool = True,
        max_branches_per_level: int = 5
    ):
        super().__init__(
            agent_name="Joey",
            default_depth=default_depth,
            enable_tree_of_selfs=enable_tree_of_selfs,
            max_branches_per_level=max_branches_per_level
        )
    
    def _extract_features(self, input_data: Any) -> Dict[str, Any]:
        """Joey-specific feature extraction for data analysis"""
        if not isinstance(input_data, dict):
            return super()._extract_features(input_data)
        
        # Extract data analysis features
        features = {
            'type': 'analytical_data',
            'data_type': input_data.get('data_type', 'unknown'),
            'timestamp': input_data.get('timestamp')
        }
        
        # Handle array/list data
        if 'data' in input_data:
            data = input_data['data']
            if isinstance(data, (list, np.ndarray)):
                data_array = np.array(data) if isinstance(data, list) else data
                features.update({
                    'sample_size': len(data_array),
                    'mean': float(np.mean(data_array)),
                    'std_dev': float(np.std(data_array)),
                    'min': float(np.min(data_array)),
                    'max': float(np.max(data_array)),
                    'range': float(np.max(data_array) - np.min(data_array)),
                    'skewness': self._calculate_skewness(data_array),
                    'kurtosis': self._calculate_kurtosis(data_array),
                    'has_outliers': self._has_outliers(data_array)
                })
        
        # Handle correlation data
        if 'variables' in input_data:
            features['num_variables'] = len(input_data['variables'])
            features['analysis_type'] = 'correlation'
        
        # Handle pattern data
        if 'patterns' in input_data:
            features['num_patterns'] = len(input_data['patterns'])
            features['analysis_type'] = 'pattern_detection'
        
        features['complexity'] = self._calculate_analytical_complexity(features)
        
        return features
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            n = len(data)
            if std == 0 or n < 3:
                return 0.0
            skewness = (n / ((n-1) * (n-2))) * np.sum(((data - mean) / std) ** 3)
            return float(skewness)
        except:
            return 0.0
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            n = len(data)
            if std == 0 or n < 4:
                return 3.0
            kurtosis = (n * (n+1) / ((n-1) * (n-2) * (n-3))) * np.sum(((data - mean) / std) ** 4)
            kurtosis -= 3 * (n-1)**2 / ((n-2) * (n-3))
            return float(kurtosis + 3)
        except:
            return 3.0
    
    def _has_outliers(self, data: np.ndarray) -> bool:
        """Check for outliers using IQR method"""
        try:
            q25 = np.percentile(data, 25)
            q75 = np.percentile(data, 75)
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            outliers = np.sum((data < lower_bound) | (data > upper_bound))
            return outliers > 0
        except:
            return False
    
    def _calculate_analytical_complexity(self, features: Dict[str, Any]) -> int:
        """Calculate complexity score for analytical data"""
        complexity = 3  # Base complexity
        
        if features.get('num_variables', 0) > 5:
            complexity += 2
        if features.get('num_patterns', 0) > 3:
            complexity += 2
        if features.get('sample_size', 0) > 1000:
            complexity += 1
        if features.get('has_outliers', False):
            complexity += 1
        
        return complexity
    
    def _detect_patterns(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Joey-specific pattern detection"""
        patterns = []
        
        # Statistical distribution patterns
        if 'mean' in features and 'std_dev' in features:
            skewness = features.get('skewness', 0)
            kurtosis = features.get('kurtosis', 3)
            
            # Normality pattern
            if abs(skewness) < 0.5 and abs(kurtosis - 3) < 0.5:
                patterns.append({
                    'type': 'normal_distribution',
                    'confidence': 0.9,
                    'description': 'Data follows normal distribution',
                    'parameters': {
                        'mean': features['mean'],
                        'std_dev': features['std_dev']
                    }
                })
            
            # Skewness pattern
            if abs(skewness) > 1.0:
                direction = 'right' if skewness > 0 else 'left'
                patterns.append({
                    'type': 'skewed_distribution',
                    'confidence': min(0.95, abs(skewness) / 2),
                    'description': f'Strong {direction}-skewed distribution',
                    'parameters': {
                        'skewness': skewness,
                        'direction': direction
                    }
                })
            
            # Heavy tails pattern
            if kurtosis > 4:
                patterns.append({
                    'type': 'heavy_tails',
                    'confidence': 0.85,
                    'description': 'Distribution has heavy tails (leptokurtic)',
                    'parameters': {
                        'kurtosis': kurtosis
                    }
                })
            
            # Outlier pattern
            if features.get('has_outliers', False):
                patterns.append({
                    'type': 'outlier_presence',
                    'confidence': 0.8,
                    'description': 'Significant outliers detected',
                    'parameters': {
                        'outlier_method': 'IQR'
                    }
                })
        
        # Correlation patterns
        if features.get('analysis_type') == 'correlation':
            patterns.append({
                'type': 'multivariate_relationship',
                'confidence': 0.75,
                'description': f'Analyzing {features.get("num_variables", 0)} variables',
                'parameters': {
                    'variables': features.get('num_variables', 0)
                }
            })
        
        # Temporal patterns
        if 'timestamp' in features:
            patterns.append({
                'type': 'temporal_data',
                'confidence': 0.7,
                'description': 'Time-series data detected',
                'parameters': {
                    'temporal': True
                }
            })
        
        return patterns
    
    def _analyze_structure(self, features: Dict[str, Any], patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Joey-specific structural analysis"""
        # Determine dominant analytical framework
        dominant_pattern = None
        max_confidence = 0.0
        for pattern in patterns:
            if pattern['confidence'] > max_confidence:
                max_confidence = pattern['confidence']
                dominant_pattern = pattern['type']
        
        # Data quality assessment
        sample_size = features.get('sample_size', 0)
        if sample_size > 1000:
            data_quality = 'high'
        elif sample_size > 100:
            data_quality = 'medium'
        else:
            data_quality = 'low'
        
        # Statistical robustness
        has_outliers = features.get('has_outliers', False)
        robustness = 'robust' if not has_outliers and sample_size > 100 else 'moderate'
        
        return {
            'type': 'statistical_structure',
            'dominant_pattern': dominant_pattern,
            'pattern_count': len(patterns),
            'pattern_diversity': len(set(p['type'] for p in patterns)),
            'data_quality': data_quality,
            'sample_size': sample_size,
            'statistical_robustness': robustness,
            'complexity_level': 'high' if features.get('complexity', 0) > 5 else 'moderate'
        }
    
    def _detect_anomalies(self, features: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Joey-specific anomaly detection"""
        anomalies = []
        
        # Sample size anomaly
        sample_size = features.get('sample_size', 0)
        if sample_size < 30:
            anomalies.append({
                'type': 'insufficient_sample_size',
                'severity': 'high',
                'description': f'Sample size ({sample_size}) below statistical threshold',
                'recommendation': 'Collect more data for reliable analysis'
            })
        
        # Extreme skewness
        skewness = features.get('skewness', 0)
        if abs(skewness) > 2:
            anomalies.append({
                'type': 'extreme_skewness',
                'severity': 'medium',
                'value': skewness,
                'description': 'Data highly skewed, may require transformation'
            })
        
        # Extreme kurtosis
        kurtosis = features.get('kurtosis', 3)
        if kurtosis > 7:
            anomalies.append({
                'type': 'extreme_kurtosis',
                'severity': 'medium',
                'value': kurtosis,
                'description': 'Heavy tails detected, extreme values present'
            })
        
        # Range anomaly
        if 'range' in features and 'std_dev' in features:
            range_ratio = features['range'] / (features['std_dev'] * 6)
            if range_ratio > 2:
                anomalies.append({
                    'type': 'excessive_range',
                    'severity': 'low',
                    'description': 'Data range exceeds expected bounds'
                })
        
        # Consistency check with historical patterns
        expected_pattern = context.get('expected_pattern')
        if expected_pattern:
            current_patterns = [p['type'] for p in context.get('current_patterns', [])]
            if expected_pattern not in current_patterns:
                anomalies.append({
                    'type': 'pattern_mismatch',
                    'severity': 'medium',
                    'description': f'Expected pattern "{expected_pattern}" not found'
                })
        
        return anomalies
    
    def _integrate_with_context(self, patterns: List[Dict[str, Any]], structure: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Joey-specific context integration"""
        # Get analytical context
        analysis_history = context.get('analysis_history', [])
        accuracy_threshold = context.get('accuracy_threshold', 0.75)
        
        # Calculate pattern consistency with history
        consistency_score = 0.0
        if analysis_history:
            historical_pattern_types = [h.get('pattern_type') for h in analysis_history if 'pattern_type' in h]
            current_pattern_types = [p['type'] for p in patterns]
            
            if historical_pattern_types and current_pattern_types:
                overlap = len(set(current_pattern_types) & set(historical_pattern_types))
                consistency_score = overlap / max(len(set(current_pattern_types)), 1)
        
        # Statistical significance assessment
        statistical_power = 0.8 if structure.get('sample_size', 0) > 100 else 0.5
        
        return {
            'patterns': patterns,
            'structure': structure,
            'historical_consistency': consistency_score,
            'statistical_power': statistical_power,
            'accuracy_threshold': accuracy_threshold,
            'context_applied': True,
            'integration_quality': 0.75 + consistency_score * 0.25
        }
    
    def _build_narrative(self, integrated: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Joey-specific narrative construction"""
        patterns = integrated.get('patterns', [])
        structure = integrated.get('structure', {})
        consistency = integrated.get('historical_consistency', 0)
        
        # Build analytical narrative
        if not patterns:
            theme = 'random_noise'
            coherence = 0.3
        elif len(patterns) == 1:
            theme = f"clear_{patterns[0]['type']}"
            coherence = 0.9
        elif structure.get('dominant_pattern'):
            theme = f"dominant_{structure['dominant_pattern']}"
            coherence = 0.7
        else:
            theme = 'complex_multivariate'
            coherence = 0.5
        
        # Assess completeness
        has_distribution_info = any('distribution' in p['type'] for p in patterns)
        has_structure_info = structure.get('dominant_pattern') is not None
        has_context = consistency > 0
        completeness = sum([has_distribution_info, has_structure_info, has_context]) / 3.0
        
        return {
            'theme': theme,
            'coherence': coherence,
            'completeness': completeness,
            'primary_finding': structure.get('dominant_pattern', 'unclear'),
            'analytical_context': 'consistent' if consistency > 0.5 else 'novel'
        }
    
    def _identify_implications(self, integrated: Dict[str, Any], narrative: Dict[str, Any]) -> List[str]:
        """Joey-specific implication identification"""
        implications = []
        
        patterns = integrated.get('patterns', [])
        structure = integrated.get('structure', {})
        statistical_power = integrated.get('statistical_power', 0.5)
        
        # Pattern-specific implications
        for pattern in patterns:
            ptype = pattern['type']
            confidence = pattern['confidence']
            
            if ptype == 'normal_distribution' and confidence > 0.8:
                implications.append("Data suitable for parametric statistical tests")
            
            elif ptype == 'skewed_distribution':
                direction = pattern.get('parameters', {}).get('direction', 'unknown')
                implications.append(f"{direction.capitalize()}-skewed data may require transformation or non-parametric methods")
            
            elif ptype == 'heavy_tails' and confidence > 0.7:
                implications.append("⚠️ Heavy tails indicate higher risk of extreme events")
            
            elif ptype == 'outlier_presence':
                implications.append("Outliers detected - investigate for data quality issues or genuine extremes")
            
            elif ptype == 'multivariate_relationship':
                implications.append("Complex variable interactions present - consider multivariate analysis")
        
        # Statistical power implications
        if statistical_power < 0.6:
            implications.append("⚠️ Low statistical power - results may not be reliable")
        
        # Data quality implications
        data_quality = structure.get('data_quality', 'unknown')
        if data_quality == 'low':
            implications.append("⚠️ Limited sample size - collect more data for robust conclusions")
        elif data_quality == 'high':
            implications.append("High-quality dataset enables confident statistical inference")
        
        if not implications:
            implications.append("Standard statistical analysis applicable")
        
        return implications
    
    def _assess_quality(self, synthesis_output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Joey-specific quality assessment"""
        narrative = synthesis_output.get('narrative', {})
        integrated = synthesis_output.get('integrated', {})
        
        coherence = narrative.get('coherence', 0.5)
        completeness = narrative.get('completeness', 0.5)
        integration_quality = integrated.get('integration_quality', 0.5)
        statistical_power = integrated.get('statistical_power', 0.5)
        
        # Weight factors for analytical quality
        quality = (
            coherence * 0.3 +
            completeness * 0.2 +
            integration_quality * 0.2 +
            statistical_power * 0.3
        )
        
        return min(0.95, max(0.1, quality))
    
    def _assess_risks(self, implications: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Joey-specific risk assessment"""
        risks = []
        
        # Check for statistical validity warnings
        if any('low statistical power' in imp.lower() for imp in implications):
            risks.append({
                'type': 'statistical_power_risk',
                'severity': 'high',
                'description': 'Insufficient statistical power for reliable inference'
            })
        
        # Check for data quality warnings
        if any('limited sample' in imp.lower() or 'collect more data' in imp.lower() for imp in implications):
            risks.append({
                'type': 'data_quality_risk',
                'severity': 'medium',
                'description': 'Sample size may be insufficient for robust analysis'
            })
        
        # Check for extreme value warnings
        if any('heavy tails' in imp.lower() or 'extreme' in imp.lower() for imp in implications):
            risks.append({
                'type': 'extreme_value_risk',
                'severity': 'medium',
                'description': 'Presence of extreme values may affect analysis'
            })
        
        # Check for transformation needs
        if any('transformation' in imp.lower() or 'non-parametric' in imp.lower() for imp in implications):
            risks.append({
                'type': 'method_appropriateness_risk',
                'severity': 'low',
                'description': 'Standard methods may not be optimal for this data'
            })
        
        # Historical consistency risk
        consistency = context.get('historical_consistency', 0)
        if consistency < 0.3:
            risks.append({
                'type': 'pattern_novelty_risk',
                'severity': 'low',
                'description': 'Pattern differs significantly from historical observations'
            })
        
        return risks
    
    def _generate_decision_options(self, evaluation_output: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Joey-specific decision option generation"""
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        accuracy_threshold = context.get('accuracy_threshold', 0.75)
        
        options = []
        
        # High confidence analysis option
        if quality > accuracy_threshold and len(risks) <= 1:
            options.append({
                'action': 'confident_analysis',
                'confidence': min(0.95, quality),
                'description': 'High-confidence analytical findings',
                'priority': 1,
                'recommendations': []
            })
        
        # Moderate confidence option
        if quality > accuracy_threshold * 0.7:
            options.append({
                'action': 'moderate_confidence_analysis',
                'confidence': quality * 0.85,
                'description': 'Moderate confidence - additional validation recommended',
                'priority': 2,
                'recommendations': ['Validate with additional data', 'Cross-check with alternative methods']
            })
        
        # Low confidence option
        if quality > accuracy_threshold * 0.5:
            options.append({
                'action': 'low_confidence_analysis',
                'confidence': quality * 0.7,
                'description': 'Preliminary findings - significant limitations present',
                'priority': 3,
                'recommendations': ['Collect more data', 'Apply robust methods', 'Interpret cautiously']
            })
        
        # Inconclusive option
        options.append({
            'action': 'inconclusive',
            'confidence': 0.0,
            'description': 'Insufficient evidence for reliable conclusions',
            'priority': 4,
            'recommendations': ['Gather more data', 'Refine analysis approach', 'Consider alternative methods']
        })
        
        return sorted(options, key=lambda x: x['priority'])
    
    def _select_best_option(self, options: List[Dict[str, Any]], quality: float, risks: List[Dict[str, Any]], confidence: float) -> Dict[str, Any]:
        """Joey-specific option selection"""
        if not options:
            return {
                'action': 'inconclusive',
                'confidence': 0.0,
                'description': 'No viable analytical options',
                'recommendations': []
            }
        
        # Check for high-severity risks
        high_severity_risks = [r for r in risks if r.get('severity') == 'high']
        
        if high_severity_risks:
            # Downgrade to more conservative option
            conservative_options = [o for o in options if o['priority'] >= 2]
            return conservative_options[0] if conservative_options else options[0]
        
        # Select highest priority (best) option
        return options[0]
    
    def _calculate_commitment(self, confidence: float, risks: List[Dict[str, Any]]) -> float:
        """Joey-specific commitment calculation"""
        commitment = confidence
        
        # Reduce commitment based on risk severity
        for risk in risks:
            severity = risk.get('severity', 'low')
            if severity == 'high':
                commitment *= 0.6
            elif severity == 'medium':
                commitment *= 0.8
            else:
                commitment *= 0.95
        
        return max(0.1, min(0.95, commitment))
    
    def _generate_rationale(self, selected_option: Dict[str, Any], evaluation_output: Dict[str, Any], confidence: float) -> str:
        """Joey-specific rationale generation"""
        action = selected_option.get('action', 'unknown')
        option_confidence = selected_option.get('confidence', 0.0)
        description = selected_option.get('description', '')
        recommendations = selected_option.get('recommendations', [])
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        rationale = f"Joey's Statistical Analysis: {description}\n"
        rationale += f"Analytical Confidence: {option_confidence:.2f}\n"
        rationale += f"Quality Score: {quality:.2f}\n"
        rationale += f"Overall Confidence: {confidence:.2f}\n"
        
        if risks:
            rationale += f"\nRisks Identified: {len(risks)}\n"
            for risk in risks:
                rationale += f"  - {risk.get('type', 'unknown')}: {risk.get('description', '')}\n"
        
        if recommendations:
            rationale += f"\nRecommendations:\n"
            for rec in recommendations:
                rationale += f"  • {rec}\n"
        
        return rationale
