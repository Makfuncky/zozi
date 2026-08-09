"""Unified inbox controller.

Thin orchestration between the API layer and the comms service. This satisfies
the CIR2 circuit rule (routers must call controllers, not services directly);
all DB access lives in ``services.comms.unified_inbox_service``.
"""
from __future__ import annotations

from services.comms.unified_inbox_service import (
    get_unified_inbox as _get_unified_inbox,
    reset_unified_inbox as _reset_unified_inbox,
)
import structlog
logger = structlog.get_logger(__name__)


def reset_unified_inbox(
    db,
    *,
    user_id,
    username,
    user_role,
    ip_address: str,
) -> dict:
    """Clear and re-seed unified-inbox demo data (delegates to the service)."""
    return _reset_unified_inbox(
        db,
        user_id=user_id,
        username=username,
        user_role=user_role,
        ip_address=ip_address,
    )


def get_unified_inbox(
    db,
    *,
    user_id: int,
    lens: str = "all",
    cursor=None,
    limit: int = 50,
    transport=None,
) -> dict:
    """Cursor-paginated merge of all conversation types (delegates to the service)."""
    return _get_unified_inbox(
        db,
        user_id=user_id,
        lens=lens,
        cursor=cursor,
        limit=limit,
        transport=transport,
    )
