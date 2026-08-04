"""Categories router."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from data.db import get_db
from data.schemas import CursorPage, CategoryOut, CategoryCreate, CategoryUpdate, MessageResponse
from data.models import User
from utils.dependencies import require_admin
from utils.slug import generate_slug
from utils.pagination import cursor_paginate_desc

from services.catalog.products_write_service import (
    build_category_query, get_category_by_slug, get_category_by_id,
    get_category_by_slug_excluding,
)
from services.catalog.categories_write_service import (
    create_category_with_slug, update_category_full, deactivate_category,
)
router = APIRouter()


@router.get("/", response_model=CursorPage)
async def list_categories(
    active_only: bool = Query(True),
    parent_id: Optional[int] = Query(None),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = build_category_query(db, active_only=active_only, parent_id=parent_id)
    return cursor_paginate_desc(query, cursor=cursor, page_size=limit)


@router.get("/{category_ref}", response_model=CategoryOut)
async def get_category(category_ref: str, db: Session = Depends(get_db)):
    cat = get_category_by_slug(db, category_ref)
    if not cat and category_ref.isdigit():
        cat = get_category_by_id(db, int(category_ref))
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
    if get_category_by_slug(db, slug):
        raise HTTPException(status_code=409, detail="Category slug already exists")

    payload_data = payload.model_dump(exclude_none=True, exclude={"slug"})
    extra = {k: v for k, v in payload_data.items() if k != "name"}
    return create_category_with_slug(db, payload.name, slug, parent_id=None, **extra)


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = get_category_by_id(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    updates = payload.model_dump(exclude_none=True)
    requested_slug = updates.pop("slug", None)
    if requested_slug is not None:
        slug = generate_slug(requested_slug)
        existing = get_category_by_slug_excluding(db, slug, category_id)
        if existing:
            raise HTTPException(status_code=409, detail="Category slug already exists")
        cat.slug = slug
    for k, v in updates.items():
        setattr(cat, k, v)
    update_category_full(db, category_id, updates)
    return get_category_by_id(db, category_id)


@router.get("/admin/flat", response_model=CursorPage)
async def list_categories_flat(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
):
    """Return all active categories with id, slug, name, parent_id, commission_rate for admin commission config."""
    query = build_category_query(db, active_only=True)
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
    cat = get_category_by_id(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    deactivate_category(db, category_id)
    return MessageResponse(message="Category deactivated")

