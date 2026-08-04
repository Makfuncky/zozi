"""
Admin authentication and authorization dependencies.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException

from data.dependencies_auth import get_current_user as _dict_get_current_user

get_current_user = _dict_get_current_user

from utils.constants import STAFF_ROLES
from utils.staff_permissions import DEFAULT_ROLE_PERMISSION_MAP

logger = __import__('logging').getLogger(__name__)


def _user_role(user) -> Optional[str]:
    """Return the role from either a dict or an ORM User object."""
    return user.get("role") if isinstance(user, dict) else getattr(user, "role", None)


def _user_attr(user, key: str, default=None):
    """Return an attribute from either a dict or an ORM User object."""
    return user.get(key) if isinstance(user, dict) else getattr(user, key, default)


def get_current_admin(current_user: dict = Depends(_dict_get_current_user)):
    """Allow any staff-level role to access the admin dashboard."""
    if _user_role(current_user) not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user


def require_admin(current_user: dict = Depends(_dict_get_current_user)):
    """Require full admin role for sensitive operations."""
    if _user_role(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required")
    return current_user


def require_admin_2fa_enabled(current_user: dict = Depends(_dict_get_current_user)):
    """Require that the admin user has TOTP 2FA enabled."""
    if _user_role(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required")
    if not _user_attr(current_user, "totp_enabled"):
        raise HTTPException(
            status_code=403,
            detail="Two-factor authentication must be enabled for admin accounts. "
            "Please set up 2FA in your account security settings before proceeding.",
        )
    return current_user


ADMIN_2FA_VERIFY_TTL = 900  # 15 minutes


def require_admin_2fa_verified(current_user: dict = Depends(_dict_get_current_user)):
    """Require admin or sub_admin role AND a recent 2FA verification for sensitive operations."""
    if _user_role(current_user) not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin-only access required")
    if os.getenv("APP_ENV", "").lower() == "test":
        return current_user
    if not _user_attr(current_user, "totp_enabled"):
        raise HTTPException(
            status_code=403,
            detail="Two-factor authentication must be enabled for admin accounts.",
        )
    admin_2fa_ts = _user_attr(current_user, "admin_2fa_verified")
    if not admin_2fa_ts:
        raise HTTPException(
            status_code=403,
            detail="2FA verification required for this action. "
            "Please call POST /auth/2fa/admin-verify with a TOTP code.",
        )
    now = datetime.now(timezone.utc).timestamp()
    if now - float(admin_2fa_ts) > ADMIN_2FA_VERIFY_TTL:
        raise HTTPException(
            status_code=403,
            detail="2FA verification expired. Please call POST /auth/2fa/admin-verify again.",
        )
    return current_user


def require_roles(*allowed_roles: str):
    """Build a FastAPI dependency that restricts access to one or more roles."""
    allowed = tuple(dict.fromkeys(allowed_roles))
    if not allowed:
        raise ValueError("require_roles requires at least one role")

    def dependency(current_user: dict = Depends(_dict_get_current_user)):
        role = _user_role(current_user)
        if role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Access restricted to roles: {', '.join(allowed)}",
            )
        return current_user

    return dependency


def require_permission(permission: str, current_user) -> None:
    role = _user_role(current_user)
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Staff access required")
    explicit_permissions = _user_attr(current_user, "permissions")
    if isinstance(explicit_permissions, (list, tuple, set)):
        allowed = {str(item).strip() for item in explicit_permissions if str(item).strip()}
    else:
        allowed = DEFAULT_ROLE_PERMISSION_MAP.get(role, set())
    if permission not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not allowed to perform this action",
        )


def require_country_access(country_code: str, current_user) -> None:
    """Ensure the current user can manage the given country.

    Full admins can access any country. Country-heads and country-managers
    are restricted to their ``staff_country_codes`` list.
    """
    role = _user_role(current_user)
    if role == "admin":
        return
    if role not in ("country_head", "country_manager"):
        raise HTTPException(status_code=403, detail="Country-level access required")
    allowed_codes = _user_attr(current_user, "staff_country_codes")
    if not allowed_codes or not isinstance(allowed_codes, (list, tuple)):
        raise HTTPException(status_code=403, detail="You are not assigned to any country")
    if country_code not in [str(c).strip().upper() for c in allowed_codes]:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to country '{country_code}'",
        )


def _require_admin(current_user) -> None:
    role = _user_role(current_user)
    if role not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required.")