from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from db.database import get_db
from models import CountryConfig
from utils.websocket_manager import manager
from utils.auth import get_current_user
from schemas.country import CountryCrossBorderSession, CountryLegalContract, CountryWarehouseLocation, LogisticsPartnerLocation

router = APIRouter()


@router.get("/admin/countries/{country_code}/cross-border-sessions")
async def list_cross_border_sessions(country_code: str, db: Session = Depends(get_db)):
    from models import CrossCountryCustomerSession
    sessions = db.query(CrossCountryCustomerSession).filter(
        CrossCountryCustomerSession.target_country_code == country_code.upper()
    ).order_by(CrossCountryCustomerSession.created_at.desc()).limit(50).all()
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


@router.get("/admin/countries/{country_code}/legal-contracts")
async def list_legal_contracts(country_code: str, db: Session = Depends(get_db)):
    from db.models_country_control import LegalContractTemplate
    contracts = db.query(LegalContractTemplate).filter(
        LegalContractTemplate.country_code == country_code.upper(),
        LegalContractTemplate.is_active == True
    ).order_by(LegalContractTemplate.created_at.desc()).all()
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


@router.get("/admin/countries/{country_code}/warehouses")
async def list_warehouses(country_code: str, db: Session = Depends(get_db)):
    from db.models_country_control import ShopWarehouseLocation
    warehouses = db.query(ShopWarehouseLocation).filter(
        ShopWarehouseLocation.country_code == country_code.upper(),
        ShopWarehouseLocation.is_active == True
    ).all()
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


@router.get("/admin/countries/{country_code}/partner-locations")
async def list_partner_locations(country_code: str, db: Session = Depends(get_db)):
    from db.models_country_control import LogisticsPartnerLocation
    locations = db.query(LogisticsPartnerLocation).join(
        db.Model("LogisticsPartner")
    ).filter(
        LogisticsPartnerLocation.country_code == country_code.upper(),
        LogisticsPartnerLocation.is_active == True
    ).all()
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


@router.websocket("/ws/country/{country_code}/communications")
async def websocket_country_communications(
    websocket: WebSocket,
    country_code: str,
    current_user: dict = Depends(get_current_user)
):
    await websocket.accept()
    room = f"country:{country_code.upper()}"
    user_id = current_user.get("id")
    
    await manager.connect(websocket, room, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "message":
                await manager.broadcast_to_room(room, {
                    "event": "new_message",
                    "data": message.get("data"),
                    "timestamp": message.get("timestamp")
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


@router.websocket("/ws/country/{country_code}/notifications")
async def websocket_country_notifications(
    websocket: WebSocket,
    country_code: str,
    current_user: dict = Depends(get_current_user)
):
    await websocket.accept()
    room = f"country:{country_code.upper()}"
    
    await manager.connect(websocket, room)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
