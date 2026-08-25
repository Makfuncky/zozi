"""Customer accounts router — consolidated from 3 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/customer/accounts", tags=["customer", "accounts"])


# === From addresses.py ===
"""Address routes with compatibility for the recovered customer address contract."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from infrastructure.utils.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.accounts.models.core import Address
from domains.accounts.services.addresses.addresses_service import create_address as create_address_model
from domains.accounts.services.addresses.addresses_service import update_address as update_address_model
from domains.accounts.services.addresses.addresses_service import delete_address as delete_address_model
from domains.accounts.services.addresses.addresses_service import set_default_address as set_default_address_model
from domains.customers.services.commerce_write_service import unset_other_default_addresses
from domains.customers.services.commerce_read_service import list_user_addresses
from domains.customers.services.commerce_read_service import get_user_address

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
    return get_user_address(db, address_id, user_id)


@router.get("")
def list_addresses(limit: int = 100, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = list_user_addresses(db, current_user["id"], limit, offset)
    return [_serialize_address(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_address(payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    normalized = _normalize_address_payload(payload)
    user_id = int(current_user["id"])
    if normalized.get("is_default"):
        unset_other_default_addresses(db, user_id)
    address_data = {
        "user_id": user_id,
        "full_name": "Customer",
        "address_line1": normalized.get("street", ""),
        "city": normalized.get("city", ""),
        "state": normalized.get("state"),
        "postal_code": normalized.get("postal_code"),
        "country": normalized.get("country", "US"),
        "is_default": normalized.get("is_default", False),
    }
    if normalized.get("label"):
        address_data["label"] = normalized["label"]
    if normalized.get("phone"):
        address_data["phone"] = normalized["phone"]
    address = create_address_model(db, **address_data)
    return _serialize_address(address)


@router.put("/{address_id}")
def update_address(address_id: int, payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    updates = _normalize_address_payload(payload, partial=True)
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, int(current_user["id"]), address_id)
    if "street" in updates:
        updates.pop("street")
    address = update_address_model(db, address, updates)
    return _serialize_address(address)


@router.delete("/{address_id}")
def delete_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    delete_address_model(db, address)
    return {"detail": "Deleted"}


@router.post("/{address_id}/set-default")
def set_default_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    unset_other_default_addresses(db, user_id, address_id)
    address = _get_user_address(address_id, user_id, db)
    address = set_default_address_model(db, address)
    return _serialize_address(address)



# === From auth.py ===
"""Auth router for customer module."""
from fastapi import APIRouter



# === From customer.py ===
"""Customer profile router — coins and recommendations."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.utils.dependencies import get_current_user
from domains.customers.services.coins.zozi_coins_service import get_coin_summary, redeem_coins
from domains.customers.services.recommendations.recommendation_service import get_may_you_like, get_last_seen

# ── Zozi Coins ─────────────────────────────────────────────────────────────────

@router.get("/coins")
def customer_get_coins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated customer's coin balance and history."""
    return get_coin_summary(db, current_user.id)


@router.post("/coins/redeem")
def customer_redeem_coins(
    points: int = Query(..., gt=0, description="Number of coins to redeem"),
    reason: str = Query("redemption", description="Reason for redemption"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Redeem coins from the authenticated customer's balance."""
    return redeem_coins(db, current_user.id, points, reason=reason)


# ── Recommendations ────────────────────────────────────────────────────────────

@router.get("/recommendations")
def customer_get_recommendations(
    limit: int = Query(8, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get personalized product recommendations for the authenticated customer."""
    return get_may_you_like(db, current_user.id, limit=limit)


@router.get("/last-seen")
def customer_get_last_seen(
    limit: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recently viewed products for the authenticated customer."""
    return get_last_seen(db, current_user.id, limit=limit)

