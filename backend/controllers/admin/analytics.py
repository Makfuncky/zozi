"""Admin analytics controller."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from models import AdminAnalyticsSnapshot, ChatbotQueryEvent, Product, Order, OrderItem, User
from utils.audit import audit_log, AuditAction
from utils.constants import _ADMIN_MAX_PAGE_SIZE, _ADMIN_DEFAULT_PAGE_SIZE
from utils.staff_permissions import DEFAULT_ROLE_PERMISSION_MAP
from utils.cache import cache_get_json, cache_set_json, build_versioned_cache_key

from services.write_helpers import add_and_flush, flush_only
_ANALYTICS_SNAPSHOT_TTL = 3600
_ANALYTICS_CACHE_TTL_SECONDS = 300
_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}


def _load_admin_analytics_snapshot(snapshot_key: str, db: Session) -> dict[str, Any] | None:
    snapshot = db.query(AdminAnalyticsSnapshot).filter(AdminAnalyticsSnapshot.snapshot_key == snapshot_key).first()
    if snapshot is None:
        return None
    expires_at = cast(datetime | None, getattr(snapshot, "expires_at", None))
    if expires_at is not None and expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        return None
    try:
        payload = json.loads(cast(str, getattr(snapshot, "payload_json")))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _store_admin_analytics_snapshot(
    snapshot_key: str,
    snapshot_group: str,
    payload: dict[str, Any],
    db: Session,
    *,
    period: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + _ANALYTICS_SNAPSHOT_TTL
    snapshot = db.query(AdminAnalyticsSnapshot).filter(AdminAnalyticsSnapshot.snapshot_key == snapshot_key).first()
    serialized_payload = json.dumps(payload, default=str)
    if snapshot is None:
        snapshot = AdminAnalyticsSnapshot(
            snapshot_key=snapshot_key,
            snapshot_group=snapshot_group,
            period=period,
            payload_json=serialized_payload,
            computed_at=now,
            expires_at=expires_at,
        )
        add_and_flush(db, snapshot)
    else:
        setattr(snapshot, "snapshot_group", snapshot_group)
        setattr(snapshot, "period", period)
        setattr(snapshot, "payload_json", serialized_payload)
        setattr(snapshot, "computed_at", now)
        setattr(snapshot, "expires_at", expires_at)
    flush_only(db)
    return payload


def _get_admin_analytics_payload(
    snapshot_key: str,
    snapshot_group: str,
    compute: callable,
    db: Session,
    *,
    cache_payload: dict[str, Any] | None = None,
    period: str | None = None,
) -> dict[str, Any]:
    cache_key = build_versioned_cache_key(
        "admin_analytics",
        snapshot_key,
        cache_payload or {"period": period or ""},
    )
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    persisted_payload = _load_admin_analytics_snapshot(snapshot_key, db)
    if persisted_payload is not None:
        cache_set_json(cache_key, persisted_payload, _ANALYTICS_CACHE_TTL_SECONDS)
        return persisted_payload

    payload = compute()
    payload = _store_admin_analytics_snapshot(snapshot_key, snapshot_group, payload, db, period=period)
    cache_set_json(cache_key, payload, _ANALYTICS_CACHE_TTL_SECONDS)
    return payload


def refresh_admin_analytics_snapshots(db: Session) -> dict[str, Any]:
    snapshots = {
        "overview": _compute_analytics_overview(db),
        "timeseries:7d": _compute_analytics_timeseries_payload("7d", db),
        "timeseries:30d": _compute_analytics_timeseries_payload("30d", db),
        "timeseries:90d": _compute_analytics_timeseries_payload("90d", db),
        "top-products:10": _compute_top_products_payload(10, db),
        "user-growth:30d": _compute_user_growth_payload("30d", db),
    }
    for snapshot_key, payload in snapshots.items():
        if snapshot_key.startswith("timeseries:"):
            period = snapshot_key.split(":", 1)[1]
            snapshot_group = "timeseries"
        elif snapshot_key.startswith("top-products:"):
            period = snapshot_key.split(":", 1)[1]
            snapshot_group = "top-products"
        elif snapshot_key.startswith("user-growth:"):
            period = snapshot_key.split(":", 1)[1]
            snapshot_group = "user-growth"
        else:
            period = None
            snapshot_group = snapshot_key
        _store_admin_analytics_snapshot(snapshot_key, snapshot_group, payload, db, period=period)
    return {"refreshed": len(snapshots), "keys": sorted(snapshots.keys())}

ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    role: set(permissions)
    for role, permissions in DEFAULT_ROLE_PERMISSION_MAP.items()
}

VALID_USER_ROLES = {"customer", "supplier", "admin", "sub_admin", "moderator", "support"}


def get_analytics(db: Session) -> dict:
    return _get_admin_analytics_payload("overview", "overview", lambda: _compute_analytics_overview(db), db)


def get_customer_insights(db: Session) -> dict:
    top_cust_rows = (
        db.query(
            Order.user_id,
            User.username,
            User.email,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_spent"),
        )
        .join(User, User.id == Order.user_id)
        .group_by(Order.user_id, User.username, User.email)
        .order_by(desc(func.sum(Order.total_amount)))
        .limit(10)
        .all()
    )
    top_customers = [
        {
            "user_id": row.user_id,
            "username": row.username,
            "email": row.email,
            "order_count": row.order_count,
            "total_spent": round(float(row.total_spent or 0), 2),
        }
        for row in top_cust_rows
    ]

    cat_rows = (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units_sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(10)
        .all()
    )
    top_categories = [
        {"category": row.category or "Uncategorized", "units_sold": int(row.units_sold or 0)}
        for row in cat_rows
    ]

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    new_this_month = db.query(User).filter(
        User.role == "customer",
        User.created_at >= this_month_start,
    ).count()
    new_last_month = db.query(User).filter(
        User.role == "customer",
        User.created_at >= last_month_start,
        User.created_at < this_month_start,
    ).count()

    return {
        "top_customers": top_customers,
        "top_categories": top_categories,
        "new_customers_this_month": new_this_month,
        "new_customers_last_month": new_last_month,
    }


def get_analytics_timeseries(period: str, db: Session) -> dict:
    return _get_admin_analytics_payload(
        f"timeseries:{period}",
        "timeseries",
        lambda: _compute_analytics_timeseries_payload(period, db),
        db,
        cache_payload={"period": period},
        period=period,
    )


def get_top_products_analytics(limit: int, db: Session) -> dict:
    return _get_admin_analytics_payload(
        f"top-products:{limit}",
        "top-products",
        lambda: _compute_top_products_payload(limit, db),
        db,
        cache_payload={"limit": limit},
        period=str(limit),
    )


def get_user_growth_analytics(period: str, db: Session) -> dict:
    return _get_admin_analytics_payload(
        f"user-growth:{period}",
        "user-growth",
        lambda: _compute_user_growth_payload(period, db),
        db,
        cache_payload={"period": period},
        period=period,
    )


def get_chatbot_analytics(period: str, db: Session) -> dict:
    """Return assistant query trends, shopper behavior signals, and click engagement."""
    days = _PERIOD_DAYS.get(period, 30)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    events = (
        db.query(ChatbotQueryEvent)
        .filter(ChatbotQueryEvent.created_at >= since)
        .order_by(ChatbotQueryEvent.created_at.asc())
        .all()
    )
    query_events = [event for event in events if cast(str | None, getattr(event, "event_type", None)) == "query"]
    click_events = [event for event in events if cast(str | None, getattr(event, "event_type", None)) == "product_click"]

    top_queries: Counter[str] = Counter()
    top_intents: Counter[str] = Counter()
    top_categories: Counter[str] = Counter()
    top_brands: Counter[str] = Counter()
    top_colors: Counter[str] = Counter()
    top_sizes: Counter[str] = Counter()
    no_result_queries: Counter[str] = Counter()
    daily_data: dict[str, dict[str, Any]] = {}
    budget_focused = 0
    quality_focused = 0
    brand_specific = 0

    for event in query_events:
        normalized_query = str(getattr(event, "normalized_query", "") or "").strip()
        intent = str(getattr(event, "intent", "") or "unknown")
        result_count = int(cast(Any, getattr(event, "result_count", 0)) or 0)
        filters = _safe_load_chatbot_filters(cast(str | None, getattr(event, "filters_json", None)))
        day = str(cast(datetime, getattr(event, "created_at")).date()) if getattr(event, "created_at", None) else "unknown"
        bucket = daily_data.setdefault(day, {"date": day, "queries": 0, "clicks": 0, "product_searches": 0})
        bucket["queries"] += 1
        if intent == "product_search":
            bucket["product_searches"] += 1

        if normalized_query:
            top_queries[normalized_query] += 1
            if result_count == 0:
                no_result_queries[normalized_query] += 1
        top_intents[intent] += 1

        category = str(filters.get("category") or "").strip()
        brand = str(filters.get("brand") or "").strip()
        color = str(filters.get("color") or "").strip()
        size = str(filters.get("size") or "").strip()
        if category:
            top_categories[category] += 1
        if brand:
            top_brands[brand] += 1
            brand_specific += 1
        if color:
            top_colors[color] += 1
        if size:
            top_sizes[size] += 1
        if filters.get("max_price") is not None or filters.get("min_price") is not None:
            budget_focused += 1
        if filters.get("quality") or filters.get("min_rating") is not None:
            quality_focused += 1

    for event in click_events:
        day = str(cast(datetime, getattr(event, "created_at")).date()) if getattr(event, "created_at", None) else "unknown"
        bucket = daily_data.setdefault(day, {"date": day, "queries": 0, "clicks": 0, "product_searches": 0})
        bucket["clicks"] += 1

    top_clicked_rows = (
        db.query(
            Product.id,
            Product.name,
            func.count(ChatbotQueryEvent.id).label("clicks"),
        )
        .join(Product, Product.id == ChatbotQueryEvent.clicked_product_id)
        .filter(
            ChatbotQueryEvent.created_at >= since,
            ChatbotQueryEvent.event_type == "product_click",
        )
        .group_by(Product.id, Product.name)
        .order_by(desc(func.count(ChatbotQueryEvent.id)))
        .limit(10)
        .all()
    )

    query_count = len(query_events)
    click_count = len(click_events)
    clicked_sessions = {getattr(event, "session_id", None) for event in click_events if getattr(event, "session_id", None)}
    clicked_session_count = len(clicked_sessions)

    return {
        "period": period,
        "days": days,
        "total_queries": query_count,
        "total_clicks": click_count,
        "unique_sessions": len({getattr(event, "session_id", None) for event in query_events if getattr(event, "session_id", None)}),
        "unique_users": len({getattr(event, "user_id", None) for event in query_events if getattr(event, "user_id", None)}),
        "product_search_queries": top_intents.get("product_search", 0),
        "avg_results_per_query": round(sum(int(cast(Any, getattr(event, "result_count", 0)) or 0) for event in query_events) / query_count, 2) if query_count else 0.0,
        "click_through_rate": round((clicked_session_count / query_count) * 100, 1) if query_count else 0.0,
        "top_queries": [{"query": query, "count": count} for query, count in top_queries.most_common(10)],
        "top_intents": [{"intent": intent, "count": count} for intent, count in top_intents.most_common(8)],
        "top_filters": {
            "categories": [{"value": value, "count": count} for value, count in top_categories.most_common(8)],
            "brands": [{"value": value, "count": count} for value, count in top_brands.most_common(8)],
            "colors": [{"value": value, "count": count} for value, count in top_colors.most_common(8)],
            "sizes": [{"value": value, "count": count} for value, count in top_sizes.most_common(8)],
        },
        "behavior_summary": {
            "budget_focused_queries": budget_focused,
            "quality_focused_queries": quality_focused,
            "brand_specific_queries": brand_specific,
        },
        "top_clicked_products": [
            {"id": row.id, "name": row.name, "clicks": int(row.clicks or 0)}
            for row in top_clicked_rows
        ],
        "no_result_queries": [{"query": query, "count": count} for query, count in no_result_queries.most_common(10)],
        "daily_data": sorted(daily_data.values(), key=lambda item: item["date"]),
    }


def _compute_analytics_overview(db: Session) -> dict[str, Any]:
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0)
    total_customers = db.query(func.count(User.id)).filter(User.role == "customer").scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_customers": total_customers,
        "total_products": total_products,
        "average_order_value": round(total_revenue / total_orders, 2) if total_orders else 0.0,
    }


def _compute_analytics_timeseries_payload(period: str, db: Session) -> dict[str, Any]:
    days = _PERIOD_DAYS.get(period, 30)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    rows = (
        db.query(func.date(Order.created_at).label("date"), func.count(Order.id).label("orders"), func.coalesce(func.sum(Order.total_amount), 0).label("revenue"))
        .filter(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    data = [
        {
            "date": str(row.date),
            "orders": int(row.orders or 0),
            "revenue": round(float(row.revenue or 0), 2),
        }
        for row in rows
    ]
    return {"period": period, "days": days, "data": data}


def _compute_top_products_payload(limit: int, db: Session) -> dict[str, Any]:
    rows = (
        db.query(Product.id, Product.name, func.sum(OrderItem.quantity).label("units_sold"), func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .limit(max(1, limit))
        .all()
    )
    products = [
        {
            "id": row.id,
            "name": row.name,
            "units_sold": int(row.units_sold or 0),
            "revenue": round(float(row.revenue or 0), 2),
        }
        for row in rows
    ]
    return {"limit": limit, "products": products}


def _compute_user_growth_payload(period: str, db: Session) -> dict[str, Any]:
    days = _PERIOD_DAYS.get(period, 30)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    rows = (
        db.query(func.date(User.created_at).label("date"), func.count(User.id).label("count"))
        .filter(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )
    data = [{"date": str(row.date), "new_users": int(row.count or 0)} for row in rows]
    return {"period": period, "days": days, "data": data}


# â”€â”€ Admin: Recipient Bank Account Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_ALLOWED_BANK_ACCOUNT_KINDS = {"supplier", "logistics_partner"}


