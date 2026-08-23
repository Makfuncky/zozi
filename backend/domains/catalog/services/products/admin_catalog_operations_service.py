"""Admin products router."""
from fastapi import Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.catalog.models.products import Product
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest
from infrastructure.utils.dependencies import require_admin, require_super_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.pagination import paginated_response
from domains.governance.services.core.bulk_ops_service import bulk_category_change  # noqa: F401


def bulk_product_moderation(product_ids, action, note, current_user, db):
    """Re-export: defers to canonical implementation to avoid circular import."""
    from domains.governance.services.products.products_service import bulk_product_moderation as _impl
    return _impl(product_ids, action, note, current_user, db)

# Re-export for backward compatibility with legacy module-level imports
__all__ = ["approve_product", "reject_product", "bulk_category_change", "list_all_products", "update_product_badge"]

def list_all_products(country_code: str = Path(..., description='ISO country code'), page: int = Query(1, ge=1), size: int = Query(50), moderation_status: str = None, include_deleted: bool = False, _=Depends(require_admin), db: Session = Depends(get_db)):
    """List all products with optional filtering and pagination."""
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

def approve_product(country_code: str = Path(..., description='ISO country code'), product_id: int = Path(...), _=Depends(require_admin), db: Session = Depends(get_db)):
    """Approve a product after moderation."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        p.moderation_status = 'approved'
        p.is_verified = True
        db.commit()
        from domains.catalog.ports import _bump_product_cache_version
        _bump_product_cache_version()
        return {'message': 'Product approved'}
    finally:
        clear_rls_context()


def reject_product(country_code: str = Path(..., description='ISO country code'), product_id: int = Path(...), reason: str = None, _=Depends(require_admin), db: Session = Depends(get_db)):
    """Reject a product after moderation."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        p.moderation_status = 'rejected'
        p.moderation_notes = reason
        db.commit()
        from domains.catalog.ports import _bump_product_cache_version
        _bump_product_cache_version()
        return {'message': 'Product rejected'}
    finally:
        clear_rls_context()


def update_product_badge(country_code: str = Path(..., description='ISO country code'), product_id: int = Path(...), field: str = Body(...), value: bool = Body(...), _=Depends(require_admin), db: Session = Depends(get_db)):
    """Update product badge flags (is_hot, is_featured)."""
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
        from domains.catalog.ports import _bump_product_cache_version
        _bump_product_cache_version()
        return {'message': f'Product badge updated', 'field': field, 'value': value}
    finally:
        clear_rls_context()
