"""
Frontend Error Reporting Endpoint
Accepts error reports from frontend clients, logs them, and optionally forwards to Sentry.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel
import structlog

from utils.ip_utils import get_request_ip
from utils.logging_config import get_request_id

logger = structlog.get_logger("frontend-errors")

router = APIRouter()


class FrontendErrorEntry(BaseModel):
    message: str
    source: str
    stack: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: str


class FrontendErrorBatch(BaseModel):
    errors: List[FrontendErrorEntry]
    user_agent: Optional[str] = None
    url: Optional[str] = None


@router.post("/api/frontend-errors")
async def report_frontend_errors(
    batch: FrontendErrorBatch,
    request: Request,
):
    request_id = get_request_id() or getattr(request.state, "request_id", "")
    client_ip = get_request_ip(request)

    for entry in batch.errors:
        logger.error(
            "frontend_error",
            request_id=request_id,
            client_ip=client_ip,
            user_agent=batch.user_agent or "",
            url=batch.url or "",
            source=entry.source,
            message=entry.message,
            stack=entry.stack or "",
            context=entry.context or {},
        )

    return {"status": "ok", "received": len(batch.errors)}
