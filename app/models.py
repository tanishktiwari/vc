"""
Data models for the video conferencing application.
"""
from typing import Optional
from pydantic import BaseModel


class RoomCreateResponse(BaseModel):
    """Response model for room creation."""
    room_id: str
    join_link: str
    message: str


class RoomInfo(BaseModel):
    """Information about a room."""
    room_id: str
    participant_count: int
    created_at: str


class SignalingMessage(BaseModel):
    """WebSocket signaling message model."""
    type: str  # 'offer', 'answer', 'ice-candidate', 'join', 'leave'
    room_id: str
    user_id: Optional[str] = None
    data: Optional[dict] = None  # SDP or ICE candidate data


