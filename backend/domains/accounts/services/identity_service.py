"""Identity (customer-facing) service.

Backend for ``public_identity_operations`` router. Owns profile reads/updates
and user listing so the router performs no direct ``db.query``/``db.commit``
and never instantiates ORM models.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from domains.accounts.models.user import User
from infrastructure.database.schemas import UserOut


def get_profile(db: Session, current_user: dict) -> User:
    user = db.query(User).filter(User.id == current_user.get("id")).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_profile(db: Session, current_user: dict, payload) -> User:
    user = get_profile(db, current_user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    return user


def delete_user(db: Session, user_id: int) -> dict:
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    return {"message": "User deleted", "id": user_id}
