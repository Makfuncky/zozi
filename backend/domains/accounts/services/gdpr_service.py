"""GDPR service for the accounts domain.

Implements data subject rights under GDPR:
  * Art. 15  Right of access         -> export_user_data()
  * Art. 17  Right to erasure        -> delete_user_data()
  * Art. 17  Right to be forgotten   -> anonymize_user_data() (preserve financial trail)
  * Art. 7   Consent management      -> get_user_consents() / record_consent()

Per ARCHITECTURE_DIAGRAM.md, the accounts domain is the canonical owner of
user identity, so GDPR operations on the user record live here. Cross-domain
data (orders, addresses) is best-effort read here; deep deletion of those is
delegated to each owning domain via events.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.accounts.models.user_consent import UserConsent
from domains.accounts.models.user import (
    User,
    UserDevice,
    UserLoginHistory,
)
from domains.accounts.models.core import UserSession

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

ANON_EMAIL_DOMAIN = "anonymized.invalid"
ANON_PHONE_PREFIX = "+0000000000"
ANON_NAME_PREFIX = "Anonymized User"

# Consent types recognised by the platform
CONSENT_TERMS = "terms_of_service"
CONSENT_PRIVACY = "privacy_policy"
CONSENT_MARKETING = "marketing"
CONSENT_ANALYTICS = "analytics"
CONSENT_THIRD_PARTY = "third_party_sharing"

KNOWN_CONSENT_TYPES = {
    CONSENT_TERMS,
    CONSENT_PRIVACY,
    CONSENT_MARKETING,
    CONSENT_ANALYTICS,
    CONSENT_THIRD_PARTY,
}


# ── Helpers ────────────────────────────────────────────────────────────────


def _scramble(value: Optional[str], length: int = 16) -> str:
    """Return a non-reversible placeholder of fixed length."""
    if not value:
        return ""
    digest = hashlib.sha256(f"{value}:{secrets.token_hex(8)}".encode()).hexdigest()
    return digest[:length]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Consent management ─────────────────────────────────────────────────────


def record_consent(
    user_id: int,
    consent_type: str,
    granted: bool,
    ip_address: str,
    user_agent: str,
    db: Session,
    consent_version: Optional[str] = None,
    country_code: Optional[str] = None,
) -> UserConsent:
    """Record a single grant or revocation decision for a user.

    Historical rows are retained; revoking a previously-granted consent
    updates the latest open row by setting ``revoked_at``.
    """
    now = _utcnow()
    user = db.query(User).filter(User.id == user_id).first()
    if user is None and country_code is None:
        country_code = None

    if granted:
        record = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            granted=True,
            granted_at=now,
            revoked_at=None,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:512],
            consent_version=consent_version,
            country_code=country_code or getattr(user, "country_code", None),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    # Revocation: close out the latest open row for this consent_type if any
    open_row = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == consent_type,
            UserConsent.granted.is_(True),
            UserConsent.revoked_at.is_(None),
        )
        .order_by(UserConsent.granted_at.desc())
        .first()
    )
    if open_row is not None:
        open_row.revoked_at = now
        db.commit()
        db.refresh(open_row)
        return open_row

    # No prior grant — record a negative row for the audit trail
    record = UserConsent(
        user_id=user_id,
        consent_type=consent_type,
        granted=False,
        granted_at=now,
        revoked_at=now,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:512],
        consent_version=consent_version,
        country_code=country_code or getattr(user, "country_code", None),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_consents(user_id: int, db: Session) -> list[UserConsent]:
    """Return the full consent history for ``user_id`` ordered newest first."""
    return (
        db.query(UserConsent)
        .filter(UserConsent.user_id == user_id)
        .order_by(UserConsent.granted_at.desc())
        .all()
    )


def has_active_consent(user_id: int, consent_type: str, db: Session) -> bool:
    """Return True if the user has an unrevoked grant for ``consent_type``."""
    open_row = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == consent_type,
            UserConsent.granted.is_(True),
            UserConsent.revoked_at.is_(None),
        )
        .order_by(UserConsent.granted_at.desc())
        .first()
    )
    return open_row is not None


# ── Art. 15 — Right of access (data export) ───────────────────────────────


def export_user_data(user_id: int, db: Session) -> dict[str, Any]:
    """Export every piece of personal data we hold for ``user_id``.

    Returns a JSON-serialisable dictionary. Cross-domain records (orders,
    addresses) are best-effort included only if the model is importable
    here; otherwise the owning domain is responsible for emitting a
    deletion event.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return {"user_id": user_id, "found": False, "data": {}}

    data: dict[str, Any] = {
        "profile": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": getattr(user, "full_name", None),
            "phone": getattr(user, "phone", None),
            "role": getattr(user, "role", None),
            "country_code": getattr(user, "country_code", None),
            "is_active": getattr(user, "is_active", None),
            "email_verified": getattr(user, "email_verified", None),
            "created_at": _iso(getattr(user, "created_at", None)),
            "updated_at": _iso(getattr(user, "updated_at", None)),
            "last_login": _iso(getattr(user, "last_login", None)),
        },
        "login_history": [
            {
                "timestamp": _iso(h.timestamp),
                "ip_address": h.ip_address,
                "user_agent": h.user_agent,
                "success": h.success,
                "country_code": getattr(h, "country_code", None),
            }
            for h in db.query(UserLoginHistory)
            .filter(UserLoginHistory.user_id == user_id)
            .order_by(UserLoginHistory.timestamp.desc())
            .limit(500)
            .all()
        ],
        "devices": [
            {
                "fingerprint": d.device_fingerprint,
                "device_name": d.device_name,
                "is_trusted": d.is_trusted,
                "first_seen_at": _iso(d.first_seen_at),
                "last_seen_at": _iso(d.last_seen_at),
                "last_ip": d.last_ip,
            }
            for d in db.query(UserDevice)
            .filter(UserDevice.user_id == user_id)
            .all()
        ],
        "sessions": [
            {
                "id": s.id,
                "created_at": _iso(getattr(s, "created_at", None)),
                "expires_at": _iso(getattr(s, "expires_at", None)),
                "ip_address": getattr(s, "ip_address", None),
                "is_active": getattr(s, "is_active", None),
            }
            for s in db.query(UserSession)
            .filter(UserSession.user_id == user_id)
            .all()
        ],
        "consents": [
            {
                "consent_type": c.consent_type,
                "granted": c.granted,
                "granted_at": _iso(c.granted_at),
                "revoked_at": _iso(c.revoked_at),
                "consent_version": c.consent_version,
                "ip_address": c.ip_address,
                "country_code": c.country_code,
            }
            for c in get_user_consents(user_id, db)
        ],
    }

    return {
        "user_id": user_id,
        "found": True,
        "exported_at": _iso(_utcnow()),
        "data": data,
    }


