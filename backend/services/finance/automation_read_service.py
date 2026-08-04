"""Service methods for finance automation rules read operations."""
from __future__ import annotations
from typing import Optional

from sqlalchemy.orm import Session

from data.models import (
    Accrual,
    AutomationLog,
    AutomationRule,
    BankMappingRule,
    FixedAsset,
    ScannedExpense,
)


def get_automation_rules(db: Session, skip: int = 0, limit: int = 20) -> list[AutomationRule]:
    """Get all automation rules."""
    return (
        db.query(AutomationRule)
        .filter(AutomationRule.is_active == True)
        .order_by(AutomationRule.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_automation_rule_by_id(db: Session, rule_id: int) -> AutomationRule | None:
    """Get an automation rule by ID."""
    return db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()


def execute_automation_rule(db: Session, rule_id: int) -> dict:
    """Execute an automation rule and return results."""
    # This would contain the actual rule execution logic
    return {"status": "executed", "rule_id": rule_id}


def get_automation_logs(db: Session, rule_id: int, skip: int = 0, limit: int = 50) -> list[AutomationLog]:
    """Get logs for an automation rule."""
    return (
        db.query(AutomationLog)
        .filter(AutomationLog.rule_id == rule_id)
        .order_by(AutomationLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_automation_metrics(db: Session) -> dict:
    """Get automation system metrics."""
    from sqlalchemy import func as sqlfunc
    total_rules = db.query(sqlfunc.count(AutomationRule.id)).scalar() or 0
    active_rules = (
        db.query(sqlfunc.count(AutomationRule.id))
        .filter(AutomationRule.is_active == True)
        .scalar()
        or 0
    )
    total_logs = db.query(sqlfunc.count(AutomationLog.id)).scalar() or 0
    return {
        "total_rules": total_rules,
        "active_rules": active_rules,
        "total_logs": total_logs,
    }


# ── Finance-automation entity reads (LC1: routers stay thin) ────────────────


def list_bank_mapping_rules(
    db: Session,
    country_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[BankMappingRule]:
    """List bank-mapping rules, optional country filter, priority ascending."""
    q = db.query(BankMappingRule)
    if country_code:
        q = q.filter(
            (BankMappingRule.country_code == country_code)
            | (BankMappingRule.country_code.is_(None))
        )
    return q.order_by(BankMappingRule.priority.asc()).offset(skip).limit(limit).all()


def list_scanned_expenses(
    db: Session,
    country_code: Optional[str] = None,
    limit: int = 200,
) -> list[ScannedExpense]:
    """List scanned expenses (newest first, optional country filter)."""
    q = db.query(ScannedExpense)
    if country_code:
        q = q.filter(ScannedExpense.country_code == country_code)
    return q.order_by(ScannedExpense.id.desc()).limit(limit).all()


def list_fixed_assets(
    db: Session,
    country_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[FixedAsset]:
    """List fixed assets (newest first, optional country filter)."""
    q = db.query(FixedAsset)
    if country_code:
        q = q.filter(
            (FixedAsset.country_code == country_code) | (FixedAsset.country_code.is_(None))
        )
    return q.order_by(FixedAsset.id.desc()).offset(skip).limit(limit).all()


def list_accruals(
    db: Session,
    country_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Accrual]:
    """List accruals (newest first, optional country filter)."""
    q = db.query(Accrual)
    if country_code:
        q = q.filter(
            (Accrual.country_code == country_code) | (Accrual.country_code.is_(None))
        )
    return q.order_by(Accrual.id.desc()).offset(skip).limit(limit).all()
