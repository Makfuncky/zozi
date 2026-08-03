from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow
from ..mixins import TenantMixin

__all__ = ["Notification", "Announcement", "FAQ", "HelpCategory", "TicketMessage",
           "ProxyChannel", "ProxySession", "ProxyMessage", "ProxyCallLog",
           "EmployeeCommunicationThread", "ExternalContactMasking", "CommunicationAuditTrail",
           "InternalChannel", "InternalChannelMember", "InternalMessage",
           "ChatAttachment", "InternalEmail", "EmailFolder"]

class Notification(Base, TenantMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_user_read", "user_id", "is_read"), {"schema": "communication"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
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

class TicketMessage(Base, TenantMixin):
    __tablename__ = "ticket_messages"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("communication.support_tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

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

class FAQ(Base, TenantMixin):
    __tablename__ = "faqs"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=True)

    created_at = Column(DateTime, default=_utcnow)

class HelpCategory(Base):
    __tablename__ = "help_categories"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_utcnow)

class ProxyChannel(Base):
    __tablename__ = "proxy_channels"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    proxy_phone = Column(String, unique=True, nullable=False, index=True)
    proxy_email = Column(String, unique=True, nullable=False, index=True)
    participants = Column(JSON, nullable=True)

    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    __table_args__ = (
        Index("idx_proxy_entity", "entity_type", "entity_id"), {"schema": "communication"})
    sessions = relationship("ProxySession", back_populates="channel")
    call_logs = relationship("ProxyCallLog", back_populates="channel")

class ProxySession(Base):
    __tablename__ = "proxy_sessions"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("communication.proxy_channels.id"), nullable=False)
    participant_one_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    participant_two_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_encrypted = Column(Boolean, default=True)
    session_metadata = Column(JSON, nullable=True)
    channel = relationship("ProxyChannel", back_populates="sessions")
    participant_one = relationship("User", foreign_keys=[participant_one_id])
    participant_two = relationship("User", foreign_keys=[participant_two_id])
    messages = relationship("ProxyMessage", back_populates="session")

class ProxyMessage(Base):
    __tablename__ = "proxy_messages"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("communication.proxy_sessions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
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
    channel_id = Column(Integer, ForeignKey("communication.proxy_channels.id"), nullable=False)
    caller_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    callee_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
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

class EmployeeCommunicationThread(Base, TenantMixin):
    __tablename__ = "employee_communication_threads"
    __table_args__ = (
        Index("ix_emp_comm_entity", "entity_type", "entity_id"), {"schema": "communication"})

    id = Column(Integer, primary_key=True, index=True)

    entity_id = Column(Integer, nullable=False)

    entity_type = Column(String(50), nullable=False)
    participants = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)

    country = relationship("CountryConfig")

class ExternalContactMasking(Base):
    __tablename__ = "external_contact_masking"
    __table_args__ = (
        UniqueConstraint("user_id", "external_contact_type", "external_contact_id", name="uq_masking_contact"),
        Index("ix_masking_user", "user_id"), {"schema": "communication"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    external_contact_type = Column(String(50), nullable=False)
    external_contact_id = Column(Integer, nullable=False)
    masked_phone = Column(String(20), nullable=True)
    masked_email = Column(String(255), nullable=True)

    user = relationship("User")

class CommunicationAuditTrail(Base):
    __tablename__ = "communication_audit_trail"
    __table_args__ = (
        Index("ix_comm_entity", "entity_type", "entity_id"),
        Index("ix_comm_user", "user_id", "created_at"), {"schema": "communication"})

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    content_preview = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")

class InternalChannel(Base, TenantMixin):
    __tablename__ = "internal_channels"
    __table_args__ = (
        Index("ix_internal_channel_entity", "entity_type", "entity_id"), {"schema": "communication"})

    id = Column(Integer, primary_key=True, index=True)

    entity_type = Column(String(50), nullable=False)

    entity_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    channel_id = Column(String(64), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    allowed_roles = Column(JSON, nullable=True)

    country = relationship("CountryConfig")
    members = relationship("InternalChannelMember", back_populates="channel", cascade="all, delete-orphan")
    messages = relationship("InternalMessage", back_populates="channel", cascade="all, delete-orphan")

class InternalChannelMember(Base):
    __tablename__ = "internal_channel_members"
    __table_args__ = (
        UniqueConstraint("channel_id", "user_id", name="uq_channel_member"), {"schema": "communication"})

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("communication.internal_channels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
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
    channel_id = Column(Integer, ForeignKey("communication.internal_channels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    is_masked = Column(Boolean, default=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    channel = relationship("InternalChannel", back_populates="messages")
    user = relationship("User")

class ChatReadReceipt(Base):
    __tablename__ = "chat_read_receipts"
    __table_args__ = (
        UniqueConstraint("message_id", "message_type", "employee_id", name="uq_chat_read_receipt"),
        Index("ix_chat_read_receipts_employee", "employee_id"), {"schema": "communication"})

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False, index=True)
    message_type = Column(String(20), nullable=False, default="direct")
    employee_id = Column(Integer, nullable=False)
    read_at = Column(DateTime, default=_utcnow)

class ChatAttachment(Base):
    __tablename__ = "chat_attachments"
    __table_args__ = ({"schema": "communication"},)

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False, index=True)
    message_type = Column(String(20), nullable=False, default="direct")
    attachment_type = Column(String(20), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    waveform_json = Column(Text, nullable=True)
    is_processed = Column(Boolean, default=False)

class InternalEmail(Base, TenantMixin):
    __tablename__ = "internal_emails"
    __table_args__ = (
        Index("ix_internal_emails_thread_id", "thread_id"),
        Index("ix_internal_emails_sender_id", "sender_id"),
        Index("ix_internal_emails_folder_id", "folder_id"),
        ({"schema": "communication"}),
    )

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    recipients = Column(Text, nullable=True)
    thread_id = Column(String(64), nullable=True)
    is_external = Column(Boolean, default=False)
    external_message_id = Column(String(200), nullable=True)

    in_reply_to = Column(Integer, ForeignKey("communication.internal_emails.id"), nullable=True, index=True)
    folder_id = Column(Integer, ForeignKey("communication.email_folders.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    replies = relationship("InternalEmail", remote_side=[id], backref="parent")
    folder = relationship("EmailFolder", backref="emails")

class EmailFolder(Base):
    __tablename__ = "email_folders"
    __table_args__ = ({"schema": "communication"},)

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("logistics.employees.id"), nullable=False)
    name = Column(String(50), nullable=False)
    folder_type = Column(String(20), default="inbox")
    sort_order = Column(Integer, default=0)
    is_system = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

