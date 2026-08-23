"""Admin category write service (behavior-preserving extraction).

Mirrors the exact behavior of the legacy admin category endpoints so the
router performs no inline ``db.add``/``db.commit``/``db.delete``. The generic
``services.catalog.category_service`` intentionally uses different contracts
(soft-delete, slug auto-generation, integer return codes), so the admin
endpoints keep their original hard-delete + explicit-slug semantics here.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.catalog.models.products import Category
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from domains.catalog.services.categories.category_service import rebuild_category_paths


def _scope(db: Session, country_code: str) -> str:
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    return code


def _get_or_404(db: Session, code: str, category_id: int) -> Category:
    category = db.query(Category).filter(Category.id == category_id, Category.country_code == code).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def create_category(db: Session, country_code: str, *, name: Optional[str], slug: Optional[str], parent_id: Optional[int], sort_order: int, description: Optional[str]) -> Category:
    code = _scope(db, country_code)
    try:
        category = Category(
            name=name,
            slug=slug,
            parent_id=parent_id,
            sort_order=sort_order,
            description=description,
            country_code=code,
        )
        db.add(category)
        db.flush()
        rebuild_category_paths(db)
        db.commit()
        db.refresh(category)
        return category
    finally:
        clear_rls_context()


def update_category(db: Session, country_code: str, category_id: int, *, name: Optional[str], slug: Optional[str], parent_id: Optional[int], sort_order: Optional[int], description: Optional[str]) -> Category:
    code = _scope(db, country_code)
    try:
        category = _get_or_404(db, code, category_id)
        if name is not None:
            category.name = name
        if slug is not None:
            category.slug = slug
        if parent_id is not None:
            category.parent_id = parent_id
        if sort_order is not None:
            category.sort_order = sort_order
        if description is not None:
            category.description = description
        db.flush()
        rebuild_category_paths(db)
        db.commit()
        db.refresh(category)
        return category
    finally:
        clear_rls_context()


def reorder_categories(db: Session, country_code: str, order: Optional[Dict[Any, Any]]) -> Dict[str, Any]:
    code = _scope(db, country_code)
    try:
        order = order or {}
        for cid, pos in order.items():
            category = db.query(Category).filter(Category.id == int(cid), Category.country_code == code).first()
            if category:
                category.sort_order = pos
        db.commit()
        return {"message": "Categories reordered"}
    finally:
        clear_rls_context()


def delete_category(db: Session, country_code: str, category_id: int) -> Dict[str, Any]:
    code = _scope(db, country_code)
    try:
        category = _get_or_404(db, code, category_id)
        db.delete(category)
        db.commit()
        return {"message": "Category deleted"}
    finally:
        clear_rls_context()
