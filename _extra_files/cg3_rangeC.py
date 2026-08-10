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


