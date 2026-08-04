"""Enhanced Command Center Service with comprehensive metrics."""
import asyncio
import hashlib
import json
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Dict, Any

import feedparser
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from data.models import (
    User, LogisticsPartner, Order, CountryConfig,
    SystemHealthEvent, FraudAlert, NewsSource, NewsArticle,
    InternalNotice, PredictiveSimulation, AlertEscalationRule,
    ExecutiveNews
)
from data.models_employee_models import Employee
from data.services_write_helpers import (
    add_and_flush, commit_and_refresh, delete_only, commit_only,
)
from utils.config import settings
from utils.redis_client import redis_client


class WebSocketManager:
    """Manages WebSocket connections for real-time dashboard updates."""
    
    def __init__(self):
        self.rooms: Dict[str, List] = {}
        self.user_subscriptions: Dict[int, List[str]] = {}
    
    async def broadcast_to_room(self, room: str, message: dict) -> None:
        """Broadcast message to all connections in a room."""
        if room not in self.rooms:
            return
        message_str = json.dumps(message)
        for ws in list(self.rooms[room]):
            try:
                await ws.send_text(message_str)
            except Exception:
                self.rooms[room].remove(ws)
    
    async def broadcast_to_user(self, user_id: int, message: dict) -> None:
        """Broadcast message to a specific user."""
        if user_id not in self.user_subscriptions:
            return
        for room in self.user_subscriptions[user_id]:
            await self.broadcast_to_room(room, message)
    
    def subscribe_user(self, user_id: int, room: str) -> None:
        """Subscribe a user to a room."""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = []
        if room not in self.user_subscriptions[user_id]:
            self.user_subscriptions[user_id].append(room)
        if room not in self.rooms:
            self.rooms[room] = []
        if hasattr(self, '_ws_instances'):
            pass
    
    def unsubscribe_user(self, user_id: int, room: str) -> None:
        """Unsubscribe a user from a room."""
        if user_id in self.user_subscriptions:
            if room in self.user_subscriptions[user_id]:
                self.user_subscriptions[user_id].remove(room)


websocket_manager = WebSocketManager()


def get_safe_scalar(db: Session, sql: str, params: dict | None = None) -> Any:
    """Execute a safe scalar SQL query."""
    try:
        return db.execute(text(sql), params or {}).scalar() or 0
    except Exception:
        return 0


def get_safe_fetch(db: Session, sql: str, params: dict | None = None, scalar: bool = False) -> Any:
    """Execute a safe fetch SQL query."""
    try:
        result = db.execute(text(sql), params or {})
        return result.scalar() if scalar else result.fetchall()
    except Exception:
        return 0 if scalar else []


def get_safe_count(db: Session, table: str, where: str, params: dict | None = None) -> Any:
    """Execute a safe count SQL query."""
    query = text("SELECT COUNT(*) FROM " + table + " WHERE " + where)
    if params:
        query = query.bindparams(**params)
    try:
        return db.execute(query).scalar() or 0
    except Exception:
        return 0


def _safe_scalar(db: Session, sql: str, params: dict | None = None) -> Any:
    """Execute a safe scalar SQL query, returning 0 on any error."""
    try:
        return db.execute(text(sql), params or {}).scalar() or 0
    except Exception:
        return 0


def count_unresolved_fraud_alerts(db: Session) -> int:
    """Count fraud alerts that are not yet resolved (delegated read for router)."""
    return db.query(FraudAlert).filter(FraudAlert.is_resolved == False).count()


