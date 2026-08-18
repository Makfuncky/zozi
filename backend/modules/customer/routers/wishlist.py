"""Wishlist router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from domains.catalog.services.products_controller import get_products as get_products_controller
from infrastructure.database.database import get_db
from domains.catalog.models.products import Product
from domains.catalog.models.products import WishlistItem
from infrastructure.utils.dependencies import get_current_user

router = APIRouter()


def _product_exists_for_wishlist(product_id: int, db: Session) -> bool:
    if db.query(Product).filter(Product.id == product_id).first() is not None:
        return True

    # Keep wishlist compatibility with IDs coming from the public /products feed,
    # even when a stale cache makes direct row lookup inconsistent.
    try:
        visible_products = get_products_controller(
            db=db,
            response=None,
            limit=500,
            offset=0,
        )
    except Exception:
        return False

    for entry in visible_products:
        candidate_id = entry.get("id") if isinstance(entry, dict) else getattr(entry, "id", None)
        if candidate_id == product_id:
            return True
    return False

@router.get("")
def get_wishlist(limit: int = 200, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(WishlistItem).options(selectinload(WishlistItem.product)).filter(WishlistItem.user_id == current_user.get("id")).offset(max(0, offset)).limit(min(max(1, limit), 200)).all()

@router.post("/{product_id}")
def add_to_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _product_exists_for_wishlist(product_id, db):
        raise HTTPException(status_code=404, detail="Product not found")
    if db.query(WishlistItem).filter(WishlistItem.user_id == current_user.get("id"), WishlistItem.product_id == product_id).first():
        return {"product_id": product_id, "detail": "Already in wishlist"}
    db.add(WishlistItem(user_id=current_user.get("id"), product_id=product_id))
    db.commit()
    return {"product_id": product_id, "detail": "Added to wishlist"}

@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.get("id"), WishlistItem.product_id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(item); db.commit()
    return {"product_id": product_id, "detail": "Removed from wishlist"}

