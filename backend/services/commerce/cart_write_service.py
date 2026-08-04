"""Cart write service — DB write operations for cart items."""

from typing import Optional

from sqlalchemy.orm import Session, joinedload, selectinload

from data.models import CartItem, Product


def load_cart_items(db: Session, user_id: int) -> list[CartItem]:
    """Return all cart items for *user_id* with product + variants preloaded."""
    return (
        db.query(CartItem)
        .options(joinedload(CartItem.product).selectinload(Product.variants))
        .filter(CartItem.user_id == user_id)
        .all()
    )


def get_products_by_ids(db: Session, product_ids: list[int]) -> list[Product]:
    """Return non-deleted products with variants preloaded for the given IDs."""
    return (
        db.query(Product)
        .options(selectinload(Product.variants))
        .filter(
            Product.id.in_(product_ids),
            Product.is_deleted.is_(False),
        )
        .all()
    )


def get_active_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Return a non-deleted product with variants preloaded, or None."""
    return (
        db.query(Product)
        .options(selectinload(Product.variants))
        .filter(
            Product.id == product_id,
            Product.is_deleted.is_(False),
        )
        .first()
    )


def get_cart_item_by_variant(
    db: Session,
    user_id: int,
    product_id: int,
    selected_size: str,
    selected_color: str,
) -> Optional[CartItem]:
    """Return a single cart item matching the given variant, or None."""
    return (
        db.query(CartItem)
        .filter(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
            CartItem.selected_size == selected_size,
            CartItem.selected_color == selected_color,
        )
        .first()
    )


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


def delete_cart_item_by_variant(
    db: Session,
    user_id: int,
    product_id: int,
    selected_size: str | None,
    selected_color: str | None,
) -> None:
    from data.models import CartItem
    normalized_size = (selected_size or "").strip()
    normalized_color = (selected_color or "").strip()
    db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id,
        CartItem.selected_size == normalized_size,
        CartItem.selected_color == normalized_color,
    ).delete(synchronize_session=False)
    db.commit()


def delete_cart_items_by_user(db: Session, user_id: int) -> None:
    db.query(CartItem).filter(CartItem.user_id == user_id).delete(synchronize_session=False)
    db.commit()


def delete_cart_items_by_filter(db: Session, filters) -> None:
    db.query(CartItem).filter(filters).delete()
    db.commit()


def commit_cart_items(db: Session) -> None:
    db.commit()


def upsert_cart_item(
    db: Session,
    user_id: int,
    product_id: int,
    quantity: int,
    selected_size: str,
    selected_color: str,
    existing: CartItem | None = None,
) -> CartItem:
    if existing:
        existing.quantity = quantity
        db.commit()
        db.refresh(existing)
        return existing
    else:
        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            selected_size=selected_size,
            selected_color=selected_color,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


def sync_cart_items(
    db: Session,
    user_id: int,
    actions: list[dict],
) -> None:
    """Apply a list of add/update/delete actions for cart items."""
    for action in actions:
        op = action.get("op")
        if op == "delete":
            item = action.get("item")
            if item:
                db.delete(item)
        elif op == "upsert":
            item = action.get("item")
            if item:
                db.add(item)
    db.commit()