"""Logistics domain — sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain reads may ONLY happen through a
publishing domain's ports.py. Other domains import these functions instead of
importing domains.logistics.models or domains.logistics.services directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via rbac).

This file mirrors the domain-level ``domains/logistics/ports.py`` surface so that
service-layer consumers can import from the canonical services path.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from .events import LogisticsEvent  # noqa: F401 — re-export for type hints


def _get_models():
    from domains.logistics.models.logistics import (
        LogisticsPartner,
        LogisticsPartnerProfile,
        LogisticsPricingProfile,
        Shipment,
        ShipmentEvent,
    )
    return LogisticsPartner, LogisticsPartnerProfile, LogisticsPricingProfile, Shipment, ShipmentEvent


def get_logistics_partner_by_id(db: Session, id_: int) -> Optional[object]:
    """Return LogisticsPartner by primary key (or None)."""
    LogisticsPartner, *_ = _get_models()
    return db.get(LogisticsPartner, id_)


def list_logistics_partners(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` LogisticsPartner rows."""
    LogisticsPartner, *_ = _get_models()
    return db.query(LogisticsPartner).limit(limit).all()


def get_logistics_partner_profile_by_id(db: Session, id_: int) -> Optional[object]:
    """Return LogisticsPartnerProfile by primary key (or None)."""
    _, LogisticsPartnerProfile, *_ = _get_models()
    return db.get(LogisticsPartnerProfile, id_)


def list_logistics_partner_profiles(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` LogisticsPartnerProfile rows."""
    _, LogisticsPartnerProfile, *_ = _get_models()
    return db.query(LogisticsPartnerProfile).limit(limit).all()


def get_logistics_pricing_profile_by_id(db: Session, id_: int) -> Optional[object]:
    """Return LogisticsPricingProfile by primary key (or None)."""
    _, _, LogisticsPricingProfile, *_ = _get_models()
    return db.get(LogisticsPricingProfile, id_)


def list_logistics_pricing_profiles(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` LogisticsPricingProfile rows."""
    _, _, LogisticsPricingProfile, *_ = _get_models()
    return db.query(LogisticsPricingProfile).limit(limit).all()


def get_shipment_by_id(db: Session, id_: int) -> Optional[object]:
    """Return Shipment by primary key (or None)."""
    *_, Shipment, _ = _get_models()
    return db.get(Shipment, id_)


def list_shipments(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` Shipment rows."""
    *_, Shipment, _ = _get_models()
    return db.query(Shipment).limit(limit).all()


def get_shipment_event_by_id(db: Session, id_: int) -> Optional[object]:
    """Return ShipmentEvent by primary key (or None)."""
    *_, ShipmentEvent = _get_models()
    return db.get(ShipmentEvent, id_)


def list_shipment_events(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` ShipmentEvent rows."""
    *_, ShipmentEvent = _get_models()
    return db.query(ShipmentEvent).limit(limit).all()


__all__ = [
    "get_logistics_partner_by_id",
    "list_logistics_partners",
    "get_logistics_partner_profile_by_id",
    "list_logistics_partner_profiles",
    "get_logistics_pricing_profile_by_id",
    "list_logistics_pricing_profiles",
    "get_shipment_by_id",
    "list_shipments",
    "get_shipment_event_by_id",
    "list_shipment_events",
]
