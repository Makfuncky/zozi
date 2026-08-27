"""Auto-migrated service logic from routers/wishlist.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session, selectinload

from infrastructure.database.database import get_db

from domains.catalog.models.products import Product
from domains.catalog.models.products import WishlistItem

from infrastructure.utils.dependencies import get_current_user

def _product_exists_for_wishlist(product_id: int, db: Session) -> bool:
    # Law 1 compliant: direct domain-level product lookup (no module layer import)
    product = db.query(Product).filter(Product.id == product_id).first()
    return product is not None

def get_wishlist(limit: int, offset: int, current_user: dict, db: Session):
    return db.query(WishlistItem).options(selectinload(WishlistItem.product)).filter(WishlistItem.user_id == current_user.get("id")).offset(max(0, offset)).limit(min(max(1, limit), 200)).all()

def add_to_wishlist(product_id: int, current_user: dict, db: Session):
    if not _product_exists_for_wishlist(product_id, db):
        raise HTTPException(status_code=404, detail="Product not found")
    if db.query(WishlistItem).filter(WishlistItem.user_id == current_user.get("id"), WishlistItem.product_id == product_id).first():
        return {"product_id": product_id, "detail": "Already in wishlist"}
    db.add(WishlistItem(user_id=current_user.get("id"), product_id=product_id))
    db.commit()
    return {"product_id": product_id, "detail": "Added to wishlist"}

def remove_from_wishlist(product_id: int, current_user: dict, db: Session):
    item = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.get("id"), WishlistItem.product_id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(item); db.commit()
    return {"product_id": product_id, "detail": "Removed from wishlist"}