def get_command_center_heartbeat_metrics(
    db: Session, now: datetime
) -> dict:
    """Compute the real-time command-center heartbeat metrics (delegated reads).

    All queries are wrapped so a failure of any single metric degrades gracefully
    to 0 instead of breaking the websocket stream.
    """
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)
    active_threshold = now - timedelta(minutes=10)
    active_order = "('cancelled', 'returned')"
    return {
        "today_orders": _safe_scalar(
            db, "SELECT COUNT(*) FROM orders WHERE created_at >= :today", {"today": today_start}
        ),
        "today_revenue": float(
            _safe_scalar(
                db,
                "SELECT COALESCE(SUM(total_amount), 0) FROM orders "
                "WHERE created_at >= :today AND status NOT IN " + active_order,
                {"today": today_start},
            )
        ),
        "today_gmv": float(
            _safe_scalar(
                db,
                "SELECT COALESCE(SUM(total_amount), 0) FROM orders "
                "WHERE created_at >= :today AND status NOT IN " + active_order,
                {"today": today_start},
            )
        ),
        "delayed_orders": int(
            _safe_scalar(
                db,
                "SELECT COUNT(*) FROM shipments WHERE status = 'delayed' AND estimated_delivery < :now",
                {"now": now},
            )
        ),
        "failed_deliveries": int(
            _safe_scalar(
                db,
                "SELECT COUNT(*) FROM orders WHERE status = 'failed' AND created_at >= :today",
                {"today": today_start},
            )
        ),
        "active_customers_buying": int(
            _safe_scalar(
                db,
                "SELECT COUNT(DISTINCT customer_id) FROM orders "
                "WHERE created_at >= :today AND status NOT IN " + active_order,
                {"today": today_start},
            )
        ),
        "active_customers_window_shopping": int(
            _safe_scalar(
                db,
                "SELECT COUNT(*) FROM user_sessions WHERE last_activity >= :active AND is_active = true",
                {"active": active_threshold},
            )
        ),
        "employees_working": int(
            _safe_scalar(db, "SELECT COUNT(*) FROM employees WHERE employment_status = 'active'")
        ),
        "system_issues": int(
            _safe_scalar(
                db,
                "SELECT COUNT(*) FROM system_health_events WHERE severity IN ('error', 'critical') AND created_at >= :since",
                {"since": one_hour_ago},
            )
        ),
        "active_logistics_partners": int(
            _safe_scalar(db, "SELECT COUNT(*) FROM logistics_partners WHERE status = 'active'")
        ),
        "logistics_issues": int(
            _safe_scalar(
                db,
                "SELECT COUNT(*) FROM logistics_partners WHERE status = 'active' AND verification_status = 'rejected'",
            )
        ),
    }


