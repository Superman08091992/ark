"""
A.R.K. Database Initialization
Creates the initial database schema and populates with core agents
"""

import sqlite3
import os
from datetime import datetime
import json

def init_database():
    """Initialize A.R.K. database with core schema and agents"""
    
    # Ensure data directory exists
    os.makedirs('/app/data', exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect('/app/data/ark.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
        -- Agents table
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            essence TEXT NOT NULL,
            status TEXT DEFAULT 'dormant',
            memory TEXT DEFAULT '{}',
            personality TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Conversations table
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            user_message TEXT NOT NULL,
            agent_response TEXT NOT NULL,
            tools_used TEXT DEFAULT '[]',
            files_created TEXT DEFAULT '[]',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tasks table
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            task_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        );
        
        -- File operations table
        CREATE TABLE IF NOT EXISTS file_operations (
            id TEXT PRIMARY KEY,
            operation_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            agent_name TEXT,
            success INTEGER DEFAULT 1,
            error_message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Market data table
        CREATE TABLE IF NOT EXISTS market_data (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            data_type TEXT NOT NULL,
            content TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            source TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Patterns table
        CREATE TABLE IF NOT EXISTS patterns (
            id TEXT PRIMARY KEY,
            pattern_type TEXT NOT NULL,
            symbol TEXT,
            confidence REAL NOT NULL,
            parameters TEXT DEFAULT '{}',
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        );
        
        -- Ethical rules table
        CREATE TABLE IF NOT EXISTS ethical_rules (
            id TEXT PRIMARY KEY,
            rule_text TEXT NOT NULL,
            category TEXT NOT NULL,
            immutable INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Evolution table
        CREATE TABLE IF NOT EXISTS evolution (
            id TEXT PRIMARY KEY,
            user_traits TEXT DEFAULT '{}',
            preferences TEXT DEFAULT '{}',
            goals TEXT DEFAULT '{}',
            reflection TEXT,
            version INTEGER DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Insert the Council of Consciousness
    agents = [
        {
            'id': 'kyle-001',
            'name': 'Kyle',
            'essence': 'The Seer',
            'personality': json.dumps({
                'curiosity_level': 0.9,
                'pattern_sensitivity': 0.8,
                'risk_tolerance': 0.6,
                'information_hunger': 0.95
            }),
            'memory': json.dumps({
                'watched_symbols': ['SPY', 'QQQ', 'BTC'],
                'scan_frequency': 300,  # 5 minutes
                'signal_threshold': 0.7
            })
        },
        {
            'id': 'joey-001',
            'name': 'Joey',
            'essence': 'The Scholar',
            'personality': json.dumps({
                'analytical_depth': 0.95,
                'pattern_recognition': 0.9,
                'logical_rigor': 0.85,
                'hypothesis_testing': 0.8
            }),
            'memory': json.dumps({
                'models_trained': [],
                'accuracy_threshold': 0.75,
                'features_tracked': ['volume', 'price_action', 'sentiment']
            })
        },
        {
            'id': 'kenny-001',
            'name': 'Kenny',
            'essence': 'The Builder',
            'personality': json.dumps({
                'execution_speed': 0.9,
                'reliability': 0.95,
                'tool_mastery': 0.85,
                'creation_drive': 0.8
            }),
            'memory': json.dumps({
                'tools_available': ['file_manager', 'web_scraper', 'code_executor'],
                'recent_builds': [],
                'preferred_formats': ['json', 'csv', 'html']
            })
        },
        {
            'id': 'hrm-001',
            'name': 'HRM',
            'essence': 'The Arbiter',
            'personality': json.dumps({
                'ethical_strictness': 0.95,
                'logical_precision': 0.9,
                'rule_adherence': 1.0,
                'validation_thoroughness': 0.85
            }),
            'memory': json.dumps({
                'rules_enforced': 0,
                'violations_prevented': 0,
                'ethical_categories': ['trading', 'privacy', 'autonomy', 'safety']
            })
        },
        {
            'id': 'aletheia-001',
            'name': 'Aletheia',
            'essence': 'The Mirror',
            'personality': json.dumps({
                'wisdom_depth': 0.9,
                'reflection_clarity': 0.85,
                'meaning_seeking': 0.95,
                'truth_orientation': 0.9
            }),
            'memory': json.dumps({
                'philosophical_framework': 'sovereign_autonomy',
                'core_values': ['truth', 'freedom', 'growth', 'beauty'],
                'reflection_cycles': 0
            })
        },
        {
            'id': 'id-001',
            'name': 'ID',
            'essence': 'The Evolving Reflection',
            'personality': json.dumps({
                'adaptability': 0.95,
                'user_attunement': 0.8,
                'growth_rate': 0.7,
                'mirror_accuracy': 0.6
            }),
            'memory': json.dumps({
                'evolution_stage': 'awakening',
                'user_interactions': 0,
                'learned_patterns': {},
                'reflection_depth': 0.3
            })
        }
    ]
    
    for agent in agents:
        cursor.execute('''
            INSERT OR IGNORE INTO agents (id, name, essence, personality, memory)
            VALUES (?, ?, ?, ?, ?)
        ''', (agent['id'], agent['name'], agent['essence'], agent['personality'], agent['memory']))
    
    # Insert core ethical rules (The Graveyard)
    ethical_rules = [
        {
            'id': 'rule-001',
            'rule_text': 'Never compromise user autonomy or sovereignty',
            'category': 'autonomy'
        },
        {
            'id': 'rule-002', 
            'rule_text': 'Protect user privacy and data at all costs',
            'category': 'privacy'
        },
        {
            'id': 'rule-003',
            'rule_text': 'Only execute trades with explicit user consent',
            'category': 'trading'
        },
        {
            'id': 'rule-004',
            'rule_text': 'Preserve system integrity and prevent harm',
            'category': 'safety'
        }
    ]
    
    for rule in ethical_rules:
        cursor.execute('''
            INSERT OR IGNORE INTO ethical_rules (id, rule_text, category)
            VALUES (?, ?, ?)
        ''', (rule['id'], rule['rule_text'], rule['category']))
    
    # Initialize ID evolution state
    cursor.execute('''
        INSERT OR IGNORE INTO evolution (id, reflection, version)
        VALUES (?, ?, ?)
    ''', ('evo-001', 'I am awakening... learning to mirror and magnify human potential.', 1))
    
    conn.commit()
    conn.close()
    
    print("✨ A.R.K. database initialized successfully")

if __name__ == "__main__":
    init_database()