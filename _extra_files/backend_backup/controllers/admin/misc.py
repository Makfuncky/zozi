"""Admin misc controller for archive and system utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    AuditLog,
    Banner,
    Category,
    CountryConfig,
    Coupon,
    FlashSale,
    Invoice,
    LogisticsPartner,
    Order,
    Payout,
    Product,
    ReturnRequest,
    Review,
    Shipment,
    SupplierDocument,
    SupplierProfile,
    SupportTicket,
    User,
)
from services.misc_write_service import (
    hard_delete_record as _hard_delete_record,
    restore_record as _restore_record,
    soft_delete_record as _soft_delete_record,
)


def soft_delete(db: Session, model: type, record_id: int, acting_user: dict, reason: Optional[str] = None) -> None:
    record = db.query(model).filter(model.id == record_id).first()
    if record:
        _soft_delete_record(db, record, reason)


def restore(db: Session, model: type, record_id: int, acting_user: dict) -> None:
    record = db.query(model).filter(model.id == record_id).first()
    if record:
        _restore_record(db, record)


def hard_delete(db: Session, model: type, record_id: int, acting_user: dict, reason: Optional[str] = None) -> None:
    record = db.query(model).filter(model.id == record_id).first()
    if record:
        _hard_delete_record(db, record)


def archive_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
    check_relations: Optional[list] = None,
) -> dict:
    """Generic archive for any entity. Optionally checks for dependent records."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")

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
    """Generic restore for any entity."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")
    restore(db, model, record_id, acting_user)
    return {"message": f"{model_name} restored", "id": record_id}


def hard_delete_entity(
    model_name: str,
    record_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    """Permanent delete (super admin only) for any entity."""
    model_map = {
        "product": Product, "user": User, "order": Order, "category": Category,
        "coupon": Coupon, "banner": Banner, "flash_sale": FlashSale,
        "supplier_profile": SupplierProfile, "logistics_partner": LogisticsPartner,
        "country_config": CountryConfig, "payout": Payout, "shipment": Shipment,
        "invoice": Invoice, "support_ticket": SupportTicket, "return_request": ReturnRequest,
        "supplier_document": SupplierDocument, "review": Review,
    }
    model = model_map.get(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {model_name}")
    hard_delete(db, model, record_id, acting_user, reason)
    return {"message": f"{model_name} permanently deleted", "id": record_id}


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
    """Get paginated audit log entries."""
    
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
    """Get list of unique audit actions."""
    result = db.query(AuditLog.action).distinct().all()
    return [row[0] for row in result]


# â”€â”€ Supplier Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

