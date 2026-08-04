from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from data.db import get_db, SessionLocal
from data.dependencies_auth import get_current_user
from data.models import (
    FraudAlert, SystemAlert, CommandCenterView,
    User, Order, OrderItem, Product, Shipment, LogisticsPartner,
    CountryConfig, SystemHealthEvent, UserSession, ReturnRequest,
    SupportTicket,
)
from data.services_database import get_db_sync
from services.command_center_service import (
    CommandCenterService,
    get_safe_scalar,
    get_safe_fetch,
    get_safe_count,
    get_command_center_heartbeat_metrics,
    count_unresolved_fraud_alerts,
)
from utils.dependencies import require_admin

_ALLOWED_TABLES = {
    "orders", "order_items", "shipments", "users", "user_sessions",
    "employees", "system_health_events", "logistics_partners", "accounts",
    "account_balances", "products", "system_alerts", "fraud_alerts",
    "executive_news", "support_tickets", "return_requests", "search_logs",
    "supplier_profiles", "employee_work_logs", "supplier_kyc_requirements",
}


def _validate_table_name(table_name: str) -> str:
    normalized = table_name.strip().lower()
    if normalized not in _ALLOWED_TABLES:
        raise ValueError(f"Table '{table_name}' is not allowed in command center queries")
    return normalized


def safe_scalar(db: Session, sql: str, params: dict | None = None) -> Any:
    return get_safe_scalar(db, sql, params)


def safe_fetch(db: Session, sql: str, params: dict | None = None, scalar: bool = False) -> Any:
    return get_safe_fetch(db, sql, params, scalar)


def _validate_where_clause(where: str) -> str:
    """Validate WHERE clause contains only safe SQL patterns."""
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ =<>!()',:/.%+-*")
    if not all(c in allowed_chars for c in where):
        raise ValueError(f"Unsafe characters in WHERE clause")
    return where

def safe_count(db: Session, table: str, where: str = "1=1", params: dict | None = None) -> Any:
    validated_table = _validate_table_name(table)
    validated_where = _validate_where_clause(where)
    return get_safe_count(db, validated_table, validated_where, params)


router = APIRouter()


class SystemMetricsResponse(BaseModel):
    api_latency_p95: float
    api_latency_p99: float
    error_rate: float
    db_connections: int
    redis_hit_ratio: float
    active_users: int
    active_sessions: int


class TreasuryMetricsResponse(BaseModel):
    available_cash: float
    locked_cash: float
    operating_cash: float
    commission_reserve: float
    vat_liability: float
    pending_payouts: float


class CommandCenterDashboardResponse(BaseModel):
    timestamp: str
    system_metrics: SystemMetricsResponse
    treasury_metrics: TreasuryMetricsResponse
    active_alerts: list[dict[str, Any]]
    market_headlines: list[dict[str, Any]]


class FraudAlertResponse(BaseModel):
    id: int
    fraud_score: int
    triggered_rules: list[str]
    created_at: str
    status: str
    priority: str


class NewsArticleResponse(BaseModel):
    id: int
    title: str
    summary: str
    category: str
    priority: str
    country_code: Optional[str]
    published_at: str
    ai_sentiment: str


class AlertResponse(BaseModel):
    id: int
    type: str
    severity: str
    title: str
    message: str
    country_code: Optional[str]
    created_at: str


class RealtimeMetrics(BaseModel):
    latency_ms: float
    error_rate: float
    active_users: int
    cpu_usage: float
    memory_usage: float


active_connections: List[WebSocket] = []


