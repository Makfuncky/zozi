"""Auth dependency facade — the canonical home of the JWT auth dependencies.

`get_current_user` / `get_optional_user` used to live in
``controllers/auth_controller.py``; services importing them there created a
services -> controllers dependency-graph violation. They now live here so any
layer (controllers, routers, services) can consume them without depending on
the auth controller.

Everything here is self-contained: it only imports from ``models``, ``db``,
``utils`` and ``dependencies`` — never from ``controllers``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from models import User
from db.schemas import User as UserSchema
from dependencies.db import get_db
from utils.auth import verify_token
from utils.cache import cache_get_json, cache_set_json
from utils.constants import STAFF_ROLES
from utils.staff_permissions import DEFAULT_ROLE_PERMISSION_MAP, sanitize_staff_permissions

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

DEFAULT_LANGUAGE = "en"
DEFAULT_CURRENCY = "OMR"
DEFAULT_COUNTRY = "OM"
_USER_CACHE_TTL_SECONDS = 5 * 60


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
    # Fix: the old lazy `from controllers.admin_controller import ROLE_PERMISSION_MAP`
    # targeted a symbol that never existed there (it lives in
    # controllers/admin/analytics.py, built 1:1 from this map). Using the
    # canonical DEFAULT_ROLE_PERMISSION_MAP is behaviorally identical.
    return sorted(DEFAULT_ROLE_PERMISSION_MAP.get(role, set()))


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
