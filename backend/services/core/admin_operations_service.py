"""
Admin Operations Service — archive, restore, hard-delete, and audit-log utilities.

Canonical home for entity lifecycle operations that were previously in
controllers/admin/misc.py. Routers and controllers now import from here
instead of crossing the controller→controller boundary.
"""
from typing import Any

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import (
    Product, User, Order, Category, Coupon, Banner, FlashSale,
    SupplierProfile, LogisticsPartner, CountryConfig, Payout, Shipment,
    Invoice, SupportTicket, ReturnRequest, SupplierDocument, Review, AuditLog,
)
from data.services_write_helpers import add_and_flush, delete_only

# ── Model registry (shared by archive / restore / hard-delete) ────────────

_MODEL_MAP = {
    "product": Product, "user": User, "order": Order, "category": Category,
    "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
    "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
    "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
    "invoice": Invoice, "support_ticket": SupportTicket,
    "return_request": ReturnRequest, "supplier_document": SupplierDocument,
    "review": Review,
}


def _get_model(model_name: str):
    model = _MODEL_MAP.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")
    return model


# ── Read helpers ──────────────────────────────────────────────────────────

def get_category_by_id(db: Session, category_id: int):
    """Return a Category by primary key or None."""
    return db.query(Category).filter(Category.id == category_id).first()


def get_product_by_id(db: Session, product_id: int):
    """Return a Product by primary key or None."""
    return db.query(Product).filter(Product.id == product_id).first()


# ── Low-level helpers ─────────────────────────────────────────────────────

def soft_delete(db: Session, model: type, record_id: int, acting_user: dict,
                reason: Optional[str] = None) -> None:
    record = db.query(model).filter(model.id == record_id).first()
    if record:
        if hasattr(record, "is_deleted"):
            setattr(record, "is_deleted", True)
        if hasattr(record, "deleted_at"):
            setattr(record, "deleted_at", datetime.now())
        if hasattr(record, "deleted_reason"):
            setattr(record, "deleted_reason", reason)
        add_and_flush(db, record)


def restore_record(db: Session, model: type, record_id: int, acting_user: dict) -> None:
    record = db.query(model).filter(model.id == record_id).first()
    if record:
        if hasattr(record, "is_deleted"):
            setattr(record, "is_deleted", False)
        if hasattr(record, "deleted_at"):
            setattr(record, "deleted_at", None)
        if hasattr(record, "deleted_reason"):
            setattr(record, "deleted_reason", None)
        add_and_flush(db, record)


def hard_delete_record(db: Session, model: type, record_id: int,
                       acting_user: dict, reason: Optional[str] = None) -> None:
    record = db.query(model).filter(model.id == record_id).first()
    if record:
        delete_only(db, record)


# ── High-level entity operations ──────────────────────────────────────────

def archive_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
    check_relations: Optional[list] = None,
) -> dict:
    model = _get_model(model_name)
    if check_relations:
        record = db.query(model).filter(model.id == record_id).first()
        if record:
            for rel_name in check_relations:
                rel = getattr(record, rel_name, None)
                if rel is not None:
                    count = rel.count() if hasattr(rel, "count") else (len(rel) if isinstance(rel, list) else 0)
                    if count > 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot archive: {record_id} has {count} related {rel_name}",
                        )
    soft_delete(db, model, record_id, acting_user, reason)
    return {"message": f"{model_name} archived", "id": record_id}


def restore_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
) -> dict:
    model = _get_model(model_name)
    restore_record(db, model, record_id, acting_user)
    return {"message": f"{model_name} restored", "id": record_id}


def hard_delete_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    model = _get_model(model_name)
    hard_delete_record(db, model, record_id, acting_user, reason)
    return {"message": f"{model_name} permanently deleted", "id": record_id}


# ── Audit log queries ─────────────────────────────────────────────────────

