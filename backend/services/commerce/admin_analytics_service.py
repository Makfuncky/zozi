"""
Admin Analytics Service.

Moved out of controllers/admin/analytics.py to break the
services -> controllers forbidden dependency edge (DG violation).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from data.models import AdminAnalyticsSnapshot, Order, OrderItem, Product, User

_ANALYTICS_SNAPSHOT_TTL = 3600
_ANALYTICS_CACHE_TTL_SECONDS = 300
_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}


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
        db.add(snapshot)
    else:
        setattr(snapshot, "snapshot_group", snapshot_group)
        setattr(snapshot, "period", period)
        setattr(snapshot, "payload_json", serialized_payload)
        setattr(snapshot, "computed_at", now)
        setattr(snapshot, "expires_at", expires_at)
    db.flush()
    return payload


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
