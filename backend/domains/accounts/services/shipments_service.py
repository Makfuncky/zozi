"""Auto-migrated service logic from routers/shipments.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import (
    ShipmentCreate,
    ShipmentEventCreate,
    ShipmentEventOut,
    ShipmentOut,
    ShipmentUpdate,
)

from domains.accounts.models.user import User
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent

from infrastructure.utils.dependencies import get_current_user, require_admin, require_logistics

def get_shipment(shipment_id: int, db: Session):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    return s

def track_shipment(tracking_number: str, db: Session):
    s = db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
    if not s: raise HTTPException(404, "Tracking number not found")
    return s

def create_shipment(payload: ShipmentCreate, _: User, db: Session):
    s = Shipment(**payload.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s

def update_shipment(shipment_id: int, payload: ShipmentUpdate, _: User, db: Session):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

def add_event(shipment_id: int, payload: ShipmentEventCreate, current_user: User, db: Session):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    event = ShipmentEvent(shipment_id=shipment_id, created_by=current_user.id, **payload.model_dump())
    db.add(event); db.commit(); db.refresh(event)
    return event


