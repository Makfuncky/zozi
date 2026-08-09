"""
Commerce Domain — wishlist, reviews, address book, categories.
"""
from typing import List, cast

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from data.schemas import (
    AddressCreate,
    AddressUpdate,
    CategoryCreate,
    CategorySchema,
)
from models import Address, Category, Product, Wishlist
from utils.audit import AuditAction, audit_log
from services.products_write_service import (
    create_category as service_create_category,
    update_category as service_update_category,
)
from utils.cache import (
    build_versioned_cache_key,
    bump_cache_version,
    cache_get_json,
    cache_set_json,
)

# ── Wishlist ──────────────────────────────────────────────────────────────────


def get_wishlist(current_user: dict, db: Session, limit: int = 200, offset: int = 0) -> List[Wishlist]:
    return (
        db.query(Wishlist)
        .filter(Wishlist.user_id == current_user["id"])
        .order_by(Wishlist.created_at.desc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 200))
        .all()
    )


def add_to_wishlist(product_id: int, current_user: dict, db: Session) -> Wishlist:
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user["id"],
        Wishlist.product_id == product_id,
    ).first()
    if existing:
        return existing

    return service_create_wishlist_item(db, current_user["id"], product_id)


def remove_from_wishlist(product_id: int, current_user: dict, db: Session) -> dict:
    item = db.query(Wishlist).filter(
        Wishlist.user_id == current_user["id"],
        Wishlist.product_id == product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in wishlist")
    service_delete_wishlist_item(db, item)
    return {"detail": "Removed from wishlist"}


def clear_wishlist(current_user: dict, db: Session) -> dict:
    service_clear_wishlist(db, current_user["id"])
    return {"detail": "Wishlist cleared"}


# ── Address Book ──────────────────────────────────────────────────────────────


def list_addresses(user_id: int, db: Session, limit: int = 100, offset: int = 0) -> List[Address]:
    return (
        db.query(Address)
        .filter(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 100))
        .all()
    )


def create_address(user_id: int, body: AddressCreate, current_user: dict, db: Session) -> Address:
    if body.is_default:
        db.query(Address).filter(
            Address.user_id == user_id, Address.is_default == True  # noqa: E712
        ).update({"is_default": False})

    addr = service_create_address(
        user_id=user_id,
        label=body.label,
        street=body.street,
        city=body.city,
        state=body.state,
        postal_code=body.postal_code,
        country=body.country,
        is_default=body.is_default,
    )
    audit_log(
        db,
        action=AuditAction.ADDRESS_CREATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=cast(int, getattr(addr, "id")),
        details={"label": addr.label, "is_default": addr.is_default},
    )
    return addr


def update_address(address_id: int, user_id: int, body: AddressUpdate, current_user: dict, db: Session) -> Address:
    addr = _get_own_address(address_id, user_id, db)
    updates = body.model_dump(exclude_unset=True)

    if body.is_default is True:
        db.query(Address).filter(
            Address.user_id == user_id, Address.is_default == True  # noqa: E712
        ).update({"is_default": False})

    result = service_update_address(db, addr, updates)
    audit_log(
        db,
        action=AuditAction.ADDRESS_UPDATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=cast(int, getattr(addr, "id")),
        details={"updated_fields": sorted(updates.keys())},
    )
    return result


def delete_address(address_id: int, user_id: int, current_user: dict, db: Session) -> None:
    addr = _get_own_address(address_id, user_id, db)
    address_label = addr.label
    service_delete_address(db, addr)
    audit_log(
        db,
        action=AuditAction.ADDRESS_DELETED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=address_id,
        details={"label": address_label},
    )


def set_default_address(address_id: int, user_id: int, current_user: dict, db: Session) -> Address:
    db.query(Address).filter(
        Address.user_id == user_id, Address.is_default == True  # noqa: E712
    ).update({"is_default": False})

    addr = _get_own_address(address_id, user_id, db)
    result = service_set_default_address(db, addr)
    audit_log(
        db,
        action=AuditAction.ADDRESS_SET_DEFAULT,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="address",
        resource_id=cast(int, getattr(addr, "id")),
        details={"label": addr.label},
    )
    return result


def _get_own_address(address_id: int, user_id: int, db: Session) -> Address:
    addr = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user_id,
    ).first()
    if not addr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found.",
        )
    return addr


# ── Categories ────────────────────────────────────────────────────────────────


_CATEGORY_LIST_CACHE_TTL = 300
_CATEGORY_DETAIL_CACHE_TTL = 300


def _serialize_category(category: Category) -> dict:
    return jsonable_encoder(CategorySchema.model_validate(category))


def list_categories(db: Session) -> List[Category]:
    cache_key = build_versioned_cache_key("categories", "list", {"scope": "root-active"})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, list):
        return cached_payload

    categories = (
        db.query(Category)
        .filter(Category.is_active.is_(True), Category.parent_id.is_(None))
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    serialized = [_serialize_category(category) for category in categories]
    cache_set_json(cache_key, serialized, _CATEGORY_LIST_CACHE_TTL)
    return serialized


def get_category(slug: str, db: Session) -> Category:
    cache_key = build_versioned_cache_key("categories", "detail", {"slug": slug})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    cat = db.query(Category).filter(Category.slug == slug, Category.is_active.is_(True)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    serialized = _serialize_category(cat)
    cache_set_json(cache_key, serialized, _CATEGORY_DETAIL_CACHE_TTL)
    return serialized


def create_category(category: CategoryCreate, current_user: dict, db: Session) -> Category:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    if db.query(Category).filter(Category.slug == category.slug).first():
        raise HTTPException(status_code=409, detail="Slug already exists")
    db_cat = service_create_category(**category.model_dump())
    bump_cache_version("categories")
    return db_cat


def update_category(category_id: int, category: CategoryCreate, current_user: dict, db: Session) -> Category:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    updates = category.model_dump()
    result = service_update_category(db, db_cat, updates)
    bump_cache_version("categories")
    return result

from services.commerce_write_service import (
    clear_wishlist as service_clear_wishlist,
    create_address as service_create_address,
    create_wishlist_item as service_create_wishlist_item,
    delete_address as service_delete_address,
    delete_wishlist_item as service_delete_wishlist_item,
    set_default_address as service_set_default_address,
    update_address as service_update_address,
)
