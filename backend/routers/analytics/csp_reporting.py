# CSP Reporting with SIEM Integration
# Logs CSP violations for security monitoring

import json
import logging
import hashlib
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from utils.ip_utils import get_request_ip

logger = logging.getLogger("csp-reports")

router = APIRouter()


class CSPReport(BaseModel):
    document_uri: Optional[str] = None
    violated_directive: Optional[str] = None
    effective_directive: Optional[str] = None
    original_policy: Optional[str] = None
    disposition: Optional[str] = None
    blocked_uri: Optional[str] = None
    status_code: Optional[int] = None


def _hash_ip(ip: str) -> str:
    """Hash IP for privacy while allowing correlation."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _send_to_siem(report: dict, ip_hash: str, timestamp: str) -> None:
    """Send CSP report to SIEM (Splunk, ELK, or Azure Monitor)."""
    # Log in structured format for SIEM ingestion
    log_entry = {
        "event_type": "csp_violation",
        "timestamp": timestamp,
        "ip_hash": ip_hash,
        "severity": "medium",
        "report": report,
    }
    
    # JSON log for SIEM ingestion
    logger.warning(json.dumps(log_entry))


@router.post("/csp-report")
async def csp_report(
    request: Request,
    background_tasks: BackgroundTasks,
):
    try:
        report = await request.json()
    except Exception:
        return {"status": "ok"}

    client_ip = get_request_ip(request)
    ip_hash = _hash_ip(client_ip)
    timestamp = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(_send_to_siem, report, ip_hash, timestamp)

    return {"status": "ok"}
