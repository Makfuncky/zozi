"""Promotion Engine controller for admin builder settings and tier discounts."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from utils.audit_log import audit_log
from data.models import PromotionEngineConfig, PromotionLedgerEntry, PromotionOrderTier
from utils.money import to_decimal
from services.promotion_engine_service import ensure_promotion_tables
from data.services_write_helpers import (
from services.commerce.promotion_engine_service import _db_promotionengineconfig_first_0, _db_promotionordertier_count_1, _db_promotionordertier_query_2, _db_promotionordertier_first_3, _db_promotionordertier_first_4, _db_promotionordertier_query_5
    add_and_flush,
    commit_and_refresh,
    commit_only,
    delete_only,
    flush_only,
    rollback_only,
)


_ALLOWED_STACKING_MODES = {"best_only", "stack_all", "custom"}


def _serialize_config(row: PromotionEngineConfig) -> dict[str, Any]:
    return {
        "id": int(getattr(row, "id", 0) or 0),
        "engine_enabled": bool(getattr(row, "engine_enabled", False)),
        "allow_product_coupons": bool(getattr(row, "allow_product_coupons", False)),
        "allow_category_coupons": bool(getattr(row, "allow_category_coupons", False)),
        "allow_order_tier_discounts": bool(getattr(row, "allow_order_tier_discounts", False)),
        "allow_referral_rewards": bool(getattr(row, "allow_referral_rewards", False)),
        "allow_supplier_promotions": bool(getattr(row, "allow_supplier_promotions", False)),
        "allow_global_coupons": bool(getattr(row, "allow_global_coupons", False)),
        "stacking_mode": str(getattr(row, "stacking_mode", "best_only") or "best_only"),
        "max_combined_discount_percent": float(getattr(row, "max_combined_discount_percent", 0) or 0),
        "max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount", 0) or 0),
        "show_savings_line_item": bool(getattr(row, "show_savings_line_item", False)),
        "tier_discount_visible": bool(getattr(row, "tier_discount_visible", False)),
        "points_per_omr": int(getattr(row, "points_per_omr", 0) or 0),
        "referral_referrer_points": int(getattr(row, "referral_referrer_points", 0) or 0),
        "referral_referee_points": int(getattr(row, "referral_referee_points", 0) or 0),
        "points_expiry_months": int(getattr(row, "points_expiry_months", 0) or 0),
        "referral_monthly_cap": int(getattr(row, "referral_monthly_cap", 0) or 0),
        "referral_verification_delay_days": int(getattr(row, "referral_verification_delay_days", 0) or 0),
        "min_points_redeem": int(getattr(row, "min_points_redeem", 0) or 0),
        "allow_partial_points_redemption": bool(getattr(row, "allow_partial_points_redemption", False)),
        "updated_by": getattr(row, "updated_by", None),
        "created_at": getattr(row, "created_at", None),
        "updated_at": getattr(row, "updated_at", None),
    }


def _serialize_tier(row: PromotionOrderTier) -> dict[str, Any]:
    return {
        "id": int(getattr(row, "id", 0) or 0),
        "tier_name": str(getattr(row, "tier_name", "") or ""),
        "min_order": float(getattr(row, "min_order_amount", 0) or 0),
        "max_order": float(getattr(row, "max_order_amount")) if getattr(row, "max_order_amount", None) is not None else None,
        "discount_type": str(getattr(row, "discount_type", "fixed") or "fixed"),
        "discount_value": float(getattr(row, "discount_value", 0) or 0),
        "stacking_allowed": bool(getattr(row, "stacking_allowed", False)),
        "is_active": bool(getattr(row, "is_active", False)),
        "sort_order": int(getattr(row, "sort_order", 0) or 0),
        "updated_by": getattr(row, "updated_by", None),
        "created_at": getattr(row, "created_at", None),
    }


def _get_or_create_config(db: Session) -> PromotionEngineConfig:
    ensure_promotion_tables(db)
    row = _db_promotionengineconfig_first_0(db)
    if row:
        return row

    row = PromotionEngineConfig(
        engine_enabled=False,
        allow_product_coupons=True,
        allow_category_coupons=True,
        allow_order_tier_discounts=True,
        allow_referral_rewards=True,
        allow_supplier_promotions=True,
        allow_global_coupons=True,
        stacking_mode="best_only",
        max_combined_discount_percent=Decimal("50.00"),
        max_combined_discount_amount=Decimal("0.000"),
        show_savings_line_item=True,
        tier_discount_visible=True,
        points_per_omr=1000,
        referral_referrer_points=100,
        referral_referee_points=100,
        points_expiry_months=12,
        referral_monthly_cap=20,
        referral_verification_delay_days=7,
        min_points_redeem=1000,
        allow_partial_points_redemption=True,
        updated_at=datetime.now(timezone.utc),
    )
    add_and_flush(db, row)
    flush_only(db)
    _seed_default_tiers(db, updated_by=None)
    commit_and_refresh(db, row)
    return row


def _seed_default_tiers(db: Session, updated_by: Optional[int]) -> None:
    _db_promotionordertier_count_1(db)


    defaults = [
        {
            "tier_name": "Tier A",
            "min_order": Decimal("10.00"),
            "max_order": Decimal("24.99"),
            "discount_type": "fixed",
            "discount_value": Decimal("0.50"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 1,
        },
        {
            "tier_name": "Tier B",
            "min_order": Decimal("25.00"),
            "max_order": Decimal("49.99"),
            "discount_type": "fixed",
            "discount_value": Decimal("1.50"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 2,
        },
        {
            "tier_name": "Tier C",
            "min_order": Decimal("50.00"),
            "max_order": Decimal("99.99"),
            "discount_type": "fixed",
            "discount_value": Decimal("4.00"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 3,
        },
        {
            "tier_name": "Tier D",
            "min_order": Decimal("100.00"),
            "max_order": None,
            "discount_type": "percent",
            "discount_value": Decimal("5.00"),
            "stacking_allowed": False,
            "is_active": True,
            "sort_order": 4,
        },
    ]

    for payload in defaults:
        add_and_flush(db, 
            PromotionOrderTier(
                tier_name=payload["tier_name"],
                min_order_amount=payload["min_order"],
                max_order_amount=payload["max_order"],
                discount_type=payload["discount_type"],
                discount_amount=payload["discount_value"],
                discount_value=payload["discount_value"],
                stacking_allowed=payload["stacking_allowed"],
                is_active=payload["is_active"],
                sort_order=payload["sort_order"],
                updated_by=updated_by,
            )
        )


def get_promotion_config(db: Session) -> dict[str, Any]:
    row = _get_or_create_config(db)
    return _serialize_config(row)


def update_promotion_config(payload: dict[str, Any], acting_user: dict[str, Any], db: Session) -> dict[str, Any]:
    row = _get_or_create_config(db)

    if "stacking_mode" in payload:
        stacking_mode = str(payload["stacking_mode"] or "").strip().lower()
        if stacking_mode not in _ALLOWED_STACKING_MODES:
            raise HTTPException(status_code=422, detail="stacking_mode must be one of: best_only, stack_all, custom")
        setattr(row, "stacking_mode", stacking_mode)

    bool_fields = {
        "engine_enabled",
        "allow_product_coupons",
        "allow_category_coupons",
        "allow_order_tier_discounts",
        "allow_referral_rewards",
        "allow_supplier_promotions",
        "allow_global_coupons",
        "show_savings_line_item",
        "tier_discount_visible",
        "allow_partial_points_redemption",
    }
    for field in bool_fields:
        if field in payload:
            setattr(row, field, bool(payload[field]))

    numeric_decimal_fields = {
        "max_combined_discount_percent": (Decimal("0"), Decimal("100")),
        "max_combined_discount_amount": (Decimal("0"), None),
    }
    for field, (minimum, maximum) in numeric_decimal_fields.items():
        if field not in payload:
            continue
        value = to_decimal(payload[field])
        if value < minimum:
            raise HTTPException(status_code=422, detail=f"{field} must be >= {minimum}")
        if maximum is not None and value > maximum:
            raise HTTPException(status_code=422, detail=f"{field} must be <= {maximum}")
        setattr(row, field, value)

    numeric_int_fields = {
        "points_per_omr": 1,
        "referral_referrer_points": 0,
        "referral_referee_points": 0,
        "points_expiry_months": 0,
        "referral_monthly_cap": 0,
        "referral_verification_delay_days": 0,
        "min_points_redeem": 0,
    }
    for field, minimum in numeric_int_fields.items():
        if field not in payload:
            continue
        try:
            value = int(payload[field])
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=422, detail=f"{field} must be an integer") from exc
        if value < minimum:
            raise HTTPException(status_code=422, detail=f"{field} must be >= {minimum}")
        setattr(row, field, value)

    setattr(row, "updated_by", acting_user.get("id"))
    commit_and_refresh(db, row)

    audit_log(
        db=db,
        action="PROMOTION_CONFIG_UPDATED",
        user_id=acting_user.get("id"),
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="promotion_config",
        resource_id=getattr(row, "id", None),
        details={"updated_fields": sorted(payload.keys())},
        status="success",
    )
    return _serialize_config(row)


def list_promotion_tiers(db: Session) -> list[dict[str, Any]]:
    _get_or_create_config(db)
    rows = (
        _db_promotionordertier_query_2(db)
        .order_by(PromotionOrderTier.sort_order.asc(), PromotionOrderTier.min_order_amount.asc())
        .all()
    )
    return [_serialize_tier(row) for row in rows]


def _validate_tier_payload(payload: dict[str, Any], partial: bool = False) -> None:
    required = {"tier_name", "min_order", "discount_type", "discount_value"}
    if not partial:
        missing = [field for field in required if field not in payload]
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing required fields: {', '.join(missing)}")

    if "discount_type" in payload:
        discount_type = str(payload.get("discount_type") or "").strip().lower()
        if discount_type not in {"fixed", "percent"}:
            raise HTTPException(status_code=422, detail="discount_type must be fixed or percent")

    if "min_order" in payload and to_decimal(payload["min_order"]) < Decimal("0"):
        raise HTTPException(status_code=422, detail="min_order must be >= 0")

    if "max_order" in payload and payload["max_order"] is not None:
        if to_decimal(payload["max_order"]) < Decimal("0"):
            raise HTTPException(status_code=422, detail="max_order must be >= 0")

    if "discount_value" in payload and to_decimal(payload["discount_value"]) < Decimal("0"):
        raise HTTPException(status_code=422, detail="discount_value must be >= 0")


def create_promotion_tier(payload: dict[str, Any], acting_user: dict[str, Any], db: Session) -> dict[str, Any]:
    _get_or_create_config(db)
    _validate_tier_payload(payload, partial=False)

    min_order = to_decimal(payload["min_order"])
    max_order = to_decimal(payload["max_order"]) if payload.get("max_order") is not None else None
    if max_order is not None and max_order < min_order:
        raise HTTPException(status_code=422, detail="max_order must be >= min_order")

    row = PromotionOrderTier(
        tier_name=str(payload["tier_name"]).strip(),
        min_order_amount=min_order,
        max_order_amount=max_order,
        discount_type=str(payload["discount_type"]).strip().lower(),
        discount_value=to_decimal(payload["discount_value"]),
        stacking_allowed=bool(payload.get("stacking_allowed", False)),
        is_active=bool(payload.get("is_active", True)),
        sort_order=int(payload.get("sort_order") or 0),
        updated_by=acting_user.get("id"),
    )
    add_and_flush(db, row)
    commit_and_refresh(db, row)

    audit_log(
        db=db,
        action="PROMOTION_TIER_CREATED",
        user_id=acting_user.get("id"),
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="promotion_tier",
        resource_id=getattr(row, "id", None),
        details={"tier_name": row.tier_name},
        status="success",
    )
    return _serialize_tier(row)


def update_promotion_tier(tier_id: int, payload: dict[str, Any], acting_user: dict[str, Any], db: Session) -> dict[str, Any]:
    _get_or_create_config(db)
    row = _db_promotionordertier_first_3(db, id, tier_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tier not found")

    _validate_tier_payload(payload, partial=True)

    if "tier_name" in payload:
        setattr(row, "tier_name", str(payload["tier_name"]).strip())
    if "discount_type" in payload:
        setattr(row, "discount_type", str(payload["discount_type"]).strip().lower())
    if "min_order" in payload:
        setattr(row, "min_order_amount", to_decimal(payload["min_order"]))
    if "max_order" in payload:
        setattr(row, "max_order_amount", to_decimal(payload["max_order"]) if payload["max_order"] is not None else None)
    row_max_order = to_decimal(getattr(row, "max_order_amount", None), default=Decimal("0")) if getattr(row, "max_order_amount", None) is not None else None
    row_min_order = to_decimal(getattr(row, "min_order_amount", 0), default=Decimal("0"))
    if row_max_order is not None and row_max_order < row_min_order:
        raise HTTPException(status_code=422, detail="max_order must be >= min_order")
    if "discount_value" in payload:
        setattr(row, "discount_value", to_decimal(payload["discount_value"]))
    if "stacking_allowed" in payload:
        setattr(row, "stacking_allowed", bool(payload["stacking_allowed"]))
    if "is_active" in payload:
        setattr(row, "is_active", bool(payload["is_active"]))
    if "sort_order" in payload:
        setattr(row, "sort_order", int(payload["sort_order"]))
    setattr(row, "updated_by", acting_user.get("id"))

    commit_and_refresh(db, row)

    audit_log(
        db=db,
        action="PROMOTION_TIER_UPDATED",
        user_id=acting_user.get("id"),
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="promotion_tier",
        resource_id=tier_id,
        details={"updated_fields": sorted(payload.keys())},
        status="success",
    )
    return _serialize_tier(row)


def delete_promotion_tier(tier_id: int, acting_user: dict[str, Any], db: Session) -> dict[str, Any]:
    _get_or_create_config(db)
    row = _db_promotionordertier_first_4(db, id, tier_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tier not found")

    ledger_count = db.query(func.count(PromotionLedgerEntry.id)).filter(PromotionLedgerEntry.tier_id == tier_id).scalar() or 0
    if ledger_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Tier is referenced by {ledger_count} promotion ledger entr{'y' if ledger_count == 1 else 'ies'}. Disable it instead of deleting.",
        )

    tier_name = str(getattr(row, "tier_name", "") or "")
    try:
        delete_only(db, row)
        commit_only(db)
    except IntegrityError:
        rollback_only(db)
        raise HTTPException(
            status_code=409,
            detail="Tier has related records that must be archived or removed before deletion.",
        )

    audit_log(
        db=db,
        action="PROMOTION_TIER_DELETED",
        user_id=acting_user.get("id"),
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="promotion_tier",
        resource_id=tier_id,
        details={"tier_name": tier_name},
        status="success",
    )
    return {"message": "Tier deleted"}


def _find_matching_tier(order_value: Decimal, db: Session) -> Optional[PromotionOrderTier]:
    rows = (
        _db_promotionordertier_query_5(db)
        .filter(PromotionOrderTier.is_active.is_(True))
        .order_by(PromotionOrderTier.sort_order.asc(), PromotionOrderTier.min_order_amount.asc())
        .all()
    )
    for row in rows:
        min_order = to_decimal(getattr(row, "min_order_amount", 0), default=Decimal("0"))
        max_order = (
            to_decimal(getattr(row, "max_order_amount"), default=Decimal("0"))
            if getattr(row, "max_order_amount", None) is not None
            else None
        )
        if order_value < min_order:
            continue
        if max_order is not None and order_value > max_order:
            continue
        return row
    return None


def calculate_order_tier_discount(order_subtotal: Decimal, db: Session) -> tuple[Decimal, Optional[PromotionOrderTier]]:
    config = _get_or_create_config(db)
    if not bool(getattr(config, "engine_enabled", False)) or not bool(getattr(config, "allow_order_tier_discounts", False)):
        return Decimal("0.00"), None

    subtotal = max(to_decimal(order_subtotal), Decimal("0.00"))
    tier = _find_matching_tier(subtotal, db)
    if tier is None:
        return Decimal("0.00"), None

    if str(getattr(tier, "discount_type", "fixed") or "fixed") == "percent":
        discount = (subtotal * to_decimal(getattr(tier, "discount_value", 0), default=Decimal("0"))) / Decimal("100")
    else:
        discount = to_decimal(getattr(tier, "discount_value", 0), default=Decimal("0"))

    max_pct = to_decimal(getattr(config, "max_combined_discount_percent", 0), default=Decimal("0"))
    max_pct_discount = subtotal * max_pct / Decimal("100")
    discount = min(discount, max_pct_discount)

    max_amount = to_decimal(getattr(config, "max_combined_discount_amount", 0), default=Decimal("0"))
    if max_amount > 0:
        discount = min(discount, max_amount)

    discount = min(discount, subtotal)
    return discount.quantize(Decimal("0.01")), tier


def preview_order_tier_discount(order_subtotal: Decimal, coupon_discount: Decimal, db: Session) -> dict[str, Any]:
    config = _get_or_create_config(db)
    subtotal = max(to_decimal(order_subtotal), Decimal("0.00"))
    coupon_value = max(to_decimal(coupon_discount), Decimal("0.00"))
    after_coupon = max(subtotal - coupon_value, Decimal("0.00"))

    tier_discount, tier = calculate_order_tier_discount(after_coupon, db)
    return {
        "engine_enabled": bool(getattr(config, "engine_enabled", False)),
        "stacking_mode": str(getattr(config, "stacking_mode", "best_only") or "best_only"),
        "subtotal": float(subtotal),
        "coupon_discount": float(coupon_value),
        "after_coupon": float(after_coupon),
        "tier_discount": float(tier_discount),
        "final_discount": float(coupon_value + tier_discount),
        "final_payable_before_tax_shipping": float(max(after_coupon - tier_discount, Decimal("0.00"))),
        "matched_tier": _serialize_tier(tier) if tier else None,
    }


def record_order_tier_ledger(
    *,
    order_id: int,
    user_id: Optional[int],
    tier: PromotionOrderTier,
    discount_amount: Decimal,
    db: Session,
) -> None:
    if discount_amount <= 0:
        return

    ensure_promotion_tables(db)
    entry = PromotionLedgerEntry(
        order_id=order_id,
        user_id=user_id,
        promotion_type="order_tier",
        promotion_code=getattr(tier, "tier_name", None),
        tier_id=getattr(tier, "id", None),
        discount_amount=to_decimal(discount_amount),
        points_awarded=0,
        points_redeemed=0,
        stacking_flag=bool(getattr(tier, "stacking_allowed", False)),
        source="checkout",
        metadata_json=None,
    )
    add_and_flush(db, entry)

