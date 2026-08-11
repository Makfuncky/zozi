"""Admin product mutation write service (W1 transaction owner).

Owns every DB write behind the admin product controller so that
``controllers.catalog.products`` never calls ``commit_only`` or mutates ORM rows
directly. Reads stay in the controller via ``services.common.db_read``.
"""
from __future__ import annotations

from typing import Any, List

from sqlalchemy.orm import Session

from data.models import Product
import structlog
logger = structlog.get_logger(__name__)


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
