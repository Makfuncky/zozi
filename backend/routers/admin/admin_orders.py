"""Admin orders router — country-scoped."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from db.database import get_db
from models import Order, User
from db.schemas import CursorPage, OrderOut, OrderStatusUpdate, ArchiveRequest, BulkActionRequest, BulkStatusUpdateRequest
from utils.dependencies import require_admin, require_super_admin
from utils.country_rls import enforce_country_access, get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.pagination import cursor_paginate_desc
from services.admin.admin_operations import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, update_order_status
from utils.audit_log import audit_log
from services.orders_write_service import update_order

router = APIRouter()


@router.get("/orders/{country_code}", response_model=CursorPage)
def list_all_orders(
    country_code: str = Path(..., description="ISO country code, or '*' for all"),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(50, ge=1, le=100),
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
        return cursor_paginate_desc(q.order_by(Order.id.desc()), cursor=cursor, page_size=limit)
    finally:
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
        from utils.rls_interceptor import clear_rls_context
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
        from utils.rls_interceptor import clear_rls_context
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
        from utils.rls_interceptor import clear_rls_context
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
        from utils.rls_interceptor import clear_rls_context
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
        from utils.rls_interceptor import clear_rls_context
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
                update_order(db, o, {"status": payload.status})
                updated += 1
        return {"message": f"Status updated for {updated} orders", "updated": updated}
    finally:
        from utils.rls_interceptor import clear_rls_context
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
        from utils.rls_interceptor import clear_rls_context
        clear_rls_context()
