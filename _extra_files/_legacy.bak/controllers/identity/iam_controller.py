"""controllers.identity.iam_controller controller.

Business logic is delegated to services.identity.iam_service (routers -> controllers -> services)."""

from services.identity.iam_service import (
    _QR_SECRET_KEY, enroll_biometric, generate_physical_card, generate_qr_token, log_geo_fence_event, revoke_physical_card,
    validate_geo_fence, validate_qr_token
)

__all__ = [
    "_QR_SECRET_KEY", "enroll_biometric", "generate_physical_card", "generate_qr_token", "log_geo_fence_event", "revoke_physical_card",
    "validate_geo_fence", "validate_qr_token"
]
