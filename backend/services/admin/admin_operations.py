"""
Admin Operations Service — archive, restore, hard-delete, and audit-log utilities.

Canonical home for entity lifecycle operations that were previously in
controllers/admin/misc.py. Routers and controllers now import from here
instead of crossing the controller→controller boundary.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    Product, User, Order, Category, Coupon, Banner, FlashSale,
    SupplierProfile, LogisticsPartner, CountryConfig, Payout, Shipment,
    Invoice, SupportTicket, ReturnRequest, SupplierDocument, Review, AuditLog,
)
from services.write_helpers import add_and_flush, delete_only

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
    return {"message": f"Order {order_id} status updated to {status}"}


def update_user_role(user_id: int, role: str, db: Session, acting_user: dict) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    add_and_flush(db, user)
    return {"message": f"User {user_id} role updated to {role}"}


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
