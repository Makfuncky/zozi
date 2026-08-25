from sqlalchemy import func
from domains.catalog.ports import Category as CategoryModel
from domains.governance.models.admin import CommissionGlobalConfig
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.hr.ports import Employee
from domains.logistics.models.logistics import Shipment
from domains.finance.models.payments import Payment
from domains.finance.models.payments import Payout as PayoutModel
import logging
from sqlalchemy.orm import Session
from infrastructure.utils.pagination import keyset_offset_window

logger = logging.getLogger(__name__)

def admin_dashboard_fallback(db: Session):
    """Simple admin dashboard stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from domains.governance.ports import User as UserModel
    from domains.catalog.ports import Product as ProductModel
    from domains.orders.ports import Order as OrderModel

    total_revenue = (
        db.query(sqlfunc.sum(Payment.amount))
        .filter(Payment.status == "completed")
        .scalar()
        or 0
    )
    total_users = db.query(sqlfunc.count(UserModel.id)).scalar() or 0
    total_orders = db.query(sqlfunc.count(OrderModel.id)).scalar() or 0

    return {
        "total_revenue": float(total_revenue),
        "total_users": total_users,
        "total_orders": total_orders,
        "active_sessions": 0,
        "pending_payouts": db.query(PayoutModel).filter(
            PayoutModel.status == "pending"
        ).count(),
    }

def admin_stats_fallback(db: Session):
    """Simple aggregate stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from domains.governance.ports import User as UserModel
    from domains.catalog.ports import Product as ProductModel
    from domains.orders.ports import Order as OrderModel

    return {
        "total_users": db.query(sqlfunc.count(UserModel.id)).scalar() or 0,
        "total_customers": db.query(sqlfunc.count(UserModel.id)).filter(
            UserModel.role == "customer"
        ).scalar() or 0,
        "total_suppliers": db.query(sqlfunc.count(UserModel.id)).filter(
            UserModel.role == "supplier"
        ).scalar() or 0,
        "total_orders": db.query(sqlfunc.count(OrderModel.id)).scalar() or 0,
        "total_products": db.query(sqlfunc.count(ProductModel.id)).filter(
            ProductModel.is_deleted == False
        ).scalar() or 0,
        "pending_payouts": db.query(PayoutModel).filter(
            PayoutModel.status == "pending"
        ).count(),
    }

def admin_payouts_fallback(page, page_size, db: Session):
    """List all payouts (no country code required)."""
    skip = (page - 1) * page_size
    items = (
        keyset_offset_window(db.query(PayoutModel)
        .order_by(PayoutModel.created_at.desc()), offset=skip, limit=page_size)
    )
    total = db.query(PayoutModel).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}

def admin_categories_fallback(page, page_size, db: Session):
    """List all categories (no country code required)."""
    skip = (page - 1) * page_size
    items = (
        keyset_offset_window(db.query(CategoryModel)
        .order_by(CategoryModel.name), offset=skip, limit=page_size)
    )
    total = db.query(CategoryModel).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}

def admin_commission_fallback(db: Session):
    """Get commission global config (no country code required)."""
    config = db.query(CommissionGlobalConfig).first()
    return config or {}

def admin_employees_fallback(page, page_size, db: Session):
    """List all employees (no country code required)."""
    from domains.governance.ports import User as UserModel
    skip = (page - 1) * page_size
    items = (
        keyset_offset_window(db.query(Employee)
        .join(UserModel, Employee.user_id == UserModel.id)
        .order_by(UserModel.full_name.asc().nullslast(), Employee.id), offset=skip, limit=page_size)
    )
    total = db.query(Employee).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}

def admin_payments_fallback(page, page_size, db: Session):
    """List all payments (no country code required)."""
    skip = (page - 1) * page_size
    items = (
        keyset_offset_window(db.query(Payment)
        .order_by(Payment.created_at.desc()), offset=skip, limit=page_size)
    )
    total = db.query(Payment).count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}

def admin_logistics_fallback(db: Session):
    """List logistics carriers and partners (no country code required)."""
    from domains.governance.models.admin import ShippingZone
    from domains.logistics.models.logistics import Shipment

    carriers = db.query(ShippingCarrier).filter(
        ShippingCarrier.is_active == True
    ).all()
    zone_count = db.query(ShippingZone).filter(
        ShippingZone.is_active == True
    ).count()
    shipment_count = db.query(Shipment).count()

    return {
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in carriers
        ],
        "active_zones": zone_count,
        "total_shipments": shipment_count,
    }

def admin_logistics_partners_fallback(db: Session):
    """List logistics partners (no country code required)."""
    carriers = db.query(ShippingCarrier).filter(
        ShippingCarrier.is_active == True
    ).all()
    return {
        "partners": [
            {"id": c.id, "name": c.name, "code": c.code, "is_active": c.is_active}
            for c in carriers
        ],
        "total": len(carriers),
    }

def admin_treasury_fallback(db: Session):
    """Treasury summary — redirect to /admin/treasury/metrics if you need full metrics."""
    from domains.finance.models.finance import Account as AccountModel
    from domains.finance.models.finance import AccountBalance as AccountBalanceModel

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

def admin_treasury_metrics_fallback(db: Session):
    """Treasury metrics summary (no country code required)."""
    from domains.finance.models.finance import Account as AccountModel
    from domains.finance.models.finance import AccountBalance as AccountBalanceModel


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