class NewsAggregatorService:
    """Aggregates news from multiple sources with AI enrichment."""
    
    def __init__(self, db: Session):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_all_sources(self):
        """Fetch news from all active sources."""
        sources = self.db.query(NewsSource).filter(NewsSource.is_active == True).all()
        tasks = [self._fetch_source(source) for source in sources]
        await asyncio.gather(*tasks)
    
    async def _fetch_source(self, source: NewsSource):
        """Fetch news from a single source."""
        try:
            if source.source_type == "rss":
                await self._fetch_rss(source)
            elif source.source_type == "api":
                await self._fetch_api(source)
        except Exception as e:
            self._log_health_event("news_aggregator", "fetch_error", 1, str(e))
    
    async def _fetch_rss(self, source: NewsSource):
        """Fetch RSS feed."""
        response = await self.http_client.get(source.url)
        feed = feedparser.parse(response.text)
        
        for entry in feed.entries:
            external_id = entry.get("id", entry.get("link", ""))
            content_hash = hashlib.sha256(f"{entry.title}{entry.link}".encode()).hexdigest()
            
            existing = self.db.query(NewsArticle).filter(
                (NewsArticle.external_id == external_id) | 
                (NewsArticle.content_hash == content_hash)
            ).first()
            if existing:
                continue
            
            published_at = datetime.now(timezone.utc)
            if "published_parsed" in entry:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            article = NewsArticle(
                source_id=source.id,
                external_id=external_id,
                content_hash=content_hash,
                title=entry.title,
                summary=entry.get("summary", ""),
                content=entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
                url=entry.link,
                image_url=entry.get("top_level_image", entry.get("image", "")),
                published_at=published_at,
                country_code=self._extract_country(source, entry),
                ai_sentiment=self._detect_sentiment(entry.title + " " + entry.get("summary", "")),
                ai_tags=self._extract_tags(entry),
                is_published=True,
            )
            self.db.add(article)
        
        self.db.commit()
    
    async def _fetch_api(self, source: NewsSource):
        """Fetch from API endpoint."""
        headers = {}
        if source.api_key_required:
            headers["Authorization"] = f"Bearer {settings.NEWS_API_KEY}"
        
        response = await self.http_client.get(source.url, headers=headers)
        data = response.json()
        await self._process_api_response(source, data)
    
    async def _process_api_response(self, source: NewsSource, data: dict):
        """Process API response and store articles."""
        articles = data.get("articles", data.get("results", []))
        
        for item in articles:
            external_id = str(item.get("id", item.get("url", "")))
            content_hash = hashlib.sha256(f"{item.get('title', '')}{item.get('url', '')}".encode()).hexdigest()
            
            existing = self.db.query(NewsArticle).filter(
                (NewsArticle.external_id == external_id) | 
                (NewsArticle.content_hash == content_hash)
            ).first()
            if existing:
                continue
            
            article = NewsArticle(
                source_id=source.id,
                external_id=external_id,
                content_hash=content_hash,
                title=item.get("title", ""),
                summary=item.get("description", item.get("summary", "")),
                content=item.get("content", ""),
                url=item.get("url", ""),
                image_url=item.get("urlToImage", item.get("image", "")),
                published_at=datetime.fromisoformat(item.get("publishedAt", datetime.now(timezone.utc).isoformat())),
                country_code=self._extract_country_from_item(source, item),
                ai_sentiment=self._detect_sentiment(item.get("title", "") + " " + item.get("description", "")),
                ai_tags=self._extract_tags_from_item(item),
                is_published=True,
            )
            self.db.add(article)
        
        self.db.commit()
    
    def _extract_country(self, source: NewsSource, entry) -> Optional[str]:
        if source.category == "regulatory":
            return "GCC"
        return None
    
    def _extract_country_from_item(self, source: NewsSource, item: dict) -> Optional[str]:
        return item.get("country_code") or item.get("country") or ("GCC" if source.category == "regulatory" else None)
    
    def _detect_sentiment(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["crisis", "failure", "delay", "shortage", "ban"]):
            return "negative"
        if any(w in text_lower for w in ["opportunity", "growth", "launch", "success", "new"]):
            return "positive"
        return "neutral"
    
    def _extract_tags(self, entry) -> List[str]:
        tags = []
        if hasattr(entry, "tags"):
            tags = [tag.term for tag in entry.tags]
        if "GCC" in str(entry.title) or "GCC" in str(entry.summary):
            tags.append("GCC")
        return list(set(tags))
    
    def _extract_tags_from_item(self, item: dict) -> List[str]:
        tags = item.get("tags", [])
        if item.get("country_code"):
            tags.append(item["country_code"])
        return list(set(tags)) if isinstance(tags, list) else [tags]
    
    def _log_health_event(self, service: str, metric_name: str, value: float, message: str):
        event = SystemHealthEvent(
            service=service,
            metric_name=metric_name,
            metric_value=value,
            severity="warning",
            message=message,
        )
        self.db.add(event)
        self.db.commit()


