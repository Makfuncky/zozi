"""Address routes with compatibility for the recovered customer address contract."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from data.db import get_db
from services.customer.customer_router_service import (
    list_addresses as list_addresses_service,
    create_address as create_address_service,
    update_address as update_address_service,
    delete_address as delete_address_service,
    set_default_address as set_default_address_service,
)

router = APIRouter()


@router.get("")
def list_addresses(limit: int = 100, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    return list_addresses_service(db, user_id, limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_address(payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    return create_address_service(db, user_id, payload)


@router.put("/{address_id}")
def update_address(address_id: int, payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    return update_address_service(db, address_id, user_id, payload)


@router.delete("/{address_id}")
def delete_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    return delete_address_service(db, address_id, user_id)


@router.post("/{address_id}/set-default")
def set_default_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    return set_default_address_service(db, address_id, user_id)