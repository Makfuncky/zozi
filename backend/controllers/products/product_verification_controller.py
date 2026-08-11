"""controllers.products.product_verification_controller controller.

Business logic is delegated to services.products.product_verification_service (routers -> controllers -> services)."""

from services.products.product_verification_service import (
    ALLOWED_RESULTS, ALLOWED_TYPES, _serialize, _utcnow, bulk_update_verifications, create_verification,
    get_verification, list_verifications, logger, update_verification
)

__all__ = [
    "ALLOWED_RESULTS", "ALLOWED_TYPES", "_serialize", "_utcnow", "bulk_update_verifications", "create_verification",
    "get_verification", "list_verifications", "logger", "update_verification"
]
