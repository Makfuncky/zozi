"""
Commission Controller — admin-managed supplier and product-level commission rates.

Combined lookup flow:
    1. Supplier component comes from an active supplier override or the supplier badge tier.
    2. Base component comes from a product override, else category rate, else global default.
    3. Final commission rate = supplier component + resolved base component.

Low-value cap: if order_value < low_value_threshold (5 OMR):
    final_commission = min(rate * order_value, fixed_cap_amount)
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from data.models import (
    CommissionAgreement,
    CommissionBadgeTier,
    CommissionCategoryRate,
    CommissionGlobalConfig,
    CommissionLedgerEntry,
    ProductCommissionOverride,
    SupplierProfile,
    User,
    Product,
)
from utils.audit_log import AuditAction, audit_log
from services import commission_engine
from data.services_write_helpers import (
from services.finance.commission_read_service import get_product_by_id, get_user_by_id
    add_and_flush,
    commit_and_refresh,
    commit_only,
    delete_only,
    flush_only,
)


def _build_list_page_payload(items: list[Any], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict[str, Any]:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }


def _float_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _category_to_slug(raw_value: Any) -> Optional[str]:
    raw = str(raw_value or "").strip().lower()
    if not raw:
        return None
    return raw.replace(" & ", "-").replace(" ", "-")


def _supplier_rate_snapshot(supplier_id: int, db: Session) -> commission_engine.RateResult:
    return commission_engine.get_effective_rate(
        supplier_id=supplier_id,
        product_id=None,
        category_slug=None,
        db=db,
    )


# ── Effective rate lookup ────────────────────────────────────────────────────

def get_effective_rate(
    supplier_id: int,
    product_id: Optional[int],
    db: Session,
) -> Decimal:
    """Return the effective commission rate for a supplier/product combo."""
    category_slug: Optional[str] = None
    if product_id:
        product = get_product_by_id(db, product_id)
        category_slug = _category_to_slug(getattr(product, "category", None) if product else None)

    return commission_engine.get_effective_rate(
        supplier_id=supplier_id,
        product_id=product_id,
        category_slug=category_slug,
        db=db,
    ).applied_rate


# ── Supplier-level commission ────────────────────────────────────────────────

def get_supplier_commission(supplier_id: int, db: Session) -> dict:
    """Return active commission agreement and full history for a supplier."""
    supplier = get_user_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    active = (
        _db_commissionagreement_query_0(db)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .first()
    )

    history = (
        _db_commissionagreement_query_1(db)
        .filter(CommissionAgreement.supplier_id == supplier_id)
        .order_by(CommissionAgreement.effective_from.desc())
        .all()
    )

    current_snapshot = _supplier_rate_snapshot(supplier_id, db)

    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.full_name or supplier.username,
        "current_rate": float(current_snapshot.supplier_rate),
        "using_default": active is None,
        "calculation_method": current_snapshot.supplier_rate_source,
        "badge_level": current_snapshot.badge_level,
        "default_base_rate": float(current_snapshot.global_default_rate),
        "combined_default_rate": float(current_snapshot.applied_rate),
        "active_agreement": _serialize_agreement(active) if active else None,
        "history": [_serialize_agreement(a) for a in history],
    }


def set_supplier_commission(
    supplier_id: int,
    rate: float,
    note: Optional[str],
    acting_user: dict,
    db: Session,
) -> dict:
    """
    Set a new supplier-level commission rate.

    Deactivates any previous active agreement, then inserts a new one.
    Rate must be in 0.0–1.0 range (e.g. 0.12 for 12%).
    """
    _require_admin(acting_user)
    if not (0.0 <= rate <= 1.0):
        raise HTTPException(status_code=422, detail="Rate must be between 0.0 and 1.0")

    supplier = _db_user_first_2(db, id, role, supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    now = datetime.now(timezone.utc)

    # Deactivate previous active agreement
    prev = (
        _db_commissionagreement_query_3(db)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .first()
    )
    if prev:
        prev.is_active = False  # type: ignore[assignment]
        prev.effective_to = now  # type: ignore[assignment]

    new_agreement = CommissionAgreement(
        supplier_id=supplier_id,
        rate=Decimal(str(rate)),
        effective_from=now,
        effective_to=None,
        is_active=True,
        set_by_admin_id=acting_user["id"],
        note=note,
    )
    add_and_flush(db, new_agreement)
    commit_and_refresh(db, new_agreement)

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="commission_agreement",
        resource_id=cast(int, getattr(new_agreement, "id")),
        details={"supplier_id": supplier_id, "new_rate": rate, "note": note},
        status="success",
    )

    return {"message": "Commission rate updated", "agreement_id": new_agreement.id}


def delete_supplier_commission_override(
    supplier_id: int,
    acting_user: dict,
    db: Session,
) -> dict:
    """Remove any active supplier-level commission override and revert to badge/default logic."""
    _require_admin(acting_user)

    active_agreements = (
        _db_commissionagreement_query_4(db)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .order_by(CommissionAgreement.created_at.desc(), CommissionAgreement.id.desc())
        .all()
    )
    if not active_agreements:
        raise HTTPException(status_code=404, detail="No active supplier commission override found")

    deleted_ids = [cast(int, getattr(agreement, "id")) for agreement in active_agreements]
    for agreement in active_agreements:
        delete_only(db, agreement)
    commit_only(db)

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="commission_agreement",
        resource_id=supplier_id,
        details={"action": "removed_supplier_override", "supplier_id": supplier_id, "agreement_ids": deleted_ids},
        status="success",
    )

    return {"message": "Supplier commission override removed", "deleted": len(deleted_ids)}


# ── Product-level commission override ────────────────────────────────────────

def get_product_commission_override(product_id: int, db: Session) -> Optional[dict]:
    """Return the active commission override for a product, or None."""
    override = (
        _db_productcommissionoverride_query_5(db)
        .filter(ProductCommissionOverride.product_id == product_id)
        .first()
    )
    return _serialize_override(override) if override else None


def set_product_commission_override(
    product_id: int,
    rate: float,
    note: Optional[str],
    acting_user: dict,
    db: Session,
) -> dict:
    """
    Create or update the product-level commission override.
    Rate must be in 0.0–1.0 range.
    """
    _require_admin(acting_user)
    if not (0.0 <= rate <= 1.0):
        raise HTTPException(status_code=422, detail="Rate must be between 0.0 and 1.0")

    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        _db_productcommissionoverride_query_6(db)
        .filter(ProductCommissionOverride.product_id == product_id)
        .first()
    )

    if existing:
        existing.rate = Decimal(str(rate))  # type: ignore[assignment]
        existing.is_active = True  # type: ignore[assignment]
        existing.set_by_admin_id = acting_user["id"]  # type: ignore[assignment]
        existing.note = note  # type: ignore[assignment]
        existing.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        override_id = existing.id
    else:
        override = ProductCommissionOverride(
            product_id=product_id,
            supplier_id=product.supplier_id,
            rate=Decimal(str(rate)),
            is_active=True,
            set_by_admin_id=acting_user["id"],
            note=note,
        )
        add_and_flush(db, override)
        flush_only(db)
        override_id = override.id

    commit_only(db)

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product_commission_override",
        resource_id=product_id,
        details={"rate": rate, "note": note},
        status="success",
    )

    return {"message": "Product commission override saved", "override_id": override_id}


def delete_product_commission_override(
    product_id: int,
    acting_user: dict,
    db: Session,
) -> dict:
    """Remove the product-level commission override (revert to supplier agreement)."""
    _require_admin(acting_user)

    override = (
        _db_productcommissionoverride_query_7(db)
        .filter(ProductCommissionOverride.product_id == product_id)
        .first()
    )
    if not override:
        raise HTTPException(status_code=404, detail="No commission override found for this product")

    delete_only(db, override)
    commit_only(db)

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product_commission_override",
        resource_id=product_id,
        details={"action": "removed"},
        status="success",
    )

    return {"message": "Commission override removed"}


def list_product_commission_overrides(
    db: Session,
    *,
    search: Optional[str] = None,
    supplier_id: Optional[int] = None,
    limit: int = 100,
) -> list[dict]:
    """Return product-level overrides with product and supplier context for admin operations."""
    q = (
        db.query(ProductCommissionOverride, Product, User)
        .join(Product, Product.id == ProductCommissionOverride.product_id)
        .join(User, User.id == ProductCommissionOverride.supplier_id)
        .order_by(ProductCommissionOverride.updated_at.desc(), ProductCommissionOverride.id.desc())
    )

    if supplier_id:
        q = q.filter(ProductCommissionOverride.supplier_id == supplier_id)
    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            (Product.name.ilike(term)) |
            (User.username.ilike(term)) |
            (User.full_name.ilike(term)) |
            (Product.category.ilike(term))
        )

    rows = q.limit(limit).all()
    return [
        {
            **cast(dict[str, Any], _serialize_override(override)),
            "product_name": getattr(product, "name", None),
            "product_category": getattr(product, "category", None),
            "supplier_name": getattr(supplier, "full_name", None) or getattr(supplier, "username", None),
        }
        for override, product, supplier in rows
    ]


def list_all_supplier_commissions(
    db: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict:
    """Return current commission rate for every active supplier."""
    resolved_limit = 100 if limit is None else max(1, min(limit, 500))
    query = _db_user_query_8(db, True, is_active, role, supplier)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.username.ilike(term), User.full_name.ilike(term), User.email.ilike(term)))
    total = query.count()
    suppliers = (
        query.order_by(User.full_name, User.username, User.id)
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    supplier_ids = [cast(int, getattr(supplier, "id")) for supplier in suppliers]
    agreements: dict[int, CommissionAgreement] = {}
    if supplier_ids:
        for agreement in (
            _db_commissionagreement_query_9(db)
            .filter(
                CommissionAgreement.supplier_id.in_(supplier_ids),
                CommissionAgreement.is_active == True,  # noqa: E712
            )
            .order_by(CommissionAgreement.created_at.desc(), CommissionAgreement.id.desc())
            .all()
        ):
            supplier_id = cast(int, getattr(agreement, "supplier_id"))
            agreements.setdefault(supplier_id, agreement)

    results = []
    for s in suppliers:
        active = agreements.get(cast(int, getattr(s, "id")))
        current_snapshot = _supplier_rate_snapshot(cast(int, getattr(s, "id")), db)
        results.append({
            "supplier_id": cast(int, getattr(s, "id")),
            "supplier_name": s.full_name or s.username,
            "current_rate": float(current_snapshot.supplier_rate),
            "using_default": active is None,
            "agreement_id": cast(int, getattr(active, "id")) if active else None,
            "calculation_method": current_snapshot.supplier_rate_source,
            "badge_level": current_snapshot.badge_level,
            "default_base_rate": float(current_snapshot.global_default_rate),
            "combined_default_rate": float(current_snapshot.applied_rate),
        })

    return _build_list_page_payload(results, total, offset=offset, page_size=resolved_limit)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _require_admin(user: dict) -> None:
    if user.get("role") not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required")


def _serialize_agreement(a: CommissionAgreement | None) -> Optional[dict]:
    if a is None:
        return None
    return {
        "id": cast(int, getattr(a, "id")),
        "supplier_id": cast(int, getattr(a, "supplier_id")),
        "rate": float(getattr(a, "rate")),
        "effective_from": getattr(a, "effective_from"),
        "effective_to": getattr(a, "effective_to"),
        "is_active": bool(getattr(a, "is_active")),
        "set_by_admin_id": getattr(a, "set_by_admin_id"),
        "note": getattr(a, "note"),
        "created_at": getattr(a, "created_at"),
    }


def _serialize_override(o: ProductCommissionOverride | None) -> Optional[dict]:
    if o is None:
        return None
    return {
        "id": cast(int, getattr(o, "id")),
        "product_id": cast(int, getattr(o, "product_id")),
        "supplier_id": cast(int, getattr(o, "supplier_id")),
        "rate": float(getattr(o, "rate")),
        "is_active": bool(getattr(o, "is_active")),
        "set_by_admin_id": getattr(o, "set_by_admin_id"),
        "note": getattr(o, "note"),
        "created_at": getattr(o, "created_at"),
        "updated_at": getattr(o, "updated_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Global Config
# ══════════════════════════════════════════════════════════════════════════════

def get_global_config(db: Session) -> dict:
    config = commission_engine.get_global_config(db)
    return _serialize_global_config(config)


def get_supplier_policy_snapshot(current_user: dict, db: Session) -> dict:
    config = get_global_config(db)
    active_categories = [
        row for row in cast(list[dict[str, Any]], list_category_rates(db, limit=500)["data"])
        if bool(row.get("is_active"))
    ]
    active_badge_tiers = [
        row for row in cast(list[dict[str, Any]], list_badge_tiers(db, limit=500)["data"])
        if bool(row.get("is_active"))
    ]

    supplier_id = current_user.get("id") if current_user.get("role") == "supplier" else None
    supplier_rate: Optional[dict[str, Any]] = None
    current_badge_level: Optional[str] = None

    if supplier_id is not None:
        snapshot = _supplier_rate_snapshot(int(supplier_id), db)
        supplier_rate = {
            "current_rate": float(snapshot.supplier_rate),
            "calculation_method": snapshot.supplier_rate_source,
            "badge_level": snapshot.badge_level,
            "using_default": snapshot.supplier_rate_source != "override",
            "combined_default_rate": float(snapshot.applied_rate),
            "default_base_rate": float(snapshot.global_default_rate),
        }
        current_badge_level = snapshot.badge_level

    resolution_order = [
        {
            "order": 1,
            "label": "Product exception",
            "state": "available",
            "detail": "A product-specific base rate replaces the category base rate when a product override exists.",
        },
        {
            "order": 2,
            "label": "Category base rate",
            "state": "available",
            "detail": f"{len(active_categories)} active category rates feed the base commission component when no product exception exists.",
        },
        {
            "order": 3,
            "label": "Supplier commission component",
            "state": "active" if supplier_rate is not None else "available",
            "detail": (
                f"Current supplier component uses {supplier_rate['calculation_method']} with badge {current_badge_level}."
                if current_badge_level and supplier_rate is not None
                else f"{len(active_badge_tiers)} active badge tiers can apply when supplier qualification is met."
            ),
        },
        {
            "order": 4,
            "label": "Guardrails",
            "state": "fallback",
            "detail": "Low-value cap applies after the combined rate is calculated, and margin protection remains an admin guardrail.",
        },
    ]

    return {
        "updated_at": config.get("updated_at"),
        "global_config": config,
        "supplier_rate": supplier_rate,
        "active_categories": [
            {
                "category_slug": row.get("category_slug"),
                "category_display_name": row.get("category_display_name"),
                "rate": row.get("rate"),
                "notes": row.get("notes"),
            }
            for row in active_categories
        ],
        "active_badge_tiers": [
            {
                "badge_level": row.get("badge_level"),
                "commission_rate": row.get("commission_rate"),
                "setup_fee": row.get("setup_fee"),
                "recurring_fee": row.get("recurring_fee"),
                "recurring_interval": row.get("recurring_interval"),
                "min_fulfilled_orders": row.get("min_fulfilled_orders"),
                "min_monthly_revenue": row.get("min_monthly_revenue"),
            }
            for row in active_badge_tiers
        ],
        "resolution_order": resolution_order,
    }


def update_global_config(payload: dict, acting_user: dict, db: Session) -> dict:
    _require_admin(acting_user)
    config = commission_engine.get_global_config(db)

    allowed = {
        "default_rate", "low_value_threshold", "fixed_cap_amount",
        "fixed_cap_enabled", "margin_protection_enabled", "margin_threshold",
    }
    for key, value in payload.items():
        if key not in allowed:
            continue
        if key in {"default_rate", "margin_threshold"} and value is not None:
            if not (0.0 <= float(value) <= 1.0):
                raise HTTPException(status_code=422, detail=f"{key} must be between 0.0 and 1.0")
        normalized = value
        if key in {"default_rate", "low_value_threshold", "fixed_cap_amount", "margin_threshold"}:
            normalized = None if value is None else Decimal(str(value))
        setattr(config, key, normalized)

    setattr(config, "updated_by", acting_user["id"])
    setattr(config, "updated_at", datetime.now(timezone.utc))
    commit_and_refresh(db, config)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_global_config",
        resource_id=1, details=payload, status="success",
    )
    return _serialize_global_config(config)


def _serialize_global_config(c: CommissionGlobalConfig) -> dict:
    return {
        "id": cast(int, getattr(c, "id")),
        "default_rate": float(getattr(c, "default_rate")),
        "low_value_threshold": float(getattr(c, "low_value_threshold")),
        "fixed_cap_amount": float(getattr(c, "fixed_cap_amount")),
        "fixed_cap_enabled": bool(getattr(c, "fixed_cap_enabled")),
        "margin_protection_enabled": bool(getattr(c, "margin_protection_enabled")),
        "margin_threshold": _float_or_none(getattr(c, "margin_threshold")),
        "updated_by": getattr(c, "updated_by"),
        "updated_at": getattr(c, "updated_at"),
        "created_at": getattr(c, "created_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Category Rates
# ══════════════════════════════════════════════════════════════════════════════

def list_category_rates(
    db: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict:
    """Return all category rates, seeding defaults on first call."""
    query = _db_commissioncategoryrate_query_10(db)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                CommissionCategoryRate.category_slug.ilike(term),
                CommissionCategoryRate.category_display_name.ilike(term),
            )
        )
    rows = query.order_by(CommissionCategoryRate.category_display_name, CommissionCategoryRate.id).all()
    if not rows:
        commission_engine.seed_defaults(db)
        query = _db_commissioncategoryrate_query_11(db)
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    CommissionCategoryRate.category_slug.ilike(term),
                    CommissionCategoryRate.category_display_name.ilike(term),
                )
            )
        rows = query.order_by(CommissionCategoryRate.category_display_name, CommissionCategoryRate.id).all()
    total = len(rows)
    resolved_limit = total if limit is None else max(1, min(limit, 500))
    sliced_rows = rows[max(0, offset):max(0, offset) + resolved_limit]
    return _build_list_page_payload([_serialize_category_rate(row) for row in sliced_rows], total, offset=offset, page_size=resolved_limit)


def update_category_rate(
    category_slug: str, payload: dict, acting_user: dict, db: Session
) -> dict:
    _require_admin(acting_user)
    row = _db_commissioncategoryrate_first_12(db, category_slug)


    if not row:
        raise HTTPException(status_code=404, detail=f"Category rate not found: {category_slug}")

    if "rate" in payload:
        r = float(payload["rate"])
        if not (0.0 <= r <= 1.0):
            raise HTTPException(status_code=422, detail="Rate must be between 0.0 and 1.0")
        setattr(row, "rate", Decimal(str(r)))
    if "is_active" in payload:
        setattr(row, "is_active", bool(payload["is_active"]))
    if "notes" in payload:
        setattr(row, "notes", payload["notes"])
    if "category_display_name" in payload:
        setattr(row, "category_display_name", payload["category_display_name"])

    setattr(row, "updated_by", acting_user["id"])
    setattr(row, "updated_at", datetime.now(timezone.utc))
    commit_and_refresh(db, row)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_category_rate",
        resource_id=cast(int, getattr(row, "id")), details={"category_slug": category_slug, **payload}, status="success",
    )
    return _serialize_category_rate(row)


def _serialize_category_rate(r: CommissionCategoryRate) -> dict:
    return {
        "id": cast(int, getattr(r, "id")),
        "category_id": getattr(r, "category_id"),
        "category_slug": str(getattr(r, "category_slug")),
        "category_display_name": str(getattr(r, "category_display_name")),
        "rate": float(getattr(r, "rate_percent", 0) or 0),
        "is_active": bool(getattr(r, "is_active")),
        "notes": getattr(r, "notes", None),
        "country_code": getattr(r, "country_code"),
        "created_at": getattr(r, "created_at"),
        "updated_at": getattr(r, "updated_at", None),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Badge Tiers
# ══════════════════════════════════════════════════════════════════════════════

def list_badge_tiers(
    db: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict:
    query = _db_commissionbadgetier_query_13(db)
    if search and search.strip():
        query = query.filter(CommissionBadgeTier.badge_level.ilike(f"%{search.strip()}%"))
    rows = query.order_by(CommissionBadgeTier.sort_order, CommissionBadgeTier.id).all()
    if not rows:
        commission_engine.seed_defaults(db)
        query = _db_commissionbadgetier_query_14(db)
        if search and search.strip():
            query = query.filter(CommissionBadgeTier.badge_level.ilike(f"%{search.strip()}%"))
        rows = query.order_by(CommissionBadgeTier.sort_order, CommissionBadgeTier.id).all()
    total = len(rows)
    resolved_limit = total if limit is None else max(1, min(limit, 500))
    sliced_rows = rows[max(0, offset):max(0, offset) + resolved_limit]
    return _build_list_page_payload([_serialize_badge_tier(row) for row in sliced_rows], total, offset=offset, page_size=resolved_limit)


def update_badge_tier(
    badge_level: str, payload: dict, acting_user: dict, db: Session
) -> dict:
    _require_admin(acting_user)
    row = _db_commissionbadgetier_first_15(db, badge_level)


    if not row:
        raise HTTPException(status_code=404, detail=f"Badge tier not found: {badge_level}")

    if "commission_rate" in payload:
        r = float(payload["commission_rate"])
        if not (0.0 <= r <= 1.0):
            raise HTTPException(status_code=422, detail="commission_rate must be between 0.0 and 1.0")
        setattr(row, "commission_rate", Decimal(str(r)))
    for field in ("setup_fee", "recurring_fee"):
        if field in payload:
            if float(payload[field]) < 0:
                raise HTTPException(status_code=422, detail=f"{field} must be >= 0")
            setattr(row, field, Decimal(str(payload[field])))
    for field in ("recurring_interval", "benefits_json", "is_active", "sort_order",
                  "min_fulfilled_orders"):
        if field in payload:
            setattr(row, field, payload[field])
    if "min_monthly_revenue" in payload:
        setattr(
            row,
            "min_monthly_revenue",
            None if payload["min_monthly_revenue"] is None else Decimal(str(payload["min_monthly_revenue"])),
        )

    setattr(row, "updated_by", acting_user["id"])
    setattr(row, "updated_at", datetime.now(timezone.utc))
    commit_and_refresh(db, row)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_badge_tier",
        resource_id=cast(int, getattr(row, "id")), details={"badge_level": badge_level, **payload}, status="success",
    )
    return _serialize_badge_tier(row)


def _serialize_badge_tier(t: CommissionBadgeTier) -> dict:
    import json as _json
    benefits = None
    raw_benefits = getattr(t, "benefits_json")
    if raw_benefits not in (None, ""):
        try:
            benefits = _json.loads(str(raw_benefits))
        except Exception:
            benefits = raw_benefits
    return {
        "id": cast(int, getattr(t, "id")),
        "badge_level": str(getattr(t, "badge_level")),
        "commission_rate": float(getattr(t, "commission_rate")),
        "setup_fee": float(getattr(t, "setup_fee")),
        "recurring_fee": float(getattr(t, "recurring_fee")),
        "recurring_interval": getattr(t, "recurring_interval"),
        "benefits": benefits,
        "min_fulfilled_orders": getattr(t, "min_fulfilled_orders"),
        "min_monthly_revenue": _float_or_none(getattr(t, "min_monthly_revenue")),
        "sort_order": getattr(t, "sort_order"),
        "is_active": bool(getattr(t, "is_active")),
        "updated_by": getattr(t, "updated_by"),
        "created_at": getattr(t, "created_at"),
        "updated_at": getattr(t, "updated_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Ledger
# ══════════════════════════════════════════════════════════════════════════════

def list_ledger_entries(
    db: Session,
    supplier_id: Optional[int] = None,
    order_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = _db_commissionledgerentry_query_16(db)
    if supplier_id:
        q = q.filter(CommissionLedgerEntry.supplier_id == supplier_id)
    if order_id:
        q = q.filter(CommissionLedgerEntry.order_id == order_id)
    total = q.count()
    rows = q.order_by(CommissionLedgerEntry.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [_serialize_ledger_entry(e) for e in rows]}


def create_ledger_adjustment(
    ledger_id: int, new_amount: float, reason: str, acting_user: dict, db: Session
) -> dict:
    """Create an adjustment entry when a dispute is resolved."""
    _require_admin(acting_user)
    original = _db_commissionledgerentry_first_17(db, id, ledger_id)
    if not original:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    if bool(getattr(original, "is_adjusted")):
        raise HTTPException(status_code=409, detail="Entry already adjusted")

    now = datetime.now(timezone.utc)
    setattr(original, "is_adjusted", True)
    setattr(original, "adjusted_by", acting_user["id"])
    setattr(original, "adjusted_at", now)
    setattr(original, "adjustment_reason", reason)
    setattr(original, "original_commission_amount", getattr(original, "commission_amount"))
    setattr(original, "commission_amount", Decimal(str(new_amount)))
    commit_and_refresh(db, original)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_ledger_entry",
        resource_id=ledger_id,
        details={"new_amount": new_amount, "reason": reason},
        status="success",
    )
    return _serialize_ledger_entry(original)


def _serialize_ledger_entry(e: CommissionLedgerEntry) -> dict:
    return {
        "id": cast(int, getattr(e, "id")),
        "order_id": cast(int, getattr(e, "order_id")),
        "order_item_id": getattr(e, "order_item_id"),
        "supplier_id": cast(int, getattr(e, "supplier_id")),
        "product_id": getattr(e, "product_id"),
        "category_slug": getattr(e, "category_slug"),
        "badge_level": getattr(e, "badge_level"),
        "global_default_rate": _float_or_none(getattr(e, "global_default_rate")),
        "category_rate": _float_or_none(getattr(e, "category_rate")),
        "badge_rate": _float_or_none(getattr(e, "badge_rate")),
        "override_rate": _float_or_none(getattr(e, "override_rate")),
        "applied_rate": float(getattr(e, "applied_rate")),
        "calculation_method": str(getattr(e, "calculation_method")),
        "order_value": float(getattr(e, "order_value")),
        "commission_pct": float(getattr(e, "commission_pct")),
        "cap_applied": bool(getattr(e, "cap_applied")),
        "commission_amount": float(getattr(e, "commission_amount")),
        "low_value_threshold_used": _float_or_none(getattr(e, "low_value_threshold_used")),
        "fixed_cap_used": _float_or_none(getattr(e, "fixed_cap_used")),
        "override_flag": bool(getattr(e, "override_flag")),
        "is_adjusted": bool(getattr(e, "is_adjusted")),
        "adjusted_by": getattr(e, "adjusted_by"),
        "adjusted_at": getattr(e, "adjusted_at", getattr(e, "created_at", None)),
        "adjustment_reason": getattr(e, "adjustment_reason", None),
        "original_commission_amount": _float_or_none(getattr(e, "original_commission_amount", getattr(e, "amount", None))),
        "currency": str(getattr(e, "currency")),
        "created_at": getattr(e, "created_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Preview Calculator (no DB writes)
# ══════════════════════════════════════════════════════════════════════════════

def preview_commission(
    supplier_id: int,
    order_value: float,
    category_slug: Optional[str],
    db: Session,
) -> dict:
    return commission_engine.preview_commission(
        supplier_id=supplier_id,
        order_value=order_value,
        category_slug=category_slug,
        db=db,
    )


