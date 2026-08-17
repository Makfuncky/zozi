"""Auto-migrated service logic from routers/admin_products.py."""
from __future__ import annotations

from fastapi import Body, Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

from modules.admin.routers.admin_controller import (
    archive_entity,
    bulk_archive_entities,
    bulk_category_change,
    bulk_product_moderation,
    bulk_restore_entities,
    hard_delete_entity,
    restore_entity,
)

from modules.products.routers.products_controller import _bump_product_cache_version

from infrastructure.database.database import get_db

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest

from _legacy.models import Product

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin, require_super_admin

from infrastructure.utils.pagination import paginated_response

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

def list_all_products(country_code: str, page: int, size: int, moderation_status: str, include_deleted: bool, _, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Product).filter(Product.country_code == country_code.upper())
        if moderation_status: q = q.filter(Product.moderation_status == moderation_status)
        if not include_deleted: q = q.filter(Product.is_deleted == False)
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()

def approve_product(country_code: str, product_id: int, _, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.moderation_status = "approved"; p.is_verified = True
        db.commit()
        _bump_product_cache_version()
        return {"message": "Product approved"}
    finally:
        clear_rls_context()

def reject_product(country_code: str, product_id: int, reason: str, _, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.moderation_status = "rejected"; p.moderation_notes = reason
        db.commit()
        _bump_product_cache_version()
        return {"message": "Product rejected"}
    finally:
        clear_rls_context()

def update_product_badge(country_code: str, product_id: int, field: str, value: bool, _, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        if field not in ("is_hot", "is_featured"):
            raise HTTPException(400, "field must be 'is_hot' or 'is_featured'")
        setattr(p, field, value)
        db.commit()
        _bump_product_cache_version()
        return {"message": "Product badge updated", "field": field, "value": value}
    finally:
        clear_rls_context()

def bulk_archive_products(country_code: str, payload: BulkActionRequest, _, db: Session, current_user):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()

def bulk_restore_products(country_code: str, payload: BulkActionRequest, _, db: Session, current_user):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def bulk_moderate_products(country_code: str, payload: dict, _, db: Session, current_user):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        product_ids = payload.get("product_ids", [])
        action = payload.get("action")
        if not product_ids or action not in ("approve", "reject"):
            raise HTTPException(400, "product_ids and action (approve/reject) are required")
        return bulk_product_moderation(product_ids, action, payload.get("note"), {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def bulk_change_category(country_code: str, payload: BulkCategoryChangeRequest, _, db: Session, current_user):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_category_change(payload.ids, payload.category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()

def archive_product(country_code: str, product_id: int, payload: ArchiveRequest, _, db: Session, current_user):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()

def restore_product_route(country_code: str, product_id: int, _, db: Session, current_user):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

def delete_product_permanent(country_code: str, product_id: int, _, db: Session, current_user):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


