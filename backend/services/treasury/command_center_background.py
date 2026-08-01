from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from sqlalchemy import text

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.database import get_service_session
from models import (
    CountryConfig,
    Employee,
    LogisticsPartner,
    Order,
    ReturnRequest,
    Shipment,
    SupportTicket,
    User,
    NewsSource,
    FraudAlert,
    SystemHealthEvent,
)
from utils.config import settings
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


class CommandCenterCacheJob:
    """Background jobs for pre-calculating and caching Tier 2 metrics."""
    
    def __init__(self):
        self.redis = redis_client()
    
    async def run_all_jobs(self) -> None:
        """Run all cache update jobs."""
        logger.info("Starting Command Center cache update jobs")
        try:
            await asyncio.gather(
                self.calculate_and_cache_demographics(),
                self.calculate_and_cache_country_sales(),
                self.calculate_and_cache_search_trends(),
                self.calculate_and_cache_employee_metrics(),
                self.calculate_and_cache_fraud_metrics(),
                self.calculate_and_cache_system_health(),
                return_exceptions=True
            )
            logger.info("Completed Command Center cache update jobs")
        except Exception as e:
            logger.error(f"Error in cache update jobs: {e}")
    
    async def calculate_and_cache_demographics(self) -> None:
        """Calculate and cache demographic data."""
        with get_service_session() as db:
            try:
                gender_result = db.execute(text(
                    """
                    SELECT 
                        'unknown' as gender, 
                        COUNT(*) as count
                    FROM users 
                    WHERE role = 'customer'
                    """
                )).fetchall()
                
                country_result = db.execute(text(
                    """
                    SELECT 
                        c.name as country_name,
                        COUNT(u.id) as user_count
                    FROM users u
                    JOIN country_configs c ON u.country_code = c.code
                    WHERE u.role = 'customer'
                    GROUP BY c.name
                    ORDER BY user_count DESC
                    LIMIT 10
                    """
                )).fetchall()
                
                result = {
                    "gender_stats": [{"gender": row[0], "count": row[1]} for row in gender_result],
                    "country_distribution": [{"country": row[0], "count": row[1]} for row in country_result],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.redis.setex(
                    "command_center:demographics", 
                    settings.background_job_ttl_seconds, 
                    json.dumps(result)
                )
                logger.info("Demographics cache updated")
                
            except Exception as e:
                logger.error(f"Failed to update demographics cache: {e}")
    
    @staticmethod
    def _safe_isoformat(value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.isoformat()
    
    async def calculate_and_cache_country_sales(self) -> None:
        """Calculate and cache country-wise sales trends."""
        with get_service_session() as db:
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                country_sales = db.execute(text(
                    """
                    SELECT 
                        c.name as country,
                        DATE(o.created_at) as sale_date,
                        COUNT(o.id) as order_count,
                        SUM(o.total_amount) as revenue
                    FROM orders o
                    JOIN users u ON o.user_id = u.id
                    JOIN country_configs c ON u.country_code = c.code
                    WHERE o.created_at >= :cutoff
                    GROUP BY c.name, DATE(o.created_at)
                    ORDER BY sale_date DESC
                    """
                ), {"cutoff": cutoff}).fetchall()
                
                data_by_country = {}
                for row in country_sales:
                    country, date, orders, revenue = row
                    if country not in data_by_country:
                        data_by_country[country] = []
                    data_by_country[country].append({
                        "date": self._safe_isoformat(date),
                        "orders": int(orders or 0),
                        "revenue": float(revenue or 0)
                    })
                
                result = {
                    "country_sales_trends": data_by_country,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.redis.setex(
                    "command_center:country_sales_trends", 
                    settings.background_job_ttl_seconds, 
                    json.dumps(result)
                )
                logger.info("Country sales trends cache updated")
                
            except Exception as e:
                logger.error(f"Failed to update country sales trends cache: {e}")
    
    async def calculate_and_cache_search_trends(self) -> None:
        """Calculate and cache search trends and popular queries."""
        with get_service_session() as db:
            try:
                one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                
                top_searches = db.execute(text(
                    """
                    SELECT 
                        search_query, 
                        COUNT(*) as search_count,
                        SUM(CASE WHEN zero_result = true THEN 1 ELSE 0 END) as zero_result_count
                    FROM search_logs
                    WHERE created_at >= :one_day_ago
                    GROUP BY search_query
                    ORDER BY search_count DESC
                    LIMIT 20
                    """
                ), {"one_day_ago": one_day_ago}).fetchall()
                
                zero_result_trends = db.execute(text(
                    """
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as zero_result_count
                    FROM search_logs
                    WHERE zero_result = true
                    AND created_at >= :seven_days_ago
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    """
                ), {"seven_days_ago": seven_days_ago}).fetchall()
                
                result = {
                    "top_searches": [
                        {
                            "query": row[0], 
                            "count": row[1],
                            "zero_result_count": row[2]
                        } for row in top_searches
                    ],
                    "zero_result_trends": [
                        {
                            "date": self._safe_isoformat(row[0]),
                            "count": row[1]
                        } for row in zero_result_trends
                    ],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.redis.setex(
                    "command_center:search_trends", 
                    settings.background_job_ttl_seconds, 
                    json.dumps(result)
                )
                logger.info("Search trends cache updated")
                
            except Exception as e:
                logger.error(f"Failed to update search trends cache: {e}")
    
    async def calculate_and_cache_employee_metrics(self) -> None:
        """Calculate and cache workforce metrics."""
        with get_service_session() as db:
            try:
                employees_by_country = db.execute(text(
                    """
                    SELECT 
                        c.name as country,
                        COUNT(e.id) as employee_count
                    FROM employees e
                    JOIN country_configs c ON e.country_code = c.code
                    WHERE e.employment_status = 'active'
                    GROUP BY c.name
                    ORDER BY employee_count DESC
                    """
                )).fetchall()
                
                employees_by_dept = db.execute(text(
                    """
                    SELECT 
                        department,
                        COUNT(*) as count
                    FROM employees
                    WHERE employment_status = 'active'
                    AND department IS NOT NULL
                    GROUP BY department
                    ORDER BY count DESC
                    """
                )).fetchall()
                
                thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
                recent_hires = db.execute(text(
                    """
                    SELECT COUNT(*) 
                    FROM employees 
                    WHERE hire_date >= :thirty_days_ago
                    AND employment_status = 'active'
                    """
                ), {"thirty_days_ago": thirty_days_ago}).scalar() or 0
                
                result = {
                    "employees_by_country": [
                        {"country": row[0], "count": row[1]} for row in employees_by_country
                    ],
                    "employees_by_department": [
                        {"department": row[0] or "Unspecified", "count": row[1]} for row in employees_by_dept
                    ],
                    "recent_hires_30d": int(recent_hires),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.redis.setex(
                    "command_center:employee_metrics", 
                    settings.background_job_ttl_seconds, 
                    json.dumps(result)
                )
                logger.info("Employee metrics cache updated")
                
            except Exception as e:
                logger.error(f"Failed to update employee metrics cache: {e}")
    
    async def calculate_and_cache_fraud_metrics(self) -> None:
        """Calculate and cache fraud metrics."""
        with get_service_session() as db:
            try:
                one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
                
                fraud_stats = db.execute(text(
                    """
                    SELECT 
                        COUNT(CASE WHEN fe.created_at >= :since THEN 1 END) as recent_events,
                        COUNT(CASE WHEN fe.status = 'new' THEN 1 END) as pending_alerts,
                        COUNT(CASE WHEN fe.is_flagged = true THEN 1 END) as suspicious_ips
                    FROM fraud_events fe
                    """
                ), {"since": one_hour_ago}).fetchone()
                
                result = {
                    "recent_fraud_events": int(fraud_stats[0] or 0),
                    "pending_alerts": int(fraud_stats[1] or 0),
                    "suspicious_ips": int(fraud_stats[2] or 0),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.redis.setex(
                    "command_center:fraud_metrics", 
                    300,
                    json.dumps(result)
                )
                logger.info("Fraud metrics cache updated")
                
            except Exception as e:
                logger.error(f"Failed to update fraud metrics cache: {e}")
    
    async def calculate_and_cache_system_health(self) -> None:
        """Calculate and cache system health metrics."""
        with get_service_session() as db:
            try:
                five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
                
                health_stats = db.execute(text(
                    """
                    SELECT 
                        service,
                        COUNT(CASE WHEN severity = 'error' THEN 1 END) as error_count,
                        COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_count,
                        MAX(created_at) as last_event
                    FROM system_health_events
                    WHERE created_at >= :since
                    GROUP BY service
                    """
                ), {"since": five_minutes_ago}).fetchall()
                
                result = {
                    "services": [
                        {
                            "service": row[0],
                            "errors": row[1],
                            "warnings": row[2],
                            "last_event": row[3].isoformat() if row[3] else None
                        } for row in health_stats
                    ],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.redis.setex(
                    "command_center:system_health", 
                    300,
                    json.dumps(result)
                )
                logger.info("System health cache updated")
                
            except Exception as e:
                logger.error(f"Failed to update system health cache: {e}")


cache_job = CommandCenterCacheJob()


async def _run_finance_cycle_job() -> None:
    """Periodic finance cycle (payouts, dispatch, reconciliation)."""
    if not getattr(settings, "finance_scheduler_enabled", False):
        return
    try:
        from services.cash_management_service import run_scheduled_finance_cycle

        with get_service_session() as db:
            run_scheduled_finance_cycle(db)
        logger.info("Scheduled finance cycle completed")
    except Exception:
        logger.exception("Scheduled finance cycle failed")


async def _run_reconciliation_cycle_job() -> None:
    """Periodic bank reconciliation pass."""
    if not getattr(settings, "finance_scheduler_enabled", False):
        return
    try:
        from services.cash_management_service import run_scheduled_reconciliation_cycle

        with get_service_session() as db:
            run_scheduled_reconciliation_cycle(db)
        logger.info("Scheduled reconciliation cycle completed")
    except Exception:
        logger.exception("Scheduled reconciliation cycle failed")


def start_background_jobs() -> None:
    """Start all background jobs for Command Center caching and finance cycles."""
    if not scheduler.running:
        scheduler.add_job(
            cache_job.run_all_jobs,
            trigger=IntervalTrigger(minutes=5),
            id="command_center_cache_update",
            name="Update Command Center cache",
            replace_existing=True,
        )
        if getattr(settings, "finance_scheduler_enabled", False):
            scheduler.add_job(
                _run_finance_cycle_job,
                trigger=IntervalTrigger(minutes=getattr(settings, "finance_scheduler_interval_minutes", 60) or 60),
                id="finance_scheduled_cycle",
                name="Run scheduled finance cycle",
                replace_existing=True,
            )
            scheduler.add_job(
                _run_reconciliation_cycle_job,
                trigger=IntervalTrigger(minutes=getattr(settings, "finance_reconciliation_interval_minutes", 15) or 15),
                id="finance_reconciliation_cycle",
                name="Run scheduled reconciliation cycle",
                replace_existing=True,
            )
        scheduler.start()
        logger.info("Command Center background jobs started")
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cache_job.run_all_jobs())
        else:
            asyncio.run(cache_job.run_all_jobs())
    except RuntimeError:
        logger.info("Will run initial cache population when event loop is available")


def stop_background_jobs() -> None:
    """Stop all background jobs."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Command Center background jobs stopped")

