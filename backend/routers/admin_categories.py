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

from services.catalog.category_service import (
    get_category_query,
    get_category_by_ref,
    get_category_by_id,
    category_slug_exists,
    create_category,
    update_category,
    deactivate_category,
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
    query = get_category_query(db, active_only=active_only, parent_id=parent_id)
    return cursor_paginate_desc(query, cursor=cursor, page_size=limit)


@router.get("/{category_ref}", response_model=CategoryOut)
async def get_category(category_ref: str, db: Session = Depends(get_db)):
    cat = get_category_by_ref(db, category_ref)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post("/", response_model=CategoryOut)
async def create_category_endpoint(
    payload: CategoryCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    slug = generate_slug(payload.slug or payload.name)
    if category_slug_exists(db, slug):
        raise HTTPException(status_code=409, detail="Category slug already exists")

    payload_data = payload.model_dump(exclude_none=True, exclude={"slug"})
    name = payload.name
    cat = create_category(db, name=name, slug=slug, **payload_data)
    return cat


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category_endpoint(
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
        if category_slug_exists(db, slug, exclude_id=category_id):
            raise HTTPException(status_code=409, detail="Category slug already exists")
        cat.slug = slug
    updated = update_category(db, cat, updates)
    return updated


@router.get("/admin/flat", response_model=CursorPage)
async def list_categories_flat(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
):
    """Return all active categories with id, slug, name, parent_id, commission_rate for admin commission config."""
    query = get_category_query(db, active_only=True)
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
    deactivate_category(db, cat)
    return MessageResponse(message="Category deactivated")
