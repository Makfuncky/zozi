"""
Auth write service â€” persistence helpers for account lifecycle, verification,
referrals and 2FA.

These functions were previously imported by `controllers/auth_controller.py` as a
flat service module. They provide thin, transactional ORM write helpers so the
controller can stay focused on request/response orchestration.

All functions take an active SQLAlchemy `Session` as their first argument and are
responsible for flushing/committing their own writes.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from infrastructure.database.database import SessionLocal
from models import (
    EmailVerificationToken,
    LogisticsPartner,
    PasswordResetToken,
    ReferralPointEvent,
    SupplierProfile,
    User,
    UserDevice,
    UserLoginHistory,
)
from infrastructure.utils.datetime_utils import utcnow
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


# â”€â”€ User creation / update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_user(
    *,
    email: Optional[str],
    username: Optional[str],
    hashed_password: str,
    role: str = "customer",
    phone: Optional[str] = None,
    referral_code: Optional[str] = None,
    country_code: Optional[str] = None,
    referred_by_user_id: Optional[int] = None,
    email_verified: bool = False,
    full_name: Optional[str] = None,
) -> User:
    """Insert a new user row and return the persisted instance (id assigned)."""
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        role=role,
        phone=phone,
        referral_code=referral_code,
        country_code=country_code,
        referred_by_user_id=referred_by_user_id,
        email_verified=email_verified,
        full_name=full_name,
    )
    return user


def _bind(session: Session, obj) -> None:
    session.add(obj)
    session.flush()


def create_user_persist(session: Session, user: User) -> User:
    """Persist a pre-built User instance (used when a Session is supplied)."""
    _bind(session, user)
    return user


def update_user(db: Session, user: User, updates: dict[str, Any]) -> User:
    """Apply a dict of column updates to an existing user and flush."""
    for key, value in updates.items():
        setattr(user, key, value)
    db.add(user)
    db.flush()
    return user


def update_user_profile(db: Session, user: User, updates: dict[str, Any]) -> User:
    """Alias of :func:`update_user` for profile-specific updates."""
    return update_user(db, user, updates)


def update_user_points(db: Session, user: User, points: int) -> User:
    """Set the user's referral point total and flush."""
    user.referral_points = points
    db.add(user)
    db.flush()
    return user


def persist_last_login(db: Session, user: User) -> None:
    """Record the current time as the user's last login."""
    user.last_login = utcnow()
    db.add(user)
    db.commit()
    db.flush()


def flush_user(db: Session) -> None:
    """Flush pending changes to the database without committing."""
    db.flush()


def commit_user_registration(db: Session) -> None:
    """Commit the unit of work for a registration transaction."""
    db.commit()
    db.flush()


# â”€â”€ Social / OAuth users â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_social_user(
    db: Session,
    *,
    email: str,
    username: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    profile_image: Optional[str] = None,
    country_code: Optional[str] = None,
    referral_code: Optional[str] = None,
) -> User:
    """Create a user derived from an OAuth identity."""
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        profile_image=profile_image,
        country_code=country_code,
        referral_code=referral_code,
        role="customer",
        email_verified=True,
    )
    _bind(db, user)
    return user


def update_or_create_social_user(
    db: Session,
    *,
    email: str,
    username: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    profile_image: Optional[str] = None,
    country_code: Optional[str] = None,
    referral_code: Optional[str] = None,
) -> User:
    """Return an existing social user (by email) or create one."""
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        return existing
    return create_social_user(
        db,
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        profile_image=profile_image,
        country_code=country_code,
        referral_code=referral_code,
    )


# â”€â”€ Email verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_email_verification_token(
    db: Session,
    *,
    user_id: int,
    raw_token: str,
    expires_at: Any,
) -> EmailVerificationToken:
    """Persist a new email verification token."""
    token = EmailVerificationToken(
        user_id=user_id,
        token=raw_token,
        expires_at=expires_at,
        used=False,
    )
    _bind(db, token)
    return token


def mark_email_verification_token_used(db: Session, ev: EmailVerificationToken) -> None:
    """Mark an email verification token as used."""
    ev.used = True
    db.add(ev)
    db.flush()


def expire_email_verification_token(db: Session, ev: EmailVerificationToken) -> None:
    """Expire an email verification token (alias for marking it used)."""
    ev.used = True
    db.add(ev)
    db.flush()


