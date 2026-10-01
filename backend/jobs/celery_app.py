"""Celery configuration for distributed task processing."""
from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_init, worker_shutdown
from kombu import Exchange, Queue

from infrastructure.utils.config import settings

# Create Celery app
celery_app = Celery(
    "zozi",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "jobs.ai_tasks",
        "jobs.periodic_tasks",
        "jobs.payout_tasks",
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
        "jobs.email_tasks.*": {"queue": "emails"},
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
    
    # Retry configuration with exponential backoff
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
        # Clean up expired tokens daily
        "cleanup-tokens": {
            "task": "jobs.periodic_tasks.cleanup_expired_tokens",
            "schedule": crontab(hour=1, minute=30),
        },
    },
    
    # Task annotations for specific tasks
    task_annotations={
        "jobs.ai_tasks.remove_background": {
            "rate_limit": "10/m",
            "time_limit": 300,
            "soft_time_limit": 240,
            "retry_backoff": True,
            "retry_backoff_max": 300,
        },
        "jobs.ai_tasks.analyze_product_image": {
            "rate_limit": "20/m",
            "time_limit": 180,
            "soft_time_limit": 120,
            "retry_backoff": True,
            "retry_backoff_max": 300,
        },
        "jobs.ai_tasks.generate_angles": {
            "rate_limit": "5/m",
            "time_limit": 600,
            "soft_time_limit": 540,
            "retry_backoff": True,
            "retry_backoff_max": 300,
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "jobs.ai_tasks",
    "jobs.periodic_tasks",
    "jobs.payout_tasks",
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

if __name__ == "__main__":
    celery_app.start()
