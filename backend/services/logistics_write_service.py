"""Logistics write service — DB write operations for shipping carriers, zones, shipments, and events."""
from typing import Optional

from sqlalchemy.orm import Session

from models import (
    Notification,
    Shipment,
    ShipmentEvent,
    ShippingCarrier,
    ShippingZone,
)


def create_shipping_carrier(db: Session, **carrier_data) -> ShippingCarrier:
    carrier = ShippingCarrier(**carrier_data)
    db.add(carrier)
    db.commit()
    db.refresh(carrier)
    return carrier


def update_shipping_carrier(db: Session, carrier: ShippingCarrier, updates: dict) -> ShippingCarrier:
    for key, value in updates.items():
        setattr(carrier, key, value)
    db.commit()
    db.refresh(carrier)
    return carrier


def delete_shipping_carrier(db: Session, carrier: ShippingCarrier) -> None:
    db.delete(carrier)
    db.commit()


def create_shipping_zone(db: Session, **zone_data) -> ShippingZone:
    zone = ShippingZone(**zone_data)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def update_shipping_zone(db: Session, zone: ShippingZone, updates: dict) -> ShippingZone:
    for key, value in updates.items():
        setattr(zone, key, value)
    db.commit()
    db.refresh(zone)
    return zone


def delete_shipping_zone(db: Session, zone: ShippingZone) -> None:
    db.delete(zone)
    db.commit()


def create_shipment(db: Session, **shipment_data) -> Shipment:
    shipment = Shipment(**shipment_data)
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


def update_shipment(db: Session, shipment: Shipment, updates: dict) -> Shipment:
    for key, value in updates.items():
        setattr(shipment, key, value)
    db.commit()
    db.refresh(shipment)
    return shipment


def delete_shipment(db: Session, shipment: Shipment) -> None:
    db.delete(shipment)
    db.commit()


def create_shipment_event(db: Session, **event_data) -> ShipmentEvent:
    event = ShipmentEvent(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_shipment_event(db: Session, event: ShipmentEvent, updates: dict) -> ShipmentEvent:
    for key, value in updates.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event


def delete_shipment_event(db: Session, event: ShipmentEvent) -> None:
    db.delete(event)
    db.commit()


def create_notification(db: Session, **notification_data) -> Notification:
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def update_notification(db: Session, notification: Notification, updates: dict) -> Notification:
    for key, value in updates.items():
        setattr(notification, key, value)
    db.commit()
    db.refresh(notification)
    return notification


def delete_notification(db: Session, notification: Notification) -> None:
    db.delete(notification)
    db.commit()


def add_and_flush(db: Session, model) -> None:
    db.add(model)
    db.flush()


def commit_only(db: Session) -> None:
    db.commit()


def refresh_model(db: Session, model) -> None:
    db.refresh(model)