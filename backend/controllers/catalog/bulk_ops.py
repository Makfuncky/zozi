"""Admin bulk operations controller."""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import (
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
from utils.audit import AuditAction, audit_log
from services.common.db_read import first
from services.catalog.bulk_ops_write_service import (
    bulk_archive_entities as _archive_entities,
    bulk_restore_entities as _restore_entities,
    bulk_change_product_category as _change_product_category,
)
import structlog
logger = structlog.get_logger(__name__)


def bulk_archive_entities(
    model_name: str,
    record_ids: List[int],
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    """Bulk archive for any entity."""
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
    result = _archive_entities(db, model, record_ids, acting_user, reason)
    return {"message": f"{len(record_ids)} {model_name}(s) archived", **result}


def bulk_restore_entities(
    model_name: str,
    record_ids: List[int],
    acting_user: dict,
    db: Session,
) -> dict:
    """Bulk restore for any entity."""
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
    result = _restore_entities(db, model, record_ids, acting_user)
    return {"message": f"{len(record_ids)} {model_name}(s) restored", **result}


def bulk_category_change(
    product_ids: List[int],
    category_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    """Change category for multiple products at once."""
    try:
        updated = _change_product_category(db, product_ids, category_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")
    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user.get("id"),
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=None,
        details={"action": "bulk_category_change", "product_ids": product_ids, "category_id": category_id, "reason": reason},
        status="success",
    )
    return {"message": f"Category changed for {updated} products", "updated": updated}
