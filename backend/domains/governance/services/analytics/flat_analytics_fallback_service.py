"""
Admin fallback aggregates.

Holds the DB read/aggregation logic that previously lived inline in
``routers/admin_analytics_fallback_dashboard.py`` (the ``/dashboard``,
``/stats`` and ``/treasury`` endpoints).  Moving it here keeps the router
thin: the router only declares routes + auth dependencies and delegates
to ``controllers.admin.analytics_fallback_controller``.
"""
from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domains.governance.models.user import User as UserModel
from domains.catalog.models.products import Product as ProductModel
from domains.finance.models.finance import Account as AccountModel
from domains.finance.models.finance import AccountBalance as AccountBalanceModel
from domains.governance.models.admin import CommissionGlobalConfig
from domains.payments.models.payments import Payment
from domains.payments.models.payments import Payout as PayoutModel
from domains.comms.services.shared.utility.db_read import all_rows
from domains.comms.services.shared.utility.db_read import count
from domains.comms.services.shared.utility.db_read import first
from domains.comms.services.shared.utility.db_read import scalar
from domains.comms.services.shared.utility.db_read import scalar_sum
from domains.comms.services.shared.utility.db_read import scalar_with_filters


def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Simple admin dashboard stats — works without country_code."""
    total_revenue = scalar_sum(db, Payment.amount, [Payment.status == "completed"])
    total_users = scalar_with_filters(db, func.count(UserModel.id)) or 0
    total_orders = scalar_with_filters(db, func.count(UserModel.id)) or 0
    return {
        "total_revenue": float(total_revenue),
        "total_users": total_users,
        "total_orders": total_orders,
        "active_sessions": 0,
        "pending_payouts": count(db, PayoutModel, [PayoutModel.status == "pending"]),
    }


def get_admin_stats(db: Session) -> Dict[str, Any]:
    """Simple aggregate stats — works without country_code."""
    return {
        "total_users": scalar_with_filters(db, func.count(UserModel.id)) or 0,
        "total_customers": scalar_with_filters(
            db, func.count(UserModel.id), [UserModel.role == "customer"]
        )
        or 0,
        "total_suppliers": scalar_with_filters(
            db, func.count(UserModel.id), [UserModel.role == "supplier"]
        )
        or 0,
        "total_orders": scalar_with_filters(db, func.count(UserModel.id)) or 0,
        "total_products": scalar_with_filters(
            db, func.count(ProductModel.id), [ProductModel.is_deleted == False]
        )
        or 0,
        "pending_payouts": count(db, PayoutModel, [PayoutModel.status == "pending"]),
    }


def get_treasury_summary(db: Session) -> Dict[str, Any]:
    """Treasury summary — redirect to /admin/treasury/metrics for full metrics."""
    total_cash = (
        scalar(
            db,
            select(func.sum(AccountBalanceModel.balance)).select_from(
                AccountBalanceModel
            ),
        )
        or 0
    )
    account_count = count(db, AccountModel)
    return {
        "total_cash": float(total_cash),
        "total_accounts": account_count,
        "metrics_available_at": "/admin/treasury/metrics",
    }


def get_treasury_metrics(db: Session) -> Dict[str, Any]:
    """Treasury metrics summary (no country code required)."""
    accounts = all_rows(db, AccountModel)
    total_cash = (
        scalar(
            db,
            select(func.sum(AccountBalanceModel.balance)).select_from(
                AccountBalanceModel
            ),
        )
        or 0
    )
    return {
        "total_accounts": len(accounts),
        "total_cash": float(total_cash),
        "accounts": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "currency": a.currency,
            }
            for a in accounts
        ],
    }


def get_commission_config(db: Session) -> Any:
    """Get commission global config (no country code required)."""
    return first(db, CommissionGlobalConfig) or {}
