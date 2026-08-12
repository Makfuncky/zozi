"""Logistics-partner write operations.

This module centralises the ORM write helpers that the logistics partner
controller depends on. It replaces the previous re-export shim that only
forwarded a handful of symbols and raised ``NotImplementedError`` for every
other referenced handler.

Writes belong in the ``services`` layer (W1), so these helpers are permitted
to call ``db.add`` / ``db.flush`` / ``db.delete``. They deliberately do NOT
commit: the surrounding request/transaction boundary commits once. A few
backward-compatible symbols are still re-exported lazily to avoid the
import-time circular cycles that originally motivated the shim.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Type

import importlib
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    CityDistanceMatrix,
    CountryConfig,
    LogisticsCategoryPricingRule,
    LogisticsCODRemittanceReceipt,
    LogisticsPartner,
    LogisticsPartnerBankAccount,
    LogisticsPartnerLocation,
    LogisticsPartnerDocument,
    LogisticsPartnerPayout,
    LogisticsPartnerServiceArea,
    LogisticsPricingProfile,
    LogisticsSettlement,
    LogisticsVehicleRule,
    Notification,
    Order,
    OrderLogisticsAllocation,
    Shipment,
    ShipmentConfirmation,
    ShipmentEvent,
    TransactionLedger,
)
from utils.datetime_utils import utcnow as _utcnow  # noqa: F401
import structlog
logger = structlog.get_logger(__name__)

# Backward-compatible lazy re-exports. These targets live in modules that
# previously imported this shim, so resolving them lazily breaks the cycle.
_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_shipment": ("controllers.orders.logistics_controller", "create_shipment"),
    "create_logistics_partner": ("services.security.auth_write_service", "create_logistics_partner"),
    "delete_notification": ("services.comms.communication_write_service", "delete_notification"),
    "create_notification": ("services.comms.tickets_write_service", "create_notification"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _column_names(model: Type[Any]) -> set[str]:
    return {c.name for c in model.__table__.columns}


# Field-name aliases where the controller passes a key that does not match the
# underlying column (e.g. the document model stores ``doc_type``).
_ALIASES: dict[Type[Any], dict[str, str]] = {
    LogisticsPartnerDocument: {"document_type": "doc_type"},
}


def _new(model: Type[Any], db: Session, *, partner_id: int | None = None, **kwargs: Any) -> Any:
    """Instantiate ``model`` from ``kwargs`` (filtered to real columns, with
    alias resolution), set ``partner_id`` when applicable, stage and flush."""
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
    """Apply ``updates`` to ``obj``, writing only keys that map to real columns
    (alias-aware)."""
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
    # Route through the canonical soft-delete util so soft-delete fields,
    # actor bookkeeping and audit semantics stay consistent across the app.
    # ``skip_audit=True`` keeps this helper commit-free to honour the
    # module's single-transaction-boundary contract; the surrounding request
    # transaction commits once.
    from utils.soft_delete import soft_delete

    soft_delete(db, type(obj), obj.id, None, skip_audit=True)


# ── LogisticsPartnerServiceArea ──────────────────────────────────────────────
def create_logistics_partner_service_area(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsPartnerServiceArea, db, partner_id=partner_id, **payload)


def update_logistics_partner_service_area(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPartnerServiceArea, payload))


def delete_logistics_partner_service_area(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsPricingProfile ──────────────────────────────────────────────────
def create_pricing_profile(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsPricingProfile, db, partner_id=partner_id, **payload)


def update_pricing_profile(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPricingProfile, payload))


def delete_pricing_profile(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsCategoryPricingRule ─────────────────────────────────────────────
def create_pricing_rule(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsCategoryPricingRule, db, partner_id=partner_id, **payload)


def update_pricing_rule(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsCategoryPricingRule, payload))


def delete_pricing_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def delete_category_pricing_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsVehicleRule ─────────────────────────────────────────────────────
def create_vehicle_rule(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsVehicleRule, db, partner_id=partner_id, **payload)


def update_vehicle_rule(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsVehicleRule, payload))


def delete_vehicle_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsPartnerPayout ───────────────────────────────────────────────────
def create_logistics_partner_payout(
    db: Session,
    *,
    partner_id: int,
    amount: Any,
    method: str | None = None,
    notes: str | None = None,
    **kwargs: Any,
) -> Any:
    return _new(
        LogisticsPartnerPayout,
        db,
        partner_id=partner_id,
        amount=amount,
        method=method,
        notes=notes,
        **kwargs,
    )


def update_logistics_partner_payout(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPartnerPayout, updates))


def delete_logistics_partner_payout(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── ShipmentConfirmation ────────────────────────────────────────────────────
def create_shipment_confirmation(db: Session, **kwargs: Any) -> Any:
    return _new(ShipmentConfirmation, db, **kwargs)


# ── ShipmentEvent ────────────────────────────────────────────────────────────
def create_shipment_event(db: Session, **kwargs: Any) -> Any:
    return _new(ShipmentEvent, db, **kwargs)


# ── LogisticsPartnerBankAccount ──────────────────────────────────────────────
def create_logistics_partner_bank_account(db: Session, *, partner_id: int, **updates: Any) -> Any:
    return _new(LogisticsPartnerBankAccount, db, partner_id=partner_id, **updates)


def update_logistics_partner_bank_account(db: Session, account: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(account, LogisticsPartnerBankAccount, updates))


def delete_logistics_partner_bank_account(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsPartnerDocument ─────────────────────────────────────────────────
def create_logistics_partner_document(db: Session, *, partner_id: int, **kwargs: Any) -> Any:
    return _new(LogisticsPartnerDocument, db, partner_id=partner_id, **kwargs)


def update_logistics_partner_document(db: Session, doc: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(doc, LogisticsPartnerDocument, updates))


def delete_logistics_partner_document(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── CityDistanceMatrix ──────────────────────────────────────────────────────
def create_city_distance_matrix(db: Session, **kwargs: Any) -> Any:
    return _new(CityDistanceMatrix, db, **kwargs)


def update_city_distance_matrix(db: Session, matrix: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(matrix, CityDistanceMatrix, updates))


def delete_city_distance_matrix(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsSettlement ──────────────────────────────────────────────────────
def create_settlement(db: Session, **kwargs: Any) -> Any:
    return _new(LogisticsSettlement, db, **kwargs)


def update_settlement(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsSettlement, updates))


# ── TransactionLedger ───────────────────────────────────────────────────────
def create_transaction_ledger_entry(db: Session, **kwargs: Any) -> Any:
    return _new(TransactionLedger, db, **kwargs)


def update_transaction_ledger(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, TransactionLedger, updates))


# ── LogisticsCODRemittanceReceipt ───────────────────────────────────────────
def create_coding_remittance_receipt(db: Session, **kwargs: Any) -> Any:
    return _new(LogisticsCODRemittanceReceipt, db, **kwargs)


# ── LogisticsPartner (soft-delete) ──────────────────────────────────────────
def update_logistics_partner(db: Session, partner: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(partner, LogisticsPartner, updates))


def delete_logistics_partner(db: Session, partner: Any) -> None:
    _soft_delete(db, partner)


# ── Shipment (soft-delete) ──────────────────────────────────────────────────
def update_shipment(db: Session, shipment: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(shipment, Shipment, updates))


def delete_shipment(db: Session, shipment: Any) -> None:
    _soft_delete(db, shipment)


# ── Order ───────────────────────────────────────────────────────────────────
def update_order(db: Session, order: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(order, Order, updates))


# ── OrderLogisticsAllocation ────────────────────────────────────────────────
def update_order_logistics_allocation(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, OrderLogisticsAllocation, updates))


# ── Notification ─────────────────────────────────────────────────────────────
def update_notification(db: Session, notification: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(notification, Notification, updates))


# ── LogisticsPartnerLocation ─────────────────────────────────────────────────
def create_logistics_partner_location(db: Session, country_code: str, payload: dict[str, Any]) -> dict:
    """Create a location for a logistics partner in ``country_code``.

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_locations_create.create_logistics_partner_location``:
    validates the country and partner, stages the row and commits once.
    """
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


def list_logistics_partner_locations(
    db: Session,
    country_code: str,
    partner_id: int | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """List logistics-partner locations for a country (optionally filtered).

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_locations_create.list_logistics_partner_locations``.
    """
    query = db.query(LogisticsPartnerLocation).filter(
        LogisticsPartnerLocation.country_code == country_code.upper()
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(
        LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at
    ).all()
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


# ── Shipment (admin status update) ────────────────────────────────────────────
def admin_update_shipment_status(db: Session, shipment_id: int, data: dict[str, Any], current_user: Any) -> dict:
    """Admin-only direct shipment status update (bypasses supplier check).

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_logistics_status.admin_update_shipment_status``: enforces
    the admin role gate, records a ``ShipmentEvent``, commits once and returns the
    same response shape.
    """
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
