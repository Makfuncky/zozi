"""
Categories Controller — category tree retrieval and admin CRUD logic.
"""
from typing import List

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from controllers.cache_utils import build_versioned_cache_key, bump_cache_version, cache_get_json, cache_set_json
from models import Category
from db.schemas import CategoryCreate, CategorySchema

_CATEGORY_LIST_CACHE_TTL = 300
_CATEGORY_DETAIL_CACHE_TTL = 300


def _serialize_category(category: Category) -> dict:
    return jsonable_encoder(CategorySchema.model_validate(category))


def list_categories(db: Session) -> List[Category]:
    cache_key = build_versioned_cache_key("categories", "list", {"scope": "root-active"})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, list):
        return cached_payload

    categories = (
        db.query(Category)
        .filter(Category.is_active.is_(True), Category.parent_id.is_(None))
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    serialized = [_serialize_category(category) for category in categories]
    cache_set_json(cache_key, serialized, _CATEGORY_LIST_CACHE_TTL)
    return serialized


def get_category(slug: str, db: Session) -> Category:
    cache_key = build_versioned_cache_key("categories", "detail", {"slug": slug})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    cat = db.query(Category).filter(Category.slug == slug, Category.is_active.is_(True)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    serialized = _serialize_category(cat)
    cache_set_json(cache_key, serialized, _CATEGORY_DETAIL_CACHE_TTL)
    return serialized


def create_category(category: CategoryCreate, current_user: dict, db: Session) -> Category:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    if db.query(Category).filter(Category.slug == category.slug).first():
        raise HTTPException(status_code=409, detail="Slug already exists")
    db_cat = Category(**category.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    bump_cache_version("categories")
    return db_cat


def update_category(category_id: int, category: CategoryCreate, current_user: dict, db: Session) -> Category:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in category.model_dump().items():
        setattr(db_cat, k, v)
    db.commit()
    db.refresh(db_cat)
    bump_cache_version("categories")
    return db_cat

