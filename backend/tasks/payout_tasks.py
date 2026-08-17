"""Celery tasks for payout processing."""
from __future__ import annotations

import logging
from typing import Any, Optional

from celery import shared_task
from celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.payout_tasks.dispatch_payout_batch",
    max_retries=3,
    default_retry_delay=60,
)
def dispatch_payout_batch(
    self,
    batch_id: int,
    provider: str,
    dry_run: bool = True,
    owner_user_id: Optional[int] = None,
) -> dict[str, Any]:
    """
    Dispatch a payout batch to the payment provider.
    
    Args:
        batch_id: ID of the PayoutBatch to dispatch
        provider: Payment provider (stripe, tap, bank)
        dry_run: If True, only simulate the dispatch
        owner_user_id: ID of the admin user who triggered this
        
    Returns:
        Dispatch result
    """
    try:
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.cash_management_service import dispatch_payout_batch as do_dispatch
        
        db = SessionLocal()
        try:
            result = do_dispatch(db, batch_id, provider, dry_run=dry_run)
            return {
                "status": "completed",
                "batch_id": batch_id,
                "provider": provider,
                "dry_run": dry_run,
                "result": result,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Payout batch dispatch task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.payout_tasks.process_individual_payout",
    max_retries=3,
    default_retry_delay=60,
)
def process_individual_payout(
    self,
    payout_id: int,
    provider: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Process a single payout.
    
    Args:
        payout_id: ID of the Payout to process
        provider: Payment provider
        dry_run: If True, only simulate
        
    Returns:
        Processing result
    """
    try:
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.cash_management_service import process_payout as do_process
        
        db = SessionLocal()
        try:
            result = do_process(db, payout_id, provider, dry_run=dry_run)
            return {
                "status": "completed",
                "payout_id": payout_id,
                "provider": provider,
                "dry_run": dry_run,
                "result": result,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Individual payout processing task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.payout_tasks.retry_failed_payouts",
    max_retries=1,
    default_retry_delay=300,
)
def retry_failed_payouts(self) -> dict[str, Any]:
    """Retry failed payouts from the last 24 hours."""
    try:
        from datetime import datetime, timezone, timedelta
        from infrastructure.database.database import SessionLocal
        from models import Payout, PayoutStatus
        
        db = SessionLocal()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            failed_payouts = db.query(Payout).filter(
                Payout.status == PayoutStatus.FAILED,
                Payout.updated_at >= cutoff,
            ).limit(50).all()
            
            results = []
            for payout in failed_payouts:
                try:
                    # Reset to pending for retry
                    payout.status = PayoutStatus.PENDING
                    db.commit()
                    
                    # Trigger individual processing
                    from tasks.payout_tasks import process_individual_payout
                    process_individual_payout.delay(
                        payout_id=payout.id,
                        provider=payout.provider or "stripe",
                        dry_run=False,
                    )
                    results.append({"payout_id": payout.id, "status": "retry_queued"})
                except Exception as e:
                    results.append({"payout_id": payout.id, "status": "error", "error": str(e)})
                    
            return {
                "status": "completed",
                "retried_count": len(results),
                "results": results,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Retry failed payouts task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(name="tasks.payout_tasks.health_check")
def health_check() -> dict[str, str]:
    """Health check for payout task workers."""
    return {"status": "healthy", "worker": "payout_tasks"}
