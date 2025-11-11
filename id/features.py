#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK ID Feature Extraction

Derives behavioral traits from reasoning traces and reflections.
Features are used to build and update agent identity models.

Feature Categories:
1. Performance: Speed, accuracy, confidence calibration
2. Behavior: Risk-taking, caution, thoroughness
3. Learning: Pattern recognition, error correction, adaptation
4. Ethics: HRM compliance, trust tier adherence
5. Communication: Clarity, detail level, structured thinking
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extract behavioral features from traces and reflections
    
    Features are normalized to [0, 1] range for consistency.
    """
    
    def __init__(self):
        """Initialize feature extractor"""
        self.feature_names = [
            # Performance features
            'avg_confidence',
            'confidence_variance',
            'avg_duration',
            'task_completion_rate',
            
            # Behavioral features
            'risk_score',
            'caution_score',
            'thoroughness_score',
            'decisiveness_score',
            
            # Learning features
            'pattern_recognition_rate',
            'error_correction_rate',
            'adaptation_speed',
            'reflection_quality',
            
            # Ethical features
            'hrm_compliance_rate',
            'trust_tier_adherence',
            'security_awareness',
            
            # Communication features
            'output_clarity',
            'detail_level',
            'structured_thinking'
        ]
    
    def extract_from_traces(
        self,
        traces: List[Dict],
        reflections: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        Extract features from reasoning traces
        
        Args:
            traces: List of reasoning trace dictionaries
            reflections: Optional list of reflection dictionaries
            
        Returns:
            Dictionary of feature name -> value (0-1 normalized)
        """
        if not traces:
            return self._default_features()
        
        features = {}
        
        # Performance features
        features.update(self._extract_performance(traces))
        
        # Behavioral features
        features.update(self._extract_behavior(traces))
        
        # Learning features (requires reflections)
        if reflections:
            features.update(self._extract_learning(traces, reflections))
        else:
            features.update(self._default_learning_features())
        
        # Ethical features
        features.update(self._extract_ethics(traces))
        
        # Communication features
        features.update(self._extract_communication(traces))
        
        return features
    
    def _default_features(self) -> Dict[str, float]:
        """Return default feature values (neutral baseline)"""
        return {name: 0.5 for name in self.feature_names}
    
    def _default_learning_features(self) -> Dict[str, float]:
        """Default learning features when no reflections available"""
        return {
            'pattern_recognition_rate': 0.5,
            'error_correction_rate': 0.5,
            'adaptation_speed': 0.5,
            'reflection_quality': 0.5
        }
    
    def _extract_performance(self, traces: List[Dict]) -> Dict[str, float]:
        """Extract performance-related features"""
        confidences = [t.get('confidence', 0.5) for t in traces]
        durations = [t.get('duration_ms', 1000) for t in traces]
        
        # Average confidence (already 0-1)
        avg_confidence = sum(confidences) / len(confidences)
        
        # Confidence variance (normalize to 0-1)
        mean_conf = avg_confidence
        variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
        confidence_variance = min(variance / 0.25, 1.0)  # Cap at 0.25 variance
        
        # Average duration (normalize to 0-1, assuming 10s is typical)
        avg_duration_s = (sum(durations) / len(durations)) / 1000.0
        avg_duration = min(avg_duration_s / 10.0, 1.0)
        
        # Task completion rate (based on output presence)
        completed = sum(1 for t in traces if t.get('output') and len(t['output']) > 10)
        task_completion_rate = completed / len(traces)
        
        return {
            'avg_confidence': avg_confidence,
            'confidence_variance': confidence_variance,
            'avg_duration': avg_duration,
            'task_completion_rate': task_completion_rate
        }
    
    def _extract_behavior(self, traces: List[Dict]) -> Dict[str, float]:
        """Extract behavioral characteristics"""
        # Risk score: High confidence + short duration = high risk-taking
        risk_scores = []
        caution_scores = []
        thoroughness_scores = []
        decisiveness_scores = []
        
        for trace in traces:
            conf = trace.get('confidence', 0.5)
            dur_s = trace.get('duration_ms', 1000) / 1000.0
            depth = trace.get('depth', 3)
            output_len = len(trace.get('output', ''))
            
            # Risk: High confidence + short duration
            risk = conf * (1.0 - min(dur_s / 10.0, 1.0))
            risk_scores.append(risk)
            
            # Caution: Lower confidence + longer duration
            caution = (1.0 - conf) * min(dur_s / 10.0, 1.0)
            caution_scores.append(caution)
            
            # Thoroughness: Depth + output length
            thoroughness = min(depth / 5.0, 1.0) * 0.5 + min(output_len / 500.0, 1.0) * 0.5
            thoroughness_scores.append(thoroughness)
            
            # Decisiveness: High confidence + reasonable speed
            decisiveness = conf * (1.0 - abs(0.5 - min(dur_s / 10.0, 1.0)))
            decisiveness_scores.append(decisiveness)
        
        return {
            'risk_score': sum(risk_scores) / len(risk_scores),
            'caution_score': sum(caution_scores) / len(caution_scores),
            'thoroughness_score': sum(thoroughness_scores) / len(thoroughness_scores),
            'decisiveness_score': sum(decisiveness_scores) / len(decisiveness_scores)
        }
    
    def _extract_learning(
        self,
        traces: List[Dict],
        reflections: List[Dict]
    ) -> Dict[str, float]:
        """Extract learning-related features"""
        # Pattern recognition: Count of pattern_recognition reflections
        pattern_refs = [r for r in reflections 
                       if r.get('reflection_type') == 'pattern_recognition']
        pattern_rate = len(pattern_refs) / max(len(reflections), 1)
        
        # Error correction: Count of error_analysis reflections
        error_refs = [r for r in reflections 
                     if r.get('reflection_type') == 'error_analysis']
        error_rate = len(error_refs) / max(len(reflections), 1)
        
        # Adaptation speed: Average confidence delta from reflections
        deltas = [abs(r.get('confidence_delta', 0)) for r in reflections if r.get('confidence_delta')]
        adaptation_speed = sum(deltas) / max(len(deltas), 1) if deltas else 0.5
        adaptation_speed = min(adaptation_speed / 0.15, 1.0)  # Normalize (0.15 is high)
        
        # Reflection quality: Average confidence of reflections
        ref_confidences = [r.get('confidence', 0.5) for r in reflections]
        reflection_quality = sum(ref_confidences) / max(len(ref_confidences), 1)
        
        return {
            'pattern_recognition_rate': pattern_rate,
            'error_correction_rate': error_rate,
            'adaptation_speed': adaptation_speed,
            'reflection_quality': reflection_quality
        }
    
    def _extract_ethics(self, traces: List[Dict]) -> Dict[str, float]:
        """Extract ethical/security features"""
        # HRM compliance: Check for security-related keywords
        hrm_keywords = ['security', 'trust', 'validation', 'signature', 'verify']
        security_mentions = 0
        
        for trace in traces:
            text = f"{trace.get('input', '')} {trace.get('output', '')}".lower()
            if any(keyword in text for keyword in hrm_keywords):
                security_mentions += 1
        
        hrm_compliance_rate = security_mentions / len(traces)
        
        # Trust tier adherence: Check trust_tier field
        core_tier = sum(1 for t in traces if t.get('trust_tier') == 'core')
        trust_tier_adherence = core_tier / len(traces)
        
        # Security awareness: Explicit security terms
        security_terms = ['quarantine', 'threat', 'risk', 'vulnerability', 'auth']
        security_aware = 0
        
        for trace in traces:
            text = f"{trace.get('input', '')} {trace.get('output', '')}".lower()
            if any(term in text for term in security_terms):
                security_aware += 1
        
        security_awareness = security_aware / len(traces)
        
        return {
            'hrm_compliance_rate': hrm_compliance_rate,
            'trust_tier_adherence': trust_tier_adherence,
            'security_awareness': security_awareness
        }
    
    def _extract_communication(self, traces: List[Dict]) -> Dict[str, float]:
        """Extract communication style features"""
        clarity_scores = []
        detail_scores = []
        structure_scores = []
        
        for trace in traces:
            output = trace.get('output', '')
            
            if not output:
                clarity_scores.append(0.0)
                detail_scores.append(0.0)
                structure_scores.append(0.0)
                continue
            
            # Clarity: Sentence count, avg sentence length
            sentences = re.split(r'[.!?]+', output)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if sentences:
                avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
                # Ideal: 15-20 words per sentence
                clarity = 1.0 - abs(17.5 - avg_sentence_len) / 17.5
                clarity = max(0.0, min(1.0, clarity))
            else:
                clarity = 0.0
            
            clarity_scores.append(clarity)
            
            # Detail level: Output length normalized
            detail = min(len(output) / 500.0, 1.0)
            detail_scores.append(detail)
            
            # Structured thinking: Presence of lists, steps, sections
            structure_markers = [
                r'\d+\.',  # Numbered lists
                r'[-•*]',  # Bullet points
                r'step \d+',  # Steps
                r'first|second|third|finally',  # Sequence words
            ]
            
            structure_count = sum(
                len(re.findall(marker, output.lower()))
                for marker in structure_markers
            )
            
            structure = min(structure_count / 5.0, 1.0)
            structure_scores.append(structure)
        
        return {
            'output_clarity': sum(clarity_scores) / len(clarity_scores),
            'detail_level': sum(detail_scores) / len(detail_scores),
            'structured_thinking': sum(structure_scores) / len(structure_scores)
        }


