"""Comms domain fraud-adjacent models (meeting recordings)."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import relationship

from . import Base

__all__ = ["MeetingRecording"]


class MeetingRecording(Base):
    __tablename__ = "meeting_recordings"

    __table_args__ = (
        CheckConstraint("status_code IN ('recording', 'completed', 'failed', 'processing')", name="chk_meeting_recordings_status_valid"),
        {"schema": "comms"},
    )

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), nullable=False)
    started_by_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False)
    recording_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, default=0)
    status_code = Column(String(20), default="recording")
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    starter = relationship("User")
