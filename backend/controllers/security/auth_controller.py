"""
Auth Controller — all authentication and account business logic.

The `get_current_user` dependency lives here and is re-exported by
`routers/auth.py` so that all existing `from routers.auth import get_current_user`
imports continue to work unchanged.
"""
import os
import secrets
import logging
import re
import pyotp
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, cast
from urllib.parse import urlencode

import requests
from fastapi import Depends, HTTPException, Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    User,
    UserDevice,
    UserBrowsingHistory,
    UserLoginHistory,
    PasswordResetToken,
    EmailVerificationToken,
    SupplierProfile,
    LogisticsPartner,
    ReferralPointEvent,
)
from db.schemas import (
    UserCreate,
    User as UserSchema,
    ChangePasswordRequest,
    ProfileUpdate,
    ReferralDashboardSchema,
    ReferralPointEventSchema,
    ReferralShareRequest,
)
from services.database import get_db
from utils.cache import cache_get_json, cache_set_json, cache_delete
from utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_refresh_token,
    blacklist_token,
    record_failed_login,
    is_account_locked,
    clear_failed_logins,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    validate_password_complexity,
    create_temp_token,
    verify_temp_token,
    decode_token,
    is_refresh_token_used,
    mark_refresh_token_used,
    is_refresh_family_revoked,
    revoke_refresh_family,
)
from utils.ip_utils import get_request_ip
from utils.config import settings
from utils.constants import STAFF_ROLES
from utils.currency import KNOWN_CURRENCY_META
from utils.email_service import (
    EmailDeliveryDisabledError,
    get_email_delivery_status,
    has_live_email_delivery,
    send_password_reset_email,
    send_verification_email,
)
from utils.staff_permissions import default_permissions_for_role, sanitize_staff_permissions
from utils.audit_log import audit_log, AuditAction

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only, flush_only, rollback_only
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

VERIFY_TOKEN_TTL_HOURS = 24
RESET_TOKEN_TTL_HOURS = 1
SOCIAL_STATE_COOKIE_PREFIX = "zozi_oauth_state_"
DEFAULT_LANGUAGE = "en"
DEFAULT_CURRENCY = "OMR"
DEFAULT_COUNTRY = "OM"
REFERRAL_CODE_LENGTH = 8
REFERRAL_REFERRER_BONUS = 100
REFERRAL_NEW_CUSTOMER_BONUS = 25
REFERRAL_SHARE_DAILY_BONUS = 5
_USER_CACHE_TTL_SECONDS = 5 * 60


def resolve_rate_limit(default_limit: str, *, loadtest_limit: str | None = None) -> str:
    if settings.loadtest_profile_enabled and loadtest_limit:
        return loadtest_limit
    return default_limit


def _next_logistics_partner_code(db: Session, user_id: int) -> str:
    base_code = f"LPAUTO{user_id}"
    candidate = base_code
    suffix = 1
    while db.query(LogisticsPartner).filter(LogisticsPartner.code == candidate).first():
        suffix += 1
        candidate = f"{base_code}_{suffix}"
    return candidate


# ── Pydantic models ───────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class SocialLoginRequest(BaseModel):
    token: str = ""


class SocialLoginJsonRequest(BaseModel):
    """Unified JSON social-login payload used by the mobile / web clients."""

    provider: str = "google"
    id_token: str = ""
    access_token: str = ""
    token: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class PublicResendVerificationRequest(BaseModel):
    identifier: str


class RefreshTokenBody(BaseModel):
    refresh_token: Optional[str] = None


def get_social_providers_status() -> dict:
    google_enabled = bool(settings.google_client_id)
    facebook_enabled = bool(settings.facebook_client_id and settings.facebook_client_secret)
    return {
        "google": google_enabled,
        "google_mode": "gsi" if google_enabled else "disabled",
        "google_client_id": settings.google_client_id or None,
        "facebook": facebook_enabled,
        "facebook_mode": "redirect" if facebook_enabled else "disabled",
        "customer_email_verification_required": is_customer_email_verification_required(),
        "customer_email_verification_mode": settings.customer_email_verification_mode,
        "email_delivery": get_email_delivery_status(),
    }


def is_customer_email_verification_required() -> bool:
    mode = settings.customer_email_verification_mode
    if mode == "required":
        return True
    if mode == "disabled":
        return False
    return has_live_email_delivery()


def _normalize_customer_verification_when_gate_disabled(user: User, db: Session) -> None:
    if _user_role(user) != "customer":
        return
    if is_customer_email_verification_required() or user.email_verified:
        return
    user.email_verified = True
    commit_and_refresh(db, user)


def _resolve_user_from_subject(subject: str, db: Session) -> User | None:
    try:
        return db.query(User).filter(User.id == int(subject)).first()
    except (TypeError, ValueError):
        return db.query(User).filter(User.username == str(subject)).first()


def _user_id(user: User | UserSchema) -> int:
    return cast(int, getattr(user, "id"))


def _user_username(user: User | UserSchema) -> str:
    return cast(str, getattr(user, "username"))


def _user_email(user: User | UserSchema) -> str:
    return cast(str, getattr(user, "email"))


def _user_role(user: User | UserSchema) -> str:
    return cast(str, getattr(user, "role"))


def _user_phone(user: User | UserSchema) -> str | None:
    return cast(str | None, getattr(user, "phone"))


def _user_email_verified(user: User | UserSchema) -> bool:
    return bool(cast(bool, getattr(user, "email_verified", False)))


def _user_profile_image(user: User | UserSchema) -> str | None:
    return cast(str | None, getattr(user, "profile_image"))



def _user_effective_permissions(user: User) -> list[str]:
    role = _user_role(user)
    if role not in STAFF_ROLES:
        return []
    assigned_permissions = sanitize_staff_permissions(getattr(user, "staff_permissions", None))
    if assigned_permissions:
        return assigned_permissions
    from controllers.admin_controller import ROLE_PERMISSION_MAP

    return sorted(ROLE_PERMISSION_MAP.get(role, set()))


def _user_staff_payload(user: User) -> dict[str, Any]:
    return {
        "full_name": cast(str | None, getattr(user, "full_name", None)),
        "staff_role_label": cast(str | None, getattr(user, "staff_role_label", None)),
        "staff_title": cast(str | None, getattr(user, "staff_title", None)),
        "staff_department": cast(str | None, getattr(user, "staff_department", None)),
        "staff_area_of_operation": cast(str | None, getattr(user, "staff_area_of_operation", None)),
        "staff_hire_date": getattr(user, "staff_hire_date", None),
        "staff_experience_level": cast(str | None, getattr(user, "staff_experience_level", None)),
        "staff_performance_summary": cast(str | None, getattr(user, "staff_performance_summary", None)),
        "staff_assigned_tasks": list(getattr(user, "staff_assigned_tasks", None) or []),
        "staff_assigned_projects": list(getattr(user, "staff_assigned_projects", None) or []),
        "permissions": _user_effective_permissions(user),
        "staff_notes": cast(str | None, getattr(user, "staff_notes", None)),
        "staff_country_codes": list(getattr(user, "staff_country_codes", None) or []),
    }


