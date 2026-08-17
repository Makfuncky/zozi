"""Backward-compatible re-export shim for supplier badge/credibility operations.



This module intentionally performs NO imports at module-load time so it can be

imported from `controllers.supplier.supplier_controller`, `controllers.supplier.badge`

and `services.treasury.cash_management_service` without creating an import-time

circular-import cycle. Names are resolved lazily via module-level

`__getattr__`.

"""

from __future__ import annotations



import importlib

from typing import Any



_REEXPORTS: dict[str, tuple[str, str]] = {

    # Implemented in the dedicated write service (see supplier_badge_write_service).

    "record_badge_billing_payment": (

        "services.supplier.supplier_badge_write_service",

        "record_badge_billing_payment",

    ),

}





def __getattr__(name: str) -> Any:

    if name in _REEXPORTS:

        module_path, attr = _REEXPORTS[name]

        return getattr(importlib.import_module(module_path), attr)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")





from typing import Optional



from sqlalchemy import func

from sqlalchemy.orm import Session



from _legacy.models import (

    SupplierBadge,

    SupplierBadgeBillingHistory,

    SupplierBadgeCatalog,

    SupplierProfile,

)

from utils.datetime_utils import utcnow as _utcnow

import structlog

logger = structlog.get_logger(__name__)





def _level_from_score(score: float) -> str:

    if score >= 80:

        return "gold"

    if score >= 50:

        return "silver"

    return "bronze"





def list_supplier_badge_catalog(

    db: Session,

    *,

    country_code: Optional[str] = None,

    active_only: bool = True,

) -> list:

    """Return the catalogue of purchasable/earnable supplier badges."""

    q = db.query(SupplierBadgeCatalog)

    if active_only:

        q = q.filter(SupplierBadgeCatalog.is_active.is_(True))

    if country_code is not None:

        q = q.filter(SupplierBadgeCatalog.country_code == country_code)

    return q.order_by(SupplierBadgeCatalog.price.asc()).all()





def list_supplier_badge_billing_history(

    db: Session,

    *,

    supplier_id: Optional[int] = None,

    country_code: Optional[str] = None,

    limit: int = 100,

) -> list:

    """Return badge billing history, optionally scoped to a supplier/country."""

    q = db.query(SupplierBadgeBillingHistory)

    if supplier_id is not None:

        q = q.filter(SupplierBadgeBillingHistory.supplier_id == supplier_id)

    if country_code is not None:

        q = q.filter(SupplierBadgeBillingHistory.country_code == country_code)

    return q.order_by(SupplierBadgeBillingHistory.created_at.desc()).limit(limit).all()





def purchase_supplier_badge(

    db: Session,

    *,

    supplier_id: int,

    catalog_id: int,

    country_code: Optional[str] = None,

    billing_reference: Optional[str] = None,

    set_by: Optional[int] = None,

) -> SupplierBadge:

    """Purchase (create) a badge for a supplier and record the billing event."""

    catalog = db.get(SupplierBadgeCatalog, catalog_id)

    if catalog is None:

        raise ValueError(f"SupplierBadgeCatalog {catalog_id} not found")

    if not catalog.is_active:

        raise ValueError("Badge catalog item is not active")



    badge = SupplierBadge(

        supplier_id=supplier_id,

        catalog_id=catalog_id,

        badge_name=catalog.name,

        badge_level=catalog.badge_level,

        status="active",

        assigned_by=set_by,

        credibility_weight=catalog.credibility_weight,

        country_code=country_code or catalog.country_code,

    )

    db.add(badge)

    db.flush()



    billing = SupplierBadgeBillingHistory(

        supplier_id=supplier_id,

        badge_id=badge.id,

        catalog_id=catalog_id,

        billing_reference=billing_reference,

        charge_type="purchase",

        amount=catalog.price,

        currency=catalog.currency,

        status="pending",

        country_code=badge.country_code,

    )

    db.add(billing)

    db.commit()

    db.refresh(badge)

    return badge





def admin_set_supplier_badge(

    db: Session,

    *,

    supplier_id: int,

    badge_name: str,

    country_code: Optional[str] = None,

    status: str = "active",

    set_by: Optional[int] = None,

) -> SupplierBadge:

    """Admin-assign a badge to a supplier (no billing) and recalc credibility."""

    badge = SupplierBadge(

        supplier_id=supplier_id,

        catalog_id=None,

        badge_name=badge_name,

        badge_level=_level_from_score(0),

        status=status,

        assigned_by=set_by,

        credibility_weight=10.0,

        country_code=country_code,

    )

    db.add(badge)

    db.commit()

    db.refresh(badge)

    refresh_supplier_badge(db, supplier_id=supplier_id, country_code=country_code)

    return badge





def refresh_supplier_badge(

    db: Session,

    *,

    supplier_id: int,

    country_code: Optional[str] = None,

) -> float:

    """Recompute and persist the supplier's credibility score from active badges."""

    score = compute_credibility_score(db, supplier_id=supplier_id, country_code=country_code)

    profile = (

        db.query(SupplierProfile)

        .filter(SupplierProfile.user_id == supplier_id)

        .first()

    )

    if profile is not None:

        profile.credibility_score = score

        db.commit()

    return score





def compute_credibility_score(

    db: Session,

    *,

    supplier_id: int,

    country_code: Optional[str] = None,

) -> float:

    """Compute a 0-100 credibility score from the supplier's active badges.



    Each active badge contributes its ``credibility_weight``; the total is

    clamped to the [0, 100] range.

    """

    weight = (

        db.query(func.coalesce(func.sum(SupplierBadge.credibility_weight), 0.0))

        .filter(

            SupplierBadge.supplier_id == supplier_id,

            SupplierBadge.status == "active",

        )

    )

    if country_code is not None:

        weight = weight.filter(SupplierBadge.country_code == country_code)

    total = float(weight.scalar() or 0.0)

    return max(0.0, min(100.0, total))





def run_badge_recalculation_cycle(

    db: Session,

    *,

    country_code: Optional[str] = None,

) -> dict:

    """Recalculate credibility scores for all suppliers (or a country subset)."""

    q = db.query(SupplierProfile)

    if country_code is not None:

        q = q.filter(SupplierProfile.country_code == country_code)

    profiles = q.all()

    updated = 0

    for profile in profiles:

        if profile.user_id is None:

            continue

        score = compute_credibility_score(db, supplier_id=profile.user_id, country_code=country_code)

        profile.credibility_score = score

        updated += 1

    db.commit()

    return {"updated": updated, "as_of": _utcnow().isoformat()}

