from domains.comms.services.utility.db_read import all_rows, count, first, scalar, scalar_sum, scalar_with_filters
"""Admin dashboard fallback aggregates (no country-code scope).

Holds the business logic that previously lived inline in
``routers/admin_analytics_fallback_dashboard.py``. The router is now a thin
delegator that calls these functions, satisfying the
``routers -> controllers -> services`` layering (routers must not import
``models`` / ``services`` directly or perform commits).
"""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domains.governance.models.user import User as UserModel
from domains.catalog.models.products import Category as CategoryModel
from domains.catalog.models.products import Product as ProductModel
from domains.finance.models.finance import Account as AccountModel
from domains.finance.models.finance import AccountBalance as AccountBalanceModel
from domains.governance.models.admin import CommissionGlobalConfig
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.hr.models.employee_models import Employee
from domains.logistics.models.logistics import Shipment
from domains.finance.models.payments import Payout as PayoutModel
from domains.finance.models.payments import Payment


def admin_dashboard_fallback(db: Session) -> dict:
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


def admin_stats_fallback(db: Session) -> dict:
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


def admin_payouts_fallback(db: Session, page: int, page_size: int) -> dict:
    skip = (page - 1) * page_size
    items = all_rows(
        db,
        PayoutModel,
        order_by=PayoutModel.created_at.desc(),
        offset=skip,
        limit=page_size,
    )
    total = count(db, PayoutModel)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def admin_commission_fallback(db: Session) -> dict:
    config = first(db, CommissionGlobalConfig)
    return config or {}


def admin_employees_fallback(db: Session, page: int, page_size: int) -> dict:
    skip = (page - 1) * page_size
    items = all_rows(
        db,
        Employee,
        joins=[(UserModel, Employee.user_id == UserModel.id)],
        order_by=UserModel.full_name.asc().nullslast(),
        offset=skip,
        limit=page_size,
    )
    total = count(db, Employee)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def admin_payments_fallback(db: Session, page: int, page_size: int) -> dict:
    skip = (page - 1) * page_size
    items = all_rows(
        db,
        Payment,
        order_by=Payment.created_at.desc(),
        offset=skip,
        limit=page_size,
    )
    total = count(db, Payment)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def admin_logistics_fallback(db: Session) -> dict:
    carriers = all_rows(db, ShippingCarrier, [ShippingCarrier.is_active == True])
    zone_count = count(db, ShippingZone, [ShippingZone.is_active == True])
    shipment_count = count(db, Shipment)
    return {
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in carriers
        ],
        "active_zones": zone_count,
        "total_shipments": shipment_count,
    }


def admin_logistics_partners_fallback(db: Session) -> dict:
    carriers = all_rows(db, ShippingCarrier, [ShippingCarrier.is_active == True])
    return {
        "partners": [
            {"id": c.id, "name": c.name, "code": c.code, "is_active": c.is_active}
            for c in carriers
        ],
        "total": len(carriers),
    }


def admin_treasury_fallback(db: Session) -> dict:
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


def admin_treasury_metrics_fallback(db: Session) -> dict:
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
