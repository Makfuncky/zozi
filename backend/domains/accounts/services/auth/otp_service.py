"""OTP / MFA challenge logic for the accounts domain.

Thin challenge store plus best-effort delivery. Real email/SMS transport is
stubbed here and wired to the messaging layer later (twilio is not configured
in dev, so SMS only logs). Codes are bcrypt-hashed at rest; plaintext is never
persisted.
"""
from __future__ import annotations

import logging
import random
import string
from datetime import timedelta

from sqlalchemy.orm import Session

from domains.accounts.models.otp import OtpCode
from infrastructure.security.auth import get_password_hash, verify_password
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.config import settings

logger = logging.getLogger(__name__)

def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


OTP_TTL_SECONDS = _as_int(getattr(settings, "otp_ttl_seconds", 300), 300)
OTP_MAX_ATTEMPTS = _as_int(getattr(settings, "otp_max_attempts", 5), 5)


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def start_otp(user, purpose: str, channel: str = "email", destination: str | None = None, db: Session | None = None) -> OtpCode:
    """Issue a fresh OTP for ``user``/``purpose`` and attempt delivery."""
    code = _generate_code()
    expires_at = utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    record = OtpCode(
        user_id=user.id,
        purpose=purpose,
        channel=channel,
        destination=destination,
        code_hash=get_password_hash(code),
        expires_at=expires_at,
        country_code=getattr(user, "country_code", None),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    _deliver(user, channel, destination, code)
    return record


def verify_otp(user, purpose: str, code: str, db: Session | None = None) -> bool:
    """Return True if ``code`` matches the latest unverified, unexpired challenge."""
    record = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == user.id,
            OtpCode.purpose == purpose,
            OtpCode.verified.is_(False),
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if record is None:
        return False
    if record.expires_at < utcnow():
        return False
    if record.attempts >= OTP_MAX_ATTEMPTS:
        return False
    record.attempts += 1
    if verify_password(code, record.code_hash):
        record.verified = True
        db.commit()
        return True
    db.commit()
    return False


def _deliver(user, channel: str, destination: str | None, code: str) -> None:
    dest = destination or getattr(user, "email", None) or getattr(user, "phone", None)
    if channel == "email" and dest:
        # TODO(zozi): route through the email service once wired; log for dev.
        logger.info("OTP(email) user=%s destination=%s code=%s", user.id, dest, code)
    elif channel == "sms" and dest:
        # TODO(zozi): integrate twilio/SMS provider; log for dev (not configured).
        logger.info("OTP(sms) user=%s destination=%s code=%s [delivery stub]", user.id, dest, code)
    else:
        logger.warning("OTP delivery skipped: no destination for user=%s", user.id)
