"""Admin logistics service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.logistics.models.logistics import LogisticsPartner

from domains.country.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import clear_rls_context, set_rls_context
from infrastructure.utils.pagination import keyset_paginate


def list_partners(country_code: str, include_deleted: bool, page: int, page_size: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(LogisticsPartner).filter(LogisticsPartner.country_code == country_code.upper())
        if not include_deleted:
            q = q.filter(LogisticsPartner.is_deleted == False)
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


def list_partners_paginated(country_code: str, include_deleted: bool, limit: int, cursor: str | None, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        query = db.query(LogisticsPartner).filter(LogisticsPartner.country_code == country_code.upper())
        if not include_deleted:
            query = query.filter(LogisticsPartner.is_deleted.is_(False))
        return keyset_paginate(query, sort_keys=[(LogisticsPartner.id, "asc")], cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


def approve_partner(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.verification_status = "approved"
        db.commit()
        return {"message": "Partner approved"}
    finally:
        clear_rls_context()


def reject_partner(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.verification_status = "rejected"
        db.commit()
        return {"message": "Partner rejected"}
    finally:
        clear_rls_context()


def toggle_partner_active(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.status = "suspended" if p.status == "active" else "active"
        db.commit()
        return {"message": f"Partner {'suspended' if p.status == 'suspended' else 'activated'}"}
    finally:
        clear_rls_context()


def archive_partner(country_code: str, partner_id: int, db: Session, reason: str | None = None) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.is_deleted = True
        p.status = "archived"
        db.commit()
        return {"message": "Partner archived"}
    finally:
        clear_rls_context()


def restore_partner(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        p.is_deleted = False
        p.status = "active"
        db.commit()
        return {"message": "Partner restored"}
    finally:
        clear_rls_context()


def hard_delete_partner(country_code: str, partner_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p:
            raise ValueError("Partner not found")
        db.delete(p)
        db.commit()
        return {"message": "Partner permanently deleted"}
    finally:
        clear_rls_context()

