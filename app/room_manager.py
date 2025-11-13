"""
Room management logic for handling video conference rooms.
"""
import uuid
from datetime import datetime
from typing import Dict, Set, Optional
from app.models import RoomInfo


class RoomManager:
    """Manages video conference rooms and their participants."""
    
    def __init__(self):
        # Store room_id -> set of user_ids
        self.rooms: Dict[str, Set[str]] = {}
        # Store room creation timestamps
        self.room_timestamps: Dict[str, datetime] = {}
    
    def create_room(self) -> str:
        """Create a new room and return its ID."""
        room_id = str(uuid.uuid4())
        self.rooms[room_id] = set()
        self.room_timestamps[room_id] = datetime.now()
        return room_id
    
    def join_room(self, room_id: str, user_id: str) -> bool:
        """Add a user to a room. Returns True if successful, False if room doesn't exist."""
        if room_id not in self.rooms:
            return False
        self.rooms[room_id].add(user_id)
        return True
    
    def leave_room(self, room_id: str, user_id: str):
        """Remove a user from a room."""
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            # Clean up empty rooms
            if not self.rooms[room_id]:
                self._remove_room(room_id)
    
    def get_room_participants(self, room_id: str) -> Set[str]:
        """Get all participants in a room."""
        return self.rooms.get(room_id, set())
    
    def room_exists(self, room_id: str) -> bool:
        """Check if a room exists."""
        return room_id in self.rooms
    
    def get_all_rooms(self) -> list[RoomInfo]:
        """Get information about all active rooms."""
        return [
            RoomInfo(
                room_id=room_id,
                participant_count=len(participants),
                created_at=self.room_timestamps[room_id].isoformat()
            )
            for room_id, participants in self.rooms.items()
        ]
    
    def _remove_room(self, room_id: str):
        """Remove a room from the system."""
        if room_id in self.rooms:
            del self.rooms[room_id]
        if room_id in self.room_timestamps:
            del self.room_timestamps[room_id]


# Global room manager instance
room_manager = RoomManager()


