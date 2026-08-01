"""Categories router."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import get_db
from db.schemas import CursorPage, CategoryOut, CategoryCreate, CategoryUpdate, MessageResponse
from models import Category, User
from utils.dependencies import require_admin
from utils.slug import generate_slug
from utils.pagination import cursor_paginate_desc

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only
router = APIRouter()


@router.get("/", response_model=CursorPage)
async def list_categories(
    active_only: bool = Query(True),
    parent_id: Optional[int] = Query(None),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    return cursor_paginate_desc(query, cursor=cursor, page_size=limit)


@router.get("/{category_ref}", response_model=CategoryOut)
async def get_category(category_ref: str, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.slug == category_ref).first()
    if not cat and category_ref.isdigit():
        cat = db.query(Category).filter(Category.id == int(category_ref)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post("/", response_model=CategoryOut)
async def create_category(
    payload: CategoryCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    slug = generate_slug(payload.slug or payload.name)
    if db.query(Category).filter(Category.slug == slug).first():
        raise HTTPException(status_code=409, detail="Category slug already exists")

    payload_data = payload.model_dump(exclude_none=True, exclude={"slug"})
    cat = Category(name=payload.name, slug=slug)
    for field_name, value in payload_data.items():
        if field_name == "name":
            continue
        setattr(cat, field_name, value)
    add_and_flush(db, cat)
    commit_and_refresh(db, cat)
    return cat


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    updates = payload.model_dump(exclude_none=True)
    requested_slug = updates.pop("slug", None)
    if requested_slug is not None:
        slug = generate_slug(requested_slug)
        existing = db.query(Category).filter(Category.slug == slug, Category.id != category_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Category slug already exists")
        cat.slug = slug
    for k, v in updates.items():
        setattr(cat, k, v)
    commit_and_refresh(db, cat)
    return cat


@router.get("/admin/flat", response_model=CursorPage)
async def list_categories_flat(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
):
    """Return all active categories with id, slug, name, parent_id, commission_rate for admin commission config."""
    query = db.query(Category).filter(Category.is_active == True)
    result = cursor_paginate_desc(query, cursor=cursor, page_size=limit)
    result.items = [
        {
            "id": c.id,
            "slug": c.slug,
            "name": c.name,
            "parent_id": c.parent_id,
            "commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,
            "sort_order": c.sort_order,
        }
        for c in result.items
    ]
    return result


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.is_active = False
    commit_only(db)
    return MessageResponse(message="Category deactivated")