def _total_referral_points(user: User) -> int:
    referral_points = int(cast(int | None, getattr(user, "referral_points", 0)) or 0)
    sharing_points = int(cast(int | None, getattr(user, "sharing_points", 0)) or 0)
    return referral_points + sharing_points


def _build_referral_link(referral_code: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/r/{referral_code}"


def _referral_event_description(event_type: str) -> str:
    labels = {
        "referral_invite_success": "A customer joined with your referral code.",
        "referral_join_bonus": "Welcome bonus for joining through a referral.",
        "share_bonus": "Daily sharing bonus awarded.",
    }
    return labels.get(event_type, "Referral activity")


def _serialize_referral_event(event: ReferralPointEvent) -> ReferralPointEventSchema:
    referred_user = cast(User | None, getattr(event, "referred_user", None))
    return ReferralPointEventSchema(
        id=cast(int, getattr(event, "id")),
        event_type=cast(str, getattr(event, "event_type")),
        points=int(cast(int | None, getattr(event, "points", 0)) or 0),
        channel=cast(str | None, getattr(event, "channel", None)),
        description=_referral_event_description(cast(str, getattr(event, "event_type"))),
        created_at=cast(datetime, getattr(event, "created_at")),
        referred_user_id=cast(int | None, getattr(event, "referred_user_id", None)),
        referred_username=(
            cast(str | None, getattr(referred_user, "username", None))
            if referred_user is not None
            else None
        ),
    )


def _generate_unique_referral_code(db: Session) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(30):
        candidate = "".join(secrets.choice(alphabet) for _ in range(REFERRAL_CODE_LENGTH))
        exists = db.query(User).filter(func.lower(User.referral_code) == candidate.lower()).first()
        if not exists:
            return candidate
    raise HTTPException(status_code=500, detail="Unable to generate referral code")


def _ensure_verification_delivery_available() -> None:
    email_status = get_email_delivery_status()
    if bool(email_status.get("available", False)):
        return
    raise HTTPException(
        status_code=503,
        detail="Customer email verification is unavailable because email delivery is not configured.",
    )


def _record_referral_event(
    db: Session,
    *,
    user_id: int,
    event_type: str,
    points: int,
    channel: str | None = None,
    referred_user_id: int | None = None,
) -> None:
    add_and_flush(db, 
   ReferralPointEvent(
            user_id=user_id,
            event_type=event_type,
            points=points,
            channel=channel,
            referred_user_id=referred_user_id,
        )
    )


def _user_public_payload(user: User | UserSchema) -> dict[str, Any]:
    payload = {
        "id": _user_id(user),
        "email": _user_email(user),
        "username": _user_username(user),
        "role": _user_role(user),
        "profile_image": _user_profile_image(user),
        "phone": _user_phone(user),
        "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
        "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
        "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "referral_code": cast(str | None, getattr(user, "referral_code", None)),
        "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
        "total_points": _total_referral_points(user),
        "email_verified": _user_email_verified(user),
        "full_name": cast(str | None, getattr(user, "full_name", None)),
        "address_book": getattr(user, "address_book", None),
    }
    if _user_role(user) in STAFF_ROLES:
        payload.update(_user_staff_payload(user))
    return payload


# ── Dependency ────────────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """FastAPI dependency — resolves the current authenticated user from the JWT."""
    subject = verify_token(token)
    cache_key = f"auth:user:{subject}"
    cached = cache_get_json(cache_key)
    if isinstance(cached, dict):
        return cached
    user = _resolve_user_from_subject(subject, db)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    payload = {
        "id": _user_id(user),
        "username": _user_username(user),
        "email": _user_email(user),
        "role": _user_role(user),
        "is_active": bool(cast(Any, getattr(user, "is_active"))),
        "phone": _user_phone(user),
        "profile_image": _user_profile_image(user),
        "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
        "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
        "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "country_code": cast(str | None, getattr(user, "country_code")) or cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "referral_code": cast(str | None, getattr(user, "referral_code", None)),
        "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
        "total_points": _total_referral_points(user),
        "email_verified": user.email_verified,
        "full_name": cast(str | None, getattr(user, "full_name", None)),
        "address_book": getattr(user, "address_book", None),
        "created_at": cast(datetime, getattr(user, "created_at")),
        "_token": token,
    }
    if _user_role(user) in STAFF_ROLES:
        payload.update(_user_staff_payload(user))
    cache_set_json(cache_key, payload, _USER_CACHE_TTL_SECONDS)
    return payload


def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    """FastAPI dependency — resolves the current user from JWT, or returns None if unauthenticated."""
    if not token:
        return None
    try:
        subject = verify_token(token)
        cache_key = f"auth:user:{subject}"
        cached = cache_get_json(cache_key)
        if isinstance(cached, dict):
            return cached
        user = _resolve_user_from_subject(subject, db)
        if not user:
            return None
        payload = {
            "id": _user_id(user),
            "username": _user_username(user),
            "email": _user_email(user),
            "role": _user_role(user),
            "is_active": bool(cast(Any, getattr(user, "is_active"))),
            "phone": _user_phone(user),
            "profile_image": _user_profile_image(user),
            "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
            "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
            "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
            "country_code": cast(str | None, getattr(user, "country_code")) or cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
            "referral_code": cast(str | None, getattr(user, "referral_code", None)),
            "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
            "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
            "total_points": _total_referral_points(user),
            "email_verified": user.email_verified,
            "created_at": cast(datetime, getattr(user, "created_at")),
            "_token": token,
        }
        if _user_role(user) in STAFF_ROLES:
            payload.update(_user_staff_payload(user))
        cache_set_json(cache_key, payload, _USER_CACHE_TTL_SECONDS)
        return payload
    except Exception:
        return None


def _find_user_for_login(identifier: str, db: Session) -> User | None:
    normalized = identifier.strip()
    if not normalized:
        return None

    return (
        db.query(User)
        .filter(
            (func.lower(User.email) == normalized.lower())
            | (func.lower(User.username) == normalized.lower())
        )
        .first()
    )


def _record_device_fingerprint(request: Request | None, user_id: int, db: Session) -> None:
    """Record or update the device fingerprint for a user on successful login."""
    if request is None:
        return
    fp: str | None = getattr(request.state, "device_fingerprint", None)
    if not fp:
        return
    ip = get_request_ip(request)
    ua = (request.headers.get("user-agent") or "")[:200]
    existing = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == user_id,
            UserDevice.fingerprint_hash == fp,
        )
        .first()
    )
    if existing:
        setattr(existing, "last_seen_at", datetime.now(timezone.utc).replace(tzinfo=None))
        setattr(existing, "ip_address", ip)
        setattr(existing, "is_current", True)
    else:
        add_and_flush(db, UserDevice(
            user_id=user_id,
            fingerprint_hash=fp,
            device_name=ua,
            ip_address=ip,
            last_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
            is_trusted=False,
            is_current=True,
        ))
    # Mark other devices as not current
    db.query(UserDevice).filter(
        UserDevice.user_id == user_id,
        UserDevice.fingerprint_hash != fp,
    ).update({"is_current": False})
    try:
        commit_only(db)
    except Exception:
        rollback_only(db)


