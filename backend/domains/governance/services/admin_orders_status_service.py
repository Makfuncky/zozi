"""Admin orders router — country-scoped."""
from fastapi import Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from db.database import get_db
from _legacy.models import Order, User
from db.schemas import OrderOut, OrderStatusUpdate, ArchiveRequest, BulkActionRequest, BulkStatusUpdateRequest
from utils.dependencies import require_admin, require_super_admin
from controllers.admin.admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, update_order_status
from utils.audit import audit_log
from utils.country_rls import enforce_country_access, get_country_or_404
from utils.rls_interceptor import set_rls_context
import math

def list_all_orders(country_code: str=Path(..., description="ISO country code, or '*' for all"), page: int=Query(1, ge=1), size: int=Query(50), status: str=None, include_deleted: bool=False, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    if country_code == '*':
        set_rls_context(None, is_restricted=False)
    else:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Order)
        if status:
            q = q.filter(Order.status == status)
        if not include_deleted:
            q = q.filter(Order.is_deleted == False)
        total = q.count()
        items = q.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return {'items': items, 'total': total, 'page': page, 'pages': math.ceil(total / size) if total else 1}
    finally:
        from utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def bulk_update_order_status(country_code: str=Path(..., description='ISO country code'), payload: BulkStatusUpdateRequest=..., _: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        updated = 0
        for oid in payload.ids:
            o = db.query(Order).filter(Order.id == oid).first()
            if o:
                o.status = payload.status
                updated += 1
        db.commit()
        return {'message': f'Status updated for {updated} orders', 'updated': updated}
    finally:
        from utils.rls_interceptor import clear_rls_context
        clear_rls_context()
