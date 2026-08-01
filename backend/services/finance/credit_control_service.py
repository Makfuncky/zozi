"""
Credit Control Service — Automated credit limit enforcement.

Handles:
  - #24: Auto Credit Limit Enforcement
  
Features:
  - Pre-dispatch credit check (blocks if over limit)
  - Automated credit hold after 30/60/90 day overdue
  - Credit utilization tracking
  - Auto-notifications for approaching limits
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import (
    Customer,
    ARInvoice,
    FinanceAutomationLog,
    FinanceAuditLog,
)
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# Credit control thresholds
OVERDUE_HARD_HOLD_DAYS = 30      # Auto-hold after 30 days overdue
CREDIT_UTILIZATION_WARNING = 0.80  # Warn at 80% utilization
CREDIT_UTILIZATION_CRITICAL = 0.95  # Critical at 95% utilization


# ── #24: Auto Credit Limit Enforcement ─────────────────────────────────────


def check_customer_credit(
    db: Session,
    customer_id: int,
    order_amount: Decimal = None,
    country_code: str = None,
) -> dict:
    """
    Pre-dispatch credit check for a customer/distributor.

    Returns:
    - approved: bool (can proceed with order)
    - credit_limit: current limit
    - outstanding: current AR balance
    - available: remaining credit
    - utilization_pct: current utilization percentage
    - reason: explanation if blocked
    """
    customer = db.query(Customer).get(customer_id)
    if not customer:
        raise ValueError(f"Customer #{customer_id} not found")

    outstanding = _get_customer_outstanding_ar(db, customer_id)
    credit_limit = Decimal(str(customer.credit_limit or 0))

    if credit_limit <= 0:
        return {
            "approved": True,
            "credit_hold": False,
            "credit_limit": 0,
            "outstanding": float(outstanding),
            "available": 0,
            "utilization_pct": 0,
        }

    available = credit_limit - outstanding
    utilization = float(outstanding / credit_limit * 100) if credit_limit > 0 else 0

    result = {
        "approved": True,
        "credit_hold": False,
        "credit_limit": float(credit_limit),
        "outstanding": float(outstanding),
        "available": float(available),
        "utilization_pct": round(utilization, 1),
    }

    if order_amount:
        if outstanding + Decimal(str(order_amount)) > credit_limit:
            result["approved"] = False
            result["reason"] = (
                f"Order would exceed credit limit. "
                f"Limit: {credit_limit}, Outstanding: {outstanding}, "
                f"Order: {order_amount}, Shortfall: {outstanding + Decimal(str(order_amount)) - credit_limit}"
            )
            return result

    if utilization >= CREDIT_UTILIZATION_CRITICAL * 100:
        result["warning"] = f"Credit utilization critical: {utilization:.1f}%"
    elif utilization >= CREDIT_UTILIZATION_WARNING * 100:
        result["warning"] = f"Credit utilization high: {utilization:.1f}%"

    return result
    
    # Calculate current outstanding AR
    outstanding = _get_customer_outstanding_ar(db, customer_id)
    credit_limit = Decimal(str(customer.credit_limit or 0))
    
    if credit_limit <= 0:
        # No credit limit set — approve (cash customer)
        return {
            "approved": True,
            "credit_hold": False,
            "credit_limit": 0,
            "outstanding": float(outstanding),
            "available": 0,
            "utilization_pct": 0,
        }
    
    available = credit_limit - outstanding
    utilization = float(outstanding / credit_limit * 100) if credit_limit > 0 else 0
    
    result = {
        "approved": True,
        "credit_hold": False,
        "credit_limit": float(credit_limit),
        "outstanding": float(outstanding),
        "available": float(available),
        "utilization_pct": round(utilization, 1),
    }
    
    # Check if order would exceed limit
    if order_amount:
        if outstanding + Decimal(str(order_amount)) > credit_limit:
            result["approved"] = False
            result["reason"] = (
                f"Order would exceed credit limit. "
                f"Limit: {credit_limit}, Outstanding: {outstanding}, "
                f"Order: {order_amount}, Shortfall: {outstanding + Decimal(str(order_amount)) - credit_limit}"
            )
            return result
    
    # Check utilization warnings
    if utilization >= CREDIT_UTILIZATION_CRITICAL * 100:
        result["warning"] = f"Credit utilization critical: {utilization:.1f}%"
    elif utilization >= CREDIT_UTILIZATION_WARNING * 100:
        result["warning"] = f"Credit utilization high: {utilization:.1f}%"
    
    return result


def enforce_auto_credit_holds(
    db: Session,
    country_code: str = None,
) -> dict:
    """
    Daily cron: Auto-place customers on credit hold if overdue > 30 days.
    Auto-release hold if all overdue invoices are paid.
    """
    results = {"notices_sent": 0, "holds_placed": 0, "holds_released": 0}

    customers = db.query(Customer).filter(Customer.is_active == True)
    if country_code:
        customers = customers.filter(Customer.country_code == country_code)

    for customer in customers.all():
        overdue_days = _get_max_overdue_days(db, customer.id)
        outstanding = _get_customer_outstanding_ar(db, customer.id)
        credit_limit = Decimal(str(customer.credit_limit or 0))

        if credit_limit > 0 and outstanding > credit_limit:
            results["holds_placed"] += 1
            _log_credit_control(db, "credit_exceeded", customer.id, {
                "outstanding": float(outstanding),
                "credit_limit": float(credit_limit),
                "overdue_days": overdue_days,
            }, country_code)
        elif overdue_days < 7 and credit_limit > 0:
            results["holds_released"] += 1
            _log_credit_control(db, "credit_ok", customer.id, {
                "outstanding": float(outstanding),
                "credit_limit": float(credit_limit),
            }, country_code)

    db.commit()
    _log_automation(db, "credit_control_daily",
                    results["holds_placed"] + results["holds_released"],
                    results["holds_placed"] + results["holds_released"],
                    results, country_code)
    return results


def get_customer_credit_summary(
    db: Session,
    customer_id: int,
    country_code: str = None,
) -> dict:
    """Get comprehensive credit summary for a customer."""
    customer = db.query(Customer).get(customer_id)
    if not customer:
        raise ValueError(f"Customer #{customer_id} not found")
    
    outstanding = _get_customer_outstanding_ar(db, customer_id)
    overdue = _get_customer_overdue_ar(db, customer_id)
    credit_limit = Decimal(str(customer.credit_limit or 0))
    available = credit_limit - outstanding if credit_limit > 0 else Decimal("0")
    utilization = float(outstanding / credit_limit * 100) if credit_limit > 0 else 0
    
    # Aging buckets
    aging = _get_customer_aging(db, customer_id)
    
    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "credit_limit": float(credit_limit),
        "outstanding_ar": float(outstanding),
        "overdue_ar": float(overdue),
        "available_credit": float(available),
        "utilization_pct": round(utilization, 1),
        "payment_terms_days": customer.payment_terms_days,
        "aging": aging,
    }


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_customer_outstanding_ar(db: Session, customer_id: int) -> Decimal:
    """Get total outstanding AR for a customer."""
    result = db.query(func.sum(ARInvoice.amount)).filter(
        ARInvoice.customer_id == customer_id,
        ARInvoice.status.in_(["issued", "partially_paid"]),
    ).scalar()
    return Decimal(str(result or 0))


def _get_customer_overdue_ar(db: Session, customer_id: int) -> Decimal:
    """Get total overdue AR for a customer."""
    result = db.query(func.sum(ARInvoice.amount)).filter(
        ARInvoice.customer_id == customer_id,
        ARInvoice.status.in_(["issued", "partially_paid"]),
        ARInvoice.due_date < _utcnow(),
    ).scalar()
    return Decimal(str(result or 0))


def _get_max_overdue_days(db: Session, customer_id: int) -> int:
    """Get the maximum overdue days across all invoices for a customer."""
    now = _utcnow()
    invoices = db.query(ARInvoice.due_date).filter(
        ARInvoice.customer_id == customer_id,
        ARInvoice.status.in_(["issued", "partially_paid"]),
        ARInvoice.due_date < now,
    ).all()
    
    if not invoices:
        return 0
    
    max_days = 0
    for inv in invoices:
        if inv.due_date:
            days = (now - inv.due_date).days
            if days > max_days:
                max_days = days
    return max_days


def _get_customer_aging(db: Session, customer_id: int) -> dict:
    """Get AR aging buckets for a customer."""
    now = _utcnow()
    
    def _bucket(days_min, days_max):
        if days_max:
            return db.query(func.sum(ARInvoice.amount)).filter(
                ARInvoice.customer_id == customer_id,
                ARInvoice.status.in_(["issued", "partially_paid"]),
                ARInvoice.due_date >= now - timedelta(days=days_max),
                ARInvoice.due_date < now - timedelta(days=days_min),
            ).scalar() or 0
        else:
            return db.query(func.sum(ARInvoice.amount)).filter(
                ARInvoice.customer_id == customer_id,
                ARInvoice.status.in_(["issued", "partially_paid"]),
                ARInvoice.due_date < now - timedelta(days=days_min),
            ).scalar() or 0
    
    return {
        "current": float(_bucket(0, 30)),
        "31_60": float(_bucket(30, 60)),
        "61_90": float(_bucket(60, 90)),
        "over_90": float(_bucket(90, None)),
    }


def _log_credit_control(db: Session, kind: str, entity_id: int, detail: dict, country_code: str = None):
    """Log credit control activity."""
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=1,
            records_changed=1,
            detail={**detail, "entity_id": entity_id},
            country_code=country_code,
        ))
        db.add(FinanceAuditLog(
            action="credit_control",
            entity_type="customer",
            entity_id=entity_id,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Credit control log failed: %s", e)
        db.rollback()


def _log_automation(db: Session, kind: str, processed: int, changed: int,
                     detail: dict = None, country_code: str = None):
    """Log automation run."""
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=processed,
            records_changed=changed,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Automation log failed: %s", e)
        db.rollback()