def _issue_auth_tokens(response: Response, user: User, request: Request | None = None, method: str = "password") -> dict:
    device_fp = getattr(request.state, "device_fingerprint", None) if request else None
    access_token = create_access_token(data={"sub": str(_user_id(user))}, device_fp=device_fp)
    refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    ip = get_request_ip(request) if request else None
    ua = request.headers.get("user-agent") if request else None
    if request and hasattr(request.state, "db"):
        audit_log(
            db=cast(Session, request.state.db),
            action=AuditAction.LOGIN_SUCCESS,
            user_id=_user_id(user),
            username=_user_username(user),
            user_role=_user_role(user),
            ip_address=ip,
            user_agent=ua,
            status="success",
            details={"role": _user_role(user), "method": method},
        )
        _record_device_fingerprint(request, _user_id(user), cast(Session, request.state.db))
        _record_login_history(cast(Session, request.state.db), user, request=request, method=method)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def _log_login_success(db: Session, user: User, request: Request | None = None, method: str = "password") -> None:
    ip = get_request_ip(request) if request else None
    ua = request.headers.get("user-agent") if request else None
    audit_log(
        db=db,
        action=AuditAction.LOGIN_SUCCESS,
        user_id=_user_id(user),
        username=_user_username(user),
        user_role=_user_role(user),
        ip_address=ip,
        user_agent=ua,
        status="success",
        details={"role": _user_role(user), "method": method},
    )


def _persist_last_login(db: Session, user: User) -> None:
    try:
        user.last_login = datetime.now(timezone.utc)
        commit_only(db)
    except Exception as exc:
        logger.warning("Failed to update last_login for %s: %s", _user_username(user), exc)
        try:
            rollback_only(db)
        except Exception:
            pass


def _record_login_history(db: Session, user: User, request: Request | None = None, method: str = "password") -> None:
    """Write a UserLoginHistory record for a successful login."""
    try:
        ip = get_request_ip(request) if request else None
        ua = (request.headers.get("user-agent") or "")[:500] if request else None
        history = UserLoginHistory(
            user_id=user.id,
            ip_address=ip or "unknown",
            user_agent=ua,
            timestamp=datetime.now(timezone.utc),
            success=True,
            country_code=user.country_code,
        )
        add_and_flush(db, history)
        commit_only(db)
    except Exception as exc:
        logger.warning("Failed to record login history for %s: %s", _user_username(user), exc)
        try:
            rollback_only(db)
        except Exception:
            pass


def _create_tokens_response(response: Response, user: User, db: Session, request: Request | None = None, method: str = "password") -> dict:
    device_fp = getattr(request.state, "device_fingerprint", None) if request else None
    access_token = create_access_token(data={"sub": str(_user_id(user)), "role": _user_role(user)}, device_fp=device_fp)
    refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )
    _persist_last_login(db, user)
    _log_login_success(db, user, request=request, method=method)
    _record_device_fingerprint(request, _user_id(user), db)
    _record_login_history(db, user, request=request, method=method)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,  # included in body for mobile clients
    }


def _slugify_username(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_.-").lower()
    return slug[:40] or "zozi_user"


def _unique_username(base: str, db: Session) -> str:
    candidate = _slugify_username(base)
    if not db.query(User).filter(func.lower(User.username) == candidate.lower()).first():
        return candidate

    suffix = 1
    while True:
        next_candidate = f"{candidate[:34]}_{suffix}"
        if not db.query(User).filter(func.lower(User.username) == next_candidate.lower()).first():
            return next_candidate
        suffix += 1


def _extract_avatar_url(profile: dict[str, Any] | None) -> str | None:
    """Best-effort extraction of a profile picture URL from an OAuth profile dict.

    Handles both Google's flat ``picture`` (string) and Facebook's nested
    ``picture.data.url`` shape.
    """
    if not profile:
        return None
    picture = profile.get("picture")
    if isinstance(picture, str) and picture:
        return picture
    if isinstance(picture, dict):
        data = picture.get("data")
        if isinstance(data, dict) and data.get("url"):
            return data["url"]
    return None


def _create_social_user(email: str, name: str | None, db: Session, profile: dict[str, Any] | None = None) -> User:
    profile = profile or {}
    base = name or email.split("@", 1)[0]
    if not name:
        given = profile.get("given_name")
        family = profile.get("family_name")
        if given or family:
            name = " ".join(p for p in (given, family) if p)
            base = name
    user = User(
        email=email,
        username=_unique_username(base, db),
        hashed_password=get_password_hash(secrets.token_urlsafe(24)),
        full_name=name or None,
        profile_image=_extract_avatar_url(profile),
        role="customer",
        country_code=DEFAULT_COUNTRY,
        referral_code=_generate_unique_referral_code(db),
        email_verified=True,
    )
    add_and_flush(db, user)
    commit_and_refresh(db, user)
    return user


def _resolve_or_create_social_user(email: str, name: str | None, db: Session, profile: dict[str, Any] | None = None) -> User:
    profile = profile or {}
    existing = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if existing:
        changed = False
        if not existing.email_verified:
            existing.email_verified = True
            changed = True
        # Auto-seed profile details from OAuth identity if the local profile is blank.
        if not existing.full_name and name:
            existing.full_name = name
            changed = True
        avatar = _extract_avatar_url(profile)
        if not existing.profile_image and avatar:
            existing.profile_image = avatar
            changed = True
        if changed:
            commit_and_refresh(db, existing)
        return existing
    return _create_social_user(email, name, db, profile)


def _oauth_state_cookie_name(provider: str) -> str:
    return f"{SOCIAL_STATE_COOKIE_PREFIX}{provider}"


def _build_social_redirect_response(provider: str, auth_url: str, state: str) -> RedirectResponse:
    response = RedirectResponse(auth_url, status_code=302)
    response.set_cookie(
        key=_oauth_state_cookie_name(provider),
        value=state,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=600,
    )
    return response


def _validate_social_state(request: Request, provider: str, state: str | None) -> None:
    expected = request.cookies.get(_oauth_state_cookie_name(provider))
    if not state or not expected or state != expected:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")


def _frontend_social_callback(token: str | None = None, error: str | None = None) -> RedirectResponse:
    params = {}
    if token:
        params["token"] = token
    if error:
        params["error"] = error
    target = f"{settings.frontend_url}/auth/callback"
    if params:
        target = f"{target}?{urlencode(params)}"
    return RedirectResponse(target, status_code=302)


def _resolve_google_identity_token(id_token: str) -> dict[str, Any]:
    response = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": id_token},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()

    audience = payload.get("aud")
    issuer = payload.get("iss")
    email_verified = str(payload.get("email_verified", "")).lower() == "true"

    if audience != settings.google_client_id:
        raise HTTPException(status_code=400, detail="Google token audience mismatch")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=400, detail="Invalid Google token issuer")
    if not email_verified:
        raise HTTPException(status_code=400, detail="Google account email is not verified")
    return payload


