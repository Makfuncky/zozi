from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON, func
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = ["IncidentWarRoom", "IncidentThread", "IncidentActionItem", "WarRoomTemplate"]


class IncidentWarRoom(Base):
    __tablename__ = "incident_war_rooms"
    __table_args__ = {"schema": "comms"}
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    severity = Column(String(50), default="medium")
    status = Column(String(50), default="active")
    created_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    context_data = Column(JSON, nullable=True)
    threads = relationship("IncidentThread", back_populates="war_room", cascade="all, delete-orphan")
    action_items = relationship("IncidentActionItem", back_populates="war_room", cascade="all, delete-orphan")
    creator = relationship("User", backref="incident_war_rooms")
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class IncidentThread(Base):
    __tablename__ = "incident_threads"
    __table_args__ = {"schema": "comms"}
    id = Column(Integer, primary_key=True, index=True)
    war_room_id = Column(Integer, ForeignKey("comms.incident_war_rooms.id", ondelete="SET NULL"), nullable=False)
    participant_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    war_room = relationship("IncidentWarRoom", back_populates="threads")
    participant = relationship("User")


class IncidentActionItem(Base):
    __tablename__ = "incident_action_items"
    __table_args__ = {"schema": "comms"}
    id = Column(Integer, primary_key=True, index=True)
    war_room_id = Column(Integer, ForeignKey("comms.incident_war_rooms.id", ondelete="SET NULL"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    priority = Column(String(50), default="medium")
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    war_room = relationship("IncidentWarRoom", back_populates="action_items")
    assignee = relationship("User")


class WarRoomTemplate(Base):
    __tablename__ = "war_room_templates"
    __table_args__ = {"schema": "comms"}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    auto_assign = Column(Boolean, default=False)
    template_data = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
