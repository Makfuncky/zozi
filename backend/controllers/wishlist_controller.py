"""
Wishlist Controller — persistent user wishlist CRUD logic.
"""
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Wishlist, Product


def get_wishlist(current_user: dict, db: Session) -> List[Wishlist]:
    return (
        db.query(Wishlist)
        .filter(Wishlist.user_id == current_user["id"])
        .order_by(Wishlist.created_at.desc())
        .all()
    )


def add_to_wishlist(product_id: int, current_user: dict, db: Session) -> Wishlist:
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user["id"],
        Wishlist.product_id == product_id,
    ).first()
    if existing:
        return existing  # idempotent

    item = Wishlist(user_id=current_user["id"], product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_wishlist(product_id: int, current_user: dict, db: Session) -> dict:
    item = db.query(Wishlist).filter(
        Wishlist.user_id == current_user["id"],
        Wishlist.product_id == product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in wishlist")
    db.delete(item)
    db.commit()
    return {"detail": "Removed from wishlist"}


def clear_wishlist(current_user: dict, db: Session) -> dict:
    db.query(Wishlist).filter(Wishlist.user_id == current_user["id"]).delete()
    db.commit()
    return {"detail": "Wishlist cleared"}

