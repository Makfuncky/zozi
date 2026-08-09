"""Admin payouts controller.

Thin delegation layer between ``routers/admin_payouts.py`` and
``services/finance/payout_admin_write_service.py``.

Country resolution and RLS scoping (reads) stay here; every DB mutation is
delegated to the write service so neither the router nor this controller
performs Layer-1 writes (W1 layer contract). ``HTTPException`` propagates.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from services.finance.payout_admin_write_service import (
    create_country_payout,
    process_country_payout,
    verify_country_payout,
)
from utils.country_access import get_country_or_404
from utils.rls_interceptor import clear_rls_context, set_rls_context
import structlog
logger = structlog.get_logger(__name__)


def create_payout(country_code: str, payload, current_admin, db: Session):
    """Create a country-scoped payout."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        return create_country_payout(
            db,
            country_code=code,
            payload=payload,
            admin_id=current_admin.id,
            admin_username=current_admin.username,
        )
    finally:
        clear_rls_context()


def verify_payout(country_code: str, payout_id: int, payload, current_admin, db: Session) -> dict:
    """Verify a country-scoped payout."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        return verify_country_payout(
            db,
            country_code=code,
            payout_id=payout_id,
            payload=payload,
            admin_id=current_admin.id,
            admin_username=current_admin.username,
        )
    finally:
        clear_rls_context()


def process_payout(country_code: str, payout_id: int, current_admin, db: Session) -> dict:
    """Mark a country-scoped payout as paid."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        return process_country_payout(
            db,
            country_code=code,
            payout_id=payout_id,
            admin_id=current_admin.id,
            admin_username=current_admin.username,
        )
    finally:
        clear_rls_context()
