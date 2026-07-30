"""Admin categories router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from db.database import get_db
from models import Category, User
from db.schemas import ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.category_tree import rebuild_category_paths
from controllers.admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity

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
        cat = Category(name=name, slug=slug, parent_id=parent_id, sort_order=sort_order, description=description, country_code=country_code.upper())
        db.add(cat); db.flush()
        rebuild_category_paths(db)
        db.commit(); db.refresh(cat)
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
        if name is not None: cat.name = name
        if slug is not None: cat.slug = slug
        if parent_id is not None: cat.parent_id = parent_id
        if sort_order is not None: cat.sort_order = sort_order
        if description is not None: cat.description = description
        db.flush()
        rebuild_category_paths(db)
        db.commit(); db.refresh(cat)
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
        for cid, pos in order.items():
            cat = db.query(Category).filter(Category.id == int(cid), Category.country_code == country_code.upper()).first()
            if cat: cat.sort_order = pos
        db.commit()
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
        db.delete(cat); db.commit()
        return {"message": "Category deleted"}
    finally:
        clear_rls_context()

