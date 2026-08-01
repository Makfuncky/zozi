"""
Auto-Payout Scheduler
=====================
Background job that checks eligible SupplierSettlements AND LogisticsSettlements
whose eligible_at has passed and creates Payout / LogisticsPartnerPayout records
with a PayoutBatch for automated disbursement.

Triggers:
  - On server startup (via main.py lifespan, behind BACKGROUND_JOBS_ENABLED=1)
  - On-demand via POST /admin/payouts/run-auto-sweep

Design:
  Supplier sweep:
    1. Query all pending SupplierSettlements where eligible_at <= now() and payout_id IS NULL
    2. For each eligible settlement → create a Payout record
    3. Group created Payouts by supplier → create PayoutBatchItem per supplier
    4. Wrap everything in a single PayoutBatch (status='draft' for admin review)
    5. Update each settlement with its payout_id
    6. Log to FinanceAutomationLog
    7. Return a summary dict

  Logistics sweep (identical pattern):
    1. Query all pending LogisticsSettlements where eligible_at <= now() and payout_id IS NULL
    2. For each eligible settlement → create a LogisticsPartnerPayout record
    3. Group by partner_id → create PayoutBatchItem per partner (entity_type="logistics")
    4. Same PayoutBatch, same FinanceAutomationLog pattern

Idempotency:
  - Each settlement is processed at most once (guarded by payout_id IS NULL)
  - The entire batch is wrapped in a DB transaction
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session

from models import (
    FinanceAutomationLog,
    LogisticsPartnerPayout,
    LogisticsSettlement,
    Payout,
    PayoutBatch,
    PayoutBatchItem,
    SupplierSettlement,
)
from utils.datetime_utils import utcnow as _utcnow
from utils.money import round_money, to_decimal

logger = logging.getLogger(__name__)

# ── Settings ────────────────────────────────────────────────────────────────

# How often the background thread runs (seconds)
SWEEP_INTERVAL_SECONDS = 3600  # 1 hour

# Default holding period (days) used when settlement.eligible_at is NULL
DEFAULT_HOLDING_DAYS = 10


# ── Core sweep logic ────────────────────────────────────────────────────────


def run_auto_payout_sweep(
    db: Session,
    *,
    force_date: datetime | None = None,
    batch_notes: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Find eligible settlements and create payouts.

    Parameters
    ----------
    db : Session
        Active database session.
    force_date : datetime, optional
        Override the eligibility check for testing (defaults to now).
    batch_notes : str, optional
        Notes attached to the PayoutBatch.
    dry_run : bool, default=False
        When True, only count eligible settlements without creating records.

    Returns
    -------
    dict
        Summary with keys:
          - processed: number of settlements processed
          - total_net_amount: sum of net amounts
          - supplier_count: unique suppliers paid
          - payout_ids: list[dict] — supplier_id, payout_id, amount
          - batch_id: PayoutBatch.id (None for dry_run)
          - status: "ok", "no_eligible_settlements", or "error"
          - error: str (only on status="error")
    """
    now = force_date or _utcnow()
    try:
        # ── 1. Find eligible settlements ────────────────────────────────────
        settlements = (
            db.query(SupplierSettlement)
            .filter(
                SupplierSettlement.status == "pending",
                SupplierSettlement.payout_id.is_(None),
                SupplierSettlement.is_deleted == False,  # noqa: E712
                # eligible_at is NULL → use the created_at + default holding period
                (
                    SupplierSettlement.eligible_at.is_(None)
                    & (SupplierSettlement.created_at <= now - timedelta(days=DEFAULT_HOLDING_DAYS))
                )
                | (SupplierSettlement.eligible_at <= now),
            )
            .order_by(SupplierSettlement.supplier_id.asc(), SupplierSettlement.id.asc())
            .all()
        )

        if not settlements:
            return {
                "processed": 0,
                "total_net_amount": 0.0,
                "supplier_count": 0,
                "payout_ids": [],
                "batch_id": None,
                "status": "no_eligible_settlements",
            }

        # ── 2. Verify supplier bank accounts exist ───────────────────────────
        supplier_ids_in_scope = {cast(int, s.supplier_id) for s in settlements}
        try:
            from models.suppliers import SupplierBankAccount

            bank_accounts = (
                db.query(SupplierBankAccount.supplier_id)
                .filter(
                    SupplierBankAccount.supplier_id.in_(supplier_ids_in_scope),
                    SupplierBankAccount.is_verified == True,  # noqa: E712
                )
                .all()
            )
            verified_supplier_ids = {row[0] for row in bank_accounts}
        except Exception:
            # If SupplierBankAccount model isn't available (no migration yet),
            # proceed without bank verification.
            logger.warning("SupplierBankAccount model not available; skipping bank verification")
            verified_supplier_ids = supplier_ids_in_scope

        # Filter out suppliers without verified bank accounts
        unverified_suppliers = supplier_ids_in_scope - verified_supplier_ids
        if unverified_suppliers:
            logger.warning(
                "Skipping %d suppliers with no verified bank account: %s",
                len(unverified_suppliers),
                sorted(unverified_suppliers),
            )
            settlements = [s for s in settlements if cast(int, s.supplier_id) in verified_supplier_ids]
            if not settlements:
                return {
                    "processed": 0,
                    "total_net_amount": 0.0,
                    "supplier_count": 0,
                    "payout_ids": [],
                    "batch_id": None,
                    "status": "no_eligible_settlements",
                    "warning": f"{len(unverified_suppliers)} supplier(s) skipped: no verified bank account",
                }

        # ── 3. Group by supplier ────────────────────────────────────────────
        supplier_groups: dict[int, list[SupplierSettlement]] = {}
        for s in settlements:
            supplier_groups.setdefault(cast(int, s.supplier_id), []).append(s)

        net_by_supplier: dict[int, Decimal] = {}
        for supplier_id, group in supplier_groups.items():
            net_by_supplier[supplier_id] = sum(
                (to_decimal(s.net_amount or 0) for s in group),
                Decimal("0"),
            )

        total_net = round_money(sum(net_by_supplier.values(), Decimal("0")))

        if dry_run:
            return {
                "processed": len(settlements),
                "total_net_amount": float(total_net),
                "supplier_count": len(supplier_groups),
                "payout_ids": [
                    {"supplier_id": sid, "amount": float(amt), "settlement_count": len(supplier_groups[sid])}
                    for sid, amt in net_by_supplier.items()
                ],
                "batch_id": None,
                "status": "ok",
            }

        # ── 3. Create Payout records (one per settlement) ───────────────────
        created_payouts: list[Payout] = []
        for settlement in settlements:
            country_code = cast(str | None, settlement.country_code) or "OM"
            settlement_currency = cast(str | None, getattr(settlement, "currency", None)) or "OMR"
            payout = Payout(
                supplier_id=cast(int, settlement.supplier_id),
                order_id=cast(int | None, settlement.order_id),
                amount=round_money(to_decimal(settlement.net_amount or 0)),
                currency=settlement_currency,
                method="bank_transfer",
                status="pending",
                country_code=country_code,
                notes=f"Auto-payout from settlement #{settlement.id}",
            )
            db.add(payout)
            db.flush()  # get payout.id

            settlement.payout_id = cast(int, payout.id)
            settlement.status = "processed"
            created_payouts.append(payout)

        # Derive batch-level country_code / currency from the most common
        # values across all settlements (avoids mixing currencies in one batch).
        settlement_countries: dict[str, int] = {}
        settlement_currencies: dict[str, int] = {}
        for s in settlements:
            cc = cast(str | None, getattr(s, "country_code", None)) or "OM"
            settlement_countries[cc] = settlement_countries.get(cc, 0) + 1
            sc = cast(str | None, getattr(s, "currency", None)) or "OMR"
            settlement_currencies[sc] = settlement_currencies.get(sc, 0) + 1
        batch_country = max(settlement_countries, key=settlement_countries.get)  # type: ignore[arg-type]
        batch_currency = max(settlement_currencies, key=settlement_currencies.get)  # type: ignore[arg-type]

        # ── 4. Create PayoutBatch ───────────────────────────────────────────
        batch_number = f"APB-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        payout_batch = PayoutBatch(
            batch_number=batch_number,
            country_code=batch_country,
            total_amount=total_net,
            item_count=len(supplier_groups),
            status="draft",
            notes=batch_notes or f"Auto-payout batch for {len(settlements)} settlements",
        )
        db.add(payout_batch)
        db.flush()

        # ── 5. Create PayoutBatchItem records (one per supplier) ────────────
        for supplier_id, amt in net_by_supplier.items():
            item = PayoutBatchItem(
                batch_id=cast(int, payout_batch.id),
                entity_type="supplier",
                entity_id=supplier_id,
                amount=round_money(amt),
                currency=batch_currency,
                reference=f"Supplier #{supplier_id} — {len(supplier_groups[supplier_id])} settlement(s)",
                status="pending",
                country_code=batch_country,
            )
            db.add(item)

        # ── 6. Log to FinanceAutomationLog ──────────────────────────────────
        log_entry = FinanceAutomationLog(
            kind="auto_payout",
            records_processed=len(settlements),
            records_changed=len(created_payouts),
            detail={
                "batch_id": cast(int, payout_batch.id),
                "batch_number": batch_number,
                "supplier_count": len(supplier_groups),
                "settlement_count": len(settlements),
                "total_net_amount": float(total_net),
                "payout_ids": [cast(int, p.id) for p in created_payouts],
                "batch_country": batch_country,
                "batch_currency": batch_currency,
            },
            country_code=batch_country,
        )
        db.add(log_entry)
        db.commit()

        # ── 7. Send payout notifications ────────────────────────────────────
        notifications: list[dict[str, Any]] = []
        try:
            from services.payout_notification_service import notify_suppliers_of_payout

            summary = {
                "payout_ids": [
                    {"supplier_id": sid, "amount": float(amt), "settlement_count": len(supplier_groups[sid])}
                    for sid, amt in net_by_supplier.items()
                ],
                "batch_number": batch_number,
                "status": "ok",
            }
            notifications = notify_suppliers_of_payout(db, summary)
        except Exception as notify_exc:
            logger.exception("Failed to send payout notifications: %s", notify_exc)

        logger.info(
            "Auto-payout sweep complete: %d settlements → %d payouts "
            "for %d suppliers, batch %s (total %s OMR) — %d notifications",
            len(settlements),
            len(created_payouts),
            len(supplier_groups),
            batch_number,
            float(total_net),
            len(notifications),
        )

        return {
            "processed": len(settlements),
            "total_net_amount": float(total_net),
            "supplier_count": len(supplier_groups),
            "payout_ids": [
                {
                    "supplier_id": sid,
                    "payout_id": cast(int, p.id),
                    "amount": float(to_decimal(p.amount or 0)),
                }
                for sid, group in supplier_groups.items()
                for p in created_payouts
                if cast(int, p.supplier_id) == sid
            ],
            "batch_id": cast(int, payout_batch.id),
            "batch_number": batch_number,
            "status": "ok",
            "notifications": notifications,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Auto-payout sweep failed: %s", exc)
        return {
            "processed": 0,
            "total_net_amount": 0.0,
            "supplier_count": 0,
            "payout_ids": [],
            "batch_id": None,
            "status": "error",
            "error": str(exc),
        }


# ── Logistics payout sweep ──────────────────────────────────────────────────


def run_auto_logistics_payout_sweep(
    db: Session,
    *,
    force_date: datetime | None = None,
    batch_notes: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Find eligible LogisticsSettlements and create LogisticsPartnerPayout records.

    Mirrors ``run_auto_payout_sweep`` but for logistics partners:
      - Queries ``LogisticsSettlement`` instead of ``SupplierSettlement``
      - Creates ``LogisticsPartnerPayout`` records instead of ``Payout``
      - Groups by ``partner_id`` with ``entity_type="logistics"`` in batch items

    Parameters
    ----------
    db : Session
        Active database session.
    force_date : datetime, optional
        Override the eligibility check for testing (defaults to now).
    batch_notes : str, optional
        Notes attached to the PayoutBatch.
    dry_run : bool, default=False
        When True, only count eligible settlements without creating records.

    Returns
    -------
    dict
        Summary with keys:
          - processed: number of settlements processed
          - total_amount: sum of settlement amounts
          - partner_count: unique partners paid
          - payout_ids: list[dict] — partner_id, payout_id, amount
          - batch_id: PayoutBatch.id (None for dry_run)
          - status: "ok", "no_eligible_settlements", or "error"
    """
    now = force_date or _utcnow()
    try:
        # ── 1. Find eligible logistics settlements ──────────────────────────
        settlements = (
            db.query(LogisticsSettlement)
            .filter(
                LogisticsSettlement.status == "pending",
                LogisticsSettlement.payout_id.is_(None),
                # eligible_at is NULL → use created_at + default holding period
                (
                    LogisticsSettlement.eligible_at.is_(None)
                    & (LogisticsSettlement.created_at <= now - timedelta(days=DEFAULT_HOLDING_DAYS))
                )
                | (LogisticsSettlement.eligible_at <= now),
            )
            .order_by(LogisticsSettlement.partner_id.asc(), LogisticsSettlement.id.asc())
            .all()
        )

        if not settlements:
            return {
                "processed": 0,
                "total_amount": 0.0,
                "partner_count": 0,
                "payout_ids": [],
                "batch_id": None,
                "status": "no_eligible_settlements",
            }

        # ── 2. Verify logistics partner bank accounts exist ─────────────────
        partner_ids_in_scope = {cast(int, s.partner_id) for s in settlements}
        try:
            from models.admin import LogisticsPartnerBankAccount

            bank_accounts = (
                db.query(LogisticsPartnerBankAccount.partner_id)
                .filter(
                    LogisticsPartnerBankAccount.partner_id.in_(partner_ids_in_scope),
                    LogisticsPartnerBankAccount.is_active == True,  # noqa: E712
                )
                .all()
            )
            verified_partner_ids = {row[0] for row in bank_accounts}
        except Exception:
            logger.warning("LogisticsPartnerBankAccount model not available; skipping bank verification")
            verified_partner_ids = partner_ids_in_scope

        # Filter out partners without active bank accounts
        unverified_partners = partner_ids_in_scope - verified_partner_ids
        if unverified_partners:
            logger.warning(
                "Skipping %d partners with no active bank account: %s",
                len(unverified_partners),
                sorted(unverified_partners),
            )
            settlements = [s for s in settlements if cast(int, s.partner_id) in verified_partner_ids]
            if not settlements:
                return {
                    "processed": 0,
                    "total_amount": 0.0,
                    "partner_count": 0,
                    "payout_ids": [],
                    "batch_id": None,
                    "status": "no_eligible_settlements",
                    "warning": f"{len(unverified_partners)} partner(s) skipped: no active bank account",
                }

        # ── 3. Group by partner ─────────────────────────────────────────────
        partner_groups: dict[int, list[LogisticsSettlement]] = {}
        for s in settlements:
            partner_groups.setdefault(cast(int, s.partner_id), []).append(s)

        amount_by_partner: dict[int, Decimal] = {}
        for partner_id, group in partner_groups.items():
            amount_by_partner[partner_id] = sum(
                (to_decimal(s.amount or 0) for s in group),
                Decimal("0"),
            )

        total_amount = round_money(sum(amount_by_partner.values(), Decimal("0")))

        if dry_run:
            return {
                "processed": len(settlements),
                "total_amount": float(total_amount),
                "partner_count": len(partner_groups),
                "payout_ids": [
                    {"partner_id": pid, "amount": float(amt), "settlement_count": len(partner_groups[pid])}
                    for pid, amt in amount_by_partner.items()
                ],
                "batch_id": None,
                "status": "ok",
            }

        # ── 4. Create LogisticsPartnerPayout records ────────────────────────
        created_payouts: list[LogisticsPartnerPayout] = []
        for settlement in settlements:
            country_code = cast(str | None, settlement.country_code) or "OM"
            settlement_currency = cast(str | None, getattr(settlement, "currency", None)) or "OMR"
            payout = LogisticsPartnerPayout(
                partner_id=cast(int, settlement.partner_id),
                amount=round_money(to_decimal(settlement.amount or 0)),
                currency=settlement_currency,
                method="bank_transfer",
                status="pending",
                country_code=country_code,
                notes=f"Auto-payout from logistics settlement #{settlement.id}",
            )
            db.add(payout)
            db.flush()

            settlement.payout_id = cast(int, payout.id)
            settlement.status = "processed"
            created_payouts.append(payout)

        # Derive batch-level country_code / currency
        batch_countries: dict[str, int] = {}
        batch_currencies: dict[str, int] = {}
        for s in settlements:
            cc = cast(str | None, getattr(s, "country_code", None)) or "OM"
            batch_countries[cc] = batch_countries.get(cc, 0) + 1
            sc = cast(str | None, getattr(s, "currency", None)) or "OMR"
            batch_currencies[sc] = batch_currencies.get(sc, 0) + 1
        batch_country = max(batch_countries, key=batch_countries.get)  # type: ignore[arg-type]
        batch_currency = max(batch_currencies, key=batch_currencies.get)  # type: ignore[arg-type]

        # ── 5. Create PayoutBatch ───────────────────────────────────────────
        batch_number = f"ALB-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        payout_batch = PayoutBatch(
            batch_number=batch_number,
            country_code=batch_country,
            total_amount=total_amount,
            item_count=len(partner_groups),
            status="draft",
            notes=batch_notes or f"Auto-logistics-payout batch for {len(settlements)} settlements",
        )
        db.add(payout_batch)
        db.flush()

        # ── 6. Create PayoutBatchItem records (one per partner) ─────────────
        for partner_id, amt in amount_by_partner.items():
            item = PayoutBatchItem(
                batch_id=cast(int, payout_batch.id),
                entity_type="logistics",
                entity_id=partner_id,
                amount=round_money(amt),
                currency=batch_currency,
                reference=f"Logistics Partner #{partner_id} — {len(partner_groups[partner_id])} settlement(s)",
                status="pending",
                country_code=batch_country,
            )
            db.add(item)

        # ── 7. Log to FinanceAutomationLog ──────────────────────────────────
        log_entry = FinanceAutomationLog(
            kind="auto_logistics_payout",
            records_processed=len(settlements),
            records_changed=len(created_payouts),
            detail={
                "batch_id": cast(int, payout_batch.id),
                "batch_number": batch_number,
                "partner_count": len(partner_groups),
                "settlement_count": len(settlements),
                "total_amount": float(total_amount),
                "payout_ids": [cast(int, p.id) for p in created_payouts],
                "batch_country": batch_country,
                "batch_currency": batch_currency,
            },
            country_code=batch_country,
        )
        db.add(log_entry)
        db.commit()

        # ── 8. Send payout notifications ────────────────────────────────────
        logistics_notifications: list[dict[str, Any]] = []
        try:
            from services.payout_notification_service import notify_logistics_partners_of_payout

            summary = {
                "payout_ids": [
                    {"partner_id": pid, "amount": float(amt), "settlement_count": len(partner_groups[pid])}
                    for pid, amt in amount_by_partner.items()
                ],
                "batch_number": batch_number,
                "status": "ok",
            }
            logistics_notifications = notify_logistics_partners_of_payout(db, summary)
        except Exception as notify_exc:
            logger.exception("Failed to send logistics payout notifications: %s", notify_exc)

        logger.info(
            "Auto-logistics-payout sweep complete: %d settlements → %d payouts "
            "for %d partners, batch %s (total %s OMR) — %d notifications",
            len(settlements),
            len(created_payouts),
            len(partner_groups),
            batch_number,
            float(total_amount),
            len(logistics_notifications),
        )

        return {
            "processed": len(settlements),
            "total_amount": float(total_amount),
            "partner_count": len(partner_groups),
            "payout_ids": [
                {
                    "partner_id": pid,
                    "payout_id": cast(int, p.id),
                    "amount": float(to_decimal(p.amount or 0)),
                }
                for pid, group in partner_groups.items()
                for p in created_payouts
                if cast(int, p.partner_id) == pid
            ],
            "batch_id": cast(int, payout_batch.id),
            "batch_number": batch_number,
            "status": "ok",
            "notifications": logistics_notifications,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Auto-logistics-payout sweep failed: %s", exc)
        return {
            "processed": 0,
            "total_amount": 0.0,
            "partner_count": 0,
            "payout_ids": [],
            "batch_id": None,
            "status": "error",
            "error": str(exc),
        }


# ── Background job state (exposed for admin dashboard) ───────────────────


_auto_payout_thread: threading.Thread | None = None
_stop_event = threading.Event()
_background_status: dict[str, Any] = {
    "is_running": False,
    "is_thread_alive": False,
    "last_run_at": None,
    "last_run_status": None,
    "last_error": None,
    "total_sweep_count": 0,
    "total_settlements_processed": 0,
    "last_supplier_result": None,
    "last_logistics_result": None,
    "thread_started_at": None,
    "thread_stopped_at": None,
}
_background_status_lock = threading.Lock()


def update_background_status(**kwargs: Any) -> None:
    """Thread-safe update of the shared background-status dict.

    This is a public function exposed so the admin router can update
    in-memory state after a manual trigger (POST /background-job/trigger).
    """
    with _background_status_lock:
        _background_status.update(kwargs)


def _update_background_status(**kwargs: Any) -> None:
    """Internal alias for backward compatibility."""
    update_background_status(**kwargs)
    """Thread-safe update of the shared background-status dict."""
    with _background_status_lock:
        _background_status.update(kwargs)


def get_background_job_status() -> dict[str, Any]:
    """Return a snapshot of the background job state for the admin dashboard.

    Returns a copy so callers can't mutate internal state.
    """
    with _background_status_lock:
        snapshot = dict(_background_status)
    # Live-check the thread
    snapshot["is_thread_alive"] = (
        _auto_payout_thread is not None and _auto_payout_thread.is_alive()
    )
    return snapshot


def _update_after_sweep(
    sweep_name: str,
    result: dict[str, Any],
    status: str,
) -> None:
    """Update shared state after a background sweep run.

    Uses the lock for atomic read-modify-write to avoid race conditions
    between the supplier and logistics sweeps running sequentially.
    """
    error = result.get("error") if status == "error" else None
    processed = result.get("processed", 0)

    with _background_status_lock:
        prev_total = _background_status.get("total_settlements_processed", 0)
        prev_error = _background_status.get("last_error")
        _background_status["total_settlements_processed"] = prev_total + processed

        if sweep_name == "supplier":
            _background_status["last_supplier_result"] = result
            # Always update last_run_status — if logistics runs after and fails,
            # the logistics branch below will overwrite this
            _background_status["last_run_status"] = status
            if error:
                _background_status["last_error"] = error
        elif sweep_name == "logistics":
            _background_status["last_logistics_result"] = result
            # Overwrite the top-level status so a logistics failure is visible
            _background_status["last_run_status"] = status
            if error:
                _background_status["last_error"] = error
            elif not _background_status.get("last_error"):
                # Only clear error if neither sweep failed
                _background_status["last_error"] = None

    # ── Fire-and-forget WebSocket broadcast ────────────────────────────────
    _broadcast_sweep_completed(sweep_name=sweep_name, status=status, result=result)


def _broadcast_sweep_completed(
    sweep_name: str,
    status: str,
    result: dict[str, Any],
) -> None:
    """Broadcast a sweep-completion event to the admin dashboard via WebSocket.

    Fires from sync code; silently no-ops if no event loop is running.
    """
    try:
        from utils.websocket_manager import broadcast_background_job_update

        broadcast_background_job_update(
            {
                "event": "sweep_completed",
                "sweep_name": sweep_name,
                "status": status,
                "processed": result.get("processed", 0),
                "batch_number": result.get("batch_number"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception:
        logger.debug("Failed to broadcast sweep completion (expected if no WS connected)")


def start_auto_payout_background_job(interval_seconds: int = SWEEP_INTERVAL_SECONDS) -> None:
    """Start a daemon thread that runs both supplier and logistics payout
    sweeps periodically.

    Call this once from the application lifespan.  The thread is a daemon so it
    will be killed when the main process exits.

    Use ``BACKGROUND_JOBS_ENABLED=1`` env var (already checked in main.py) to
    gate this behind the same flag as other background jobs.
    """
    global _auto_payout_thread
    if _auto_payout_thread is not None and _auto_payout_thread.is_alive():
        logger.warning("Auto-payout background job is already running, skipping duplicate start.")
        return

    _stop_event.clear()
    _update_background_status(
        is_running=True,
        thread_started_at=datetime.now(timezone.utc).isoformat(),
        thread_stopped_at=None,
    )

    def _loop() -> None:
        logger.info("Auto-payout background job started (interval=%ds)", interval_seconds)
        # Initial run after a short delay to let the server warm up
        _run_once_with_retry(delay_before=15)
        while not _stop_event.is_set():
            if _stop_event.wait(interval_seconds):
                break
            _run_once_with_retry()

    _auto_payout_thread = threading.Thread(target=_loop, daemon=True, name="auto-payout-sweep")
    _auto_payout_thread.start()
    logger.info("Auto-payout background job thread started.")


def stop_auto_payout_background_job() -> None:
    """Signal the background thread to stop gracefully."""
    _stop_event.set()
    _update_background_status(
        is_running=False,
        thread_stopped_at=datetime.now(timezone.utc).isoformat(),
    )
    logger.info("Auto-payout background job stop requested.")


def _run_once_with_retry(delay_before: int = 0) -> None:
    """Run both supplier and logistics sweeps inside a fresh DB session."""
    if delay_before > 0:
        time.sleep(delay_before)

    try:
        from db.database import SessionLocal

        # Supplier sweep
        db = SessionLocal()
        try:
            result = run_auto_payout_sweep(db)
            status = result.get("status", "error")
            if status == "no_eligible_settlements":
                logger.debug("Supplier auto-payout sweep: no eligible settlements.")
            elif status == "ok":
                logger.info(
                    "Supplier auto-payout sweep: %d settlements → %d suppliers, batch=%s total=%s",
                    result.get("processed", 0),
                    result.get("supplier_count", 0),
                    result.get("batch_number"),
                    result.get("total_net_amount"),
                )
            else:
                logger.error("Supplier auto-payout sweep error: %s", result.get("error"))
            _update_after_sweep("supplier", result, status)
        finally:
            db.close()

        # Logistics sweep
        db = SessionLocal()
        try:
            result = run_auto_logistics_payout_sweep(db)
            status = result.get("status", "error")
            if status == "no_eligible_settlements":
                logger.debug("Logistics auto-payout sweep: no eligible settlements.")
            elif status == "ok":
                logger.info(
                    "Logistics auto-payout sweep: %d settlements → %d partners, batch=%s total=%s",
                    result.get("processed", 0),
                    result.get("partner_count", 0),
                    result.get("batch_number"),
                    result.get("total_amount"),
                )
            else:
                logger.error("Logistics auto-payout sweep error: %s", result.get("error"))
            _update_after_sweep("logistics", result, status)
        finally:
            db.close()

        _update_background_status(
            last_run_at=datetime.now(timezone.utc).isoformat(),
            total_sweep_count=_background_status.get("total_sweep_count", 0) + 1,
        )

    except Exception as exc:
        logger.exception("Auto-payout sweep runner crashed: %s", exc)
        _update_background_status(
            last_run_at=datetime.now(timezone.utc).isoformat(),
            last_run_status="error",
            last_error=str(exc),
        )
