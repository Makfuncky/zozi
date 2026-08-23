"""Country communications read service.

Owns the read queries behind the country-scoped list endpoints in
``routers.country_communications`` so the router performs no direct ``db.query``.
All functions translate the ORM rows into the exact JSON shapes the former inline
handlers returned.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from domains.country.models.country_enhancements import CrossCountryCustomerSession
from domains.country.models.country_control import LegalContractTemplate
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.country.models.country_control import ShopWarehouseLocation


def list_cross_border_sessions(db: Session, country_code: str) -> list[dict[str, Any]]:
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


def list_legal_contracts(db: Session, country_code: str) -> list[dict[str, Any]]:
    contracts = (
        db.query(LegalContractTemplate)
        .filter(
            LegalContractTemplate.country_code == country_code.upper(),
            LegalContractTemplate.is_active == True,
        )
        .order_by(LegalContractTemplate.created_at.desc())
        .all()
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


def list_warehouses(db: Session, country_code: str) -> list[dict[str, Any]]:
    warehouses = (
        db.query(ShopWarehouseLocation)
        .filter(
            ShopWarehouseLocation.country_code == country_code.upper(),
            ShopWarehouseLocation.is_active == True,
        )
        .all()
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


def list_partner_locations(db: Session, country_code: str) -> list[dict[str, Any]]:
    locations = (
        db.query(LogisticsPartnerLocation)
        .join(db.Model("LogisticsPartner"))
        .filter(
            LogisticsPartnerLocation.country_code == country_code.upper(),
            LogisticsPartnerLocation.is_active == True,
        )
        .all()
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
