#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK ID Model

Agent identity model with confidence-weighted EWMA (Exponentially Weighted Moving Average)
learning curves. Behavioral features evolve over time based on reflection insights.

Learning Mechanisms:
1. EWMA Updates: Smooth adaptation with exponential decay
2. Confidence Weighting: High-confidence reflections have more impact
3. Learning Rate Adaptation: Faster learning for new agents, slower for stable
4. Feature Normalization: All features maintained in [0, 1] range
5. Provenance Tracking: Full history of updates for audit

Mathematical Model:
- new_value = alpha * observed_value + (1 - alpha) * old_value
- alpha = base_alpha * confidence_weight * learning_rate_factor
- confidence_weight = reflection_confidence^2 (quadratic to emphasize quality)
"""

import json
import logging
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available - using pure Python math")

logger = logging.getLogger(__name__)


class IDModel:
    """
    Agent Identity Model with confidence-weighted learning
    
    Maintains behavioral features for each agent and updates them
    based on reflection insights using EWMA with confidence weighting.
    """
    
    def __init__(
        self,
        db_path: str = 'data/demo_memory.db',
        base_alpha: float = 0.3,
        min_alpha: float = 0.05,
        max_alpha: float = 0.8
    ):
        """
        Initialize ID model
        
        Args:
            db_path: Path to SQLite database
            base_alpha: Base learning rate for EWMA (0.0-1.0)
            min_alpha: Minimum learning rate
            max_alpha: Maximum learning rate
        """
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        
        # Learning parameters
        self.base_alpha = base_alpha
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        
        # Initialize schema
        self._init_schema()
        
        logger.info(f"ID Model initialized: {db_path}")
    
    def _init_schema(self):
        """Initialize ID state table if not exists"""
        cursor = self.db.cursor()
        
        # Main ID state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS id_state (
                state_id TEXT PRIMARY KEY,
                agent TEXT NOT NULL UNIQUE,
                ts INTEGER NOT NULL,
                risk_score REAL DEFAULT 0.5,
                latency_score REAL DEFAULT 0.5,
                preference_vector TEXT,
                behavior_features TEXT,
                learning_curve TEXT,
                update_count INTEGER DEFAULT 0,
                last_updated INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Update history for provenance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS id_updates (
                update_id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                ts INTEGER NOT NULL,
                features_before TEXT,
                features_after TEXT,
                confidence_weight REAL,
                alpha_used REAL,
                reflection_count INTEGER,
                metadata TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_id_agent 
            ON id_state(agent)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_id_updates_agent 
            ON id_updates(agent, ts DESC)
        """)
        
        self.db.commit()
        logger.debug("ID schema initialized")
    
    def get_state(self, agent: str) -> Optional[Dict]:
        """
        Get current ID state for agent
        
        Args:
            agent: Agent name
            
        Returns:
            Dictionary with agent state or None if not found
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM id_state WHERE agent = ?
        """, (agent,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        state = dict(row)
        
        # Parse JSON fields
        if state.get('preference_vector'):
            state['preference_vector'] = json.loads(state['preference_vector'])
        if state.get('behavior_features'):
            state['behavior_features'] = json.loads(state['behavior_features'])
        if state.get('learning_curve'):
            state['learning_curve'] = json.loads(state['learning_curve'])
        
        return state
    
    def initialize_agent(
        self,
        agent: str,
        initial_features: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Initialize new agent in ID system
        
        Args:
            agent: Agent name
            initial_features: Optional initial feature values
            
        Returns:
            State ID
        """
        # Check if already exists
        existing = self.get_state(agent)
        if existing:
            logger.warning(f"Agent {agent} already initialized")
            return existing['state_id']
        
        state_id = str(uuid.uuid4())
        ts = int(time.time())
        
        # Default features (neutral baseline)
        if initial_features is None:
            initial_features = {
                'avg_confidence': 0.5,
                'risk_score': 0.5,
                'caution_score': 0.5,
                'thoroughness_score': 0.5,
                'pattern_recognition_rate': 0.5,
                'hrm_compliance_rate': 0.5
            }
        
        behavior_features = json.dumps(initial_features)
        
        # Initialize learning curve (EWMA parameters)
        learning_curve = json.dumps({
            'base_alpha': self.base_alpha,
            'current_alpha': self.base_alpha,
            'learning_phase': 'initialization',
            'stability_score': 0.0
        })
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO id_state 
            (state_id, agent, ts, behavior_features, learning_curve, update_count)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (state_id, agent, ts, behavior_features, learning_curve))
        
        self.db.commit()
        
        logger.info(f"Initialized agent {agent} with state_id {state_id}")
        return state_id
    
    def update(
        self,
        agent: str,
        observed_features: Dict[str, float],
        confidence: float = 0.8,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Update agent ID using confidence-weighted EWMA
        
        Args:
            agent: Agent name
            observed_features: New feature observations
            confidence: Confidence weight (0.0-1.0)
            metadata: Optional metadata for provenance
            
        Returns:
            Update statistics
        """
        # Get or initialize state
        state = self.get_state(agent)
        if not state:
            self.initialize_agent(agent, observed_features)
            state = self.get_state(agent)
        
        # Get current features
        current_features = state.get('behavior_features', {})
        if not current_features:
            current_features = {}
        
        # Calculate adaptive alpha
        alpha = self._calculate_alpha(
            update_count=state['update_count'],
            confidence=confidence,
            stability_score=state.get('learning_curve', {}).get('stability_score', 0.0)
        )
        
        # Apply EWMA updates
        new_features = {}
        feature_changes = {}
        
        for feature_name, observed_value in observed_features.items():
            current_value = current_features.get(feature_name, 0.5)
            
            # EWMA update: new = alpha * observed + (1 - alpha) * old
            new_value = alpha * observed_value + (1 - alpha) * current_value
            
            # Clamp to [0, 1]
            new_value = max(0.0, min(1.0, new_value))
            
            new_features[feature_name] = new_value
            feature_changes[feature_name] = new_value - current_value
        
        # Preserve features not in observed (carry forward)
        for feature_name, value in current_features.items():
            if feature_name not in new_features:
                new_features[feature_name] = value
        
        # Update learning curve
        learning_curve = state.get('learning_curve', {})
        learning_curve['current_alpha'] = alpha
        learning_curve['last_confidence'] = confidence
        
        # Calculate stability (how much features changed)
        if feature_changes:
            avg_change = sum(abs(c) for c in feature_changes.values()) / len(feature_changes)
            learning_curve['stability_score'] = 1.0 - min(avg_change / 0.5, 1.0)
        
        # Determine learning phase
        if state['update_count'] < 10:
            learning_curve['learning_phase'] = 'initialization'
        elif learning_curve.get('stability_score', 0) > 0.8:
            learning_curve['learning_phase'] = 'stable'
        else:
            learning_curve['learning_phase'] = 'adaptation'
        
        # Update database
        ts = int(time.time())
        update_count = state['update_count'] + 1
        
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE id_state
            SET behavior_features = ?,
                learning_curve = ?,
                update_count = ?,
                last_updated = ?,
                ts = ?
            WHERE agent = ?
        """, (
            json.dumps(new_features),
            json.dumps(learning_curve),
            update_count,
            ts,
            ts,
            agent
        ))
        
        # Record update history
        update_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO id_updates
            (update_id, agent, ts, features_before, features_after, 
             confidence_weight, alpha_used, reflection_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            update_id,
            agent,
            ts,
            json.dumps(current_features),
            json.dumps(new_features),
            confidence,
            alpha,
            len(observed_features),
            json.dumps(metadata or {})
        ))
        
        self.db.commit()
        
        logger.info(f"Updated agent {agent}: alpha={alpha:.3f}, changes={len(feature_changes)}")
        
        return {
            'agent': agent,
            'update_id': update_id,
            'alpha_used': alpha,
            'confidence_weight': confidence,
            'features_updated': len(new_features),
            'avg_change': sum(abs(c) for c in feature_changes.values()) / max(len(feature_changes), 1),
            'learning_phase': learning_curve['learning_phase'],
            'stability_score': learning_curve.get('stability_score', 0.0),
            'update_count': update_count
        }
    
    def _calculate_alpha(
        self,
        update_count: int,
        confidence: float,
        stability_score: float
    ) -> float:
        """
        Calculate adaptive alpha (learning rate) for EWMA
        
        Strategy:
        1. New agents (low update_count): Higher alpha (faster learning)
        2. High confidence: Higher alpha (trust the observation)
        3. Stable agents: Lower alpha (resist noise)
        
        Args:
            update_count: Number of previous updates
            confidence: Confidence in current observation
            stability_score: Current stability (0=volatile, 1=stable)
            
        Returns:
            Alpha value in [min_alpha, max_alpha]
        """
        # Base alpha
        alpha = self.base_alpha
        
        # Confidence weighting (quadratic to emphasize quality)
        confidence_weight = confidence ** 2
        alpha *= confidence_weight
        
        # Experience factor: Higher alpha for new agents
        if update_count < 10:
            experience_factor = 1.5
        elif update_count < 50:
            experience_factor = 1.0
        else:
            experience_factor = 0.8
        
        alpha *= experience_factor
        
        # Stability factor: Lower alpha for stable agents
        if stability_score > 0.8:
            stability_factor = 0.7
        elif stability_score > 0.5:
            stability_factor = 0.9
        else:
            stability_factor = 1.0
        
        alpha *= stability_factor
        
        # Clamp to valid range
        alpha = max(self.min_alpha, min(self.max_alpha, alpha))
        
        return alpha
    
    def get_learning_curve(self, agent: str) -> Optional[Dict]:
        """Get learning curve statistics for agent"""
        state = self.get_state(agent)
        if not state:
            return None
        
        return state.get('learning_curve', {})
    
    def get_update_history(
        self,
        agent: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get update history for agent
        
        Args:
            agent: Agent name
            limit: Max number of updates to return
            
        Returns:
            List of update records
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM id_updates
            WHERE agent = ?
            ORDER BY ts DESC
            LIMIT ?
        """, (agent, limit))
        
        updates = []
        for row in cursor.fetchall():
            update = dict(row)
            # Parse JSON fields
            if update.get('features_before'):
                update['features_before'] = json.loads(update['features_before'])
            if update.get('features_after'):
                update['features_after'] = json.loads(update['features_after'])
            if update.get('metadata'):
                update['metadata'] = json.loads(update['metadata'])
            updates.append(update)
        
        return updates
    
    def get_all_agents(self) -> List[str]:
        """Get list of all agents in ID system"""
        cursor = self.db.cursor()
        cursor.execute("SELECT agent FROM id_state ORDER BY agent")
        return [row[0] for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get ID system statistics"""
        cursor = self.db.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM id_state")
        total_agents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM id_updates")
        total_updates = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT AVG(update_count) FROM id_state
        """)
        avg_updates_per_agent = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT agent, update_count
            FROM id_state
            ORDER BY update_count DESC
            LIMIT 5
        """)
        top_agents = [(row[0], row[1]) for row in cursor.fetchall()]
        
        return {
            'total_agents': total_agents,
            'total_updates': total_updates,
            'avg_updates_per_agent': round(avg_updates_per_agent, 2),
            'top_agents': top_agents
        }
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
            logger.info("ID model closed")


if __name__ == '__main__':
    # Test ID model
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ARK ID Model - Test Suite")
    print("=" * 60)
    
    # Initialize model
    model = IDModel(db_path='data/demo_memory.db')
    
    print("\n1. Initializing test agent...")
    state_id = model.initialize_agent('TestAgent')
    print(f"State ID: {state_id}")
    
    print("\n2. Initial state:")
    state = model.get_state('TestAgent')
    if state:
        print(f"  Features: {state['behavior_features']}")
        print(f"  Learning curve: {state['learning_curve']}")
    
    print("\n3. Simulating updates...")
    
    # Update 1: High confidence
    update1 = model.update('TestAgent', {
        'avg_confidence': 0.85,
        'risk_score': 0.7,
        'pattern_recognition_rate': 0.6
    }, confidence=0.9)
    print(f"\nUpdate 1 (conf=0.9): alpha={update1['alpha_used']:.3f}, "
          f"phase={update1['learning_phase']}")
    
    # Update 2: Medium confidence
    update2 = model.update('TestAgent', {
        'avg_confidence': 0.75,
        'risk_score': 0.65,
        'pattern_recognition_rate': 0.7
    }, confidence=0.6)
    print(f"Update 2 (conf=0.6): alpha={update2['alpha_used']:.3f}, "
          f"phase={update2['learning_phase']}")
    
    # Update 3: Low confidence (should have less impact)
    update3 = model.update('TestAgent', {
        'avg_confidence': 0.95,
        'risk_score': 0.9,
        'pattern_recognition_rate': 0.9
    }, confidence=0.3)
    print(f"Update 3 (conf=0.3): alpha={update3['alpha_used']:.3f}, "
          f"phase={update3['learning_phase']}")
    
    print("\n4. Final state:")
    state = model.get_state('TestAgent')
    if state:
        print(f"  Update count: {state['update_count']}")
        print(f"  Learning phase: {state['learning_curve']['learning_phase']}")
        print(f"  Stability: {state['learning_curve'].get('stability_score', 0):.3f}")
        print(f"  Features:")
        for name, value in state['behavior_features'].items():
            print(f"    {name}: {value:.3f}")
    
    print("\n5. Update history:")
    history = model.get_update_history('TestAgent', limit=3)
    for i, update in enumerate(history, 1):
        print(f"\n  Update {i}:")
        print(f"    Timestamp: {datetime.fromtimestamp(update['ts'])}")
        print(f"    Alpha: {update['alpha_used']:.3f}")
        print(f"    Confidence: {update['confidence_weight']:.3f}")
    
    print("\n6. System statistics:")
    stats = model.get_stats()
    print(f"  Total agents: {stats['total_agents']}")
    print(f"  Total updates: {stats['total_updates']}")
    print(f"  Avg updates/agent: {stats['avg_updates_per_agent']}")
    
    print("\n7. Cleanup...")
    model.close()
    
    print("\n" + "=" * 60)
    print("ID model test complete!")
    print("=" * 60)
