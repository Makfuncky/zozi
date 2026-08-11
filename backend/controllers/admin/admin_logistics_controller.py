"""Admin logistics controller.

Thin delegation layer between ``routers/admin_logistics.py`` and
``services/logistics/logistics_partner_admin_write_service.py``.

Country resolution and RLS scoping (reads) stay here; every DB mutation is
delegated to the write service so neither the router nor this controller
performs Layer-1 writes (W1 layer contract). ``HTTPException`` propagates.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from services.logistics.logistics_partner_admin_write_service import (
    approve_logistics_partner,
    reject_logistics_partner,
    toggle_logistics_partner_active,
)
from utils.country_access import get_country_or_404
from utils.rls_interceptor import clear_rls_context, set_rls_context
import structlog
logger = structlog.get_logger(__name__)


def approve_partner(country_code: str, partner_id: int, db: Session) -> dict:
    """Approve a country-scoped logistics partner."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        return approve_logistics_partner(db, country_code=code, partner_id=partner_id)
    finally:
        clear_rls_context()


def reject_partner(country_code: str, partner_id: int, db: Session) -> dict:
    """Reject a country-scoped logistics partner."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        return reject_logistics_partner(db, country_code=code, partner_id=partner_id)
    finally:
        clear_rls_context()


def toggle_partner_active(country_code: str, partner_id: int, db: Session) -> dict:
    """Toggle a country-scoped logistics partner between active and suspended."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        return toggle_logistics_partner_active(db, country_code=code, partner_id=partner_id)
    finally:
        clear_rls_context()
