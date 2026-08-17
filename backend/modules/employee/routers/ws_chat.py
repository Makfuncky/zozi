"""ws chat router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/ws-chat")


@router.get("/ws_chat/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "ws_chat", "prefix": "/api/v1/ws-chat"}
