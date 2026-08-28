"""Supplier sub-module — imports shared helpers from supplier_shared."""

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from domains.accounts.models.user import User
from domains.catalog.models.products import Product
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.suppliers.services.supplier_shared import _sanitize_profile_string

def get_supplier_profile(current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from domains.comms.models.suppliers import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()

    total_products = db.query(Product).filter(Product.supplier_id == current_user["id"]).count()
    total_orders = (
        db.query(Order).join(OrderItem).join(Product)
        .filter(Product.supplier_id == current_user["id"])
        .distinct()
        .count()
    )
    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).join(Product).filter(
        Product.supplier_id == current_user["id"],
        Order.status == "completed",
    ).scalar() or 0

    return {
        "id": supplier.id,
        "username": supplier.username,
        "email": supplier.email,
        "phone": supplier.phone,
        "business_name": profile.business_name if profile else None,
        "business_address": profile.address if profile else None,
        "website": profile.website if profile else None,
        "bio": profile.bio if profile else None,
        "about_us": getattr(profile, "about_us", None) if profile else None,
        "verification_status": profile.verification_status if profile else "pending",
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "created_at": supplier.created_at.isoformat(),
    }


def update_supplier_profile(profile_update: dict, current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from domains.comms.models.suppliers import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)

    if "phone" in profile_update:
        supplier.phone = _sanitize_profile_string(profile_update.get("phone"))

    profile_field_map = {
        "business_name": "business_name",
        "business_address": "address",
        "website": "website",
        "bio": "bio",
        "about_us": "about_us",
        "business_type": "business_type",
    }
    for source_field, target_field in profile_field_map.items():
        if source_field not in profile_update:
            continue
        value = profile_update.get(source_field)
        if target_field == "website" and isinstance(value, str) and value.strip() and not value.startswith(("http://", "https://")):
            value = f"https://{value.strip()}"
        setattr(profile, target_field, _sanitize_profile_string(value))

    if "established_year" in profile_update:
        raw_year = profile_update.get("established_year")
        if raw_year in (None, ""):
            profile.established_year = None
        else:
            try:
                profile.established_year = int(raw_year)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="Established year must be a number") from exc

    db.commit()
    db.refresh(supplier)
    return get_supplier_profile(current_user, db)


def request_verification(current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from domains.comms.models.suppliers import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = SP(user_id=current_user["id"], verification_status="pending")
        db.add(profile)

    if profile.verification_status in (None, "pending"):
        profile.verification_status = "under_review"
    db.commit()
    return {"message": "Verification request submitted successfully", "status": profile.verification_status or "pending"}


# ── Payouts ───────────────────────────────────────────────────────────────────

