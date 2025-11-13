"""
FastAPI backend for video conferencing application with WebRTC signaling.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

from app.models import RoomCreateResponse, RoomInfo
from app.room_manager import room_manager
from app.websocket_handler import manager
from app.admin import router as admin_router
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if database is configured
# Support both DATABASE_URL (Railway/Heroku) and individual variables
USE_DATABASE = bool(os.getenv('DATABASE_URL') or (os.getenv('DB_PASSWORD') and os.getenv('DB_NAME')))

if USE_DATABASE:
    try:
        from app.database import get_db, engine, Base
        from app.room_manager_db import RoomManagerDB
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database connected - Using PostgreSQL")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("⚠️  Falling back to in-memory storage")
        USE_DATABASE = False
else:
    print("ℹ️  Using in-memory storage (PostgreSQL not configured)")


app = FastAPI(
    title="Video Conferencing Backend",
    description="Backend API for Zoom-like video conferencing with WebRTC signaling",
    version="1.0.0"
)

# Include admin router (only if database is configured)
try:
    app.include_router(admin_router)
except Exception as e:
    print(f"Warning: Admin endpoints not available: {e}")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Video Conferencing Backend API",
        "version": "1.0.0",
        "endpoints": {
            "create_room": "POST /create-room",
            "list_rooms": "GET /rooms",
            "websocket": "WS /ws/{room_id}"
        }
    }


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables (for troubleshooting)."""
    import os
    database_url = os.getenv('DATABASE_URL')
    
    # Mask password in DATABASE_URL for security
    masked_url = None
    if database_url:
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                if len(user_pass) >= 3:  # postgresql://user:pass
                    masked_url = f"{user_pass[0]}://{user_pass[1]}:****@{parts[1]}"
                elif len(user_pass) >= 2:
                    masked_url = f"{user_pass[0]}:****@{parts[1]}"
                else:
                    masked_url = database_url[:50] + "..."
            else:
                masked_url = database_url[:50] + "..."
        else:
            masked_url = database_url[:50] + "..."
    
    return {
        "DATABASE_URL_set": bool(database_url),
        "DATABASE_URL_preview": masked_url,
        "DB_HOST": os.getenv('DB_HOST'),
        "DB_NAME": os.getenv('DB_NAME'),
        "DB_USER": os.getenv('DB_USER'),
        "DB_PASSWORD_set": bool(os.getenv('DB_PASSWORD')),
        "USE_DATABASE": USE_DATABASE,
        "database_configured": USE_DATABASE
    }


@app.post("/create-room", response_model=RoomCreateResponse)
async def create_room():
    """
    Create a new video conference room.
    Returns a room ID and join link.
    """
    if USE_DATABASE:
        db = next(get_db())
        try:
            db_manager = RoomManagerDB(db)
            room_id = db_manager.create_room()
            join_link = f"/room/{room_id}"
            return RoomCreateResponse(
                room_id=room_id,
                join_link=join_link,
                message=f"Room {room_id} created successfully"
            )
        finally:
            db.close()
    else:
        room_id = room_manager.create_room()
        join_link = f"/room/{room_id}"
        return RoomCreateResponse(
            room_id=room_id,
            join_link=join_link,
            message=f"Room {room_id} created successfully"
        )


@app.get("/rooms", response_model=List[RoomInfo])
async def list_rooms():
    """
    List all active rooms with participant counts.
    """
    if USE_DATABASE:
        db = next(get_db())
        try:
            db_manager = RoomManagerDB(db)
            return db_manager.get_all_rooms()
        finally:
            db.close()
    else:
        return room_manager.get_all_rooms()


@app.get("/rooms/{room_id}")
async def get_room_info(room_id: str):
    """
    Get information about a specific room.
    """
    if USE_DATABASE:
        db = next(get_db())
        try:
            db_manager = RoomManagerDB(db)
            room_info = db_manager.get_room_info(room_id)
            if not room_info:
                raise HTTPException(status_code=404, detail="Room not found")
            return room_info
        finally:
            db.close()
    else:
        if not room_manager.room_exists(room_id):
            raise HTTPException(status_code=404, detail="Room not found")
        
        participants = room_manager.get_room_participants(room_id)
        return {
            "room_id": room_id,
            "participant_count": len(participants),
            "participants": list(participants),
            "exists": True
        }


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for WebRTC signaling.
    
    Handles:
    - Connection establishment
    - SDP offer/answer exchange
    - ICE candidate exchange
    - User join/leave notifications
    
    Message format:
    {
        "type": "offer" | "answer" | "ice-candidate" | "join" | "leave",
        "room_id": "room-uuid",
        "user_id": "user-uuid" (optional, auto-assigned),
        "data": { ... } (SDP or ICE candidate data)
    }
    """
    user_id = None
    try:
        # Connect the WebSocket
        user_id = await manager.connect(websocket, room_id)
        
        # Send connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "user_id": user_id,
            "room_id": room_id,
            "message": "Successfully connected to room"
        }, websocket)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Handle signaling message
                await manager.handle_signaling_message(websocket, data)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error handling message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }, websocket)
    
    except ValueError as e:
        # Room doesn't exist
        print(f"Connection error: {e}")
        if websocket.client_state.name == "CONNECTED":
            await websocket.close(code=1008, reason=str(e))
    
    except WebSocketDisconnect:
        # Handle disconnection
        pass
    
    finally:
        # Clean up on disconnect
        if user_id:
            room_id, user_id = manager.disconnect(websocket)
            # Notify other participants
            await manager.broadcast_to_room(room_id, {
                "type": "user-left",
                "user_id": user_id,
                "room_id": room_id
            })


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