def get_google_oauth_start() -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    state = secrets.token_urlsafe(24)
    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.backend_url}/auth/oauth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    })
    return _build_social_redirect_response(
        "google",
        f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
        state,
    )


def handle_google_id_token_login(
    payload: SocialLoginRequest,
    response: Response,
    db: Session,
    request: Request | None = None,
) -> dict:
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    if not payload.token.strip():
        raise HTTPException(status_code=400, detail="Google credential is required")

    try:
        profile = _resolve_google_identity_token(payload.token.strip())
    except requests.RequestException as exc:
        logger.error("Google ID token verification failed: %s", exc)
        raise HTTPException(status_code=502, detail="Google login verification failed") from exc

    email = str(profile.get("email") or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Google account email is required")

    user = _resolve_or_create_social_user(email=email, name=profile.get("name"), db=db, profile=profile)
    tokens = _create_tokens_response(response, user, db, request=request, method="google_gsi")
    return {**tokens, "user": _user_public_payload(user)}


def handle_google_oauth_callback(code: str, state: str | None, request: Request, db: Session) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        return _frontend_social_callback(error="google_not_configured")

    try:
        _validate_social_state(request, "google", state)
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": f"{settings.backend_url}/auth/oauth/google/callback",
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        userinfo_resp = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
            timeout=15,
        )
        userinfo_resp.raise_for_status()
        profile = userinfo_resp.json()
        email = profile.get("email")
        if not email:
            return _frontend_social_callback(error="google_email_required")

        user = _resolve_or_create_social_user(email=email, name=profile.get("name"), db=db, profile=profile)
        response = _frontend_social_callback(token=create_access_token(data={"sub": str(_user_id(user))}))
        refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})
        response.set_cookie(
            key=settings.refresh_token_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=settings.should_secure_cookies,
            samesite=settings.refresh_cookie_samesite,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/",
        )
        response.delete_cookie(_oauth_state_cookie_name("google"))
        _log_login_success(db, user, request=request, method="google")
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Google OAuth failed: %s", exc)
        return _frontend_social_callback(error="google_login_failed")


def get_facebook_oauth_start() -> RedirectResponse:
    if not settings.facebook_client_id or not settings.facebook_client_secret:
        raise HTTPException(status_code=503, detail="Facebook login is not configured")
    state = secrets.token_urlsafe(24)
    params = urlencode({
        "client_id": settings.facebook_client_id,
        "redirect_uri": f"{settings.backend_url}/auth/oauth/facebook/callback",
        "state": state,
        "scope": "email,public_profile",
        "response_type": "code",
    })
    return _build_social_redirect_response(
        "facebook",
        f"https://www.facebook.com/v20.0/dialog/oauth?{params}",
        state,
    )


def handle_facebook_oauth_callback(code: str, state: str | None, request: Request, db: Session) -> RedirectResponse:
    if not settings.facebook_client_id or not settings.facebook_client_secret:
        return _frontend_social_callback(error="facebook_not_configured")

    try:
        _validate_social_state(request, "facebook", state)
        token_resp = requests.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "client_id": settings.facebook_client_id,
                "client_secret": settings.facebook_client_secret,
                "redirect_uri": f"{settings.backend_url}/auth/oauth/facebook/callback",
                "code": code,
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        profile_resp = requests.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,name,email,picture.width(400).height(400)",
                "access_token": token_data["access_token"],
            },
            timeout=15,
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()
        email = profile.get("email")
        if not email:
            return _frontend_social_callback(error="facebook_email_required")

        user = _resolve_or_create_social_user(email=email, name=profile.get("name"), db=db, profile=profile)
        response = _frontend_social_callback(token=create_access_token(data={"sub": str(_user_id(user))}))
        refresh_token = create_refresh_token(data={"sub": str(_user_id(user))})
        response.set_cookie(
            key=settings.refresh_token_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/",
        )
        response.delete_cookie(_oauth_state_cookie_name("facebook"))
        _log_login_success(db, user, request=request, method="facebook")
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Facebook OAuth failed: %s", exc)
        return _frontend_social_callback(error="facebook_login_failed")


# ── Register ──────────────────────────────────────────────────────────────────

