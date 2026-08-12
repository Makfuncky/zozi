from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from db.database import get_db
from models import CountryConfig
from utils.websocket_manager import manager
from utils.dependencies import get_current_user
from models.country_control import LogisticsPartnerLocation

async def list_cross_border_sessions(country_code: str, db: Session=Depends(get_db)):
    from models import CrossCountryCustomerSession
    sessions = db.query(CrossCountryCustomerSession).filter(CrossCountryCustomerSession.target_country_code == country_code.upper()).order_by(CrossCountryCustomerSession.created_at.desc()).limit(50).all()
    return [{'id': s.id, 'user_id': s.user_id, 'source_country_code': s.source_country_code, 'target_country_code': s.target_country_code, 'conversion': s.conversion, 'order_id': s.order_id, 'created_at': s.created_at.isoformat() if s.created_at else None} for s in sessions]

async def list_legal_contracts(country_code: str, db: Session=Depends(get_db)):
    from models.country_control import LegalContractTemplate
    contracts = db.query(LegalContractTemplate).filter(LegalContractTemplate.country_code == country_code.upper(), LegalContractTemplate.is_active == True).order_by(LegalContractTemplate.created_at.desc()).all()
    return [{'id': c.id, 'country_code': c.country_code, 'template_type': c.template_type, 'version': c.version, 'content': c.content, 'is_active': c.is_active, 'created_at': c.created_at.isoformat() if c.created_at else None} for c in contracts]

async def list_warehouses(country_code: str, db: Session=Depends(get_db)):
    from models.country_control import ShopWarehouseLocation
    warehouses = db.query(ShopWarehouseLocation).filter(ShopWarehouseLocation.country_code == country_code.upper(), ShopWarehouseLocation.is_active == True).all()
    return [{'id': w.id, 'country_code': w.country_code, 'name': w.name, 'warehouse_code': w.warehouse_code, 'latitude': float(w.latitude) if w.latitude else None, 'longitude': float(w.longitude) if w.longitude else None, 'address': w.address, 'is_active': w.is_active, 'created_at': w.created_at.isoformat() if w.created_at else None} for w in warehouses]

async def list_partner_locations(country_code: str, db: Session=Depends(get_db)):
    locations = db.query(LogisticsPartnerLocation).join(db.Model('LogisticsPartner')).filter(LogisticsPartnerLocation.country_code == country_code.upper(), LogisticsPartnerLocation.is_active == True).all()
    return [{'id': p.id, 'partner_id': p.partner_id, 'partner': {'name': p.partner.name} if p.partner else None, 'country_code': p.country_code, 'location_type': p.location_type, 'latitude': float(p.latitude) if p.latitude else None, 'longitude': float(p.longitude) if p.longitude else None, 'address': p.address, 'is_active': p.is_active, 'created_at': p.created_at.isoformat() if p.created_at else None} for p in locations]
