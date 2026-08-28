from __future__ import annotations

"""Logistics partner write operations."""

from datetime import datetime, timezone
from typing import Any, Type
from fastapi import HTTPException
from sqlalchemy.orm import Session
from domains.governance.models.core import CityDistanceMatrix
from domains.comms.models.communication import Notification
from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics_country_sync import LogisticsPartnerLocation
from domains.finance.models.finance import TransactionLedger
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.governance.models.admin import LogisticsPartnerBankAccount
from domains.governance.models.admin import LogisticsPartnerDocument
from domains.governance.models.admin import LogisticsSettlement
from domains.governance.models.admin import ShipmentConfirmation
from domains.logistics.models.logistics import LogisticsCategoryPricingRule
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.logistics.models.logistics import Shipment, ShipmentEvent
from domains.orders.models.order_entities import Order, OrderLogisticsAllocation
from domains.finance.models.payments import LogisticsPartnerPayout
import structlog

logger = structlog.get_logger(__name__)

_ALIASES: dict[Type[Any], dict[str, str]] = {
    LogisticsPartnerDocument: {"document_type": "doc_type"},
}


def _column_names(model: Type[Any]) -> set[str]:
    return {c.name for c in model.__table__.columns}


def _new(model: Type[Any], db: Session, *, partner_id: int | None = None, **kwargs: Any) -> Any:
    cols = _column_names(model)
    aliases = _ALIASES.get(model, {})
    data: dict[str, Any] = {}
    for key, value in kwargs.items():
        target = aliases.get(key, key)
        if target in cols:
            data[target] = value
    if partner_id is not None and "partner_id" in cols:
        data["partner_id"] = partner_id
    obj = model(**data)
    db.add(obj)
    db.flush()
    return obj


def _apply(obj: Any, model: Type[Any], updates: dict[str, Any]) -> Any:
    cols = _column_names(model)
    aliases = _ALIASES.get(model, {})
    for key, value in updates.items():
        target = aliases.get(key, key)
        if target in cols:
            setattr(obj, target, value)
    return obj


def _save(db: Session, obj: Any) -> Any:
    db.flush()
    return obj


def _hard_delete(db: Session, obj: Any) -> None:
    db.delete(obj)
    db.flush()


def _soft_delete(db: Session, obj: Any) -> None:
    from infrastructure.utils.soft_delete import soft_delete
    soft_delete(db, type(obj), obj.id, None, skip_audit=True)


def create_logistics_partner_service_area(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsPartnerServiceArea, db, partner_id=partner_id, **payload)


def update_logistics_partner_service_area(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPartnerServiceArea, payload))


def delete_logistics_partner_service_area(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_pricing_profile(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsPricingProfile, db, partner_id=partner_id, **payload)


def update_pricing_profile(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPricingProfile, payload))


def delete_pricing_profile(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_pricing_rule(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsCategoryPricingRule, db, partner_id=partner_id, **payload)


def update_pricing_rule(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsCategoryPricingRule, payload))


def delete_pricing_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def delete_category_pricing_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_vehicle_rule(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsVehicleRule, db, partner_id=partner_id, **payload)


def update_vehicle_rule(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsVehicleRule, payload))


def delete_vehicle_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_logistics_partner_payout(db: Session, *, partner_id: int, amount: Any, method: str | None = None, notes: str | None = None, **kwargs: Any) -> Any:
    return _new(LogisticsPartnerPayout, db, partner_id=partner_id, amount=amount, method=method, notes=notes, **kwargs)


def update_logistics_partner_payout(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPartnerPayout, updates))


def delete_logistics_partner_payout(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_shipment_confirmation(db: Session, **kwargs: Any) -> Any:
    return _new(ShipmentConfirmation, db, **kwargs)


def create_shipment_event(db: Session, **kwargs: Any) -> Any:
    return _new(ShipmentEvent, db, **kwargs)


def create_logistics_partner_bank_account(db: Session, *, partner_id: int, **updates: Any) -> Any:
    return _new(LogisticsPartnerBankAccount, db, partner_id=partner_id, **updates)


def update_logistics_partner_bank_account(db: Session, account: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(account, LogisticsPartnerBankAccount, updates))


def delete_logistics_partner_bank_account(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_logistics_partner_document(db: Session, *, partner_id: int, **kwargs: Any) -> Any:
    return _new(LogisticsPartnerDocument, db, partner_id=partner_id, **kwargs)


def update_logistics_partner_document(db: Session, doc: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(doc, LogisticsPartnerDocument, updates))


def delete_logistics_partner_document(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_city_distance_matrix(db: Session, **kwargs: Any) -> Any:
    return _new(CityDistanceMatrix, db, **kwargs)


def update_city_distance_matrix(db: Session, matrix: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(matrix, CityDistanceMatrix, updates))


def delete_city_distance_matrix(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def create_settlement(db: Session, **kwargs: Any) -> Any:
    return _new(LogisticsSettlement, db, **kwargs)


def update_settlement(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsSettlement, updates))


def create_transaction_ledger_entry(db: Session, **kwargs: Any) -> Any:
    return _new(TransactionLedger, db, **kwargs)


def update_transaction_ledger(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, TransactionLedger, updates))


def create_coding_remittance_receipt(db: Session, **kwargs: Any) -> Any:
    return _new(LogisticsCODRemittanceReceipt, db, **kwargs)


def update_logistics_partner(db: Session, partner: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(partner, LogisticsPartner, updates))


def delete_logistics_partner(db: Session, partner: Any) -> None:
    _soft_delete(db, partner)


def update_shipment(db: Session, shipment: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(shipment, Shipment, updates))


def delete_shipment(db: Session, shipment: Any) -> None:
    _soft_delete(db, shipment)


def update_order(db: Session, order: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(order, Order, updates))


def update_order_logistics_allocation(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, OrderLogisticsAllocation, updates))


def update_notification(db: Session, notification: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(notification, Notification, updates))


def create_logistics_partner_location(db: Session, country_code: str, payload: dict[str, Any]) -> dict:
    config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    partner_id = payload.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=422, detail="partner_id is required")
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found")
    location = LogisticsPartnerLocation(
        country_code=country_code.upper(),
        partner_id=partner_id,
        location_type=payload.get("location_type", "warehouse"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        address=payload.get("address"),
        is_active=payload.get("is_active", True),
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return {"id": location.id, "message": "Logistics partner location created"}


def list_logistics_partner_locations(db: Session, country_code: str, partner_id: int | None = None, is_active: bool | None = None) -> list[dict[str, Any]]:
    query = db.query(LogisticsPartnerLocation).filter(LogisticsPartnerLocation.country_code == country_code.upper())
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at).all()
    return [
        {
            "id": loc.id,
            "partner_id": loc.partner_id,
            "location_type": loc.location_type,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": loc.address,
            "is_active": loc.is_active,
            "created_at": loc.created_at,
        }
        for loc in locations
    ]


def admin_update_shipment_status(db: Session, shipment_id: int, data: dict[str, Any], current_user: Any) -> dict:
    role = (current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)) or ""
    if str(role).lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    new_status = data.get("status")
    if new_status:
        shipment.status = new_status
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if new_status == "delivered" and not shipment.actual_delivery:
            shipment.actual_delivery = now
        elif new_status == "shipped" and not shipment.shipped_at:
            shipment.shipped_at = now
        event = ShipmentEvent(
            shipment_id=shipment_id,
            event_type="status_change",
            status_after=new_status,
            location=shipment.current_hub,
            notes=data.get("note", "Admin status update"),
            created_at=now,
        )
        db.add(event)
    db.commit()
    db.refresh(shipment)
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
    }
