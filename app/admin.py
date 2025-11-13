"""
Admin endpoints for viewing database data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import os

router = APIRouter(prefix="/admin", tags=["admin"])

# Check if database is configured
# Try to load from .env file first
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_CONFIGURED = bool(os.getenv('DB_PASSWORD') or (os.getenv('DB_NAME') and os.getenv('DB_NAME') != 'video_conferencing'))

def get_db():
    """Get database session if configured."""
    if not DB_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Please set up PostgreSQL and configure .env file."
        )
    from app.database import get_db as _get_db
    return next(_get_db())


@router.get("/rooms")
async def get_all_rooms(db: Session = Depends(get_db)):
    """Get all rooms from database."""
    if not DB_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Please set up PostgreSQL and configure .env file."
        )
    try:
        result = db.execute(text("""
            SELECT 
                room_id,
                created_at,
                created_by,
                status,
                (SELECT COUNT(*) FROM participants WHERE room_id = rooms.room_id AND status = 'active') as participant_count
            FROM rooms
            ORDER BY created_at DESC
        """))
        
        rooms = []
        for row in result:
            rooms.append({
                "room_id": str(row[0]),
                "created_at": row[1].isoformat() if row[1] else None,
                "created_by": row[2],
                "status": row[3],
                "participant_count": row[4]
            })
        
        return {"rooms": rooms, "total": len(rooms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/rooms/{room_id}")
async def get_room_details(room_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific room."""
    try:
        # Get room info
        room_result = db.execute(text("""
            SELECT room_id, created_at, created_by, status
            FROM rooms
            WHERE room_id = :room_id
        """), {"room_id": room_id})
        
        room = room_result.fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get participants
        participants_result = db.execute(text("""
            SELECT user_id, username, joined_at, left_at, status
            FROM participants
            WHERE room_id = :room_id
            ORDER BY joined_at DESC
        """), {"room_id": room_id})
        
        participants = []
        for p in participants_result:
            participants.append({
                "user_id": str(p[0]),
                "username": p[1],
                "joined_at": p[2].isoformat() if p[2] else None,
                "left_at": p[3].isoformat() if p[3] else None,
                "status": p[4]
            })
        
        return {
            "room_id": str(room[0]),
            "created_at": room[1].isoformat() if room[1] else None,
            "created_by": room[2],
            "status": room[3],
            "participants": participants,
            "participant_count": len(participants)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/participants")
async def get_all_participants(db: Session = Depends(get_db)):
    """Get all participants from database."""
    try:
        result = db.execute(text("""
            SELECT 
                participant_id,
                room_id,
                user_id,
                username,
                joined_at,
                left_at,
                status
            FROM participants
            ORDER BY joined_at DESC
            LIMIT 100
        """))
        
        participants = []
        for row in result:
            participants.append({
                "participant_id": str(row[0]),
                "room_id": str(row[1]),
                "user_id": str(row[2]),
                "username": row[3],
                "joined_at": row[4].isoformat() if row[4] else None,
                "left_at": row[5].isoformat() if row[5] else None,
                "status": row[6]
            })
        
        return {"participants": participants, "total": len(participants)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/sessions")
async def get_active_sessions(db: Session = Depends(get_db)):
    """Get all active WebSocket sessions."""
    try:
        result = db.execute(text("""
            SELECT 
                session_id,
                room_id,
                user_id,
                connected_at,
                disconnected_at,
                status
            FROM sessions
            WHERE status = 'connected'
            ORDER BY connected_at DESC
        """))
        
        sessions = []
        for row in result:
            sessions.append({
                "session_id": str(row[0]),
                "room_id": str(row[1]),
                "user_id": str(row[2]),
                "connected_at": row[3].isoformat() if row[3] else None,
                "disconnected_at": row[4].isoformat() if row[4] else None,
                "status": row[5]
            })
        
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get database statistics."""
    if not DB_CONFIGURED:
        return {
            "message": "Database not configured",
            "active_rooms": 0,
            "ended_rooms": 0,
            "active_participants": 0,
            "left_participants": 0,
            "active_sessions": 0,
            "total_rooms": 0,
            "total_participants": 0
        }
    try:
        result = db.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM rooms WHERE status = 'active') as active_rooms,
                (SELECT COUNT(*) FROM rooms WHERE status = 'ended') as ended_rooms,
                (SELECT COUNT(*) FROM participants WHERE status = 'active') as active_participants,
                (SELECT COUNT(*) FROM participants WHERE status = 'left') as left_participants,
                (SELECT COUNT(*) FROM sessions WHERE status = 'connected') as active_sessions,
                (SELECT COUNT(*) FROM rooms) as total_rooms,
                (SELECT COUNT(*) FROM participants) as total_participants
        """))
        
        stats = result.fetchone()
        
        return {
            "active_rooms": stats[0],
            "ended_rooms": stats[1],
            "active_participants": stats[2],
            "left_participants": stats[3],
            "active_sessions": stats[4],
            "total_rooms": stats[5],
            "total_participants": stats[6]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

