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

# Canonical home for ``communication``-schema tables that lived in the old
# ``domains.accounts.models.core`` God-module (A3 / RESOLVER §26 ACC-01).
# ``domains.accounts.models.core`` keeps re-exports so legacy imports resolve.

__all__ = [
    "SupportTicket", "SupportTicketReply", "TicketAttachment", "NewsSource",
    "InternalNotice", "EntityChatMessage", "DirectChatMessage", "GroupChatRoom",
    "GroupChatMessage", "EscalationSLARule",
]


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    subject = Column(String, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default="open")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    replies = relationship("SupportTicketReply", back_populates="ticket")
    attachments = relationship("TicketAttachment", back_populates="ticket")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class SupportTicketReply(Base):
    __tablename__ = "support_ticket_replies"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("comms.support_tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    ticket = relationship("SupportTicket", back_populates="replies")
    attachments = relationship("TicketAttachment", back_populates="ticket_reply")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_reply_id = Column(Integer, ForeignKey("comms.support_ticket_replies.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("comms.support_tickets.id"), nullable=True)
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    ticket_reply = relationship("SupportTicketReply", back_populates="attachments")
    ticket = relationship("SupportTicket", back_populates="attachments")


class NewsSource(Base):
    __tablename__ = "news_sources"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    source_type = Column(String(20), default="rss")
    api_key_required = Column(Boolean, default=False)
    category = Column(String(50), default="general")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class InternalNotice(Base):
    __tablename__ = "internal_notices"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class EntityChatMessage(Base):
    __tablename__ = "entity_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("customer.entity_chat_threads.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    thread = relationship("EntityChatThread", back_populates="messages")
    sender = relationship("User")


class DirectChatMessage(Base):
    __tablename__ = "direct_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("customer.direct_chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
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
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    members = relationship("GroupChatMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("GroupChatMessage", back_populates="room", cascade="all, delete-orphan")


class GroupChatMessage(Base):
    __tablename__ = "group_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.group_chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    room = relationship("GroupChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


class EscalationSLARule(Base):
    __tablename__ = "escalation_sla_rules"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    priority = Column(String(20), nullable=False)
    escalate_after_minutes = Column(Integer, nullable=False)
    escalate_to_role = Column(String(40), nullable=False)
    notify_via = Column(String(100), default="email,sms")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)