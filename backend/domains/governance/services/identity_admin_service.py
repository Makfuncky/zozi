"""Thin orchestration controller for admin identity/user operations.

This module is the single controller surface that the identity routers
(``routers.admin_identity_operations`` and ``routers.admin_identity_operations_api``)
delegate to, so those routers stay within the allowed circuit
(routers -> controllers/schemas/auth-deps only). All direct ``db`` reads/writes
and model construction happen here, never in the routers.

RLS context is applied here (the routers already set it before calling) so the
DB access remains country-scoped.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.comms.services.db_read import query as db_read_query
import domains.comms.services as db_write
from domains.accounts.models.user import User

from infrastructure.utils.audit import audit_log, AuditAction
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

logger = logging.getLogger(__name__)


def _actor_dict(actor: Any) -> dict:
    if isinstance(actor, dict):
        return actor
    return {
        "id": getattr(actor, "id", None),
        "username": getattr(actor, "username", None),
        "role": getattr(actor, "role", None),
    }


def list_users_for_country(
    country_code: str,
    db: Session,
    role: Optional[str] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
    page: int = 1,
    size: int = 50,
) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db_read_query(db, User).filter(User.country_code == country_code.upper())
        if role:
            q = q.filter(User.role == role)
        if search:
            q = q.filter(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
        if not include_deleted:
            q = q.filter(User.is_deleted == False)
        total = q.count()
        items = q.order_by(User.id.desc()).limit(size).offset((page - 1) * size).all()
        return {
            "items": [u for u in items],
            "total": total,
            "page": page,
            "size": size,
        }
    finally:
        clear_rls_context()


def update_user_for_country(
    country_code: str,
    user_id: int,
    payload: Any,
    db: Session,
) -> User:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        u = db_read_query(db, User).filter(
            User.id == user_id, User.country_code == country_code.upper()
        ).first()
        if not u:
            raise HTTPException(404, "User not found")
        for (k, v) in payload.model_dump(exclude_unset=True).items():
            setattr(u, k, v)
        db_write.commit(db)
        db_write.refresh(db, u)
        return u
    finally:
        clear_rls_context()


def bulk_toggle_user_active_for_country(
    country_code: str,
    user_ids: list[int],
    is_active: bool,
    db: Session,
) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        updated = 0
        for uid in user_ids:
            u = db_read_query(db, User).filter(
                User.id == uid, User.country_code == country_code.upper()
            ).first()
            if u:
                u.is_active = is_active
                updated += 1
        db_write.commit(db)
        return {"message": f"Updated {updated} users", "updated": updated}
    finally:
        clear_rls_context()


def delete_user_permanent_for_country(
    country_code: str,
    user_id: int,
    actor: Any,
    db: Session,
    delete_orders: bool = False,
) -> dict:
    from domains.governance.services.misc_service import hard_delete_entity

    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity(
            "user", user_id, _actor_dict(actor), db, delete_orders=delete_orders
        )
    finally:
        clear_rls_context()


def get_profile(user_id: int, db: Session) -> User:
    u = db_read_query(db, User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    return u


def update_profile(user_id: int, payload: Any, db: Session) -> User:
    u = db_read_query(db, User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    for (k, v) in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    db_write.commit(db)
    db_write.refresh(db, u)
    return u


def list_users_api(db: Session, skip: int = 0, limit: int = 50) -> list[User]:
    return db_read_query(db, User).offset(skip).limit(limit).all()


def get_user_api(user_id: int, db: Session) -> User:
    u = db_read_query(db, User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    return u


def admin_update_user_api(user_id: int, payload: Any, db: Session) -> User:
    u = db_read_query(db, User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    for (k, v) in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    db_write.commit(db)
    db_write.refresh(db, u)
    return u
