"""Returns router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from controllers.returns_controller import (
    bulk_update_return_requests,
    create_return_request,
    get_return_request,
    list_return_requests,
    update_return_request,
)
from data.db import get_db
from data.models import ReturnRequest, User
from data.schemas import ReturnRequestCreate, ReturnRequestOut, ReturnRequestUpdate
from utils.dependencies import get_current_user, require_admin
from services.orders.orders_router_service import (
    serialize_return_request,
    get_return_by_id,
    update_return_status,
)


router = APIRouter()


class BulkReturnStatusUpdateBody(BaseModel):
    return_ids: list[int]
    status: str
    resolution_notes: Optional[str] = None
    notes: Optional[str] = None


@router.get("", response_model=list[ReturnRequestOut])
def list_returns(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_ctx = {
        "id": getattr(current_user, "id", None),
        "username": getattr(current_user, "username", None),
        "role": getattr(current_user, "role", None),
    }
    requests = list_return_requests(user_ctx, db)
    return [serialize_return_request(req) for req in requests]


@router.post("", response_model=ReturnRequestOut, status_code=201)
def create_return(payload: ReturnRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_ctx = {
        "id": getattr(current_user, "id", None),
        "username": getattr(current_user, "username", None),
        "role": getattr(current_user, "role", None),
    }
    req = create_return_request(user_ctx, payload, db)
    return serialize_return_request(req)


@router.get("/{return_id}", response_model=ReturnRequestOut)
def get_return(return_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_ctx = {
        "id": getattr(current_user, "id", None),
        "username": getattr(current_user, "username", None),
        "role": getattr(current_user, "role", None),
    }
    req = get_return_request(return_id, user_ctx, db)
    return serialize_return_request(req)


@router.put("/bulk")
def bulk_update_returns(
    body: BulkReturnStatusUpdateBody,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user_ctx = {
        "id": getattr(current_user, "id", None),
        "username": getattr(current_user, "username", None),
        "role": getattr(current_user, "role", None),
    }
    payload = ReturnRequestUpdate(
        status=body.status,
        notes=body.resolution_notes if body.resolution_notes is not None else body.notes,
    )
    return bulk_update_return_requests(body.return_ids, payload, user_ctx, db)


@router.put("/{return_id}", response_model=ReturnRequestOut)
def update_return(
    return_id: int,
    payload: ReturnRequestUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user_ctx = {
        "id": getattr(current_user, "id", None),
        "username": getattr(current_user, "username", None),
        "role": getattr(current_user, "role", None),
    }
    req = update_return_request(return_id, payload, user_ctx, db)
    return serialize_return_request(req)


@router.put("/{return_id}/status")
def update_return_status_endpoint(return_id: int, status: str, notes: str = None, db: Session = Depends(get_db)):
    return update_return_status(db, return_id, status, notes)