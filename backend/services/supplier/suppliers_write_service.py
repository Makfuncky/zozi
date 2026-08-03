"""Suppliers write service — DB write operations for supplier-related entities."""
from typing import Optional, cast

from sqlalchemy.orm import Session

from data.models import (
    Payout,
    Shipment,
    ShipmentEvent,
    SupplierBankAccount,
    SupplierDocument,
    SupplierProfile,
    SupplierSettlement,
)


def create_supplier_profile(db: Session, user_id: int, **profile_data) -> SupplierProfile:
    profile = SupplierProfile(user_id=user_id, **profile_data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_supplier_profile(db: Session, profile: SupplierProfile, updates: dict) -> SupplierProfile:
    for key, value in updates.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def delete_supplier_profile(db: Session, profile: SupplierProfile) -> None:
    db.delete(profile)
    db.commit()


def create_supplier_document(db: Session, supplier_id: int, **doc_data) -> SupplierDocument:
    doc = SupplierDocument(supplier_id=supplier_id, **doc_data)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_supplier_document(db: Session, doc: SupplierDocument, updates: dict) -> SupplierDocument:
    for key, value in updates.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return doc


def delete_supplier_document(db: Session, doc: SupplierDocument) -> None:
    db.delete(doc)
    db.commit()


def create_payout(db: Session, **payout_data) -> Payout:
    payout = Payout(**payout_data)
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


def update_payout(db: Session, payout: Payout, updates: dict) -> Payout:
    for key, value in updates.items():
        setattr(payout, key, value)
    db.commit()
    db.refresh(payout)
    return payout


def delete_payout(db: Session, payout: Payout) -> None:
    db.delete(payout)
    db.commit()


def create_supplier_bank_account(db: Session, **account_data) -> SupplierBankAccount:
    account = SupplierBankAccount(**account_data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_supplier_bank_account(db: Session, account: SupplierBankAccount, updates: dict) -> SupplierBankAccount:
    for key, value in updates.items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


def delete_supplier_bank_account(db: Session, account: SupplierBankAccount) -> None:
    db.delete(account)
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


def create_supplier_settlement(db: Session, **settlement_data) -> SupplierSettlement:
    settlement = SupplierSettlement(**settlement_data)
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def update_supplier_settlement(db: Session, settlement: SupplierSettlement, updates: dict) -> SupplierSettlement:
    for key, value in updates.items():
        setattr(settlement, key, value)
    db.commit()
    db.refresh(settlement)
    return settlement


def delete_supplier_settlement(db: Session, settlement: SupplierSettlement) -> None:
    db.delete(settlement)
    db.commit()


def commit_only(db: Session) -> None:
    db.commit()


def refresh_model(db: Session, model) -> None:
    db.refresh(model)


def add_and_flush(db: Session, model) -> None:
    db.add(model)
    db.flush()


def add_notification(db: Session, **notification_data) -> "Notification":
    from data.models import Notification
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    return notification


def add_to_session(db: Session, model) -> None:
    db.add(model)


def flush_session(db: Session) -> None:
    db.flush()


def commit_session(db: Session) -> None:
    """Commit the current session (bulk/batch flows)."""
    db.commit()


def commit_and_refresh(db: Session, *objects) -> None:
    """Commit then refresh each provided ORM object in one call."""
    db.commit()
    for obj in objects:
        db.refresh(obj)


def stage_notification(db: Session, **notification_data) -> "Notification":
    """Queue a Notification in the session WITHOUT committing (caller owns the transaction)."""
    from data.models import Notification

    notification = Notification(**notification_data)
    db.add(notification)
    return notification


def create_supplier_payout_request(
    db: Session,
    *,
    supplier_id: int,
    amount: float,
    method: str,
    notes: Optional[str],
    country_code: Optional[str],
) -> Payout:
    """Create a supplier payout with a generated transfer reference and a notification, in one transaction."""
    from services.finance_transfer_service import build_transfer_reference

    payout = Payout(
        supplier_id=supplier_id,
        amount=float(amount),
        method=method,
        notes=notes,
        country_code=country_code,
    )
    db.add(payout)
    db.flush()
    payout.reference_id = build_transfer_reference(
        db,
        kind="supplier_payout",
        entity_id=int(supplier_id),
        record_id=int(cast(int, payout.id)),
    )
    stage_notification(
        db,
        user_id=supplier_id,
        type="payout",
        title="Payout Request Received",
        message=f"Your payout request of {amount} AED has been submitted and is under review.",
        link="/supplier/payouts",
    )
    db.commit()
    db.refresh(payout)
    return payout