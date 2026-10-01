"""Governance domain — product administration service (keyset pagination)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.catalog.models.products import Product
from infrastructure.utils.pagination import keyset_offset_window


def get_all_products(
    db: Session,
    offset: int = 0,
    limit: int = 50,
    moderation_status: str | None = None,
    is_active: bool | None = None,
    is_deleted: bool = False,
) -> dict:
    """Adoption-layer admin product list using keyset_offset_window."""
    query = db.query(Product)
    if moderation_status:
        query = query.filter(Product.moderation_status == moderation_status)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if not is_deleted:
        query = query.filter(Product.is_deleted == False)
    items = keyset_offset_window(
        query,
        sort_keys=[(Product.created_at, "desc"), (Product.id, "desc")],
        offset=offset,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price": float(p.price) if p.price is not None else None,
                "stock": p.stock,
                "supplier_id": p.supplier_id,
                "category": p.category,
                "moderation_status": p.moderation_status,
                "is_active": p.is_active,
                "is_deleted": p.is_deleted,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in items
        ],
        "count": len(items),
    }
