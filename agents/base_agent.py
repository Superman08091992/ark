from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import uuid
from datetime import datetime
import asyncio
import logging
from config.database import db_manager, AgentLog
from utils.logger import get_logger
from core.security import SecurityManager
from core.cache_manager import CacheManager

class BaseAgent(ABC):
    """Base class for all A.R.K. agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = get_logger(name)
        self.security = SecurityManager()
        self.cache = CacheManager()
        self.is_running = False
        self.health_status = "healthy"
        self.last_activity = datetime.utcnow()
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method - must be implemented by each agent"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data format - must be implemented by each agent"""
        pass
    
    async def execute(self, input_data: Dict[str, Any], parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute agent with logging and error handling"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Security check
            if not await self.security.validate_request(input_data, self.name):
                raise SecurityError(f"Security validation failed for {self.name}")
            
            # Input validation
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input data for {self.name}")
            
            # Check cache first
            cache_key = self._generate_cache_key(input_data)
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                self.logger.info(f"Returning cached result for {execution_id}")
                return cached_result
            
            # Process the request
            self.logger.info(f"Starting execution {execution_id}")

