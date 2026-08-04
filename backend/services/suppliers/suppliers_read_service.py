"""Service methods for supplier read operations."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import Supplier, Product


def get_all_suppliers(db: Session, skip: int = 0, limit: int = 20) -> list[Supplier]:
    """Get all suppliers with pagination."""
    return (
        db.query(Supplier)
        .order_by(Supplier.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_supplier_by_id(db: Session, supplier_id: int) -> Supplier | None:
    """Get a supplier by ID."""
    return db.query(Supplier).filter(Supplier.id == supplier_id).first()


def search_suppliers(
    db: Session,
    query: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Supplier]:
    """Search suppliers with filters."""
    q = db.query(Supplier)
    if query:
        q = q.filter(Supplier.name.contains(query) | Supplier.email.contains(query))
    if status:
        q = q.filter(Supplier.status == status)
    return q.order_by(Supplier.created_at.desc()).offset(skip).limit(limit).all()


def get_supplier_products(
    db: Session, supplier_id: int, skip: int = 0, limit: int = 20
) -> list[Product]:
    """Get products for a supplier."""
    return (
        db.query(Product)
        .filter(Product.supplier_id == supplier_id)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_supplier_metrics(db: Session, supplier_id: int) -> dict:
    """Get supplier performance metrics."""
    from sqlalchemy import func as sqlfunc
    products = (
        db.query(sqlfunc.count(Product.id))
        .filter(Product.supplier_id == supplier_id)
        .scalar()
        or 0
    )
    return {"product_count": products}
