"""Cart write service — DB write operations for cart items."""

from sqlalchemy.orm import Session

from models import CartItem


def create_cart_item(db: Session, **item_data) -> CartItem:
    item = CartItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_cart_item(db: Session, item: CartItem, updates: dict) -> CartItem:
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_cart_item(db: Session, item: CartItem) -> None:
    db.delete(item)
    db.commit()


def delete_cart_items_by_user(db: Session, user_id: int) -> None:
    db.query(CartItem).filter(CartItem.user_id == user_id).delete(synchronize_session=False)
    db.commit()


def delete_cart_items_by_filter(db: Session, filters) -> None:
    db.query(CartItem).filter(filters).delete()
    db.commit()


def commit_cart_items(db: Session) -> None:
    db.commit()