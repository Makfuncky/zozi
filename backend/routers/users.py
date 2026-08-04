"""Users router â€” profile CRUD, admin user management."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from data.schemas import UserOut, UserUpdate, UserAdminUpdate, MessageResponse, CursorPage
from utils.dependencies import get_current_user, require_admin
from utils.pagination import cursor_paginate_desc

from services.core.users_write_service import get_user_by_id, build_user_query, save_user
from services.security.auth_write_service import update_user_profile
router = APIRouter()

@router.get("/me", response_model=UserOut)
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_by_id(db, current_user.get("id"))


@router.put("/me", response_model=UserOut)
def update_profile(payload: UserUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_id(db, current_user.get("id"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updates = payload.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(user, k, v)
    update_user_profile(db, user, updates)
    return user

@router.get("", response_model=CursorPage)
def list_users(
    cursor: str | None = Query(None, description="Cursor for next page (from previous response's nextCursor)"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users with cursor-based pagination.

    Returns CursorPage with items, nextCursor, hasMore, and pageSize.
    Pass nextCursor as cursor parameter to fetch the next page.
    """
    result = cursor_paginate_desc(
        query=build_user_query(db),
        cursor=cursor,
        page_size=limit,
    )
    return result

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = get_user_by_id(db, user_id)
    if not u: raise HTTPException(404, "User not found")
    return u

@router.put("/{user_id}", response_model=UserOut)
def admin_update_user(user_id: int, payload: UserAdminUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = get_user_by_id(db, user_id)
    if not u: raise HTTPException(404, "User not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    return save_user(db, u)