@router.get("/admin/command-center/metrics/system", response_model=SystemMetricsResponse)
def get_system_metrics(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SystemMetricsResponse:
    try:
        health_events = CommandCenterService(db).get_system_health_events(skip=skip, limit=limit)
        latencies = [float(e.metric_value) for e in health_events if e.metric_name == "api_latency"]
        errors = [float(e.metric_value) for e in health_events if e.metric_name == "error_rate"]
        return SystemMetricsResponse(
            api_latency_p95=max(latencies) if latencies else 0.0,
            api_latency_p99=max(latencies) if latencies else 0.0,
            error_rate=sum(errors) if errors else 0.0,
            db_connections=10,
            redis_hit_ratio=0.95,
            active_users=150,
            active_sessions=200,
        )
    except Exception:
        return SystemMetricsResponse(
            api_latency_p95=0.0,
            api_latency_p99=0.0,
            error_rate=0.0,
            db_connections=10,
            redis_hit_ratio=0.95,
            active_users=150,
            active_sessions=200,
        )


@router.get("/admin/command-center/metrics/treasury", response_model=TreasuryMetricsResponse)
def get_treasury_metrics(db: Session = Depends(get_db)) -> TreasuryMetricsResponse:
    return TreasuryMetricsResponse(
        available_cash=125000.00,
        locked_cash=75000.00,
        operating_cash=50000.00,
        commission_reserve=25000.00,
        vat_liability=15000.00,
        pending_payouts=85000.00,
    )


@router.get("/admin/command-center/dashboard", response_model=CommandCenterDashboardResponse)
def get_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommandCenterDashboardResponse:
    system_metrics = get_system_metrics(db)
    treasury_metrics = get_treasury_metrics(db)
    
    alerts = CommandCenterService(db).get_unacknowledged_alerts(limit=10)
    
    active_alerts = [
        {
            "id": a.id,
            "type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "country_code": a.country_code,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]
    
    user_country = (current_user or {}).get("staff_country_codes") or ["OM"]
    user_country = user_country[0] if user_country else "OM"
    headlines = []
    try:
        articles = CommandCenterService(db).get_executive_news(limit=5)
        
        for article in articles:
            headlines.append({
                "title": article.title,
                "url": article.url or "",
                "relevance_score": 0.8,
                "sentiment": article.ai_sentiment or "neutral",
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "category": article.category,
            })
    except Exception:
        headlines = []
    
    return CommandCenterDashboardResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        system_metrics=system_metrics,
        treasury_metrics=treasury_metrics,
        active_alerts=active_alerts,
        market_headlines=headlines,
    )


@router.get("/admin/command-center/fraud-alerts", response_model=List[FraudAlertResponse])
def get_fraud_alerts(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
) -> List[FraudAlertResponse]:
    alerts = CommandCenterService(db).get_fraud_alerts(limit=limit, unresolved_only=True)
    
    return [
        FraudAlertResponse(
            id=a.id,
            fraud_score=a.fraud_score,
            triggered_rules=json.loads(a.triggered_rules) if a.triggered_rules else [],
            created_at=a.created_at.isoformat() if a.created_at else None,
            status=a.status,
            priority=a.priority,
        )
        for a in alerts
    ]


@router.get("/admin/executive-news", response_model=List[NewsArticleResponse])
def get_executive_news(
    limit: int = Query(5, le=20),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[NewsArticleResponse]:
    articles = CommandCenterService(db).get_executive_news(category=category, limit=limit)
    
    return [
        NewsArticleResponse(
            id=a.id,
            title=a.title,
            summary=a.summary or "",
            category=a.category or "general",
            priority=a.priority or "normal",
            country_code=a.country_code,
            published_at=a.published_at.isoformat() if a.published_at else None,
            ai_sentiment=a.ai_sentiment or "neutral",
        )
        for a in articles
    ]


@router.get("/admin/command-center/headlines", response_model=List[NewsArticleResponse])
def get_command_center_headlines(
    limit: int = Query(5, le=20),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[NewsArticleResponse]:
    articles = CommandCenterService(db).get_executive_news(category=category, limit=limit)
    
    return [
        NewsArticleResponse(
            id=a.id,
            title=a.title,
            summary=a.summary or "",
            category=a.category or "general",
            priority=a.priority or "normal",
            country_code=a.country_code,
            published_at=a.published_at.isoformat() if a.published_at else None,
            ai_sentiment=a.ai_sentiment or "neutral",
        )
        for a in articles
    ]


@router.post("/admin/executive-news", response_model=NewsArticleResponse, status_code=201)
def create_executive_news(
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
) -> NewsArticleResponse:
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    service = CommandCenterService(db)
    article = service.create_executive_news(payload)
    return NewsArticleResponse(
        id=article.id,
        title=article.title,
        summary=article.summary or "",
        category=article.category or "general",
        priority=article.priority or "normal",
        country_code=article.country_code,
        published_at=article.published_at.isoformat() if article.published_at else None,
        ai_sentiment=article.ai_sentiment or "neutral",
    )


@router.delete("/admin/executive-news/{news_id}")
def delete_executive_news(
    news_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = CommandCenterService(db)
    article = service.get_executive_news_by_id(news_id)
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    service.delete_executive_news(article)
    return {"message": "Deleted", "id": news_id}


@router.get("/admin/command-center/alerts", response_model=List[AlertResponse])
def get_alerts(
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[AlertResponse]:
    alerts = CommandCenterService(db).get_alerts(severity=severity, acknowledged=False, limit=20)
    
    return [
        AlertResponse(
            id=a.id,
            type=a.alert_type,
            severity=a.severity,
            title=a.title,
            message=a.message,
            country_code=a.country_code,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in alerts
    ]


@router.post("/admin/command-center/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = CommandCenterService(db)
    alert = service.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    service.resolve_alert(alert)
    return {"message": "Alert resolved", "id": alert_id}


@router.get("/admin/command-center/stats")
def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats = CommandCenterService(db).get_dashboard_stats(today_start)
    
    return {
        "users": {
            "customers": stats["customers"],
            "suppliers": stats["suppliers"],
            "employees": 12,
            "logistics_companies": stats["logistics_companies"],
            "logistics_individuals": 0,
        },
        "logistics": {
            "active": stats["active"],
            "issues": shipments,
        },
        "orders": {
            "today": orders_today,
            "pending": orders_pending,
            "delayed": shipments,
            "failed": stats["failed"],
        },
        "finance": {
            "pending_payouts": 85000.00,
            "vat_liability": 15000.00,
        },
        "fraud": {
            "events_24h": fraud_events,
            "alerts_pending": count_unresolved_fraud_alerts(db),
            "suspicious_ips": 0,
        },
        "revenue": {
            "revenue": 250000.00,
            "commission": 25000.00,
            "gmv": 300000.00,
        },
        "system": {
            "active_sessions": stats["active_sessions"],
            "window_shoppers": 45,
        },
        "trends": {"top_categories": []},
        "search": {"top_searches": []},
    }


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        message_str = json.dumps(message)
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message_str)
            except Exception:
                self.active_connections.remove(connection)


manager = ConnectionManager()


@router.websocket("/admin/command-center/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                with get_db_sync() as db:
                    now = datetime.now(timezone.utc)
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    one_hour_ago = now - timedelta(hours=1)

                    heartbeat = get_command_center_heartbeat_metrics(db, now)

                    await websocket.send_json({"type": "heartbeat", "data": heartbeat, "timestamp": now.isoformat()})
            except Exception:
                pass
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/admin/command-center/metrics/realtime", response_model=RealtimeMetrics)
def get_realtime_metrics(db: Session = Depends(get_db)) -> RealtimeMetrics:
    return RealtimeMetrics(
        latency_ms=150.5,
        error_rate=0.02,
        active_users=150,
        cpu_usage=45.0,
        memory_usage=62.0,
    )


def get_command_center(db: Session) -> CommandCenterService:
    return CommandCenterService(db)


@router.get("/admin/command-center/comprehensive")
def get_comprehensive_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    country_code: str | None = Query(None, alias="country_code"),
):
    """Single endpoint returning ALL Command Center metrics for the 6-Zone layout.
    
    Args:
        country_code: Optional ISO 2-letter country code to scope results.
            If omitted, falls back to user's staff_country_codes or "OM".
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    one_hour_ago = now - timedelta(hours=1)

    # ── Helper to safely ISO-format a value that may be datetime or str ──
    def to_iso(val) -> str | None:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.isoformat()
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val).isoformat()
            except (ValueError, TypeError):
                return str(val)
        return str(val)

    # ── Resolve effective country ──
    # Query param takes precedence; fallback to user's staff country or "OM"
    effective_country = country_code or (
        (current_user or {}).get("staff_country_codes") or ["OM"]
    )[0]

    # ── Zone 1: Heartbeat (scoped to effective_country) ──
    today_orders = safe_count(db, "orders", "created_at >= :today AND country_code = :cc", {"today": today_start, "cc": effective_country})
    today_revenue = safe_fetch(db, "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE created_at >= :today AND status NOT IN ('cancelled', 'returned') AND country_code = :cc", {"today": today_start, "cc": effective_country}, scalar=True) or 0
    today_gmv = safe_fetch(db, "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE created_at >= :today AND status NOT IN ('cancelled', 'returned') AND country_code = :cc", {"today": today_start, "cc": effective_country}, scalar=True) or 0

    delayed_count = safe_fetch(db,
        "SELECT COUNT(*) FROM shipments s JOIN orders o ON s.order_id = o.id WHERE s.status = 'delayed' AND s.estimated_delivery < :now AND o.country_code = :cc",
        {"now": now, "cc": effective_country}, scalar=True,
    ) or 0
    failed_deliveries = safe_count(db, "orders", "status = 'failed' AND created_at >= :today AND country_code = :cc", {"today": today_start, "cc": effective_country})
    buying_customers = safe_fetch(db, "SELECT COUNT(DISTINCT customer_id) FROM orders WHERE created_at >= :today AND status NOT IN ('cancelled', 'returned') AND country_code = :cc", {"today": today_start, "cc": effective_country}, scalar=True) or 0
    window_shoppers = safe_fetch(db,
        "SELECT COUNT(*) FROM user_sessions us JOIN users u ON us.user_id = u.id WHERE us.last_activity >= :active AND us.is_active = true AND u.country_code = :cc",
        {"active": now - timedelta(minutes=10), "cc": effective_country}, scalar=True,
    ) or 0
    employees_working = safe_count(db, "employees", "employment_status = 'active' AND country_code = :cc", {"cc": effective_country})
    system_issues = safe_count(db,
        "system_health_events",
        "severity IN ('error', 'critical') AND created_at >= :since",
        {"since": one_hour_ago},
    )

    # ── Zone 2: Treasury & Cash ──
    # Live ledger balances from the double-entry Chart of Accounts (global, not country-scoped)
    acct_balances = safe_fetch(db, """
        SELECT a.code, COALESCE(ab.balance, 0) as balance
        FROM accounts a
        LEFT JOIN account_balances ab ON ab.account_id = a.id AND ab.currency = 'OMR'
        WHERE a.code IN ('1010','1020','2010','2020','2030','2040','2050')
    """)
    balance_map: dict[str, float] = {str(r[0]): float(r[1]) for r in acct_balances}
    available_cash = balance_map.get("1010", 0)
    locked_cash = balance_map.get("1020", 0)
    operating_cash = available_cash + locked_cash
    commission_reserve = abs(balance_map.get("2050", 0))
    vat_liability = abs(balance_map.get("2040", 0))
    supplier_payables = abs(balance_map.get("2010", 0))
    logistics_payables = abs(balance_map.get("2020", 0))
    refund_reserve = abs(balance_map.get("2030", 0))
    pending_payouts = supplier_payables + logistics_payables

    refunds_today = safe_fetch(db,
        "SELECT COALESCE(SUM(refund_amount), 0) FROM orders WHERE created_at >= :today AND status = 'returned' AND country_code = :cc",
        {"today": today_start, "cc": effective_country}, scalar=True,
    ) or 0
    active_disputes = safe_count(db, "system_alerts", "alert_type = 'dispute' AND is_acknowledged = 0 AND country_code = :cc", {"cc": effective_country})
    return_requests = safe_count(db, "return_requests", "status = 'pending' AND country_code = :cc", {"cc": effective_country})

    # ── Zone 3: Growth & Trends (scoped to effective_country) ──
    revenue_trend = safe_fetch(db, """
        SELECT DATE(created_at) as dt,
               COALESCE(SUM(total_amount), 0) as revenue
        FROM orders
        WHERE created_at >= :since AND status NOT IN ('cancelled', 'returned') AND country_code = :cc
        GROUP BY DATE(created_at)
        ORDER BY dt ASC
    """, {"since": thirty_days_ago, "cc": effective_country})

    # country_sales stays global — it's a cross-country comparison view
    country_sales = safe_fetch(db, """
        SELECT COALESCE(u.country_code, 'Unknown') as country,
               COUNT(o.id) as orders,
               COALESCE(SUM(o.total_amount), 0) as revenue
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.created_at >= :since AND o.status NOT IN ('cancelled', 'returned')
        GROUP BY u.country_code
        ORDER BY revenue DESC
    """, {"since": thirty_days_ago})

    category_trend = safe_fetch(db, """
        SELECT COALESCE(p.category, 'Uncategorized') as category,
               COUNT(oi.id) as items_sold,
               COALESCE(SUM(oi.total_price), 0) as revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.created_at >= :since AND o.status NOT IN ('cancelled', 'returned') AND o.country_code = :cc
        GROUP BY p.category
        ORDER BY revenue DESC
        LIMIT 10
    """, {"since": thirty_days_ago, "cc": effective_country})

    top_products = safe_fetch(db, """
        SELECT p.id, p.name,
               COUNT(oi.id) as units_sold,
               COALESCE(SUM(oi.total_price), 0) as revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.created_at >= :since AND o.status NOT IN ('cancelled', 'returned') AND o.country_code = :cc
        GROUP BY p.id, p.name
        ORDER BY revenue DESC
        LIMIT 10
    """, {"since": thirty_days_ago, "cc": effective_country})

    top_searches = safe_fetch(db, """
        SELECT search_query, COUNT(*) as cnt,
               SUM(CASE WHEN zero_result THEN 1 ELSE 0 END) as zero_results
        FROM search_logs
        WHERE created_at >= :since
        GROUP BY search_query
        ORDER BY cnt DESC
        LIMIT 10
    """, {"since": seven_days_ago})

    # ── Zone 4: Demographics & Ecosystem (scoped to effective_country) ──
    user_totals = {
        "customers": safe_count(db, "users", "role = 'customer' AND is_active = true AND country_code = :cc", {"cc": effective_country}),
        "suppliers": safe_count(db, "users", "role = 'supplier' AND is_active = true AND country_code = :cc", {"cc": effective_country}),
        "employees": employees_working,
        "logistics_companies": safe_count(db, "logistics_partners", "type = 'company' AND status = 'active'"),
        "logistics_individuals": safe_count(db, "logistics_partners", "type = 'individual' AND status = 'active'"),
    }

    gender_stats = safe_fetch(db, """
        SELECT COALESCE(gender, 'unknown') as gender, COUNT(*) as cnt
        FROM users WHERE role = 'customer' AND gender IS NOT NULL AND country_code = :cc
        GROUP BY gender
    """, {"cc": effective_country})

    active_suppliers = safe_count(db, "users", "role = 'supplier' AND is_active = true AND country_code = :cc", {"cc": effective_country})
    # supplier_profiles — country_code status unknown, keeping unscoped
    supplier_issues = safe_count(db, "supplier_profiles", "verification_status = 'rejected'")
    total_products = safe_count(db, "products", "is_active = true AND country_code = :cc", {"cc": effective_country})

    # ── Operations (scoped where possible) ──
    stuck_orders = safe_count(db, "orders", "status = 'processing' AND updated_at < :stuck AND country_code = :cc", {"stuck": one_hour_ago, "cc": effective_country})
    pending_kyc = safe_count(db, "supplier_kyc_requirements", "status = 'pending'")
    product_moderation = safe_count(db, "products", "is_active = false AND country_code = :cc", {"cc": effective_country})
    open_tickets = safe_count(db, "support_tickets", "status = 'open'")
    active_logistics = safe_count(db, "logistics_partners", "status = 'active'")
    logistics_issues_count = safe_count(db, "logistics_partners", "status = 'active' AND verification_status = 'rejected'")

    # ── Alerts & News (raw SQL avoids model mismatch) ──
    active_alerts_raw = safe_fetch(db, """
        SELECT id, alert_type, severity, title, message, country_code, created_at
        FROM system_alerts WHERE COALESCE(is_acknowledged, 0) = 0 AND (country_code IS NULL OR country_code = :cc)
        ORDER BY severity DESC, created_at DESC LIMIT 10
    """, {"cc": effective_country})
    active_alerts = [
        {
            "id": r[0], "type": r[1], "severity": r[2], "title": r[3],
            "message": r[4], "country_code": r[5],
            "created_at": to_iso(r[6]),
        }
        for r in active_alerts_raw
    ]

    fraud_alerts_raw = safe_fetch(db, """
        SELECT id, fraud_score, triggered_rules, is_resolved, priority, created_at
        FROM fraud_alerts WHERE is_resolved = false
        ORDER BY created_at DESC LIMIT 10
    """)
    fraud_alerts_list = [
        {
            "id": r[0], "score": float(r[1] or 0),
            "triggered_rules": json.loads(r[2]) if r[2] else [],
            "status": "resolved" if r[3] else "active",
            "priority": r[4] or "medium",
            "created_at": to_iso(r[5]),
        }
        for r in fraud_alerts_raw
    ]

    news_headlines_raw = safe_fetch(db, """
        SELECT id, title, COALESCE(summary, ''), COALESCE(category, 'general'),
               COALESCE(ai_sentiment, 'neutral'), published_at
        FROM executive_news WHERE is_published = true AND (country_code IS NULL OR country_code = :cc)
        ORDER BY published_at DESC LIMIT 5
    """, {"cc": effective_country})
    headlines = [
        {
            "id": r[0], "title": r[1], "summary": r[2],
            "category": r[3], "sentiment": r[4],
            "published_at": to_iso(r[5]),
        }
        for r in news_headlines_raw
    ]

    # ── Workforce (scoped to effective_country) ──
    employees_by_dept = safe_fetch(db, """
        SELECT department, COUNT(*) as cnt
        FROM employees
        WHERE employment_status = 'active' AND department IS NOT NULL AND country_code = :cc
        GROUP BY department ORDER BY cnt DESC
    """, {"cc": effective_country})
    recent_hires = safe_fetch(db,
        "SELECT COUNT(*) FROM employees WHERE hire_date >= :since AND employment_status = 'active' AND country_code = :cc",
        {"since": thirty_days_ago.date(), "cc": effective_country}, scalar=True,
    ) or 0

    # ── Workforce Performance Tickers (scoped where possible) ──
    tickets_resolved_today = safe_fetch(db,
        "SELECT COUNT(*) FROM support_tickets WHERE status = 'resolved' AND updated_at >= :today",
        {"today": today_start}, scalar=True,
    ) or 0
    moderation_approved = safe_fetch(db,
        "SELECT COUNT(*) FROM products WHERE is_active = true AND country_code = :cc", {"cc": effective_country}, scalar=True,
    ) or 1
    moderation_pending = safe_fetch(db,
        "SELECT COUNT(*) FROM products WHERE is_active = false AND deleted_at IS NULL AND country_code = :cc", {"cc": effective_country}, scalar=True,
    ) or 0
    moderation_approval_rate = round(moderation_approved / (moderation_approved + moderation_pending) * 100, 1) if (moderation_approved + moderation_pending) > 0 else 0
    employees_logged_today = safe_fetch(db,
        "SELECT COUNT(DISTINCT employee_id) FROM employee_work_logs WHERE date = CURRENT_DATE AND country_code = :cc",
        {"cc": effective_country}, scalar=True,
    ) or 0
    avg_hours_logged_today = safe_fetch(db,
        "SELECT COALESCE(AVG(hours_worked), 0) FROM employee_work_logs WHERE date = CURRENT_DATE AND country_code = :cc",
        {"cc": effective_country}, scalar=True,
    ) or 0

    # System health metrics — global (infrastructure), not country-scoped
    active_sessions = safe_fetch(db,
        "SELECT COUNT(*) FROM user_sessions us JOIN users u ON us.user_id = u.id WHERE us.last_activity >= :since AND us.is_active = true AND u.country_code = :cc",
        {"since": one_hour_ago, "cc": effective_country}, scalar=True,
    ) or 0

    return {
        "timestamp": now.isoformat(),
        "heartbeat": {
            "today_orders": today_orders,
            "today_revenue": float(today_revenue),
            "today_gmv": float(today_gmv),
            "delayed_orders": delayed_count,
            "failed_deliveries": failed_deliveries,
            "active_customers_buying": buying_customers,
            "active_customers_window_shopping": window_shoppers,
            "employees_working": employees_working,
            "system_issues": system_issues,
            "active_logistics_partners": active_logistics,
            "logistics_issues": logistics_issues_count,
        },
        "treasury": {
            "available_cash": available_cash,
            "locked_cash": locked_cash,
            "operating_cash": operating_cash,
            "commission_reserve": commission_reserve,
            "vat_liability": vat_liability,
            "pending_payouts": pending_payouts,
            "supplier_payables": supplier_payables,
            "logistics_payables": logistics_payables,
            "refund_reserve": refund_reserve,
            "refunds_today": float(refunds_today),
            "active_disputes": active_disputes,
        },
        "operations": {
            "stuck_orders": stuck_orders,
            "failed_deliveries": failed_deliveries,
            "late_deliveries": delayed_count,
            "kyc_pending": pending_kyc,
            "supplier_issues": supplier_issues,
            "logistics_issues": logistics_issues_count,
            "product_moderation": product_moderation,
            "return_requests": return_requests,
            "open_tickets": open_tickets,
        },
        "ecosystem": {
            "users": user_totals,
            "total_products": total_products,
            "active_suppliers": active_suppliers,
            "supplier_issues": supplier_issues,
            "gender_stats": [{"gender": str(r[0]), "count": int(r[1])} for r in gender_stats],
        },
        "growth": {
            "revenue_trend": [{"date": str(r[0]), "revenue": float(r[1])} for r in revenue_trend],
            "country_sales": [{"country": str(r[0]), "orders": int(r[1]), "revenue": float(r[2])} for r in country_sales],
            "category_trends": [{"category": str(r[0]), "items_sold": int(r[1]), "revenue": float(r[2])} for r in category_trend],
            "top_products": [{"product_id": int(r[0]), "product_name": str(r[1]), "units_sold": int(r[2]), "revenue": float(r[3])} for r in top_products],
            "top_searches": [{"query": str(r[0]), "count": int(r[1]), "zero_results": int(r[2])} for r in top_searches],
        },
        "workforce": {
            "employees_by_department": [{"department": str(r[0] or "Unspecified"), "count": int(r[1])} for r in employees_by_dept],
            "recent_hires_30d": int(recent_hires),
            "total_employees": employees_working,
            "tickets_resolved_today": int(tickets_resolved_today),
            "moderation_approval_rate": moderation_approval_rate,
            "moderation_pending": moderation_pending,
            "employees_logged_today": int(employees_logged_today),
            "avg_hours_logged_today": float(avg_hours_logged_today),
        },
        "system": {
            "active_sessions": active_sessions,
            "api_latency": safe_fetch(db,
                "SELECT COALESCE(AVG(metric_value), 0) FROM system_health_events WHERE metric_name = 'api_latency' AND created_at >= :since",
                {"since": one_hour_ago}, scalar=True,
            ) or 0.0,
            "error_rate": safe_fetch(db,
                "SELECT COUNT(*) FROM system_health_events WHERE metric_name = 'error_rate' AND created_at >= :since",
                {"since": one_hour_ago}, scalar=True,
            ) or 0.0,
            "cpu_usage": safe_fetch(db,
                "SELECT COALESCE(AVG(metric_value), 0) FROM system_health_events WHERE metric_name = 'cpu_usage' AND created_at >= :since",
                {"since": one_hour_ago}, scalar=True,
            ) or 0.0,
            "memory_usage": safe_fetch(db,
                "SELECT COALESCE(AVG(metric_value), 0) FROM system_health_events WHERE metric_name = 'memory_usage' AND created_at >= :since",
                {"since": one_hour_ago}, scalar=True,
            ) or 0.0,
            "db_connections": 10,
            "redis_hit_ratio": 0.95,
        },
        "alerts": active_alerts,
        "fraud_alerts": fraud_alerts_list,
        "headlines": headlines,
    }