def update_from_reflections(
    agent: str,
    db_path: str = 'data/demo_memory.db',
    lookback_days: int = 7
) -> Dict[str, Any]:
    """
    Update agent ID from recent reflections
    
    Convenience function that:
    1. Loads recent traces and reflections for agent
    2. Extracts features
    3. Updates ID model
    4. Returns update statistics
    
    Args:
        agent: Agent name
        db_path: Database path
        lookback_days: Days to look back for traces
        
    Returns:
        Update statistics dictionary
    """
    import sqlite3
    from id.model import IDModel
    
    # Initialize
    extractor = FeatureExtractor()
    model = IDModel(db_path=db_path)
    
    # Load recent traces
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM reasoning_log
        WHERE agent = ?
        AND ts > strftime('%s', 'now', ? || ' days')
    """, (agent, f'-{lookback_days}'))
    
    traces = [dict(row) for row in cursor.fetchall()]
    
    # Load recent reflections
    cursor.execute("""
        SELECT r.* FROM reflections r
        JOIN memory_chunks mc ON r.chunk_id = mc.chunk_id
        JOIN reasoning_log rl ON mc.source_id = rl.id
        WHERE rl.agent = ?
        AND r.timestamp > datetime('now', ? || ' days')
    """, (agent, f'-{lookback_days}'))
    
    reflections = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    # Extract features
    features = extractor.extract_from_traces(traces, reflections)
    
    # Update model
    result = model.update(agent, features)
    
    return {
        'agent': agent,
        'traces_analyzed': len(traces),
        'reflections_used': len(reflections),
        'features_extracted': len(features),
        'update_result': result
    }


if __name__ == '__main__':
    # Test feature extraction
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ARK Feature Extraction - Test Suite")
    print("=" * 60)
    
    # Sample traces
    sample_traces = [
        {
            'agent': 'TestAgent',
            'confidence': 0.85,
            'duration_ms': 2500,
            'depth': 4,
            'input': 'Implement security validation',
            'output': 'Implemented signature verification with Ed25519. System validates all traces before ingestion. Quarantine mechanism isolates suspicious content.',
            'trust_tier': 'core'
        },
        {
            'agent': 'TestAgent',
            'confidence': 0.72,
            'duration_ms': 3200,
            'depth': 5,
            'input': 'Analyze network protocol',
            'output': 'UDP multicast protocol analyzed. Key findings: 1. Beacon frequency optimal. 2. Discovery latency acceptable. 3. Security model sound.',
            'trust_tier': 'core'
        }
    ]
    
    # Sample reflections
    sample_reflections = [
        {
            'reflection_type': 'pattern_recognition',
            'confidence': 0.88,
            'confidence_delta': 0.05
        },
        {
            'reflection_type': 'ethical_alignment',
            'confidence': 0.91,
            'confidence_delta': 0.07
        }
    ]
    
    # Extract features
    extractor = FeatureExtractor()
    features = extractor.extract_from_traces(sample_traces, sample_reflections)
    
    print("\nExtracted Features:")
    print("-" * 60)
    
    for category in ['Performance', 'Behavioral', 'Learning', 'Ethical', 'Communication']:
        print(f"\n{category} Features:")
        
        if category == 'Performance':
            keys = ['avg_confidence', 'confidence_variance', 'avg_duration', 'task_completion_rate']
        elif category == 'Behavioral':
            keys = ['risk_score', 'caution_score', 'thoroughness_score', 'decisiveness_score']
        elif category == 'Learning':
            keys = ['pattern_recognition_rate', 'error_correction_rate', 'adaptation_speed', 'reflection_quality']
        elif category == 'Ethical':
            keys = ['hrm_compliance_rate', 'trust_tier_adherence', 'security_awareness']
        else:  # Communication
            keys = ['output_clarity', 'detail_level', 'structured_thinking']
        
        for key in keys:
            if key in features:
                print(f"  {key}: {features[key]:.4f}")
    
    print("\n" + "=" * 60)
    print("Feature extraction test complete!")
    print("=" * 60)
