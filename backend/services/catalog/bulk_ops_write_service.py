"""Catalog bulk operations write service (W1 transaction owner).

Owns the DB mutations behind admin bulk archive/restore/category-change so the
controller stays free of ``commit_only`` / ``bulk_soft_delete`` / ``bulk_restore``
calls. The soft-delete primitives live in ``utils.soft_delete`` (service-layer
only) and are invoked here.
"""
from __future__ import annotations

from typing import Any, List, Optional, Type

from sqlalchemy.orm import Session

from data.models import Category, Product
from utils.soft_delete import bulk_restore, bulk_soft_delete
import structlog
logger = structlog.get_logger(__name__)


def bulk_archive_entities(db: Session, model: Type[Any], record_ids: List[Any], acting_user: dict, reason: Optional[str] = None) -> dict:
    """Archive many records of *model* and return the result payload."""
    return bulk_soft_delete(db, model, record_ids, acting_user, reason)


def bulk_restore_entities(db: Session, model: Type[Any], record_ids: List[Any], acting_user: dict) -> dict:
    """Restore many archived records of *model* and return the result payload."""
    return bulk_restore(db, model, record_ids, acting_user)


def bulk_change_product_category(db: Session, product_ids: List[int], category_id: int) -> int:
    """Reassign products to a category and commit. Returns the count updated."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise ValueError("Category not found")
    updated = 0
    for pid in product_ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product and not product.is_deleted:
            product.category_id = category_id
            product.category = category.name
            updated += 1
    db.commit()
    return updated
