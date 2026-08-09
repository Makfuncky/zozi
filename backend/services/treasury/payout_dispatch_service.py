"""Payout transfer-dispatch write service.

Owns the DB write path for bulk payout transfer dispatch so the
controller/router layer stays read-only (LC1 / W1 layer contract):

* ``dispatch_transfer_batch_with_audit`` performs the writes through a
  caller-supplied session (used by the synchronous admin endpoint).
* ``run_dispatch_transfer_batch_job`` owns the session lifecycle and the
  ``commit``/``rollback`` (used by the background job enqueued from the
  controller). It is the only place here that opens a session and commits.
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.finance_transfer_service import execute_transfer_batch
from utils.audit import AuditAction, audit_log
from utils.dependencies import SessionLocal
import structlog
logger = structlog.get_logger(__name__)


def normalize_dispatch_kind(kind: str) -> tuple[str, str]:
    normalized_kind = kind.strip().lower()
    if normalized_kind not in {"supplier", "logistics"}:
        raise HTTPException(status_code=422, detail="kind must be 'supplier' or 'logistics'")
    export_type = "supplier-payout-transfers" if normalized_kind == "supplier" else "logistics-payout-transfers"
    return normalized_kind, export_type


def dispatch_transfer_batch_with_audit(
    kind: str,
    admin_user: dict,
    db: Session,
    *,
    provider: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_kind, export_type = normalize_dispatch_kind(kind)
    result = execute_transfer_batch(
        export_type,
        db=db,
        provider=provider,
        dry_run=dry_run,
    )
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_user.get("id"),
        username=admin_user.get("username"),
        user_role=admin_user.get("role"),
        resource_type=f"{normalized_kind}_payout_dispatch",
        details={
            "provider": result.get("provider"),
            "status": result.get("status"),
            "dry_run": dry_run,
            "dispatchable_count": result.get("dispatchable_count"),
            "skipped_count": result.get("skipped_count"),
            "batch_reference": result.get("batch_reference"),
        },
    )
    return result


def run_dispatch_transfer_batch_job(
    kind: str,
    admin_user: dict,
    *,
    provider: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Background-job entrypoint: owns the session lifecycle and commit."""
    session = SessionLocal()
    try:
        result = dispatch_transfer_batch_with_audit(
            kind,
            admin_user,
            session,
            provider=provider,
            dry_run=dry_run,
        )
        session.commit()
        return result
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("run_dispatch_transfer_batch_job_failed", error=str(e))
        session.rollback()
        raise
    finally:
        session.close()