from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Canonical home for ``customer``-schema tables that lived in the old
# ``domains.accounts.models.core`` God-module (A3 / RESOLVER §26 ACC-01).
# ``domains.accounts.models.core`` keeps re-exports so legacy imports resolve.

__all__ = [
    "Address", "Cart", "CartItem", "SystemHealthEvent", "UserSession", "NewsArticle",
    "EntityChatThread", "VideoRoom", "VideoRoomParticipant", "DirectChatRoom",
    "GroupChatMember", "ShiftHandoverSession", "EscalationSLALog",
    "Referral", "ReferralPointEvent",
]


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
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
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="addresses")


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("catalog.products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    selected_size = Column(String(50), default="", nullable=False)
    selected_color = Column(String(50), default="", nullable=False)
    variant_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


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
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    __table_args__ = (Index("ix_user_sessions_user_active", "user_id", "is_active"), {"schema": "customer"})


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (Index("ix_news_articles_published", "published_at"), {"schema": "customer"})

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("comms.news_sources.id"), nullable=True)
    external_id = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    country_code = Column(String(10), nullable=True)
    ai_sentiment = Column(String(20), default="neutral")
    ai_tags = Column(JSON, nullable=True)
    is_published = Column(Boolean, default=True)
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


class VideoRoom(Base):
    __tablename__ = "video_rooms"
    __table_args__ = (
        Index("ix_video_room_status", "status"),
        Index("ix_video_room_created", "created_at"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), unique=True, nullable=False, index=True)
    room_uuid = Column(String(32), unique=True, nullable=True)
    name = Column(String(200), nullable=False)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    created_by = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
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
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    role = Column(String(20), default="participant")
    joined_at = Column(DateTime, default=_utcnow)
    left_at = Column(DateTime, nullable=True)
    room = relationship("VideoRoom", back_populates="participants")
    user = relationship("User")


class DirectChatRoom(Base):
    __tablename__ = "direct_chat_rooms"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(64), unique=True, nullable=False, index=True)
    participant_one = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    participant_two = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    is_masked = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    messages = relationship("DirectChatMessage", back_populates="room", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("participant_one", "participant_two", name="uq_direct_chat_pair"), {"schema": "customer"})


class GroupChatMember(Base):
    __tablename__ = "group_chat_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_group_member"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.group_chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    role = Column(String(20), default="member")
    joined_at = Column(DateTime, default=_utcnow)
    room = relationship("GroupChatRoom", back_populates="members")
    user = relationship("User")


class ShiftHandoverSession(Base):
    __tablename__ = "shift_handover_sessions"
    __table_args__ = (
        Index("ix_handover_outgoing", "outgoing_employee_id"),
        Index("ix_handover_incoming", "incoming_employee_id"),
        Index("ix_handover_status", "status"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    outgoing_employee_id = Column(Integer, ForeignKey("logistics.employees.id"), nullable=False)
    incoming_employee_id = Column(Integer, ForeignKey("logistics.employees.id"), nullable=True)
    shift_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    tasks = relationship("ShiftHandoverTask", back_populates="session", cascade="all, delete-orphan")


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False, unique=True, index=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_given")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referred_by")


class ReferralPointEvent(Base):
    __tablename__ = "referral_point_events"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    points = Column(Integer, nullable=False)
    referred_user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)

    user = relationship("User", foreign_keys=[user_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class EscalationSLALog(Base):
    __tablename__ = "escalation_sla_logs"
    __table_args__ = (
        Index("ix_escalation_message", "message_id"),
        Index("ix_escalation_status", "status"), {"schema": "customer"})
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False)
    message_type = Column(String(30), nullable=False)
    original_recipient_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    escalated_to_user_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    escalated_to_role = Column(String(40), nullable=True)
    priority = Column(String(20), nullable=False)
    elapsed_minutes = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    escalated_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
