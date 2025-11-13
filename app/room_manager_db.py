"""
Database-backed room management for PostgreSQL.
"""
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, List
from sqlalchemy.orm import Session
from app.database import get_db, Room, Participant, Session as DBSession
from app.models import RoomInfo


class RoomManagerDB:
    """Manages video conference rooms using PostgreSQL database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_room(self, created_by: Optional[str] = None) -> str:
        """Create a new room and return its ID."""
        room = Room(
            room_id=uuid.uuid4(),
            created_by=created_by,
            status='active'
        )
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return str(room.room_id)
    
    def join_room(self, room_id: str, user_id: str, username: Optional[str] = None) -> bool:
        """Add a user to a room. Returns True if successful, False if room doesn't exist."""
        try:
            room_uuid = uuid.UUID(room_id)
        except ValueError:
            return False
        
        # Check if room exists
        room = self.db.query(Room).filter(Room.room_id == room_uuid).first()
        if not room or room.status != 'active':
            return False
        
        # Check if participant already exists
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        existing = self.db.query(Participant).filter(
            Participant.room_id == room_uuid,
            Participant.user_id == user_uuid,
            Participant.status == 'active'
        ).first()
        
        if not existing:
            participant = Participant(
                room_id=room_uuid,
                user_id=user_uuid,
                username=username,
                status='active'
            )
            self.db.add(participant)
            self.db.commit()
        
        return True
    
    def leave_room(self, room_id: str, user_id: str):
        """Remove a user from a room."""
        try:
            room_uuid = uuid.UUID(room_id)
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return
        
        # Mark participant as left
        participant = self.db.query(Participant).filter(
            Participant.room_id == room_uuid,
            Participant.user_id == user_uuid,
            Participant.status == 'active'
        ).first()
        
        if participant:
            participant.status = 'left'
            participant.left_at = datetime.utcnow()
            self.db.commit()
        
        # Check if room is empty and mark as ended if needed
        active_count = self.db.query(Participant).filter(
            Participant.room_id == room_uuid,
            Participant.status == 'active'
        ).count()
        
        if active_count == 0:
            room = self.db.query(Room).filter(Room.room_id == room_uuid).first()
            if room:
                room.status = 'ended'
                self.db.commit()
    
    def get_room_participants(self, room_id: str) -> Set[str]:
        """Get all active participants in a room."""
        try:
            room_uuid = uuid.UUID(room_id)
        except ValueError:
            return set()
        
        participants = self.db.query(Participant).filter(
            Participant.room_id == room_uuid,
            Participant.status == 'active'
        ).all()
        
        return {str(p.user_id) for p in participants}
    
    def room_exists(self, room_id: str) -> bool:
        """Check if a room exists and is active."""
        try:
            room_uuid = uuid.UUID(room_id)
        except ValueError:
            return False
        
        room = self.db.query(Room).filter(
            Room.room_id == room_uuid,
            Room.status == 'active'
        ).first()
        
        return room is not None
    
    def get_all_rooms(self) -> List[RoomInfo]:
        """Get information about all active rooms."""
        rooms = self.db.query(Room).filter(Room.status == 'active').all()
        
        result = []
        for room in rooms:
            participant_count = self.db.query(Participant).filter(
                Participant.room_id == room.room_id,
                Participant.status == 'active'
            ).count()
            
            result.append(RoomInfo(
                room_id=str(room.room_id),
                participant_count=participant_count,
                created_at=room.created_at.isoformat() if room.created_at else datetime.utcnow().isoformat()
            ))
        
        return result
    
    def get_room_info(self, room_id: str) -> Optional[dict]:
        """Get detailed information about a specific room."""
        try:
            room_uuid = uuid.UUID(room_id)
        except ValueError:
            return None
        
        room = self.db.query(Room).filter(Room.room_id == room_uuid).first()
        if not room:
            return None
        
        participants = self.db.query(Participant).filter(
            Participant.room_id == room_uuid,
            Participant.status == 'active'
        ).all()
        
        return {
            'room_id': str(room.room_id),
            'participant_count': len(participants),
            'participants': [str(p.user_id) for p in participants],
            'created_at': room.created_at.isoformat() if room.created_at else None,
            'status': room.status,
            'exists': True
        }


