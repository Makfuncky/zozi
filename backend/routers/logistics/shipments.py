"""Shipments router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import Shipment, ShipmentEvent, User
from db.schemas import ShipmentCreate, ShipmentOut, ShipmentUpdate, ShipmentEventCreate, ShipmentEventOut
from utils.dependencies import get_current_user, require_admin, require_logistics

from services.write_helpers import add_and_flush, commit_only, refresh_only
router = APIRouter()

@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    return s

@router.get("/track/{tracking_number}", response_model=ShipmentOut)
def track_shipment(tracking_number: str, db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
    if not s: raise HTTPException(404, "Tracking number not found")
    return s

@router.post("", response_model=ShipmentOut, status_code=201)
def create_shipment(payload: ShipmentCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = Shipment(**payload.model_dump())
    add_and_flush(db, s); commit_only(db); refresh_only(db, s)
    return s

@router.put("/{shipment_id}", response_model=ShipmentOut)
def update_shipment(shipment_id: int, payload: ShipmentUpdate, _: User = Depends(require_logistics), db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    commit_only(db); refresh_only(db, s)
    return s

@router.post("/{shipment_id}/events", response_model=ShipmentEventOut, status_code=201)
def add_event(shipment_id: int, payload: ShipmentEventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    event = ShipmentEvent(shipment_id=shipment_id, created_by=current_user.id, **payload.model_dump())
    add_and_flush(db, event); commit_only(db); refresh_only(db, event)
    return event

