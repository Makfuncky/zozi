"""Wishlist router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from controllers.products_controller import get_products as get_products_controller
from db.database import get_db
from models import WishlistItem, Product, User
from utils.dependencies import get_current_user

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
def get_wishlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()

@router.post("/{product_id}")
def add_to_wishlist(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _product_exists_for_wishlist(product_id, db):
        raise HTTPException(status_code=404, detail="Product not found")
    if db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id).first():
        return {"product_id": product_id, "detail": "Already in wishlist"}
    db.add(WishlistItem(user_id=current_user.id, product_id=product_id))
    db.commit()
    return {"product_id": product_id, "detail": "Added to wishlist"}

@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(item); db.commit()
    return {"product_id": product_id, "detail": "Removed from wishlist"}

