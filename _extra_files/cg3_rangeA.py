_BADGE_THRESHOLDS = {
    # (min_credibility_score, label)
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

