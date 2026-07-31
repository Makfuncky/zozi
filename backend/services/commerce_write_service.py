"""Commerce write service — DB write operations for wishlist, reviews, and addresses."""
from typing import Optional

from sqlalchemy.orm import Session

from models import Address, Review, Wishlist


def create_wishlist_item(db: Session, user_id: int, product_id: int) -> Wishlist:
    item = Wishlist(user_id=user_id, product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_wishlist_item(db: Session, item: Wishlist) -> None:
    db.delete(item)
    db.commit()


def clear_wishlist(db: Session, user_id: int) -> None:
    db.query(Wishlist).filter(Wishlist.user_id == user_id).delete()
    db.commit()


def create_review(db: Session, **review_data) -> Review:
    review = Review(**review_data)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def update_review(db: Session, review: Review, updates: dict) -> Review:
    for key, value in updates.items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)
    return review


def soft_delete_review(db: Session, review: Review) -> None:
    review.is_deleted = True
    db.commit()


def create_address(db: Session, **address_data) -> Address:
    address = Address(**address_data)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, address: Address, updates: dict) -> Address:
    for key, value in updates.items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()


def set_default_address(db: Session, address: Address) -> Address:
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address


def unset_other_default_addresses(db: Session, user_id: int, exclude_address_id: int | None = None) -> None:
    query = db.query(Address).filter(Address.user_id == user_id, Address.is_default == True)
    if exclude_address_id is not None:
        query = query.filter(Address.id != exclude_address_id)
    for addr in query.all():
        addr.is_default = False
    db.commit()