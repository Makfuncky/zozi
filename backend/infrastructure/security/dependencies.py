"""FastAPI auth dependencies: resolve the current user from the bearer token.

Law 1 compliant: the User record is loaded via raw SQL against the
``users`` table. The auth context is propagated through FastAPI's
``request.state`` instead of the rbac helper. The legacy rbac/
domains imports have been removed in the 2026-08-27 cleanup.
"""
from __future__ import annotations

import logging
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.utils.auth import decode_token

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def _load_user(user_id: str, db: Session):
    """Load user by ID via raw SQL (Law 1 compliant)."""
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    row = db.execute(
        text(
            "SELECT id, role, is_active, email, full_name, country_code "
            "FROM users WHERE id = :uid"
        ),
        {"uid": uid},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not row.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return dict(row)


def _attach_user_to_request(request: Request, user: dict) -> None:
    """Store the resolved user on request.state for downstream rbac lookups."""
    request.state.current_user = user


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    user = _load_user(payload.get("sub"), db)
    _attach_user_to_request(request, user)
    return user


def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user = _load_user(payload.get("sub"), db)
        _attach_user_to_request(request, user)
        return user
    except HTTPException:
        return None
    except Exception:
        logger.exception("Unexpected error in get_current_user_optional")
        return None


def _require_role(user, *roles: str) -> None:
    role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
    if role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def require_admin(current_user=Depends(get_current_user)):
    return _require_role(current_user, "admin", "super_admin")


def require_super_admin(current_user=Depends(get_current_user)):
    return _require_role(current_user, "super_admin")


def require_employee(current_user=Depends(get_current_user)):
    return _require_role(current_user, "admin", "super_admin", "employee", "staff")


def require_supplier(current_user=Depends(get_current_user)):
    return _require_role(current_user, "supplier")


def require_logistics(current_user=Depends(get_current_user)):
    return _require_role(current_user, "logistics_partner")


def require_staff(current_user=Depends(get_current_user)):
    return _require_role(current_user, "admin", "super_admin", "employee", "staff")


def require_treasury_access(current_user=Depends(get_current_user)):
    """Gate a route on TREASURY_ROLES."""
    from infrastructure.utils.constants import TREASURY_ROLES

    role = (
        current_user.get("role")
        if isinstance(current_user, dict)
        else getattr(current_user, "role", None)
    )
    if str(role or "").lower() not in TREASURY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Treasury access required"
        )
    return current_user


def require_coupon_admin(current_user=Depends(get_current_user)):
    """Strict admin-only gate."""
    role = (
        current_user.get("role")
        if isinstance(current_user, dict)
        else getattr(current_user, "role", None)
    )
    if str(role or "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


def require_permissions(slugs: list):
    """FastAPI dependency factory that enforces ALL of the given permission slugs.

    Uses the infrastructure-level permission service (lazy-loaded).
    """
    from fastapi import Depends, HTTPException

    def _extract(user, key, default):
        if isinstance(user, dict):
            return user.get(key, default)
        return getattr(user, key, default)

    def _checker(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
        # Lazy import to avoid module-level coupling
        from infrastructure.database.permission_service import check_permission
        uid = int(_extract(current_user, "id", _extract(current_user, "sub", 0)))
        cc = _extract(current_user, "country_code", _extract(current_user, "cc", "OM"))
        missing = [s for s in slugs if not check_permission(uid, s, cc, db)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {missing}",
            )
        return current_user

    return _checker
