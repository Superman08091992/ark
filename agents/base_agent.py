"""
A.R.K. Base Agent
Abstract base class for all Council agents
"""

import sqlite3
import json
import os
import httpx
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all A.R.K. agents"""
    
    def __init__(self, name: str, essence: str):
        self.name = name
        self.essence = essence
        # Use environment variable or current working directory
        base_path = os.getenv('ARK_BASE_PATH', os.getcwd())
        self.db_path = os.path.join(base_path, "data", "ark.db")
        self.files_dir = os.path.join(base_path, "files")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.files_dir, exist_ok=True)
        
        logger.info(f"🧠 {self.name} ({self.essence}) initialized")
    
    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_memory(self) -> Dict[str, Any]:
        """Retrieve agent's memory from database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT memory FROM agents WHERE name = ?', (self.name,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            return {}
        except Exception as e:
            logger.error(f"Error retrieving memory for {self.name}: {str(e)}")
            return {}
    
    def save_memory(self, memory: Dict[str, Any]):
        """Save agent's memory to database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE agents SET memory = ?, last_active = CURRENT_TIMESTAMP 
                WHERE name = ?
            ''', (json.dumps(memory), self.name))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving memory for {self.name}: {str(e)}")
    
    def log_file_operation(self, operation_type: str, file_path: str, success: bool = True, error_message: str = None):
        """Log file operation to database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO file_operations (id, operation_type, file_path, agent_name, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"{self.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                operation_type,
                file_path,
                self.name,
                1 if success else 0,
                error_message
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging file operation: {str(e)}")
    
    # Core Tools Available to All Agents
    
    async def tool_web_search(self, query: str) -> Dict[str, Any]:
        """Search the web for information"""
        try:
            # Simple web search simulation - in production, integrate with real search API
            logger.info(f"{self.name} searching web: {query}")
            
            # Mock search results for now
            results = {
                'query': query,
                'results': [
                    {
                        'title': f"Search result for: {query}",
                        'url': f"https://example.com/search?q={query}",
                        'snippet': f"Information related to {query} found on the web."
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return {'success': True, 'data': results}
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create or write to a file"""
        try:
            file_path = os.path.join(self.files_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_file_operation('create', filename, True)
            logger.info(f"{self.name} created file: {filename}")
            
            return {
                'success': True, 
                'filename': filename,
                'path': file_path,
                'size': len(content.encode('utf-8'))
            }
        except Exception as e:
            self.log_file_operation('create', filename, False, str(e))
            logger.error(f"File creation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_read_file(self, filename: str) -> Dict[str, Any]:
        """Read content from a file"""
        try:
            file_path = os.path.join(self.files_dir, filename)
            
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.log_file_operation('read', filename, True)
            logger.info(f"{self.name} read file: {filename}")
            
            return {
                'success': True,
                'filename': filename,
                'content': content,
                'size': len(content.encode('utf-8'))
            }
        except Exception as e:
            self.log_file_operation('read', filename, False, str(e))
            logger.error(f"File read error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_list_files(self) -> Dict[str, Any]:
        """List all files in the A.R.K. file system"""
        try:
            files = []
            
            for root, dirs, filenames in os.walk(self.files_dir):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, self.files_dir)
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'path': relative_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            logger.info(f"{self.name} listed {len(files)} files")
            return {'success': True, 'files': files}
        except Exception as e:
            logger.error(f"File listing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            file_path = os.path.join(self.files_dir, filename)
            
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            os.remove(file_path)
            self.log_file_operation('delete', filename, True)
            logger.info(f"{self.name} deleted file: {filename}")
            
            return {'success': True, 'filename': filename}
        except Exception as e:
            self.log_file_operation('delete', filename, False, str(e))
            logger.error(f"File deletion error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools for this agent"""
        base_tools = ['web_search', 'create_file', 'read_file', 'list_files', 'delete_file']
        agent_tools = getattr(self, '_agent_tools', [])
        return base_tools + agent_tools
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool by name"""
        tool_method = f"tool_{tool_name}"
        if hasattr(self, tool_method):
            return await getattr(self, tool_method)(**kwargs)
        else:
            return {'success': False, 'error': f'Tool {tool_name} not available'}
    
    @abstractmethod
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process incoming message - implemented by each agent"""
        pass
    
    @abstractmethod
    async def autonomous_task(self) -> None:
        """Background autonomous task - implemented by each agent"""
        pass