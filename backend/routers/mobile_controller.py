"""Mobile router.

Thin delegating router for ``controllers.core.mobile_controller`` (biometric login,
check-in, leave-balance, expenses).

NOTE: the referenced controller module does not yet exist; this router owns its own
empty ``APIRouter`` so the app boots. Implement ``controllers.core.mobile_controller``
and replace the import once ready.
"""
from fastapi import APIRouter

router = APIRouter()
__router_prefix__ = "/api/v1"

__all__ = ["router"]
