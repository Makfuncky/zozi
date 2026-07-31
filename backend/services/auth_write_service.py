"""Auth write service — DB write operations for authentication and user management."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

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


def update_user_email_verified(db: Session, user: User) -> User:
    user.email_verified = True
    db.commit()
    db.refresh(user)
    return user


def update_user_email_verification(db: Session, user: User, email_verified: bool = True) -> User:
    user.email_verified = email_verified
    db.commit()
    db.refresh(user)
    return user


def mark_token_expired(db: Session, token: Any) -> None:
    token.used = True
    db.commit()


def create_email_verification_token(
    db: Session, user_id: int, raw_token: str, expires_at: datetime
) -> EmailVerificationToken:
    token = EmailVerificationToken(
        user_id=user_id, token=raw_token, expires_at=expires_at
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def expire_email_verification_token(db: Session, token: EmailVerificationToken) -> None:
    token.expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()


def mark_email_verification_token_used(db: Session, token: EmailVerificationToken) -> None:
    token.used = True
    db.commit()


def create_password_reset_token(
    db: Session, user_id: int, raw_token: str, expires_at: datetime
) -> PasswordResetToken:
    token = PasswordResetToken(user_id=user_id, token=raw_token, expires_at=expires_at)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def mark_password_reset_token_used(db: Session, token: PasswordResetToken) -> None:
    token.used = True
    db.commit()


def expire_password_reset_token(db: Session, token: PasswordResetToken) -> None:
    token.expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()


def execute_password_reset(db: Session, user: User, db_token: PasswordResetToken, hashed_password: str) -> User:
    user.hashed_password = hashed_password
    db_token.used = True
    db.commit()
    db.refresh(user)
    return user


def update_user_preferences(db: Session, user: User, updates: dict) -> User:
    for key, value in updates.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def persist_last_login(db: Session, user: User) -> None:
    user.last_login = datetime.now(timezone.utc)
    db.commit()


def record_login_history(
    db: Session, user_id: int, ip_address: str | None, user_agent: str | None, success: bool = True, country_code: str | None = None
) -> UserLoginHistory:
    history = UserLoginHistory(
        user_id=user_id,
        ip_address=ip_address or "unknown",
        user_agent=user_agent[:500] if user_agent else None,
        timestamp=datetime.now(timezone.utc),
        success=success,
        country_code=country_code,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def add_user_device(
    db: Session,
    user_id: int,
    fingerprint_hash: str,
    device_name: str | None,
    ip_address: str,
    is_trusted: bool = False,
) -> UserDevice:
    device = UserDevice(
        user_id=user_id,
        fingerprint_hash=fingerprint_hash,
        device_name=device_name or "unknown",
        ip_address=ip_address,
        last_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
        is_trusted=is_trusted,
        is_current=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_user_device_fingerprint(
    db: Session, user_id: int, fingerprint_hash: str, ip: str, user_agent: str
) -> UserDevice:
    existing = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == user_id,
            UserDevice.fingerprint_hash == fingerprint_hash,
        )
        .first()
    )
    if existing:
        existing.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None)
        existing.ip_address = ip
        existing.last_user_agent = user_agent
        existing.is_current = True
    else:
        existing = add_user_device(db, user_id, fingerprint_hash, user_agent, ip, is_trusted=False)

    db.query(UserDevice).filter(
        UserDevice.user_id == user_id,
        UserDevice.fingerprint_hash != fingerprint_hash,
    ).update({"is_current": False})

    db.commit()
    return existing


def create_user(db: Session, **user_data) -> User:
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, updates: dict) -> User:
    for key, value in updates.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def record_referral_event(
    db: Session,
    user_id: int,
    event_type: str,
    points: int,
    channel: str | None = None,
    referred_user_id: int | None = None,
) -> ReferralPointEvent:
    event = ReferralPointEvent(
        user_id=user_id,
        event_type=event_type,
        points=points,
        channel=channel,
        referred_user_id=referred_user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_user_referral_code(db: Session, user: User, referral_code: str) -> User:
    user.referral_code = referral_code
    db.commit()
    db.refresh(user)
    return user


def update_user_points(db: Session, user: User, field: str, points: int) -> User:
    current = int(getattr(user, field, 0) or 0)
    setattr(user, field, current + points)
    db.commit()
    db.refresh(user)
    return user


def expire_token(db: Session, token: Any) -> None:
    token.expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()


def ensure_referral_code(db: Session, user: User, generate_func) -> str:
    referral_code = getattr(user, "referral_code", None)
    if referral_code:
        return referral_code
    referral_code = generate_func()
    user.referral_code = referral_code
    db.commit()
    db.refresh(user)
    return referral_code


def create_social_user(
    db: Session,
    email: str,
    username: str,
    hashed_password: str,
    full_name: str | None,
    profile_image: str | None,
    country_code: str,
    referral_code: str,
) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        profile_image=profile_image,
        role="customer",
        country_code=country_code,
        referral_code=referral_code,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_or_create_social_user(
    db: Session,
    email: str,
    name: str | None,
    profile_image: str | None,
    avatar_url: str | None,
) -> User:
    existing = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if existing:
        changed = False
        if not existing.email_verified:
            existing.email_verified = True
            changed = True
        if not existing.full_name and name:
            existing.full_name = name
            changed = True
        if not existing.profile_image and avatar_url:
            existing.profile_image = avatar_url
            changed = True
        if changed:
            db.commit()
            db.refresh(existing)
        return existing
    raise ValueError("User not found")


def update_user_profile(db: Session, user: User, updates: dict) -> User:
    for key, value in updates.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def update_user_totp(db: Session, user: User, secret: str, code: str) -> User:
    user.totp_secret = secret
    user.totp_enabled = True
    user.totp_recovery_codes = [secrets.token_hex(8) for _ in range(8)]
    db.commit()
    db.refresh(user)
    return user


def disable_user_totp(db: Session, user: User, password: str, verify_func) -> User:
    if not verify_func(password, getattr(user, "hashed_password")):
        raise ValueError("Invalid password")
    user.totp_secret = None
    user.totp_enabled = False
    user.totp_recovery_codes = None
    db.commit()
    db.refresh(user)
    return user


def update_user_referral_points(db: Session, user: User, referrer_user: User, new_customer_user: User) -> None:
    user.referral_points = int(getattr(user, "referral_points", 0) or 0) + 100
    new_customer_user.referral_points = int(getattr(new_customer_user, "referral_points", 0) or 0) + 25
    db.commit()


def claim_share_points(db: Session, user: User, channel: str, daily_bonus: int) -> User:
    user.sharing_points = int(getattr(user, "sharing_points", 0) or 0) + daily_bonus
    event = ReferralPointEvent(
        user_id=user.id,
        event_type="share_bonus",
        points=daily_bonus,
        channel=channel,
    )
    db.add(event)
    db.commit()
    db.refresh(user)
    return user


def create_supplier_profile(
    db: Session,
    user_id: int,
    business_name: str | None,
    slug: str,
    business_type: str,
    country: str,
    country_code: str,
    phone_business: str | None,
    website_url: str | None,
) -> SupplierProfile:
    profile = SupplierProfile(
        user_id=user_id,
        business_name=business_name,
        slug=slug,
        business_type=business_type,
        country=country,
        country_code=country_code,
        phone_business=phone_business,
        website_url=website_url,
        is_terms_accepted=True,
        terms_version="1.0",
        verification_status="pending",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def create_logistics_partner(
    db: Session,
    name: str,
    code: str,
    contact_name: str,
    contact_email: str,
    contact_phone: str | None,
    status: str,
    country_code: str,
    user_id: int,
) -> LogisticsPartner:
    partner = LogisticsPartner(
        name=name,
        code=code,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        status=status,
        country_code=country_code,
        user_id=user_id,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def commit_user_registration(db: Session) -> None:
    db.commit()


def flush_user(db: Session, user: User) -> int:
    db.add(user)
    db.flush()
    return user.id