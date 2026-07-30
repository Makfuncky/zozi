"""Admin products router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from db.database import get_db
from models import Product
from db.schemas import ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest
from utils.dependencies import require_admin, require_super_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.pagination import paginated_response
from controllers.admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, bulk_product_moderation, bulk_category_change
from controllers.products_controller import _bump_product_cache_version

router = APIRouter()


@router.get("/products/{country_code}")
def list_all_products(country_code: str = Path(..., description="ISO country code"), page: int = Query(1, ge=1), size: int = Query(50), moderation_status: str = None, include_deleted: bool = False, _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Product).filter(Product.country_code == country_code.upper())
        if moderation_status: q = q.filter(Product.moderation_status == moderation_status)
        if not include_deleted: q = q.filter(Product.is_deleted == False)
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()


@router.put("/products/{country_code}/{product_id}/approve")
def approve_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_admin), db: Session = Depends(get_db)):
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


@router.put("/products/{country_code}/{product_id}/reject")
def reject_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), reason: str = None, _=Depends(require_admin), db: Session = Depends(get_db)):
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


@router.patch("/products/{country_code}/{product_id}/badge")
def update_product_badge(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), field: str = Body(...), value: bool = Body(...), _=Depends(require_admin), db: Session = Depends(get_db)):
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
        return {"message": f"Product badge updated", "field": field, "value": value}
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/bulk/archive")
def bulk_archive_products(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/bulk/restore")
def bulk_restore_products(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/bulk/moderate")
def bulk_moderate_products(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
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


@router.post("/products/{country_code}/bulk/category-change")
def bulk_change_category(country_code: str = Path(..., description="ISO country code"), payload: BulkCategoryChangeRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_category_change(payload.ids, payload.category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/{product_id}/archive")
def archive_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), payload: ArchiveRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/{product_id}/restore")
def restore_product_route(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.delete("/products/{country_code}/{product_id}")
def delete_product_permanent(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_super_admin), db: Session = Depends(get_db), current_user=Depends(require_super_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

