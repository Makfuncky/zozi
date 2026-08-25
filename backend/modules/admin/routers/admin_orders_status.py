"""Admin orders router — country-scoped."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.orders.models.orders import Order
from infrastructure.database.schemas import OrderOut, OrderStatusUpdate, ArchiveRequest, BulkActionRequest, BulkStatusUpdateRequest
from infrastructure.utils.dependencies import require_admin, require_super_admin
from domains.governance.services.settings.misc_service import archive_entity
from domains.governance.services.settings.misc_service import restore_entity
from domains.catalog.services.products.bulk_ops_write_service import bulk_archive_entities
from domains.catalog.services.products.bulk_ops_write_service import bulk_restore_entities
from domains.governance.services.settings.misc_service import hard_delete_entity
from domains.orders.services.orders_service import update_order_status
from infrastructure.utils.audit import audit_log
from domains.country.utils.country_rls import enforce_country_access, get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context
import math

router = APIRouter(prefix="/api/v1/admin")


@router.get("/orders/{country_code}")
def list_all_orders(
    country_code: str = Path(..., description="ISO country code, or '*' for all"),
    page: int = Query(1, ge=1),
    size: int = Query(50),
    status: str = None,
    include_deleted: bool = False,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if country_code == "*":
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
        return {"items": items, "total": total, "page": page, "pages": math.ceil(total / size) if total else 1}
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()


@router.put("/orders/{country_code}/{order_id}/status")
def update_status(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    payload: OrderStatusUpdate = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        acting_user = {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
        }
        result = update_order_status(order_id, payload.status, acting_user, db)
        return {
            "message": "Updated",
            "from": result.get("old_status"),
            "to": result.get("new_status", payload.status),
        }
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()


@router.post("/orders/{country_code}/{order_id}/archive")
def archive_order(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    payload: ArchiveRequest = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity(
            "order",
            order_id,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
            payload.reason if payload else None,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()


@router.post("/orders/{country_code}/{order_id}/restore")
def restore_order(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity(
            "order",
            order_id,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()


@router.post("/orders/{country_code}/bulk/archive")
def bulk_archive_orders(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities(
            "order",
            payload.ids,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
            payload.reason,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()


@router.post("/orders/{country_code}/bulk/restore")
def bulk_restore_orders(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities(
            "order",
            payload.ids,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()


@router.post("/orders/{country_code}/bulk/status")
def bulk_update_order_status(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkStatusUpdateRequest = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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
        return {"message": f"Status updated for {updated} orders", "updated": updated}
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()


@router.delete("/orders/{country_code}/{order_id}")
def delete_order_permanent(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity(
            "order",
            order_id,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

