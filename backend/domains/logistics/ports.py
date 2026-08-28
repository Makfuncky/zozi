"""logistics domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.logistics.models`` or ``domains.logistics.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so cross-domain consumers are unaffected, but they are now sourced via keyset
# (stable ``id`` order, no OFFSET). The ``*_page`` companions return a ``CursorPage``
# for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)

from domains.logistics.models.logistics import LogisticsCategoryPricingRule, LogisticsPartner, LogisticsPartnerProfile, LogisticsPartnerServiceArea, LogisticsPricingProfile, LogisticsVehicleRule, Shipment, ShipmentEvent
from domains.logistics.models.logistics_schema_models import CityDistanceMatrix  # A3: sanctioned ports surface for accounts hub


def get_logistics_partner_by_id(db: Session, id_: int) -> Optional[LogisticsPartner]:
    """Return LogisticsPartner by primary key (or None)."""
    return db.get(LogisticsPartner, id_)

def list_logistics_partners(db: Session, limit: int = 100) -> List[LogisticsPartner]:
    """Return up to ``limit`` LogisticsPartner rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsPartner, db, limit)

def list_logistics_partners_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsPartner rows (scale-ready)."""
    return _keyset_page(LogisticsPartner, db, cursor, page_size)

def get_logistics_partner_profile_by_id(db: Session, id_: int) -> Optional[LogisticsPartnerProfile]:
    """Return LogisticsPartnerProfile by primary key (or None)."""
    return db.get(LogisticsPartnerProfile, id_)

def list_logistics_partner_profiles(db: Session, limit: int = 100) -> List[LogisticsPartnerProfile]:
    """Return up to ``limit`` LogisticsPartnerProfile rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsPartnerProfile, db, limit)

def list_logistics_partner_profiles_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsPartnerProfile rows (scale-ready)."""
    return _keyset_page(LogisticsPartnerProfile, db, cursor, page_size)

def get_logistics_partner_service_area_by_id(db: Session, id_: int) -> Optional[LogisticsPartnerServiceArea]:
    """Return LogisticsPartnerServiceArea by primary key (or None)."""
    return db.get(LogisticsPartnerServiceArea, id_)

def list_logistics_partner_service_areas(db: Session, limit: int = 100) -> List[LogisticsPartnerServiceArea]:
    """Return up to ``limit`` LogisticsPartnerServiceArea rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsPartnerServiceArea, db, limit)

def list_logistics_partner_service_areas_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsPartnerServiceArea rows (scale-ready)."""
    return _keyset_page(LogisticsPartnerServiceArea, db, cursor, page_size)

def get_logistics_pricing_profile_by_id(db: Session, id_: int) -> Optional[LogisticsPricingProfile]:
    """Return LogisticsPricingProfile by primary key (or None)."""
    return db.get(LogisticsPricingProfile, id_)

def list_logistics_pricing_profiles(db: Session, limit: int = 100) -> List[LogisticsPricingProfile]:
    """Return up to ``limit`` LogisticsPricingProfile rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsPricingProfile, db, limit)

def list_logistics_pricing_profiles_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsPricingProfile rows (scale-ready)."""
    return _keyset_page(LogisticsPricingProfile, db, cursor, page_size)

def get_logistics_vehicle_rule_by_id(db: Session, id_: int) -> Optional[LogisticsVehicleRule]:
    """Return LogisticsVehicleRule by primary key (or None)."""
    return db.get(LogisticsVehicleRule, id_)

def list_logistics_vehicle_rules(db: Session, limit: int = 100) -> List[LogisticsVehicleRule]:
    """Return up to ``limit`` LogisticsVehicleRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsVehicleRule, db, limit)

def list_logistics_vehicle_rules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsVehicleRule rows (scale-ready)."""
    return _keyset_page(LogisticsVehicleRule, db, cursor, page_size)

def get_logistics_category_pricing_rule_by_id(db: Session, id_: int) -> Optional[LogisticsCategoryPricingRule]:
    """Return LogisticsCategoryPricingRule by primary key (or None)."""
    return db.get(LogisticsCategoryPricingRule, id_)

def list_logistics_category_pricing_rules(db: Session, limit: int = 100) -> List[LogisticsCategoryPricingRule]:
    """Return up to ``limit`` LogisticsCategoryPricingRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsCategoryPricingRule, db, limit)

def list_logistics_category_pricing_rules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsCategoryPricingRule rows (scale-ready)."""
    return _keyset_page(LogisticsCategoryPricingRule, db, cursor, page_size)

def get_shipment_by_id(db: Session, id_: int) -> Optional[Shipment]:
    """Return Shipment by primary key (or None)."""
    return db.get(Shipment, id_)

def list_shipments(db: Session, limit: int = 100) -> List[Shipment]:
    """Return up to ``limit`` Shipment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Shipment, db, limit)

