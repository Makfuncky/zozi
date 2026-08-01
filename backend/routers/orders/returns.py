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
from db.database import get_db
from models import ReturnRequest, User
from db.schemas import ReturnRequestCreate, ReturnRequestOut, ReturnRequestUpdate
from utils.dependencies import get_current_user, require_admin

from services.write_helpers import commit_only
router = APIRouter()


class BulkReturnStatusUpdateBody(BaseModel):
    return_ids: list[int]
    status: str
    resolution_notes: Optional[str] = None
    notes: Optional[str] = None


def _user_context(user: User) -> dict:
    return {
        "id": getattr(user, "id", None),
        "username": getattr(user, "username", None),
        "role": getattr(user, "role", None),
    }


def _serialize_return(req: ReturnRequest) -> dict:
    return {
        "id": getattr(req, "id", None),
        "order_id": getattr(req, "order_id", None),
        "order_item_id": getattr(req, "order_item_id", None),
        "customer_id": getattr(req, "user_id", None),
        "intent": getattr(req, "intent", "return"),
        "reason": getattr(req, "reason", None),
        "description": getattr(req, "description", None),
        "images": getattr(req, "images", None),
        "status": getattr(req, "status", None),
        "resolution": getattr(req, "resolution_notes", None),
        "resolution_notes": getattr(req, "resolution_notes", None),
        "refund_amount": getattr(req, "refund_amount", None),
        "items": getattr(req, "items", None),
        "return_window_days": getattr(req, "return_window_days", None),
        "delivered_at": getattr(req, "delivered_at", None),
        "return_deadline": getattr(req, "return_deadline", None),
        "created_at": getattr(req, "created_at", None),
        "updated_at": getattr(req, "updated_at", None),
    }

@router.get("", response_model=list[ReturnRequestOut])
def list_returns(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = list_return_requests(_user_context(current_user), db)
    return [_serialize_return(req) for req in requests]

@router.post("", response_model=ReturnRequestOut, status_code=201)
def create_return(payload: ReturnRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = create_return_request(_user_context(current_user), payload, db)
    return _serialize_return(req)


@router.get("/{return_id}", response_model=ReturnRequestOut)
def get_return(return_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = get_return_request(return_id, _user_context(current_user), db)
    return _serialize_return(req)


@router.put("/bulk")
def bulk_update_returns(
    body: BulkReturnStatusUpdateBody,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    payload = ReturnRequestUpdate(
        status=body.status,
        notes=body.resolution_notes if body.resolution_notes is not None else body.notes,
    )
    return bulk_update_return_requests(body.return_ids, payload, _user_context(current_user), db)


@router.put("/{return_id}", response_model=ReturnRequestOut)
def update_return(
    return_id: int,
    payload: ReturnRequestUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    req = update_return_request(return_id, payload, _user_context(current_user), db)
    return _serialize_return(req)

@router.put("/{return_id}/status")
def update_return_status(return_id: int, status: str, notes: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not r: raise HTTPException(404)
    r.status = status
    if notes: r.resolution_notes = notes
    commit_only(db)
    return {"message": "Updated"}

