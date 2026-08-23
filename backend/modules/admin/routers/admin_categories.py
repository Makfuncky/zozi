"""Admin categories router."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from domains.governance.services.settings.misc_service import archive_entity
from domains.catalog.services.bulk_ops_write_service import bulk_archive_entities
from domains.catalog.services.bulk_ops_write_service import bulk_restore_entities
from domains.governance.services.settings.misc_service import restore_entity
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
from domains.governance.models.user import User
from domains.catalog.models.products import Category
from domains.catalog.services.products_write_service import create_category as create_category_model
from domains.catalog.services.products_write_service import update_category as update_category_model
from domains.catalog.services.products_write_service import delete_category as delete_category_model
from domains.catalog.services.products_write_service import reorder_categories as reorder_categories_model
from domains.catalog.utils.category_tree import rebuild_category_paths
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

router = APIRouter()


@router.get("/categories/{country_code}")
def list_categories(country_code: str = Path(..., description="ISO country code"), include_deleted: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Category).filter(Category.country_code == country_code.upper())
        if not include_deleted: q = q.filter(Category.is_active == True)
        total = q.count()
        rows = q.order_by(Category.sort_order).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}")
def create_category(country_code: str = Path(..., description="ISO country code"), name: str = None, slug: str = None, parent_id: int = None, sort_order: int = 0, description: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat_data = {
            "name": name,
            "slug": slug,
            "parent_id": parent_id,
            "sort_order": sort_order,
            "description": description,
            "country_code": country_code.upper(),
        }
        cat = create_category_model(db, **cat_data)
        rebuild_category_paths(db)
        return cat
    finally:
        clear_rls_context()


@router.put("/categories/{country_code}/{category_id}")
def update_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), name: str = None, slug: str = None, parent_id: int = None, sort_order: int = None, description: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat = db.query(Category).filter(Category.id == category_id, Category.country_code == country_code.upper()).first()
        if not cat: raise HTTPException(404)
        updates = {}
        if name is not None: updates["name"] = name
        if slug is not None: updates["slug"] = slug
        if parent_id is not None: updates["parent_id"] = parent_id
        if sort_order is not None: updates["sort_order"] = sort_order
        if description is not None: updates["description"] = description
        cat = update_category_model(db, cat, updates)
        rebuild_category_paths(db)
        return cat
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/{category_id}/archive")
def archive_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), payload: ArchiveRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/{category_id}/restore")
def restore_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/reorder")
def reorder_categories(country_code: str = Path(..., description="ISO country code"), order: dict = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        reorder_categories_model(db, {int(k): v for k, v in order.items()})
        return {"message": "Categories reordered"}
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/bulk/archive")
def bulk_archive_categories(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/bulk/restore")
def bulk_restore_categories(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.delete("/categories/{country_code}/{category_id}")
def delete_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat = db.query(Category).filter(Category.id == category_id, Category.country_code == country_code.upper()).first()
        if not cat: raise HTTPException(404)
        delete_category_model(db, cat)
        return {"message": "Category deleted"}
    finally:
        clear_rls_context()

