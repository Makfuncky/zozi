"""Supplier logistics router — supplier-facing shipment and carrier operations.

Per ARCHITECTURE_DIAGRAM.md §3, this is a thin per-actor router:
auth context + require_feature(...) + one service call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_supplier
from rbac.dependencies import require_feature

router = APIRouter(prefix="/supplier/logistics", tags=["supplier", "logistics"])


# === Pydantic Schemas ===

class CreateCarrierRequest(BaseModel):
    name: str
    code: str
    tracking_url: Optional[str] = None
    notes: Optional[str] = None


class ShippingZoneRequest(BaseModel):
    name: str
    countries: list[str] = Field(default_factory=list)
    base_price: float = 0.0
    price_per_kg: float = 0.0
    free_shipping_above: Optional[float] = None
    estimated_days_min: Optional[int] = None
    estimated_days_max: Optional[int] = None
    carrier_id: Optional[int] = None
    carrier_name: Optional[str] = None
    is_active: bool = True


class ShippingZoneUpdateRequest(BaseModel):
    name: Optional[str] = None
    countries: Optional[list[str]] = None
    base_price: Optional[float] = None
    price_per_kg: Optional[float] = None
    free_shipping_above: Optional[float] = None
    estimated_days_min: Optional[int] = None
    estimated_days_max: Optional[int] = None
    carrier_id: Optional[int] = None
    carrier_name: Optional[str] = None
    is_active: Optional[bool] = None


# === Carriers ===

@router.get("/carriers")
async def list_carriers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.core.carrier_service import get_carriers
    return await get_carriers(current_user, db)


@router.post("/carriers")
async def create_carrier(
    data: CreateCarrierRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    from domains.logistics.services.core.carrier_service import create_carrier
    return await create_carrier(data.model_dump(), current_user, db)


@router.delete("/carriers/{carrier_id}")
async def delete_carrier(
    carrier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    from domains.logistics.services.core.carrier_service import delete_carrier
    return await delete_carrier(carrier_id, current_user, db)


# === Shipping Zones ===

@router.get("/zones")
async def list_zones(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.core.zone_service import get_shipping_zones
    return await get_shipping_zones(current_user, db)


@router.post("/zones")
async def create_zone(
    data: ShippingZoneRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    from domains.logistics.services.core.zone_service import upsert_shipping_zone
    return await upsert_shipping_zone(data.model_dump(), current_user, db)


@router.put("/zones/{zone_id}")
async def update_zone(
    zone_id: int,
    data: ShippingZoneUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    from domains.logistics.services.core.zone_service import upsert_shipping_zone
    payload = data.model_dump(exclude_unset=True)
    payload["id"] = zone_id
    return await upsert_shipping_zone(payload, current_user, db)


@router.delete("/zones/{zone_id}")
async def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    from domains.logistics.services.core.zone_service import delete_shipping_zone
    return await delete_shipping_zone(zone_id, current_user, db)


# === Shipments ===

@router.get("/shipments")
async def list_shipments(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.core.shipment_service import get_active_shipments
    return await get_active_shipments(current_user, db)


@router.get("/shipments/{shipment_id}/events")
async def get_shipment_events(
    shipment_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supplier),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.core.shipment_service import get_shipment_events
    return await get_shipment_events(shipment_id, current_user, db)
