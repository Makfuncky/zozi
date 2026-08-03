"""Shipments router."""
from fastapi import APIRouter, Depends

from data.dependencies_auth import get_current_user
from data.services_logistics_shipments_service import (
    get_shipment,
    track_shipment,
    create_shipment,
    update_shipment,
    add_event,
)
from data.schemas import ShipmentCreate, ShipmentOut, ShipmentUpdate, ShipmentEventCreate, ShipmentEventOut
from utils.dependencies import require_admin, require_logistics

router = APIRouter()


@router.get("/{shipment_id}", response_model=ShipmentOut)
def read_shipment(shipment_id: int, _=Depends(require_admin)):
    return get_shipment(shipment_id)


@router.get("/track/{tracking_number}", response_model=ShipmentOut)
def track(tracking_number: str):
    return track_shipment(tracking_number)


@router.post("", response_model=ShipmentOut, status_code=201)
def make_shipment(payload: ShipmentCreate, _=Depends(require_admin)):
    return create_shipment(payload)


@router.put("/{shipment_id}", response_model=ShipmentOut)
def edit_shipment(shipment_id: int, payload: ShipmentUpdate, _=Depends(require_logistics)):
    return update_shipment(shipment_id, payload)


@router.post("/{shipment_id}/events", response_model=ShipmentEventOut, status_code=201)
def new_event(shipment_id: int, payload: ShipmentEventCreate, current_user=Depends(get_current_user)):
    return add_event(shipment_id, payload, current_user.id)
