"""Admin bulk operations controller."""
from __future__ import annotations

from typing import Any, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import (
    Product, User, Order, Category, Coupon, Banner, FlashSale,
    SupplierProfile, LogisticsPartner, CountryConfig, Payout, Shipment,
    Invoice, SupportTicket, ReturnRequest, SupplierDocument, Review
)
from services.core.admin_operations_service import archive_entity

from services.write_helpers import commit_only

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
    result = bulk_soft_delete(db, model, record_ids, acting_user, reason)
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
    result = bulk_restore(db, model, record_ids, acting_user)
    return {"message": f"{len(record_ids)} {model_name}(s) restored", **result}


def bulk_category_change(
    product_ids: List[int],
    category_id: int,
    acting_user: dict,
    db: Session,
    reason: Optional[str] = None,
) -> dict:
    """Change category for multiple products at once."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    updated = 0
    for pid in product_ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product and not product.is_deleted:
            product.category_id = category_id
            product.category = category.name
            updated += 1
    commit_only(db)
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


