"""suppliers domain - ORM model package init.

Re-exports the ``Base`` declarative metadata and all supplier-domain ORM model
classes so importers can use either ``from domains.suppliers.models import Base``
or ``from domains.suppliers.models import SupplierProfile`` uniformly.
"""

from infrastructure.database.base import Base  # noqa: F401

from .suppliers import (  # noqa: F401
    SupplierBadge,
    SupplierBadgeBillingHistory,
    SupplierBadgeCatalog,
    SupplierDocument,
    SupplierNotificationPreference,
    SupplierProfile,
)

__all__ = [
    "Base",
    "SupplierBadge",
    "SupplierBadgeBillingHistory",
    "SupplierBadgeCatalog",
    "SupplierDocument",
    "SupplierNotificationPreference",
    "SupplierProfile",
]
