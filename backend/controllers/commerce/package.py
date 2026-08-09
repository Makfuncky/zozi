"""
Commerce Domain — wishlist, reviews, address book, categories.
"""
from typing import List, cast

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from controllers.audit_controller import audit_log, AuditAction
from utils.cache import build_versioned_cache_key, bump_cache_version, cache_get_json, cache_set_json
from db.schemas import AddressCreate, AddressOut, AddressUpdate, CategoryCreate, CategorySchema, ReviewCreate
from models import Address, Category, Order, OrderItem, Product, Review, Wishlist


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

    item = Wishlist(user_id=current_user["id"], product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_wishlist(product_id: int, current_user: dict, db: Session) -> dict:
    item = db.query(Wishlist).filter(
        Wishlist.user_id == current_user["id"],
        Wishlist.product_id == product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in wishlist")
    db.delete(item)
    db.commit()
    return {"detail": "Removed from wishlist"}


def clear_wishlist(current_user: dict, db: Session) -> dict:
    db.query(Wishlist).filter(Wishlist.user_id == current_user["id"]).delete()
    db.commit()
    return {"detail": "Wishlist cleared"}


# ── Reviews ───────────────────────────────────────────────────────────────────


def get_product_reviews(product_id: int, skip: int, limit: int, db: Session) -> List[Review]:
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_review(product_id: int, review: ReviewCreate, current_user: dict, db: Session) -> Review:
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Review).filter(
        Review.product_id == product_id,
        Review.user_id == current_user["id"],
        Review.is_deleted == False,  # noqa: E712
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this product")

    purchased = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == current_user["id"],
            OrderItem.product_id == product_id,
            Order.status.in_(["delivered", "completed"]),
        )
        .first()
    )

    db_review = Review(
        product_id=product_id,
        user_id=current_user["id"],
        rating=review.rating,
        comment=review.comment,
        image_url=review.image_url,
        is_verified_purchase=bool(purchased),
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    all_ratings = (
        db.query(Review.rating)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .all()
    )
    avg = sum(r[0] for r in all_ratings) / len(all_ratings)
    db.query(Product).filter(Product.id == product_id).update({"rating": round(avg, 2)})
    db.commit()
    return db_review


def update_review(review_id: int, review: ReviewCreate, current_user: dict, db: Session) -> Review:
    db_review = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    setattr(db_review, "rating", review.rating)
    setattr(db_review, "comment", review.comment)
    setattr(db_review, "image_url", review.image_url)
    db.commit()
    db.refresh(db_review)
    return db_review


def delete_review(review_id: int, current_user: dict, db: Session) -> dict:
    db_review = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    setattr(db_review, "is_deleted", True)
    db.commit()
    return {"detail": "Review deleted"}


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

    addr = Address(
        user_id=user_id,
        label=body.label,
        street=body.street,
        city=body.city,
        state=body.state,
        postal_code=body.postal_code,
        country=body.country,
        is_default=body.is_default,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
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

    for field, value in updates.items():
        setattr(addr, field, value)

    db.commit()
    db.refresh(addr)
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
    return addr


def delete_address(address_id: int, user_id: int, current_user: dict, db: Session) -> None:
    addr = _get_own_address(address_id, user_id, db)
    address_label = addr.label
    db.delete(addr)
    db.commit()
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
    setattr(addr, "is_default", True)
    db.commit()
    db.refresh(addr)
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
    return addr


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
    db_cat = Category(**category.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    bump_cache_version("categories")
    return db_cat


def update_category(category_id: int, category: CategoryCreate, current_user: dict, db: Session) -> Category:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in category.model_dump().items():
        setattr(db_cat, k, v)
    db.commit()
    db.refresh(db_cat)
    bump_cache_version("categories")
    return db_cat
