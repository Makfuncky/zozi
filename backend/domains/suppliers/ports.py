"""suppliers domain - sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.suppliers.models`` or ``domains.suppliers.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).

The suppliers-domain ORM models (SupplierProfile, SupplierDocument, etc.) are
defined in ``domains.suppliers.models.suppliers`` under the ``supplier`` schema.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile


def get_supplier_profile_by_user(db: Session, user_id: int) -> Optional[SupplierProfile]:
    """Return the supplier profile for a user, or None if not found.

    Sanctioned cross-domain read: other domains call this instead of querying
    the supplier tables directly.
    """
    return (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user_id)
        .first()
    )


def get_supplier_profile_by_id(db: Session, profile_id: int) -> Optional[SupplierProfile]:
    """Return a supplier profile by its primary key, or None if not found."""
    return db.query(SupplierProfile).filter(SupplierProfile.id == profile_id).first()


def get_supplier_profile(db: Session, user_id: int) -> Optional[SupplierProfile]:
    """Return the supplier profile for a user, or None if not found.

    Alias for ``get_supplier_profile_by_user`` — some callers reference the
    shorter name. Both resolve to the same sanctioned cross-domain read.
    """
    return get_supplier_profile_by_user(db, user_id)


def list_public_suppliers(
    db: Session,
    q: str | None = None,
    country: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Return active suppliers for the customer discovery page.

    Sanctioned cross-domain read: customer module calls this instead of querying
    the supplier tables directly. No PII is exposed — only business-facing fields.
    """
    from sqlalchemy import or_

    query = db.query(SupplierProfile).filter(
        SupplierProfile.verification_status.in_(["approved", "verified"]),
        SupplierProfile.is_deleted == False,  # noqa: E712
    )
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                SupplierProfile.business_name.ilike(term),
                SupplierProfile.bio.ilike(term),
                SupplierProfile.country_code.ilike(term),
            )
        )
    if country:
        query = query.filter(SupplierProfile.country_code == country.upper())
    total = query.count()
    items = query.order_by(SupplierProfile.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": s.id,
                "business_name": s.business_name,
                "country_code": s.country_code,
                "verification_status": s.verification_status,
                "credibility_score": float(s.credibility_score) if s.credibility_score else 0,
            }
            for s in items
        ],
        "total": total,
    }


# ── sanctioned READ surface re-exports (Law 3) ─────────────────────────────
# Cross-domain consumers import these from ``domains.suppliers.ports`` instead
# of from the model modules directly. Read-only; no service logic re-exported.
from domains.suppliers.models.suppliers import (  # noqa: F401
    SupplierBadge,
    SupplierBadgeBillingHistory,
    SupplierBadgeCatalog,
    SupplierDocument,
    SupplierNotificationPreference,
)

# Service re-exports (Law 3 sanctioned cross-domain surface). Modules under
# modules/supplier import these from ``domains.suppliers.ports`` instead of
# reaching into the services tree directly.
from domains.suppliers.services.analytics.supplier_analytics_service import (  # noqa: E402, F401
    get_supplier_analytics_summary,
)
from domains.suppliers.services.profile.supplier_product_image_service import (  # noqa: E402, F401
    upload_supplier_product_image,
)
from domains.suppliers.services.profile.supplier_payouts_service import (  # noqa: E402, F401
    list_payouts,
    request_payout,
)
from domains.suppliers.services.orders.supplier_orders_service import (  # noqa: E402, F401
    get_parcel_verification_history,
    get_reference_image,
    get_supplier_label,
    list_supplier_orders,
    replace_reference_image,
    upload_parcel_proof,
    verify_parcel_proof,
)
from domains.suppliers.services.profile.supplier_bank_account_service import (  # noqa: E402, F401
    upsert_supplier_bank_account,
)
from domains.suppliers.services.bank_account_service import (  # noqa: E402, F401
    deactivate_supplier_bank_account,
)
from domains.suppliers.services.profile.supplier_bank_account_service import (  # noqa: E402, F401
    get_supplier_bank_account,
    upsert_supplier_bank_account_from_router,
)
from domains.suppliers.services.profile.supplier_profile_service import (  # noqa: E402, F401
    update_supplier_profile,
)


__all__ = [
    "get_supplier_profile_by_user",
    "get_supplier_profile_by_id",
    "list_public_suppliers",
    # model re-exports
    "SupplierBadge",
    "SupplierBadgeBillingHistory",
    "SupplierBadgeCatalog",
    "SupplierDocument",
    "SupplierNotificationPreference",
    "SupplierProfile",
    # service re-exports
    "get_supplier_analytics_summary",
    "upload_supplier_product_image",
    "list_payouts",
    "request_payout",
    "get_parcel_verification_history",
    "get_reference_image",
    "get_supplier_label",
    "list_supplier_orders",
    "replace_reference_image",
    "upload_parcel_proof",
    "verify_parcel_proof",
    "deactivate_supplier_bank_account",
    "get_supplier_bank_account",
    "upsert_supplier_bank_account_from_router",
    "update_supplier_profile",
]



