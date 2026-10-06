"""Celery configuration for distributed task processing."""
from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_init, worker_shutdown
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue

from infrastructure.utils.config import settings

logger = get_task_logger(__name__)

# Create Celery app
celery_app = Celery(
    "zozi",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "jobs.ai_tasks",
        "jobs.periodic_tasks",
        "jobs.payout_tasks",
        "jobs.payout_sweep",
        "jobs.email_tasks",
        "jobs.event_workers",
        "jobs.fraud_monitoring",
        "jobs.ghost_order_detector",
        "jobs.data_retention",
        "jobs.reconciliation_cron",
        "jobs.bank_statement_importer",
        "jobs.ml_worker",
        "jobs.mcp_server",
        "jobs.mcp_marketplace_server",
        "jobs.fx_revaluation",
        "jobs.payroll_run",
        "jobs.accrual_reversal",
        "jobs.background_tasks",
        "jobs.video_tasks",
        "jobs.threat_feed_updater",
        "jobs.async_workers",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "jobs.ai_tasks.*": {"queue": "ml"},
        "jobs.periodic_tasks.*": {"queue": "periodic"},
        "jobs.payout_tasks.*": {"queue": "payouts"},
        "jobs.payout_sweep.*": {"queue": "payouts"},
        "jobs.email_tasks.*": {"queue": "emails"},
        "jobs.payroll_run.*": {"queue": "periodic"},
    },
    
    # Task queues with dead-letter routing for failed tasks
    task_queues=(
        Queue("ml", Exchange("ml"), routing_key="ml", queue_arguments={"x-dead-letter-routing-key": "dlq", "x-dead-letter-exchange": "dlx"}),
        Queue("periodic", Exchange("periodic"), routing_key="periodic", queue_arguments={"x-dead-letter-routing-key": "dlq", "x-dead-letter-exchange": "dlx"}),
        Queue("payouts", Exchange("payouts"), routing_key="payouts", queue_arguments={"x-dead-letter-routing-key": "dlq", "x-dead-letter-exchange": "dlx"}),
        Queue("emails", Exchange("emails"), routing_key="emails", queue_arguments={"x-dead-letter-routing-key": "dlq", "x-dead-letter-exchange": "dlx"}),
        Queue("dlq", Exchange("dlx", type="direct"), routing_key="dlq"),
    ),
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_disable_rate_limits=False,
    worker_concurrency=4,
    
    # Task execution
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,

    # Hard and soft task time limits (Law 226 / Law 296 - PERF2-025).
    # Without these a hung task holds its worker slot forever: a dead DB socket
    # or an unbounded provider call never returns, so the slot is never
    # reclaimed and the queue silently backs up.
    #
    # These are the WORKER-WIDE BACKSTOP, not a per-task override. Resolution
    # order (verified against the installed celery 5.6 / billiard 4.2.4):
    #   worker/request.py:363-364   soft_timeout=soft_time_limit or task.soft_time_limit
    #   billiard/pool.py:1495-1496  soft_timeout = soft_timeout or self.soft_timeout
    # The pool default comes from worker/worker.py:393-397, which reads these
    # two keys via app.either(). A per-task annotation (jobs.ai_tasks.*) is
    # passed explicitly and therefore wins via the `or` short-circuit, so the
    # tighter 300/240, 180/120 and 600/540 limits below are all preserved.
    #
    # Law 267 caps request time at 30s; these are worker slots, not requests,
    # so the budget is sized for the longest legitimate job in the include list
    # (payroll batch, reconciliation, FX revaluation) with headroom. The soft
    # limit fires first so the task can raise SoftTimeLimitExceeded and commit
    # or clean up; the hard limit is the backstop that guarantees the slot comes
    # back if the soft limit is ignored.
    task_soft_time_limit=1800,
    task_time_limit=1860,

    # Retry configuration with exponential backoff
    #
    # NOTE (OBS2-022 / WIRE-006): in Celery 5.6 `retry_backoff`,
    # `retry_backoff_max` and `retry_jitter` are NOT app-level configuration
    # keys. Verified: app.conf['retry_backoff'] raises KeyError, and setting
    # them via conf.update() does not reach any task attribute (celery/app/
    # task.py:325-336 `from_config` has no such mapping). They are honoured
    # ONLY per-task or through task_annotations, which is applied by
    # Task.annotate() (celery/app/task.py:390-395). So the real backoff
    # behaviour for this app is the task_annotations block below.
    #
    # The values are kept here as documentation of intent, and the effective
    # jitter is declared explicitly in the annotations so it does not depend on
    # Celery's `getattr(task, 'retry_jitter', True)` default (celery/app/
    # autoretry.py:29-30) remaining True in a future release.
    retry_backoff=True,
    retry_backoff_max=300,


    # Dead-letter queue behavior
    task_acks_on_failure_or_timeout=False,
    task_reject_on_worker_lost=True,
    
    # Result backend
    result_expires=3600,
    result_compression="gzip",
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Auto-payout sweep every hour
        "auto-payout-sweep": {
            "task": "jobs.periodic_tasks.run_auto_payout_sweep",
            "schedule": 3600.0,  # Every hour
        },
        # Finance reconciliation daily at 2 AM UTC
        "finance-reconciliation": {
            "task": "jobs.periodic_tasks.run_finance_reconciliation",
            "schedule": crontab(hour=2, minute=0),
        },
        # VAT remittance calculation on 1st of month
        "vat-remittance": {
            "task": "jobs.periodic_tasks.compute_vat_remittance",
            "schedule": crontab(day_of_month=1, hour=3, minute=0),
        },
        # Supplier statement generation monthly
        "supplier-statements": {
            "task": "jobs.periodic_tasks.generate_supplier_statements",
            "schedule": crontab(day_of_month=1, hour=4, minute=0),
        },
        # Distributor statement generation monthly
        "distributor-statements": {
            "task": "jobs.periodic_tasks.generate_distributor_statements",
            "schedule": crontab(day_of_month=1, hour=5, minute=0),
        },
        # Alert engine every 30 minutes
        "alert-engine": {
            "task": "jobs.periodic_tasks.run_alert_engine",
            "schedule": 1800.0,  # Every 30 minutes
        },
        # Clean up old background job records daily
        "cleanup-jobs": {
            "task": "jobs.periodic_tasks.cleanup_old_jobs",
            "schedule": crontab(hour=1, minute=0),
        },
        # Ghost order detection every hour
        "ghost-order-detection": {
            "task": "jobs.ghost_order_detector.detect_ghost_orders",
            "schedule": 3600.0,  # Every hour
        },
        # Clean up expired tokens daily
        "cleanup-tokens": {
            "task": "jobs.periodic_tasks.cleanup_expired_tokens",
            "schedule": crontab(hour=1, minute=30),
        },
        # Ghost employee detection nightly at 1:30 AM UTC
        "ghost-employee-detection": {
            "task": "jobs.fraud_monitoring.run_ghost_employee_detection",
            "schedule": crontab(hour=1, minute=30),
        },
        # Anomaly detection every 6 hours
        "anomaly-detection": {
            "task": "jobs.fraud_monitoring.run_anomaly_detection",
            "schedule": 21600.0,  # Every 6 hours
        },
        # FX revaluation daily at end of business day UTC
        "fx-revaluation": {
            "task": "jobs.fx_revaluation.run_fx_revaluation_task",
            "schedule": crontab(hour=23, minute=0),
        },
        # Payroll batch processing on the 1st of each month at 5 AM UTC
        "payroll-batch": {
            "task": "jobs.payroll_run.run_payroll_batch",
            "schedule": crontab(day_of_month=1, hour=5, minute=0),
        },
    },
    
    # Task annotations for specific tasks
    #
    # `retry_jitter=True` is declared EXPLICITLY on every retry-configured task
    # (OBS2-022, Law 297 "Retry + backoff | 1-2-4-8s. Jitter. Max 5"). Celery
    # applies full jitter in celery/utils/time.py:450-466
    # (get_exponential_backoff_interval(..., full_jitter=True) ->
    #  random.randrange(countdown + 1)), so retries from many workers that
    # failed at the same instant no longer re-fire in lockstep.
    #
    # These are the ONLY keys that actually change behaviour. `time_limit` and
    # `soft_time_limit` are left exactly as they were: a task_annotations '*'
    # entry would be applied last (celery/app/annotations.py:50-52 resolve_all)
    # and would RELAX these tighter limits. A '*' entry is therefore deliberately
    # NOT used; the app-level limits above are the backstop for unannotated tasks.
    task_annotations={
        "jobs.ai_tasks.remove_background": {
            "rate_limit": "10/m",
            "time_limit": 300,
            "soft_time_limit": 240,
            "retry_backoff": True,
            "retry_backoff_max": 300,
            "retry_jitter": True,
        },
        "jobs.ai_tasks.analyze_product_image": {
            "rate_limit": "20/m",
            "time_limit": 180,
            "soft_time_limit": 120,
            "retry_backoff": True,
            "retry_backoff_max": 300,
            "retry_jitter": True,
        },
        "jobs.ai_tasks.generate_angles": {
            "rate_limit": "5/m",
            "time_limit": 600,
            "soft_time_limit": 540,
            "retry_backoff": True,
            "retry_backoff_max": 300,
            "retry_jitter": True,
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "jobs.ai_tasks",
    "jobs.periodic_tasks",
    "jobs.payout_tasks",
    "jobs.payout_sweep",
    "jobs.email_tasks",
    "jobs.event_workers",
    "jobs.fraud_monitoring",
    "jobs.ghost_order_detector",
    "jobs.data_retention",
    "jobs.reconciliation_cron",
    "jobs.bank_statement_importer",
    "jobs.ml_worker",
    "jobs.mcp_server",
    "jobs.mcp_marketplace_server",
    "jobs.fx_revaluation",
    "jobs.payroll_run",
    "jobs.accrual_reversal",
    "jobs.background_tasks",
    "jobs.video_tasks",
    "jobs.threat_feed_updater",
    "jobs.async_workers",
])

