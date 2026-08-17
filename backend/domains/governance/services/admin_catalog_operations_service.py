"""Admin products router."""
from fastapi import Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from db.database import get_db
from models import Product
from db.schemas import ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest
from utils.dependencies import require_admin, require_super_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.pagination import paginated_response
from controllers.admin.admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, bulk_product_moderation, bulk_category_change
from controllers.products.products_controller import _bump_product_cache_version

def list_all_products(country_code: str=Path(..., description='ISO country code'), page: int=Query(1, ge=1), size: int=Query(50), moderation_status: str=None, include_deleted: bool=False, _=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Product).filter(Product.country_code == country_code.upper())
        if moderation_status:
            q = q.filter(Product.moderation_status == moderation_status)
        if not include_deleted:
            q = q.filter(Product.is_deleted == False)
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()

def approve_product(country_code: str=Path(..., description='ISO country code'), product_id: int=Path(...), _=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        p.moderation_status = 'approved'
        p.is_verified = True
        db.commit()
        _bump_product_cache_version()
        return {'message': 'Product approved'}
    finally:
        clear_rls_context()

def reject_product(country_code: str=Path(..., description='ISO country code'), product_id: int=Path(...), reason: str=None, _=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        p.moderation_status = 'rejected'
        p.moderation_notes = reason
        db.commit()
        _bump_product_cache_version()
        return {'message': 'Product rejected'}
    finally:
        clear_rls_context()

def update_product_badge(country_code: str=Path(..., description='ISO country code'), product_id: int=Path(...), field: str=Body(...), value: bool=Body(...), _=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        if field not in ('is_hot', 'is_featured'):
            raise HTTPException(400, "field must be 'is_hot' or 'is_featured'")
        setattr(p, field, value)
        db.commit()
        _bump_product_cache_version()
        return {'message': f'Product badge updated', 'field': field, 'value': value}
    finally:
        clear_rls_context()
