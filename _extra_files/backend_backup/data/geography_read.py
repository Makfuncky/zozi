"""Read access for geography / cross-border communication queries.

Kept in the ``data`` layer so routers never execute ``db.query`` directly
(layer-contract LC1). Routers call these helpers and keep presentation/
serialisation logic.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from data.orm_models import (
    CrossCountryCustomerSession,
    LegalContractTemplate,
    LogisticsPartnerLocation,
    ShopWarehouseLocation,
)


def list_cross_border_sessions(
    db: Session, country_code: str, limit: int = 50
) -> List[CrossCountryCustomerSession]:
    return (
        db.query(CrossCountryCustomerSession)
        .filter(CrossCountryCustomerSession.target_country_code == country_code.upper())
        .order_by(CrossCountryCustomerSession.created_at.desc())
        .limit(limit)
        .all()
    )


def list_legal_contracts(
    db: Session, country_code: str, limit: int = 50
) -> List[LegalContractTemplate]:
    return (
        db.query(LegalContractTemplate)
        .filter(
            LegalContractTemplate.country_code == country_code.upper(),
            LegalContractTemplate.is_active == True,
        )
        .order_by(LegalContractTemplate.created_at.desc())
        .all()
    )


def list_warehouses(db: Session, country_code: str) -> List[ShopWarehouseLocation]:
    return (
        db.query(ShopWarehouseLocation)
        .filter(
            ShopWarehouseLocation.country_code == country_code.upper(),
            ShopWarehouseLocation.is_active == True,
        )
        .all()
    )


def list_partner_locations(db: Session, country_code: str) -> List[LogisticsPartnerLocation]:
    return (
        db.query(LogisticsPartnerLocation)
        .join(db.Model("LogisticsPartner"))
        .filter(
            LogisticsPartnerLocation.country_code == country_code.upper(),
            LogisticsPartnerLocation.is_active == True,
        )
        .all()
    )
