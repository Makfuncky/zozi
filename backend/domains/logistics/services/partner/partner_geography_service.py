"""Country-scoped logistics partner read/write operations.

Owns the DB reads/writes for the inline partner endpoints in
``admin_logistics_geography`` so the router stays free of ``db.query``/``db.commit``.
Archive/restore/hard-delete are delegated to the admin controller.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.logistics.models.logistics import LogisticsPartner
from infrastructure.utils.pagination import keyset_paginated_response
import structlog
logger = structlog.get_logger(__name__)


def list_partners(db: Session, country_code: str, include_deleted: bool, cursor: str | None, page_size: int) -> dict:
    """Return a keyset (cursor) page of logistics partners for a country (diagram §6: never OFFSET)."""
    q = db.query(LogisticsPartner).filter(LogisticsPartner.country_code == country_code.upper())
    if not include_deleted:
        q = q.filter(LogisticsPartner.is_deleted == False)  # noqa: E712
    total = q.count()
    return keyset_paginated_response(
        q, sort_keys=[(LogisticsPartner.id, "asc")], cursor=cursor, page_size=page_size, total=total,
    )


def _get_partner(db: Session, partner_id: int, country_code: str) -> LogisticsPartner:
    p = (
        db.query(LogisticsPartner)
        .filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper())
        .first()
    )
    if not p:
        raise HTTPException(404)
    return p


def approve_partner(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.verification_status = "approved"
    db.commit()
    return {"message": "Partner approved"}


def reject_partner(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.verification_status = "rejected"
    db.commit()
    return {"message": "Partner rejected"}


def toggle_partner_active(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.status = "suspended" if p.status == "active" else "active"
    db.commit()
    return {"message": f"Partner {'suspended' if p.status == 'suspended' else 'activated'}"}
