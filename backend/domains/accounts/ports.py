"""accounts domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.accounts.models`` or ``domains.accounts.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).

A3 / RESOLVER §26 ACC-01 cleanup: this file previously imported 30+ models
spanning security, hr, and the god-module ``core`` hub. Per Law 3, only
accounts-owned models live here. Cross-domain helpers were moved:

  * security.DocumentVerification / KYCVerification / AlertEscalationRule
      -> ``domains.security.ports``
  * hr.OnboardingPipeline / OnboardingStep
      -> ``domains.hr.ports``
  * The ``core`` models that were actually hr-shift / security composites
    (ShiftHandoverSession, ShiftHandoverTask, EscalationSLARule, EscalationSLALog)
    remain here ONLY because they are owned by accounts (see
    ``domains.accounts.models.core``); they are NOT re-homed.

Keyset (cursor) pagination: ``list_*`` returns a plain ``List`` (back-compat);
``*_page`` companions return a ``CursorPage`` for scale-ready cursor paging
(100Ks-concurrent-user path, no OFFSET on hot lists).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

from domains.accounts.models.core import (
    Address,
    Cart,
    CartItem,
    CityDistanceMatrix,
    CommandCenterView,
    DirectChatMessage,
    DirectChatRoom,
    EntityChatMessage,
    EntityChatThread,
    EscalationSLALog,
    EscalationSLARule,
    ExecutiveNews,
    GroupChatMember,
    GroupChatMessage,
    GroupChatRoom,
    InternalNotice,
    NewsArticle,
    NewsSource,
    PredictiveSimulation,
    ShiftHandoverSession,
    ShiftHandoverTask,
    SupportTicket,
    SupportTicketReply,
    SystemHealthEvent,
    TicketAttachment,
    UserBrowsingHistory,
    UserSession,
    VideoRoom,
    VideoRoomParticipant,
    VideoRoomRecording,
    AuditLog,
)
from domains.accounts.models.mfa_factor import MfaFactor
from domains.accounts.models.onboarding import OCRResult
from domains.accounts.models.otp import OtpCode
from domains.accounts.models.social import SocialIdentity
from domains.accounts.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    RevokedToken,
    User,
    UserDevice,
    UserLoginHistory,
)

# Referral / ReferralPointEvent: owned by customers domain; re-exported via
# the accounts.models.core lazy __getattr__ so ports.py stays free of
# cross-domain imports at module load time (Law 3).
from domains.accounts.models import core as _accounts_core
Referral = _accounts_core.Referral
ReferralPointEvent = _accounts_core.ReferralPointEvent
del _accounts_core


# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)


# --- Filtered read helpers (router-layer consolidation) ---
# These express the exact filters the customer/employee routers previously ran
# inline so callers stay free of raw ``db.query`` in the module layer.

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Return the User whose ``id`` matches (or None)."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Return the User whose ``email`` matches (or None)."""
    return db.query(User).filter(User.email == email).first()


def list_active_user_sessions(db: Session, user_id: int) -> List[UserSession]:
    """Return non-expired UserSession rows for a user, newest first."""
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.expires_at > db.func.now())
        .order_by(UserSession.created_at.desc())
        .all()
    )


def list_open_support_tickets_for_user(db: Session, user_id: int) -> List[SupportTicket]:
    """Return open SupportTicket rows for a user, newest first."""
    return (
        db.query(SupportTicket)
        .filter(
            SupportTicket.user_id == user_id,
            SupportTicket.status.in_(("open", "in_progress", "pending")),
        )
        .order_by(SupportTicket.created_at.desc())
        .all()
    )


# --- Service delegation (sanctioned cross-domain wrappers) ---
# These expose service-level helpers so module routers can import from
# accounts.ports without crossing into domains.accounts.services directly.

def get_referral_dashboard(current_user: dict, db: Session):
    """Sanctioned cross-domain read: referral dashboard for the current user."""
    from domains.accounts.services.auth.auth_service import get_referral_dashboard as _svc
    return _svc(current_user, db)


__all__ = [
    "Address",
    "Cart",
    "CartItem",
    "CityDistanceMatrix",
    "CommandCenterView",
    "DirectChatMessage",
    "DirectChatRoom",
    "EntityChatMessage",
    "EntityChatThread",
    "EscalationSLALog",
    "EscalationSLARule",
    "ExecutiveNews",
    "GroupChatMember",
    "GroupChatMessage",
    "GroupChatRoom",
    "InternalNotice",
    "NewsArticle",
    "NewsSource",
    "OCRResult",
    "OtpCode",
    "PredictiveSimulation",
    "ShiftHandoverSession",
    "ShiftHandoverTask",
    "SocialIdentity",
    "SupportTicket",
    "SupportTicketReply",
    "SystemHealthEvent",
    "TicketAttachment",
    "User",
    "UserBrowsingHistory",
    "UserDevice",
    "UserLoginHistory",
    "UserSession",
    "VideoRoom",
    "VideoRoomParticipant",
    "VideoRoomRecording",
    "AuditLog",
    "EmailVerificationToken",
    "MfaFactor",
    "PasswordResetToken",
    "Referral",
    "ReferralPointEvent",
    "RevokedToken",
    "get_user_by_id",
    "get_user_by_email",
    "list_active_user_sessions",
    "list_open_support_tickets_for_user",
    "get_referral_dashboard",
]

# Service re-exports (Law 3 sanctioned cross-domain surface). Modules under
# modules/supplier import these from ``domains.accounts.ports`` instead of
# reaching into the services tree directly.
# Disabled: circular import issue
# from domains.accounts.services.auth.auth_service import (  # noqa: E402, F401
#     create_supplier_profile,
# )

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "get_current_user": ("domains.accounts.services.auth.security_dependencies", "get_current_user"),
    "start_otp": ("domains.accounts.services.auth.auth_service", "start_otp"),
    "verify_otp": ("domains.accounts.services.auth.auth_service", "verify_otp"),
    "RBACService": ("domains.accounts.services.permissions.permission_service", "RBACService"),
    "get_hierarchy_permissions": ("domains.accounts.services.permissions.permission_service", "get_hierarchy_permissions"),
    "update_role_permissions": ("domains.accounts.services.permissions.permission_service", "update_role_permissions"),
    "force_reset_password_admin": ("domains.accounts.services.users.user_management_service", "force_reset_password_admin"),
    "create_supplier_profile": ("domains.accounts.services.auth.auth_service", "create_supplier_profile"),
}
import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

