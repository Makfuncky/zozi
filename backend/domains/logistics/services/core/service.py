from __future__ import annotations

"""Auto-migrated service logic from routers/logistics.py."""

from typing import Any

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

import domains.logistics.services.core.logistics_service as ctrl

from infrastructure.database.database import get_db

from infrastructure.utils.dependencies import get_current_user

async def get_logistics_summary(db: Session, current_user: dict):
    return await ctrl.get_logistics_summary(current_user, db)

async def get_carriers(db: Session, current_user: dict):
    return await ctrl.get_carriers(current_user, db)

async def create_carrier(data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.create_carrier(data, current_user, db)

async def delete_carrier(carrier_id: int, db: Session, current_user: dict):
    return await ctrl.delete_carrier(carrier_id, current_user, db)

async def get_shipping_zones(db: Session, current_user: dict):
    return await ctrl.get_shipping_zones(current_user, db)

async def upsert_shipping_zone(data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.upsert_shipping_zone(data, current_user, db)

async def update_shipping_zone(zone_id: int, data: dict[str, Any], db: Session, current_user: dict):
    data["id"] = zone_id
    return await ctrl.upsert_shipping_zone(data, current_user, db)

async def delete_shipping_zone(zone_id: int, db: Session, current_user: dict):
    return await ctrl.delete_shipping_zone(zone_id, current_user, db)

async def get_orders_to_fulfil(limit: int, offset: int, db: Session, current_user: dict):
    return await ctrl.get_orders_to_fulfil(current_user, db, limit=limit, offset=offset)

async def create_shipment(data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.create_shipment(data, current_user, db)

async def scan_lookup_shipment(code: str, db: Session, current_user: dict):
    """Look up a shipment by tracking number or scan code. Admin only."""
    if str(current_user.get("role") or "").lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from domains.logistics.models.logistics import Shipment
    shipment = db.query(Shipment).filter(
        (Shipment.tracking_number == code) | (Shipment.id == (int(code) if code.isdigit() else -1))
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
        "shipping_address": (shipment.order.shipping_address if shipment.order else None),
        "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
        "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None,
    }

async def admin_update_shipment_status(shipment_id: int, data: dict[str, Any], db: Session, current_user: dict):
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    if str(current_user.get("role") or "").lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import datetime, timezone

    from domains.logistics.models.logistics import Shipment
    from domains.logistics.models.logistics import ShipmentEvent
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

async def get_active_shipments(db: Session, current_user: dict):
    return await ctrl.get_active_shipments(current_user, db)

async def get_shipment_history(page: int, per_page: int, db: Session, current_user: dict):
    return await ctrl.get_shipment_history(current_user, db, page=page, per_page=per_page)

async def get_shipment_events(shipment_id: int, db: Session, current_user: dict):
    return await ctrl.get_shipment_events(shipment_id, current_user, db)

async def scan_shipment_event(shipment_id: int, data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.scan_shipment_event(shipment_id, data, current_user, db)

async def update_shipment_status(shipment_id: int, data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.update_shipment_status(shipment_id, data, current_user, db)

async def get_distribution_channels(db: Session, current_user: dict):
    return await ctrl.get_distribution_channels(current_user, db)

async def update_shipment_event_gps(event_id: int, data: dict[str, Any], db: Session, current_user: dict):
    """Attach GPS coordinates to a shipment event (supplier or admin).

    Body: ``{"latitude": float, "longitude": float}``
    """
    try:
        lat = float(data["latitude"])
        lng = float(data["longitude"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="latitude and longitude (floats) are required")
    return await ctrl.update_event_gps(event_id, lat, lng, current_user, db)



# -------------------------------------------------------------------
# FROM: logistics_engine.py
# -------------------------------------------------------------------


import json
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.services.partners.service import normalize_country_code

logger = logging.getLogger(__name__)


class LogisticsEngine:
    """Country-aware logistics provider orchestration.

    Reads provider config from ``CountryConfig.logistics_providers_json``
    and maps to ``LogisticsPartner`` models for shipment fulfilment.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ─────────────────────────────────────────────────────────

    def get_enabled_providers(self, country_code: str) -> list[dict[str, Any]]:
        """Return enabled logistics providers configured for a country."""
        country = self._get_country(country_code)
        if not country:
            return []
        raw_providers = self._parse_providers(country)
        return [p for p in raw_providers if p.get("enabled", False)]

    def get_provider_rates(self, country_code: str) -> list[dict[str, Any]]:
        """Return all providers with their pricing for a country."""
        providers = self.get_enabled_providers(country_code)
        for prov in providers:
            partner = self._find_partner(prov["provider_id"])
            prov["partner_registered"] = partner is not None
            if partner:
                prov["partner_id"] = partner.id
                prov["verification_status"] = partner.verification_status
        return providers

    def calculate_shipping_cost(
        self,
        country_code: str,
        provider_id: str,
        *,
        weight_kg: float = 0.0,
        distance_km: float = 0.0,
        is_express: bool = False,
    ) -> dict[str, Any]:
        """Calculate shipping cost for a given provider and country."""
        country = self._get_country(country_code)
        if not country:
            return {"error": "Country not found", "cost": None}

        providers = self._parse_providers(country)
        provider_config = None
        for p in providers:
            if str(p.get("provider_id", "")).lower() == provider_id.lower():
                provider_config = p
                break

        if not provider_config:
            return {"error": f"Provider '{provider_id}' not configured for {country_code}", "cost": None}
        if not provider_config.get("enabled", False):
            return {"error": f"Provider '{provider_id}' is disabled for {country_code}", "cost": None}

        base_rate = Decimal(str(provider_config.get("base_rate", 0)))
        per_kg_rate = Decimal(str(provider_config.get("per_kg_rate", 0)))
        currency = provider_config.get("currency") or country.currency

        total = base_rate + (per_kg_rate * Decimal(str(weight_kg)))
        if distance_km > 0:
            total += base_rate * Decimal(str(distance_km)) / Decimal("10")

        sla_key = "sla_express_days" if is_express else "sla_standard_days"
        sla = provider_config.get(sla_key, "3-5")

        partner = self._find_partner(provider_id)

        return {
            "provider_id": provider_id,
            "provider_name": provider_config.get("name", provider_id),
            "country_code": country_code,
            "currency": currency,
            "base_rate": float(base_rate),
            "per_kg_rate": float(per_kg_rate),
            "weight_kg": weight_kg,
            "distance_km": distance_km,
            "total_cost": float(total),
            "sla_days": sla,
            "is_express": is_express,
            "partner_registered": partner is not None,
            "partner_id": partner.id if partner else None,
            "partner_verified": partner.verification_status == "approved" if partner else False,
        }

    def register_provider(
        self,
        country_code: str,
        provider_config: dict[str, Any],
        *,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        """Upsert a logistics provider into a country's config.

        ``provider_config`` must include at minimum ``provider_id`` and ``name``.
        """
        country = self._get_country(country_code)
        if not country:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Country not found")

        provider_id = str(provider_config.get("provider_id") or "").strip().lower()
        if not provider_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="provider_id is required")

        raw = country.logistics_providers_json
        try:
            providers = json.loads(raw) if isinstance(raw, str) else (raw or [])
        except (json.JSONDecodeError, TypeError):
            providers = []
        if not isinstance(providers, list):
            providers = []

        existing = None
        for p in providers:
            if isinstance(p, dict) and str(p.get("provider_id", "")).lower() == provider_id:
                existing = p
                break

        normalized = {
            "provider_id": provider_id,
            "name": str(provider_config.get("name") or provider_id).strip(),
            "enabled": bool(provider_config.get("enabled", True)),
            "service_areas": provider_config.get("service_areas") if isinstance(provider_config.get("service_areas"), list) else ["all_regions"],
            "sla_standard_days": str(provider_config.get("sla_standard_days") or "3-5").strip(),
            "sla_express_days": str(provider_config.get("sla_express_days") or "1-2").strip(),
            "base_rate": float(provider_config.get("base_rate") or 0),
            "per_kg_rate": float(provider_config.get("per_kg_rate") or 0),
            "currency": str(provider_config.get("currency") or "").strip().upper() or None,
        }

        if existing:
            existing.update(normalized)
        else:
            providers.append(normalized)

        country.logistics_providers_json = json.dumps(providers, default=str)
        self.db.commit()
        self.db.refresh(country)

        return {
            "message": f"Provider '{provider_id}' {'updated' if existing else 'created'} for {country_code}",
            "provider": normalized,
        }

    # ── Internal helpers ───────────────────────────────────────────────────

    def _get_country(self, country_code: str) -> CountryConfig | None:
        return self.db.query(CountryConfig).filter(
            CountryConfig.code == normalize_country_code(country_code),
            CountryConfig.is_active == True,
        ).first()

    def _parse_providers(self, country: CountryConfig) -> list[dict[str, Any]]:
        raw = country.logistics_providers_json
        if not raw:
            return []
        try:
            providers = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return []
        return providers if isinstance(providers, list) else []

    def _find_partner(self, provider_id: str) -> LogisticsPartner | None:
        return self.db.query(LogisticsPartner).filter(
            LogisticsPartner.code == provider_id.lower(),
        ).first()


# -------------------------------------------------------------------
# FROM: logistics_write_service.py
# -------------------------------------------------------------------

"""Backward-compatible re-export shim for logistics write operations.



This module intentionally performs NO imports at module-load time. It used to

re-export handler functions from `controllers.orders.logistics_controller`,

`routers.public_logistics_access` and `routers.public_shipments_access`, which created import-time

circular-import cycles (`logistics_controller` -> `logistics_write_service` ->

`logistics_controller`). Resolving names lazily via module-level `__getattr__`

breaks those cycles: the underlying modules are only imported on first

attribute access, by which point the importing module is fully initialised.

"""




import importlib

from typing import Any



_REEXPORTS: dict[str, tuple[str, str]] = {

    "delete_shipping_zone": ("controllers.orders.logistics_controller", "delete_shipping_zone"),

    "update_shipment": ("routers.public_shipments_access", "update_shipment"),

    "add_and_flush": ("services.common.write_helpers", "add_and_flush"),

    "commit_only": ("services.common.write_helpers", "commit_only"),

}





def __getattr__(name: str) -> Any:

    if name in _REEXPORTS:

        module_path, attr = _REEXPORTS[name]

        return getattr(importlib.import_module(module_path), attr)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")





from typing import Optional



from sqlalchemy.orm import Session



from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.logistics.models.logistics import ShipmentEvent

import structlog

logger = structlog.get_logger(__name__)





def _is_orm(obj, Model) -> bool:

    """True when ``obj`` is an ORM instance of ``Model`` (vs an id)."""

    return isinstance(obj, Model)





def _apply_changes(record, changes):

    """Apply a dict of field -> value to an ORM row, skipping ``None`` values.



    Mirrors the convention used across the other write services so updates are

    idempotent and never reset fields the caller didn't ask to change.

    """

    for field, value in (changes or {}).items():

        if value is None:

            continue

        if hasattr(record, field):

            setattr(record, field, value)

    return record





def _model_kwargs(Model, kwargs):

    """Keep only kwargs that map to real columns on ``Model`` (absorbs extras)."""

    cols = {c.name for c in Model.__table__.columns}

    return {k: v for k, v in kwargs.items() if k in cols}





def create_shipping_carrier(

    db: Session,

    *,

    name: str,

    code: str,

    supplier_id: Optional[int] = None,

    country_code: Optional[str] = None,

    is_active: bool = True,

    **extra,

) -> ShippingCarrier:

    """Create a supplier-specific shipping carrier.



    Absorbs caller-supplied extras (e.g. ``tracking_url``/``notes``) that are not

    part of the persisted model so legacy callers keep working.

    """

    carrier = ShippingCarrier(

        **_model_kwargs(

            ShippingCarrier,

            dict(

                name=name,

                code=code,

                supplier_id=supplier_id,

                country_code=country_code,

                is_active=is_active,

                **extra,

            ),

        )

    )

    db.add(carrier)

    db.commit()

    db.refresh(carrier)

    return carrier





def create_shipping_zone(

    db: Session,

    *,

    name: str,

    countries,

    supplier_id: Optional[int] = None,

    country_code: Optional[str] = None,

    is_active: bool = True,

    **extra,

) -> ShippingZone:

    """Create a shipping zone. ``countries`` may be a JSON string or list."""

    if isinstance(countries, (list, tuple, dict)):

        import json as _json

        countries = _json.dumps(countries)

    zone = ShippingZone(

        **_model_kwargs(

            ShippingZone,

            dict(

                name=name,

                countries=countries,

                supplier_id=supplier_id,

                country_code=country_code,

                is_active=is_active,

                **extra,

            ),

        )

    )

    db.add(zone)

    db.commit()

    db.refresh(zone)

    return zone





def update_shipping_zone(db: Session, zone_or_id, changes: Optional[dict] = None, **kw):

    """Update a shipping zone (id or ORM object)."""

    if _is_orm(zone_or_id, ShippingZone):

        record = zone_or_id

    else:

        record = db.get(ShippingZone, int(zone_or_id))

        if record is None:

            raise ValueError(f"ShippingZone {zone_or_id} not found")

    _apply_changes(record, changes or kw)

    db.commit()

    db.refresh(record)

    return record





def update_shipping_carrier(db: Session, carrier_or_id, changes: Optional[dict] = None, **kw):

    """Update a shipping carrier.



    Compatible with both the spec form ``(db, id, **changes)`` and the legacy

    controller form ``(db, carrier_obj, {"is_active": False})``.

    """

    if _is_orm(carrier_or_id, ShippingCarrier):

        record = carrier_or_id

    else:

        record = db.get(ShippingCarrier, int(carrier_or_id))

        if record is None:

            raise ValueError(f"ShippingCarrier {carrier_or_id} not found")

    _apply_changes(record, changes or kw)

    db.commit()

    db.refresh(record)

    return record





def update_shipment_event(db: Session, event_or_id, changes: Optional[dict] = None, **kw):

    """Update a shipment event (legacy controller form passes an object + dict)."""

    if _is_orm(event_or_id, ShipmentEvent):

        record = event_or_id

    else:

        record = db.get(ShipmentEvent, int(event_or_id))

        if record is None:

            raise ValueError(f"ShipmentEvent {event_or_id} not found")

    _apply_changes(record, changes or kw)

    db.commit()

    db.refresh(record)

    return record





def refresh_model(db: Session, obj) -> None:

    """Refresh an ORM instance from the database (flushes pending changes)."""

    db.refresh(obj)


# -------------------------------------------------------------------
# FROM: logistics_admin_operations_service.py
# -------------------------------------------------------------------

# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.logistics.admin_operations_service re-exports for HTTP routers."""
# TODO: Module not yet created
# from domains.logistics.services.admin_operations_service import get_email_stats
# TODO: Module not yet created
# from domains.logistics.services.admin_operations_service import get_logistics_overview
# TODO: Module not yet created
# from domains.logistics.services.admin_operations_service import get_payout_amount

# -------------------------------------------------------------------
# FROM: admin_logistics_service.py
# -------------------------------------------------------------------

"""Admin logistics service."""

from sqlalchemy.orm import Session

from domains.logistics.models.logistics import LogisticsPartner

from infrastructure.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import clear_rls_context, set_rls_context


def list_partners(country_code: str, include_deleted: bool, page: int, page_size: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(LogisticsPartner).filter(LogisticsPartner.country_code == country_code.upper())
        if not include_deleted:
            q = q.filter(LogisticsPartner.is_deleted == False)
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


def approve_partner(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.verification_status = "approved"
        db.commit()
        return {"message": "Partner approved"}
    finally:
        clear_rls_context()


def reject_partner(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.verification_status = "rejected"
        db.commit()
        return {"message": "Partner rejected"}
    finally:
        clear_rls_context()


def toggle_partner_active(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.status = "suspended" if p.status == "active" else "active"
        db.commit()
        return {"message": f"Partner {'suspended' if p.status == 'suspended' else 'activated'}"}
    finally:
        clear_rls_context()


# -------------------------------------------------------------------
# FROM: admin_logistics_fallback_service.py
# -------------------------------------------------------------------

"""
Admin Fallback Router — non-country-scoped route aliases.

The dedicated admin_*.py routers define routes WITH a {country_code} path
parameter (e.g. GET /{code}/suppliers).  The admin frontend often hits
the SAME endpoints WITHOUT a country code (GET /admin/suppliers).

This router provides shallow proxy routes that delegate to the same
underlying controllers, so the frontend works whether or not a country
code is supplied.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.ports import archive_entity, bulk_archive_entities, bulk_restore_entities, download_export_job_result, export_audit_logs_csv, export_coupons_csv, export_orders_csv, export_products_csv, export_transfer_csv, export_users_csv, get_audit_log_page, get_available_audit_actions, get_current_admin, get_ticket_detail, hard_delete_entity, queue_export_job, require_admin_2fa_enabled, require_admin_2fa_verified, restore_entity
# TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_all_suppliers
from domains.finance.ports import list_pending_payouts
from domains.catalog.models.products import Category as CategoryModel
from domains.governance.models.admin import CommissionGlobalConfig
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.hr.models.employee_models import Employee
from domains.logistics.models.logistics import Shipment
from domains.finance.models.payments import Payment
from domains.finance.models.payments import Payout as PayoutModel

def admin_dashboard_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Simple admin dashboard stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from domains.accounts.models.user import User as UserModel
    from domains.catalog.models.products import Product as ProductModel
    from domains.orders.models.orders import Order as OrderModel
    total_revenue = db.query(sqlfunc.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    total_users = db.query(sqlfunc.count(UserModel.id)).scalar() or 0
    total_orders = db.query(sqlfunc.count(OrderModel.id)).scalar() or 0
    return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_orders': total_orders, 'active_sessions': 0, 'pending_payouts': db.query(PayoutModel).filter(PayoutModel.status == 'pending').count()}

def admin_stats_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Simple aggregate stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from domains.accounts.models.user import User as UserModel
    from domains.catalog.models.products import Product as ProductModel
    from domains.orders.models.orders import Order as OrderModel
    return {'total_users': db.query(sqlfunc.count(UserModel.id)).scalar() or 0, 'total_customers': db.query(sqlfunc.count(UserModel.id)).filter(UserModel.role == 'customer').scalar() or 0, 'total_suppliers': db.query(sqlfunc.count(UserModel.id)).filter(UserModel.role == 'supplier').scalar() or 0, 'total_orders': db.query(sqlfunc.count(OrderModel.id)).scalar() or 0, 'total_products': db.query(sqlfunc.count(ProductModel.id)).filter(ProductModel.is_deleted == False).scalar() or 0, 'pending_payouts': db.query(PayoutModel).filter(PayoutModel.status == 'pending').count()}

def admin_payouts_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all payouts (no country code required)."""
    skip = (page - 1) * page_size
    items = db.query(PayoutModel).order_by(PayoutModel.created_at.desc()).offset(skip).limit(page_size).all()
    total = db.query(PayoutModel).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_categories_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all categories (no country code required)."""
    skip = (page - 1) * page_size
    items = db.query(CategoryModel).order_by(CategoryModel.name).offset(skip).limit(page_size).all()
    total = db.query(CategoryModel).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_commission_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Get commission global config (no country code required)."""
    config = db.query(CommissionGlobalConfig).first()
    return config or {}

def admin_employees_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all employees (no country code required)."""
    from domains.accounts.models.user import User as UserModel
    skip = (page - 1) * page_size
    items = db.query(Employee).join(UserModel, Employee.user_id == UserModel.id).order_by(UserModel.full_name.asc().nullslast(), Employee.id).offset(skip).limit(page_size).all()
    total = db.query(Employee).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_payments_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all payments (no country code required)."""
    skip = (page - 1) * page_size
    items = db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(page_size).all()
    total = db.query(Payment).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_logistics_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List logistics carriers and partners (no country code required)."""
    from domains.governance.models.admin import ShippingZone
    from domains.logistics.models.logistics import Shipment
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zone_count = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()
    shipment_count = db.query(Shipment).count()
    return {'active_carriers': [{'id': c.id, 'name': c.name, 'code': c.code} for c in carriers], 'active_zones': zone_count, 'total_shipments': shipment_count}

def admin_logistics_partners_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List logistics partners (no country code required)."""
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    return {'partners': [{'id': c.id, 'name': c.name, 'code': c.code, 'is_active': c.is_active} for c in carriers], 'total': len(carriers)}

def admin_treasury_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Treasury summary — redirect to /admin/treasury/metrics if you need full metrics."""
    from domains.finance.models.finance import Account as AccountModel
    from domains.finance.models.finance import AccountBalance as AccountBalanceModel
    total_cash = db.query(func.sum(AccountBalanceModel.balance)).select_from(AccountBalanceModel).scalar() or 0
    account_count = db.query(AccountModel).count()
    return {'total_cash': float(total_cash), 'total_accounts': account_count, 'metrics_available_at': '/admin/treasury/metrics'}

def admin_treasury_metrics_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Treasury metrics summary (no country code required)."""
    from domains.finance.models.finance import Account as AccountModel
    from domains.finance.models.finance import AccountBalance as AccountBalanceModel
    accounts = db.query(AccountModel).all()
    total_cash = db.query(func.sum(AccountBalanceModel.balance)).select_from(AccountBalanceModel).scalar() or 0
    return {'total_accounts': len(accounts), 'total_cash': float(total_cash), 'accounts': [{'id': a.id, 'name': a.name, 'type': a.type, 'currency': a.currency} for a in accounts]}

# -------------------------------------------------------------------
# FROM: admin_logistics_geography_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/admin_logistics_geography.py."""

from fastapi import Depends, HTTPException, Query, Path

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.accounts.models.user import User

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest

from infrastructure.utils.dependencies import require_admin, require_super_admin

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context

# TODO: Module not yet created
# from domains.governance.services.admin.core.bulk_ops_service import bulk_archive_entities, bulk_restore_entities

from domains.logistics.ports import approve_partner
from domains.logistics.ports import list_partners
from domains.logistics.ports import reject_partner
from domains.logistics.ports import toggle_partner_active

def list_partners_route(country_code: str, include_deleted: bool, page: int, page_size: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_partners(db, country_code, include_deleted, page, page_size)
    finally:
        clear_rls_context()

def approve_partner_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return approve_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()

def reject_partner_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return reject_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()

def toggle_partner_active_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return toggle_partner_active(db, partner_id, country_code)
    finally:
        clear_rls_context()

def archive_partner(country_code: str, partner_id: int, payload: ArchiveRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()

def restore_partner(country_code: str, partner_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def bulk_archive_partners(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()

def bulk_restore_partners(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def delete_partner_permanent(country_code: str, partner_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()



# -------------------------------------------------------------------
# FROM: admin_logistics_imports_service.py
# -------------------------------------------------------------------

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils import import_service as svc

class ShipmentLineInput(BaseModel):
    po_line_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    hs_code: Optional[str] = None
    quantity: float
    unit_cost_fx: float
    weight_kg: Optional[float] = None
    volume_cbm: Optional[float] = None

class ShipmentCreate(BaseModel):
    po_id: Optional[int] = None
    supplier_id: Optional[int] = None
    origin_country: Optional[str] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    vessel_name: Optional[str] = None
    bill_of_lading: Optional[str] = None
    container_number: Optional[str] = None
    shipment_date: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    currency: str = 'OMR'
    exchange_rate: float = 1.0
    warehouse_id: Optional[int] = None
    country_code: Optional[str] = None
    notes: Optional[str] = None
    lines: list[ShipmentLineInput] = []

class CostAllocateInput(BaseModel):
    freight_cost: Optional[float] = None
    insurance_cost: Optional[float] = None
    port_charges: Optional[float] = None
    inland_freight: Optional[float] = None
    bank_charges: Optional[float] = None
    other_costs: Optional[float] = None
    allocation_method: str = 'by_value'

class CustomsInput(BaseModel):
    customs_declaration_number: Optional[str] = None
    customs_broker: Optional[str] = None
    entry_date: Optional[datetime] = None
    duty_rate: Optional[float] = None
    duty_amount: Optional[float] = None
    vat_on_duty: Optional[float] = None
    penalties: Optional[float] = None
    notes: Optional[str] = None

class FinalizeInput(BaseModel):
    warehouse_id: Optional[int] = None

class TemplateCreate(BaseModel):
    name: str
    default_duty_rate: Optional[float] = None
    default_freight_percent: Optional[float] = None
    default_insurance_percent: Optional[float] = None
    default_port_charges_percent: Optional[float] = None
    default_bank_charges_percent: Optional[float] = None
    allocation_method: str = 'by_value'
    country_code: Optional[str] = None

class AutoAllocateInput(BaseModel):
    template_id: Optional[int] = None
    country_code: Optional[str] = None

def get_shipment(shipment_id: int, db: Session=Depends(get_db), _admin: dict=Depends(require_admin)):
    s = db.query(svc.ImportShipment).filter(svc.ImportShipment.id == shipment_id).first()
    if not s:
        raise HTTPException(404, 'Shipment not found')
    return s

# -------------------------------------------------------------------
# FROM: admin_logistics_operations_service.py
# -------------------------------------------------------------------

"""
Admin Router  route declarations only (HTTP layer).
All business logic lives in controllers/admin_controller.py.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import Body, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from infrastructure.utils.constants import MAX_BULK_ITEMS
from infrastructure.database.database import get_db, Base
from infrastructure.database.schemas import User as UserSchema, Product as ProductSchema, Order as OrderSchema, CouponSchema, ListPage, AuditLogSchema, AuditLogPage, CreateStaffAccount, UpdateStaffAccount, BulkUpdateStaffBody
from domains.accounts.ports import get_current_user, get_hierarchy_permissions, update_role_permissions
from infrastructure.utils.dependencies import require_admin
# TODO: Module not yet created
# from domains.governance.services.permissions.effective_permissions import require_permission
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import get_all_users
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import update_user_role
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import toggle_user_active
from domains.governance.ports import delete_user_admin
# TODO: Module not yet created
# from domains.governance.services.users.admin_users import bulk_delete_users_admin
# TODO: Module not yet created
# from domains.governance.services.users.admin_users import force_reset_password_admin
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import create_staff_account
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import update_staff_account
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import bulk_update_staff_accounts
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import delete_staff_account
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import get_all_orders
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import delete_order_admin
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import update_order_status
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import refund_order
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import update_order_tracking
# TODO: Module not yet created
# from domains.governance.services.products.products_service import get_all_products
# TODO: Module not yet created
# from domains.governance.services.products.products_service import delete_product_admin
# TODO: Module not yet created
# from domains.governance.services.products.products_service import restore_product_admin
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_analytics
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_supplier_comparison
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_customer_insights
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_pending_suppliers
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import verify_supplier
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import reject_supplier
# TODO: Module not yet created
# from domains.governance.services.products.products_service import get_pending_products
from domains.governance.ports import approve_product
from domains.governance.ports import reject_product
# TODO: Module not yet created
# from domains.governance.services.products.products_service import toggle_product_badge
from domains.governance.ports import list_coupons
from domains.governance.ports import create_coupon
from domains.governance.ports import delete_coupon
# TODO: Module not yet created
# from domains.comms.services.ticket.tickets_service import list_tickets
# TODO: Module not yet created
# from domains.comms.services.ticket.tickets_service import reply_to_ticket
# TODO: Module not yet created
# from domains.comms.services.ticket.tickets_write_service import update_ticket_status
from domains.finance.ports import list_pending_payouts
from domains.governance.ports import verify_payout
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_analytics_timeseries
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_top_products_analytics
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_user_growth_analytics
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_chatbot_analytics
# TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_all_suppliers
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import bulk_update_order_status_admin
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import bulk_delete_orders_admin
# TODO: Module not yet created
# from domains.governance.services.products.products_service import bulk_delete_products_admin
# TODO: Module not yet created
# from domains.governance.services.products.products_service import bulk_product_moderation
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import bulk_supplier_verification
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import bulk_manage_suppliers
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import bulk_update_users_role
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import bulk_toggle_users_active
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import list_staff_accounts
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import update_staff_account
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import list_pending_bank_accounts
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import delete_bank_account_record
from domains.governance.ports import verify_bank_account
# TODO: Module not yet created
# from domains.governance.services.settings.database_service import get_database_overview
from domains.governance.ports import get_authority_level
from domains.governance.ports import get_user_chain
from domains.governance.ports import get_all_subordinates
from domains.governance.ports import get_team_members
from domains.governance.ports import is_in_chain
from domains.governance.ports import can_manage
from domains.governance.ports import get_org_chart
from domains.governance.ports import get_home_org_unit
from domains.governance.ports import reassign_manager
from domains.governance.ports import backfill_authority_levels
from domains.governance.ports import APPROVAL_RULES, can_approve, get_approval_chain, require_approval, resolve_approvers
from domains.catalog.ports import get_banners
from domains.catalog.ports import get_banner_by_id
from domains.catalog.ports import create_banner
from domains.catalog.ports import update_banner
from domains.catalog.ports import delete_banner
from domains.catalog.ports import BannerCreate
from domains.catalog.ports import BannerUpdate
# TODO: Module not yet created
# from domains.governance.services.admin.core.export_service import export_users_csv, export_orders_csv, export_products_csv, export_coupons_csv, export_audit_logs_csv, export_transfer_csv, queue_export_job, download_export_job_result
from domains.orders.ports import get_promotion_config
from domains.orders.ports import update_promotion_config
from domains.orders.ports import list_promotion_tiers
from domains.orders.ports import create_promotion_tier
from domains.orders.ports import update_promotion_tier
from domains.orders.ports import delete_promotion_tier
from domains.orders.ports import preview_order_tier_discount
from infrastructure.utils.backup import get_backup_manager
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
from domains.orders.ports import get_all_flash_sales
from domains.orders.ports import create_flash_sale
from domains.orders.ports import update_flash_sale

class BulkDeleteUsersBody(BaseModel):
    user_ids: List[int]

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkToggleActiveBody(BaseModel):
    user_ids: List[int]
    is_active: bool

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkUserRoleBody(BaseModel):
    user_ids: List[int]
    role: str

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class ResetPasswordBody(BaseModel):
    new_password: str

class BulkOrderStatusBody(BaseModel):
    order_ids: List[int]
    status: str

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkOrderDeleteBody(BaseModel):
    order_ids: List[int]

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkProductDeleteBody(BaseModel):
    product_ids: List[int]

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkProductModerationBody(BaseModel):
    product_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkSupplierVerifyBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkSupplierLifecycleBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None
    badge_level: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class PromotionConfigBody(BaseModel):
    engine_enabled: Optional[bool] = None
    allow_product_coupons: Optional[bool] = None
    allow_category_coupons: Optional[bool] = None
    allow_order_tier_discounts: Optional[bool] = None
    allow_referral_rewards: Optional[bool] = None
    allow_supplier_promotions: Optional[bool] = None
    allow_global_coupons: Optional[bool] = None
    stacking_mode: Optional[str] = None
    max_combined_discount_percent: Optional[float] = None
    max_combined_discount_amount: Optional[float] = None
    show_savings_line_item: Optional[bool] = None
    tier_discount_visible: Optional[bool] = None
    points_per_omr: Optional[int] = None
    referral_referrer_points: Optional[int] = None
    referral_referee_points: Optional[int] = None
    points_expiry_months: Optional[int] = None
    referral_monthly_cap: Optional[int] = None
    referral_verification_delay_days: Optional[int] = None
    min_points_redeem: Optional[int] = None
    allow_partial_points_redemption: Optional[bool] = None

class PromotionTierBody(BaseModel):
    tier_name: str
    min_order: float
    max_order: Optional[float] = None
    discount_type: str
    discount_value: float
    stacking_allowed: bool = False
    is_active: bool = True
    sort_order: int = 0

class PromotionTierUpdateBody(BaseModel):
    tier_name: Optional[str] = None
    min_order: Optional[float] = None
    max_order: Optional[float] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    stacking_allowed: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class PromotionPreviewBody(BaseModel):
    order_subtotal: float
    coupon_discount: float = 0.0

class AdminDisputeBulkActionBody(BaseModel):
    dispute_ids: List[int]
    action: str
    value: Optional[str] = None

    @field_validator('dispute_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class UpdateRolePermissionsIn(BaseModel):
    permissions: List[str]

class ReassignManagerBody(BaseModel):
    user_id: int
    new_manager_id: int | None = None

class ResourceApprovalCheckIn(BaseModel):
    resource_type: str
    amount: Optional[float] = None

def verify_payout_route(payout_id: int, data: dict, db: Session=Depends(get_db), current_admin: dict=Depends(require_admin_2fa_verified)):
    require_permission('payouts.verify', current_admin)
    from domains.finance.models.payments import Payout
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    amount = float(payout.amount) if payout and payout.amount is not None else None
    require_approval(db, current_admin['id'], 'payout', amount=amount)
    return verify_payout(payout_id, data, current_admin, db)

def admin_email_stats(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Real email marketing statistics from the database."""
    require_permission('analytics.view', current_admin)
    from sqlalchemy import func as sqlfunc, case as sql_case
    from domains.comms.models.marketing import NewsletterSubscriber
    from domains.comms.models.marketing import EmailCampaign
    from domains.comms.models.marketing import CampaignRecipient
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0
    campaign_stats = db.query(sqlfunc.count(EmailCampaign.id).label('total'), sqlfunc.sum(sql_case((EmailCampaign.status == 'sending', 1), else_=0)).label('active')).first()
    total_sent = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.sent_at.isnot(None)).scalar() or 0
    total_opened = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.opened_at.isnot(None)).scalar() or 0
    total_clicked = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.clicked_at.isnot(None)).scalar() or 0
    open_rate = round(total_opened / total_sent * 100, 1) if total_sent else 0
    click_rate = round(total_clicked / total_opened * 100, 1) if total_opened else 0
    recent_campaigns = db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(10).all()

    def _ser_campaign(c: EmailCampaign):
        recipient_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.campaign_id == c.id).scalar() or 0
        return {'id': c.id, 'name': c.name, 'subject': c.subject, 'status': c.status, 'recipient_count': recipient_count, 'sent_count': recipient_count, 'opened_count': total_opened, 'clicked_count': total_clicked, 'send_at': c.send_at.isoformat() if c.send_at else None, 'sent_at': c.send_at.isoformat() if c.send_at else None, 'created_at': c.created_at.isoformat() if c.created_at else None}
    return {'total_subscribers': total_subscribers, 'active_campaigns': int(campaign_stats.active or 0), 'total_campaigns': int(campaign_stats.total or 0), 'total_sent': total_sent, 'open_rate': open_rate, 'click_rate': click_rate, 'recent_campaigns': [_ser_campaign(c) for c in recent_campaigns]}

def admin_logistics_overview(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Admin overview of all shipments, carriers, and distribution channels."""
    require_permission('orders.manage', current_admin)
    from sqlalchemy import func as sqlfunc
    from domains.governance.models.admin import ShippingCarrier
    from domains.governance.models.admin import ShippingZone
    from domains.logistics.models.logistics import Shipment
    shipment_counts = db.query(Shipment.status, sqlfunc.count(Shipment.id).label('count')).group_by(Shipment.status).all()
    channel_counts = db.query(Shipment.distribution_channel, sqlfunc.count(Shipment.id).label('count')).filter(Shipment.distribution_channel.isnot(None)).group_by(Shipment.distribution_channel).all()
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()
    recent_shipments = db.query(Shipment).order_by(Shipment.updated_at.desc()).limit(20).all()

    def _ser_shipment(s: Shipment):
        return {'id': s.id, 'order_id': s.order_id, 'supplier_id': s.supplier_id, 'carrier_name': s.carrier_name, 'tracking_number': s.tracking_number, 'status': s.status, 'distribution_channel': s.distribution_channel, 'current_hub': s.current_hub, 'scan_code': s.scan_code, 'shipped_at': s.shipped_at.isoformat() if s.shipped_at else None, 'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None, 'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None}
    return {'shipment_by_status': {s: c for (s, c) in shipment_counts}, 'shipment_by_channel': {ch: c for (ch, c) in channel_counts}, 'active_carriers': [{'id': c.id, 'name': c.name, 'code': c.code, 'is_global': c.supplier_id is None} for c in carriers], 'active_zones': zones, 'recent_shipments': [_ser_shipment(s) for s in recent_shipments]}

def admin_reset_demo_data(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """
    Clear all non-essential seed data  orders, products, reviews, communication
    data, coupons, and non-admin users  so the demo environment can be reset
    from the UI without SSH or terminal access.

    Admin user accounts (role=admin) are preserved.
    """
    require_admin(current_admin)
    app_env = getattr(settings, 'APP_ENV', None)
    if not app_env or app_env not in ('development', 'dev', 'test'):
        raise HTTPException(status_code=400, detail='Reset is only available in development/test environments')
    from datetime import datetime, timezone
    from sqlalchemy import text
    tables_to_clear = ['entity_chat_messages', 'entity_chat_threads', 'group_chat_messages', 'group_chat_members', 'group_chat_rooms', 'direct_chat_messages', 'direct_chat_rooms', 'internal_emails', 'email_folders', 'order_items', 'orders', 'reviews', 'order_logistics_allocations', 'shipments', 'wishlist_items', 'cart_items', 'coupon_usages', 'coupons', 'promotion_ledger_entries', 'promotion_order_tiers', 'product_variants', 'products', 'categories', 'audit_logs', 'notifications']
    deleted_counts: dict[str, int] = {}
    for table in tables_to_clear:
        try:
            if table not in Base.metadata.tables:
                deleted_counts[table] = -1
                continue
            result = db.execute(Base.metadata.tables[table].delete())
            deleted_counts[table] = result.rowcount or 0
        except Exception:
            deleted_counts[table] = -1
    non_admin_count = db.execute(text("DELETE FROM users WHERE role != 'admin'")).rowcount or 0
    deleted_counts['users_(non_admin)'] = non_admin_count
    try:
        db.execute(text('DELETE FROM sqlite_sequence'))
    except Exception:
        pass
    db.commit()
    total = sum((v for v in deleted_counts.values() if v >= 0))
    return {'detail': 'Demo data reset complete', 'tables_cleared': len(tables_to_clear) + 1, 'total_rows_deleted': total, 'counts': deleted_counts, 'note': 'Admin accounts preserved. Run seed_all.py to re-seed.'}


# -------------------------------------------------------------------
# FROM: admin_operations_service.py
# -------------------------------------------------------------------

"""Admin logistics / email-marketing aggregation service.

Holds the read-only DB aggregation that was previously inlined in
``routers/admin_logistics_operations.py`` for three admin endpoints:
``/email/stats``, ``/logistics/overview``, and the payout-verify amount lookup.
"""

from typing import Optional

from sqlalchemy import func as sqlfunc, case as sql_case
from sqlalchemy.orm import Session

from domains.comms.models.marketing import CampaignRecipient
from domains.comms.models.marketing import EmailCampaign
from domains.comms.models.marketing import NewsletterSubscriber
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.logistics.models.logistics import Shipment
from domains.finance.models.payments import Payout


def get_payout_amount(db: Session, payout_id: int) -> Optional[float]:
    """Return the payout amount (or None) used for 2FA approval gating."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if payout and payout.amount is not None:
        return float(payout.amount)
    return None


def get_email_stats(db: Session) -> dict:
    """Real email marketing statistics from the database."""
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.is_active == True
    ).scalar() or 0

    campaign_stats = db.query(
        sqlfunc.count(EmailCampaign.id).label("total"),
        sqlfunc.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
    ).first()

    total_sent = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.sent_at.isnot(None)
    ).scalar() or 0
    total_opened = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.opened_at.isnot(None)
    ).scalar() or 0
    total_clicked = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.clicked_at.isnot(None)
    ).scalar() or 0

    open_rate = round((total_opened / total_sent * 100), 1) if total_sent else 0
    click_rate = round((total_clicked / total_opened * 100), 1) if total_opened else 0

    recent_campaigns = db.query(EmailCampaign).order_by(
        EmailCampaign.created_at.desc()
    ).limit(10).all()

    def _ser_campaign(c: EmailCampaign) -> dict:
        recipient_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id
        ).scalar() or 0
        sent_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.sent_at.isnot(None),
        ).scalar() or 0
        opened_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.opened_at.isnot(None),
        ).scalar() or 0
        clicked_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.clicked_at.isnot(None),
        ).scalar() or 0
        return {
            "id": c.id,
            "name": c.name,
            "subject": c.subject,
            "status": c.status,
            "recipient_count": recipient_count,
            "sent_count": sent_count,
            "opened_count": opened_count,
            "clicked_count": clicked_count,
            "send_at": c.send_at.isoformat() if c.send_at else None,
            "sent_at": c.send_at.isoformat() if c.send_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }

    return {
        "total_subscribers": total_subscribers,
        "active_campaigns": int(campaign_stats.active or 0),
        "total_campaigns": int(campaign_stats.total or 0),
        "total_sent": total_sent,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "recent_campaigns": [_ser_campaign(c) for c in recent_campaigns],
    }


def get_logistics_overview(db: Session) -> dict:
    """Admin overview of all shipments, carriers, and distribution channels."""
    shipment_counts = db.query(
        Shipment.status,
        sqlfunc.count(Shipment.id).label("count"),
    ).group_by(Shipment.status).all()

    channel_counts = db.query(
        Shipment.distribution_channel,
        sqlfunc.count(Shipment.id).label("count"),
    ).filter(Shipment.distribution_channel.isnot(None)).group_by(
        Shipment.distribution_channel
    ).all()

    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()

    recent_shipments = db.query(Shipment).order_by(
        Shipment.updated_at.desc()
    ).limit(20).all()

    def _ser_shipment(s: Shipment) -> dict:
        return {
            "id": s.id,
            "order_id": s.order_id,
            "supplier_id": s.supplier_id,
            "carrier_name": s.carrier_name,
            "tracking_number": s.tracking_number,
            "status": s.status,
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": s.scan_code,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
        }

    return {
        "shipment_by_status": {s: c for s, c in shipment_counts},
        "shipment_by_channel": {ch: c for ch, c in channel_counts},
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code, "is_global": c.supplier_id is None}
            for c in carriers
        ],
        "active_zones": zones,
        "recent_shipments": [_ser_shipment(s) for s in recent_shipments],
    }

# -------------------------------------------------------------------
# FROM: flat_admin_logistics_fallback_service.py
# -------------------------------------------------------------------

"""
Admin Fallback Router — non-country-scoped route aliases.

The dedicated admin_*.py routers define routes WITH a {country_code} path
parameter (e.g. GET /{code}/suppliers).  The admin frontend often hits
the SAME endpoints WITHOUT a country code (GET /admin/suppliers).

This router provides shallow proxy routes that delegate to the same
underlying controllers, so the frontend works whether or not a country
code is supplied.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.admin_service import get_current_admin
# TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_all_suppliers
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.finance.services.payments.payout_approval_read_service import list_pending_payouts
from domains.catalog.models.products import Category as CategoryModel
from domains.governance.models.admin import CommissionGlobalConfig
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.hr.models.employee_models import Employee
from domains.logistics.models.logistics import Shipment
from domains.finance.models.payments import Payment
from domains.finance.models.payments import Payout as PayoutModel

def admin_dashboard_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Simple admin dashboard stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from domains.accounts.models.user import User as UserModel
    from domains.catalog.models.products import Product as ProductModel
    from domains.orders.models.orders import Order as OrderModel
    total_revenue = db.query(sqlfunc.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0
    total_users = db.query(sqlfunc.count(UserModel.id)).scalar() or 0
    total_orders = db.query(sqlfunc.count(OrderModel.id)).scalar() or 0
    return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_orders': total_orders, 'active_sessions': 0, 'pending_payouts': db.query(PayoutModel).filter(PayoutModel.status == 'pending').count()}

def admin_stats_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Simple aggregate stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from domains.accounts.models.user import User as UserModel
    from domains.catalog.models.products import Product as ProductModel
    from domains.orders.models.orders import Order as OrderModel
    return {'total_users': db.query(sqlfunc.count(UserModel.id)).scalar() or 0, 'total_customers': db.query(sqlfunc.count(UserModel.id)).filter(UserModel.role == 'customer').scalar() or 0, 'total_suppliers': db.query(sqlfunc.count(UserModel.id)).filter(UserModel.role == 'supplier').scalar() or 0, 'total_orders': db.query(sqlfunc.count(OrderModel.id)).scalar() or 0, 'total_products': db.query(sqlfunc.count(ProductModel.id)).filter(ProductModel.is_deleted == False).scalar() or 0, 'pending_payouts': db.query(PayoutModel).filter(PayoutModel.status == 'pending').count()}

def admin_payouts_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all payouts (no country code required)."""
    skip = (page - 1) * page_size
    items = db.query(PayoutModel).order_by(PayoutModel.created_at.desc()).offset(skip).limit(page_size).all()
    total = db.query(PayoutModel).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_categories_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all categories (no country code required)."""
    skip = (page - 1) * page_size
    items = db.query(CategoryModel).order_by(CategoryModel.name).offset(skip).limit(page_size).all()
    total = db.query(CategoryModel).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_commission_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Get commission global config (no country code required)."""
    config = db.query(CommissionGlobalConfig).first()
    return config or {}

def admin_employees_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all employees (no country code required)."""
    from domains.accounts.models.user import User as UserModel
    skip = (page - 1) * page_size
    items = db.query(Employee).join(UserModel, Employee.user_id == UserModel.id).order_by(UserModel.full_name.asc().nullslast(), Employee.id).offset(skip).limit(page_size).all()
    total = db.query(Employee).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_payments_fallback(page: int=Query(1, ge=1), page_size: int=Query(100, ge=1, le=500), db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List all payments (no country code required)."""
    skip = (page - 1) * page_size
    items = db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(page_size).all()
    total = db.query(Payment).count()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

def admin_logistics_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List logistics carriers and partners (no country code required)."""
    from domains.governance.models.admin import ShippingZone
    from domains.logistics.models.logistics import Shipment
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zone_count = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()
    shipment_count = db.query(Shipment).count()
    return {'active_carriers': [{'id': c.id, 'name': c.name, 'code': c.code} for c in carriers], 'active_zones': zone_count, 'total_shipments': shipment_count}

def admin_logistics_partners_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """List logistics partners (no country code required)."""
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    return {'partners': [{'id': c.id, 'name': c.name, 'code': c.code, 'is_active': c.is_active} for c in carriers], 'total': len(carriers)}

def admin_treasury_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Treasury summary — redirect to /admin/treasury/metrics if you need full metrics."""
    from domains.finance.models.finance import Account as AccountModel
    from domains.finance.models.finance import AccountBalance as AccountBalanceModel
    total_cash = db.query(func.sum(AccountBalanceModel.balance)).select_from(AccountBalanceModel).scalar() or 0
    account_count = db.query(AccountModel).count()
    return {'total_cash': float(total_cash), 'total_accounts': account_count, 'metrics_available_at': '/admin/treasury/metrics'}

def admin_treasury_metrics_fallback(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Treasury metrics summary (no country code required)."""
    from domains.finance.models.finance import Account as AccountModel
    from domains.finance.models.finance import AccountBalance as AccountBalanceModel
    accounts = db.query(AccountModel).all()
    total_cash = db.query(func.sum(AccountBalanceModel.balance)).select_from(AccountBalanceModel).scalar() or 0
    return {'total_accounts': len(accounts), 'total_cash': float(total_cash), 'accounts': [{'id': a.id, 'name': a.name, 'type': a.type, 'currency': a.currency} for a in accounts]}

# -------------------------------------------------------------------
# FROM: flat_admin_logistics_geography_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/admin_logistics_geography.py."""

from fastapi import Depends, HTTPException, Query, Path

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.accounts.models.user import User

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest

from infrastructure.utils.dependencies import require_admin, require_super_admin

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context


# TODO: Module not yet created
# from domains.logistics.services.partner_geography_service import approve_partner
# TODO: Module not yet created
# from domains.logistics.services.partner_geography_service import list_partners
# TODO: Module not yet created
# from domains.logistics.services.partner_geography_service import reject_partner
# TODO: Module not yet created
# from domains.logistics.services.partner_geography_service import toggle_partner_active

def list_partners_route(country_code: str, include_deleted: bool, page: int, page_size: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_partners(db, country_code, include_deleted, page, page_size)
    finally:
        clear_rls_context()

def approve_partner_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return approve_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()

def reject_partner_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return reject_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()

def toggle_partner_active_route(country_code: str, partner_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return toggle_partner_active(db, partner_id, country_code)
    finally:
        clear_rls_context()

def archive_partner(country_code: str, partner_id: int, payload: ArchiveRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()

def restore_partner(country_code: str, partner_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def bulk_archive_partners(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()

def bulk_restore_partners(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def delete_partner_permanent(country_code: str, partner_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()



# -------------------------------------------------------------------
# FROM: flat_admin_logistics_operations_service.py
# -------------------------------------------------------------------

"""
Admin Router — route declarations only (HTTP layer).
All business logic lives in controllers/admin_controller.py.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import Body, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from infrastructure.utils.constants import MAX_BULK_ITEMS
from infrastructure.database.database import get_db, Base
from infrastructure.database.schemas import User as UserSchema, Product as ProductSchema, Order as OrderSchema, CouponSchema, ListPage, AuditLogSchema, AuditLogPage, CreateStaffAccount, UpdateStaffAccount, BulkUpdateStaffBody
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.admin_service import get_current_admin
from infrastructure.utils.dependencies import require_admin
# TODO: Module not yet created
# from domains.governance.services.admin_service import require_admin_2fa_enabled
# TODO: Module not yet created
# from domains.governance.services.admin_service import require_admin_2fa_verified
# TODO: Module not yet created
# from domains.governance.services.effective_permissions import require_permission
# TODO: Module not yet created
# from domains.governance.services.users_service import get_all_users
# TODO: Module not yet created
# from domains.governance.services.users_service import update_user_role
# TODO: Module not yet created
# from domains.governance.services.users_service import toggle_user_active
# TODO: Module not yet created
# from domains.governance.services.identity_admin_service import delete_user_admin
# TODO: Module not yet created
# from domains.governance.services.admin_users import bulk_delete_users_admin
# TODO: Module not yet created
# from domains.governance.services.admin_users import force_reset_password_admin
# TODO: Module not yet created
# from domains.governance.services.users_service import create_staff_account
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.users_service import update_staff_account
# TODO: Module not yet created
# from domains.governance.services.users_service import bulk_update_staff_accounts
# TODO: Module not yet created
# from domains.governance.services.users_service import delete_staff_account
# TODO: Module not yet created
# from domains.governance.services.orders_service import get_all_orders
# TODO: Module not yet created
# from domains.governance.services.orders_service import delete_order_admin
# TODO: Module not yet created
# from domains.governance.services.orders_service import update_order_status
# TODO: Module not yet created
# from domains.governance.services.orders_service import refund_order
# TODO: Module not yet created
# from domains.governance.services.orders_service import update_order_tracking
# TODO: Module not yet created
# from domains.governance.services.products_service import get_all_products
# TODO: Module not yet created
# from domains.governance.services.products_service import delete_product_admin
# TODO: Module not yet created
# from domains.governance.services.products_service import restore_product_admin
# TODO: Module not yet created
# from domains.governance.services.analytics_service import get_analytics
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_supplier_comparison
# TODO: Module not yet created
# from domains.governance.services.analytics_service import get_customer_insights
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_pending_suppliers
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import verify_supplier
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import reject_supplier
# TODO: Module not yet created
# from domains.governance.services.products_service import get_pending_products
# TODO: Module not yet created
# from domains.governance.services.products.products_service import approve_product
# TODO: Module not yet created
# from domains.governance.services.products.products_service import reject_product
# TODO: Module not yet created
# from domains.governance.services.products_service import toggle_product_badge
# TODO: Module not yet created
# from domains.promotions.services.admin_commerce_configuration_service import list_coupons
# TODO: Module not yet created
# from domains.promotions.services.admin_commerce_configuration_service import create_coupon
from domains.promotions.ports import create_promotion_tier, delete_promotion_tier, get_promotion_config, list_promotion_tiers, preview_order_tier_discount, update_coupon, update_promotion_config, update_promotion_tier
# TODO: Module not yet created
# from domains.promotions.services.public_commerce_validation_service import delete_coupon
# TODO: Module not yet created
# from domains.comms.services.shared.ticket.tickets_service import list_tickets
# TODO: Module not yet created
# from domains.governance.services.admin_service import get_ticket_detail
# TODO: Module not yet created
# from domains.comms.services.shared.ticket.tickets_service import reply_to_ticket
# TODO: Module not yet created
# from domains.comms.services.shared.ticket.tickets_write_service import update_ticket_status
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.finance.services.payments.payout_approval_read_service import list_pending_payouts
# TODO: Module not yet created
# from domains.governance.services.admin.payouts_service import verify_payout
# TODO: Module not yet created
# from domains.accounts.services.permissions_service import get_hierarchy_permissions
# TODO: Module not yet created
# from domains.accounts.services.permissions_service import update_role_permissions
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.analytics_service import get_analytics_timeseries
# TODO: Module not yet created
# from domains.governance.services.analytics_service import get_top_products_analytics
# TODO: Module not yet created
# from domains.governance.services.analytics_service import get_user_growth_analytics
# TODO: Module not yet created
# from domains.governance.services.analytics_service import get_chatbot_analytics
# TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_all_suppliers
# TODO: Module not yet created
# from domains.governance.services.orders_service import bulk_update_order_status_admin
# TODO: Module not yet created
# from domains.governance.services.orders_service import bulk_delete_orders_admin
# TODO: Module not yet created
# from domains.governance.services.products_service import bulk_delete_products_admin
# TODO: Module not yet created
# from domains.governance.services.products_service import bulk_product_moderation
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import bulk_supplier_verification
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import bulk_manage_suppliers
# TODO: Module not yet created
# from domains.governance.services.users_service import bulk_update_users_role
# TODO: Module not yet created
# from domains.governance.services.users_service import bulk_toggle_users_active
# TODO: Module not yet created
# from domains.governance.services.users_service import list_staff_accounts
# TODO: Module not yet created
# from domains.accounts.services.permissions_service import get_staff_permission_catalog
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.users_service import update_staff_account
# TODO: Module not yet created
# from domains.governance.services.users_service import list_pending_bank_accounts
# TODO: Module not yet created
# from domains.governance.services.users_service import delete_bank_account_record
from domains.hr.services.payroll.payroll_service import verify_bank_account
# TODO: Module not yet created
# from domains.governance.services.database_service import get_database_overview
from domains.hr.ports import backfill_authority_levels, can_manage, get_all_subordinates, get_authority_level, get_home_org_unit, get_org_chart, get_team_members, get_user_chain, is_in_chain, reassign_manager
# TODO: Module not yet created
# from domains.governance.services.approval_matrix_service import APPROVAL_RULES
# TODO: Module not yet created
# from domains.governance.services.approval_matrix_service import can_approve
# TODO: Module not yet created
# from domains.governance.services.approval_matrix_service import require_approval
# TODO: Module not yet created
# from domains.governance.services.approval_matrix_service import resolve_approvers
# TODO: Module not yet created
# from domains.governance.services.approval_matrix_service import get_approval_chain
# TODO: Module not yet created
# from domains.catalog.services.banners.banner_service import get_banners
# TODO: Module not yet created
# from domains.catalog.services.banners.banner_service import get_banner_by_id
# TODO: Module not yet created
# from domains.catalog.services.banners.banner_service import create_banner
# TODO: Module not yet created
# from domains.catalog.services.banners.banner_service import update_banner
# TODO: Module not yet created
# from domains.catalog.services.banners.banner_service import delete_banner
# TODO: Module not yet created
# from domains.catalog.services.banners.banner_service import BannerCreate
# TODO: Module not yet created
# from domains.catalog.services.banners.banner_service import BannerUpdate
from infrastructure.utils.backup import get_backup_manager
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
# TODO: Module not yet created
# from domains.orders.services.flash_sale_service import get_all_flash_sales
# TODO: Module not yet created
# from domains.orders.services.flash_sale_service import create_flash_sale
# TODO: Module not yet created
# from domains.orders.services.flash_sale_service import update_flash_sale
# TODO: Module not yet created
# from domains.orders.services.flash_sale_service import delete_flash_sale

class BulkDeleteUsersBody(BaseModel):
    user_ids: List[int]

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkToggleActiveBody(BaseModel):
    user_ids: List[int]
    is_active: bool

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkUserRoleBody(BaseModel):
    user_ids: List[int]
    role: str

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class ResetPasswordBody(BaseModel):
    new_password: str

class BulkOrderStatusBody(BaseModel):
    order_ids: List[int]
    status: str

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkOrderDeleteBody(BaseModel):
    order_ids: List[int]

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkProductDeleteBody(BaseModel):
    product_ids: List[int]

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkProductModerationBody(BaseModel):
    product_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkSupplierVerifyBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkSupplierLifecycleBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None
    badge_level: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class PromotionConfigBody(BaseModel):
    engine_enabled: Optional[bool] = None
    allow_product_coupons: Optional[bool] = None
    allow_category_coupons: Optional[bool] = None
    allow_order_tier_discounts: Optional[bool] = None
    allow_referral_rewards: Optional[bool] = None
    allow_supplier_promotions: Optional[bool] = None
    allow_global_coupons: Optional[bool] = None
    stacking_mode: Optional[str] = None
    max_combined_discount_percent: Optional[float] = None
    max_combined_discount_amount: Optional[float] = None
    show_savings_line_item: Optional[bool] = None
    tier_discount_visible: Optional[bool] = None
    points_per_omr: Optional[int] = None
    referral_referrer_points: Optional[int] = None
    referral_referee_points: Optional[int] = None
    points_expiry_months: Optional[int] = None
    referral_monthly_cap: Optional[int] = None
    referral_verification_delay_days: Optional[int] = None
    min_points_redeem: Optional[int] = None
    allow_partial_points_redemption: Optional[bool] = None

class PromotionTierBody(BaseModel):
    tier_name: str
    min_order: float
    max_order: Optional[float] = None
    discount_type: str
    discount_value: float
    stacking_allowed: bool = False
    is_active: bool = True
    sort_order: int = 0

class PromotionTierUpdateBody(BaseModel):
    tier_name: Optional[str] = None
    min_order: Optional[float] = None
    max_order: Optional[float] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    stacking_allowed: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class PromotionPreviewBody(BaseModel):
    order_subtotal: float
    coupon_discount: float = 0.0

class AdminDisputeBulkActionBody(BaseModel):
    dispute_ids: List[int]
    action: str
    value: Optional[str] = None

    @field_validator('dispute_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class UpdateRolePermissionsIn(BaseModel):
    permissions: List[str]

class ReassignManagerBody(BaseModel):
    user_id: int
    new_manager_id: int | None = None

class ResourceApprovalCheckIn(BaseModel):
    resource_type: str
    amount: Optional[float] = None

def verify_payout_route(payout_id: int, data: dict, db: Session=Depends(get_db), current_admin: dict=Depends(require_admin_2fa_verified)):
    require_permission('payouts.verify', current_admin)
    from domains.finance.models.payments import Payout
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    amount = float(payout.amount) if payout and payout.amount is not None else None
    require_approval(db, current_admin['id'], 'payout', amount=amount)
    return verify_payout(payout_id, data, current_admin, db)

def admin_email_stats(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Real email marketing statistics from the database."""
    require_permission('analytics.view', current_admin)
    from sqlalchemy import func as sqlfunc, case as sql_case
    from domains.comms.models.marketing import NewsletterSubscriber
    from domains.comms.models.marketing import EmailCampaign
    from domains.comms.models.marketing import CampaignRecipient
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0
    campaign_stats = db.query(sqlfunc.count(EmailCampaign.id).label('total'), sqlfunc.sum(sql_case((EmailCampaign.status == 'sending', 1), else_=0)).label('active')).first()
    total_sent = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.sent_at.isnot(None)).scalar() or 0
    total_opened = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.opened_at.isnot(None)).scalar() or 0
    total_clicked = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.clicked_at.isnot(None)).scalar() or 0
    open_rate = round(total_opened / total_sent * 100, 1) if total_sent else 0
    click_rate = round(total_clicked / total_opened * 100, 1) if total_opened else 0
    recent_campaigns = db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(10).all()

    def _ser_campaign(c: EmailCampaign):
        recipient_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.campaign_id == c.id).scalar() or 0
        return {'id': c.id, 'name': c.name, 'subject': c.subject, 'status': c.status, 'recipient_count': recipient_count, 'sent_count': recipient_count, 'opened_count': total_opened, 'clicked_count': total_clicked, 'send_at': c.send_at.isoformat() if c.send_at else None, 'sent_at': c.send_at.isoformat() if c.send_at else None, 'created_at': c.created_at.isoformat() if c.created_at else None}
    return {'total_subscribers': total_subscribers, 'active_campaigns': int(campaign_stats.active or 0), 'total_campaigns': int(campaign_stats.total or 0), 'total_sent': total_sent, 'open_rate': open_rate, 'click_rate': click_rate, 'recent_campaigns': [_ser_campaign(c) for c in recent_campaigns]}

def admin_logistics_overview(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Admin overview of all shipments, carriers, and distribution channels."""
    require_permission('orders.manage', current_admin)
    from sqlalchemy import func as sqlfunc
    from domains.governance.models.admin import ShippingCarrier
    from domains.governance.models.admin import ShippingZone
    from domains.logistics.models.logistics import Shipment
    shipment_counts = db.query(Shipment.status, sqlfunc.count(Shipment.id).label('count')).group_by(Shipment.status).all()
    channel_counts = db.query(Shipment.distribution_channel, sqlfunc.count(Shipment.id).label('count')).filter(Shipment.distribution_channel.isnot(None)).group_by(Shipment.distribution_channel).all()
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()
    recent_shipments = db.query(Shipment).order_by(Shipment.updated_at.desc()).limit(20).all()

    def _ser_shipment(s: Shipment):
        return {'id': s.id, 'order_id': s.order_id, 'supplier_id': s.supplier_id, 'carrier_name': s.carrier_name, 'tracking_number': s.tracking_number, 'status': s.status, 'distribution_channel': s.distribution_channel, 'current_hub': s.current_hub, 'scan_code': s.scan_code, 'shipped_at': s.shipped_at.isoformat() if s.shipped_at else None, 'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None, 'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None}
    return {'shipment_by_status': {s: c for (s, c) in shipment_counts}, 'shipment_by_channel': {ch: c for (ch, c) in channel_counts}, 'active_carriers': [{'id': c.id, 'name': c.name, 'code': c.code, 'is_global': c.supplier_id is None} for c in carriers], 'active_zones': zones, 'recent_shipments': [_ser_shipment(s) for s in recent_shipments]}

def admin_reset_demo_data(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """
    Clear all non-essential seed data — orders, products, reviews, communication
    data, coupons, and non-admin users — so the demo environment can be reset
    from the UI without SSH or terminal access.

    Admin user accounts (role=admin) are preserved.
    """
    require_admin(current_admin)
    app_env = getattr(settings, 'APP_ENV', None)
    if not app_env or app_env not in ('development', 'dev', 'test'):
        raise HTTPException(status_code=400, detail='Reset is only available in development/test environments')
    from datetime import datetime, timezone
    from sqlalchemy import text
    tables_to_clear = ['entity_chat_messages', 'entity_chat_threads', 'group_chat_messages', 'group_chat_members', 'group_chat_rooms', 'direct_chat_messages', 'direct_chat_rooms', 'internal_emails', 'email_folders', 'order_items', 'orders', 'reviews', 'order_logistics_allocations', 'shipments', 'wishlist_items', 'cart_items', 'coupon_usages', 'coupons', 'promotion_ledger_entries', 'promotion_order_tiers', 'product_variants', 'products', 'categories', 'audit_logs', 'notifications']
    deleted_counts: dict[str, int] = {}
    for table in tables_to_clear:
        try:
            if table not in Base.metadata.tables:
                deleted_counts[table] = -1
                continue
            result = db.execute(Base.metadata.tables[table].delete())
            deleted_counts[table] = result.rowcount or 0
        except Exception:
            deleted_counts[table] = -1
    non_admin_count = db.execute(text("DELETE FROM users WHERE role != 'admin'")).rowcount or 0
    deleted_counts['users_(non_admin)'] = non_admin_count
    try:
        db.execute(text('DELETE FROM sqlite_sequence'))
    except Exception:
        pass
    db.commit()
    total = sum((v for v in deleted_counts.values() if v >= 0))
    return {'detail': 'Demo data reset complete', 'tables_cleared': len(tables_to_clear) + 1, 'total_rows_deleted': total, 'counts': deleted_counts, 'note': 'Admin accounts preserved. Run seed_all.py to re-seed.'}

class BulkDeleteUsersBody(BaseModel):
    user_ids: List[int]

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class BulkToggleActiveBody(BaseModel):
    user_ids: List[int]
    is_active: bool

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class BulkUserRoleBody(BaseModel):
    user_ids: List[int]
    role: str

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class ResetPasswordBody(BaseModel):
    new_password: str
class BulkOrderStatusBody(BaseModel):
    order_ids: List[int]
    status: str

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class BulkOrderDeleteBody(BaseModel):
    order_ids: List[int]

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class BulkProductDeleteBody(BaseModel):
    product_ids: List[int]

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class BulkProductModerationBody(BaseModel):
    product_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class BulkSupplierVerifyBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class BulkSupplierLifecycleBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None
    badge_level: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class PromotionConfigBody(BaseModel):
    engine_enabled: Optional[bool] = None
    allow_product_coupons: Optional[bool] = None
    allow_category_coupons: Optional[bool] = None
    allow_order_tier_discounts: Optional[bool] = None
    allow_referral_rewards: Optional[bool] = None
    allow_supplier_promotions: Optional[bool] = None
    allow_global_coupons: Optional[bool] = None
    stacking_mode: Optional[str] = None
    max_combined_discount_percent: Optional[float] = None
    max_combined_discount_amount: Optional[float] = None
    show_savings_line_item: Optional[bool] = None
    tier_discount_visible: Optional[bool] = None
    points_per_omr: Optional[int] = None
    referral_referrer_points: Optional[int] = None
    referral_referee_points: Optional[int] = None
    points_expiry_months: Optional[int] = None
    referral_monthly_cap: Optional[int] = None
    referral_verification_delay_days: Optional[int] = None
    min_points_redeem: Optional[int] = None
    allow_partial_points_redemption: Optional[bool] = None
class PromotionTierBody(BaseModel):
    tier_name: str
    min_order: float
    max_order: Optional[float] = None
    discount_type: str
    discount_value: float
    stacking_allowed: bool = False
    is_active: bool = True
    sort_order: int = 0
class PromotionTierUpdateBody(BaseModel):
    tier_name: Optional[str] = None
    min_order: Optional[float] = None
    max_order: Optional[float] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    stacking_allowed: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
class PromotionPreviewBody(BaseModel):
    order_subtotal: float
    coupon_discount: float = 0.0
class AdminDisputeBulkActionBody(BaseModel):
    dispute_ids: List[int]
    action: str
    value: Optional[str] = None

    @field_validator('dispute_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v
class UpdateRolePermissionsIn(BaseModel):
    permissions: List[str]
class ReassignManagerBody(BaseModel):
    user_id: int
    new_manager_id: int | None = None
class ResourceApprovalCheckIn(BaseModel):
    resource_type: str
    amount: Optional[float] = None

# -------------------------------------------------------------------
# FROM: country_communication_service.py
# -------------------------------------------------------------------

"""Service methods for country communication data access."""
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from domains.country.models.countries import CountryCommunication
from domains.governance.models.legal_contract_template import LegalContractTemplate
from domains.country.models.country_control import ShopWarehouseLocation
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.customers.models.cross_country_session import CrossCountryCustomerSession
from domains.logistics.models.logistics import LogisticsPartner
import structlog
logger = structlog.get_logger(__name__)


def get_country_communications(
    db: Session, user_id: int, status: str | None = None, priority: str | None = None, limit: int = 50
) -> list[dict]:
    """Get country communications for a user."""
    query = db.query(CountryCommunication).filter(
        (CountryCommunication.to_user_id == user_id)
        | (CountryCommunication.to_user_id.is_(None))
    )
    if status:
        query = query.filter(CountryCommunication.status == status)
    if priority:
        query = query.filter(CountryCommunication.priority == priority)
    comms = query.order_by(desc(CountryCommunication.created_at)).limit(limit).all()
    return [
        {
            "id": c.id,
            "country_code": c.country_code,
            "from_user_id": c.from_user_id,
            "subject": c.subject,
            "body": c.body,
            "priority": c.priority,
            "category": c.category,
            "related_entity_type": c.related_entity_type,
            "related_entity_id": c.related_entity_id,
            "status": c.status,
            "read_at": c.read_at.isoformat() if c.read_at else None,
            "created_at": c.created_at.isoformat(),
        }
        for c in comms
    ]


def get_country_communication_by_id(db: Session, comm_id: int) -> CountryCommunication | None:
    """Get a single country communication by ID."""
    return db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()


def mark_country_communication_read(db: Session, comm: CountryCommunication) -> dict:
    """Mark a communication as read."""
    comm.status = "read"
    comm.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "read", "read_at": comm.read_at.isoformat()}


def get_cross_border_sessions(db: Session, country_code: str) -> list[dict]:
    """Get recent cross-border customer sessions for a country."""
    sessions = (
        db.query(CrossCountryCustomerSession)
        .filter(CrossCountryCustomerSession.target_country_code == country_code.upper())
        .order_by(CrossCountryCustomerSession.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "source_country_code": s.source_country_code,
            "target_country_code": s.target_country_code,
            "conversion": s.conversion,
            "order_id": s.order_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


def get_legal_contracts(db: Session, country_code: str) -> list[dict]:
    """Get active legal contract templates for a country."""
    contracts = (
        db.query(LegalContractTemplate)
        .filter(
            LegalContractTemplate.country_code == country_code.upper(),
            LegalContractTemplate.is_active.is_(True),
        )
        .order_by(LegalContractTemplate.created_at.desc())
        .limit(SAFE_QUERY_LIMIT).all()
    )
    return [
        {
            "id": c.id,
            "country_code": c.country_code,
            "template_type": c.template_type,
            "version": c.version,
            "content": c.content,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contracts
    ]


def get_shop_warehouses(db: Session, country_code: str) -> list[dict]:
    """Get active shop warehouse locations for a country."""
    warehouses = (
        db.query(ShopWarehouseLocation)
        .filter(
            ShopWarehouseLocation.country_code == country_code.upper(),
            ShopWarehouseLocation.is_active.is_(True),
        )
        .limit(SAFE_QUERY_LIMIT).all()
    )
    return [
        {
            "id": w.id,
            "country_code": w.country_code,
            "name": w.name,
            "warehouse_code": w.warehouse_code,
            "latitude": float(w.latitude) if w.latitude else None,
            "longitude": float(w.longitude) if w.longitude else None,
            "address": w.address,
            "is_active": w.is_active,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in warehouses
    ]


def get_partner_locations(db: Session, country_code: str) -> list[dict]:
    """Get active logistics partner locations for a country."""
    locations = (
        db.query(LogisticsPartnerLocation)
        .join(LogisticsPartner)
        .filter(
            LogisticsPartnerLocation.country_code == country_code.upper(),
            LogisticsPartnerLocation.is_active.is_(True),
        )
        .limit(SAFE_QUERY_LIMIT).all()
    )
    return [
        {
            "id": p.id,
            "partner_id": p.partner_id,
            "partner": {"name": p.partner.name} if p.partner else None,
            "country_code": p.country_code,
            "location_type": p.location_type,
            "latitude": float(p.latitude) if p.latitude else None,
            "longitude": float(p.longitude) if p.longitude else None,
            "address": p.address,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in locations
    ]

# -------------------------------------------------------------------
# FROM: logistics_analytics_service.py
# -------------------------------------------------------------------

"""Logistics analytics aggregation helpers.

These live behind the service layer so the request-path (routers/controllers) never
issues live aggregates (``func.count`` / ``group_by``) directly. Moving the heavy
aggregation here clears DB19 (analytics snapshot discipline).
"""

from sqlalchemy import func

from infrastructure.utils.pagination import SAFE_QUERY_LIMIT, windowed_iterate
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
import structlog
logger = structlog.get_logger(__name__)


def partner_status_breakdown(shipments_q, db) -> dict:
    """Return {status: count} for the given shipments query (keyset-paced)."""
    return {
        shipment_status: count
        for shipment_status, count in windowed_iterate(
            shipments_q.with_entities(Shipment.status, func.count(Shipment.id)).group_by(
                Shipment.status
            )
        )
    }


def shipments_with_events_count(shipments_q, db, shipment_ids_subquery) -> int:
    """Count distinct shipments that have at least one event recorded."""
    return (
        db.query(func.count(func.distinct(ShipmentEvent.shipment_id)))
        .filter(ShipmentEvent.shipment_id.in_(db.query(shipment_ids_subquery.c.id)))
        .scalar()
        or 0
    )


def order_shipment_counts(order_ids: list, db) -> dict:
    """Return {order_id: shipment_count} for the supplied order ids."""
    if not order_ids:
        return {}
    rows = (
        db.query(Shipment.order_id, func.count(Shipment.id))
        .filter(Shipment.order_id.in_(order_ids))
        .group_by(Shipment.order_id)
        .limit(SAFE_QUERY_LIMIT)
        .all()
    )
    return {int(order_id): int(count) for order_id, count in rows}


def partner_dashboard_channel_stats(shipments_q, db) -> list:
    """Return [(distribution_channel, count), ...] for non-null channels."""
    return list(
        shipments_q.filter(Shipment.distribution_channel.isnot(None))
        .with_entities(Shipment.distribution_channel, func.count(Shipment.id))
        .group_by(Shipment.distribution_channel)
        .limit(SAFE_QUERY_LIMIT)
        .all()
    )

# -------------------------------------------------------------------
# FROM: logistics_locations_create_service.py
# -------------------------------------------------------------------

"""
Logistics Partner Location Router
"""
import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.logistics.models.logistics import LogisticsPartner
from infrastructure.utils.dependencies import get_current_user
logger = logging.getLogger(__name__)

def list_logistics_partner_locations(country_code: str=Path(...), partner_id: Optional[int]=Query(None), is_active: Optional[bool]=Query(None), db: Session=Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(LogisticsPartnerLocation).filter(LogisticsPartnerLocation.country_code == country_code.upper())
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at).all()
    return [{'id': loc.id, 'partner_id': loc.partner_id, 'location_type': loc.location_type, 'latitude': loc.latitude, 'longitude': loc.longitude, 'address': loc.address, 'is_active': loc.is_active, 'created_at': loc.created_at} for loc in locations]

def create_logistics_partner_location(country_code: str=Path(...), payload: dict=None, db: Session=Depends(get_db), current_user=Depends(get_current_user)):
    if not payload:
        payload = {}
    config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    if not config:
        raise HTTPException(status_code=404, detail='Country not found')
    partner_id = payload.get('partner_id')
    if not partner_id:
        raise HTTPException(status_code=422, detail='partner_id is required')
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail='Logistics partner not found')
    location = LogisticsPartnerLocation(country_code=country_code.upper(), partner_id=partner_id, location_type=payload.get('location_type', 'warehouse'), latitude=payload.get('latitude'), longitude=payload.get('longitude'), address=payload.get('address'), is_active=payload.get('is_active', True))
    db.add(location)
    db.commit()
    db.refresh(location)
    return {'id': location.id, 'message': 'Logistics partner location created'}

# -------------------------------------------------------------------
# FROM: logistics_locations_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/logistics_locations.py."""

import logging

from typing import List, Optional

from fastapi import Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session


from infrastructure.database.database import get_db

from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.logistics.models.logistics import LogisticsPartner

logger = logging.getLogger(__name__)

def list_logistics_partner_locations(country_code: str, partner_id: Optional[int], is_active: Optional[bool], db: Session, current_user):
    query = db.query(LogisticsPartnerLocation).filter(
        LogisticsPartnerLocation.country_code == country_code.upper()
    )
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

def create_logistics_partner_location(country_code: str, payload: dict, db: Session, current_user):
    if not payload:
        payload = {}
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


# -------------------------------------------------------------------
# FROM: logistics_logistics_partner_write_service.py
# -------------------------------------------------------------------

# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.logistics.logistics_partner_write_service re-exports for HTTP routers."""
from domains.logistics.services.partners.service import admin_update_shipment_status as svc_admin_update_shipment_status
from domains.logistics.services.partners.service import create_logistics_partner_location
from domains.logistics.services.partners.service import list_logistics_partner_locations

from domains.logistics.services.partners.service import admin_update_shipment_status

# -------------------------------------------------------------------
# FROM: logistics_logistics_status_service.py
# -------------------------------------------------------------------

"""
Logistics Router — shipping carriers, zones, and shipment fulfilment.
All business logic lives in controllers/logistics_controller.py.
"""
from typing import Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user
import domains.logistics.services.core.logistics_service as ctrl

async def scan_lookup_shipment(code: str, db: Session=Depends(get_db), current_user: dict=Depends(get_current_user)):
    """Look up a shipment by tracking number or scan code. Admin only."""
    if str(current_user.get('role') or '').lower() not in ('admin', 'sub_admin', 'moderator', 'support'):
        raise HTTPException(status_code=403, detail='Admin access required')
    from domains.logistics.models.logistics import Shipment
    shipment = db.query(Shipment).filter((Shipment.tracking_number == code) | (Shipment.id == (int(code) if code.isdigit() else -1))).first()
    if not shipment:
        raise HTTPException(status_code=404, detail='Shipment not found')
    return {'id': shipment.id, 'order_id': shipment.order_id, 'status': shipment.status, 'carrier_name': shipment.carrier_name, 'tracking_number': shipment.tracking_number, 'distribution_channel': shipment.distribution_channel, 'current_hub': shipment.current_hub, 'shipping_address': shipment.order.shipping_address if shipment.order else None, 'created_at': shipment.created_at.isoformat() if shipment.created_at else None, 'updated_at': shipment.updated_at.isoformat() if shipment.updated_at else None}

async def admin_update_shipment_status(shipment_id: int, data: dict[str, Any], db: Session=Depends(get_db), current_user: dict=Depends(get_current_user)):
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    if str(current_user.get('role') or '').lower() not in ('admin', 'sub_admin', 'moderator', 'support'):
        raise HTTPException(status_code=403, detail='Admin access required')
    from domains.logistics.models.logistics import Shipment
    from domains.logistics.models.logistics import ShipmentEvent
    from datetime import datetime, timezone
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail='Shipment not found')
    new_status = data.get('status')
    if new_status:
        shipment.status = new_status
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if new_status == 'delivered' and (not shipment.actual_delivery):
            shipment.actual_delivery = now
        elif new_status == 'shipped' and (not shipment.shipped_at):
            shipment.shipped_at = now
        event = ShipmentEvent(shipment_id=shipment_id, event_type='status_change', status_after=new_status, location=shipment.current_hub, notes=data.get('note', 'Admin status update'), created_at=now)
        db.add(event)
    db.commit()
    db.refresh(shipment)
    return {'id': shipment.id, 'order_id': shipment.order_id, 'status': shipment.status, 'carrier_name': shipment.carrier_name, 'tracking_number': shipment.tracking_number, 'distribution_channel': shipment.distribution_channel, 'current_hub': shipment.current_hub}

# -------------------------------------------------------------------
# FROM: geography_country_audit_admin_service.py
# -------------------------------------------------------------------

# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.geography.country_audit_admin_service re-exports for HTTP routers."""
from domains.country.ports import add_city, add_country_city, archive_country, assign_staff, bulk_archive_countries, bulk_restore_countries, create_country_commission_rate, create_feature_flag, delete_city, delete_country_city, delete_country_commission_rate, delete_feature_flag, hard_delete_country, list_cities, list_communications, list_country_commission_rates, list_staff, list_tax_rates, mark_communication_read, patch_country_city, remove_staff, restore_country, send_country_communication, set_tax_rate, toggle_country_active, update_city, update_feature_flag


# -------------------------------------------------------------------
# FROM: geography_country_config_admin_service.py
# -------------------------------------------------------------------

# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.geography.country_config_admin_service re-exports for HTTP routers."""


# -------------------------------------------------------------------
# FROM: main.py
# -------------------------------------------------------------------

"""Standalone IP/location tracking server for the Zozi order/delivery system.

Run with the backend virtual environment:

    cd backend
    python run_location_server.py
    # or:
    uvicorn services.location_service.main:app --port 8005 --reload

Endpoints
---------
GET  /api/health                              liveness probe
GET  /api/geo/from-ip?ip=1.2.3.4             geolocate an arbitrary IP (omit ip for caller)
GET  /api/geo/locate                          geolocate the calling client
POST /api/geo/reverse  {lat, lon}            reverse geocode coordinates -> address
POST /api/geo/resolve   {ip?}                IP -> coords + (best-effort) address

No coordinates are ever fabricated. When a lookup is impossible a 502 with a clear
message is returned so the frontend can rely on the browser Geolocation API.
"""


import logging
import os

from fastapi import FastAPI, Header, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from providers.geography.geo import resolve_ip_location, reverse_geocode
from infrastructure.utils.auth import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("location_service")

app = FastAPI(title="Zozi Location Service", version="1.0.0")

# CORS: default to empty list; set LOCATION_CORS_ORIGINS env var (comma-separated) in production
# Example: LOCATION_CORS_ORIGINS=https://zozi.com,https://admin.zozi.com
_cors_origins = os.getenv("LOCATION_CORS_ORIGINS", "").strip()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",") if o.strip()] or [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer_scheme = HTTPBearer(auto_error=False)


class ReverseRequest(BaseModel):
    lat: float
    lon: float


class ResolveRequest(BaseModel):
    ip: str | None = None


def _get_current_user_geo(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme)):
    """Authenticate geo API requests via bearer token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return payload


def _client_meta(request: Request, x_forwarded_for: str | None, x_real_ip: str | None):
    client_host = request.client.host if request.client else "127.0.0.1"
    return client_host, x_forwarded_for, x_real_ip


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "location", "version": "1.0.0"}


@app.get("/api/geo/from-ip")
def geo_from_ip(
    request: Request,
    ip: str | None = None,
    x_forwarded_for: str | None = Header(None),
    x_real_ip: str | None = Header(None),
    _user: dict = Depends(_get_current_user_geo),
):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        location = resolve_ip_location(ip=ip, client_host=client_host, forwarded_for=fwd, real_ip=real)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return location.to_dict()


@app.get("/api/geo/locate")
def geo_locate(
    request: Request,
    x_forwarded_for: str | None = Header(None),
    x_real_ip: str | None = Header(None),
    _user: dict = Depends(_get_current_user_geo),
):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        location = resolve_ip_location(client_host=client_host, forwarded_for=fwd, real_ip=real)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return location.to_dict()


@app.post("/api/geo/reverse")
def geo_reverse(payload: ReverseRequest, _user: dict = Depends(_get_current_user_geo)):
    try:
        result = reverse_geocode(payload.lat, payload.lon)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return result.to_dict()


@app.post("/api/geo/resolve")
def geo_resolve(
    payload: ResolveRequest,
    request: Request,
    x_forwarded_for: str | None = Header(None),
    x_real_ip: str | None = Header(None),
    _user: dict = Depends(_get_current_user_geo),
):
    client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
    try:
        location = resolve_ip_location(ip=payload.ip, client_host=client_host, forwarded_for=fwd, real_ip=real)
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_service"})
    return location.to_dict()


# -------------------------------------------------------------------
# FROM: operations\logistics_engine.py
# -------------------------------------------------------------------


import json
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPricingProfile
# TODO: Module not yet created
# from domains.logistics.services.partner.logistics_partner_pricing import normalize_country_code

logger = logging.getLogger(__name__)


class LogisticsEngine:
    """Country-aware logistics provider orchestration.

    Reads provider config from ``CountryConfig.logistics_providers_json``
    and maps to ``LogisticsPartner`` models for shipment fulfilment.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ─────────────────────────────────────────────────────────

    def get_enabled_providers(self, country_code: str) -> list[dict[str, Any]]:
        """Return enabled logistics providers configured for a country."""
        country = self._get_country(country_code)
        if not country:
            return []
        raw_providers = self._parse_providers(country)
        return [p for p in raw_providers if p.get("enabled", False)]

    def get_provider_rates(self, country_code: str) -> list[dict[str, Any]]:
        """Return all providers with their pricing for a country."""
        providers = self.get_enabled_providers(country_code)
        for prov in providers:
            partner = self._find_partner(prov["provider_id"])
            prov["partner_registered"] = partner is not None
            if partner:
                prov["partner_id"] = partner.id
                prov["verification_status"] = partner.verification_status
        return providers

    def calculate_shipping_cost(
        self,
        country_code: str,
        provider_id: str,
        *,
        weight_kg: float = 0.0,
        distance_km: float = 0.0,
        is_express: bool = False,
    ) -> dict[str, Any]:
        """Calculate shipping cost for a given provider and country."""
        country = self._get_country(country_code)
        if not country:
            return {"error": "Country not found", "cost": None}

        providers = self._parse_providers(country)
        provider_config = None
        for p in providers:
            if str(p.get("provider_id", "")).lower() == provider_id.lower():
                provider_config = p
                break

        if not provider_config:
            return {"error": f"Provider '{provider_id}' not configured for {country_code}", "cost": None}
        if not provider_config.get("enabled", False):
            return {"error": f"Provider '{provider_id}' is disabled for {country_code}", "cost": None}

        base_rate = Decimal(str(provider_config.get("base_rate", 0)))
        per_kg_rate = Decimal(str(provider_config.get("per_kg_rate", 0)))
        currency = provider_config.get("currency") or country.currency

        total = base_rate + (per_kg_rate * Decimal(str(weight_kg)))
        if distance_km > 0:
            total += base_rate * Decimal(str(distance_km)) / Decimal("10")

        sla_key = "sla_express_days" if is_express else "sla_standard_days"
        sla = provider_config.get(sla_key, "3-5")

        partner = self._find_partner(provider_id)

        return {
            "provider_id": provider_id,
            "provider_name": provider_config.get("name", provider_id),
            "country_code": country_code,
            "currency": currency,
            "base_rate": float(base_rate),
            "per_kg_rate": float(per_kg_rate),
            "weight_kg": weight_kg,
            "distance_km": distance_km,
            "total_cost": float(total),
            "sla_days": sla,
            "is_express": is_express,
            "partner_registered": partner is not None,
            "partner_id": partner.id if partner else None,
            "partner_verified": partner.verification_status == "approved" if partner else False,
        }

    def register_provider(
        self,
        country_code: str,
        provider_config: dict[str, Any],
        *,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        """Upsert a logistics provider into a country's config.

        ``provider_config`` must include at minimum ``provider_id`` and ``name``.
        """
        country = self._get_country(country_code)
        if not country:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Country not found")

        provider_id = str(provider_config.get("provider_id") or "").strip().lower()
        if not provider_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="provider_id is required")

        raw = country.logistics_providers_json
        try:
            providers = json.loads(raw) if isinstance(raw, str) else (raw or [])
        except (json.JSONDecodeError, TypeError):
            providers = []
        if not isinstance(providers, list):
            providers = []

        existing = None
        for p in providers:
            if isinstance(p, dict) and str(p.get("provider_id", "")).lower() == provider_id:
                existing = p
                break

        normalized = {
            "provider_id": provider_id,
            "name": str(provider_config.get("name") or provider_id).strip(),
            "enabled": bool(provider_config.get("enabled", True)),
            "service_areas": provider_config.get("service_areas") if isinstance(provider_config.get("service_areas"), list) else ["all_regions"],
            "sla_standard_days": str(provider_config.get("sla_standard_days") or "3-5").strip(),
            "sla_express_days": str(provider_config.get("sla_express_days") or "1-2").strip(),
            "base_rate": float(provider_config.get("base_rate") or 0),
            "per_kg_rate": float(provider_config.get("per_kg_rate") or 0),
            "currency": str(provider_config.get("currency") or "").strip().upper() or None,
        }

        if existing:
            existing.update(normalized)
        else:
            providers.append(normalized)

        country.logistics_providers_json = json.dumps(providers, default=str)
        self.db.commit()
        self.db.refresh(country)

        return {
            "message": f"Provider '{provider_id}' {'updated' if existing else 'created'} for {country_code}",
            "provider": normalized,
        }

    # ── Internal helpers ───────────────────────────────────────────────────

    def _get_country(self, country_code: str) -> CountryConfig | None:
        return self.db.query(CountryConfig).filter(
            CountryConfig.code == normalize_country_code(country_code),
            CountryConfig.is_active == True,
        ).first()

    def _parse_providers(self, country: CountryConfig) -> list[dict[str, Any]]:
        raw = country.logistics_providers_json
        if not raw:
            return []
        try:
            providers = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return []
        return providers if isinstance(providers, list) else []

    def _find_partner(self, provider_id: str) -> LogisticsPartner | None:
        return self.db.query(LogisticsPartner).filter(
            LogisticsPartner.code == provider_id.lower(),
        ).first()


# -------------------------------------------------------------------
# FROM: operations\logistics_write_service.py
# -------------------------------------------------------------------

"""Logistics write operations: shipping carriers, zones, and shipment events."""

import json
from typing import Optional

from sqlalchemy.orm import Session

from domains.governance.models.admin import ShippingCarrier, ShippingZone
from domains.governance.ports import get_shipping_carrier_by_id, get_shipping_zone_by_id
from domains.logistics.models.logistics import ShipmentEvent
import structlog
logger = structlog.get_logger(__name__)


def _is_orm(obj, Model) -> bool:
    """True when ``obj`` is an ORM instance of ``Model`` (vs an id)."""
    return isinstance(obj, Model)


def _apply_changes(record, changes):
    """Apply a dict of field -> value to an ORM row, skipping ``None`` values.

    Mirrors the convention used across the other write services so updates are
    idempotent and never reset fields the caller didn't ask to change.
    """
    for field, value in (changes or {}).items():
        if value is None:
            continue
        if hasattr(record, field):
            setattr(record, field, value)
    return record


def _model_kwargs(Model, kwargs):
    """Keep only kwargs that map to real columns on ``Model`` (absorbs extras)."""
    cols = {c.name for c in Model.__table__.columns}
    return {k: v for k, v in kwargs.items() if k in cols}


def create_shipping_carrier(
    db: Session,
    *,
    name: str,
    code: str,
    supplier_id: Optional[int] = None,
    country_code: Optional[str] = None,
    is_active: bool = True,
    **extra,
) -> ShippingCarrier:
    """Create a supplier-specific shipping carrier.

    Absorbs caller-supplied extras (e.g. ``tracking_url``/``notes``) that are not
    part of the persisted model so legacy callers keep working.
    """
    carrier = ShippingCarrier(
        **_model_kwargs(
            ShippingCarrier,
            dict(name=name, code=code, supplier_id=supplier_id,
                 country_code=country_code, is_active=is_active, **extra),
        )
    )
    db.add(carrier)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(carrier)
    return carrier


def create_shipping_zone(
    db: Session,
    *,
    name: str,
    countries,
    supplier_id: Optional[int] = None,
    country_code: Optional[str] = None,
    is_active: bool = True,
    **extra,
) -> ShippingZone:
    """Create a shipping zone. ``countries`` may be a JSON string or list."""
    if isinstance(countries, (list, tuple, dict)):
        countries = json.dumps(countries)
    zone = ShippingZone(
        **_model_kwargs(
            ShippingZone,
            dict(name=name, countries=countries, supplier_id=supplier_id,
                 country_code=country_code, is_active=is_active, **extra),
        )
    )
    db.add(zone)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(zone)
    return zone


def update_shipping_zone(db: Session, zone_or_id, changes: Optional[dict] = None, **kw):
    """Update a shipping zone (id or ORM object)."""
    if _is_orm(zone_or_id, ShippingZone):
        record = zone_or_id
    else:
        record = get_shipping_zone_by_id(db, int(zone_or_id))
        if record is None:
            raise ValueError(f"ShippingZone {zone_or_id} not found")
    _apply_changes(record, changes or kw)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record


def update_shipping_carrier(db: Session, carrier_or_id, changes: Optional[dict] = None, **kw):
    """Update a shipping carrier.

    Compatible with both the spec form ``(db, id, **changes)`` and the legacy
    controller form ``(db, carrier_obj, {"is_active": False})``.
    """
    if _is_orm(carrier_or_id, ShippingCarrier):
        record = carrier_or_id
    else:
        record = get_shipping_carrier_by_id(db, int(carrier_or_id))
        if record is None:
            raise ValueError(f"ShippingCarrier {carrier_or_id} not found")
    _apply_changes(record, changes or kw)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record


def update_shipment_event(db: Session, event_or_id, changes: Optional[dict] = None, **kw):
    """Update a shipment event (legacy controller form passes an object + dict)."""
    if _is_orm(event_or_id, ShipmentEvent):
        record = event_or_id
    else:
        record = db.get(ShipmentEvent, int(event_or_id))
        if record is None:
            raise ValueError(f"ShipmentEvent {event_or_id} not found")
    _apply_changes(record, changes or kw)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record


def refresh_model(db: Session, obj) -> None:
    """Refresh an ORM instance from the database (flushes pending changes)."""
    db.refresh(obj)

