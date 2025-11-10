#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kenny-Specific Hierarchical Reasoning

Extends IntraAgentReasoner with domain-specific logic for execution planning,
risk management, and resource optimization.

Kenny's cognitive process:
- L1 Perception: Extract execution requirements and constraints
- L2 Analysis: Assess feasibility, identify dependencies, detect conflicts
- L3 Synthesis: Build execution plan with resource allocation
- L4 Evaluation: Evaluate risks, assess success probability
- L5 Decision: Select optimal execution strategy
"""

import logging
import os
from typing import Any, Dict, List, Optional
from reasoning.intra_agent_reasoner import IntraAgentReasoner, CognitiveLevel, ReasoningDepth
import time

logger = logging.getLogger(__name__)


class KennyReasoner(IntraAgentReasoner):
    """Kenny-specific hierarchical reasoner for execution planning"""
    
    def __init__(
        self,
        default_depth: ReasoningDepth = ReasoningDepth.DEEP,
        enable_tree_of_selfs: bool = True,
        max_branches_per_level: int = 5
    ):
        super().__init__(
            agent_name="Kenny",
            default_depth=default_depth,
            enable_tree_of_selfs=enable_tree_of_selfs,
            max_branches_per_level=max_branches_per_level
        )
    
    def _extract_features(self, input_data: Any) -> Dict[str, Any]:
        """Kenny-specific feature extraction for execution tasks"""
        if not isinstance(input_data, dict):
            return super()._extract_features(input_data)
        
        # Extract execution-specific features
        features = {
            'type': 'execution_task',
            'task_type': input_data.get('task_type', 'unknown'),
            'timestamp': input_data.get('timestamp')
        }
        
        # Resource requirements
        if 'resources' in input_data:
            resources = input_data['resources']
            features['resources_required'] = resources
            features['resource_complexity'] = len(resources) if isinstance(resources, (list, dict)) else 1
        
        # Dependencies
        if 'dependencies' in input_data:
            deps = input_data['dependencies']
            features['num_dependencies'] = len(deps) if isinstance(deps, list) else 0
            features['has_dependencies'] = features['num_dependencies'] > 0
        
        # Risk factors
        if 'risk_factors' in input_data:
            features['risk_factors'] = input_data['risk_factors']
            features['num_risks'] = len(input_data['risk_factors']) if isinstance(input_data['risk_factors'], list) else 0
        
        # Execution constraints
        if 'constraints' in input_data:
            constraints = input_data['constraints']
            features['constraints'] = constraints
            features['time_constrained'] = 'deadline' in constraints or 'timeout' in constraints
            features['resource_constrained'] = 'memory_limit' in constraints or 'cpu_limit' in constraints
        
        # File operations
        if 'files' in input_data:
            files = input_data['files']
            features['num_files'] = len(files) if isinstance(files, list) else 1
            features['file_operations'] = True
        
        # Build/creation tasks
        if 'build_target' in input_data:
            features['build_target'] = input_data['build_target']
            features['is_build_task'] = True
        
        features['complexity'] = self._calculate_execution_complexity(features)
        
        return features
    
    def _calculate_execution_complexity(self, features: Dict[str, Any]) -> int:
        """Calculate complexity score for execution task"""
        complexity = 2  # Base complexity
        
        # Dependencies increase complexity
        complexity += features.get('num_dependencies', 0)
        
        # Resource requirements add complexity
        if features.get('resource_complexity', 0) > 3:
            complexity += 2
        
        # Constraints add complexity
        if features.get('time_constrained', False):
            complexity += 1
        if features.get('resource_constrained', False):
            complexity += 1
        
        # Multiple files increase complexity
        if features.get('num_files', 0) > 5:
            complexity += 2
        
        # Risk factors add complexity
        complexity += features.get('num_risks', 0)
        
        return min(complexity, 10)
    
    def _detect_patterns(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Kenny-specific pattern detection for execution tasks"""
        patterns = []
        
        task_type = features.get('task_type', 'unknown')
        
        # Sequential execution pattern
        if features.get('num_dependencies', 0) > 0:
            patterns.append({
                'type': 'sequential_execution',
                'confidence': 0.9,
                'description': f'Task has {features["num_dependencies"]} dependencies requiring sequential execution',
                'parameters': {
                    'dependencies': features.get('num_dependencies', 0)
                }
            })
        
        # Parallel execution potential
        if features.get('num_files', 0) > 1 and features.get('num_dependencies', 0) == 0:
            patterns.append({
                'type': 'parallel_execution',
                'confidence': 0.85,
                'description': 'Multiple independent files can be processed in parallel',
                'parameters': {
                    'parallelizable_units': features.get('num_files', 0)
                }
            })
        
        # Resource-intensive pattern
        if features.get('resource_complexity', 0) > 3 or features.get('resource_constrained', False):
            patterns.append({
                'type': 'resource_intensive',
                'confidence': 0.8,
                'description': 'Task requires significant resource allocation',
                'parameters': {
                    'resource_level': 'high' if features.get('resource_complexity', 0) > 5 else 'moderate'
                }
            })
        
        # Time-critical pattern
        if features.get('time_constrained', False):
            patterns.append({
                'type': 'time_critical',
                'confidence': 0.9,
                'description': 'Task has time constraints requiring optimization',
                'parameters': {
                    'urgency': 'high'
                }
            })
        
        # Incremental build pattern
        if features.get('is_build_task', False):
            patterns.append({
                'type': 'incremental_build',
                'confidence': 0.75,
                'description': 'Build task benefits from incremental approach',
                'parameters': {
                    'build_type': features.get('build_target', 'unknown')
                }
            })
        
        # Idempotent operation pattern
        if task_type in ['organize', 'backup', 'cleanup']:
            patterns.append({
                'type': 'idempotent_operation',
                'confidence': 0.95,
                'description': 'Operation can be safely repeated',
                'parameters': {
                    'safe_retry': True
                }
            })
        
        return patterns
    
    def _analyze_structure(self, features: Dict[str, Any], patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Kenny-specific structural analysis"""
        # Determine execution strategy
        has_dependencies = features.get('has_dependencies', False)
        can_parallelize = any(p['type'] == 'parallel_execution' for p in patterns)
        
        if has_dependencies:
            execution_strategy = 'sequential'
        elif can_parallelize:
            execution_strategy = 'parallel'
        else:
            execution_strategy = 'simple'
        
        # Assess task scale
        complexity = features.get('complexity', 0)
        if complexity > 7:
            task_scale = 'large'
        elif complexity > 4:
            task_scale = 'medium'
        else:
            task_scale = 'small'
        
        # Dominant pattern
        dominant_pattern = None
        max_confidence = 0.0
        for pattern in patterns:
            if pattern['confidence'] > max_confidence:
                max_confidence = pattern['confidence']
                dominant_pattern = pattern['type']
        
        return {
            'type': 'execution_structure',
            'execution_strategy': execution_strategy,
            'task_scale': task_scale,
            'dominant_pattern': dominant_pattern,
            'pattern_count': len(patterns),
            'complexity_level': 'high' if complexity > 6 else 'moderate' if complexity > 3 else 'low',
            'parallelizable': can_parallelize,
            'has_dependencies': has_dependencies
        }
    
    def _detect_anomalies(self, features: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Kenny-specific anomaly detection"""
        anomalies = []
        
        # Circular dependency check
        if features.get('num_dependencies', 0) > 0:
            # In production, would do actual dependency graph analysis
            # For now, flag if suspiciously high number of dependencies
            if features['num_dependencies'] > 10:
                anomalies.append({
                    'type': 'excessive_dependencies',
                    'severity': 'high',
                    'description': f'{features["num_dependencies"]} dependencies detected - potential circular dependency or overcoupling'
                })
        
        # Resource conflict check
        if features.get('resource_constrained', False) and features.get('resource_complexity', 0) > 5:
            anomalies.append({
                'type': 'resource_conflict',
                'severity': 'high',
                'description': 'High resource requirements with resource constraints - execution may fail'
            })
        
        # Impossible deadline check
        if features.get('time_constrained', False) and features.get('complexity', 0) > 7:
            anomalies.append({
                'type': 'time_pressure',
                'severity': 'medium',
                'description': 'Complex task with tight deadline - may require optimization or simplification'
            })
        
        # File operation risk
        if features.get('num_files', 0) > 100:
            anomalies.append({
                'type': 'large_file_operation',
                'severity': 'medium',
                'description': f'Operating on {features["num_files"]} files - consider batch processing'
            })
        
        # Historical failure pattern
        task_type = features.get('task_type', 'unknown')
        build_history = context.get('build_history', [])
        if build_history:
            similar_tasks = [h for h in build_history if h.get('task_type') == task_type]
            if similar_tasks:
                failure_rate = sum(1 for t in similar_tasks if not t.get('success', True)) / len(similar_tasks)
                if failure_rate > 0.5:
                    anomalies.append({
                        'type': 'historical_failure_pattern',
                        'severity': 'medium',
                        'description': f'Similar {task_type} tasks have {failure_rate:.0%} failure rate'
                    })
        
        return anomalies
    
    def _integrate_with_context(self, patterns: List[Dict[str, Any]], structure: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Kenny-specific context integration"""
        # Get execution context
        build_history = context.get('build_history', [])
        available_resources = context.get('available_resources', {})
        preferred_formats = context.get('preferred_formats', [])
        
        # Calculate execution feasibility
        feasibility_score = 0.8  # Base feasibility
        
        # Adjust for resource availability
        if available_resources:
            resource_match = self._assess_resource_match(structure, available_resources)
            feasibility_score *= resource_match
        
        # Adjust for historical success
        if build_history:
            recent_success_rate = sum(1 for h in build_history[-10:] if h.get('success', False)) / min(len(build_history), 10)
            feasibility_score = feasibility_score * 0.7 + recent_success_rate * 0.3
        
        # Execution confidence based on patterns
        execution_confidence = sum(p['confidence'] for p in patterns) / max(len(patterns), 1) if patterns else 0.5
        
        return {
            'patterns': patterns,
            'structure': structure,
            'feasibility_score': feasibility_score,
            'execution_confidence': execution_confidence,
            'available_resources': available_resources,
            'preferred_formats': preferred_formats,
            'context_applied': True,
            'integration_quality': (feasibility_score + execution_confidence) / 2
        }
    
    def _assess_resource_match(self, structure: Dict[str, Any], available_resources: Dict[str, Any]) -> float:
        """Assess how well available resources match requirements"""
        # Simplified resource matching
        if structure.get('complexity_level') == 'high':
            required_level = 'high'
        elif structure.get('complexity_level') == 'moderate':
            required_level = 'moderate'
        else:
            required_level = 'low'
        
        available_level = available_resources.get('level', 'moderate')
        
        if available_level == required_level:
            return 1.0
        elif available_level == 'high':
            return 0.95
        else:
            return 0.7
    
    def _build_narrative(self, integrated: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Kenny-specific narrative construction"""
        patterns = integrated.get('patterns', [])
        structure = integrated.get('structure', {})
        feasibility = integrated.get('feasibility_score', 0.5)
        
        # Build execution narrative
        execution_strategy = structure.get('execution_strategy', 'unknown')
        task_scale = structure.get('task_scale', 'unknown')
        
        if not patterns:
            theme = 'simple_execution'
            coherence = 0.4
        elif execution_strategy == 'sequential':
            theme = 'orchestrated_sequential_execution'
            coherence = 0.9
        elif execution_strategy == 'parallel':
            theme = 'optimized_parallel_execution'
            coherence = 0.85
        else:
            theme = 'standard_execution'
            coherence = 0.7
        
        # Assess completeness
        has_strategy = execution_strategy != 'unknown'
        has_feasibility = feasibility > 0.5
        has_patterns = len(patterns) > 0
        completeness = sum([has_strategy, has_feasibility, has_patterns]) / 3.0
        
        return {
            'theme': theme,
            'coherence': coherence,
            'completeness': completeness,
            'execution_strategy': execution_strategy,
            'task_scale': task_scale,
            'feasibility': 'high' if feasibility > 0.8 else 'moderate' if feasibility > 0.5 else 'low'
        }
    
    def _identify_implications(self, integrated: Dict[str, Any], narrative: Dict[str, Any]) -> List[str]:
        """Kenny-specific implication identification"""
        implications = []
        
        patterns = integrated.get('patterns', [])
        structure = integrated.get('structure', {})
        feasibility = integrated.get('feasibility_score', 0.5)
        
        # Pattern-specific implications
        for pattern in patterns:
            ptype = pattern['type']
            confidence = pattern['confidence']
            
            if ptype == 'sequential_execution' and confidence > 0.8:
                num_deps = pattern.get('parameters', {}).get('dependencies', 0)
                implications.append(f"Sequential execution required - {num_deps} dependencies must complete in order")
            
            elif ptype == 'parallel_execution' and confidence > 0.8:
                units = pattern.get('parameters', {}).get('parallelizable_units', 0)
                implications.append(f"Parallel execution possible - can process {units} units concurrently for {units}x speedup")
            
            elif ptype == 'resource_intensive':
                level = pattern.get('parameters', {}).get('resource_level', 'unknown')
                implications.append(f"⚠️ {level.capitalize()} resource usage - allocate sufficient memory/CPU")
            
            elif ptype == 'time_critical':
                implications.append("⏰ Time-critical task - prioritize and optimize execution path")
            
            elif ptype == 'idempotent_operation':
                implications.append("✓ Idempotent operation - safe to retry on failure")
        
        # Feasibility implications
        if feasibility < 0.5:
            implications.append("⚠️ Low feasibility - high risk of execution failure")
        elif feasibility < 0.7:
            implications.append("⚠️ Moderate feasibility - proceed with caution and monitoring")
        
        # Scale implications
        task_scale = structure.get('task_scale', 'unknown')
        if task_scale == 'large':
            implications.append("Large-scale task - consider chunking or incremental execution")
        
        if not implications:
            implications.append("Standard execution applicable - no special considerations")
        
        return implications
    
    def _assess_quality(self, synthesis_output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Kenny-specific quality assessment"""
        narrative = synthesis_output.get('narrative', {})
        integrated = synthesis_output.get('integrated', {})
        
        coherence = narrative.get('coherence', 0.5)
        completeness = narrative.get('completeness', 0.5)
        feasibility = integrated.get('feasibility_score', 0.5)
        execution_confidence = integrated.get('execution_confidence', 0.5)
        
        # Weight factors for execution quality
        quality = (
            coherence * 0.2 +
            completeness * 0.2 +
            feasibility * 0.3 +
            execution_confidence * 0.3
        )
        
        return min(0.95, max(0.1, quality))
    
    def _assess_risks(self, implications: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Kenny-specific risk assessment"""
        risks = []
        
        # Check for execution failure risks
        if any('low feasibility' in imp.lower() for imp in implications):
            risks.append({
                'type': 'execution_failure_risk',
                'severity': 'high',
                'description': 'High probability of execution failure'
            })
        
        # Check for resource risks
        if any('resource usage' in imp.lower() for imp in implications):
            risks.append({
                'type': 'resource_exhaustion_risk',
                'severity': 'medium',
                'description': 'May exhaust available resources during execution'
            })
        
        # Check for time risks
        if any('time-critical' in imp.lower() for imp in implications):
            risks.append({
                'type': 'deadline_risk',
                'severity': 'medium',
                'description': 'May not complete within deadline'
            })
        
        # Check for dependency risks
        if any('sequential execution' in imp.lower() and 'dependencies' in imp.lower() for imp in implications):
            risks.append({
                'type': 'dependency_chain_risk',
                'severity': 'low',
                'description': 'Long dependency chain may amplify failures'
            })
        
        # Historical failure risk
        build_history = context.get('build_history', [])
        if build_history:
            recent_failures = sum(1 for h in build_history[-5:] if not h.get('success', True))
            if recent_failures >= 3:
                risks.append({
                    'type': 'pattern_failure_risk',
                    'severity': 'high',
                    'description': f'Recent failures detected ({recent_failures}/5)'
                })
        
        return risks
    
    def _generate_decision_options(self, evaluation_output: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Kenny-specific decision option generation"""
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        options = []
        
        # Execute immediately option
        if quality > 0.7 and len([r for r in risks if r.get('severity') == 'high']) == 0:
            options.append({
                'action': 'execute_immediately',
                'confidence': min(0.95, quality),
                'description': 'Execute task immediately - all checks passed',
                'priority': 1,
                'execution_plan': {
                    'approach': 'direct',
                    'monitoring': 'standard',
                    'rollback': 'available'
                }
            })
        
        # Execute with monitoring option
        if quality > 0.5:
            options.append({
                'action': 'execute_with_monitoring',
                'confidence': quality * 0.9,
                'description': 'Execute with enhanced monitoring and checkpoints',
                'priority': 2,
                'execution_plan': {
                    'approach': 'monitored',
                    'monitoring': 'enhanced',
                    'checkpoints': True,
                    'rollback': 'immediate'
                }
            })
        
        # Execute incrementally option
        if quality > 0.4:
            options.append({
                'action': 'execute_incrementally',
                'confidence': quality * 0.8,
                'description': 'Break into smaller steps, validate each step',
                'priority': 3,
                'execution_plan': {
                    'approach': 'incremental',
                    'monitoring': 'per_step',
                    'validation': 'continuous',
                    'rollback': 'per_step'
                }
            })
        
        # Defer execution option
        options.append({
            'action': 'defer_execution',
            'confidence': 0.0,
            'description': 'Defer execution - conditions not suitable',
            'priority': 4,
            'execution_plan': {
                'approach': 'deferred',
                'reason': 'quality_threshold_not_met' if quality < 0.5 else 'high_risk_detected',
                'recommendations': ['Gather more resources', 'Resolve dependencies', 'Optimize plan']
            }
        })
        
        return sorted(options, key=lambda x: x['priority'])
    
    def _select_best_option(self, options: List[Dict[str, Any]], quality: float, risks: List[Dict[str, Any]], confidence: float) -> Dict[str, Any]:
        """Kenny-specific option selection"""
        if not options:
            return {
                'action': 'defer_execution',
                'confidence': 0.0,
                'description': 'No viable execution options',
                'execution_plan': {}
            }
        
        # Check for high-severity risks
        high_severity_risks = [r for r in risks if r.get('severity') == 'high']
        
        if high_severity_risks and len(high_severity_risks) >= 2:
            # Multiple high risks - must defer
            return [o for o in options if o['action'] == 'defer_execution'][0]
        
        if high_severity_risks:
            # One high risk - use monitored or incremental approach
            conservative_options = [o for o in options if o['action'] in ['execute_with_monitoring', 'execute_incrementally']]
            return conservative_options[0] if conservative_options else options[0]
        
        # No high risks - select highest priority option
        return options[0]
    
    def _calculate_commitment(self, confidence: float, risks: List[Dict[str, Any]]) -> float:
        """Kenny-specific commitment calculation"""
        commitment = confidence
        
        # Reduce commitment based on risk severity
        for risk in risks:
            severity = risk.get('severity', 'low')
            if severity == 'high':
                commitment *= 0.5
            elif severity == 'medium':
                commitment *= 0.75
            else:
                commitment *= 0.9
        
        return max(0.1, min(0.95, commitment))
    
    def _generate_rationale(self, selected_option: Dict[str, Any], evaluation_output: Dict[str, Any], confidence: float) -> str:
        """Kenny-specific rationale generation"""
        action = selected_option.get('action', 'unknown')
        option_confidence = selected_option.get('confidence', 0.0)
        description = selected_option.get('description', '')
        execution_plan = selected_option.get('execution_plan', {})
        quality = evaluation_output.get('quality_score', 0.0)
        risks = evaluation_output.get('risks', [])
        
        rationale = f"Kenny's Execution Plan: {description}\n"
        rationale += f"Execution Confidence: {option_confidence:.2f}\n"
        rationale += f"Quality Score: {quality:.2f}\n"
        rationale += f"Overall Confidence: {confidence:.2f}\n"
        
        if execution_plan:
            rationale += f"\nExecution Strategy:\n"
            rationale += f"  Approach: {execution_plan.get('approach', 'unknown')}\n"
            rationale += f"  Monitoring: {execution_plan.get('monitoring', 'unknown')}\n"
            if 'checkpoints' in execution_plan:
                rationale += f"  Checkpoints: {'Enabled' if execution_plan['checkpoints'] else 'Disabled'}\n"
            if 'rollback' in execution_plan:
                rationale += f"  Rollback: {execution_plan['rollback']}\n"
        
        if risks:
            rationale += f"\nRisks Identified: {len(risks)}\n"
            for risk in risks:
                rationale += f"  - {risk.get('type', 'unknown')}: {risk.get('description', '')}\n"
        
        if 'recommendations' in execution_plan:
            rationale += f"\nRecommendations:\n"
            for rec in execution_plan['recommendations']:
                rationale += f"  • {rec}\n"
        
        return rationale
