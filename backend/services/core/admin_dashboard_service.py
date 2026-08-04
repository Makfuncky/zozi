"""Service methods for admin dashboard and fallback stats."""
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from data.models import User as UserModel, Order as OrderModel, Payment, Payout as PayoutModel, Category as CategoryModel, CommissionGlobalConfig, Employee, Product as ProductModel
from data.models import ShippingCarrier, ShippingZone, Shipment, AccountBalance as AccountBalanceModel, Account as AccountModel
from data.models_core import VideoRoom


def get_fallback_admin_dashboard_stats(db: Session) -> dict:
    """Get simple admin dashboard stats without country code."""
    total_revenue = (
        db.query(sqlfunc.sum(Payment.amount))
        .filter(Payment.status == "completed")
        .scalar()
        or 0
    )
    total_users = db.query(sqlfunc.count(UserModel.id)).scalar() or 0
    total_orders = db.query(sqlfunc.count(OrderModel.id)).scalar() or 0
    pending_payouts = db.query(PayoutModel).filter(
        PayoutModel.status == "pending"
    ).count()

    return {
        "total_revenue": float(total_revenue),
        "total_users": total_users,
        "total_orders": total_orders,
        "active_sessions": 0,
        "pending_payouts": pending_payouts,
    }


def list_payouts_fallback(db: Session, skip: int = 0, limit: int = 20) -> list:
    return db.query(PayoutModel).order_by(PayoutModel.id.desc()).offset(skip).limit(limit).all()


def list_categories_fallback(db: Session, skip: int = 0, limit: int = 20) -> list:
    return db.query(CategoryModel).order_by(CategoryModel.id.desc()).offset(skip).limit(limit).all()


def get_commission_config(db: Session):
    return db.query(CommissionGlobalConfig).first()


def list_payments_fallback(db: Session, skip: int = 0, limit: int = 20) -> list:
    return db.query(Payment).order_by(Payment.id.desc()).offset(skip).limit(limit).all()


def list_shipping_carriers_fallback(db: Session, supplier_id=None, active_only: bool = False) -> list:
    q = db.query(ShippingCarrier)
    if supplier_id is not None:
        q = q.filter(ShippingCarrier.supplier_id == supplier_id)
    if active_only:
        q = q.filter(ShippingCarrier.is_active == True)
    return q.all()


def get_shipping_zone_count(db: Session) -> int:
    return db.query(ShippingZone).filter(ShippingZone.is_active == True).count()


def get_shipment_count(db: Session) -> int:
    return db.query(Shipment).count()


def get_accounting_summary(db: Session, account_id=None) -> dict:
    if account_id is not None:
        balance = (
            db.query(sqlfunc.sum(AccountBalanceModel.balance))
            .filter(AccountBalanceModel.account_id == account_id)
            .scalar() or 0
        )
        return {"balance": float(balance)}
    return {
        "total_accounts": db.query(AccountModel).count(),
        "total_balance": 0.0,
    }


def list_accounts_fallback(db: Session, skip: int = 0, limit: int = 20) -> list:
    return db.query(AccountModel).offset(skip).limit(limit).all()


# ── Query builders (for cursor-paginated fallback routes) ─────────────────

def list_payouts_query(db: Session):
    """Return the payouts query (newest first) for cursor pagination."""
    return db.query(PayoutModel).order_by(PayoutModel.id.desc())


def list_categories_query(db: Session):
    """Return the categories query (newest first) for cursor pagination."""
    return db.query(CategoryModel).order_by(CategoryModel.id.desc())


def list_payments_query(db: Session):
    """Return the payments query (newest first) for cursor pagination."""
    return db.query(Payment).order_by(Payment.id.desc())


def list_accounts_query(db: Session):
    """Return the accounts query (by id) for cursor pagination."""
    return db.query(AccountModel).order_by(AccountModel.id.asc())


def list_employees_query(db: Session):
    """Return the employees query joined with user names for cursor pagination."""
    return (
        db.query(Employee)
        .join(UserModel, Employee.user_id == UserModel.id)
        .order_by(UserModel.full_name.asc().nullslast(), Employee.id)
    )


def get_fallback_admin_stats(db: Session) -> dict:
    """Aggregate admin stats used by the /stats fallback route."""
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


def get_treasury_cash_total(db: Session) -> float:
    """Sum of all account balances (treasury cash)."""
    total = (
        db.query(sqlfunc.sum(AccountBalanceModel.balance))
        .select_from(AccountBalanceModel)
        .scalar()
        or 0
    )
    return float(total)
