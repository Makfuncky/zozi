"""ERP finance write service.

Owns the DB mutations behind the ERP finance router endpoints that write
directly (GL account edit, recurring template creation) so the router and
controller layers stay write-free (W1 layer contract).

Each function takes ``db: Session`` first, mutates, commits, and raises
``HTTPException`` exactly as the original router code did.

Endpoints that already delegate to ``data.services.finance.erp_finance_service`` /
``data.services.finance.finance_automation`` are intentionally not duplicated here.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import Account, AccountGroup, RecurringTemplate
import structlog
logger = structlog.get_logger(__name__)


def update_gl_account(db: Session, code: str, payload: dict) -> dict:
    """Apply a partial update to a GL account identified by ``code``."""
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        raise HTTPException(404, f"Account '{code}' not found")

    name = payload.get("name")
    if name is not None:
        acct.name = name

    normal_side = payload.get("normal_side")
    if normal_side is not None:
        acct.normal_side = normal_side

    currency = payload.get("currency")
    if currency is not None:
        acct.currency = currency

    group_code = payload.get("group_code")
    if group_code is not None:
        grp = db.query(AccountGroup).filter(AccountGroup.code == group_code).first()
        if not grp:
            raise HTTPException(404, f"Group '{group_code}' not found")
        acct.group_id = grp.id

    db.commit()
    return {"status": "updated", "code": code}


def create_recurring_template(
    db: Session,
    *,
    name: str,
    frequency: str,
    next_run_date: Optional[datetime],
    description: str,
    lines: list[dict],
    currency: str,
    country_code: Optional[str],
    created_by: Any,
) -> RecurringTemplate:
    """Persist a new recurring journal-entry template."""
    tpl = RecurringTemplate(name=name, frequency=frequency, next_run_date=next_run_date,
                            description=description, lines=lines, currency=currency,
                            country_code=country_code, created_by=created_by)
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl
