"""ERP finance controller.

Thin delegation layer between ``routers/finance_erp.py`` and
``services/finance/finance_erp_write_service.py``.

Permission enforcement stays in the router as a FastAPI dependency
(``require_finance_permission``); this controller performs no DB writes of its
own and lets ``HTTPException`` from the service propagate (W1 layer contract).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from services.finance.finance_erp_write_service import (
    create_recurring_template,
    update_gl_account,
)
import structlog
logger = structlog.get_logger(__name__)


def update_account(code: str, body, db: Session) -> dict:
    """Apply a partial GL account update."""
    return update_gl_account(db, code, body.model_dump())


def create_recurring(body, created_by, db: Session) -> dict:
    """Create a recurring journal-entry template."""
    tpl = create_recurring_template(
        db,
        name=body.name,
        frequency=body.frequency,
        next_run_date=body.next_run_date,
        description=body.description,
        lines=body.lines,
        currency=body.currency,
        country_code=body.country_code,
        created_by=created_by,
    )
    return {"id": tpl.id}
