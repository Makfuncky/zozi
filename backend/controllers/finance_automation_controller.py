"""Thin controller for finance-automation admin writes.

Keeps the country/RLS scoping that used to live in the router (a read plus a
context-var toggle) and delegates every mutation to
``services.finance.finance_automation_write_service``. No DB writes happen
here; ``HTTPException`` raised by the service propagates untouched.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from services.finance.finance_automation_write_service import (
    create_fixed_asset as _create_fixed_asset,
    create_gl_account as _create_gl_account,
    deactivate_gl_account as _deactivate_gl_account,
)
from utils.country_access import get_country_or_404
from utils.rls_interceptor import clear_rls_context, set_rls_context
import structlog
logger = structlog.get_logger(__name__)


def _with_rls(country_code: Optional[str], db: Session):
    """Validate + scope the request to a country; returns a cleanup callable."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)

    def cleanup():
        if country_code:
            clear_rls_context()
    return cleanup


def _actor_id(current_user: Any) -> Optional[int]:
    if isinstance(current_user, dict):
        return current_user.get("id")
    return getattr(current_user, "id", None)


# ── Chart of accounts ────────────────────────────────────────────────────────

def create_account(body: Any, current_user: Any, db: Session) -> Any:
    cleanup = _with_rls(getattr(body, "country_code", None), db)
    try:
        return _create_gl_account(db, body)
    finally:
        cleanup()


def deactivate_account(code: str, current_user: Any, db: Session) -> dict:
    return _deactivate_gl_account(db, code)


# ── Fixed assets ─────────────────────────────────────────────────────────────

def create_asset(body: Any, current_user: Any, db: Session) -> dict:
    return _create_fixed_asset(db, body, created_by=_actor_id(current_user))
