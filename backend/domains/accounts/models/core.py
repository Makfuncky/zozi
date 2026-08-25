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

# accounts/models/core.py â€” owns the ``accounts``-schema tables that have no
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


# â”€â”€ accounts-owned tables (inline definitions) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
# These are NOT re-defined here to avoid InvalidRequestError conflicts.

from domains.audit.models.audit_schema_models import AuditLog, CommandCenterView  # noqa: F401
from domains.comms.models.communication_schema_models import (  # noqa: F401
    SupportTicket, SupportTicketReply, TicketAttachment,
    NewsSource, InternalNotice, EscalationSLARule,
)
from domains.comms.models.communication import TicketMessage  # noqa: F401
from domains.logistics.models.logistics_schema_models import CityDistanceMatrix  # noqa: F401
from domains.analytics.models.analytics_schema_models import (  # noqa: F401
    ExecutiveNews, PredictiveSimulation,
)
from domains.security.models.security_schema_models import AlertEscalationRule  # noqa: F401


# â”€â”€ Re-exports from canonical homes (DO NOT redefine) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# These tables have canonical definitions in other domains. Re-exported here so
# legacy ``from domains.accounts.models.core import X`` imports keep resolving.

from domains.comms.models.news import NewsArticle as NewsArticle  # noqa: F401,F811
from domains.comms.models.chat import (  # noqa: F401
    DirectChatMessage as DirectChatMessage,
    DirectChatRoom as DirectChatRoom,
    EntityChatMessage as EntityChatMessage,
    EntityChatThread as EntityChatThread,
    EscalationSLALog as EscalationSLALog,
    GroupChatMember as GroupChatMember,
    GroupChatMessage as GroupChatMessage,
    GroupChatRoom as GroupChatRoom,
    VideoRoom as VideoRoom,
    VideoRoomParticipant as VideoRoomParticipant,
    VideoRoomRecording as VideoRoomRecording,
)
from domains.hr.models.employee_models import (  # noqa: F401
    ShiftHandoverSession as ShiftHandoverSession,
    ShiftHandoverTask as ShiftHandoverTask,
)

# Re-export user-related classes from accounts/models/user.py (canonical home).
# Lazy import to avoid circular import: accounts/user.py â†’ customers â†’ accounts/core.py
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
    """Lazy import of user re-exports to break circular import."""
    if name in _USER_CACHE:
        return _USER_CACHE[name]
    if name in _USER_RE_EXPORTS:
        module_path, class_name = _USER_RE_EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _USER_CACHE[name] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


