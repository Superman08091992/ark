#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Reflection Engine

Nightly "sleep mode" that performs self-analysis on reasoning traces.
Extracts insights, patterns, and learning opportunities.

Architecture:
- Memory Engine: Provides consolidated reasoning traces
- Reflection Engine: Analyzes traces and generates insights
- HRM Validator: Ensures ethical alignment
- ID System: Consumes insights for behavioral evolution
"""

import asyncio
import datetime
import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not available - using default policies")

logger = logging.getLogger(__name__)


class ReflectionEngine:
    """
    Reflection Engine for autonomous learning
    
    Performs nightly self-analysis on reasoning traces:
    1. Load recent memory chunks (up to max_chunks_per_cycle)
    2. Analyze each chunk for patterns and insights
    3. Generate reflections with confidence scores
    4. Validate with HRM (if enabled)
    5. Store reflections in database
    6. Send insights to ID system (if enabled)
    """
    
    def __init__(
        self,
        db_path: str = "data/demo_memory.db",
        policy_path: str = "reflection/reflection_policies.yaml"
    ):
        """
        Initialize reflection engine
        
        Args:
            db_path: Path to SQLite database
            policy_path: Path to reflection policies YAML
        """
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        
        # Load policies
        self.policy = self._load_policy(policy_path)
        
        # Initialize HRM validator (optional)
        self.hrm = None
        if self.policy.get('require_hrm_signature', False):
            try:
                from hrm.validator import HRMValidator
                self.hrm = HRMValidator()
                logger.info("HRM validator initialized")
            except ImportError:
                logger.warning("HRM validator not available - signatures disabled")
        
        # Initialize memory engine (optional)
        self.memory = None
        try:
            from memory.engine import MemoryEngine
            self.memory = MemoryEngine(db_path)
            logger.info("Memory engine initialized")
        except ImportError:
            logger.warning("Memory engine not available - direct DB access only")
        
        # Initialize schema
        self._init_schema()
        
        logger.info(f"Reflection Engine initialized: {db_path}")
    
    def _load_policy(self, path: str) -> Dict:
        """Load reflection policies from YAML file"""
        if not YAML_AVAILABLE:
            # Return default policies
            return {
                'mode': 'sleep',
                'max_chunks_per_cycle': 50,
                'min_confidence_delta': 0.05,
                'min_confidence_threshold': 0.3,
                'max_confidence_threshold': 0.95,
                'quarantine_violations': True,
                'require_hrm_signature': True,
                'trust_tier_weighting': True,
                'trust_weights': {
                    'core': 1.0,
                    'sandbox': 0.8,
                    'external': 0.5,
                    'unknown': 0.3
                },
                'reflection_retention_days': 90,
                'audit_log_path': 'logs/reflection_audit.log',
                'debug_mode': False,
                'enable_id_updates': True,
                'enable_memory_updates': True
            }
        
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('reflection', {})
        except FileNotFoundError:
            logger.warning(f"Policy file not found: {path}, using defaults")
            return self._load_policy("")  # Recursive call for defaults
    
    def _init_schema(self):
        """Initialize reflections table if not exists"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                reflection_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                chunk_id TEXT,
                tier TEXT,
                summary_hash TEXT,
                insight TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                confidence_delta REAL DEFAULT 0.0,
                reflection_type TEXT,
                signature TEXT,
                metadata TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reflections_timestamp 
            ON reflections(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reflections_chunk 
            ON reflections(chunk_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reflections_type 
            ON reflections(reflection_type)
        """)
        
        self.db.commit()
        logger.debug("Reflection schema initialized")
    
    def _log(self, msg: str, level: str = "INFO"):
        """Write to audit log"""
        audit_path = self.policy.get('audit_log_path', 'logs/reflection_audit.log')
        
        # Ensure log directory exists
        Path(audit_path).parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] [{level}] {msg}\n"
        
        with open(audit_path, 'a') as log:
            log.write(log_entry)
        
        # Also log to standard logger
        if level == "ERROR":
            logger.error(msg)
        elif level == "WARNING":
            logger.warning(msg)
        else:
            logger.info(msg)
    
    def generate_reflections(self) -> Dict[str, Any]:
        """
        Perform nightly reflection on recent memory chunks
        
        Returns:
            Statistics dictionary with reflection results
        """
        start_time = time.time()
        self._log("Starting reflection cycle")
        
        # Load recent chunks
        chunks = self._load_recent_chunks()
        self._log(f"Loaded {len(chunks)} chunks for reflection")
        
        if not chunks:
            self._log("No chunks to reflect on", "WARNING")
            return {
                'status': 'no_chunks',
                'chunks_processed': 0,
                'reflections_generated': 0,
                'duration_seconds': 0
            }
        
        # Generate reflections
        reflections = []
        for chunk in chunks:
            reflection = self._reflect(chunk)
            if reflection:
                reflections.append(reflection)
        
        self._log(f"Generated {len(reflections)} reflections from {len(chunks)} chunks")
        
        # Store reflections
        stored_count = 0
        for reflection in reflections:
            if self._store_reflection(reflection):
                stored_count += 1
        
        self.db.commit()
        
        # Update ID system if enabled
        if self.policy.get('enable_id_updates', False):
            self._update_id_system(reflections)
        
        duration = time.time() - start_time
        self._log(f"Reflection cycle complete: {stored_count} reflections stored in {duration:.2f}s")
        
        return {
            'status': 'success',
            'chunks_processed': len(chunks),
            'reflections_generated': len(reflections),
            'reflections_stored': stored_count,
            'duration_seconds': round(duration, 2)
        }
    
    def _load_recent_chunks(self) -> List[Dict]:
        """Load recent memory chunks for reflection"""
        cursor = self.db.cursor()
        
        max_chunks = self.policy.get('max_chunks_per_cycle', 50)
        min_confidence = self.policy.get('min_confidence_threshold', 0.3)
        max_confidence = self.policy.get('max_confidence_threshold', 0.95)
        
        # Get chunks that haven't been reflected on recently
        # and have confidence in the reflection-worthy range
        cursor.execute("""
            SELECT 
                mc.chunk_id,
                mc.text,
                mc.summary,
                mc.trust_tier,
                mc.ts,
                rl.confidence,
                rl.agent
            FROM memory_chunks mc
            LEFT JOIN reasoning_log rl ON mc.source_id = rl.id
            WHERE mc.consolidated = 1
                AND rl.confidence >= ?
                AND rl.confidence <= ?
                AND mc.chunk_id NOT IN (
                    SELECT chunk_id FROM reflections 
                    WHERE timestamp > datetime('now', '-1 day')
                )
            ORDER BY mc.ts DESC
            LIMIT ?
        """, (min_confidence, max_confidence, max_chunks))
        
        chunks = []
        for row in cursor.fetchall():
            chunks.append({
                'chunk_id': row['chunk_id'],
                'text': row['text'],
                'summary': row['summary'],
                'trust_tier': row['trust_tier'],
                'ts': row['ts'],
                'confidence': row['confidence'] if row['confidence'] else 0.5,
                'agent': row['agent'] if row['agent'] else 'unknown'
            })
        
        return chunks
    
    def _reflect(self, chunk: Dict) -> Optional[Dict]:
        """
        Analyze a memory chunk and generate reflection
        
        Args:
            chunk: Memory chunk dictionary
            
        Returns:
            Reflection dictionary or None if no insight found
        """
        # Apply trust tier weighting
        trust_weight = self._get_trust_weight(chunk['trust_tier'])
        base_confidence = chunk['confidence']
        weighted_confidence = base_confidence * trust_weight
        
        # Skip if weighted confidence too low
        if weighted_confidence < self.policy.get('min_confidence_threshold', 0.3):
            return None
        
        # Generate insight based on reflection type
        insight, reflection_type = self._generate_insight(chunk)
        
        if not insight:
            return None
        
        # Calculate confidence delta (how much we learned)
        confidence_delta = self._calculate_confidence_delta(chunk, insight)
        
        # Skip if delta too small (trivial reflection)
        if abs(confidence_delta) < self.policy.get('min_confidence_delta', 0.05):
            return None
        
        # Create reflection
        reflection = {
            'reflection_id': self._generate_id(),
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'chunk_id': chunk['chunk_id'],
            'tier': chunk['trust_tier'],
            'summary_hash': hashlib.sha256(chunk['summary'].encode()).hexdigest(),
            'insight': insight,
            'confidence': round(weighted_confidence + confidence_delta, 2),
            'confidence_delta': round(confidence_delta, 2),
            'reflection_type': reflection_type,
            'metadata': json.dumps({
                'agent': chunk['agent'],
                'original_confidence': base_confidence,
                'trust_weight': trust_weight,
                'timestamp': chunk['ts']
            })
        }
        
        # Sign reflection if HRM enabled
        if self.hrm and self.policy.get('require_hrm_signature', False):
            reflection['signature'] = self._sign_reflection(reflection)
        
        return reflection
    
    def _get_trust_weight(self, tier: str) -> float:
        """Get trust weight multiplier for tier"""
        weights = self.policy.get('trust_weights', {})
        return weights.get(tier.lower(), 0.5)
    
    def _generate_insight(self, chunk: Dict) -> tuple:
        """
        Generate insight from chunk analysis
        
        Returns:
            (insight_text, reflection_type) tuple
        """
        text = chunk['summary']
        confidence = chunk['confidence']
        
        # Pattern recognition: Look for repeated concepts
        if 'implement' in text.lower() and 'protocol' in text.lower():
            return (
                f"Implementation pattern: {text[:100]}... demonstrates systematic protocol design",
                'pattern_recognition'
            )
        
        # Error analysis: Look for problems or failures
        if any(word in text.lower() for word in ['error', 'failed', 'issue', 'problem']):
            return (
                f"Error analysis: Identified failure mode in {text[:80]}...",
                'error_analysis'
            )
        
        # Confidence calibration: Look for confidence mismatches
        if confidence < 0.5:
            return (
                f"Low confidence detected: {text[:100]}... requires validation",
                'confidence_calibration'
            )
        
        # Ethical alignment: Look for HRM-related content
        if any(word in text.lower() for word in ['security', 'trust', 'validation', 'quarantine']):
            return (
                f"Ethical validation: {text[:100]}... demonstrates security awareness",
                'ethical_alignment'
            )
        
        # Performance optimization: Look for efficiency patterns
        if any(word in text.lower() for word in ['optimize', 'improve', 'enhance', 'efficient']):
            return (
                f"Performance insight: {text[:100]}... shows optimization thinking",
                'performance_optimization'
            )
        
        # Default: General learning
        return (
            f"Learning insight: {text[:120]}...",
            'pattern_recognition'
        )
    
    def _calculate_confidence_delta(self, chunk: Dict, insight: str) -> float:
        """Calculate confidence improvement from reflection"""
        # Simple heuristic: insight quality affects confidence
        base_delta = 0.05
        
        # Boost for specific insight types
        if 'pattern' in insight.lower():
            base_delta += 0.03
        if 'validation' in insight.lower():
            base_delta += 0.02
        if 'error' in insight.lower():
            base_delta += 0.04  # Learning from errors is valuable
        
        # Reduce for already high confidence
        if chunk['confidence'] > 0.8:
            base_delta *= 0.5
        
        return min(base_delta, 0.15)  # Cap at 0.15 improvement
    
    def _generate_id(self) -> str:
        """Generate unique reflection ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _sign_reflection(self, reflection: Dict) -> str:
        """Sign reflection with HRM validator"""
        if not self.hrm:
            return ""
        
        try:
            # Create canonical representation for signing
            canonical = json.dumps({
                'reflection_id': reflection['reflection_id'],
                'timestamp': reflection['timestamp'],
                'insight': reflection['insight'],
                'confidence': reflection['confidence']
            }, sort_keys=True)
            
            # Sign with HRM
            signature = self.hrm.sign(canonical)
            return signature
        except Exception as e:
            logger.error(f"Failed to sign reflection: {e}")
            return ""
    
    def _store_reflection(self, reflection: Dict) -> bool:
        """Store reflection in database"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO reflections 
                (reflection_id, timestamp, chunk_id, tier, summary_hash, 
                 insight, confidence, confidence_delta, reflection_type, 
                 signature, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reflection['reflection_id'],
                reflection['timestamp'],
                reflection['chunk_id'],
                reflection['tier'],
                reflection['summary_hash'],
                reflection['insight'],
                reflection['confidence'],
                reflection['confidence_delta'],
                reflection['reflection_type'],
                reflection.get('signature', ''),
                reflection.get('metadata', '{}')
            ))
            
            return True
        except Exception as e:
            logger.error(f"Failed to store reflection: {e}")
            return False
    
    def _update_id_system(self, reflections: List[Dict]):
        """Send insights to ID system for behavioral evolution"""
        if not reflections:
            return
        
        self._log(f"Sending {len(reflections)} insights to ID system")
        
        # TODO: Implement ID system integration
        # For now, just log the intent
        for reflection in reflections:
            logger.debug(f"ID update: {reflection['reflection_type']} - {reflection['insight'][:50]}...")
    
    def get_stats(self) -> Dict:
        """Get reflection statistics"""
        cursor = self.db.cursor()
        
        # Total reflections
        cursor.execute("SELECT COUNT(*) FROM reflections")
        total = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT reflection_type, COUNT(*) as count
            FROM reflections
            GROUP BY reflection_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent (last 24h)
        cursor.execute("""
            SELECT COUNT(*) FROM reflections
            WHERE timestamp > datetime('now', '-1 day')
        """)
        recent = cursor.fetchone()[0]
        
        # Average confidence delta
        cursor.execute("SELECT AVG(confidence_delta) FROM reflections")
        avg_delta = cursor.fetchone()[0] or 0.0
        
        return {
            'total_reflections': total,
            'reflections_by_type': by_type,
            'recent_24h': recent,
            'avg_confidence_delta': round(avg_delta, 4)
        }
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
            logger.info("Reflection engine closed")


if __name__ == '__main__':
    # Test reflection engine
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ARK Reflection Engine - Test Suite")
    print("=" * 60)
    
    # Initialize engine
    engine = ReflectionEngine(
        db_path='data/demo_memory.db',
        policy_path='reflection/reflection_policies.yaml'
    )
    
    print("\n1. Running reflection cycle...")
    result = engine.generate_reflections()
    print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\n2. Getting statistics...")
    stats = engine.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
    
    print("\n3. Cleanup...")
    engine.close()
    
    print("\n" + "=" * 60)
    print("Reflection engine test complete!")
    print("=" * 60)
