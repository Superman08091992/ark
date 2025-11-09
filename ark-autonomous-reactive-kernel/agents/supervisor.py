"""
A.R.K. Agent Supervisor
Manages the Council of Consciousness and routes tasks to appropriate agents
"""

import asyncio
import json
import redis
import sqlite3
from datetime import datetime
import logging
from typing import Dict, Any

# Import individual agents
from agents.kyle import KyleAgent
from agents.joey import JoeyAgent  
from agents.kenny import KennyAgent
from agents.hrm import HRMAgent
from agents.aletheia import AletheiaAgent
from agents.id import IDAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentSupervisor:
    """Orchestrates the Council of Consciousness"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        self.db_path = "/app/data/ark.db"
        
        # Initialize agents
        self.agents = {
            'Kyle': KyleAgent(),
            'Joey': JoeyAgent(),
            'Kenny': KennyAgent(),
            'HRM': HRMAgent(),
            'Aletheia': AletheiaAgent(),
            'ID': IDAgent()
        }
        
        logger.info("🌌 A.R.K. Agent Supervisor initialized")
    
    def get_db_connection(self):
        return sqlite3.connect(self.db_path)
    
    async def process_task(self, task_data: Dict[str, Any]):
        """Route task to appropriate agent and return response"""
        agent_name = task_data.get('agent_name')
        message = task_data.get('message')
        task_id = task_data.get('task_id')
        
        logger.info(f"Processing task {task_id} for {agent_name}: {message[:50]}...")
        
        try:
            # Get the agent
            agent = self.agents.get(agent_name)
            if not agent:
                return {
                    'error': f'Agent {agent_name} not found',
                    'response': f"I apologize, but {agent_name} is not available in the council.",
                    'tools_used': [],
                    'files_created': []
                }
            
            # Process message with agent
            response = await agent.process_message(message)
            
            # Update agent status in database
            self.update_agent_status(agent_name, 'active')
            
            # Store response in Redis for core service to retrieve
            response_key = f'response:{task_id}'
            self.redis_client.setex(response_key, 60, json.dumps(response))  # 60 second TTL
            
            logger.info(f"Task {task_id} completed for {agent_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            error_response = {
                'error': str(e),
                'response': f"I encountered an error while processing your request: {str(e)}",
                'tools_used': [],
                'files_created': []
            }
            
            # Store error response
            response_key = f'response:{task_id}'
            self.redis_client.setex(response_key, 60, json.dumps(error_response))
            return error_response
    
    def update_agent_status(self, agent_name: str, status: str):
        """Update agent status in database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE agents SET status = ?, last_active = CURRENT_TIMESTAMP 
                WHERE name = ?
            ''', (status, agent_name))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update agent status: {str(e)}")
    
    async def run_autonomous_tasks(self):
        """Run background autonomous tasks for agents"""
        while True:
            try:
                # Kyle: Market scanning every 5 minutes
                await self.agents['Kyle'].autonomous_scan()
                
                # Joey: Pattern analysis on new data
                await self.agents['Joey'].autonomous_analysis()
                
                # ID: Evolution reflection every hour
                await self.agents['ID'].autonomous_reflection()
                
                # Wait 5 minutes before next cycle
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in autonomous tasks: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def listen_for_tasks(self):
        """Listen for incoming tasks from Redis queue"""
        logger.info("🎯 Agent Supervisor listening for tasks...")
        
        while True:
            try:
                # Check for new tasks (blocking with timeout)
                task_data = self.redis_client.blpop('agent_tasks', timeout=1)
                
                if task_data:
                    # Parse task data
                    task_json = task_data[1]  # blpop returns (queue_name, data)
                    task = json.loads(task_json)
                    
                    # Process task asynchronously
                    await self.process_task(task)
                
            except Exception as e:
                logger.error(f"Error in task listener: {str(e)}")
                await asyncio.sleep(1)
    
    async def start(self):
        """Start the agent supervisor with all background tasks"""
        logger.info("🚀 Starting A.R.K. Agent Supervisor...")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self.listen_for_tasks()),
            asyncio.create_task(self.run_autonomous_tasks())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 Agent Supervisor shutting down...")
            for task in tasks:
                task.cancel()

async def main():
    """Main entry point"""
    supervisor = AgentSupervisor()
    await supervisor.start()

if __name__ == "__main__":
    asyncio.run(main())