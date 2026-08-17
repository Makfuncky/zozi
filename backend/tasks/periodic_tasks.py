"""Celery periodic tasks (replacing APScheduler)."""
from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.run_auto_payout_sweep",
    max_retries=1,
    default_retry_delay=300,
)
def run_auto_payout_sweep(self) -> dict[str, Any]:
    """
    Run auto-payout sweep for eligible supplier and logistics settlements.
    Replaces the threading-based background job.
    """
    try:
        from datetime import datetime, timezone
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.auto_payout_scheduler import run_auto_payout_sweep as run_sweep
        
        db = SessionLocal()
        try:
            # Supplier sweep
            supplier_result = run_sweep(db)
            
            # Logistics sweep
            from domains.finance.services.auto_payout_scheduler import run_auto_logistics_payout_sweep as run_logistics_sweep
            logistics_result = run_logistics_sweep(db)
            
            # Combine results
            total_processed = supplier_result.get("processed", 0) + logistics_result.get("processed", 0)
            
            logger.info(
                "Auto-payout sweep completed: suppliers=%d, logistics=%d",
                supplier_result.get("processed", 0),
                logistics_result.get("processed", 0)
            )
            
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "supplier_sweep": supplier_result,
                "logistics_sweep": logistics_result,
                "total_processed": total_processed,
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Auto-payout sweep task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.run_finance_reconciliation",
    max_retries=1,
    default_retry_delay=300,
)
def run_finance_reconciliation(self) -> dict[str, Any]:
    """Run daily finance reconciliation."""
    try:
        from datetime import datetime, timezone
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.cash_management_service import execute_finance_reconciliation_pass
        
        db = SessionLocal()
        try:
            result = execute_finance_reconciliation_pass(db)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Finance reconciliation task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.compute_vat_remittance",
    max_retries=1,
    default_retry_delay=300,
)
def compute_vat_remittance(self) -> dict[str, Any]:
    """Compute VAT remittance for the previous period."""
    try:
        from datetime import datetime, timezone, timedelta
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.automation_scheduler import compute_vat_remittance as compute_vat
        
        # Previous month
        now = datetime.now(timezone.utc)
        if now.month == 1:
            period_year = now.year - 1
            period_month = 12
        else:
            period_year = now.year
            period_month = now.month - 1
            
        db = SessionLocal()
        try:
            result = compute_vat(db, period_year=period_year, period_month=period_month)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "period_year": period_year,
                "period_month": period_month,
                "result": result,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("VAT remittance computation task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.generate_supplier_statements",
    max_retries=1,
    default_retry_delay=300,
)
def generate_supplier_statements(self) -> dict[str, Any]:
    """Generate monthly supplier statements."""
    try:
        from datetime import datetime, timezone, timedelta
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.automation_scheduler import generate_supplier_statements as gen_supplier
        
        # Previous month
        now = datetime.now(timezone.utc)
        if now.month == 1:
            period_year = now.year - 1
            period_month = 12
        else:
            period_year = now.year
            period_month = now.month - 1
            
        db = SessionLocal()
        try:
            result = gen_supplier(db, period_year=period_year, period_month=period_month)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "period_year": period_year,
                "period_month": period_month,
                "result": result,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Supplier statements generation task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.generate_distributor_statements",
    max_retries=1,
    default_retry_delay=300,
)
def generate_distributor_statements(self) -> dict[str, Any]:
    """Generate monthly distributor statements."""
    try:
        from datetime import datetime, timezone, timedelta
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.automation_scheduler import generate_distributor_statements as gen_distributor
        
        # Previous month
        now = datetime.now(timezone.utc)
        if now.month == 1:
            period_year = now.year - 1
            period_month = 12
        else:
            period_year = now.year
            period_month = now.month - 1
            
        db = SessionLocal()
        try:
            result = gen_distributor(db, period_year=period_year, period_month=period_month)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "period_year": period_year,
                "period_month": period_month,
                "result": result,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Distributor statements generation task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.run_alert_engine",
    max_retries=1,
    default_retry_delay=120,
)
def run_alert_engine(self) -> dict[str, Any]:
    """Run the alert engine to check for anomalies."""
    try:
        from datetime import datetime, timezone
        from infrastructure.database.database import SessionLocal
        from domains.finance.services.automation_scheduler import run_alert_engine as run_alerts
        
        db = SessionLocal()
        try:
            result = run_alerts(db)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Alert engine task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.cleanup_old_jobs",
    max_retries=0,
)
def cleanup_old_jobs(self) -> dict[str, Any]:
    """Clean up old background job records."""
    try:
        from datetime import datetime, timezone, timedelta
        from infrastructure.database.database import SessionLocal
        from models import FinanceAutomationLog
        
        db = SessionLocal()
        try:
            # Delete logs older than 90 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            deleted = db.query(FinanceAutomationLog).filter(
                FinanceAutomationLog.created_at < cutoff
            ).delete()
            db.commit()
            
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "deleted_count": deleted,
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.exception("Cleanup old jobs task failed: %s", exc)
        return {"status": "error", "error": str(exc)}


@shared_task(
    bind=True,
    name="tasks.periodic_tasks.cleanup_expired_tokens",
    max_retries=0,
)
def cleanup_expired_tokens(self) -> dict[str, Any]:
    """Clean up expired JWT tokens from Redis blacklist."""
    try:
        from datetime import datetime, timezone
        from infrastructure.utils.auth import _get_redis
        
        client = _get_redis()
        if not client:
            return {"status": "skipped", "reason": "Redis unavailable"}
            
        # Redis keys with TTL expire automatically, but we can clean up
        # any orphaned keys manually if needed
        # This is mostly a no-op since Redis handles TTL
        
        return {
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Redis TTL handles expiration automatically",
        }
        
    except Exception as exc:
        logger.exception("Cleanup expired tokens task failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# Health check
@shared_task(name="tasks.periodic_tasks.health_check")
def health_check() -> dict[str, str]:
    """Health check for periodic task workers."""
    return {"status": "healthy", "worker": "periodic_tasks"}

