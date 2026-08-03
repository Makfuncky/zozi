"""Orders write service — DB write operations for orders and order items."""

from typing import Any

from sqlalchemy.orm import Session

from data.models import (
    Order,
    OrderItem,
    OrderNotification,
)


def add_and_flush(db: Session, obj: Any) -> Any:
    """Stage a new ORM object in the session and flush to obtain its PK."""
    db.add(obj)
    db.flush()
    return obj


def commit_and_refresh(db: Session, obj: Any) -> Any:
    """Commit the pending transaction and refresh the given object."""
    db.commit()
    db.refresh(obj)
    return obj


def commit_only(db: Session) -> None:
    """Commit the pending transaction without refreshing an object."""
    db.commit()


def create_order(db: Session, **order_data) -> Order:
    order = Order(**order_data)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order: Order, updates: dict) -> Order:
    for key, value in updates.items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order: Order) -> None:
    db.delete(order)
    db.commit()


def create_order_item(db: Session, order_id: int, **item_data) -> OrderItem:
    item = OrderItem(order_id=order_id, **item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_order_item(db: Session, item: OrderItem, updates: dict) -> OrderItem:
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_order_item(db: Session, item: OrderItem) -> None:
    db.delete(item)
    db.commit()


def create_order_notification(
    db: Session, user_id: int, order_id: int, **notification_data
) -> OrderNotification:
    notification = OrderNotification(
        user_id=user_id, order_id=order_id, **notification_data
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