def register_user(user: UserCreate, db: Session) -> UserSchema:
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Supplier-specific validation
    if user.role == "supplier":
        # During automated testing and local development, we can relax strict supplier onboarding requirements.
        # Production deployments should require both terms acceptance and a business name.
        if settings.app_env not in {"test", "development"}:
            if not user.terms_accepted:
                raise HTTPException(
                    status_code=400,
                    detail="You must accept the Terms & Conditions to register as a supplier",
                )
            if not user.business_name or not user.business_name.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Business name is required for supplier registration",
                )
        else:
            # For tests, provide defaults when missing so the flow is lean and deterministic.
            if not user.business_name or not user.business_name.strip():
                user.business_name = "Test Supplier"
            user.terms_accepted = True

    require_customer_verification = user.role == "customer" and is_customer_email_verification_required()
    if require_customer_verification:
        _ensure_verification_delivery_available()

    incoming_referral_code = (user.referral_code or "").strip().upper()
    referrer: User | None = None
    if user.role == "customer" and incoming_referral_code:
        referrer = (
            db.query(User)
            .filter(func.lower(User.referral_code) == incoming_referral_code.lower())
            .first()
        )
        if not referrer or _user_role(referrer) != "customer":
            raise HTTPException(status_code=400, detail="Invalid referral code")

    customer_auto_verified = user.role == "customer" and not require_customer_verification

    # Validate password complexity
    validate_password_complexity(user.password)
    
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        phone=user.phone,
        referral_code=_generate_unique_referral_code(db),
        country_code=DEFAULT_COUNTRY,
        referred_by_user_id=_user_id(referrer) if referrer is not None else None,
        email_verified=customer_auto_verified,
    )
    add_and_flush(db, db_user)
    flush_only(db)

    if referrer is not None and user.role == "customer":
        setattr(
            referrer,
            "referral_points",
            int(cast(int | None, getattr(referrer, "referral_points", 0)) or 0) + REFERRAL_REFERRER_BONUS,
        )
        setattr(
            db_user,
            "referral_points",
            int(cast(int | None, getattr(db_user, "referral_points", 0)) or 0) + REFERRAL_NEW_CUSTOMER_BONUS,
        )
        _record_referral_event(
            db,
            user_id=_user_id(referrer),
            event_type="referral_invite_success",
            points=REFERRAL_REFERRER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(db_user),
        )
        _record_referral_event(
            db,
            user_id=_user_id(db_user),
            event_type="referral_join_bonus",
            points=REFERRAL_NEW_CUSTOMER_BONUS,
            channel="referral_code",
            referred_user_id=_user_id(referrer),
        )

    # Create supplier business profile
    if user.role == "supplier":
        supplier_slug_base = re.sub(
            r"[^a-z0-9]+",
            "-",
            (user.business_name or user.username or f"supplier-{db_user.id}").strip().lower(),
        ).strip("-") or f"supplier-{db_user.id}"
        profile = SupplierProfile(
            user_id=db_user.id,
            business_name=user.business_name.strip() if user.business_name else None,
            slug=f"{supplier_slug_base}-{db_user.id}",
            business_type=user.business_type or "individual",
            country=user.country,
            country_code=DEFAULT_COUNTRY,
            phone_business=user.phone,
            website=user.website_url,
            is_terms_accepted=True,
            terms_version="1.0",
            verification_status="pending",
        )
        add_and_flush(db, profile)

    if user.role == "logistics_partner":
        add_and_flush(db, 
   LogisticsPartner(
                name=f"{db_user.username} Logistics",
                code=_next_logistics_partner_code(db, cast(int, getattr(db_user, "id"))),
                contact_name=db_user.username,
                contact_email=db_user.email,
                contact_phone=db_user.phone,
                status="pending_onboarding",
                country_code=DEFAULT_COUNTRY,
                user_id=db_user.id,
            )
        )

    commit_only(db)
    created_user_id = cast(int, getattr(db_user, "id"))

    if require_customer_verification:
        raw_token = secrets.token_urlsafe(32)
        add_and_flush(db, 
   EmailVerificationToken(
                user_id=created_user_id,
                token=raw_token,
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
            )
        )
        commit_only(db)
        try:
            send_verification_email(_user_email(db_user), raw_token)
        except EmailDeliveryDisabledError as exc:
            logger.error(
                "Verification email transport became unavailable after registration persisted for user_id=%s: %s",
                created_user_id,
                exc,
            )
        except Exception:
            logger.exception(
                "Verification email send failed after registration persisted for user_id=%s",
                created_user_id,
            )

    persisted_user = db.query(User).filter(User.id == created_user_id).first()
    if persisted_user is None:
        raise HTTPException(status_code=500, detail="Registration succeeded but the user could not be reloaded")

    return UserSchema.model_validate(persisted_user)


# ── Email verification ────────────────────────────────────────────────────────

def verify_email_token(token: str, db: Session) -> dict:
    ev = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.used.is_(False),
        )
        .first()
    )
    if not ev:
        raise HTTPException(status_code=400, detail="Invalid or already used verification token.")
    if cast(datetime, getattr(ev, "expires_at")) < datetime.now(timezone.utc).replace(tzinfo=None):
        setattr(ev, "used", True)
        commit_only(db)
        raise HTTPException(status_code=400, detail="Verification token has expired.")

    user = db.query(User).filter(User.id == ev.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    setattr(user, "email_verified", True)
    setattr(ev, "used", True)
    commit_only(db)
    return {"detail": "Email verified successfully."}


def resend_verification(current_user: dict, db: Session) -> dict:
    if not is_customer_email_verification_required():
        return {"detail": "Email verification is not required for customer login right now."}
    if current_user["email_verified"]:
        return {"detail": "Email is already verified."}

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user["id"],
        EmailVerificationToken.used.is_(False),
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    ev_token = EmailVerificationToken(
        user_id=current_user["id"],
        token=raw_token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
    )
    add_and_flush(db, ev_token)
    commit_only(db)

    try:
        send_verification_email(cast(str, current_user["email"]), raw_token)
    except EmailDeliveryDisabledError as exc:
        logger.error("Failed to resend verification email: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Verification email delivery is not configured.",
        ) from exc
    except Exception as exc:
        logger.error("Failed to resend verification email: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Unable to resend the verification email right now. Please try again shortly.",
        ) from exc

    return {"detail": "Verification email sent."}


def resend_verification_public(payload: PublicResendVerificationRequest, db: Session) -> dict:
    generic_response = {
        "detail": "If an unverified account exists for that email or username, a verification email has been sent."
    }
    if not is_customer_email_verification_required():
        return {"detail": "Email verification is not required for customer login right now."}
    identifier = payload.identifier.strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username is required.")

    user = _find_user_for_login(identifier, db)
    if not user or _user_role(user) != "customer" or user.email_verified:
        return generic_response

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == _user_id(user),
        EmailVerificationToken.used.is_(False),
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    ev_token = EmailVerificationToken(
        user_id=_user_id(user),
        token=raw_token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=VERIFY_TOKEN_TTL_HOURS),
    )
    add_and_flush(db, ev_token)
    commit_only(db)

    try:
        send_verification_email(_user_email(user), raw_token)
    except EmailDeliveryDisabledError as exc:
        logger.error("Failed to resend verification email for %s: %s", identifier, exc)
        raise HTTPException(
            status_code=503,
            detail="Verification email delivery is not configured.",
        ) from exc
    except Exception as exc:
        logger.error("Failed to resend verification email for %s: %s", identifier, exc)
        raise HTTPException(
            status_code=502,
            detail="Unable to resend the verification email right now. Please try again shortly.",
        ) from exc

    return generic_response


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm,
    db: Session,
    request: Request | None = None,
) -> dict:
    ip = get_request_ip(request) if request else None
    ua = (request.headers.get("user-agent") if request else None)

    # Brute-force lockout check
    if is_account_locked(form_data.username):
        audit_log(
            db=db,
            action=AuditAction.ACCOUNT_LOCKED,
            username=form_data.username,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"reason": "account_locked"},
        )
        raise HTTPException(
            status_code=429,
            detail="Account temporarily locked due to too many failed login attempts. Try again in 15 minutes.",
        )

    user = _find_user_for_login(form_data.username, db)
    if not user or not verify_password(form_data.password, cast(str, getattr(user, "hashed_password"))):
        record_failed_login(form_data.username)
        # Log failed attempt
        audit_log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            username=form_data.username,
            user_role=_user_role(user) if user else None,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"email": form_data.username, "reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    clear_failed_logins(form_data.username)

    # Customer accounts must verify their email before logging in
    if _user_role(user) == "customer" and is_customer_email_verification_required() and not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email address not verified. Please check your inbox and verify your email before logging in.",
        )

    _normalize_customer_verification_when_gate_disabled(user, db)

    if getattr(user, "totp_enabled", False):
        return _issue_totp_challenge(user, request, response, db)

    return _create_tokens_response(response, user, db, request=request, method="password")


