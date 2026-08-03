"""FastAPI auth dependencies: resolve the current user from the bearer token."""
from __future__ import annotations

import logging
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from data.services_database import get_db
from data.models import User
from utils.auth import decode_token

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


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
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    user = _load_user(payload.get("sub"), db)
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user = _load_user(payload.get("sub"), db)
        return user
    except HTTPException:
        return None
    except Exception:
        logger.exception("Unexpected error in get_current_user_optional")
        return None


def _require_role(user: User, *roles: str) -> User:
    role = user.role if hasattr(user, "role") else None
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
