"""Governance domain models.

This module provides:
1. Governance-specific models (defined inline)
2. Re-export shims for models whose canonical home is another domain
   (Law 3 compliance: cross-domain model access via re-export shim)

Duplicate table definitions have been converted to lazy re-export shims
to prevent SQLAlchemy registry conflicts (InvalidRequestError).
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index, Numeric
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = [
    # Governance-specific models (defined inline)
    "UserBrowsingHistory", "SystemHealthEvent", "UserSession",
    # Re-export shims (canonical home in another domain)
    "Address", "Cart", "CartItem",  # canonical: accounts
    "AuditLog", "CommandCenterView",  # canonical: audit
    "SupportTicket", "SupportTicketReply", "TicketAttachment",  # canonical: comms
    "ExecutiveNews", "PredictiveSimulation",  # canonical: analytics
    "NewsSource", "InternalNotice", "EscalationSLARule",  # canonical: comms
    "AlertEscalationRule",  # canonical: security
    "CityDistanceMatrix",  # canonical: logistics
    "NewsArticle",  # canonical: comms
    # Chat models (canonical: comms)
    "DirectChatMessage", "DirectChatRoom", "EntityChatMessage", "EntityChatThread",
    "EscalationSLALog", "GroupChatMember", "GroupChatMessage", "GroupChatRoom",
    "VideoRoom", "VideoRoomParticipant", "VideoRoomRecording",
    # HR models (canonical: hr)
    "ShiftHandoverSession", "ShiftHandoverTask",
]


# ──────────────────────────────────────────────
# Governance-specific models (defined inline)
# These are the ONLY models that should be defined inline in this file.
# All other models should be imported via ports.py from their canonical domain.
# ──────────────────────────────────────────────

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
    country_code = Column(String(10), nullable=True, index=True)
    __table_args__ = (Index("ix_user_sessions_user_active", "user_id", "is_active"), {"schema": "customer"})


# ──────────────────────────────────────────────
# Re-export shims (lazy imports to avoid circular imports and InvalidRequestError)
# These models are defined in their canonical domain and imported lazily.
# ──────────────────────────────────────────────

_CANONICAL_EXPORTS = {
    # accounts domain
    "Address": ("domains.accounts.models.core", "Address"),
    "Cart": ("domains.accounts.models.core", "Cart"),
    "CartItem": ("domains.accounts.models.core", "CartItem"),
    # audit domain
    "AuditLog": ("domains.audit.models.audit_schema_models", "AuditLog"),
    "CommandCenterView": ("domains.audit.models.audit_schema_models", "CommandCenterView"),
    # comms domain
    "SupportTicket": ("domains.comms.models.communication_schema_models", "SupportTicket"),
    "SupportTicketReply": ("domains.comms.models.communication_schema_models", "SupportTicketReply"),
    "TicketAttachment": ("domains.comms.models.communication_schema_models", "TicketAttachment"),
    "NewsSource": ("domains.comms.models.communication_schema_models", "NewsSource"),
    "InternalNotice": ("domains.comms.models.communication_schema_models", "InternalNotice"),
    "EscalationSLARule": ("domains.comms.models.communication_schema_models", "EscalationSLARule"),
    # analytics domain
    "ExecutiveNews": ("domains.analytics.models.analytics_schema_models", "ExecutiveNews"),
    "PredictiveSimulation": ("domains.analytics.models.analytics_schema_models", "PredictiveSimulation"),
    # security domain
    "AlertEscalationRule": ("domains.security.models.security_schema_models", "AlertEscalationRule"),
    # logistics domain
    "CityDistanceMatrix": ("domains.logistics.models.logistics_schema_models", "CityDistanceMatrix"),
    # comms domain (news)
    "NewsArticle": ("domains.comms.models.news", "NewsArticle"),
    # comms domain (chat)
    "DirectChatMessage": ("domains.comms.models.chat", "DirectChatMessage"),
    "DirectChatRoom": ("domains.comms.models.chat", "DirectChatRoom"),
    "EntityChatMessage": ("domains.comms.models.chat", "EntityChatMessage"),
    "EntityChatThread": ("domains.comms.models.chat", "EntityChatThread"),
    "EscalationSLALog": ("domains.comms.models.chat", "EscalationSLALog"),
    "GroupChatMember": ("domains.comms.models.chat", "GroupChatMember"),
    "GroupChatMessage": ("domains.comms.models.chat", "GroupChatMessage"),
    "GroupChatRoom": ("domains.comms.models.chat", "GroupChatRoom"),
    "VideoRoom": ("domains.comms.models.chat", "VideoRoom"),
    "VideoRoomParticipant": ("domains.comms.models.chat", "VideoRoomParticipant"),
    "VideoRoomRecording": ("domains.comms.models.chat", "VideoRoomRecording"),
    # hr domain (shift handover)
    "ShiftHandoverSession": ("domains.hr.models.employee_models", "ShiftHandoverSession"),
    "ShiftHandoverTask": ("domains.hr.models.employee_models", "ShiftHandoverTask"),
}

_IMPORTED: dict[str, object] = {}


def __getattr__(name: str):
    """Lazy import of canonical models to avoid circular imports and InvalidRequestError."""
    if name in _IMPORTED:
        return _IMPORTED[name]
    if name in _CANONICAL_EXPORTS:
        module_path, class_name = _CANONICAL_EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _IMPORTED[name] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
