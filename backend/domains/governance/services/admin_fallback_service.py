"""Admin fallback service layer.

Houses the inline aggregate/DB logic previously embedded in
``routers/admin_logistics_fallback.py`` (non-country-scoped route aliases used
by the admin frontend). ``get_all_suppliers`` is a controller function and
remains delegated from the router.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.accounts.models.user import User as UserModel
from domains.catalog.models.products import Category as CategoryModel
from domains.catalog.models.products import Product as ProductModel
from domains.finance.models.finance import Account as AccountModel
from domains.finance.models.finance import AccountBalance as AccountBalanceModel
from domains.governance.models.admin import CommissionGlobalConfig
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.hr.models.employee_models import Employee
from domains.logistics.models.logistics import Shipment
from domains.orders.models.orders import Order as OrderModel
from domains.payments.models.payments import Payment
from domains.payments.models.payments import Payout as PayoutModel


def get_dashboard_stats(db: Session) -> dict:
    total_revenue = (
        db.query(func.sum(Payment.amount))
        .filter(Payment.status == "completed")
        .scalar()
        or 0
    )
    total_users = db.query(func.count(UserModel.id)).scalar() or 0
    total_orders = db.query(func.count(OrderModel.id)).scalar() or 0

    return {
        "total_revenue": float(total_revenue),
        "total_users": total_users,
        "total_orders": total_orders,
        "active_sessions": 0,
        "pending_payouts": db.query(PayoutModel).filter(PayoutModel.status == "pending").count(),
    }


def get_admin_stats(db: Session) -> dict:
    return {
        "total_users": db.query(func.count(UserModel.id)).scalar() or 0,
        "total_customers": db.query(func.count(UserModel.id)).filter(UserModel.role == "customer").scalar() or 0,
        "total_suppliers": db.query(func.count(UserModel.id)).filter(UserModel.role == "supplier").scalar() or 0,
        "total_orders": db.query(func.count(OrderModel.id)).scalar() or 0,
        "total_products": db.query(func.count(ProductModel.id)).filter(ProductModel.is_deleted == False).scalar() or 0,
        "pending_payouts": db.query(PayoutModel).filter(PayoutModel.status == "pending").count(),
    }


def list_payouts_fallback(db: Session, page: int, page_size: int) -> dict:
    skip = (page - 1) * page_size
    items = (
        db.query(PayoutModel)
        .order_by(PayoutModel.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = db.query(PayoutModel).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def list_categories_fallback(db: Session, page: int, page_size: int) -> dict:
    skip = (page - 1) * page_size
    items = (
        db.query(CategoryModel)
        .order_by(CategoryModel.name)
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = db.query(CategoryModel).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_commission_config_fallback(db: Session) -> dict:
    config = db.query(CommissionGlobalConfig).first()
    return config or {}


def list_employees_fallback(db: Session, page: int, page_size: int) -> dict:
    skip = (page - 1) * page_size
    items = (
        db.query(Employee)
        .join(UserModel, Employee.user_id == UserModel.id)
        .order_by(UserModel.full_name.asc().nullslast(), Employee.id)
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = db.query(Employee).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def list_payments_fallback(db: Session, page: int, page_size: int) -> dict:
    skip = (page - 1) * page_size
    items = (
        db.query(Payment)
        .order_by(Payment.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = db.query(Payment).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def list_logistics_fallback(db: Session) -> dict:
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zone_count = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()
    shipment_count = db.query(Shipment).count()

    return {
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in carriers
        ],
        "active_zones": zone_count,
        "total_shipments": shipment_count,
    }


def list_logistics_partners_fallback(db: Session) -> dict:
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    return {
        "partners": [
            {"id": c.id, "name": c.name, "code": c.code, "is_active": c.is_active}
            for c in carriers
        ],
        "total": len(carriers),
    }


def get_treasury_fallback(db: Session) -> dict:
    total_cash = (
        db.query(func.sum(AccountBalanceModel.balance))
        .select_from(AccountBalanceModel)
        .scalar()
        or 0
    )
    account_count = db.query(AccountModel).count()

    return {
        "total_cash": float(total_cash),
        "total_accounts": account_count,
        "metrics_available_at": "/admin/treasury/metrics",
    }


def get_treasury_metrics_fallback(db: Session) -> dict:
    accounts = db.query(AccountModel).all()
    total_cash = (
        db.query(func.sum(AccountBalanceModel.balance))
        .select_from(AccountBalanceModel)
        .scalar()
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
