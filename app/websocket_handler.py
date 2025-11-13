"""
WebSocket connection handler for WebRTC signaling.
"""
import json
import uuid
import os
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if database is configured
# Support both DATABASE_URL (Railway/Heroku) and individual variables
USE_DATABASE = bool(os.getenv('DATABASE_URL') or (os.getenv('DB_PASSWORD') and os.getenv('DB_NAME')))

if USE_DATABASE:
    try:
        from app.database import get_db
        from app.room_manager_db import RoomManagerDB
        # Will get db session per request
    except Exception:
        USE_DATABASE = False
        from app.room_manager import room_manager
else:
    from app.room_manager import room_manager


class ConnectionManager:
    """Manages WebSocket connections for signaling."""
    
    def __init__(self):
        # Store room_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store WebSocket -> (room_id, user_id) mapping
        self.connection_info: Dict[WebSocket, tuple[str, str]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str) -> str:
        """Connect a WebSocket to a room. Returns the user_id."""
        # Check if room exists
        if USE_DATABASE:
            db = next(get_db())
            try:
                db_manager = RoomManagerDB(db)
                if not db_manager.room_exists(room_id):
                    await websocket.close(code=1008, reason="Room does not exist")
                    raise ValueError("Room does not exist")
            finally:
                db.close()
        else:
            if not room_manager.room_exists(room_id):
                await websocket.close(code=1008, reason="Room does not exist")
                raise ValueError("Room does not exist")
        
        await websocket.accept()
        user_id = str(uuid.uuid4())
        
        # Add connection to room
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        self.connection_info[websocket] = (room_id, user_id)
        
        # Join room in room manager
        if USE_DATABASE:
            db = next(get_db())
            try:
                db_manager = RoomManagerDB(db)
                db_manager.join_room(room_id, user_id)
            finally:
                db.close()
        else:
            room_manager.join_room(room_id, user_id)
        
        # Get existing participants in the room (excluding the new user)
        existing_participants = []
        if room_id in self.active_connections:
            for conn in self.active_connections[room_id]:
                if conn != websocket:
                    conn_room_id, conn_user_id = self.connection_info.get(conn, (None, None))
                    if conn_room_id == room_id:
                        existing_participants.append(conn_user_id)
        
        # Send existing participants to the new user
        if existing_participants:
            await self.send_personal_message({
                "type": "existing-participants",
                "room_id": room_id,
                "participants": existing_participants
            }, websocket)
        
        # Notify other participants about new user
        await self._broadcast_to_others(
            websocket,
            room_id,
            {
                "type": "user-joined",
                "user_id": user_id,
                "room_id": room_id
            }
        )
        
        return user_id
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket not in self.connection_info:
            return
        
        room_id, user_id = self.connection_info[websocket]
        
        # Remove from active connections
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        del self.connection_info[websocket]
        
        if USE_DATABASE:
            db = next(get_db())
            try:
                db_manager = RoomManagerDB(db)
                db_manager.leave_room(room_id, user_id)
            finally:
                db.close()
        else:
            room_manager.leave_room(room_id, user_id)
        
        return room_id, user_id
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude_websocket: WebSocket = None):
        """Broadcast a message to all connections in a room."""
        if room_id not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[room_id]:
            if connection == exclude_websocket:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def _broadcast_to_others(self, sender_websocket: WebSocket, room_id: str, message: dict):
        """Broadcast a message to all other connections in a room (excluding sender)."""
        await self.broadcast_to_room(room_id, message, exclude_websocket=sender_websocket)
    
    async def handle_signaling_message(self, websocket: WebSocket, message: dict):
        """Handle incoming signaling messages (SDP offers/answers, ICE candidates)."""
        if websocket not in self.connection_info:
            await self.send_personal_message({
                "type": "error",
                "message": "Connection not registered"
            }, websocket)
            return
        
        room_id, user_id = self.connection_info[websocket]
        message_type = message.get("type")
        
        # Validate message type
        valid_types = ["offer", "answer", "ice-candidate", "join", "leave", "emoji", "mute-status"]
        if message_type not in valid_types:
            await self.send_personal_message({
                "type": "error",
                "message": f"Invalid message type. Must be one of: {valid_types}"
            }, websocket)
            return
        
        # Add sender info to message
        message["sender_id"] = user_id
        message["room_id"] = room_id
        
        # Broadcast to other participants in the room
        await self._broadcast_to_others(websocket, room_id, message)
    
    def get_connection_info(self, websocket: WebSocket) -> tuple[str, str] | None:
        """Get room_id and user_id for a WebSocket connection."""
        return self.connection_info.get(websocket)


# Global connection manager instance
manager = ConnectionManager()


