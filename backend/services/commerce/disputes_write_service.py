"""Disputes write service — DB write operations for dispute and notification entities."""

from sqlalchemy.orm import Session

from data.models import (
    Notification,
    SupplierDispute,
    SupplierNotificationPreference,
)


def create_supplier_notification_preference(
    db: Session, supplier_id: int, **prefs_data
) -> SupplierNotificationPreference:
    prefs = SupplierNotificationPreference(supplier_id=supplier_id, **prefs_data)
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


def update_supplier_notification_preference(
    db: Session, prefs: SupplierNotificationPreference, updates: dict
) -> SupplierNotificationPreference:
    for key, value in updates.items():
        setattr(prefs, key, value)
    db.commit()
    db.refresh(prefs)
    return prefs


def create_supplier_dispute(db: Session, **dispute_data) -> SupplierDispute:
    dispute = SupplierDispute(**dispute_data)
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute


def create_dispute_notification(db: Session, **notification_data) -> Notification:
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    return notification


def update_supplier_dispute(
    db: Session, dispute: SupplierDispute, updates: dict
) -> SupplierDispute:
    for key, value in updates.items():
        setattr(dispute, key, value)
    db.commit()
    db.refresh(dispute)
    return dispute


def create_dispute_notification_for_update(
    db: Session, **notification_data
) -> Notification:
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    return notification


def bulk_update_disputes(
    db: Session, disputes: list[SupplierDispute], updates: dict
) -> list[SupplierDispute]:
    for dispute in disputes:
        for key, value in updates.items():
            setattr(dispute, key, value)
    db.commit()
    return disputes