from __future__ import annotations

"""Admin logistics partner operations — approve/reject/toggle."""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from domains.logistics.models.logistics import LogisticsPartner
import structlog

logger = structlog.get_logger(__name__)


def _get_partner_or_404(db: Session, country_code: str, partner_id: int) -> LogisticsPartner:
    partner = (
        db.query(LogisticsPartner)
        .filter(
            LogisticsPartner.id == partner_id,
            LogisticsPartner.country_code == country_code,
        )
        .first()
    )
    if not partner:
        raise HTTPException(404)
    return partner


def approve_logistics_partner(db: Session, *, country_code: str, partner_id: int) -> dict:
    """Set a logistics partner's verification status to ``approved``."""
    partner = _get_partner_or_404(db, country_code, partner_id)
    partner.verification_status = "approved"
    db.commit()
    return {"message": "Partner approved"}


def reject_logistics_partner(db: Session, *, country_code: str, partner_id: int) -> dict:
    """Set a logistics partner's verification status to ``rejected``."""
    partner = _get_partner_or_404(db, country_code, partner_id)
    partner.verification_status = "rejected"
    db.commit()
    return {"message": "Partner rejected"}


def toggle_logistics_partner_active(db: Session, *, country_code: str, partner_id: int) -> dict:
    """Flip a logistics partner between ``active`` and ``suspended``."""
    partner = _get_partner_or_404(db, country_code, partner_id)
    partner.status = "suspended" if partner.status == "active" else "active"
    db.commit()
    return {"message": f"Partner {'suspended' if partner.status == 'suspended' else 'activated'}"}
