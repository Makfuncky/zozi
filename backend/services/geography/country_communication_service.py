"""Service methods for country communication data access."""
from __future__ import annotations
from utils.pagination import SAFE_QUERY_LIMIT
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from data.models import (
    CountryCommunication,
    CrossCountryCustomerSession,
    LegalContractTemplate,
    ShopWarehouseLocation,
    LogisticsPartnerLocation,
    LogisticsPartner,
)
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