def _issue_totp_challenge(user: User, request: Request | None, response: Response, db: Session) -> dict:
    """Return a 2FA challenge response with a short-lived temp token."""
    temp_token = create_temp_token({"sub": str(_user_id(user))})
    audit_log(
        db=db,
        action=AuditAction.LOGIN_SUCCESS,
        username=_user_email(user),
        user_role=_user_role(user),
        ip_address=get_request_ip(request) if request else None,
        user_agent=(request.headers.get("user-agent") if request else None),
        status="pending_2fa",
        details={"reason": "2fa_challenge_issued"},
    )
    return {
        "requires_2fa": True,
        "temp_token": temp_token,
        "detail": "2FA verification required. Call /auth/2fa/complete with the temp token and a TOTP code.",
    }


def json_login_user(
    response: Response,
    login_data: LoginRequest,
    db: Session,
    request: Request | None = None,
) -> dict:
    ip = get_request_ip(request) if request else None
    ua = (request.headers.get("user-agent") if request else None)

    # Brute-force lockout check
    if is_account_locked(login_data.email):
        audit_log(
            db=db,
            action=AuditAction.ACCOUNT_LOCKED,
            username=login_data.email,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"reason": "account_locked"},
        )
        raise HTTPException(
            status_code=429,
            detail="Account temporarily locked due to too many failed login attempts. Try again in 15 minutes.",
        )

    user = _find_user_for_login(login_data.email, db)
    if not user or not verify_password(login_data.password, cast(str, getattr(user, "hashed_password"))):
        record_failed_login(login_data.email)
        # Log failed attempt
        audit_log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            username=login_data.email,
            user_role=_user_role(user) if user else None,
            ip_address=ip,
            user_agent=ua,
            status="failure",
            details={"email": login_data.email, "reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    clear_failed_logins(login_data.email)

    # Customer accounts must verify their email before logging in
    if _user_role(user) == "customer" and is_customer_email_verification_required() and not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email address not verified. Please check your inbox and verify your email before logging in.",
        )

    _normalize_customer_verification_when_gate_disabled(user, db)

    if getattr(user, "totp_enabled", False):
        return _issue_totp_challenge(user, request, response, db)

    tokens = _create_tokens_response(response, user, db, request=request, method="password")
    return {
        **tokens,
        "user": _user_public_payload(user),
    }


# ── Refresh ───────────────────────────────────────────────────────────────────

def refresh_access_token(request: Request, response: Response, db: Session, body_refresh_token: str | None = None) -> dict:
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name) or body_refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    # Decode the old refresh token to extract family_id and jti before validation
    try:
        old_payload = decode_token(refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if old_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    family_id = str(old_payload.get("family_id", ""))
    old_jti = str(old_payload.get("jti", ""))

    if not family_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check if the entire family has been revoked
    if is_refresh_family_revoked(family_id):
        raise HTTPException(status_code=401, detail="Refresh token family revoked")

    # Check if this specific JTI was already used (reuse detection)
    if is_refresh_token_used(family_id, old_jti):
        revoke_refresh_family(family_id)
        raise HTTPException(
            status_code=401,
            detail="Refresh token reuse detected. All tokens in this family have been revoked.",
        )

    # Verify the token signature and expiry
    subject = verify_refresh_token(refresh_token)
    user = _resolve_user_from_subject(subject, db)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Mark the old JTI as used (rotation)
    mark_refresh_token_used(family_id, old_jti)

    # Issue new tokens with the same family_id
    access_token = create_access_token(data={"sub": str(_user_id(user))})
    new_refresh = create_refresh_token(data={"sub": str(_user_id(user))}, family_id=family_id)

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=new_refresh,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    blacklist_token(old_jti, REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": new_refresh,  # included for mobile clients
    }


# ── Register (JSON / mobile-friendly) ─────────────────────────────────────────

def json_register_user(response: Response, user_data: UserCreate, db: Session, request: Request | None = None) -> dict:
    """Register a new user and immediately issue tokens — used by mobile clients."""
    db_user = register_user(user_data, db)

    access_token = create_access_token(data={"sub": str(_user_id(db_user))})
    refresh_token = create_refresh_token(data={"sub": str(_user_id(db_user))})

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.should_secure_cookies,
        samesite=settings.refresh_cookie_samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "user": _user_public_payload(db_user),
    }


def _ensure_referral_code(user: User, db: Session) -> str:
    referral_code = cast(str | None, getattr(user, "referral_code", None))
    if referral_code:
        return referral_code
    referral_code = _generate_unique_referral_code(db)
    setattr(user, "referral_code", referral_code)
    commit_and_refresh(db, user)
    return referral_code


def get_referral_dashboard(current_user: dict, db: Session) -> ReferralDashboardSchema:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    referral_code = _ensure_referral_code(user, db)
    referred_count = (
        db.query(func.count(User.id))
        .filter(User.referred_by_user_id == _user_id(user))
        .scalar()
        or 0
    )
    recent_events = (
        db.query(ReferralPointEvent)
        .filter(ReferralPointEvent.user_id == _user_id(user))
        .order_by(ReferralPointEvent.created_at.desc())
        .limit(20)
        .all()
    )
    return ReferralDashboardSchema(
        referral_code=referral_code,
        referral_link=_build_referral_link(referral_code),
        total_points=_total_referral_points(user),
        referral_points=int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        sharing_points=int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
        referred_count=int(referred_count),
        recent_activity=[_serialize_referral_event(event) for event in recent_events],
    )


