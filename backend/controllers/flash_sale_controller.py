"""Flash Sale controller — CRUD for time-limited discount campaigns."""
import json
from datetime import datetime, timezone
from typing import Any, List, Optional, cast

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from controllers.audit_controller import audit_log, AuditAction
from utils.cache import build_versioned_cache_key, bump_cache_version, cache_get_json, cache_set_json
from controllers.products_controller import _bump_product_cache_version
from models import FlashSale
from db.schemas import FlashSaleCreate, FlashSaleOut
from utils.datetime_utils import utcnow as _utcnow

_FLASH_SALE_CACHE_TTL = 45


def _build_list_page_payload(items: list[Any], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict[str, Any]:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }


def get_active_flash_sales(db: Session) -> List[FlashSaleOut]:
    """Return all currently-active flash sales (public endpoint)."""
    cache_key = build_versioned_cache_key("flash-sales", "active", {"scope": "public"})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, list):
        return cached_payload

    now = _utcnow()
    sales = (
        db.query(FlashSale)
        .filter(
            FlashSale.is_active.is_(True),
            FlashSale.starts_at <= now,
            FlashSale.ends_at >= now,
        )
        .order_by(FlashSale.ends_at)
        .all()
    )
    serialized = [jsonable_encoder(FlashSaleOut.model_validate(s)) for s in sales]
    cache_set_json(cache_key, serialized, _FLASH_SALE_CACHE_TTL)
    return serialized


def get_all_flash_sales(
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict[str, Any]:
    """Return all flash sales (admin only)."""
    query = db.query(FlashSale)
    if search and search.strip():
        query = query.filter(FlashSale.title.ilike(f"%{search.strip()}%"))
    total = query.count()
    query = query.order_by(FlashSale.created_at.desc(), FlashSale.id.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    sales = query.all()
    serialized = [jsonable_encoder(FlashSaleOut.model_validate(sale)) for sale in sales]
    return _build_list_page_payload(serialized, total, offset=offset, page_size=limit if limit is not None else len(serialized))


def create_flash_sale(body: FlashSaleCreate, current_admin: dict, db: Session) -> FlashSaleOut:
    """Create a new flash sale (admin only)."""
    if body.discount_pct < 0 or body.discount_pct > 100:
        raise HTTPException(status_code=422, detail="discount_pct must be between 0 and 100")
    if body.ends_at <= body.starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be after starts_at")

    sale = FlashSale(
        title=body.title.strip(),
        discount_pct=body.discount_pct,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        is_active=body.is_active,
        product_ids=json.dumps(body.product_ids) if body.product_ids is not None else None,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    audit_log(
        db,
        action=AuditAction.FLASH_SALE_CREATED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="flash_sale",
        resource_id=cast(int, getattr(sale, "id")),
        details={"title": sale.title, "discount_pct": sale.discount_pct},
    )
    bump_cache_version("flash-sales")
    _bump_product_cache_version()
    return FlashSaleOut.model_validate(sale)


def update_flash_sale(sale_id: int, body: FlashSaleCreate, current_admin: dict, db: Session) -> FlashSaleOut:
    """Update an existing flash sale (admin only)."""
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Flash sale not found")

    if body.discount_pct < 0 or body.discount_pct > 100:
        raise HTTPException(status_code=422, detail="discount_pct must be between 0 and 100")
    if body.ends_at <= body.starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be after starts_at")

    setattr(sale, "title", body.title.strip())
    setattr(sale, "discount_pct", body.discount_pct)
    setattr(sale, "starts_at", body.starts_at)
    setattr(sale, "ends_at", body.ends_at)
    setattr(sale, "is_active", body.is_active)
    setattr(sale, "product_ids", json.dumps(body.product_ids) if body.product_ids is not None else None)
    db.commit()
    db.refresh(sale)
    audit_log(
        db,
        action=AuditAction.FLASH_SALE_UPDATED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="flash_sale",
        resource_id=cast(int, getattr(sale, "id")),
        details={"title": sale.title, "discount_pct": sale.discount_pct},
    )
    bump_cache_version("flash-sales")
    _bump_product_cache_version()
    return FlashSaleOut.model_validate(sale)


def delete_flash_sale(sale_id: int, current_admin: dict, db: Session) -> dict:
    """Delete a flash sale (admin only)."""
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Flash sale not found")
    sale_title = sale.title
    db.delete(sale)
    db.commit()
    audit_log(
        db,
        action=AuditAction.FLASH_SALE_DELETED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="flash_sale",
        resource_id=sale_id,
        details={"title": sale_title},
    )
    bump_cache_version("flash-sales")
    _bump_product_cache_version()
    return {"detail": "Flash sale deleted"}