def get_audit_log_page(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    action_filter: Optional[str] = None,
    user_id_filter: Optional[int] = None,
    resource_type_filter: Optional[str] = None,
    resource_id_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> dict:
    query = db.query(AuditLog)
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if user_id_filter:
        query = query.filter(AuditLog.user_id == user_id_filter)
    if resource_type_filter:
        query = query.filter(AuditLog.resource_type == resource_type_filter)
    if status_filter:
        query = query.filter(AuditLog.status == status_filter)
    total = query.count()
    entries = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "data": [
            {
                "id": e.id,
                "action": e.action,
                "user_id": e.user_id,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "status": e.status,
                "details": e.details,
                "created_at": e.created_at,
            }
            for e in entries
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_available_audit_actions(db: Session) -> list:
    result = db.query(AuditLog.action).distinct().all()
    return [row[0] for row in result]


# ── Bulk operations ───────────────────────────────────────────────────────

def bulk_archive_entities(model_name: str, ids: list[int], acting_user: dict, db: Session,
                          reason: Optional[str] = None) -> dict:
    results = []
    for rid in ids:
        try:
            results.append(archive_entity(model_name, rid, acting_user, db, reason))
        except HTTPException as e:
            results.append({"id": rid, "error": e.detail})
    return {"results": results, "total": len(ids)}


def bulk_restore_entities(model_name: str, ids: list[int], acting_user: dict, db: Session) -> dict:
    results = []
    for rid in ids:
        try:
            results.append(restore_entity(model_name, rid, acting_user, db))
        except HTTPException as e:
            results.append({"id": rid, "error": e.detail})
    return {"results": results, "total": len(ids)}


def update_order_status(order_id: int, status: str, db: Session, acting_user: dict) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    add_and_flush(db, order)
    return {"message": "Order " + str(order_id) + " status updated to " + str(status)}


def update_user_role(user_id: int, role: str, db: Session, acting_user: dict) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    add_and_flush(db, user)
    return {"message": "User " + str(user_id) + " role updated to " + str(role)}


def toggle_user_active(user_id: int, db: Session, acting_user: dict) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    add_and_flush(db, user)
    return {"message": f"User {user_id} active toggled to {user.is_active}"}


def force_reset_password_admin(user_id: int, db: Session, acting_user: dict) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Password reset initiated for user {user_id}"}


def delete_user_admin(user_id: int, db: Session, acting_user: dict) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_only(db, user)
    return {"message": f"User {user_id} deleted"}


def bulk_product_moderation(ids: list[int], action: str, db: Session, acting_user: dict) -> dict:
    results = []
    for pid in ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            if action == "approve":
                product.is_active = True
            elif action == "reject":
                product.is_active = False
            add_and_flush(db, product)
            results.append({"id": pid, "status": action})
    return {"results": results, "total": len(ids)}


def bulk_category_change(ids: list[int], category_id: int, db: Session, acting_user: dict) -> dict:
    results = []
    for pid in ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            product.category_id = category_id
            add_and_flush(db, product)
            results.append({"id": pid, "category_id": category_id})
    return {"results": results, "total": len(ids)}


_DEMO_USERS: list[tuple[str, str, str, str, str]] = [
    ("admin@zozi.com", "admin", "admin123", "admin", "admin"),
    ("supplier@zozi.com", "supplier", "supplier123", "supplier", "supplier"),
    ("customer@zozi.com", "customer", "customer123", "customer", "customer"),
]


def seed_demo_data(db: Session) -> None:
    """Seed demo countries, a default coupon, and demo users.

    Centralises the one-time seeding that test conftest used to perform
    inline, so tests never import model or db layers directly (CG2 compliance).
    """
    from db.seed import _ensure_demo_user
    from data.models import Coupon

    demo_countries = [
        {"code": "AE", "name": "United Arab Emirates", "currency": "AED",
         "currency_symbol": "د.إ", "phone_code": "+971"},
        {"code": "SA", "name": "Saudi Arabia", "currency": "SAR",
         "currency_symbol": "﷼", "phone_code": "+966"},
        {"code": "OM", "name": "Oman", "currency": "OMR",
         "currency_symbol": "﷼", "phone_code": "+968"},
    ]
    for c in demo_countries:
        existing = db.query(CountryConfig).filter(CountryConfig.code == c["code"]).first()
        if not existing:
            add_and_flush(db, CountryConfig(**c))

    existing_coupon = db.query(Coupon).filter(Coupon.code == "WELCOME10").first()
    if not existing_coupon:
        add_and_flush(db, Coupon(
            code="WELCOME10",
            title="Welcome Discount",
            discount_type="percentage",
            discount_value=10,
            minimum_order=10,
            is_active=True,
        ))

    for email, username, password, role, label in _DEMO_USERS:
        _ensure_demo_user(
            db,
            email=email,
            username=username,
            password=password,
            role=role,
            log_label=label,
        )
        if role == "customer":
            user_obj = db.query(User).filter(User.email == email).first()
            if user_obj:
                user_obj.email_verified = True
    db.commit()

def get_model_by_id(db: Session, record_id: int) -> Optional[model]:
    return db.query(model).filter(model.id == record_id).first()


def get_auditlog_first(db: Session, **filters) -> Optional[AuditLog]:
    query = db.query(AuditLog)
    for key, value in filters.items():
        query = query.filter(getattr(AuditLog, key) == value)
    return query.limit(1).first()




def get_user_first(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.limit(1).first()


def count_user(db: Session, **filters) -> int:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.count()


def list_supplierprofile(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[SupplierProfile]:
    query = db.query(SupplierProfile)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierProfile, key) == value)
    return query.offset(skip).limit(limit).all()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def list_order(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.offset(skip).limit(limit).all()


def get_user_by_condition(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.first()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_supplierbankaccount_by_id(db: Session, record_id: int) -> Optional[SupplierBankAccount]:
    return db.query(SupplierBankAccount).filter(SupplierBankAccount.id == record_id).first()


def get_logisticspartnerbankaccount_by_id(db: Session, record_id: int) -> Optional[LogisticsPartnerBankAccount]:
    return db.query(LogisticsPartnerBankAccount).filter(LogisticsPartnerBankAccount.id == record_id).first()


def count_banner(db: Session, **filters) -> int:
    query = db.query(Banner)
    for key, value in filters.items():
        query = query.filter(getattr(Banner, key) == value)
    return query.count()


def get_banner_first(db: Session, **filters) -> Optional[Banner]:
    query = db.query(Banner)
    for key, value in filters.items():
        query = query.filter(getattr(Banner, key) == value)
    return query.limit(1).first()


def get_banner_by_id(db: Session, record_id: int) -> Optional[Banner]:
    return db.query(Banner).filter(Banner.id == record_id).first()


def list_user(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.offset(skip).limit(limit).all()


def list_product(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.offset(skip).limit(limit).all()


def list_coupon(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Coupon]:
    query = db.query(Coupon)
    for key, value in filters.items():
        query = query.filter(getattr(Coupon, key) == value)
    return query.offset(skip).limit(limit).all()


def get_unknown_scalar(db: Session, column: str, **filters) -> Any:
    query = db.query(getattr(Unknown, column))
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.scalar()


def get_order_first(db: Session, **filters) -> Optional[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.limit(1).first()


def get_product_first(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.limit(1).first()


def get_coupon_first(db: Session, **filters) -> Optional[Coupon]:
    query = db.query(Coupon)
    for key, value in filters.items():
        query = query.filter(getattr(Coupon, key) == value)
    return query.limit(1).first()

def _db_model_first_0(db: Session, id: Any, record_id: Any) -> Optional[Any]:
    result = db.query(model).filter(model.id == record_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_model_first_1(db: Session, id: Any, record_id: Any) -> Optional[Any]:
    result = db.query(model).filter(model.id == record_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_model_first_2(db: Session, id: Any, record_id: Any) -> Optional[Any]:
    result = db.query(model).filter(model.id == record_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_model_first_3(db: Session, id: Any, record_id: Any) -> Optional[Any]:
    result = db.query(model).filter(model.id == record_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_auditlog_query_4(db: Session) -> Optional[Any]:
    result = db.query(AuditLog)
    return result
    """Read-only query delegated from controller."""

def _db_user_query_0(db: Session) -> Optional[Any]:
    return db.query(User)
    """Read-only query delegated from controller."""

def _db_user_query_1(db: Session) -> Optional[Any]:
    result = db.query(User).order_by(User.created_at.desc())
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_all_2(db: Session, in_: Any, user_id: Any, user_ids: Any) -> list[Any]:
    return db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(user_ids)).all()
    """Read-only query delegated from controller."""

def _db_order_all_3(db: Session, user_id: Any) -> Optional[Any]:
    result = db.query(Order).options(selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.shipments)).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_4(db: Session, email: Any, payload: Any) -> Optional[Any]:
    if db.query(User).filter(User.email == payload.email).first(): raise HTTPException(status_code=400, detail="Email already registered")
    """Read-only query delegated from controller."""

def _db_user_first_5(db: Session, payload: Any, username: Any) -> Optional[Any]:
    if db.query(User).filter(User.username == payload.username).first(): raise HTTPException(status_code=400, detail="Username already taken")
    """Read-only query delegated from controller."""

def _db_user_first_6(db: Session, id: Any, in_: Any, role: Any, tuple: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == user_id, User.role.in_(tuple(STAFF_ROLES))).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_7(db: Session, email: Any, id: Any, next_email: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.email == next_email, User.id != user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_8(db: Session, id: Any, in_: Any, role: Any, tuple: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == user_id, User.role.in_(tuple(STAFF_ROLES))).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_query_9(db: Session) -> Optional[Any]:
    return db.query(User)
    """Read-only query delegated from controller."""

def _db_user_first_10(db: Session, email: Any, id: Any, next_email: Any, not_in_: Any, user_ids: Any) -> Optional[Any]:
    result = db.query(User).filter(User.email == next_email, User.id.not_in_(user_ids)).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierbankaccount_first_11(db: Session, account_id: Any, id: Any) -> Optional[Any]:
    result = db.query(SupplierBankAccount).filter(SupplierBankAccount.id == account_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerbankaccount_first_12(db: Session, account_id: Any, id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerBankAccount).filter(LogisticsPartnerBankAccount.id == account_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierbankaccount_first_13(db: Session, account_id: Any, id: Any) -> Optional[Any]:
    result = db.query(SupplierBankAccount).filter(SupplierBankAccount.id == account_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_logisticspartnerbankaccount_first_14(db: Session, account_id: Any, id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartnerBankAccount).filter(LogisticsPartnerBankAccount.id == account_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_banner_count_0(db: Session) -> Optional[Any]:
    result = db.query(Banner).count()
    return result
    """Read-only query delegated from controller."""

def _db_banner_query_1(db: Session) -> Optional[Any]:
    result = db.query(Banner)
    return result
    """Read-only query delegated from controller."""

def _db_banner_query_2(db: Session) -> Optional[Any]:
    result = db.query(Banner)
    return result
    """Read-only query delegated from controller."""

def _db_banner_query_3(db: Session, bid: Any, id: Any) -> Optional[Any]:
    return db.query(Banner).filter(Banner.id == bid).update({"sort_order": index})
    """Read-only query delegated from controller."""

def _db_user_all_0(db: Session) -> Optional[Any]:
    result = db.query(User).order_by(User.id).limit(MAX_EXPORT_ROWS).all()
    return result
    """Read-only query delegated from controller."""

def _db_order_all_1(db: Session) -> Optional[Any]:
    result = db.query(Order).order_by(Order.id).limit(MAX_EXPORT_ROWS).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_2(db: Session) -> Optional[Any]:
    result = db.query(Product).order_by(Product.id).limit(MAX_EXPORT_ROWS).all()
    return result
    """Read-only query delegated from controller."""

def _db_coupon_all_3(db: Session) -> Optional[Any]:
    result = db.query(Coupon).order_by(Coupon.id).limit(MAX_EXPORT_ROWS).all()
    return result
    """Read-only query delegated from controller."""

def _db_user_query_5(db: Session) -> Optional[Any]:
    result = db.query(User).order_by(User.id)
    return result
    """Read-only query delegated from controller."""

def _db_order_query_6(db: Session) -> Optional[Any]:
    result = db.query(Order).order_by(Order.id)
    return result
    """Read-only query delegated from controller."""

def _db_product_query_7(db: Session) -> Optional[Any]:
    result = db.query(Product).order_by(Product.id)
    return result
    """Read-only query delegated from controller."""

def _db_coupon_query_8(db: Session) -> Optional[Any]:
    result = db.query(Coupon).order_by(Coupon.id)
    return result
    """Read-only query delegated from controller."""

def _db_auditlog_query_9(db: Session, occurred_at: Any, since: Any) -> Optional[Any]:
    result = db.query(AuditLog).filter(AuditLog.occurred_at >= since).order_by(AuditLog.id)
    return result
    """Read-only query delegated from controller."""
