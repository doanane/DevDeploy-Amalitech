# app/core/websocket.py - Complete WebSocket manager
from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Dict, List, Set, Any
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # project_id -> list of connections
        self.user_connections: Dict[int, Set[WebSocket]] = {}  # user_id -> set of connections
    
    async def connect(self, websocket: WebSocket, project_id: int, user_id: int):
        """Accept WebSocket connection and store it."""
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected for project {project_id}, user {user_id}")
    
    def disconnect(self, websocket: WebSocket, project_id: int, user_id: int):
        """Remove WebSocket connection."""
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected for project {project_id}, user {user_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to a specific WebSocket connection."""
        await websocket.send_text(message)
    
    async def broadcast_to_project(self, project_id: int, message: Any):
        """Broadcast message to all connections for a project."""
        if project_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {str(e)}")
                disconnected.append(connection)
        
        # Clean up disconnected sockets
        for connection in disconnected:
            self.active_connections[project_id].remove(connection)
    
    async def broadcast_to_user(self, user_id: int, message: Any):
        """Broadcast message to all connections for a user."""
        if user_id not in self.user_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to user WebSocket: {str(e)}")
                disconnected.append(connection)
        
        # Clean up
        for connection in disconnected:
            self.user_connections[user_id].discard(connection)
    
    async def broadcast_to_all(self, message: Any):
        """Broadcast message to all connections."""
        message_json = json.dumps(message)
        all_connections = []
        
        # Collect all connections
        for connections in self.active_connections.values():
            all_connections.extend(connections)
        
        # Remove duplicates (connections might be in multiple projects)
        unique_connections = list(set(all_connections))
        
        disconnected = []
        for connection in unique_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {str(e)}")
                disconnected.append(connection)
        
        # Clean up (this is simplified - in real implementation, you'd need to find and remove from all projects)
        for connection in disconnected:
            for project_id, connections in list(self.active_connections.items()):
                if connection in connections:
                    connections.remove(connection)
            if not connections:
                del self.active_connections[project_id]

class WebSocketManager:
    """Singleton WebSocket manager."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.manager = ConnectionManager()
        return cls._instance
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        project_id: int,
        user_id: int
    ):
        """Handle WebSocket connection lifecycle."""
        await self.manager.connect(websocket, project_id, user_id)
        
        try:
            while True:
                # Keep connection alive, handle incoming messages if needed
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    # Handle incoming messages (e.g., ping, subscribe to specific events)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong", 
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                except json.JSONDecodeError:
                    pass
                    
        except WebSocketDisconnect:
            self.manager.disconnect(websocket, project_id, user_id)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            self.manager.disconnect(websocket, project_id, user_id)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    
    async def broadcast_to_project(self, project_id: int, message: Any):
        """Broadcast message to project."""
        await self.manager.broadcast_to_project(project_id, message)
    
    async def broadcast_to_user(self, user_id: int, message: Any):
        """Broadcast message to user."""
        await self.manager.broadcast_to_user(user_id, message)
    
    async def broadcast_to_all(self, message: Any):
        """Broadcast message to all connections."""
        await self.manager.broadcast_to_all(message)

# Standalone function for easy importing
async def broadcast_build_update(build_id: int, status: str, data: dict = None):
    """
    Broadcast build update to all connected clients.
    This is a standalone async function that can be imported.
    """
    ws_manager = WebSocketManager()
    message = {
        "type": "build_update",
        "build_id": build_id,
        "status": status,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # In a real implementation, you would:
    # 1. Get the project_id from the build
    # 2. Broadcast to that specific project
    # For now, broadcast to all connections
    await ws_manager.broadcast_to_all(message)
    
    logger.info(f"Broadcast build update: {build_id} - {status}")
    return True