def list_shipments_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Shipment rows (scale-ready)."""
    return _keyset_page(Shipment, db, cursor, page_size)

def get_shipment_event_by_id(db: Session, id_: int) -> Optional[ShipmentEvent]:
    """Return ShipmentEvent by primary key (or None)."""
    return db.get(ShipmentEvent, id_)

def list_shipment_events(db: Session, limit: int = 100) -> List[ShipmentEvent]:
    """Return up to ``limit`` ShipmentEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShipmentEvent, db, limit)

def list_shipment_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ShipmentEvent rows (scale-ready)."""
    return _keyset_page(ShipmentEvent, db, cursor, page_size)


# --- Query delegation (Law 3 sanctioned cross-domain query surface) ---

def logistics_partner_query(db: Session) -> object:
    """Return a base ``LogisticsPartner`` query for sanctioned cross-domain delegation."""
    return db.query(LogisticsPartner)

def shipment_query(db: Session) -> object:
    """Return a base ``Shipment`` query for sanctioned cross-domain delegation."""
    return db.query(Shipment)


def shipment_event_query(db: Session) -> object:
    """Return a base ``ShipmentEvent`` query for sanctioned cross-domain delegation."""
    return db.query(ShipmentEvent)

def logistics_partner_service_area_query(db: Session) -> object:
    """Return a base ``LogisticsPartnerServiceArea`` query for sanctioned cross-domain delegation."""
    return db.query(LogisticsPartnerServiceArea)


# --- Model class references (for column access in cross-domain filters) ---
# These return the model class itself so cross-domain services can reference
# columns (e.g., ``logistics_partner_model.id == X``) without importing the model.

def logistics_partner_model() -> type:
    """Return the ``LogisticsPartner`` model class (for column reference only)."""
    return LogisticsPartner


def shipment_model() -> type:
    """Return the ``Shipment`` model class (for column reference only)."""
    return Shipment


def shipment_event_model() -> type:
    """Return the ``ShipmentEvent`` model class (for column reference only)."""
    return ShipmentEvent


def logistics_partner_service_area_model() -> type:
    """Return the ``LogisticsPartnerServiceArea`` model class (for column reference only)."""
    return LogisticsPartnerServiceArea


def logistics_partner_service_area_model() -> type:
    """Return the ``LogisticsPartnerServiceArea`` model class (for column reference only)."""
    return LogisticsPartnerServiceArea


# --- Country domain cross-domain helpers (Law 3 compliant) ---

def get_partner_locations(db: Session, country_code: str) -> list[dict]:
    """Return active logistics partner locations for a country."""
    from domains.country.models.country_control import LogisticsPartnerLocation
    from domains.logistics.models.logistics import LogisticsPartner
    locations = (
        db.query(LogisticsPartnerLocation)
        .join(LogisticsPartner)
        .filter(
            LogisticsPartnerLocation.country_code == country_code.upper(),
            LogisticsPartnerLocation.is_active.is_(True),
        )
        .all()
    )
    return [
        {
            "id": loc.id,
            "partner_id": loc.partner_id,
            "location_type": loc.location_type,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": loc.address,
        }
        for loc in locations
    ]


def get_logistics_partner_by_user_id(db: Session, user_id: int):
    """Look up a logistics partner by their user_id."""
    return db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()


# --- Service re-exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers (modules/*/routers) import partner profile helpers
# from ``domains.logistics.ports`` instead of reaching into services directly.
from domains.logistics.services.partners.logistics_partner_service import (  # noqa: E402, F401
    get_partner_profile,
    update_partner_profile,
)

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "review_logistics_partner_service_area": ("domains.logistics.services.partners.service", "review_logistics_partner_service_area"),
    "create_logistics_partner_service_area": ("domains.logistics.services.partners.service", "create_logistics_partner_service_area"),
    "update_logistics_partner_service_area": ("domains.logistics.services.partners.service", "update_logistics_partner_service_area"),
    "delete_logistics_partner_service_area": ("domains.logistics.services.partners.service", "delete_logistics_partner_service_area"),
    "normalize_country_code": ("domains.logistics.services.partners.service", "normalize_country_code"),
    "quote_shipping_for_destination": ("domains.logistics.services.partners.service", "quote_shipping_for_destination"),
    "normalize_city_name": ("domains.logistics.services.partners.service", "normalize_city_name"),
    "partner_can_service_order": ("domains.logistics.services.partners.service", "partner_can_service_order"),
    "partner_is_profile_approved": ("domains.logistics.services.partners.service", "partner_is_profile_approved"),
    "serialize_category_pricing_rule": ("domains.logistics.services.partners.service", "serialize_category_pricing_rule"),
    "serialize_pricing_profile": ("domains.logistics.services.partners.service", "serialize_pricing_profile"),
    "serialize_service_area": ("domains.logistics.services.partners.service", "serialize_service_area"),
    "serialize_vehicle_rule": ("domains.logistics.services.partners.service", "serialize_vehicle_rule"),
}

import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")



