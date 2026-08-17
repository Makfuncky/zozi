"""
Logistics Router — shipping carriers, zones, and shipment fulfilment.
All business logic lives in controllers/logistics_controller.py.
"""
from typing import Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from routers.core_auth_routes import get_current_user
import controllers.orders.logistics_controller as ctrl

async def scan_lookup_shipment(code: str, db: Session=Depends(get_db), current_user: dict=Depends(get_current_user)):
    """Look up a shipment by tracking number or scan code. Admin only."""
    if str(current_user.get('role') or '').lower() not in ('admin', 'sub_admin', 'moderator', 'support'):
        raise HTTPException(status_code=403, detail='Admin access required')
    from models import Shipment
    shipment = db.query(Shipment).filter((Shipment.tracking_number == code) | (Shipment.id == (int(code) if code.isdigit() else -1))).first()
    if not shipment:
        raise HTTPException(status_code=404, detail='Shipment not found')
    return {'id': shipment.id, 'order_id': shipment.order_id, 'status': shipment.status, 'carrier_name': shipment.carrier_name, 'tracking_number': shipment.tracking_number, 'distribution_channel': shipment.distribution_channel, 'current_hub': shipment.current_hub, 'shipping_address': shipment.order.shipping_address if shipment.order else None, 'created_at': shipment.created_at.isoformat() if shipment.created_at else None, 'updated_at': shipment.updated_at.isoformat() if shipment.updated_at else None}

async def admin_update_shipment_status(shipment_id: int, data: dict[str, Any], db: Session=Depends(get_db), current_user: dict=Depends(get_current_user)):
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    if str(current_user.get('role') or '').lower() not in ('admin', 'sub_admin', 'moderator', 'support'):
        raise HTTPException(status_code=403, detail='Admin access required')
    from models import Shipment, ShipmentEvent
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
