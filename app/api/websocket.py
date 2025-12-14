# app/api/websocket.py - WebSocket endpoints
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import HTMLResponse
import logging
from typing import Optional

from app.core.websocket import WebSocketManager
from app.core.security import verify_websocket_token
from app.models import User, Project
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()
logger = logging.getLogger(__name__)
ws_manager = WebSocketManager()

@router.websocket("/ws/builds/{project_id}")
async def websocket_build_updates(
    websocket: WebSocket,
    project_id: int,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time build updates."""
    try:
        # Verify authentication
        user_id = await verify_websocket_token(token)
        if not user_id:
            await websocket.close(code=1008)
            return
        
        # Verify project access
        stmt = select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            await websocket.close(code=1008)
            return
        
        # Handle WebSocket connection
        await ws_manager.handle_connection(websocket, project_id, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for project {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011)

@router.websocket("/ws/user")
async def websocket_user_updates(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for user-level updates (notifications, etc.)."""
    try:
        # Verify authentication
        user_id = await verify_websocket_token(token)
        if not user_id:
            await websocket.close(code=1008)
            return
        
        # Use project_id=0 for user-level connections
        await ws_manager.handle_connection(websocket, 0, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"User WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"User WebSocket error: {str(e)}")
        await websocket.close(code=1011)

@router.get("/ws/demo")
async def websocket_demo():
    """Demo page for WebSocket testing."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DevDeploy WebSocket Demo</title>
    </head>
    <body>
        <h1>WebSocket Build Updates Demo</h1>
        <div id="messages"></div>
        <script>
            const projectId = 1; // Change this to your project ID
            const token = "YOUR_JWT_TOKEN"; // Replace with actual token
            
            const ws = new WebSocket(`ws://localhost:8000/ws/builds/${projectId}?token=${token}`);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
                document.getElementById('messages').innerHTML += '<p>Connected to WebSocket</p>';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                console.log('Received:', data);
                
                const messages = document.getElementById('messages');
                messages.innerHTML += `<p>${new Date().toISOString()}: ${JSON.stringify(data)}</p>`;
                messages.scrollTop = messages.scrollHeight;
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                document.getElementById('messages').innerHTML += '<p style="color: red;">WebSocket error</p>';
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                document.getElementById('messages').innerHTML += '<p>Disconnected</p>';
            };
            
            // Send ping every 30 seconds to keep connection alive
            setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({type: 'ping'}));
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)