def invalidate_email_verification_tokens(db: Session, user_id: int) -> int:
    """Mark every outstanding (unused) email verification token for a user as used."""
    return (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used.is_(False),
        )
        .update({"used": True})
    )


def update_user_email_verification(
    db: Session,
    user: User,
    *,
    email_verified: bool = True,
) -> User:
    """Mark a user's email as verified."""
    user.email_verified = email_verified
    user.is_verified = email_verified
    db.add(user)
    db.flush()
    return user


def update_user_email_verified(db: Session, user: User) -> User:
    """Mark a user's email verified (convenience wrapper)."""
    return update_user_email_verification(db, user, email_verified=True)


# â”€â”€ Password reset â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_password_reset_token(
    db: Session,
    *,
    user_id: int,
    raw_token: str,
    expires_at: Any,
) -> PasswordResetToken:
    """Persist a new password reset token."""
    token = PasswordResetToken(
        user_id=user_id,
        token=raw_token,
        expires_at=expires_at,
        used=False,
    )
    _bind(db, token)
    return token


def mark_password_reset_token_used(db: Session, db_token: PasswordResetToken) -> None:
    """Mark a password reset token as used."""
    db_token.used = True
    db.add(db_token)
    db.flush()


def invalidate_password_reset_tokens(db: Session, user_id: int) -> int:
    """Mark every outstanding (unused) password reset token for a user as used."""
    return (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used.is_(False),
        )
        .update({"used": True})
    )


def execute_password_reset(db: Session, user: User, db_token: PasswordResetToken, hashed_password: str) -> None:
    """Apply a new password and consume the reset token."""
    user.hashed_password = hashed_password
    db_token.used = True
    db.add(user)
    db.add(db_token)
    db.commit()
    db.flush()


# â”€â”€ Supplier / logistics onboarding â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_supplier_profile(
    db: Session,
    *,
    user_id: int,
    business_name: Optional[str],
    slug: str,
    business_type: Optional[str] = None,
    country: Optional[str] = None,
    country_code: Optional[str] = None,
    phone_business: Optional[str] = None,
    website_url: Optional[str] = None,
) -> SupplierProfile:
    """Create a supplier business profile for a newly registered supplier."""
    profile = SupplierProfile(
        user_id=user_id,
        business_name=business_name or "",
        slug=slug,
        business_type=business_type,
        country=country,
        country_code=country_code,
        website=website_url,
    )
    _bind(db, profile)
    return profile


def create_logistics_partner(
    db: Session,
    *,
    name: str,
    code: str,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    status: str = "active",
    country_code: Optional[str] = None,
    user_id: Optional[int] = None,
) -> LogisticsPartner:
    """Create a logistics partner record for a newly registered partner."""
    partner = LogisticsPartner(
        name=name,
        code=code,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        status=status,
        verification_status="pending",
        country_code=country_code,
        user_id=user_id,
    )
    _bind(db, partner)
    return partner


# â”€â”€ Referrals â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def ensure_referral_code(db: Session, user: User, generate_fn: Callable[[Session], str]) -> str:
    """Return the user's existing referral code or generate and persist a new one."""
    existing = getattr(user, "referral_code", None)
    if existing:
        return existing
    code = generate_fn(db)
    user.referral_code = code
    db.add(user)
    db.flush()
    return code


def record_referral_event(
    db: Session,
    *,
    user_id: int,
    event_type: str,
    points: int,
    channel: Optional[str] = None,
    referred_user_id: Optional[int] = None,
) -> ReferralPointEvent:
    """Record a referral point event."""
    event = ReferralPointEvent(
        user_id=user_id,
        event_type=event_type,
        points=points,
        referred_user_id=referred_user_id,
    )
    _bind(db, event)
    return event


def update_user_referral_points(db: Session, referrer: User, referred_user: User, *_) -> User:
    """Hook for adjusting a referrer's referral point balance.

    The controller invokes this with `(db, referrer, referred_user, referred_user)`;
    the trailing duplicate argument is accepted and ignored for forward
    compatibility. Concrete point math lives in the controller layer.
    """
    db.add(referrer)
    db.flush()
    return referrer


def claim_share_points(db: Session, user: User, channel: str, points: int) -> User:
    """Award a daily sharing bonus to a user's referral/sharing point balances."""
    current_referral = int(getattr(user, "referral_points", 0) or 0)
    current_sharing = int(getattr(user, "sharing_points", 0) or 0)
    user.referral_points = current_referral + points
    user.sharing_points = current_sharing + points
    record_referral_event(
        db,
        user_id=int(getattr(user, "id")),
        event_type="share_bonus",
        points=points,
        channel=channel,
    )
    db.add(user)
    db.flush()
    return user