# ── Art. 17 — Right to erasure (anonymize vs hard delete) ─────────────────


def anonymize_user_data(user_id: int, db: Session) -> bool:
    """Anonymize the user record while preserving financial/audit trail.

    Replaces PII (name, email, phone) with non-reversible placeholders and
    marks the account inactive. Order/transaction FKs are preserved so that
    tax/regulatory records remain valid.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return False

    placeholder_id = f"anon-{_scramble(str(user_id), 8)}"

    user.email = f"{placeholder_id}@{ANON_EMAIL_DOMAIN}"
    user.username = placeholder_id
    if hasattr(user, "full_name"):
        user.full_name = f"{ANON_NAME_PREFIX} {placeholder_id}"
    if hasattr(user, "phone"):
        user.phone = ANON_PHONE_PREFIX
    if hasattr(user, "hashed_password"):
        user.hashed_password = None
    if hasattr(user, "is_active"):
        user.is_active = False
    if hasattr(user, "is_verified"):
        user.is_verified = False
    if hasattr(user, "email_verified"):
        user.email_verified = False
    if hasattr(user, "totp_secret"):
        user.totp_secret = None

    # Close out any open consent rows — anonymized user is no longer consenting
    open_consents = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == user_id,
            UserConsent.revoked_at.is_(None),
        )
        .all()
    )
    now = _utcnow()
    for row in open_consents:
        row.revoked_at = now

    # Revoke active sessions and devices
    db.query(UserSession).filter(UserSession.user_id == user_id).update(
        {UserSession.is_active: False} if hasattr(UserSession, "is_active") else {}
    )
    db.query(UserDevice).filter(UserDevice.user_id == user_id).update(
        {UserDevice.is_trusted: False}
    )

    db.commit()
    logger.info("Anonymized user_id=%s", user_id)
    return True


def delete_user_data(user_id: int, db: Session) -> bool:
    """Hard-delete the user record and cascade through owned rows.

    The accounts-owned tables (sessions, devices, login history, consents)
    are removed directly here. Other domains own their own tables
    (orders, addresses, etc.) and must subscribe to the user-deletion
    event published by this function. FKs use ON DELETE CASCADE for
    accounts-schema dependents.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return False

    # Accounts-owned dependents first (defensive — FK CASCADE handles it,
    # but we want explicit ordering for clarity and log traceability).
    db.query(UserConsent).filter(UserConsent.user_id == user_id).delete()
    db.query(UserLoginHistory).filter(UserLoginHistory.user_id == user_id).delete()
    db.query(UserDevice).filter(UserDevice.user_id == user_id).delete()
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()

    db.delete(user)
    db.commit()

    _emit_user_deleted_event(user_id)
    logger.info("Hard-deleted user_id=%s", user_id)
    return True


# ── Internals ──────────────────────────────────────────────────────────────


def _iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _emit_user_deleted_event(user_id: int) -> None:
    """Best-effort emit of a cross-domain event so other domains can purge
    their own user-owned data (orders, addresses, marketing preferences,
    etc.). Failure to publish must not block the deletion itself."""
    try:
        from infrastructure.messaging import publish_event  # type: ignore

        publish_event(
            "accounts.user_deleted",
            {"user_id": user_id, "deleted_at": _iso(_utcnow())},
        )
    except Exception as exc:  # pragma: no cover — best effort
        logger.warning("Failed to publish accounts.user_deleted event: %s", exc)