# Signal handlers for worker lifecycle
@worker_init.connect
def init_worker(**kwargs):
    """Initialize worker - set up database connections, etc."""
    pass

@worker_shutdown.connect
def shutdown_worker(**kwargs):
    """Clean up on worker shutdown."""
    pass


@celery_app.task(
    bind=True,
    name="tasks.celery_app.replay_dlq",
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    time_limit=300,
    soft_time_limit=240,
    queue="periodic",
)
def replay_dlq(self, limit: int = 50) -> dict:
    """Replay failed tasks from the Celery dead-letter queue.

    Reads up to ``limit`` messages from the ``dlq`` queue and republishes
    each to its original exchange/routing_key so workers can retry them.

    Returns:
        {"status": "ok", "replayed": int, "failures": int}
    """
    replayed = 0
    failures = 0
    try:
        with celery_app.pool.acquire(block=True) as conn:
            channel = conn.channel()
            queue = channel.queue_declare("dlq", passive=True)
            message_count = queue.message_count
            for _ in range(min(limit, message_count)):
                try:
                    message = channel.basic_get("dlq", no_ack=False)
                    if message is None or message.body is None:
                        break
                    properties = message.properties or {}
                    headers = properties.get("headers", {})
                    original_routing_key = headers.get("x-original-routing-key", "periodic")
                    original_exchange = headers.get("x-original-exchange", "periodic")
                    channel.basic_publish(
                        exchange=original_exchange,
                        routing_key=original_routing_key,
                        body=message.body,
                        properties=properties,
                        declare=[Exchange(original_exchange, type="direct")],
                    )
                    channel.basic_ack(message.delivery_tag)
                    replayed += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning("DLQ replay failed for one message: %s", exc)
                    failures += 1
    except Exception as exc:  # noqa: BLE001
        logger.error("DLQ replay task failed: %s", exc)
        raise self.retry(exc=exc)

    return {"status": "ok", "replayed": replayed, "failures": failures}


if __name__ == "__main__":
    celery_app.start()
