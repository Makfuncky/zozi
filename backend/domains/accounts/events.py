"""accounts domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The accounts domain owns authentication, identity, and session entities. It
publishes notifications when those entities change so downstream domains
(orders, governance, comms, security, audit) may react.

Transport is the sanctioned in-process ``event_bus`` (circuit-exempt data layer).
"""

from __future__ import annotations

from infrastructure.messaging.events.event_bus import publish

# --- notifications the accounts domain emits after a write (downstream reacts) ---
EVENT_USER_CREATED = "accounts.user.created"
EVENT_USER_UPDATED = "accounts.user.updated"
EVENT_USER_DELETED = "accounts.user.deleted"
EVENT_USER_ROLE_ASSIGNED = "accounts.user.role_assigned"
EVENT_SESSION_CREATED = "accounts.session.created"
EVENT_SESSION_REVOKED = "accounts.session.revoked"
EVENT_PASSWORD_CHANGED = "accounts.password.changed"
EVENT_OTP_ISSUED = "accounts.otp.issued"
EVENT_OTP_VERIFIED = "accounts.otp.verified"
EVENT_LOGIN_SUCCEEDED = "accounts.login.succeeded"
EVENT_LOGIN_FAILED = "accounts.login.failed"
EVENT_LOGOUT = "accounts.logout"


def publish_user_created(user_id: int, email: str, country_code: str | None = None) -> None:
    publish(EVENT_USER_CREATED, {"user_id": user_id, "email": email, "country_code": country_code})


def publish_user_updated(user_id: int, changed_fields: list[str] | None = None) -> None:
    publish(EVENT_USER_UPDATED, {"user_id": user_id, "changed_fields": changed_fields or []})


def publish_user_deleted(user_id: int) -> None:
    publish(EVENT_USER_DELETED, {"user_id": user_id})


def publish_user_role_assigned(user_id: int, role: str, assigned_by: int | None = None) -> None:
    publish(EVENT_USER_ROLE_ASSIGNED, {"user_id": user_id, "role": role, "assigned_by": assigned_by})


def publish_session_created(session_id: str, user_id: int, ip: str | None = None) -> None:
    publish(EVENT_SESSION_CREATED, {"session_id": session_id, "user_id": user_id, "ip": ip})


def publish_session_revoked(session_id: str, user_id: int, reason: str | None = None) -> None:
    publish(EVENT_SESSION_REVOKED, {"session_id": session_id, "user_id": user_id, "reason": reason})


def publish_password_changed(user_id: int) -> None:
    publish(EVENT_PASSWORD_CHANGED, {"user_id": user_id})


def publish_otp_issued(user_id: int, channel: str, purpose: str) -> None:
    publish(EVENT_OTP_ISSUED, {"user_id": user_id, "channel": channel, "purpose": purpose})


def publish_otp_verified(user_id: int, purpose: str) -> None:
    publish(EVENT_OTP_VERIFIED, {"user_id": user_id, "purpose": purpose})


def publish_login_succeeded(user_id: int, ip: str | None = None, user_agent: str | None = None) -> None:
    publish(EVENT_LOGIN_SUCCEEDED, {"user_id": user_id, "ip": ip, "user_agent": user_agent})


def publish_login_failed(email: str, ip: str | None = None, reason: str | None = None) -> None:
    publish(EVENT_LOGIN_FAILED, {"email": email, "ip": ip, "reason": reason})


def publish_logout(user_id: int, session_id: str | None = None) -> None:
    publish(EVENT_LOGOUT, {"user_id": user_id, "session_id": session_id})


__all__ = [
    "EVENT_USER_CREATED",
    "EVENT_USER_UPDATED",
    "EVENT_USER_DELETED",
    "EVENT_USER_ROLE_ASSIGNED",
    "EVENT_SESSION_CREATED",
    "EVENT_SESSION_REVOKED",
    "EVENT_PASSWORD_CHANGED",
    "EVENT_OTP_ISSUED",
    "EVENT_OTP_VERIFIED",
    "EVENT_LOGIN_SUCCEEDED",
    "EVENT_LOGIN_FAILED",
    "EVENT_LOGOUT",
    "publish_user_created",
    "publish_user_updated",
    "publish_user_deleted",
    "publish_user_role_assigned",
    "publish_session_created",
    "publish_session_revoked",
    "publish_password_changed",
    "publish_otp_issued",
    "publish_otp_verified",
    "publish_login_succeeded",
    "publish_login_failed",
    "publish_logout",
]