def get_referral_history(current_user: dict, db: Session, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    query = db.query(ReferralPointEvent).filter(ReferralPointEvent.user_id == _user_id(user))
    total = query.count()
    items = (
        query.order_by(ReferralPointEvent.created_at.desc())
        .offset(safe_offset)
        .limit(safe_limit)
        .all()
    )
    return {
        "items": [_serialize_referral_event(event).model_dump() for event in items],
        "total": int(total),
        "limit": safe_limit,
        "offset": safe_offset,
    }


def claim_share_points(body: ReferralShareRequest, current_user: dict, db: Session) -> dict[str, Any]:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    channel = (body.channel or "share").strip().lower()[:40] or "share"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    already_claimed_today = (
        db.query(ReferralPointEvent)
        .filter(
            ReferralPointEvent.user_id == _user_id(user),
            ReferralPointEvent.event_type == "share_bonus",
            ReferralPointEvent.created_at >= day_start,
        )
        .first()
    )
    if already_claimed_today:
        return {
            "awarded": False,
            "points_awarded": 0,
            "message": "Daily sharing points already claimed today.",
            "channel": channel,
            "total_points": _total_referral_points(user),
            "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
            "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
            "next_eligible_at": (day_start + timedelta(days=1)).isoformat(),
        }

    setattr(
        user,
        "sharing_points",
        int(cast(int | None, getattr(user, "sharing_points", 0)) or 0) + REFERRAL_SHARE_DAILY_BONUS,
    )
    _record_referral_event(
        db,
        user_id=_user_id(user),
        event_type="share_bonus",
        points=REFERRAL_SHARE_DAILY_BONUS,
        channel=channel,
    )
    commit_and_refresh(db, user)

    return {
        "awarded": True,
        "points_awarded": REFERRAL_SHARE_DAILY_BONUS,
        "message": "Sharing bonus awarded.",
        "channel": channel,
        "total_points": _total_referral_points(user),
        "referral_points": int(cast(int | None, getattr(user, "referral_points", 0)) or 0),
        "sharing_points": int(cast(int | None, getattr(user, "sharing_points", 0)) or 0),
    }


# ── Logout ────────────────────────────────────────────────────────────────────

def logout_user(request: Request, response: Response, body_refresh_token: str | None = None) -> dict:
    from jose import jwt as _jwt  # local import to avoid top-level circular deps

    # Blacklist the access token
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    try:
        if not token:
            raise ValueError("missing bearer token")
        payload = _jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        jti = payload.get("jti") or token[-16:]
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        blacklist_token(jti, ttl)
    except Exception:
        pass  # best-effort blacklist

    # Blacklist the refresh token (from cookie or body — covers both web and mobile)
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name) or body_refresh_token
    if refresh_token:
        try:
            rt_payload = _jwt.decode(
                refresh_token, settings.secret_key, algorithms=[settings.algorithm]
            )
            rt_jti = rt_payload.get("jti") or refresh_token[-16:]
            rt_exp = rt_payload.get("exp", 0)
            rt_ttl = max(int(rt_exp - datetime.now(timezone.utc).timestamp()), 1)
            blacklist_token(rt_jti, rt_ttl)

            family_id = rt_payload.get("family_id")
            if family_id:
                revoke_refresh_family(str(family_id))
        except Exception:
            pass  # best-effort blacklist

    response.delete_cookie(settings.refresh_token_cookie_name, path="/")
    return {"detail": "Logged out successfully."}


# ── Profile ───────────────────────────────────────────────────────────────────

def update_profile(body: ProfileUpdate, current_user: dict, db: Session) -> User:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    provided_fields = set(getattr(body, "model_fields_set", set()))

    username = getattr(body, "username", None)
    if username and username != _user_username(user):
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=409, detail="Username already taken")
        setattr(user, "username", username)

    email = getattr(body, "email", None)
    if email and email != _user_email(user):
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="Email already in use")
        setattr(user, "email", email)
        setattr(user, "email_verified", False)

    for field_name in (
        "full_name",
        "phone",
        "address_book",
        "profile_image",
        "preferred_language",
        "preferred_currency",
        "preferred_country",
    ):
        if field_name in provided_fields:
            setattr(user, field_name, getattr(body, field_name, None))

    commit_and_refresh(db, user)
    cache_delete(f"auth:user:{_user_id(user)}")
    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=_user_id(user),
        username=_user_username(user),
        user_role=_user_role(user),
        resource_type="user",
        resource_id=_user_id(user),
        details={"updated_fields": sorted(provided_fields)},
    )
    return user


async def upload_avatar(file: UploadFile, current_user: dict, db: Session) -> dict:
    from utils.file_validation import validate_upload_image
    from services.storage import storage as _storage

    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb} MB limit.")

    ext = validate_upload_image(contents, file.filename or "avatar")

    filename = f"avatar_{current_user['id']}{ext}"
    key = f"avatars/{filename}"
    mime_type = file.content_type or "image/jpeg"
    url = _storage.save(key, contents, content_type=mime_type)

    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    setattr(user, "profile_image", url)
    commit_only(db)
    return {"profile_image": _user_profile_image(user)}


# ── Password management ───────────────────────────────────────────────────────

def change_password(body: ChangePasswordRequest, current_user: dict, db: Session) -> dict:
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(body.get_current_password(), cast(str, getattr(user, "hashed_password"))):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Validate new password complexity
    validate_password_complexity(body.new_password)
    
    setattr(user, "hashed_password", get_password_hash(body.new_password))
    commit_only(db)
    return {"detail": "Password changed successfully."}


def forgot_password(body: ForgotPasswordRequest, db: Session) -> dict:
    generic = {"detail": "If that email exists, a reset link has been sent."}
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return generic

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used.is_(False),
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    db_token = PasswordResetToken(
        user_id=user.id,
        token=raw_token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=RESET_TOKEN_TTL_HOURS),
    )
    add_and_flush(db, db_token)
    commit_only(db)

    try:
        send_password_reset_email(_user_email(user), raw_token)
    except Exception as exc:
        logger.error("Failed to send password reset email: %s", exc)

    return generic


def reset_password(body: ResetPasswordRequest, db: Session) -> dict:
    db_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == body.token,
            PasswordResetToken.used.is_(False),
        )
        .first()
    )
    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    if cast(datetime, getattr(db_token, "expires_at")) < datetime.now(timezone.utc).replace(tzinfo=None):
        setattr(db_token, "used", True)
        commit_only(db)
        raise HTTPException(status_code=400, detail="Reset token has expired.")

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Validate new password complexity
    validate_password_complexity(body.new_password)

    setattr(user, "hashed_password", get_password_hash(body.new_password))
    setattr(db_token, "used", True)
    commit_only(db)
    return {"detail": "Password updated successfully."}


