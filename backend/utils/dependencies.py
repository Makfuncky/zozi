"""FastAPI auth dependencies: resolve the current user from the bearer token."""
from typing import Dict

import logging
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from data.services_database import get_db
from data.models import User
from utils.auth import decode_token
from utils.constants import STAFF_ROLES
from utils.staff_permissions import sanitize_staff_permissions

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


class UserView(dict):
    """Dict-shaped current-user payload with attribute fallback.

    The codebase predominantly consumes ``current_user`` as a dict
    (``current_user["id"]`` — 240+ call sites) but a small number of
    callers use attribute access (``current_user.id``).  This view
    supports both styles so the auth contract is dict-first without
    breaking attribute-style callers.
    """

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def get_or_none(self, name: str):
        return self.get(name)


def _user_view(user: User) -> UserView:
    """Build the canonical dict-shaped user payload from an ORM User."""
    payload: dict = {
        "id": int(getattr(user, "id") or 0),
        "username": getattr(user, "username", None),
        "email": getattr(user, "email", None),
        "role": getattr(user, "role", None),
        "is_active": bool(getattr(user, "is_active", True)),
        "email_verified": bool(getattr(user, "email_verified", False)),
        "phone": getattr(user, "phone", None),
        "profile_image": getattr(user, "profile_image", None),
        "preferred_language": getattr(user, "preferred_language", None),
        "preferred_currency": getattr(user, "preferred_currency", None),
        "preferred_country": getattr(user, "preferred_country", None),
        "country_code": getattr(user, "country_code", None) or getattr(user, "preferred_country", None),
        "full_name": getattr(user, "full_name", None),
        "created_at": getattr(user, "created_at", None),
        "totp_enabled": bool(getattr(user, "totp_enabled", False)),
        "admin_2fa_verified": getattr(user, "admin_2fa_verified", None),
        "referral_code": getattr(user, "referral_code", None),
        "referral_points": int(getattr(user, "referral_points", 0) or 0),
        "sharing_points": int(getattr(user, "sharing_points", 0) or 0),
        "address_book": getattr(user, "address_book", None),
        "staff_country_codes": list(getattr(user, "staff_country_codes", None) or []),
    }
    role = payload["role"]
    if role in STAFF_ROLES:
        assigned = sanitize_staff_permissions(getattr(user, "staff_permissions", None))
        if assigned:
            payload["permissions"] = assigned
        else:
            from data.controllers_admin_controller import ROLE_PERMISSION_MAP

            payload["permissions"] = sorted(ROLE_PERMISSION_MAP.get(role, set()))
        for attr in (
            "staff_role_label",
            "staff_title",
            "staff_department",
            "staff_area_of_operation",
            "staff_hire_date",
            "staff_experience_level",
            "staff_performance_summary",
            "staff_assigned_tasks",
            "staff_assigned_projects",
            "staff_notes",
        ):
            payload[attr] = getattr(user, attr, None)
    return UserView(payload)


def _load_user(user_id: str, db: Session) -> User:
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserView:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    user = _load_user(payload.get("sub"), db)
    return _user_view(user)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserView | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user = _load_user(payload.get("sub"), db)
        return _user_view(user)
    except HTTPException:
        return None
    except Exception:
        logger.exception("Unexpected error in get_current_user_optional")
        return None


def _require_role(user, *roles: str):
    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    if role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    return _require_role(current_user, "admin", "super_admin")


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    return _require_role(current_user, "super_admin")


def require_employee(current_user: User = Depends(get_current_user)) -> User:
    return _require_role(current_user, "admin", "super_admin", "employee", "staff")


def require_supplier(current_user: User = Depends(get_current_user)) -> User:
    return _require_role(current_user, "supplier")


def require_logistics(current_user: User = Depends(get_current_user)) -> User:
    return _require_role(current_user, "logistics_partner")


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    return _require_role(current_user, "admin", "super_admin", "employee", "staff")


def require_roles(*roles: str):
    """Factory that creates a role-checking dependency."""
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        return _require_role(current_user, *roles)
    return _checker
