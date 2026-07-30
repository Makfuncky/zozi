"""Admin payouts router."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from models import FinanceAutomationLog, Payout, User
from db.schemas import PayoutCreate, PayoutOut
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.datetime_utils import utcnow
from controllers.audit_controller import audit_log, AuditAction
from services.auto_payout_scheduler import (
    get_background_job_status as _get_bg_status,
    start_auto_payout_background_job as _start_bg_job,
    stop_auto_payout_background_job as _stop_bg_job,
    run_auto_payout_sweep as _run_supplier_sweep,
    run_auto_logistics_payout_sweep as _run_logistics_sweep,
)

router = APIRouter()


class PayoutVerifyRequest(BaseModel):
    note: str | None = None
    bank_reference: str | None = None
    transfer_date: str | None = None
    status: str = "verified"


@router.get("/payouts/{country_code}")
def list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


@router.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)
def create_payout(
    country_code: str = Path(..., description="ISO country code"),
    payload: PayoutCreate = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        model_cols = {c.name for c in Payout.__table__.columns}
        data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
        p = Payout(**data, country_code=country_code.upper())
        db.add(p); db.commit(); db.refresh(p)
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=p.id,
            details={"amount": str(p.amount) if p.amount else None, "method": p.method},
        )
        return p
    finally:
        clear_rls_context()


@router.get("/pending")
def list_pending_payouts(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all pending payouts (RLS-scoped if context is set)."""
    q = db.query(Payout).filter(Payout.status == "pending")
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


@router.get("/payouts/{country_code}/pending")
def list_pending_payouts_by_country(
    country_code: str = Path(..., description="ISO country code"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List pending payouts for a specific country."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


@router.post("/payouts/{country_code}/{payout_id}/verify")
def verify_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    payload: PayoutVerifyRequest = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Verify a payout."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404, "Payout not found")
        p.status = payload.status if payload and payload.status else "verified"
        p.processed_at = utcnow()
        if payload:
            if payload.note:
                p.notes = payload.note
            if payload.bank_reference:
                p.reference = payload.bank_reference
        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"status": p.status, "reference": p.reference, "notes": p.notes},
        )
        return {"verified": True, "payout_id": payout_id}
    finally:
        clear_rls_context()


@router.post("/payouts/run-auto-sweep")
def run_auto_payout_sweep(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Manually trigger the auto-payout sweep for eligible settlements.

    Runs both supplier and logistics settlement sweeps:
      1. Finds pending SupplierSettlements where ``eligible_at`` has passed
         → creates Payout records + PayoutBatchItems (entity_type="supplier")
      2. Finds pending LogisticsSettlements where ``eligible_at`` has passed
         → creates LogisticsPartnerPayout records + PayoutBatchItems (entity_type="logistics")

    Returns a combined summary dict.
    """
    admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

    supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
    if supplier_result.get("status") == "error":
        raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

    logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
    if logistics_result.get("status") == "error":
        raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

    return {
        "supplier": supplier_result,
        "logistics": logistics_result,
        "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
        "status": "ok",
    }


@router.put("/payouts/{country_code}/{payout_id}/process")
def process_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.status = "paid"; p.processed_at = utcnow()
        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"status": "paid"},
        )
        return {"message": "Payout processed"}
    finally:
        clear_rls_context()


# ── Background Job Status Dashboard ─────────────────────────────────────────


@router.get("/background-job-status")
def get_background_job_status_endpoint(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Return the current state of the auto-payout background job:
    is_running, last_run_at, last_run_status, last_error, total counts,
    and recent FinanceAutomationLog entries.
    """
    status = _get_bg_status()

    # Enrich with recent history from FinanceAutomationLog
    history = (
        db.query(FinanceAutomationLog)
        .filter(
            FinanceAutomationLog.kind.in_(["auto_payout", "auto_logistics_payout"]),
        )
        .order_by(FinanceAutomationLog.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "status": status,
        "history": [
            {
                "id": h.id,
                "kind": h.kind,
                "records_processed": h.records_processed,
                "records_changed": h.records_changed,
                "detail": h.detail,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
    }


@router.post("/background-job/start")
def start_background_job(
    current_admin: User = Depends(require_admin),
):
    """Start the auto-payout scheduler background thread."""
    _start_bg_job()
    return {"status": "ok", "message": "Background job started"}


@router.post("/background-job/stop")
def stop_background_job(
    current_admin: User = Depends(require_admin),
):
    """Stop the auto-payout scheduler background thread gracefully."""
    _stop_bg_job()
    return {"status": "ok", "message": "Background job stopping"}


@router.post("/background-job/trigger")
def trigger_background_job(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Run the auto-payout sweep immediately (both supplier and logistics).

    Returns the combined sweep result.
    """
    admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

    supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
    if supplier_result.get("status") == "error":
        raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

    logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
    if logistics_result.get("status") == "error":
        raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

    # Update in-memory status after the manual trigger
    _update_bg_status_after_manual_trigger(supplier_result, logistics_result)

    return {
        "supplier": supplier_result,
        "logistics": logistics_result,
        "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
        "status": "ok",
    }


@router.post("/background-job/trigger/{kind}")
def trigger_background_job_kind(
    kind: str = Path(..., description="'supplier' or 'logistics'"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Run ONLY the supplier OR logistics sweep individually.

    Use this from the history table "Run Now" buttons to re-run a specific
    sweep type without touching the other.
    """
    if kind not in ("supplier", "logistics"):
        raise HTTPException(status_code=400, detail="kind must be 'supplier' or 'logistics'")

    admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')} — single sweep"

    if kind == "supplier":
        result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Supplier sweep failed"))
        # Update in-memory status for just supplier
        _update_bg_status_after_manual_trigger(result, {"status": "no_eligible_settlements", "processed": 0})
    else:
        result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Logistics sweep failed"))
        _update_bg_status_after_manual_trigger({"status": "no_eligible_settlements", "processed": 0}, result)

    return result


def _update_bg_status_after_manual_trigger(
    supplier_result: dict,
    logistics_result: dict,
) -> None:
    """Update the in-memory background job status after a manual trigger."""
    from services.auto_payout_scheduler import update_background_status

    supplier_status = supplier_result.get("status", "error")
    logistics_status = logistics_result.get("status", "error")
    has_error = supplier_status == "error" or logistics_status == "error"
    overall_error = supplier_result.get("error") or logistics_result.get("error") if has_error else None

    now = utcnow()
    update_background_status(
        last_run_at=now.isoformat(),
        last_run_status="error" if overall_error else "ok",
        last_error=overall_error,
        last_supplier_result=supplier_result,
        last_logistics_result=logistics_result,
        total_sweep_count=(_get_bg_status().get("total_sweep_count", 0) + 1),
        total_settlements_processed=(
            _get_bg_status().get("total_settlements_processed", 0)
            + supplier_result.get("processed", 0)
            + logistics_result.get("processed", 0)
        ),
        is_running=True,
    )
