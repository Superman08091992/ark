"""
A.R.K. Core Backend
FastAPI server orchestrating the Council of Consciousness
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import json
import asyncio
import redis
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import uuid

app = FastAPI(title="A.R.K. Core", description="Autonomous Reactive Kernel API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection for inter-service communication
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Security: Define allowed base directory for file operations
BASE_FILES_DIR = Path("/app/files").resolve()

def validate_file_path(user_path: str) -> Path:
    """
    Validate and sanitize file paths to prevent path traversal attacks.
    
    Args:
        user_path: User-provided file path
        
    Returns:
        Validated absolute Path object
        
    Raises:
        HTTPException: If path is invalid or attempts directory traversal
    """
    if not user_path:
        raise HTTPException(status_code=400, detail="File path cannot be empty")
    
    # Remove any leading/trailing whitespace and path separators
    user_path = user_path.strip().lstrip(os.sep)
    
    # Block obvious traversal attempts
    if ".." in user_path or user_path.startswith("/"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid path: Directory traversal detected"
        )
    
    # Construct the full path and resolve it (eliminates symlinks and relative paths)
    try:
        full_path = (BASE_FILES_DIR / user_path).resolve()
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path: {str(e)}"
        )
    
    # Ensure the resolved path is within the allowed base directory
    if not str(full_path).startswith(str(BASE_FILES_DIR)):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Path outside allowed directory"
        )
    
    return full_path

class ARKDatabase:
    """Database operations for A.R.K."""
    
    def __init__(self):
        self.db_path = "/app/data/ark.db"
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_agents(self):
        """Get all agents with their current status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, essence, status, personality, memory, last_active
            FROM agents ORDER BY name
        ''')
        agents = []
        for row in cursor.fetchall():
            agents.append({
                'id': row[0],
                'name': row[1],
                'essence': row[2],
                'status': row[3],
                'personality': json.loads(row[4]) if row[4] else {},
                'memory': json.loads(row[5]) if row[5] else {},
                'last_active': row[6]
            })
        conn.close()
        return agents
    
    def save_conversation(self, agent_name: str, user_message: str, agent_response: str, tools_used: List[str] = None, files_created: List[str] = None):
        """Save conversation to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (id, agent_name, user_message, agent_response, tools_used, files_created)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            agent_name,
            user_message,
            agent_response,
            json.dumps(tools_used or []),
            json.dumps(files_created or [])
        ))
        conn.commit()
        conn.close()
    
    def get_conversations(self, agent_name: str = None, limit: int = 50):
        """Get recent conversations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if agent_name:
            cursor.execute('''
                SELECT agent_name, user_message, agent_response, timestamp
                FROM conversations WHERE agent_name = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (agent_name, limit))
        else:
            cursor.execute('''
                SELECT agent_name, user_message, agent_response, timestamp
                FROM conversations ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'agent_name': row[0],
                'user_message': row[1],
                'agent_response': row[2],
                'timestamp': row[3]
            })
        conn.close()
        return conversations

# Initialize database connection
db = ARKDatabase()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "awakened", "timestamp": datetime.now().isoformat()}

@app.get("/api/agents")
async def get_agents():
    """Get all agents in the council"""
    try:
        agents = db.get_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{agent_name}")
async def chat_with_agent(agent_name: str, message: dict):
    """Send message to specific agent"""
    user_message = message.get("message", "")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Send message to agent service via Redis
        task_id = str(uuid.uuid4())
        redis_client.rpush('agent_tasks', json.dumps({
            'task_id': task_id,
            'agent_name': agent_name,
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        }))
        
        # Wait for response (simplified - in production, use async queuing)
        response_key = f'response:{task_id}'
        response = None
        timeout = 30  # 30 seconds timeout
        
        for _ in range(timeout * 10):  # Check every 100ms
            response_data = redis_client.get(response_key)
            if response_data:
                response = json.loads(response_data)
                redis_client.delete(response_key)
                break
            await asyncio.sleep(0.1)
        
        if not response:
            raise HTTPException(status_code=408, detail="Agent response timeout")
        
        # Save conversation
        db.save_conversation(
            agent_name, 
            user_message, 
            response.get('response', ''),
            response.get('tools_used', []),
            response.get('files_created', [])
        )
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            'type': 'agent_response',
            'agent_name': agent_name,
            'user_message': user_message,
            'agent_response': response.get('response', ''),
            'tools_used': response.get('tools_used', []),
            'timestamp': datetime.now().isoformat()
        })
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def get_conversations(agent_name: str = None, limit: int = 50):
    """Get conversation history"""
    try:
        conversations = db.get_conversations(agent_name, limit)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files():
    """List files in the A.R.K. file system"""
    try:
        files = []
        files_dir = "/app/files"
        
        if os.path.exists(files_dir):
            for root, dirs, filenames in os.walk(files_dir):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, files_dir)
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'path': relative_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files")
async def create_file(file_data: dict):
    """Create or write file - with path traversal protection"""
    try:
        filepath = file_data.get('path', '')
        content = file_data.get('content', '')
        
        # Validate and sanitize the file path
        full_path = validate_file_path(filepath)
        
        # Create parent directories if they don't exist (within allowed base)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file securely
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"success": True, "path": filepath}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_path:path}")
async def read_file(file_path: str):
    """Read file content - with path traversal protection"""
    try:
        # Validate and sanitize the file path
        full_path = validate_file_path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"content": content, "path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{file_path:path}")
async def delete_file(file_path: str):
    """Delete file - with path traversal protection"""
    try:
        # Validate and sanitize the file path
        full_path = validate_file_path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Can only delete files, not directories")
        
        full_path.unlink()
        return {"success": True, "message": f"File {file_path} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_json()
            # Echo back for now - can add real-time features later
            await websocket.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)