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
    func,
)
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# accounts/models/core.py — owns the ``accounts``-schema tables that have no
# other canonical home. Tables that belong to other domains are re-exported
# from their canonical homes below so legacy imports resolve without
# re-defining any table on the shared MetaData.

__all__ = [
    # owned by accounts (defined inline below)
    "Address", "Cart", "CartItem",
    "AuditLog", "SupportTicket", "SupportTicketReply", "TicketAttachment", "UserBrowsingHistory",
    "CityDistanceMatrix", "ExecutiveNews", "UserSession", "SystemHealthEvent", "CommandCenterView",
    "NewsSource", "InternalNotice", "PredictiveSimulation", "AlertEscalationRule",
    "SupportTicketMessage",
    # re-exported from canonical homes (do NOT redefine)
    "NewsArticle",
    "EntityChatMessage",
    "EntityChatThread",
    "VideoRoom",
    "VideoRoomParticipant",
    "VideoRoomRecording",
    "DirectChatMessage",
    "DirectChatRoom",
    "GroupChatRoom",
    "GroupChatMember",
    "GroupChatMessage",
    "ShiftHandoverSession",
    "ShiftHandoverTask",
    "EscalationSLALog",
]


# ── accounts-owned tables (inline definitions) ──────────────────────────────

class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False)
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
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="addresses")


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    user = relationship("User", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        Index("ix_cart_items_user_product", "user_id", "product_id"),
        Index("ix_cart_items_created", "created_at"),
        {"schema": "commerce"},
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=False)
    product_id = Column(Integer, ForeignKey("commerce.products.id", ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, default=1)
    selected_size = Column(String(50), default="", nullable=False)
    selected_color = Column(String(50), default="", nullable=False)
    variant_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


# Re-export tables whose canonical homes live in other domains.
# Lazily imported (Law 3: avoid direct cross-domain model imports at module level).

_CANONICAL_CROSS_DOMAIN_EXPORTS: dict[str, tuple[str, str]] = {
    "AuditLog": ("domains.audit.models.audit_schema_models", "AuditLog"),
    "CommandCenterView": ("domains.audit.models.audit_schema_models", "CommandCenterView"),
    "SupportTicket": ("domains.comms.models.communication_schema_models", "SupportTicket"),
    "SupportTicketReply": ("domains.comms.models.communication_schema_models", "SupportTicketReply"),
    "TicketAttachment": ("domains.comms.models.communication_schema_models", "TicketAttachment"),
    "NewsSource": ("domains.comms.models.communication_schema_models", "NewsSource"),
    "InternalNotice": ("domains.comms.models.communication_schema_models", "InternalNotice"),
    "EscalationSLARule": ("domains.comms.models.communication_schema_models", "EscalationSLARule"),
    "TicketMessage": ("domains.comms.models.communication", "TicketMessage"),
    "CityDistanceMatrix": ("domains.logistics.models.logistics_schema_models", "CityDistanceMatrix"),
    "ExecutiveNews": ("domains.analytics.models.analytics_schema_models", "ExecutiveNews"),
    "PredictiveSimulation": ("domains.analytics.models.analytics_schema_models", "PredictiveSimulation"),
    "AlertEscalationRule": ("domains.security.models.security_schema_models", "AlertEscalationRule"),
    "NewsArticle": ("domains.comms.models.news", "NewsArticle"),
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
    "ShiftHandoverSession": ("domains.hr.models.employee_models", "ShiftHandoverSession"),
    "ShiftHandoverTask": ("domains.hr.models.employee_models", "ShiftHandoverTask"),
}

_IMPORTED_CROSS_DOMAIN: dict[str, object] = {}


# Re-export user-related classes from accounts/models/user.py (canonical home).
# Lazy import to avoid circular import: accounts/user.py → customers → accounts/core.py
_USER_RE_EXPORTS = {
    "User": ("domains.accounts.models.user", "User"),
    "UserLoginHistory": ("domains.accounts.models.user", "UserLoginHistory"),
    "UserDevice": ("domains.accounts.models.user", "UserDevice"),
    "PasswordResetToken": ("domains.accounts.models.user", "PasswordResetToken"),
    "EmailVerificationToken": ("domains.accounts.models.user", "EmailVerificationToken"),
    "RevokedToken": ("domains.accounts.models.user", "RevokedToken"),
    # governance domain (SystemHealthEvent, UserSession defined in governance/core.py)
    "SystemHealthEvent": ("domains.governance.models.core", "SystemHealthEvent"),
    "UserSession": ("domains.governance.models.core", "UserSession"),
}

_USER_CACHE: dict[str, object] = {}


def __getattr__(name: str):
    """Lazy import of cross-domain re-exports (Law 3: no import-time coupling)."""
    # Check user re-exports first (existing behavior)
    if name in _USER_CACHE:
        return _USER_CACHE[name]
    if name in _USER_RE_EXPORTS:
        module_path, class_name = _USER_RE_EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _USER_CACHE[name] = cls
        return cls
    # Then check cross-domain model re-exports
    if name in _IMPORTED_CROSS_DOMAIN:
        return _IMPORTED_CROSS_DOMAIN[name]
    if name in _CANONICAL_CROSS_DOMAIN_EXPORTS:
        module_path, class_name = _CANONICAL_CROSS_DOMAIN_EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _IMPORTED_CROSS_DOMAIN[name] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
