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


__all__ = [
    "get_supplier_profile_by_user",
    "get_supplier_profile_by_id",
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
]
