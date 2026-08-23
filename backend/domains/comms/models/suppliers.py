"""comms domain — supplier model re-export shim.

The canonical supplier model definitions now live in
``domains.suppliers.models.suppliers`` (Law 6: models belong to their owning
domain). This thin shim keeps ``from domains.comms.models.suppliers import X``
working without re-defining tables on the shared ``MetaData``.

Cross-domain import sanctioned under DOMAIN_ALLOWLIST.yaml (comms <- suppliers models).
"""
from __future__ import annotations

from domains.suppliers.models.suppliers import (  # noqa: F401
    SupplierBadge,
    SupplierBadgeBillingHistory,
    SupplierBadgeCatalog,
    SupplierDocument,
    SupplierNotificationPreference,
    SupplierProfile,
)

__all__ = [
    "SupplierBadge",
    "SupplierBadgeBillingHistory",
    "SupplierBadgeCatalog",
    "SupplierDocument",
    "SupplierNotificationPreference",
    "SupplierProfile",
]
