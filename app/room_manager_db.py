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
        except ValueError as e:
            print(f"❌ Invalid room_id format: {room_id}, error: {e}")
            return False
        
        # Check if room exists
        room = self.db.query(Room).filter(Room.room_id == room_uuid).first()
        if not room:
            print(f"❌ Room {room_id} does not exist in database")
            return False
        
        if room.status != 'active':
            print(f"❌ Room {room_id} exists but status is '{room.status}', not 'active'")
            return False
        
        # Check if participant already exists
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError as e:
            print(f"❌ Invalid user_id format: {user_id}, error: {e}")
            return False
        
        existing = self.db.query(Participant).filter(
            Participant.room_id == room_uuid,
            Participant.user_id == user_uuid,
            Participant.status == 'active'
        ).first()
        
        if not existing:
            # Check if there's a participant with 'left' status that we should reactivate
            left_participant = self.db.query(Participant).filter(
                Participant.room_id == room_uuid,
                Participant.user_id == user_uuid,
                Participant.status == 'left'
            ).first()
            
            if left_participant:
                # Reactivate the participant
                left_participant.status = 'active'
                left_participant.left_at = None
                if username:
                    left_participant.username = username
                try:
                    self.db.commit()
                    print(f"✅ Reactivated participant {user_id} in room {room_id}")
                except Exception as e:
                    print(f"❌ Error reactivating participant: {e}")
                    self.db.rollback()
                    return False
            else:
                # Create new participant
                try:
                    participant = Participant(
                        room_id=room_uuid,
                        user_id=user_uuid,
                        username=username,
                        status='active'
                    )
                    self.db.add(participant)
                    self.db.commit()
                    print(f"✅ Added new participant {user_id} to room {room_id}")
                except Exception as e:
                    print(f"❌ Error adding participant: {e}")
                    import traceback
                    traceback.print_exc()
                    self.db.rollback()
                    return False
        else:
            # Participant already exists and is active
            if username and existing.username != username:
                existing.username = username
                try:
                    self.db.commit()
                except Exception as e:
                    print(f"❌ Error updating username: {e}")
                    self.db.rollback()
            print(f"ℹ️ Participant {user_id} already active in room {room_id}")
        
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


