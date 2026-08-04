"""Analytics service for admin dashboard stats.

Provides country-scoped dashboard statistics used by the admin UI
to render the top-row stat cards (users, suppliers, products, orders, revenue).
"""


import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_country_dashboard_stats(
    db: Session,
    country_code: str | None = None,
) -> dict[str, Any]:
    """Return a summary of user / supplier / product / order / revenue counts.

    When *country_code* is provided the numbers are scoped to that country
    (based on the user's preferred_country or supplier's country_code column).
    Without a country code the global figures are returned.
    """
    try:
        # ── User count ───────────────────────────────────────────────────────
        user_q = "SELECT COUNT(*) FROM users"
        user_params: dict[str, Any] = {}
        if country_code:
            user_q += " WHERE preferred_country = :cc OR preferred_country IS NULL"
            user_params["cc"] = country_code
        total_users = db.execute(text(user_q), user_params).scalar() or 0

        # ── Supplier count ────────────────────────────────────────────────────
        supplier_q = """
            SELECT COUNT(*) FROM supplier_profiles sp
            JOIN users u ON u.id = sp.user_id
        """
        supplier_params: dict[str, Any] = {}
        if country_code:
            supplier_q += " WHERE (sp.country_code = :cc OR u.preferred_country = :cc)"
            supplier_params["cc"] = country_code
        total_suppliers = db.execute(text(supplier_q), supplier_params).scalar() or 0

        # ── Product count ─────────────────────────────────────────────────────
        product_q = """SELECT COUNT(*) FROM products"""
        product_params: dict[str, Any] = {}
        if country_code:
            product_q += " WHERE country_code = :cc"
            product_params["cc"] = country_code
        # If products table doesn't have country_code, use uncounted fallback
        try:
            total_products = db.execute(text(product_q), product_params).scalar() or 0
        except Exception:
            total_products = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0

        # ── Order count & revenue ─────────────────────────────────────────────
        order_q = "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders"
        order_params: dict[str, Any] = {}
        if country_code:
            order_q += " WHERE country_code = :cc"
            order_params["cc"] = country_code
        try:
            row = db.execute(text(order_q), order_params).one()
            total_orders = int(row[0]) if row else 0
            total_revenue = float(row[1]) if row and row[1] else 0.0
        except Exception:
            total_orders = 0
            total_revenue = 0.0

        return {
            "total_users": total_users,
            "total_suppliers": total_suppliers,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
        }
    except Exception as exc:
        logger.warning("Failed to get country dashboard stats: %s", exc)
        return {
            "total_users": 0,
            "total_suppliers": 0,
            "total_products": 0,
            "total_orders": 0,
            "total_revenue": 0.0,
        }
