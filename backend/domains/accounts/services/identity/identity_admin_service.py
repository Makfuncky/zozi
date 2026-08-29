"""Identity administration service.

Backend for ``admin_identity_operations`` router. Owns user lifecycle
operations (list / get / update / archive / restore / delete / role / active /
force-password-reset) scoped to a country. The router delegates here so it
performs no direct ``db.query``/``db.add``/``db.commit`` and does not import
other controllers.

Row-level scoping is applied through the canonical utils (``get_country_or_404``
and the request RLS context) rather than bespoke SQL in the router.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.ports import User
from domains.accounts.ports import get_user_by_id
# TODO: Module not yet created
# from domains.accounts.services.users.user_management_service import update_user_role, toggle_user_active
from infrastructure.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.pagination import cursor_paginate_asc, paginated_response


def _scope(db: Session, country_code: str):
    """Validate the country and activate request RLS for it."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)


def list_users_by_country(
    db: Session,
    country_code: str,
    page: int = 1,
    size: int = 50,
    role: Optional[str] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        q = db.query(User).filter(User.country_code == country_code.upper())
        if role:
            q = q.filter(User.role == role)
        if search:
            q = q.filter(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
        if not include_deleted:
            q = q.filter(User.is_deleted.is_(False))
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()


def get_user_in_country(db: Session, country_code: str, user_id: int) -> User:
    _scope(db, country_code)
    try:
        user = (
            db.query(User)
            .filter(User.id == user_id, User.country_code == country_code.upper())
            .first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    finally:
        clear_rls_context()


def update_user_in_country(
    db: Session, country_code: str, user_id: int, payload
) -> User:
    user = get_user_in_country(db, country_code, user_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


def list_all_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    """List users across all countries (admin console, no RLS scoping)."""
    query = db.query(User)
    if skip and skip > 0:
        page = cursor_paginate_asc(query, cursor=skip, page_size=limit)
        return list(page.items)
    page = cursor_paginate_asc(query, cursor=None, page_size=limit)
    return list(page.items)


def get_user_by_id_or_404(db: Session, user_id: int) -> User:
    """Fetch a user by primary key, raising 404 when absent."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user_by_id(db: Session, user_id: int, payload) -> User:
    """Apply an update payload to a user loaded by id (no country scoping).

    Behaviour-preserving extraction of the inline ``.put("/me")`` and
    ``.put("/{user_id}")`` handlers in ``routers.admin_identity_operations_api``
    and ``routers.public_identity_operations``: load, apply the unset-excluded
    fields, commit once, refresh and return the row.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


def archive_user(db: Session, country_code: str, user_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
    user = get_user_in_country(db, country_code, user_id)
    user.is_deleted = True
    db.commit()
    return {"message": "User archived", "id": user_id, "reason": reason}


def restore_user(db: Session, country_code: str, user_id: int) -> Dict[str, Any]:
    user = get_user_in_country(db, country_code, user_id)
    user.is_deleted = False
    db.commit()
    return {"message": "User restored", "id": user_id}


def bulk_archive_users(db: Session, country_code: str, payload, reason: Optional[str] = None) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        ids = payload.ids if payload else []
        if not ids:
            return {"message": "0 users archived", "count": 0, "reason": reason}
        count = (
            db.query(User)
            .filter(User.id.in_(ids), User.country_code == country_code.upper())
            .update({User.is_deleted: True}, synchronize_session=False)
        )
        db.commit()
        return {"message": f"{count} users archived", "count": count, "reason": reason}
    finally:
        clear_rls_context()


def bulk_toggle_active(db: Session, country_code: str, user_ids: List[int], is_active: bool = True) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        if not user_ids:
            return {"message": "Updated 0 users", "updated": 0}
        count = (
            db.query(User)
            .filter(User.id.in_(user_ids), User.country_code == country_code.upper())
            .update({User.is_active: is_active}, synchronize_session=False)
        )
        db.commit()
        return {"message": f"Updated {count} users", "updated": count}
    finally:
        clear_rls_context()


def bulk_restore_users(db: Session, country_code: str, payload) -> Dict[str, Any]:
    _scope(db, country_code)
    try:
        ids = payload.ids if payload else []
        if not ids:
            return {"message": "0 users restored", "count": 0}
        count = (
            db.query(User)
            .filter(User.id.in_(ids), User.country_code == country_code.upper())
            .update({User.is_deleted: False}, synchronize_session=False)
        )
        db.commit()
        return {"message": f"{count} users restored", "count": count}
    finally:
        clear_rls_context()


def hard_delete_user(db: Session, country_code: str, user_id: int, acting_user: dict, delete_orders: bool = False) -> Dict[str, Any]:
    get_user_in_country(db, country_code, user_id)
    from domains.governance.ports import hard_delete_entity
    hard_delete_entity("user", user_id, acting_user, db)
    return {"message": "User hard-deleted", "id": user_id}


def set_user_role(db: Session, country_code: str, user_id: int, role: str, acting_user: dict) -> Dict[str, Any]:
    get_user_in_country(db, country_code, user_id)
    return update_user_role(user_id, role, acting_user, db)


def set_user_active(db: Session, country_code: str, user_id: int, acting_user: dict) -> Dict[str, Any]:
    get_user_in_country(db, country_code, user_id)
    return toggle_user_active(user_id, acting_user, db)


def force_reset_password(db: Session, country_code: str, user_id: int, new_password: str, acting_user: dict) -> Dict[str, Any]:
    from infrastructure.utils.auth import get_password_hash

    user = get_user_in_country(db, country_code, user_id)
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": "Password reset", "id": user_id}


def delete_user_admin(db: Session, country_code: str, user_id: int, acting_user: dict, delete_orders: bool = False) -> Dict[str, Any]:
    return hard_delete_user(db, country_code, user_id, acting_user, delete_orders=delete_orders)