class CommandCenterService:
    """Service for Command Center dashboard data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_comprehensive_stats(self) -> dict:
        """Get all dashboard statistics for CEO view."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        twenty_four_hours_ago = today_start - timedelta(hours=24)
        
        stats = {
            "users": self._get_user_stats(),
            "logistics": self._get_logistics_stats(),
            "orders": self._get_order_stats(today_start, twenty_four_hours_ago),
            "finance": self._get_finance_stats(),
            "fraud": self._get_fraud_stats(twenty_four_hours_ago),
            "revenue": self._get_revenue_stats(today_start),
            "trends": self._get_trend_stats(twenty_four_hours_ago),
            "search": self._get_search_stats(),
            "system": self._get_system_stats(),
        }
        return stats
    
    def _get_user_stats(self) -> dict:
        return {
            "customers": self.db.query(User).filter(User.role == "customer").count(),
            "suppliers": self.db.query(User).filter(User.role == "supplier").count(),
            "employees": self.db.query(Employee).count(),
            "logistics_companies": self.db.query(LogisticsPartner).filter(
                LogisticsPartner.partner_type == "company"
            ).count(),
            "logistics_individuals": self.db.query(LogisticsPartner).filter(
                LogisticsPartner.partner_type == "individual"
            ).count(),
        }
    
    def _get_logistics_stats(self) -> dict:
        return {
            "active": self.db.query(LogisticsPartner).filter(
                LogisticsPartner.is_active == True
            ).count(),
            "issues": self.db.query(LogisticsPartner).filter(
                LogisticsPartner.has_issues == True
            ).count(),
        }
    
    def _get_order_stats(self, today_start: datetime, twenty_four_hours_ago: datetime) -> dict:
        return {
            "today": self.db.query(Order).filter(Order.created_at >= today_start).count(),
            "pending": self.db.query(Order).filter(Order.status == "pending").count(),
            "delayed": self.db.query(Shipment).filter(
                Shipment.status == "delayed",
                Shipment.estimated_delivery < datetime.now(timezone.utc)
            ).count(),
            "failed": self.db.query(Order).filter(Order.status == "failed").count(),
        }
    
    def _get_finance_stats(self) -> dict:
        return {
            "pending_payouts": self._calculate_pending_payouts(),
            "vat_liability": self._calculate_vat_liability(),
        }
    
    def _get_fraud_stats(self, twenty_four_hours_ago: datetime) -> dict:
        return {
            "events_24h": self.db.query(FraudEvent).filter(
                FraudEvent.created_at >= twenty_four_hours_ago
            ).count(),
            "alerts_pending": self.db.query(FraudAlert).filter(
                FraudAlert.status == "new"
            ).count(),
            "suspicious_ips": self.db.query(IPAccountLinkage).filter(
                IPAccountLinkage.is_suspicious == True
            ).count(),
        }
    
    def _get_revenue_stats(self, today_start: datetime) -> dict:
        result = self.db.execute(text("""
            SELECT 
                COALESCE(SUM(total_amount), 0) as revenue,
                COALESCE(SUM(total_amount * 0.1), 0) as commission,
                COALESCE(SUM(total_amount), 0) - COALESCE(SUM(shipping_amount), 0) as gmv
            FROM orders 
            WHERE created_at >= :today AND status NOT IN ('cancelled', 'returned')
        """)).fetchone()
        return {
            "revenue": float(result[0] or 0),
            "commission": float(result[1] or 0),
            "gmv": float(result[2] or 0),
        }
    
    def _get_trend_stats(self, twenty_four_hours_ago: datetime) -> dict:
        category_result = self.db.execute(text("""
            SELECT p.category, COUNT(*) as count, SUM(o.total_amount) as revenue
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= :since
            GROUP BY p.category
            ORDER BY revenue DESC
            LIMIT 5
        """)).fetchall()
        
        return {
            "top_categories": [{"name": r[0], "orders": r[1], "revenue": float(r[2])} for r in category_result],
        }
    
    def _get_search_stats(self) -> dict:
        return {"top_searches": []}
    
    def _get_system_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        ten_min_ago = now - timedelta(minutes=10)
        return {
            "active_sessions": self.db.execute(
                text("SELECT COUNT(*) FROM user_sessions WHERE last_activity > :since"),
                {"since": one_hour_ago}
            ).scalar() or 0,
            "window_shoppers": self.db.execute(
                text("SELECT COUNT(*) FROM user_sessions WHERE last_activity > :since"),
                {"since": ten_min_ago}
            ).scalar() or 0,
        }
    
    def _calculate_pending_payouts(self) -> float:
        result = self.db.execute(text("""
            SELECT COALESCE(SUM(amount), 0) FROM payout_batch_items WHERE status = 'pending'
        """)).fetchone()
        return float(result[0] or 0)
    
    def _calculate_vat_liability(self) -> float:
        result = self.db.execute(text("""
            SELECT COALESCE(SUM(vat_amount), 0) FROM orders WHERE payment_status != 'paid' OR payment_status IS NULL
        """)).fetchone()
        return float(result[0] or 0)
    
    def get_news_articles(self, category: Optional[str] = None, limit: int = 50) -> List[NewsArticle]:
        query = self.db.query(NewsArticle).filter(NewsArticle.is_published == True)
        if category:
            query = query.filter(NewsArticle.category == category)
        return query.order_by(NewsArticle.published_at.desc()).limit(limit).all()
    
    def get_executive_news(self, category: Optional[str] = None, limit: int = 20) -> List[ExecutiveNews]:
        query = self.db.query(ExecutiveNews).filter(ExecutiveNews.published_at <= datetime.now(timezone.utc))
        if category:
            query = query.filter(ExecutiveNews.category == category)
        return query.order_by(ExecutiveNews.published_at.desc()).limit(limit).all()
    
    def get_internal_notices(self, limit: int = 10) -> List[InternalNotice]:
        return self.db.query(InternalNotice).order_by(
            InternalNotice.priority.desc(), InternalNotice.created_at.desc()
        ).limit(limit).all()
    
    def get_system_health(self, limit: int = 50) -> List[SystemHealthEvent]:
        return self.db.query(SystemHealthEvent).order_by(
            SystemHealthEvent.created_at.desc()
        ).limit(limit).all()
    
    def get_fraud_alerts(self, limit: int = 20, unresolved_only: bool = False) -> List[FraudAlert]:
        q = self.db.query(FraudAlert)
        if unresolved_only:
            q = q.filter(FraudAlert.is_resolved == False)
        else:
            q = q.filter(FraudAlert.status != "resolved")
        return q.order_by(FraudAlert.created_at.desc()).limit(limit).all()

    def get_system_health_events(self, skip: int = 0, limit: int = 50) -> List[SystemHealthEvent]:
        """Get system health events with pagination."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            self.db.query(SystemHealthEvent)
            .filter(SystemHealthEvent.created_at >= today_start)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unacknowledged_alerts(self, limit: int = 10) -> list:
        """Get unacknowledged system alerts."""
        from data.models import SystemAlert
        return (
            self.db.query(SystemAlert)
            .filter(SystemAlert.is_acknowledged == False)
            .order_by(SystemAlert.severity.desc(), SystemAlert.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_executive_news_by_id(self, news_id: int) -> ExecutiveNews | None:
        """Get an executive news article by ID."""
        return self.db.query(ExecutiveNews).filter(ExecutiveNews.id == news_id).first()

    def get_alerts(self, severity: str | None = None, acknowledged: bool | None = None, limit: int = 20) -> list:
        """Get system alerts with filters."""
        from data.models import SystemAlert
        q = self.db.query(SystemAlert).filter(SystemAlert.is_acknowledged == False)
        if severity:
            q = q.filter(SystemAlert.severity == severity)
        return q.order_by(SystemAlert.created_at.desc()).limit(limit).all()

    def get_alert_by_id(self, alert_id: int):
        """Get a system alert by ID."""
        from data.models import SystemAlert
        return self.db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()

    def create_executive_news(self, payload: dict) -> ExecutiveNews:
        """Create and persist an executive news article."""
        article = ExecutiveNews(
            title=payload.get("title"),
            summary=payload.get("summary"),
            content=payload.get("content"),
            url=payload.get("url"),
            category=payload.get("category", "general"),
            priority=payload.get("priority", "normal"),
            country_code=payload.get("country_code"),
            is_published=bool(payload.get("is_published", True)),
            ai_sentiment=payload.get("ai_sentiment", "neutral"),
            published_at=datetime.now(timezone.utc),
        )
        add_and_flush(self.db, article)
        commit_and_refresh(self.db, article)
        return article

    def delete_executive_news(self, article: ExecutiveNews) -> None:
        """Delete a persisted executive news article."""
        delete_only(self.db, article)
        commit_only(self.db)

    def resolve_alert(self, alert: object) -> None:
        """Mark a system alert as acknowledged."""
        alert.is_acknowledged = True
        commit_only(self.db)

    def get_dashboard_stats(self, today_start: datetime) -> dict:
        """Get dashboard statistics."""
        from data.models import UserSession
        return {
            "customers": self.db.query(User).filter(User.role == "customer").count(),
            "suppliers": self.db.query(User).filter(User.role == "supplier").count(),
            "logistics_companies": self.db.query(LogisticsPartner).count(),
            "active": self.db.query(LogisticsPartner).filter(LogisticsPartner.status == "active").count(),
            "failed": self.db.query(Order).filter(Order.status == "failed").count(),
            "alerts_pending": self.db.query(FraudAlert).filter(FraudAlert.is_resolved == False).count(),
            "active_sessions": self.db.query(UserSession).filter(
                UserSession.last_activity >= datetime.now(timezone.utc).replace(hour=0)
            ).count(),
        }
    
    def get_cash_position(self) -> dict:
        result = self.db.execute(text("""
            SELECT 
                COALESCE(SUM(CASE WHEN a.normal_side = 'debit' AND a.code LIKE '1%' THEN ab.balance ELSE 0 END), 0) as assets,
                COALESCE(SUM(CASE WHEN a.normal_side = 'credit' THEN ab.balance ELSE 0 END), 0) as liabilities,
                COALESCE(SUM(ab.balance), 0) as total
            FROM account_balances ab
            JOIN accounts a ON ab.account_id = a.id
        """)).fetchone()
        return {
            "available_cash": float(result[0] or 0),
            "locked_cash": float(result[1] or 0),
            "total": float(result[2] or 0),
        }
    
    def get_treasury_metrics(self) -> dict:
        redis = redis_client()
        cached = redis.get("command_center:treasury_metrics")
        if cached:
            return json.loads(cached)
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = self.db.execute(text("""
            SELECT 
                COALESCE(SUM(os.net_supplier_amount), 0) as supplier_payables,
                COALESCE(SUM(os.net_logistics_amount), 0) as logistics_payables,
                COALESCE(SUM(r.customer_refund_amount), 0) as refund_reserve,
                COALESCE(SUM(vr.vat_amount), 0) as vat_liability,
                COALESCE(SUM(CASE WHEN a.normal_side = 'debit' AND a.code LIKE '1%' THEN ab.balance ELSE 0 END), 0) as available_cash,
                COALESCE(SUM(CASE WHEN a.normal_side = 'credit' THEN ab.balance ELSE 0 END), 0) as locked_cash
            FROM orders o
            LEFT JOIN transaction_ledgers os ON o.id = os.order_id
            LEFT JOIN return_requests rr ON o.id = rr.order_id
            LEFT JOIN refund_ledger r ON rr.id = r.return_request_id
            LEFT JOIN vat_remittances vr ON vr.period_start >= :today
            LEFT JOIN account_balances ab ON ab.account_id = (SELECT id FROM accounts WHERE code = '1010' LIMIT 1)
            LEFT JOIN accounts a ON ab.account_id = a.id
            WHERE o.created_at >= :today
        """)).fetchone()
        
        metrics = {
            "supplier_payables": float(result[0] or 0),
            "logistics_payables": float(result[1] or 0),
            "refund_reserve": float(result[2] or 0),
            "vat_liability": float(result[3] or 0),
            "available_cash": float(result[4] or 0),
            "locked_cash": float(result[5] or 0),
            "updated_at": now.isoformat()
        }
        
        redis.setex("command_center:treasury_metrics", 300, json.dumps(metrics))
        return metrics
    
    def get_predictive_simulation(self, simulation_type: str, parameters: dict) -> dict:
        result = self.db.execute(text("""
            SELECT result_json FROM predictive_simulations 
            WHERE simulation_type = :type AND parameters_json = :params
            ORDER BY created_at DESC LIMIT 1
        """), {"type": simulation_type, "params": json.dumps(parameters)})
        
        cached = result.fetchone()
        if cached and cached[0]:
            return json.loads(cached[0])
        
        return {"error": "No simulation found. Run simulation first."}
    
    def run_commission_simulation(self, commission_rate: float, order_value: float) -> dict:
        simulated_commission = order_value * commission_rate
        simulated_gmv = order_value
        result = {
            "order_value": order_value,
            "commission_rate": commission_rate,
            "simulated_commission": simulated_commission,
            "simulated_gmv": simulated_gmv,
            "break_even_analysis": {
                "supplier_revenue": order_value - simulated_commission,
                "platform_revenue": simulated_commission
            }
        }
        
        sim = PredictiveSimulation(
            simulation_type="commission",
            parameters_json=json.dumps({"commission_rate": commission_rate, "order_value": order_value}),
            result_json=json.dumps(result)
        )
        self.db.add(sim)
        self.db.commit()
        return result
    
    def run_sla_simulation(self, current_delay_rate: float, new_partner_count: int) -> dict:
        projected_improvement = min(0.15, new_partner_count * 0.02)
        projected_delay_rate = max(0.01, current_delay_rate - projected_improvement)
        
        result = {
            "current_delay_rate": current_delay_rate,
            "projected_delay_rate": projected_delay_rate,
            "improvement_percentage": ((current_delay_rate - projected_delay_rate) / current_delay_rate * 100) if current_delay_rate > 0 else 0,
            "new_partners_added": new_partner_count,
            "estimated_cost_per_partner": 500
        }
        
        sim = PredictiveSimulation(
            simulation_type="sla",
            parameters_json=json.dumps({"current_delay_rate": current_delay_rate, "new_partner_count": new_partner_count}),
            result_json=json.dumps(result)
        )
        self.db.add(sim)
        self.db.commit()
        return result
    
    def get_external_intelligence(self) -> dict:
        redis = redis_client()
        cached = redis.get("command_center:external_intelligence")
        if cached:
            return json.loads(cached)
        
        result = {
            "currency_rates": self._get_currency_rates(),
            "supply_chain_alerts": self._get_supply_chain_alerts(),
            "competitor_news": self._get_competitor_news(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        redis.setex("command_center:external_intelligence", 600, json.dumps(result))
        return result
    
    def _get_currency_rates(self) -> dict:
        return {"USD_OMR": 0.385, "EUR_OMR": 0.415, "GBP_OMR": 0.485}
    
    def _get_supply_chain_alerts(self) -> List[dict]:
        return [{"alert": "Red Sea shipping delays", "severity": "high", "affected_countries": ["SA", "AE"]}]
    
    def _get_competitor_news(self) -> List[dict]:
        return [{"competitor": "Amazon", "news": "Launched new logistics arm", "impact": "medium"}]
    
    def get_workforce_metrics(self) -> dict:
        redis = redis_client()
        cached = redis.get("command_center:workforce_metrics")
        if cached:
            return json.loads(cached)
        
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        
        result = {
            "active_employees": self.db.query(Employee).filter(
                Employee.employment_status == "active"
            ).count(),
            "new_hires_30d": self.db.query(Employee).filter(
                Employee.hire_date >= thirty_days_ago.date()
            ).count(),
            "employees_by_department": self._get_employees_by_department(),
            "updated_at": now.isoformat()
        }
        
        redis.setex("command_center:workforce_metrics", 300, json.dumps(result))
        return result
    
    def _get_employees_by_department(self) -> List[dict]:
        result = self.db.execute(text("""
            SELECT department, COUNT(*) as count
            FROM employees
            WHERE employment_status = 'active' AND department IS NOT NULL
            GROUP BY department
            ORDER BY count DESC
        """)).fetchall()
        return [{"department": r[0], "count": r[1]} for r in result]
    
    def get_fraud_war_map(self) -> dict:
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        return {
            "attack_map": self._get_attack_locations(),
            "active_alerts": self.db.query(FraudAlert).filter(
                FraudAlert.created_at >= one_hour_ago,
                FraudAlert.status != "resolved"
            ).count(),
            "blocked_ips": self.db.query(IPAccountLinkage).filter(
                IPAccountLinkage.is_suspicious == True
            ).count(),
            "updated_at": now.isoformat()
        }
    
    def _get_attack_locations(self) -> List[dict]:
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        result = self.db.execute(text("""
            SELECT ip_address, COUNT(*) as attempt_count, MAX(created_at) as last_seen
            FROM fraud_events
            WHERE created_at >= :since
            GROUP BY ip_address
            ORDER BY attempt_count DESC
            LIMIT 10
        """), {"since": one_hour_ago}).fetchall()
        return [{"ip": r[0], "attempts": r[1], "last_seen": str(r[2]) if r[2] else None} for r in result]
    
    def get_system_health_dashboard(self) -> dict:
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)
        
        return {
            "response_time_avg": self._get_avg_response_time(),
            "error_rate": self._get_error_rate(),
            "cpu_usage": self._get_cpu_usage(),
            "memory_usage": self._get_memory_usage(),
            "active_connections": self._get_active_connections(),
            "alerts": self._get_active_alerts(five_minutes_ago),
            "updated_at": now.isoformat()
        }
    
    def _get_avg_response_time(self) -> float:
        try:
            now = datetime.now(timezone.utc)
            five_min_ago = now - timedelta(minutes=5)
            result = self.db.execute(text("""
                SELECT COALESCE(AVG(response_time_ms), 0) / 1000.0 
                FROM api_requests 
                WHERE created_at >= :since
            """), {"since": five_min_ago}).scalar()
            return float(result or 0.15)
        except Exception:
            return 0.15
    
    def _get_error_rate(self) -> float:
        now = datetime.now(timezone.utc)
        five_min_ago = now - timedelta(minutes=5)
        result = self.db.execute(text(
            "SELECT COUNT(*) FROM system_health_events WHERE severity = 'error' AND created_at >= :since"
        ), {"since": five_min_ago}).scalar()
        return float(result or 0)
    
    def _get_cpu_usage(self) -> float:
        try:
            now = datetime.now(timezone.utc)
            five_min_ago = now - timedelta(minutes=5)
            result = self.db.execute(text("""
                SELECT COALESCE(AVG(cpu_percent), 0) FROM system_metrics 
                WHERE created_at >= :since
            """), {"since": five_min_ago}).scalar()
            return float(result or 0)
        except Exception:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        try:
            now = datetime.now(timezone.utc)
            five_min_ago = now - timedelta(minutes=5)
            result = self.db.execute(text("""
                SELECT COALESCE(AVG(memory_percent), 0) FROM system_metrics 
                WHERE created_at >= :since
            """), {"since": five_min_ago}).scalar()
            return float(result or 0)
        except Exception:
            return 0.0
    
    def _get_active_connections(self) -> int:
        return len(self.db.query(User).filter(User.last_login >= datetime.now(timezone.utc) - timedelta(minutes=5)).all())
    
    def _get_active_alerts(self, since: datetime) -> List[dict]:
        result = self.db.execute(text("""
            SELECT service, metric_name, metric_value, message, created_at
            FROM system_health_events
            WHERE created_at >= :since AND severity IN ('warning', 'error')
            ORDER BY created_at DESC
            LIMIT 10
        """), {"since": since})
        return [{"service": r[0], "metric": r[1], "value": float(r[2] or 0), "message": r[3], "created_at": str(r[4]) if r[4] else None} for r in result]
    
    def check_escalations(self) -> List[dict]:
        now = datetime.now(timezone.utc)
        escalations = []
        
        pending_payouts = self._calculate_pending_payouts()
        high_payout_rule = self.db.query(AlertEscalationRule).filter(
            AlertEscalationRule.alert_type == "pending_payouts",
            AlertEscalationRule.is_active == True
        ).first()
        
        if high_payout_rule and pending_payouts > (high_payout_rule.threshold_value or 0):
            escalations.append({
                "type": "pending_payouts",
                "severity": high_payout_rule.severity,
                "value": pending_payouts,
                "threshold": high_payout_rule.threshold_value,
                "next_tier": high_payout_rule.current_tier + 1
            })
        
        return escalations

