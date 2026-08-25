from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class EntityChatThread(Base):
    __tablename__ = "entity_chat_threads"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    messages = relationship("EntityChatMessage", back_populates="thread", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_entity_thread", "entity_type", "entity_id"), {"schema": "comms"})


class VideoRoom(Base):
    __tablename__ = "video_rooms"
    __table_args__ = (
        Index("ix_video_room_status", "status"),
        Index("ix_video_room_created", "created_at"), {"schema": "comms"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), unique=True, nullable=False, index=True)
    room_uuid = Column(String(32), unique=True, nullable=True)
    name = Column(String(200), nullable=False)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=True)
    created_by = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True)
    is_boardroom = Column(Boolean, default=False)
    status = Column(String(20), default="waiting")
    max_participants = Column(Integer, default=100)
    recording_enabled = Column(Boolean, default=False)
    watermark_enabled = Column(Boolean, default=True)
    transcription_enabled = Column(Boolean, default=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    participants = relationship("VideoRoomParticipant", back_populates="room", cascade="all, delete-orphan")
    recordings = relationship("VideoRoomRecording", back_populates="room", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class VideoRoomParticipant(Base):
    __tablename__ = "video_room_participants"
    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_video_participant"), {"schema": "comms"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.video_rooms.id", ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    role = Column(String(20), default="participant")
    joined_at = Column(DateTime, default=_utcnow)
    left_at = Column(DateTime, nullable=True)
    room = relationship("VideoRoom", back_populates="participants")
    user = relationship("User")


class DirectChatRoom(Base):
    __tablename__ = "direct_chat_rooms"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(64), unique=True, nullable=False, index=True)
    participant_one = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    participant_two = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=True)
    is_masked = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    messages = relationship("DirectChatMessage", back_populates="room", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("participant_one", "participant_two", name="uq_direct_chat_pair"), {"schema": "comms"})


class GroupChatMember(Base):
    __tablename__ = "group_chat_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_group_member"), {"schema": "comms"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.group_chat_rooms.id", ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    role = Column(String(20), default="member")
    joined_at = Column(DateTime, default=_utcnow)
    room = relationship("GroupChatRoom", back_populates="members")
    user = relationship("User")


class EscalationSLALog(Base):
    __tablename__ = "escalation_sla_logs"
    __table_args__ = (
        Index("ix_escalation_message", "message_id"),
        Index("ix_escalation_status", "status"), {"schema": "comms"})
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False)
    message_type = Column(String(30), nullable=False)
    original_recipient_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True)
    escalated_to_user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True)
    escalated_to_role = Column(String(40), nullable=True)
    priority = Column(String(20), nullable=False)
    elapsed_minutes = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    escalated_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class EntityChatMessage(Base):
    __tablename__ = "entity_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("comms.entity_chat_threads.id", ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    thread = relationship("EntityChatThread", back_populates="messages")
    sender = relationship("User")


class VideoRoomRecording(Base):
    __tablename__ = "video_room_recordings"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.video_rooms.id", ondelete='CASCADE'), nullable=False)
    started_by = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    recording_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String(20), default="recording")
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    room = relationship("VideoRoom", back_populates="recordings")
    starter = relationship("User", foreign_keys=[started_by])


class DirectChatMessage(Base):
    __tablename__ = "direct_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.direct_chat_rooms.id", ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    room = relationship("DirectChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


class GroupChatRoom(Base):
    __tablename__ = "group_chat_rooms"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    members = relationship("GroupChatMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("GroupChatMessage", back_populates="room", cascade="all, delete-orphan")


class GroupChatMessage(Base):
    __tablename__ = "group_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.group_chat_rooms.id", ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    room = relationship("GroupChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


__all__ = [
    "EntityChatThread",
    "VideoRoom",
    "VideoRoomParticipant",
    "DirectChatRoom",
    "GroupChatMember",
    "EscalationSLALog",
    "EntityChatMessage",
    "VideoRoomRecording",
    "DirectChatMessage",
    "GroupChatRoom",
    "GroupChatMessage",
]
