"""Payments write service — DB write operations for payment-related entities."""
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from models import (
    Coupon,
    Order,
    OrderItem,
    Payment,
    PaymentGatewayConnection,
    PaymentProviderConfig,
    Product,
    Notification,
    ProcessedWebhookEvent,
    TransactionLedger,
)


def create_payment(db: Session, **payment_data) -> Payment:
    payment = Payment(**payment_data)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def update_payment(db: Session, payment: Payment, updates: dict) -> Payment:
    for key, value in updates.items():
        setattr(payment, key, value)
    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(db: Session, payment: Payment) -> None:
    db.delete(payment)
    db.commit()


def create_payment_provider_config(db: Session, **config_data) -> PaymentProviderConfig:
    config = PaymentProviderConfig(**config_data)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_payment_provider_config(db: Session, config: PaymentProviderConfig, updates: dict) -> PaymentProviderConfig:
    for key, value in updates.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def delete_payment_provider_config(db: Session, config: PaymentProviderConfig) -> None:
    db.delete(config)
    db.commit()


def create_payment_gateway_connection(db: Session, **connection_data) -> PaymentGatewayConnection:
    connection = PaymentGatewayConnection(**connection_data)
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


def update_payment_gateway_connection(db: Session, connection: PaymentGatewayConnection, updates: dict) -> PaymentGatewayConnection:
    for key, value in updates.items():
        setattr(connection, key, value)
    db.commit()
    db.refresh(connection)
    return connection


def delete_payment_gateway_connection(db: Session, connection: PaymentGatewayConnection) -> None:
    db.delete(connection)
    db.commit()


def record_processed_webhook_event(
    db: Session, event_id: str, processor: str, payload_hash: Optional[str] = None
) -> ProcessedWebhookEvent:
    event = ProcessedWebhookEvent(
        event_id=event_id, processor=processor, payload_hash=payload_hash
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_notification(db: Session, **notification_data) -> Notification:
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def create_transaction_ledger_entry(db: Session, **ledger_data) -> TransactionLedger:
    entry = TransactionLedger(**ledger_data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_transaction_ledger(db: Session, entry: TransactionLedger, updates: dict) -> TransactionLedger:
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def create_coupon(db: Session, **coupon_data) -> Coupon:
    coupon = Coupon(**coupon_data)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(db: Session, coupon: Coupon, updates: dict) -> Coupon:
    for key, value in updates.items():
        setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    db.delete(coupon)
    db.commit()


def update_order(db: Session, order: Order, updates: dict) -> Order:
    for key, value in updates.items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


def create_order(db: Session, **order_data) -> Order:
    order = Order(**order_data)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


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


def create_payment_record(db: Session, order_id: int, **payment_data) -> Payment:
    payment = Payment(order_id=order_id, **payment_data)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def flush_model(db: Session, model) -> None:
    db.add(model)
    db.flush()


def commit_only(db: Session) -> None:
    db.commit()


def add_and_commit(db: Session, model) -> None:
    db.add(model)
    db.commit()


def add_notification(db: Session, **notification_data) -> Notification:
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()


def add_processed_webhook_event(
    db: Session, event_id: str, processor: str, payload_hash: Optional[str] = None
) -> ProcessedWebhookEvent:
    event = ProcessedWebhookEvent(event_id=event_id, processor=processor, payload_hash=payload_hash)
    db.add(event)
    db.commit()


def update_payment_provider_config_no_refresh(db: Session, config: PaymentProviderConfig, updates: dict) -> PaymentProviderConfig:
    for key, value in updates.items():
        setattr(config, key, value)
    db.commit()
    return config


def upsert_payment_provider_config(db: Session, config_data: dict) -> PaymentProviderConfig:
    config = db.query(PaymentProviderConfig).first()
    if config is None:
        config = PaymentProviderConfig(**config_data)
        db.add(config)
    else:
        for key, value in config_data.items():
            setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def update_gateway_connection(db: Session, connection: PaymentGatewayConnection, updates: dict) -> PaymentGatewayConnection:
    for key, value in updates.items():
        setattr(connection, key, value)
    db.commit()
    db.refresh(connection)
    return connection


def create_or_update_gateway_connection(db: Session, **connection_data) -> PaymentGatewayConnection:
    connection = PaymentGatewayConnection(**connection_data)
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection