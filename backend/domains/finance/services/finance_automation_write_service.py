"""Finance-automation admin writes (chart of accounts + fixed assets).

Owns every DB mutation that used to live in ``routers/finance_automation.py``
so routers and controllers stay write-free (W1). Each function takes the
injected ``db`` session first, performs its own ``add``/``flush``/``commit``
and raises the same ``HTTPException`` values the router used to raise.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import AccountGroup
from domains.finance.models.finance import FixedAsset
from domains.finance.services.finance import general_ledger_service as gl
import structlog
logger = structlog.get_logger(__name__)


def _as_dict(body: Any) -> dict:
    """Accept either a pydantic model or a plain mapping."""
    if hasattr(body, "model_dump"):
        return body.model_dump(exclude_none=True)
    return dict(body or {})


def create_gl_account(db: Session, body: Any) -> Any:
    """Create a GL account plus its zero-balance row, then return the new COA.

    Mirrors the previous router behaviour: 409 when the code already exists,
    404 when the parent account group is unknown.
    """
    if db.query(Account).filter(Account.code == body.code).first():
        raise HTTPException(409, f"Account '{body.code}' already exists")
    grp = db.query(AccountGroup).filter(AccountGroup.code == body.group_code).first()
    if not grp:
        raise HTTPException(404, f"Account group '{body.group_code}' not found")
    acct = Account(
        code=body.code,
        name=body.name,
        group_id=grp.id,
        normal_side=body.normal_side,
        currency=body.currency,
        country_code=body.country_code,
    )
    db.add(acct)
    db.flush()
    db.add(AccountBalance(account_id=acct.id, currency=body.currency, balance=Decimal("0.00")))
    db.commit()
    db.refresh(acct)
    return gl.list_accounts(db)


def deactivate_gl_account(db: Session, code: str) -> dict:
    """Soft-disable a GL account by code (404 when missing)."""
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        raise HTTPException(404, f"Account '{code}' not found")
    acct.is_active = False
    db.commit()
    return {"status": "deactivated", "code": code}


def create_fixed_asset(db: Session, body: Any, created_by: Optional[int] = None) -> dict:
    """Register a fixed asset and return its identity/status summary."""
    asset = FixedAsset(**_as_dict(body), created_by=created_by)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"id": asset.id, "name": asset.name, "status": asset.status}
