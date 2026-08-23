"""Admin product mutation write service (W1 transaction owner).

Owns every DB write behind the admin product controller so that
``controllers.catalog.products`` never calls ``commit_only`` or mutates ORM rows
directly. Reads stay in the controller via ``services.common.db_read``.
"""
from __future__ import annotations

from typing import Any, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product
import structlog
logger = structlog.get_logger(__name__)

from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context


def _bump_cache() -> None:
    from domains.catalog.services.products.products_service import _bump_product_cache_version

    _bump_product_cache_version()


def _scoped_product(db: Session, country_code: str, product_id: int) -> Product:
    """Resolve a product scoped to a country (404 + request RLS)."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        product = db.query(Product).filter(Product.id == product_id, Product.country_code == code).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    finally:
        clear_rls_context()


def approve_product_by_id(db: Session, country_code: str, product_id: int) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = "approved"
    product.is_verified = True
    db.commit()
    _bump_cache()
    return {"message": "Product approved"}


def reject_product_by_id(db: Session, country_code: str, product_id: int, reason: Optional[str] = None) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = "rejected"
    product.moderation_notes = reason
    db.commit()
    _bump_cache()
    return {"message": "Product rejected"}


def set_product_badge_by_id(db: Session, country_code: str, product_id: int, field: str, value: bool) -> dict:
    if field not in ("is_hot", "is_featured"):
        raise HTTPException(status_code=400, detail="field must be 'is_hot' or 'is_featured'")
    product = _scoped_product(db, country_code, product_id)
    setattr(product, field, value)
    db.commit()
    _bump_cache()
    return {"message": "Product badge updated", "field": field, "value": value}


def bulk_soft_delete_products(db: Session, products: List[Product]) -> None:
    """Flag many products as deleted and commit once."""
    for product in products:
        setattr(product, "is_deleted", True)
    if products:
        db.commit()


def bulk_moderate_products(db: Session, products: List[Product], action: str) -> None:
    """Approve or reject many products and commit once."""
    for product in products:
        if action == "approve":
            setattr(product, "is_approved", True)
            setattr(product, "is_active", True)
        else:
            setattr(product, "is_approved", False)
            setattr(product, "is_active", False)
    if products:
        db.commit()


def soft_delete_product(db: Session, product: Product) -> None:
    setattr(product, "is_deleted", True)
    db.commit()


def restore_product(db: Session, product: Product) -> None:
    setattr(product, "is_deleted", False)
    db.commit()


def set_product_badge(db: Session, product: Product, field: str, value: bool) -> None:
    setattr(product, field, value)
    db.commit()


def approve_product(db: Session, product: Product) -> None:
    setattr(product, "is_approved", True)
    setattr(product, "is_active", True)
    db.commit()


def reject_product(db: Session, product: Product) -> None:
    setattr(product, "is_approved", False)
    setattr(product, "is_active", False)
    db.commit()
