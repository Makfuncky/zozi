"""Orders write service — DB write operations for orders and order items."""

from sqlalchemy.orm import Session

from models import (
    Order,
    OrderItem,
    OrderNotification,
)


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