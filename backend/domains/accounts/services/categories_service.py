"""Auto-migrated service logic from routers/categories.py."""
from __future__ import annotations

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import CategoryCreate, CategoryOut, CategoryUpdate, MessageResponse

from domains.accounts.models.user import User
from domains.catalog.models.products import Category

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.slug import generate_slug

async def list_categories(active_only: bool, parent_id: Optional[int], page: int, page_size: int, db: Session):
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    total = query.count()
    items = query.order_by(Category.sort_order, Category.name).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": items, "total": total, "page": page, "page_size": page_size}

async def get_category(category_ref: str, db: Session):
    cat = db.query(Category).filter(Category.slug == category_ref).first()
    if not cat and category_ref.isdigit():
        cat = db.query(Category).filter(Category.id == int(category_ref)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat

async def create_category(payload: CategoryCreate, _admin: User, db: Session):
    slug = generate_slug(payload.slug or payload.name)
    if db.query(Category).filter(Category.slug == slug).first():
        raise HTTPException(status_code=409, detail="Category slug already exists")

    payload_data = payload.model_dump(exclude_none=True, exclude={"slug"})
    cat = Category(name=payload.name, slug=slug)
    for field_name, value in payload_data.items():
        if field_name == "name":
            continue
        setattr(cat, field_name, value)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

async def update_category(category_id: int, payload: CategoryUpdate, _admin: User, db: Session):
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
    db.commit()
    db.refresh(cat)
    return cat

async def list_categories_flat(_admin: User, db: Session, page: int, page_size: int):
    """Return all active categories with id, slug, name, parent_id, commission_rate for admin commission config."""
    query = db.query(Category).filter(Category.is_active == True)
    total = query.count()
    rows = query.order_by(Category.sort_order, Category.name).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": [
            {
                "id": c.id,
                "slug": c.slug,
                "name": c.name,
                "parent_id": c.parent_id,
                "commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,
                "sort_order": c.sort_order,
            }
            for c in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

async def delete_category(category_id: int, _admin: User, db: Session):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.is_active = False
    db.commit()
    return MessageResponse(message="Category deactivated")


