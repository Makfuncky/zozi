from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, JSON, Numeric
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "Address", "Cart", "CartItem",
    "AuditLog", "SupportTicket", "SupportTicketReply", "TicketAttachment", "UserBrowsingHistory",
    "CityDistanceMatrix", "ExecutiveNews", "UserSession", "SystemHealthEvent", "CommandCenterView",
    "NewsSource", "NewsArticle", "InternalNotice", "PredictiveSimulation", "AlertEscalationRule",
    "EntityChatThread", "EntityChatMessage",
    "VideoRoom", "VideoRoomParticipant", "VideoRoomRecording",
    "DirectChatRoom", "DirectChatMessage", "GroupChatRoom", "GroupChatMember", "GroupChatMessage",
    "ShiftHandoverSession", "ShiftHandoverTask",
    "EscalationSLARule", "EscalationSLALog",
]


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    label = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, default="US")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    user = relationship("User", back_populates="addresses")


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    user = relationship("User", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    selected_size = Column(String(50), default="", nullable=False)
    selected_color = Column(String(50), default="", nullable=False)
    variant_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    username = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    subject = Column(String, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default="open")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    replies = relationship("SupportTicketReply", back_populates="ticket")
    attachments = relationship("TicketAttachment", back_populates="ticket")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class SupportTicketReply(Base):
    __tablename__ = "support_ticket_replies"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("communication.support_tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    ticket = relationship("SupportTicket", back_populates="replies")
    attachments = relationship("TicketAttachment", back_populates="ticket_reply")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_reply_id = Column(Integer, ForeignKey("communication.support_ticket_replies.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("communication.support_tickets.id"), nullable=True)
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    ticket_reply = relationship("SupportTicketReply", back_populates="attachments")
    ticket = relationship("SupportTicket", back_populates="attachments")


class CityDistanceMatrix(Base):
    __tablename__ = "city_distance_matrix"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    origin_country_code = Column(String(3), nullable=False)
    origin_city_name = Column(String, nullable=False)
    destination_country_code = Column(String(3), nullable=False)
    destination_city_name = Column(String, nullable=False)
    distance_km = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ExecutiveNews(Base):
    __tablename__ = "executive_news"
    __table_args__ = ({"schema": "analytics"},)
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    category = Column(String(50), default="general")
    priority = Column(String(20), default="normal")
    country_code = Column(String(3), nullable=True)
    is_published = Column(Boolean, default=False)
    ai_sentiment = Column(String(20), default="neutral")
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class UserBrowsingHistory(Base):
    __tablename__ = "user_browsing_history"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False, index=True)
    viewed_at = Column(DateTime, default=_utcnow)


class SystemHealthEvent(Base):
    __tablename__ = "system_health_events"
    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(100), nullable=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(12, 4), nullable=False)
    severity = Column(String(20), default="info")
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    __table_args__ = (Index("ix_health_events_metric_time", "metric_name", "created_at"), {"schema": "customer"})


class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    __table_args__ = (Index("ix_user_sessions_user_active", "user_id", "is_active"), {"schema": "customer"})


class CommandCenterView(Base):
    __tablename__ = "command_center_views"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    view_name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class NewsSource(Base):
    __tablename__ = "news_sources"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    source_type = Column(String(20), default="rss")
    api_key_required = Column(Boolean, default=False)
    category = Column(String(50), default="general")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (Index("ix_news_articles_published", "published_at"), {"schema": "customer"})

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("communication.news_sources.id"), nullable=True)
    external_id = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    country_code = Column(String(3), nullable=True)
    ai_sentiment = Column(String(20), default="neutral")
    ai_tags = Column(JSON, nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class InternalNotice(Base):
    __tablename__ = "internal_notices"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class PredictiveSimulation(Base):
    __tablename__ = "predictive_simulations"
    __table_args__ = ({"schema": "ai"},)
    id = Column(Integer, primary_key=True, index=True)
    simulation_type = Column(String(50), nullable=False)
    parameters_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class AlertEscalationRule(Base):
    __tablename__ = "alert_escalation_rules"
    __table_args__ = ({"schema": "security"},)
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    threshold_value = Column(Numeric(15, 2), nullable=True)
    current_tier = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


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
    __table_args__ = (Index("idx_entity_thread", "entity_type", "entity_id"), {"schema": "customer"})


class EntityChatMessage(Base):
    __tablename__ = "entity_chat_messages"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("customer.entity_chat_threads.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    thread = relationship("EntityChatThread", back_populates="messages")
    sender = relationship("User")


class VideoRoom(Base):
    __tablename__ = "video_rooms"
    __table_args__ = (
        Index("ix_video_room_status", "status"),
        Index("ix_video_room_created", "created_at"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), unique=True, nullable=False, index=True)
    room_uuid = Column(String(32), unique=True, nullable=True)
    name = Column(String(200), nullable=False)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
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
        UniqueConstraint("room_id", "user_id", name="uq_video_participant"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("customer.video_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    role = Column(String(20), default="participant")
    joined_at = Column(DateTime, default=_utcnow)
    left_at = Column(DateTime, nullable=True)
    room = relationship("VideoRoom", back_populates="participants")
    user = relationship("User")


class VideoRoomRecording(Base):
    __tablename__ = "video_room_recordings"
    __table_args__ = ({"schema": "media"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("customer.video_rooms.id"), nullable=False)
    started_by = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    recording_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String(20), default="recording")
    started_at = Column(DateTime, default=_utcnow)
    ended_at = Column(DateTime, nullable=True)
    room = relationship("VideoRoom", back_populates="recordings")
    starter = relationship("User", foreign_keys=[started_by])


class DirectChatRoom(Base):
    __tablename__ = "direct_chat_rooms"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(64), unique=True, nullable=False, index=True)
    participant_one = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    participant_two = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    is_masked = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    messages = relationship("DirectChatMessage", back_populates="room", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("participant_one", "participant_two", name="uq_direct_chat_pair"), {"schema": "customer"})


class DirectChatMessage(Base):
    __tablename__ = "direct_chat_messages"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("customer.direct_chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    room = relationship("DirectChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


class GroupChatRoom(Base):
    __tablename__ = "group_chat_rooms"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    members = relationship("GroupChatMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("GroupChatMessage", back_populates="room", cascade="all, delete-orphan")


class GroupChatMember(Base):
    __tablename__ = "group_chat_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_group_member"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("communication.group_chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    role = Column(String(20), default="member")
    joined_at = Column(DateTime, default=_utcnow)
    room = relationship("GroupChatRoom", back_populates="members")
    user = relationship("User")


class GroupChatMessage(Base):
    __tablename__ = "group_chat_messages"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("communication.group_chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    room = relationship("GroupChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


class ShiftHandoverSession(Base):
    __tablename__ = "shift_handover_sessions"
    __table_args__ = (
        Index("ix_handover_outgoing", "outgoing_employee_id"),
        Index("ix_handover_incoming", "incoming_employee_id"),
        Index("ix_handover_status", "status"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    outgoing_employee_id = Column(Integer, ForeignKey("logistics.employees.id"), nullable=False)
    incoming_employee_id = Column(Integer, ForeignKey("logistics.employees.id"), nullable=True)
    shift_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    tasks = relationship("ShiftHandoverTask", back_populates="session", cascade="all, delete-orphan")


class ShiftHandoverTask(Base):
    __tablename__ = "shift_handover_tasks"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("customer.shift_handover_sessions.id"), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="open")
    assigned_to = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    session = relationship("ShiftHandoverSession", back_populates="tasks")


class EscalationSLARule(Base):
    __tablename__ = "escalation_sla_rules"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    priority = Column(String(20), nullable=False)
    escalate_after_minutes = Column(Integer, nullable=False)
    escalate_to_role = Column(String(40), nullable=False)
    notify_via = Column(String(100), default="email,sms")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class EscalationSLALog(Base):
    __tablename__ = "escalation_sla_logs"
    __table_args__ = (
        Index("ix_escalation_message", "message_id"),
        Index("ix_escalation_status", "status"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False)
    message_type = Column(String(30), nullable=False)
    original_recipient_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    escalated_to_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    escalated_to_role = Column(String(40), nullable=True)
    priority = Column(String(20), nullable=False)
    elapsed_minutes = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    escalated_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
