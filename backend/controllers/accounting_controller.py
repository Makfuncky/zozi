"""Accounting Controller — wraps general_ledger_service for API consumption."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from controllers.audit_controller import AuditAction, audit_log
from models import User
from db.schemas import (
    JournalEntryCreate,
    JournalLineInput,
)
from services import general_ledger_service as gl


# ── Pydantic request bodies ───────────────────────────────────────────────────

class JournalEntryBody(BaseModel):
    entry_date: datetime
    reference_type: str = Field(..., max_length=40)
    reference_id: int
    reference_number: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., max_length=500)
    currency: str = "OMR"
    country_code: Optional[str] = Field(None, max_length=3)
    lines: List[JournalLineInput]


# ── Controller functions ──────────────────────────────────────────────────────

def seed_chart_of_accounts(db: Session, audit_user_id: Optional[int] = None, audit_username: Optional[str] = None, audit_user_role: Optional[str] = None) -> dict:
    gl.seed_chart_of_accounts(db)
    count = len(gl.list_accounts(db))
    if audit_user_id:
        audit_log(
            db=db,
            action=AuditAction.CHART_OF_ACCOUNTS_SEEDED,
            user_id=audit_user_id,
            username=audit_username,
            user_role=audit_user_role,
            resource_type="chart_of_accounts",
            details={"accounts_created": count},
        )
    return {"status": "ok", "accounts_created": count}


def list_accounts(db: Session) -> list:
    return gl.list_accounts(db)


def get_account(db: Session, code: str):
    acct = gl.get_account_by_code(db, code)
    if not acct:
        raise HTTPException(404, f"Account '{code}' not found")
    return acct


def create_journal_entry(
    db: Session,
    body: JournalEntryBody,
    current_user: User,
) -> dict:
    entry_data = JournalEntryCreate(
        entry_date=body.entry_date,
        reference_type=body.reference_type,
        reference_id=body.reference_id,
        reference_number=body.reference_number,
        description=body.description,
        currency=body.currency,
        country_code=body.country_code,
        lines=body.lines,
    )
    entry = gl.create_journal_entry(db, entry_data, user_id=current_user.id)
    user_id = getattr(current_user, "id", None) or current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
    username = getattr(current_user, "username", None) or current_user.get("username") if isinstance(current_user, dict) else getattr(current_user, "username", None)
    user_role = getattr(current_user, "role", None) or current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    audit_log(
        db=db,
        action=AuditAction.JOURNAL_ENTRY_CREATED,
        user_id=user_id,
        username=username,
        user_role=user_role,
        resource_type="journal_entry",
        resource_id=entry.get("id") if isinstance(entry, dict) else None,
        details={
            "reference_type": body.reference_type,
            "reference_id": body.reference_id,
            "reference_number": body.reference_number,
            "currency": body.currency,
            "line_count": len(body.lines),
        },
    )
    return entry


def get_journal_entry(db: Session, entry_id: int):
    entry = gl.get_journal_entry(db, entry_id)
    if not entry:
        raise HTTPException(404, f"Journal entry #{entry_id} not found")
    return entry


def list_journal_entries(
    db: Session,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> list:
    return gl.list_journal_entries(
        db, reference_type=reference_type, reference_id=reference_id, country_code=country_code, limit=limit
    )


def get_account_balance(db: Session, account_code: str, currency: str = "OMR") -> dict:
    acct = gl.get_account_by_code(db, account_code)
    if not acct:
        raise HTTPException(404, f"Account '{account_code}' not found")
    bal = gl.get_account_balance(db, acct.id, currency=currency)
    if not bal:
        return {"account_code": account_code, "balance": Decimal("0.00"), "currency": currency}
    return bal


def get_trial_balance(
    db: Session,
    as_of_date: Optional[date] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> list:
    return gl.get_trial_balance(db, as_of_date=as_of_date, currency=currency, country_code=country_code)