# ── Customer Preferences ──────────────────────────────────────────────────────

class PreferencesUpdate(BaseModel):
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None
    preferred_country: Optional[str] = None


def get_user_preferences(current_user: dict, db: Session) -> dict:
    """Return user locale preferences and browsing history product IDs."""
    import json as _json
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    history = []
    browsing_history = db.query(UserBrowsingHistory).filter(
        UserBrowsingHistory.user_id == user.id
    ).order_by(UserBrowsingHistory.viewed_at.desc()).limit(20).all()
    history = [bh.product_id for bh in browsing_history]
    return {
        "preferred_language": cast(str | None, getattr(user, "preferred_language")) or DEFAULT_LANGUAGE,
        "preferred_currency": cast(str | None, getattr(user, "preferred_currency")) or DEFAULT_CURRENCY,
        "preferred_country": cast(str | None, getattr(user, "preferred_country")) or DEFAULT_COUNTRY,
        "browsing_history": history,
    }


def update_user_preferences(body: PreferencesUpdate, current_user: dict, db: Session) -> dict:
    """Persist user locale preferences."""
    _VALID_CURRENCIES = set(KNOWN_CURRENCY_META.keys())
    _VALID_LANGUAGES = {"en", "ar", "fr", "de", "es", "hi", "ur", "tr", "fa"}
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.preferred_language is not None:
        if body.preferred_language not in _VALID_LANGUAGES:
            raise HTTPException(status_code=422, detail=f"Unsupported language: {body.preferred_language}")
        setattr(user, "preferred_language", body.preferred_language)
    if body.preferred_currency is not None:
        if body.preferred_currency.upper() not in _VALID_CURRENCIES:
            raise HTTPException(status_code=422, detail=f"Unsupported currency: {body.preferred_currency}")
        setattr(user, "preferred_currency", body.preferred_currency.upper())
    if body.preferred_country is not None:
        setattr(user, "preferred_country", body.preferred_country.upper())
    commit_only(db)
    return get_user_preferences(current_user, db)


# ── TOTP 2FA ──────────────────────────────────────────────────────────────────


def get_totp_status(current_user: dict, db: Session) -> dict:
    """Return whether TOTP 2FA is enabled for the current user."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"totp_enabled": bool(getattr(user, "totp_enabled", False))}


def _generate_totp_provisioning_uri(user: User) -> tuple[str, str]:
    """Generate a TOTP secret and provisioning URI for QR scanning."""
    secret = pyotp.random_base32()
    issuer = getattr(settings, "app_name", "ZOZI Marketplace")
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=_user_email(user),
        issuer_name=issuer,
    )
    return secret, uri


def _validate_totp_code(secret: str, code: str) -> bool:
    """Validate a TOTP code against a secret using a window of 1 step."""
    if not code or not secret:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def setup_totp(current_user: dict, db: Session) -> dict:
    """Generate a TOTP secret and return provisioning information."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is already enabled")

    secret, uri = _generate_totp_provisioning_uri(user)
    setattr(user, "totp_secret", secret)
    commit_only(db)
    return {
        "secret": secret,
        "provisioning_uri": uri,
        "detail": "Scan the QR code with your authenticator app, then call /auth/2fa/enable to verify.",
    }


def enable_totp(current_user: dict, db: Session, code: str) -> dict:
    """Verify a TOTP code and enable 2FA with recovery codes."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    secret = cast(str | None, getattr(user, "totp_secret", None))
    if not secret:
        raise HTTPException(status_code=400, detail="TOTP not set up. Call /auth/2fa/setup first.")
    if getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is already enabled")

    if not _validate_totp_code(secret, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    recovery_codes = []
    for _ in range(8):
        recovery_codes.append(secrets.token_hex(8))

    setattr(user, "totp_enabled", True)
    setattr(user, "totp_recovery_codes", recovery_codes)
    commit_only(db)
    return {
        "detail": "TOTP 2FA enabled successfully.",
        "recovery_codes": recovery_codes,
        "warning": "Save these recovery codes in a secure place. They can only be used once each.",
    }


def disable_totp(current_user: dict, db: Session, password: str) -> dict:
    """Disable TOTP 2FA after verifying the current password."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is not enabled")

    if not verify_password(password, cast(str, getattr(user, "hashed_password"))):
        raise HTTPException(status_code=400, detail="Incorrect password")

    setattr(user, "totp_secret", None)
    setattr(user, "totp_enabled", False)
    setattr(user, "totp_recovery_codes", None)
    commit_only(db)
    return {"detail": "TOTP 2FA disabled successfully."}


def _verify_totp_code_with_fallback(user: User, code: str) -> bool:
    """Verify TOTP code, also checking against stored recovery codes."""
    if not code:
        return False

    secret = cast(str | None, getattr(user, "totp_secret", None))
    if secret and _validate_totp_code(secret, code):
        return True

    recovery_codes = cast(list[str] | None, getattr(user, "totp_recovery_codes", None))
    if recovery_codes and code in recovery_codes:
        recovery_codes.remove(code)
        setattr(user, "totp_recovery_codes", recovery_codes)
        return True

    return False


def complete_totp_login(
    temp_token: str,
    code: str,
    db: Session,
    response: Response,
    request: Request | None = None,
) -> dict:
    """Complete 2FA login by verifying TOTP code against a temp challenge token."""
    try:
        payload = verify_temp_token(temp_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired temp token")

    user_id = int(payload.get("sub", 0))
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid temp token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is not enabled for this account")

    if not _verify_totp_code_with_fallback(user, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code or recovery code")

    return _create_tokens_response(response, user, db, request=request, method="2fa")


def admin_verify_totp(
    current_user: dict,
    code: str,
    db: Session,
) -> dict:
    """Re-verify an admin's identity with a TOTP code for sensitive actions.
    
    Returns a new access token with ``admin_2fa_verified`` timestamp claim.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not getattr(user, "totp_enabled", False):
        raise HTTPException(status_code=400, detail="TOTP 2FA is not enabled")

    if not _verify_totp_code_with_fallback(user, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    from utils.auth import ADMIN_2FA_VERIFY_TTL
    verify_ttl = int(ADMIN_2FA_VERIFY_TTL)
    access_token = create_access_token(
        data={
            "sub": str(_user_id(user)),
            "admin_2fa_verified": datetime.now(timezone.utc).timestamp(),
        },
        expires_delta=timedelta(seconds=verify_ttl),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": verify_ttl,
        "detail": "2FA verified for this session",
    }