# â”€â”€ Login history / device fingerprint â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_login_history(
    db: Session,
    *,
    user_id: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    success: bool = True,
    country_code: Optional[str] = None,
) -> UserLoginHistory:
    """Write a login history row."""
    entry = UserLoginHistory(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        country_code=country_code,
    )
    _bind(db, entry)
    return entry


def find_user_by_identifier(
    db: Session,
    *,
    email: Optional[str] = None,
    username: Optional[str] = None,
) -> Optional["User"]:
    """Resolve a user by email or username (mirrors the legacy router lookup)."""
    q = db.query(User)
    if email:
        q = q.filter(User.email == email)
    elif username:
        q = q.filter(User.username == username)
    else:
        return None
    user = q.first()
    if user:
        return user
    if username and "@" in username and not email:
        return db.query(User).filter(User.email == username).first()
    return None


def get_user_by_id(db: Session, user_id: int) -> Optional["User"]:
    """Fetch a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def create_registration_user(
    db: Session,
    *,
    email: Optional[str],
    username: Optional[str],
    full_name: Optional[str],
    phone: Optional[str],
    role: str,
    hashed_password: str,
) -> User:
    """Persist a new local-registration user and return the refreshed instance."""
    user = create_user(
        email=email,
        username=username,
        hashed_password=hashed_password,
        role=role,
        phone=phone,
        full_name=full_name,
    )
    create_user_persist(db, user)
    commit_user_registration(db)
    db.refresh(user)
    return user


def record_login_history_commit(
    db: Session,
    *,
    user_id: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    success: bool = True,
    country_code: Optional[str] = None,
) -> None:
    """Write a login-history row and commit the transaction."""
    record_login_history(
        db,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        country_code=country_code,
    )
    db.commit()


def update_user_device_fingerprint(
    db: Session,
    user_id: int,
    fp: str,
    ip: Optional[str],
    ua: Optional[str],
) -> None:
    """Upsert the device fingerprint row for a user's device."""
    device = (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id, UserDevice.device_id == fp)
        .first()
    )
    if device is None:
        device = UserDevice(user_id=user_id, device_id=fp)
        db.add(device)
    device.last_seen_at = utcnow()
    device.is_current = True
    db.flush()


def add_user_device(
    db: Session,
    *,
    user_id: int,
    device_id: str,
    device_type: Optional[str] = None,
    country_code: Optional[str] = None,
) -> UserDevice:
    """Register a new user device."""
    device = UserDevice(
        user_id=user_id,
        device_id=device_id,
        device_type=device_type,
        country_code=country_code,
    )
    _bind(db, device)
    return device


# â”€â”€ TOTP 2FA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def update_user_totp(db: Session, user: User, secret: str, code: str) -> User:
    """Enable TOTP for a user and store the verified secret."""
    user.totp_secret = secret
    user.totp_enabled = True
    db.add(user)
    db.commit()
    db.flush()
    return user


def disable_user_totp(db: Session, user: User, password: str, verify_password) -> User:
    """Disable TOTP after verifying the supplied password."""
    hashed = getattr(user, "hashed_password", None)
    if not verify_password(password, hashed):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Incorrect password")
    user.totp_enabled = False
    user.totp_secret = None
    user.totp_recovery_codes = None
    db.add(user)
    db.commit()
    db.flush()
    return user


__all__ = [
    "create_user",
    "create_user_persist",
    "update_user",
    "update_user_profile",
    "update_user_points",
    "persist_last_login",
    "flush_user",
    "commit_user_registration",
    "create_social_user",
    "update_or_create_social_user",
    "create_email_verification_token",
    "mark_email_verification_token_used",
    "expire_email_verification_token",
    "update_user_email_verification",
    "update_user_email_verified",
    "create_password_reset_token",
    "mark_password_reset_token_used",
    "execute_password_reset",
    "create_supplier_profile",
    "create_logistics_partner",
    "ensure_referral_code",
    "record_referral_event",
    "update_user_referral_points",
    "claim_share_points",
    "record_login_history",
    "find_user_by_identifier",
    "get_user_by_id",
    "create_registration_user",
    "record_login_history_commit",
    "update_user_device_fingerprint",
    "add_user_device",
    "update_user_totp",
    "disable_user_totp",
]


