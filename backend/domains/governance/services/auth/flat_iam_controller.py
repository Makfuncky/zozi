"""controllers.identity.iam_controller controller.

Business logic is delegated to services.identity.iam_service (routers -> controllers -> services)."""

from domains.governance.services.iam_service import _QR_SECRET_KEY
from domains.governance.services.iam_service import enroll_biometric
from domains.governance.services.iam_service import generate_physical_card
from domains.governance.services.iam_service import generate_qr_token
from domains.governance.services.iam_service import log_geo_fence_event
from domains.governance.services.iam_service import revoke_physical_card
from domains.governance.services.iam_service import validate_geo_fence
from domains.governance.services.iam_service import validate_qr_token

__all__ = [
    "_QR_SECRET_KEY", "enroll_biometric", "generate_physical_card", "generate_qr_token", "log_geo_fence_event", "revoke_physical_card",
    "validate_geo_fence", "validate_qr_token"
]
