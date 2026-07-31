"""
Supplier Badge & Credibility Service.

Moved out of controllers/supplier_controller.py to break the
services -> controllers forbidden dependency edge (DG violation).
All badge/credibility DB-write logic now lives here in the service layer.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from models import (
    BadgeBillingRecord,
    CommissionBadgeTier,
    Order,
    OrderItem,
    Product,
    SupplierProfile,
    User,
)
from services.audit.audit_service import AuditAction, audit_log
from utils.cache import bump_cache_version
from utils.config import settings
from utils.datetime_utils import utcnow
from utils.money import to_decimal

logger = logging.getLogger(__name__)

_BADGE_THRESHOLDS = {
    "gold": 85,
    "silver": 65,
    "bronze": 40,
    "none": 0,
}
_FULFILLED_ORDER_STATUSES = ("completed", "delivered", "shipped")
_MANUAL_BADGE_LEVELS = {"membership", "verified"}
_BADGE_AMOUNT_QUANT = Decimal("0.001")


def _round_badge_amount(value: object) -> Decimal:
    return to_decimal(value).quantize(_BADGE_AMOUNT_QUANT, rounding=ROUND_HALF_UP)


def _ensure_supplier_profile_record(supplier_id: int, db: Session) -> SupplierProfile:
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    if not profile:
        profile = SupplierProfile(user_id=supplier_id, verification_status="pending")
        db.add(profile)
        db.flush()
    return profile


def _start_of_month(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_next_month(value: datetime) -> datetime:
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return value.replace(month=value.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_year(value: datetime) -> datetime:
    return value.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_next_year(value: datetime) -> datetime:
    return value.replace(year=value.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _badge_period_bounds(interval: Optional[str], reference_time: datetime) -> tuple[Optional[datetime], Optional[datetime]]:
    normalized = str(interval or "").strip().lower()
    if normalized == "monthly":
        return _start_of_month(reference_time), _start_of_next_month(reference_time)
    if normalized in {"annual", "yearly"}:
        return _start_of_year(reference_time), _start_of_next_year(reference_time)
    return None, None


def _load_active_badge_tiers(db: Session) -> list[CommissionBadgeTier]:
    rows = (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.is_active == True)  # noqa: E712
        .order_by(CommissionBadgeTier.sort_order.asc(), CommissionBadgeTier.id.asc())
        .all()
    )
    if rows:
        return rows

    from services import commission_engine as _commission_engine

    _commission_engine.seed_defaults(db)
    return (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.is_active == True)  # noqa: E712
        .order_by(CommissionBadgeTier.sort_order.asc(), CommissionBadgeTier.id.asc())
        .all()
    )


def _badge_tier_meets_metrics(tier: CommissionBadgeTier, metrics: dict[str, Any]) -> bool:
    required_orders = int(getattr(tier, "min_fulfilled_orders", None) or 0)
    required_revenue = to_decimal(getattr(tier, "min_monthly_revenue", None) or 0)
    return int(metrics["fulfilled_orders"]) >= required_orders and to_decimal(metrics["monthly_revenue"]) >= required_revenue


def _compute_badge_threshold_metrics(supplier_id: int, db: Session, reference_time: Optional[datetime] = None) -> dict[str, Any]:
    now = reference_time or utcnow()
    month_start = _start_of_month(now)

    fulfilled_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(_FULFILLED_ORDER_STATUSES),
        )
        .scalar()
    ) or 0

    monthly_revenue = (
        db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(_FULFILLED_ORDER_STATUSES),
            Order.created_at >= month_start,
        )
        .scalar()
    ) or 0

    return {
        "fulfilled_orders": int(fulfilled_orders),
        "monthly_revenue": _round_badge_amount(monthly_revenue),
        "month_start": month_start,
        "month_label": month_start.strftime("%Y-%m"),
    }


def _select_eligible_badge_tier(metrics: dict[str, Any], db: Session) -> Optional[CommissionBadgeTier]:
    tiers = _load_active_badge_tiers(db)
    fallback = next((tier for tier in tiers if str(tier.badge_level or "").lower() == "none"), None)
    selected = fallback
    for tier in tiers:
        level = str(tier.badge_level or "").lower()
        if level in _MANUAL_BADGE_LEVELS:
            continue
        if level == "none":
            continue
        if _badge_tier_meets_metrics(tier, metrics):
            selected = tier
    return selected


def _serialize_badge_billing_record(record: BadgeBillingRecord) -> dict[str, Any]:
    supplier = getattr(record, "supplier", None)
    txn = getattr(record, "bank_transaction", None)
    return {
        "id": record.id,
        "billing_reference": record.billing_reference,
        "supplier_id": record.supplier_id,
        "supplier_name": getattr(supplier, "username", None),
        "badge_level": record.badge_level,
        "charge_type": record.charge_type,
        "charge_source": record.charge_source,
        "status": record.status,
        "amount": float(_round_badge_amount(record.amount)),
        "currency": record.currency,
        "period_start": record.period_start,
        "period_end": record.period_end,
        "due_at": record.due_at,
        "billed_at": record.billed_at,
        "paid_at": record.paid_at,
        "payment_method": record.payment_method,
        "bank_transaction_id": record.bank_transaction_id,
        "transaction_ref": getattr(txn, "transaction_ref", None),
        "notes": record.notes,
        "created_by": record.created_by,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _find_existing_badge_billing(
    supplier_id: int,
    badge_level: str,
    charge_type: str,
    db: Session,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> Optional[BadgeBillingRecord]:
    q = db.query(BadgeBillingRecord).filter(
        BadgeBillingRecord.supplier_id == supplier_id,
        BadgeBillingRecord.badge_level == badge_level,
        BadgeBillingRecord.charge_type == charge_type,
        BadgeBillingRecord.status.in_(("draft", "invoiced", "paid")),
    )
    if charge_type == "setup":
        return q.order_by(BadgeBillingRecord.created_at.desc()).first()
    if period_start is not None:
        q = q.filter(BadgeBillingRecord.period_start == period_start)
    if period_end is not None:
        q = q.filter(BadgeBillingRecord.period_end == period_end)
    return q.order_by(BadgeBillingRecord.created_at.desc()).first()


def _create_badge_billing_record(
    supplier_id: int,
    badge_level: str,
    charge_type: str,
    amount: Decimal,
    db: Session,
    *,
    charge_source: str,
    created_by: Optional[int],
    notes: Optional[str] = None,
    payment_method: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    due_at: Optional[datetime] = None,
) -> tuple[BadgeBillingRecord, bool]:
    existing = _find_existing_badge_billing(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        db=db,
        period_start=period_start,
        period_end=period_end,
    )
    if existing:
        return existing, False

    now = utcnow()
    normalized_amount = _round_badge_amount(amount)
    status = "paid" if normalized_amount <= 0 else "invoiced"
    record = BadgeBillingRecord(
        billing_reference=f"BDG-{uuid.uuid4().hex[:10].upper()}",
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        charge_source=charge_source,
        status=status,
        amount=normalized_amount,
        currency=settings.default_currency,
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
        billed_at=now,
        paid_at=now if status == "paid" else None,
        payment_method=payment_method,
        notes=notes,
        created_by=created_by,
    )
    db.add(record)
    db.flush()
    return record, True


def _maybe_create_recurring_badge_billing(
    supplier_id: int,
    badge_level: str,
    badge_granted_at: Optional[datetime],
    db: Session,
    *,
    charge_source: str,
    created_by: Optional[int],
) -> Optional[BadgeBillingRecord]:
    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.badge_level == badge_level,
            CommissionBadgeTier.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not tier:
        return None

    recurring_fee = _round_badge_amount(getattr(tier, "recurring_fee", 0) or 0)
    if recurring_fee <= 0:
        return None

    period_start, period_end = _badge_period_bounds(getattr(tier, "recurring_interval", None), utcnow())
    if period_start is None or period_end is None:
        return None

    if badge_granted_at and badge_granted_at >= period_start:
        return None

    record, created = _create_badge_billing_record(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type="recurring",
        amount=recurring_fee,
        db=db,
        charge_source=charge_source,
        created_by=created_by,
        notes=f"Recurring {badge_level} badge fee for {period_start.strftime('%Y-%m')}",
        period_start=period_start,
        period_end=period_end,
        due_at=period_end,
    )
    return record if created else None


def list_supplier_badge_catalog(current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = int(current_user["id"])
    profile = _ensure_supplier_profile_record(supplier_id, db)
    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    eligible_tier = _select_eligible_badge_tier(metrics, db)
    current_badge = str(profile.badge_level or "none").lower()

    tiers = []
    for tier in _load_active_badge_tiers(db):
        badge_level = str(tier.badge_level or "none").lower()
        tiers.append({
            "badge_level": badge_level,
            "commission_rate": float(tier.commission_rate),
            "setup_fee": float(_round_badge_amount(tier.setup_fee)),
            "recurring_fee": float(_round_badge_amount(tier.recurring_fee)),
            "recurring_interval": tier.recurring_interval,
            "min_fulfilled_orders": tier.min_fulfilled_orders,
            "min_monthly_revenue": float(_round_badge_amount(tier.min_monthly_revenue or 0)),
            "is_active": bool(tier.is_active),
            "is_current": badge_level == current_badge,
            "is_eligible": _badge_tier_meets_metrics(tier, metrics) if badge_level not in _MANUAL_BADGE_LEVELS else False,
            "is_recommended": badge_level == str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        })

    return {
        "supplier_id": supplier_id,
        "current_badge_level": current_badge,
        "eligible_badge_level": str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
        "month_label": metrics["month_label"],
        "tiers": tiers,
    }


def list_supplier_badge_billing_history(current_user: dict, db: Session) -> list[dict[str, Any]]:
    supplier_id = int(current_user["id"])
    rows = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.bank_transaction), selectinload(BadgeBillingRecord.supplier))
        .filter(BadgeBillingRecord.supplier_id == supplier_id)
        .order_by(BadgeBillingRecord.created_at.desc())
        .limit(100)
        .all()
    )
    return [_serialize_badge_billing_record(row) for row in rows]


def record_badge_billing_payment(
    billing_id: int,
    payment_method: str,
    current_user: dict,
    db: Session,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    record = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.bank_transaction), selectinload(BadgeBillingRecord.supplier))
        .filter(BadgeBillingRecord.id == billing_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Badge billing record not found")
    if record.status == "paid":
        return _serialize_badge_billing_record(record)
    if record.status in {"waived", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"Cannot record payment for {record.status} badge billing")

    paid_at = utcnow()
    if _round_badge_amount(record.amount) > 0 and not record.bank_transaction_id:
        from services.cash_management_service import log_bank_transaction

        txn = log_bank_transaction(
            source="badge_billing",
            transaction_type="inflow",
            category="badge_fee",
            amount=_round_badge_amount(record.amount),
            db=db,
            currency=record.currency,
            supplier_id=record.supplier_id,
            description=f"{record.charge_type.title()} badge fee collected for {record.badge_level} tier",
            transaction_ref=transaction_ref,
            transaction_date=paid_at,
        )
        record.bank_transaction_id = txn.id
        record.bank_transaction = txn

    record.status = "paid"
    record.payment_method = payment_method.strip().lower() or "manual"
    record.paid_at = paid_at
    if notes:
        record.notes = notes if not record.notes else f"{record.notes}\n{notes}"

    db.flush()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="badge_billing",
        resource_id=record.id,
        details={"status": record.status, "payment_method": record.payment_method, "badge_level": record.badge_level},
    )
    db.commit()
    db.refresh(record)
    return _serialize_badge_billing_record(record)


def purchase_supplier_badge(body: dict, current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = int(current_user["id"])
    badge_level = str(body.get("badge_level") or "").strip().lower()
    notes = str(body.get("notes") or "").strip() or None
    if current_user["role"] != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required")
    if not badge_level or badge_level in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
        raise HTTPException(status_code=422, detail="Select a purchasable badge tier")

    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.badge_level == badge_level,
            CommissionBadgeTier.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not tier:
        raise HTTPException(status_code=404, detail="Badge tier not found")

    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    if not _badge_tier_meets_metrics(tier, metrics):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Supplier is not yet eligible for {badge_level}. "
                f"Requires {int(getattr(tier, 'min_fulfilled_orders', None) or 0)} fulfilled orders and "
                f"{float(_round_badge_amount(getattr(tier, 'min_monthly_revenue', None) or 0))} monthly revenue."
            ),
        )

    profile = _ensure_supplier_profile_record(supplier_id, db)
    previous_badge = str(profile.badge_level or "none").lower()
    charge_type = "recurring" if previous_badge == badge_level else "setup"
    amount = _round_badge_amount(tier.recurring_fee if charge_type == "recurring" else tier.setup_fee)
    period_start, period_end = (None, None)
    due_at = utcnow() + timedelta(days=7)

    if charge_type == "recurring":
        period_start, period_end = _badge_period_bounds(getattr(tier, "recurring_interval", None), utcnow())
        if period_start is None or period_end is None:
            raise HTTPException(status_code=422, detail="This badge tier does not have a recurring billing interval")
        due_at = period_end

    record, created = _create_badge_billing_record(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        amount=amount,
        db=db,
        charge_source="manual_purchase",
        created_by=supplier_id,
        notes=notes,
        payment_method="manual" if amount <= 0 else None,
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
    )

    if charge_type == "setup" and previous_badge != badge_level:
        profile.badge_level = badge_level
        profile.badge_granted_at = utcnow()

    profile.credibility_score = compute_credibility_score(supplier_id, db)
    db.flush()

    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=supplier_id,
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="badge_purchase",
        resource_id=record.id,
        details={
            "badge_level": badge_level,
            "charge_type": charge_type,
            "amount": float(_round_badge_amount(record.amount)),
            "created": created,
        },
    )

    db.commit()
    db.refresh(record)
    return {
        "badge_level": str(profile.badge_level or "none").lower(),
        "billing": _serialize_badge_billing_record(record),
        "created": created,
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
    }


def compute_credibility_score(supplier_id: int, db: Session) -> int:
    """
    Compute a 0-100 credibility score based on:
      - Order fulfilment rate        (max 35 pts)
      - Average product review score (max 25 pts)
      - Document verification status (max 20 pts)
      - Account age in days          (max 10 pts)
      - Number of approved products  (max 10 pts)
    """
    from models import Order, OrderItem, Product, Review
    from models import SupplierProfile as SP

    total_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    fulfilled_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(["completed", "delivered", "shipped"]),
        )
        .scalar()
    ) or 0
    fulfilment_rate = (fulfilled_orders / total_orders) if total_orders > 0 else 0
    pts_fulfilment = round(fulfilment_rate * 35)

    avg_review = (
        db.query(func.avg(Review.rating))
        .join(Product, Review.product_id == Product.id)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    pts_review = round((float(avg_review) / 5.0) * 25)

    profile = db.query(SP).filter(SP.user_id == supplier_id).first()
    docs = {}
    if profile and profile.verified_documents:
        try:
            docs = json.loads(profile.verified_documents)
        except Exception:
            docs = {}
    pts_docs = 0
    if profile and profile.verification_status in ("approved", "verified"):
        pts_docs = 20
    elif docs:
        pts_docs = min(15, len(docs) * 5)

    user = db.query(User).filter(User.id == supplier_id).first()
    age_days = 0
    if user and user.created_at:
        age_days = max(0, (utcnow() - user.created_at).days)
    pts_age = min(10, age_days // 30)

    approved_count = (
        db.query(func.count(Product.id))
        .filter(
            Product.supplier_id == supplier_id,
            Product.is_approved == True,  # noqa: E712
            Product.is_deleted == False,  # noqa: E712
        )
        .scalar()
    ) or 0
    pts_products = min(10, approved_count)

    return int(pts_fulfilment + pts_review + pts_docs + pts_age + pts_products)


def _badge_for_score(score: int) -> str:
    if score >= _BADGE_THRESHOLDS["gold"]:
        return "gold"
    if score >= _BADGE_THRESHOLDS["silver"]:
        return "silver"
    if score >= _BADGE_THRESHOLDS["bronze"]:
        return "bronze"
    return "none"


def refresh_supplier_badge(supplier_id: int, db: Session) -> dict:
    """Recompute credibility score and align badge assignment to tier thresholds."""
    profile = _ensure_supplier_profile_record(supplier_id, db)
    score = compute_credibility_score(supplier_id, db)
    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    eligible_tier = _select_eligible_badge_tier(metrics, db)
    previous_badge = str(profile.badge_level or "none").lower()

    if previous_badge in _MANUAL_BADGE_LEVELS:
        resolved_badge = previous_badge
    else:
        resolved_badge = str(getattr(eligible_tier, "badge_level", None) or _badge_for_score(score)).lower()

    profile.credibility_score = score
    created_billings: list[dict[str, Any]] = []
    if previous_badge != resolved_badge:
        profile.badge_level = resolved_badge
        profile.badge_granted_at = utcnow()
        if eligible_tier is not None and resolved_badge not in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
            record, created = _create_badge_billing_record(
                supplier_id=supplier_id,
                badge_level=resolved_badge,
                charge_type="setup",
                amount=_round_badge_amount(getattr(eligible_tier, "setup_fee", 0) or 0),
                db=db,
                charge_source="automatic_recalculation",
                created_by=None,
                notes=f"Automatic badge recalculation promoted supplier to {resolved_badge}",
                due_at=utcnow() + timedelta(days=7),
            )
            if created:
                created_billings.append(_serialize_badge_billing_record(record))
        audit_log(
            db=db,
            action=AuditAction.PROFILE_UPDATED,
            user_id=None,
            username="system",
            user_role="system",
            resource_type="supplier_badge",
            resource_id=supplier_id,
            details={"previous_badge": previous_badge, "badge_level": resolved_badge, "source": "automatic_recalculation"},
        )

    recurring_billing = None
    if resolved_badge not in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
        recurring_record = _maybe_create_recurring_badge_billing(
            supplier_id=supplier_id,
            badge_level=resolved_badge,
            badge_granted_at=profile.badge_granted_at,
            db=db,
            charge_source="scheduled_recurring",
            created_by=None,
        )
        if recurring_record is not None:
            recurring_billing = _serialize_badge_billing_record(recurring_record)

    db.commit()
    bump_cache_version("public_suppliers")
    return {
        "supplier_id": supplier_id,
        "credibility_score": score,
        "badge_level": str(profile.badge_level or "none").lower(),
        "previous_badge_level": previous_badge,
        "eligible_badge_level": str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
        "month_label": metrics["month_label"],
        "billing_records_created": created_billings,
        "recurring_billing": recurring_billing,
    }


def run_badge_recalculation_cycle(db: Session) -> dict[str, Any]:
    supplier_ids = [supplier_id for supplier_id, in db.query(User.id).filter(User.role == "supplier").all()]
    changed = 0
    invoiced = 0
    recurring = 0
    snapshots: list[dict[str, Any]] = []
    for supplier_id in supplier_ids:
        snapshot = refresh_supplier_badge(int(supplier_id), db)
        snapshots.append(snapshot)
        if snapshot.get("previous_badge_level") != snapshot.get("badge_level"):
            changed += 1
        invoiced += len(snapshot.get("billing_records_created") or [])
        recurring += 1 if snapshot.get("recurring_billing") else 0
    return {
        "suppliers_processed": len(supplier_ids),
        "badges_changed": changed,
        "billings_created": invoiced,
        "recurring_billings_created": recurring,
        "snapshots": snapshots,
    }


def admin_set_supplier_badge(
    supplier_user_id: int,
    badge_level: str,
    current_user: dict,
    db: Session,
) -> dict:
    """Admin: manually override badge level for a supplier."""
    from models import SupplierProfile as SP

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    normalized_badge_level = str(badge_level or "").strip().lower()
    valid_badges = {"none", "bronze", "silver", "gold", "membership", "verified"}
    if normalized_badge_level not in valid_badges:
        raise HTTPException(status_code=422, detail=f"badge_level must be one of: {', '.join(sorted(valid_badges))}")
    profile = db.query(SP).filter(SP.user_id == supplier_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    profile.badge_level = normalized_badge_level
    profile.badge_granted_at = utcnow()
    db.commit()
    bump_cache_version("public_suppliers")
    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="supplier_badge",
        resource_id=supplier_user_id,
        details={"badge_level": normalized_badge_level},
    )
    return {
        "supplier_id": supplier_user_id,
        "badge_level": profile.badge_level,
        "badge_granted_at": profile.badge_granted_at.isoformat(),
    }
