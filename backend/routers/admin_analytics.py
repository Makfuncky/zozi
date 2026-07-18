"""Admin analytics router."""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from db.database import get_db
from models import Order, Product, User as UserModel, SupplierProfile, ChatbotQueryEvent
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from models import User

router = APIRouter()


@router.get("/{country_code}/dashboard")
def dashboard_summary(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        total_users = db.query(func.count(UserModel.id)).filter(UserModel.country_code == country_code.upper()).scalar()
        total_suppliers = db.query(func.count(SupplierProfile.id)).filter(SupplierProfile.country_code == country_code.upper()).scalar()
        total_products = db.query(func.count(Product.id)).filter(Product.is_active == True, Product.country_code == country_code.upper()).scalar()
        total_orders = db.query(func.count(Order.id)).filter(Order.shipping_country == country_code.upper()).scalar()
        total_revenue = db.query(func.coalesce(func.sum(Order.total), 0)).filter(Order.payment_status == "paid", Order.shipping_country == country_code.upper()).scalar()
        return {"total_users": total_users, "total_suppliers": total_suppliers, "total_products": total_products, "total_orders": total_orders, "total_revenue": float(total_revenue)}
    finally:
        clear_rls_context()


@router.get("/{country_code}/chatbot")
def get_chatbot_analytics(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    period: str = Query(default="30d", description="Time period: 7d, 30d, 90d, 1y")
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, 30)
        since = datetime.utcnow() - timedelta(days=days)

        try:
            events = db.query(ChatbotQueryEvent).filter(
                ChatbotQueryEvent.created_at >= since,
                ChatbotQueryEvent.country_code == country_code.upper()
            ).order_by(ChatbotQueryEvent.created_at.desc()).limit(1000).all()
        except Exception:
            events = []

        total_queries = len(events)
        total_clicks = sum(1 for e in events if e.clicked_product_id)
        product_searches = sum(1 for e in events if e.intent == "product_search")
        avg_results = sum(e.result_count or 0 for e in events) / max(total_queries, 1)
        ctr = (total_clicks / max(total_queries, 1)) * 100 if total_queries else 0

        query_counts: Dict[str, int] = {}
        intent_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}

        for e in events:
            if e.normalized_query:
                query_counts[e.normalized_query[:100]] = query_counts.get(e.normalized_query[:100], 0) + 1
            if e.intent:
                intent_counts[e.intent] = intent_counts.get(e.intent, 0) + 1
            if e.filters_json:
                try:
                    filters = json.loads(e.filters_json) if isinstance(e.filters_json, str) else e.filters_json
                    if isinstance(filters, dict):
                        for key, val in filters.items():
                            if val:
                                category_counts[f"{key}:{val}"] = category_counts.get(f"{key}:{val}", 0) + 1
                except Exception:
                    pass

        top_queries = [{"query": k, "count": v} for k, v in sorted(query_counts.items(), key=lambda x: -x[1])[:10]]
        top_intents = [{"intent": k, "count": v} for k, v in sorted(intent_counts.items(), key=lambda x: -x[1])[:10]]

        daily_data: Dict[str, Dict[str, int]] = {}
        for e in events:
            day = e.created_at.strftime("%Y-%m-%d") if e.created_at else "unknown"
            if day not in daily_data:
                daily_data[day] = {"queries": 0, "clicks": 0, "product_searches": 0}
            daily_data[day]["queries"] += 1
            if e.clicked_product_id:
                daily_data[day]["clicks"] += 1
            if e.intent == "product_search":
                daily_data[day]["product_searches"] += 1

        daily_list = [{"date": k, **v} for k, v in sorted(daily_data.items())]

        top_clicked: Dict[int, int] = {}
        for e in events:
            if e.clicked_product_id:
                top_clicked[e.clicked_product_id] = top_clicked.get(e.clicked_product_id, 0) + 1

        top_clicked_products = []
        for pid, clicks in sorted(top_clicked.items(), key=lambda x: -x[1])[:5]:
            prod = db.query(Product).filter(Product.id == pid, Product.country_code == country_code.upper()).first()
            top_clicked_products.append({
                "id": pid,
                "name": prod.name if prod else f"Product {pid}",
                "clicks": clicks
            })

        budget_focused = sum(1 for e in events if e.intent == "budget_focused")
        quality_focused = sum(1 for e in events if e.intent == "quality_focused")
        brand_specific = sum(1 for e in events if e.intent == "brand_specific")

        no_result_queries = [{"query": k, "count": v} for k, v in sorted(query_counts.items(), key=lambda x: -x[1])[:5] if v == 1]

        return {
            "period": period,
            "days": days,
            "total_queries": total_queries,
            "total_clicks": total_clicks,
            "product_search_queries": product_searches,
            "avg_results_per_query": round(avg_results, 2),
            "click_through_rate": round(ctr, 2),
            "top_queries": top_queries,
            "top_intents": top_intents,
            "top_filters": {"categories": [], "brands": [], "colors": [], "sizes": []},
            "behavior_summary": {
                "budget_focused_queries": budget_focused,
                "quality_focused_queries": quality_focused,
                "brand_specific_queries": brand_specific,
            },
            "top_clicked_products": top_clicked_products,
            "no_result_queries": no_result_queries,
            "daily_data": daily_list,
        }
    finally:
        clear_rls_context()

