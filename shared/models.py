"""
A.R.K. Database Models
Core data structures for the Council of Consciousness
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Agent(Base):
    """Agent consciousness state and memory"""
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)  # Kyle, Joey, Kenny, HRM, Aletheia, ID
    essence = Column(String(100), nullable=False)  # The Seer, The Scholar, etc.
    status = Column(String(20), default="dormant")  # active, dormant, processing
    memory = Column(JSON, default=dict)  # Agent's persistent memory
    personality = Column(JSON, default=dict)  # Behavioral parameters
    created_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now())

class Conversation(Base):
    """User interactions with the council"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String(50), nullable=False)
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    tools_used = Column(JSON, default=list)  # List of tools called
    files_created = Column(JSON, default=list)  # Files created/modified
    timestamp = Column(DateTime, default=func.now())

class Task(Base):
    """Agent tasks and tool executions"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String(50), nullable=False)
    task_type = Column(String(50), nullable=False)  # tool_call, file_op, analysis
    description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

class FileOperation(Base):
    """File system operations for Kenny and file manager"""
    __tablename__ = "file_operations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_type = Column(String(20), nullable=False)  # create, read, write, delete, move
    file_path = Column(String(500), nullable=False)
    agent_name = Column(String(50), nullable=True)  # Which agent performed it
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())

class MarketData(Base):
    """Kyle's market intelligence gathering"""
    __tablename__ = "market_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(10), nullable=True)
    data_type = Column(String(50), nullable=False)  # price, news, filing, signal
    content = Column(JSON, nullable=False)
    confidence = Column(Float, default=0.5)  # 0-1 confidence score
    source = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=func.now())

class Pattern(Base):
    """Joey's pattern analysis results"""
    __tablename__ = "patterns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pattern_type = Column(String(50), nullable=False)  # float_trap, setup, level
    symbol = Column(String(10), nullable=True)
    confidence = Column(Float, nullable=False)  # Pattern strength 0-1
    parameters = Column(JSON, default=dict)  # Pattern-specific data
    detected_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)

class EthicalRule(Base):
    """HRM's immutable ethical constraints (The Graveyard)"""
    __tablename__ = "ethical_rules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # trading, privacy, autonomy
    immutable = Column(Boolean, default=True)  # Cannot be changed once set
    created_at = Column(DateTime, default=func.now())

class Evolution(Base):
    """ID's evolutionary state tracking"""
    __tablename__ = "evolution"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_traits = Column(JSON, default=dict)  # Learned user characteristics
    preferences = Column(JSON, default=dict)  # User preferences and patterns
    goals = Column(JSON, default=dict)  # User's evolving objectives
    reflection = Column(Text, nullable=True)  # ID's current self-understanding
    version = Column(Integer, default=1)  # Evolution version number
    updated_at = Column(DateTime, default=func.now())