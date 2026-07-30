from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["Notification", "Announcement", "FAQ", "HelpCategory", "TicketMessage",
           "ProxyChannel", "ProxySession", "ProxyMessage", "ProxyCallLog",
           "EmployeeCommunicationThread", "ExternalContactMasking", "CommunicationAuditTrail",
           "InternalChannel", "InternalChannelMember", "InternalMessage"]


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_user_read", "user_id", "is_read"), {"schema": "communication"})
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String, default="in_app")
    priority = Column(String, default="medium")
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    link = Column(String, nullable=True)
    template = Column(String, nullable=True)
    variables = Column(JSON, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String, default="delivered")
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User")


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class FAQ(Base):
    __tablename__ = "faqs"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class HelpCategory(Base):
    __tablename__ = "help_categories"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)


class ProxyChannel(Base):
    __tablename__ = "proxy_channels"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    proxy_phone = Column(String, unique=True, nullable=False, index=True)
    proxy_email = Column(String, unique=True, nullable=False, index=True)
    participants = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    __table_args__ = (
        Index("idx_proxy_entity", "entity_type", "entity_id"), {"schema": "communication"})


class ProxySession(Base):
    __tablename__ = "proxy_sessions"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("proxy_channels.id"), nullable=False)
    participant_one_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    participant_two_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_encrypted = Column(Boolean, default=True)
    session_metadata = Column(JSON, nullable=True)
    channel = relationship("ProxyChannel", back_populates="sessions")
    participant_one = relationship("User", foreign_keys=[participant_one_id])
    participant_two = relationship("User", foreign_keys=[participant_two_id])


class ProxyMessage(Base):
    __tablename__ = "proxy_messages"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("proxy_sessions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(String, default="text")
    content = Column(Text, nullable=False)
    is_masked = Column(Boolean, default=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    session = relationship("ProxySession", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])


class ProxyCallLog(Base):
    __tablename__ = "proxy_call_logs"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("proxy_channels.id"), nullable=False)
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    callee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    direction = Column(String, nullable=False)
    duration_seconds = Column(Integer, default=0)
    call_recording_url = Column(String, nullable=True)
    is_recorded = Column(Boolean, default=False)
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    channel = relationship("ProxyChannel", back_populates="call_logs")
    caller = relationship("User", foreign_keys=[caller_id])
    callee = relationship("User", foreign_keys=[callee_id])


ProxyChannel.sessions = relationship("ProxySession", back_populates="channel", cascade="all, delete-orphan")
ProxyChannel.call_logs = relationship("ProxyCallLog", back_populates="channel", cascade="all, delete-orphan")
ProxySession.messages = relationship("ProxyMessage", back_populates="session", cascade="all, delete-orphan")


class EmployeeCommunicationThread(Base):
    __tablename__ = "employee_communication_threads"
    __table_args__ = (
        Index("ix_emp_comm_entity", "entity_type", "entity_id"), {"schema": "communication"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    participants = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship("CountryConfig")


class ExternalContactMasking(Base):
    __tablename__ = "external_contact_masking"
    __table_args__ = (
        UniqueConstraint("user_id", "external_contact_type", "external_contact_id", name="uq_masking_contact"),
        Index("ix_masking_user", "user_id"), {"schema": "communication"})
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    external_contact_type = Column(String(50), nullable=False)
    external_contact_id = Column(Integer, nullable=False)
    masked_phone = Column(String(20), nullable=True)
    masked_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    user = relationship("User")


class CommunicationAuditTrail(Base):
    __tablename__ = "communication_audit_trail"
    __table_args__ = (
        Index("ix_comm_entity", "entity_type", "entity_id"),
        Index("ix_comm_user", "user_id", "created_at"), {"schema": "communication"})
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    content_preview = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    
    user = relationship("User")


class InternalChannel(Base):
    __tablename__ = "internal_channels"
    __table_args__ = (
        Index("ix_internal_channel_entity", "entity_type", "entity_id"), {"schema": "communication"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship("CountryConfig")
    members = relationship("InternalChannelMember", back_populates="channel", cascade="all, delete-orphan")
    messages = relationship("InternalMessage", back_populates="channel", cascade="all, delete-orphan")


class InternalChannelMember(Base):
    __tablename__ = "internal_channel_members"
    __table_args__ = (
        UniqueConstraint("channel_id", "user_id", name="uq_channel_member"), {"schema": "communication"})
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("internal_channels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")
    joined_at = Column(DateTime, default=_utcnow)
    
    channel = relationship("InternalChannel", back_populates="members")
    user = relationship("User")


class InternalMessage(Base):
    __tablename__ = "internal_messages"
    __table_args__ = (
        Index("ix_internal_msg_channel", "channel_id"),
        Index("ix_internal_msg_user", "user_id"), {"schema": "communication"})
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("internal_channels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    is_masked = Column(Boolean, default=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    
    channel = relationship("InternalChannel", back_populates="messages")
    user = relationship("User")
