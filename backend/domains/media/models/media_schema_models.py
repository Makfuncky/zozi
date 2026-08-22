from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Canonical home for ``media``-schema tables that lived in the old
# ``domains.accounts.models.core`` / ``onboarding`` God-modules (A3 / RESOLVER §26
# ACC-01). ``domains.accounts.models.core`` / ``onboarding`` keep re-exports so
# legacy imports resolve.

__all__ = ["VideoRoomRecording", "OCRResult"]


class VideoRoomRecording(Base):
    __tablename__ = "video_room_recordings"
    __table_args__ = ({"schema": "media"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("customer.video_rooms.id"), nullable=False)
    started_by = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    recording_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String(20), default="recording")
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    room = relationship("VideoRoom", back_populates="recordings")
    starter = relationship("User", foreign_keys=[started_by])


class OCRResult(Base):
    __tablename__ = "ocr_results"
    __table_args__ = ({"schema": "media"},)
    id = Column(Integer, primary_key=True, index=True)
    document_verification_id = Column(Integer, ForeignKey("security.document_verifications.id"), nullable=False, unique=True)
    extracted_text = Column(Text, nullable=True)
    confidence_score = Column(String, nullable=True)
    fields = Column(JSON, nullable=True)
    processed_at = Column(DateTime, default=_utcnow)
    document_verification = relationship("DocumentVerification", backref="ocr_result", uselist=False)
