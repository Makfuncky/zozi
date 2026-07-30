"""Address routes with compatibility for the recovered customer address contract."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from models import Address

router = APIRouter()


def _normalize_address_payload(payload: dict, *, partial: bool = False) -> dict:
    street = payload.get("street", payload.get("address_line1"))
    state = payload.get("state", payload.get("region"))
    postal_code = payload.get("postal_code", payload.get("zip"))
    normalized = {
        "label": payload.get("label"),
        "street": street,
        "city": payload.get("city"),
        "state": state,
        "postal_code": postal_code,
        "country": payload.get("country"),
        "is_default": payload.get("is_default"),
    }
    if partial:
        return {key: value for key, value in normalized.items() if value is not None}
    required = {"street": street, "city": payload.get("city"), "country": payload.get("country")}
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Missing required fields: {', '.join(missing)}")
    return normalized


def _serialize_address(address: Address) -> dict:
    return {
        "id": address.id,
        "user_id": address.user_id,
        "label": getattr(address, "label", None),
        "street": address.address_line1,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "is_default": address.is_default,
        "full_name": address.full_name,
        "phone": address.phone,
        "created_at": address.created_at,
    }


def _get_user_address(address_id: int, user_id: int, db: Session) -> Address:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    return address


@router.get("")
def list_addresses(limit: int = 100, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Address)
        .filter(Address.user_id == int(current_user["id"]))
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 100))
        .all()
    )
    return [_serialize_address(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_address(payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    normalized = _normalize_address_payload(payload)
    user_id = int(current_user["id"])
    if normalized.get("is_default"):
        db.query(Address).filter(Address.user_id == user_id).update({"is_default": False})
    address = Address(
        user_id=user_id,
        full_name="Customer",
        address_line1=normalized.get("street", ""),
        city=normalized.get("city", ""),
        state=normalized.get("state"),
        postal_code=normalized.get("postal_code"),
        country=normalized.get("country", "US"),
        is_default=normalized.get("is_default", False),
    )
    if normalized.get("label"):
        address.label = normalized["label"]
    if normalized.get("phone"):
        address.phone = normalized["phone"]
    db.add(address)
    db.commit()
    db.refresh(address)
    return _serialize_address(address)


@router.put("/{address_id}")
def update_address(address_id: int, payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    updates = _normalize_address_payload(payload, partial=True)
    if updates.get("is_default") is True:
        db.query(Address).filter(Address.user_id == address.user_id).update({"is_default": False})
    if "street" in updates:
        address.address_line1 = updates.pop("street")
    for key, value in updates.items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return _serialize_address(address)


@router.delete("/{address_id}")
def delete_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    db.delete(address)
    db.commit()
    return {"detail": "Deleted"}


@router.post("/{address_id}/set-default")
def set_default_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    db.query(Address).filter(Address.user_id == user_id).update({"is_default": False})
    address = _get_user_address(address_id, user_id, db)
    address.is_default = True
    db.commit()
    db.refresh(address)
    return _serialize_address(address)

