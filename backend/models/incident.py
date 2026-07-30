from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["IncidentWarRoom", "IncidentThread", "IncidentActionItem", "WarRoomTemplate"]


class IncidentWarRoom(Base):
    __tablename__ = "incident_war_rooms"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    severity = Column(String, default="medium")
    status = Column(String, default="active")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=_utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    context_data = Column(JSON, nullable=True)
    threads = relationship("IncidentThread", back_populates="war_room", cascade="all, delete-orphan")
    action_items = relationship("IncidentActionItem", back_populates="war_room", cascade="all, delete-orphan")
    creator = relationship("User")


class IncidentThread(Base):
    __tablename__ = "incident_threads"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    war_room_id = Column(Integer, ForeignKey("incident_war_rooms.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    war_room = relationship("IncidentWarRoom", back_populates="threads")
    participant = relationship("User")


class IncidentActionItem(Base):
    __tablename__ = "incident_action_items"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    war_room_id = Column(Integer, ForeignKey("incident_war_rooms.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    war_room = relationship("IncidentWarRoom", back_populates="action_items")
    assignee = relationship("User")


class WarRoomTemplate(Base):
    __tablename__ = "war_room_templates"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    severity = Column(String, nullable=False)
    auto_assign = Column(Boolean, default=False)
    template_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
