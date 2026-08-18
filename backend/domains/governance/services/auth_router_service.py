"""Auth router service — DB helpers for routers/auth.py."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from domains.accounts.models.user import User
from domains.accounts.models.user import UserLoginHistory
from infrastructure.utils.auth import verify_password
from infrastructure.utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)


def find_user(db: Session, email: str | None, username: str | None) -> User | None:
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


def record_login_history(db: Session, user: User, request=None, success: bool = True) -> None:
    try:
        ip = get_request_ip(request) if request else None
        ua = (request.headers.get("user-agent") or "")[:500] if request else None
        history = UserLoginHistory(
            user_id=user.id,
            ip_address=ip or "unknown",
            user_agent=ua,
            timestamp=datetime.now(timezone.utc),
            success=success,
            country_code=user.country_code,
        )
        db.add(history)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to record login history for %s: %s", user.username, exc)
        try:
            db.rollback()
        except Exception:
            pass


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def check_email_exists(db: Session, email: str) -> bool:
    return db.query(User).filter(User.email == email).first() is not None


def check_username_exists(db: Session, username: str) -> bool:
    return db.query(User).filter(User.username == username).first() is not None


def create_user(db: Session, email: str, username: str, full_name: str, phone: str | None, role: str, hashed_password: str) -> User:
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        phone=phone,
        role=role,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: User) -> None:
    user.last_login = datetime.now(timezone.utc)
    db.commit()

