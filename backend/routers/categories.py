"""Categories router."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models import Category, User
from db.schemas import CategoryCreate, CategoryUpdate, CategoryOut, MessageResponse
from utils.dependencies import require_admin
from utils.slug import generate_slug

router = APIRouter()


@router.get("/", response_model=list[CategoryOut])
async def list_categories(
    active_only: bool = Query(True),
    parent_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    return query.order_by(Category.sort_order, Category.name).all()


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
    db.add(cat)
    db.commit()
    db.refresh(cat)
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
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/admin/flat", response_model=list[dict])
async def list_categories_flat(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return all active categories with id, slug, name, parent_id, commission_rate for admin commission config."""
    rows = db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order, Category.name).all()  # noqa: E712
    return [
        {
            "id": c.id,
            "slug": c.slug,
            "name": c.name,
            "parent_id": c.parent_id,
            "commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,
            "sort_order": c.sort_order,
        }
        for c in rows
    ]


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
    db.commit()
    return MessageResponse(message="Category deactivated")

