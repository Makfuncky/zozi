"""fraud detection router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/fraud-detection")


@router.get("/fraud_detection/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "fraud_detection", "prefix": "/api/v1/fraud-detection"}
