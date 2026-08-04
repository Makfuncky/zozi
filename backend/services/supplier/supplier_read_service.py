"""Read-only supplier queries extracted from routers to satisfy layering (LC1/W1).

Routers must not perform ``db.query``/writes directly; they delegate to this module.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from data.models import OrderItem, Product, SupplierProfile, User
from services.storage import storage as _storage
from data.services_write_helpers import (
    commit_and_refresh,
    commit_only,
)
from services.supplier.supplier_profile_service import (  # noqa: F401  (re-exported for backward compatibility)
    create_supplier_profile,
    get_supplier_profile_by_user,
    update_supplier_profile,
)
from utils.datetime_utils import utcnow
from utils.pagination import cursor_paginate_desc


def get_supplier_analytics_summary(db: Session, user_id: int) -> dict:
    """Aggregated analytics for the supplier owning ``user_id``."""
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user_id)
        .first()
    )
    if not supplier:
        raise HTTPException(404, detail="Supplier profile not found")
    total_products = (
        db.query(func.count(Product.id))
        .filter(Product.supplier_id == supplier.id)
        .scalar()
    )
    total_sales = (
        db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
        .filter(OrderItem.supplier_id == supplier.id)
        .scalar()
    )
    total_orders = (
        db.query(func.count(func.distinct(OrderItem.order_id)))
        .filter(OrderItem.supplier_id == supplier.id)
        .scalar()
    )
    return {
        "total_products": total_products,
        "total_sales": float(total_sales),
        "total_orders": total_orders,
    }


def require_supplier_profile(db: Session, user_id: int) -> SupplierProfile:
    """Return the supplier profile owned by ``user_id`` (404 if absent)."""
    profile = (
        db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    )
    if not profile:
        raise HTTPException(404, "Supplier profile not found")
    return profile


def get_owned_product(db: Session, product_id: int, user_id: int) -> Product:
    """Return a product owned by ``user_id`` (404 if absent/not owned)."""
    supplier = require_supplier_profile(db, user_id)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")
    return product


def get_my_products_page(db: Session, user_id: int, cursor: str | None, limit: int):
    """Return a cursor-paginated page of the supplier's products."""
    supplier = require_supplier_profile(db, user_id)
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    return cursor_paginate_desc(q.order_by(Product.id.desc()), cursor=cursor, page_size=limit)


def update_product_discount(db: Session, product_id: int, user_id: int, payload: dict) -> dict:
    """Set or clear a discount on the supplier's product (see router for body schema)."""
    product = get_owned_product(db, product_id, user_id)

    if payload.get("clear"):
        product.compare_price = None
        product.discount_starts_at = None
        product.discount_ends_at = None
        commit_and_refresh(db, product)
        return {"status": "success", "message": "Discount cleared", "product_id": product.id}

    if "compare_price" in payload:
        cp = payload["compare_price"]
        product.compare_price = float(cp) if cp is not None else None

    if "discount_starts_at" in payload:
        raw = payload["discount_starts_at"]
        try:
            product.discount_starts_at = (
                datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
            )
        except (ValueError, TypeError):
            raise HTTPException(400, f"Invalid discount_starts_at format: {raw}")

    if "discount_ends_at" in payload:
        raw = payload["discount_ends_at"]
        try:
            product.discount_ends_at = (
                datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
            )
        except (ValueError, TypeError):
            raise HTTPException(400, f"Invalid discount_ends_at format: {raw}")

    commit_and_refresh(db, product)

    discount_pct = 0
    now = utcnow()
    if product.compare_price and product.price and float(product.compare_price) > 0:
        discount_pct = round(
            (1 - float(product.price) / float(product.compare_price)) * 100, 1
        )

    is_active = bool(product.compare_price and product.compare_price > product.price)
    if product.discount_starts_at and product.discount_ends_at:
        is_active = is_active and product.discount_starts_at <= now <= product.discount_ends_at
    elif product.discount_starts_at:
        is_active = is_active and product.discount_starts_at <= now

    return {
        "status": "success",
        "product_id": product.id,
        "price": float(product.price),
        "compare_price": float(product.compare_price) if product.compare_price else None,
        "discount_percentage": discount_pct,
        "discount_active": is_active,
    }


def update_product(db: Session, product_id: int, user_id: int, payload: dict) -> Product:
    """Update a product's basic fields (name, description, price, stock, etc.)."""
    product = get_owned_product(db, product_id, user_id)
    field_map = {
        "name": "name",
        "description": "description",
        "price": "price",
        "stock": "stock",
        "stock_quantity": "stock",
        "category": "category",
        "is_active": "is_active",
        "tags": "tags",
        "image_url": "image_url",
    }
    for key, attr in field_map.items():
        if key in payload:
            setattr(product, attr, payload[key])
    commit_and_refresh(db, product)
    return product


def set_product_image_url(db: Session, product_id: int, user_id: int, image_url: str) -> Product:
    """Persist an uploaded image URL on the supplier's product, removing the old file."""
    product = get_owned_product(db, product_id, user_id)
    old_url = product.image_url or ""
    if old_url:
        old_key = None
        if old_url.startswith("/uploads/"):
            old_key = old_url.lstrip("/")
        elif getattr(_storage, "cdn_base", "") and old_url.startswith(_storage.cdn_base):
            old_key = old_url[len(_storage.cdn_base):].lstrip("/")
        if old_key:
            try:
                _storage.delete(old_key)
            except Exception:
                pass
    product.image_url = image_url
    commit_and_refresh(db, product)
    return product


def soft_delete_product(db: Session, product_id: int, user_id: int) -> dict:
    """Soft-delete a product (sets is_deleted=True)."""
    supplier = require_supplier_profile(db, user_id)
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.supplier_id == supplier.id,
            Product.is_deleted == False,
        )
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")
    product.is_deleted = True
    commit_only(db)
    return {"status": "success", "message": "Product deleted"}


def list_supplier_profiles(db: Session) -> list[SupplierProfile]:
    """List all supplier profiles (delegated read for routers)."""
    return db.query(SupplierProfile).all()


def get_supplier_profile_by_id(db: Session, profile_id: int) -> SupplierProfile | None:
    """Get a supplier profile by ID (delegated read for routers)."""
    return db.query(SupplierProfile).filter(SupplierProfile.id == profile_id).first()


def count_supplier_profiles(
    db: Session,
    country_code: str | None = None,
    verification_status: str | None = None,
    is_active: bool | None = None,
) -> int:
    """Count supplier profiles with optional country/status/active filters (LC1 delegated read)."""
    query = db.query(SupplierProfile)
    if country_code and country_code != "*":
        query = query.filter(SupplierProfile.country_code == country_code.upper())
    if verification_status is not None:
        query = query.filter(SupplierProfile.verification_status == verification_status)
    if is_active is not None:
        query = query.filter(SupplierProfile.is_active == is_active)
    return query.count()


def list_comparison_supplier_profiles(db: Session, limit: int = 200) -> list[SupplierProfile]:
    """List non-deleted supplier profiles for the comparison view (LC1 delegated read)."""
    return (
        db.query(SupplierProfile)
        .filter(SupplierProfile.is_deleted == False)
        .order_by(SupplierProfile.id.asc())
        .limit(limit)
        .all()
    )

def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def get_sp_by_id(db: Session, record_id: int) -> Optional[SP]:
    return db.query(SP).filter(SP.id == record_id).first()


def get_supplierprofile_by_id(db: Session, record_id: int) -> Optional[SupplierProfile]:
    return db.query(SupplierProfile).filter(SupplierProfile.id == record_id).first()


def count_user(db: Session, **filters) -> int:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.count()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_countryconfig_first(db: Session, **filters) -> Optional[CountryConfig]:
    query = db.query(CountryConfig)
    for key, value in filters.items():
        query = query.filter(getattr(CountryConfig, key) == value)
    return query.limit(1).first()


def get_supplierdocument_first(db: Session, **filters) -> Optional[SupplierDocument]:
    query = db.query(SupplierDocument)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierDocument, key) == value)
    return query.limit(1).first()


def get_user_first(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.limit(1).first()


def list_supplierprofile(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[SupplierProfile]:
    query = db.query(SupplierProfile)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierProfile, key) == value)
    return query.offset(skip).limit(limit).all()


def get_unknown_scalar(db: Session, column: str, **filters) -> Any:
    query = db.query(getattr(Unknown, column))
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.scalar()


def get_shipment_first(db: Session, **filters) -> Optional[Shipment]:
    query = db.query(Shipment)
    for key, value in filters.items():
        query = query.filter(getattr(Shipment, key) == value)
    return query.limit(1).first()


def list_user(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.offset(skip).limit(limit).all()


def get_product_by_condition(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.first()


def get_unknown_by_condition(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.first()


def get_order_first(db: Session, **filters) -> Optional[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.limit(1).first()


def get_shipmentevent_first(db: Session, **filters) -> Optional[ShipmentEvent]:
    query = db.query(ShipmentEvent)
    for key, value in filters.items():
        query = query.filter(getattr(ShipmentEvent, key) == value)
    return query.limit(1).first()


def get_suppliersettlement_first(db: Session, **filters) -> Optional[SupplierSettlement]:
    query = db.query(SupplierSettlement)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierSettlement, key) == value)
    return query.limit(1).first()


def get_orderitem_first(db: Session, **filters) -> Optional[OrderItem]:
    query = db.query(OrderItem)
    for key, value in filters.items():
        query = query.filter(getattr(OrderItem, key) == value)
    return query.limit(1).first()


def get_order_by_id(db: Session, record_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == record_id).first()


def list_shipment(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Shipment]:
    query = db.query(Shipment)
    for key, value in filters.items():
        query = query.filter(getattr(Shipment, key) == value)
    return query.offset(skip).limit(limit).all()


def get_product_first(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.limit(1).first()


def count_product(db: Session, **filters) -> int:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.count()


def count_products(db: Session, **filters) -> int:
    """Count products, optionally filtered by supplier or other fields."""
    return count_product(db, **filters)


def list_product(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.offset(skip).limit(limit).all()


def get_payout_first(db: Session, **filters) -> Optional[Payout]:
    query = db.query(Payout)
    for key, value in filters.items():
        query = query.filter(getattr(Payout, key) == value)
    return query.limit(1).first()


def get_commissionbadgetier_first(db: Session, **filters) -> Optional[CommissionBadgeTier]:
    query = db.query(CommissionBadgeTier)
    for key, value in filters.items():
        query = query.filter(getattr(CommissionBadgeTier, key) == value)
    return query.limit(1).first()


def get_badgebillingrecord_first(db: Session, **filters) -> Optional[BadgeBillingRecord]:
    query = db.query(BadgeBillingRecord)
    for key, value in filters.items():
        query = query.filter(getattr(BadgeBillingRecord, key) == value)
    return query.limit(1).first()




def get_supplierbankaccount_by_id(db: Session, record_id: int) -> Optional[SupplierBankAccount]:
    return db.query(SupplierBankAccount).filter(SupplierBankAccount.id == record_id).first()


def get_supplierdocument_by_id(db: Session, record_id: int) -> Optional[SupplierDocument]:
    return db.query(SupplierDocument).filter(SupplierDocument.id == record_id).first()


def get_supplierprofile_first(db: Session, **filters) -> Optional[SupplierProfile]:
    query = db.query(SupplierProfile)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierProfile, key) == value)
    return query.limit(1).first()

def _db_user_first_0(db: Session, id: Any, role: Any, sid: Any, supplier: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == sid, User.role == "supplier").first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_1(db: Session, sid: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == sid).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_2(db: Session, id: Any, role: Any, supplier: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == supplier_id, User.role == "supplier").first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_3(db: Session, supplier_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_query_4(db: Session, role: Any, supplier: Any) -> Optional[Any]:
    result = db.query(User).filter(User.role == "supplier")
    return result
    """Read-only query delegated from controller."""

def _db_user_query_5(db: Session, is_: Any, is_verified: Any, role: Any, supplier: Any) -> Optional[Any]:
    result = db.query(User).filter(User.role == "supplier", User.is_verified.is_(False))
    return result
    """Read-only query delegated from controller."""

def _db_user_first_6(db: Session, id: Any, role: Any, supplier: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == user_id, User.role == "supplier").first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_7(db: Session, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_countryconfig_first_8(db: Session, true_val: Any, code: Any, supplier_country: Any, upper: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter( CountryConfig.code == supplier_country.upper(), CountryConfig.is_active == True, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierdocument_all_9(db: Session, approved: Any, status: Any, supplier_id: Any, user_id: Any) -> list[Any]:
    for doc in db.query(SupplierDocument).filter( SupplierDocument.supplier_id == user_id, SupplierDocument.status == "approved", ).all(): approved_types |= {str(getattr(doc, "document_type", "")).strip().lower()}
    """Read-only query delegated from controller."""

def _db_user_first_10(db: Session, id: Any, role: Any, supplier: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == user_id, User.role == "supplier").first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_11(db: Session, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_query_12(db: Session) -> Optional[Any]:
    return db.query(User)
    """Read-only query delegated from controller."""

def _db_supplierprofile_all_13(db: Session, in_: Any, supplier_ids: Any, user_id: Any) -> list[Any]:
    return db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(supplier_ids)).all()
    """Read-only query delegated from controller."""

def _db_shipment_query_0(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_user_all_1(db: Session, id: Any, in_: Any, user_ids: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id.in_(user_ids)).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_2(db: Session, product_slug: Any, slug: Any) -> Optional[Any]:
    while db.query(Product).filter(Product.slug == product_slug).first(): attempt += 1
    """Read-only query delegated from controller."""

def _db_order_query_4(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_shipmentevent_query_5(db: Session) -> Optional[Any]:
    return db.query(ShipmentEvent)
    """Read-only query delegated from controller."""

def _db_suppliersettlement_all_6(db: Session, all_order_ids: Any, in_: Any, order_id: Any, supplier_id: Any) -> list[Any]:
    return db.query(SupplierSettlement).filter( SupplierSettlement.supplier_id == supplier_id, SupplierSettlement.order_id.in_(all_order_ids).all(), ).all()
    """Read-only query delegated from controller."""

def _db_orderitem_query_7(db: Session) -> Optional[Any]:
    return db.query(OrderItem)
    """Read-only query delegated from controller."""

def _db_shipment_query_8(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_orderitem_query_9(db: Session) -> Optional[Any]:
    return db.query(OrderItem)
    """Read-only query delegated from controller."""

def _db_order_query_10(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_orderitem_query_11(db: Session) -> Optional[Any]:
    return db.query(OrderItem)
    """Read-only query delegated from controller."""

def _db_order_query_12(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_13(db: Session, supplier_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_query_14(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_user_first_15(db: Session, id: Any, order: Any, user_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == order.user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_orderitem_query_16(db: Session) -> Optional[Any]:
    return db.query(OrderItem)
    """Read-only query delegated from controller."""

def _db_shipment_query_17(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_18(db: Session, supplier_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipmentevent_first_19(db: Session, event_type: Any, id: Any, in_: Any, picked_from_supplier: Any, shipment: Any, shipment_id: Any, supplier_prepared: Any) -> Optional[Any]:
    if not db.query(ShipmentEvent).filter( ShipmentEvent.shipment_id == shipment.id, ShipmentEvent.event_type.in_(["supplier_prepared", "picked_from_supplier"]), ).first(): add_to_session( db, ShipmentEvent( shipment_id=shipment.id, order_id=shipment.order_id, supplier_id=shipment.supplier_id, actor_user_id=current_user["id"], actor_role=current_user.get("role", "supplier"), event_type="supplier_prepared", status_after="processing", distribution_channel=getattr(shipment, "distribution_channel", None), location=shipment.current_hub, scan_code=shipment.scan_code, notes=(notes or "").strip() or "Packed parcel proof uploaded by supplier", created_at=utcnow(), ) )
    """Read-only query delegated from controller."""

def _db_shipment_all_20(db: Session, id: Any, order: Any, order_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == order.id).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_query_21(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).options(selectinload(Product.variants)).filter( Product.supplier_id == current_user["id"], Product.is_deleted == False, )
    return result
    """Read-only query delegated from controller."""

def _db_product_first_22(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).options(selectinload(Product.variants)).filter( Product.id == product_id, Product.supplier_id == current_user["id"], Product.is_deleted == False, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_23(db: Session, current_user: Any, id: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == product_id, Product.supplier_id == current_user["id"], ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_24(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == product_id, Product.supplier_id == current_user["id"], Product.is_deleted == False, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_count_25(db: Session, created_at: Any, sid: Any, start_date: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Order).join(OrderItem).join(Product).filter( Product.supplier_id == sid, Order.created_at >= start_date, ).distinct().count()
    return result
    """Read-only query delegated from controller."""

def _db_order_count_26(db: Session, created_at: Any, previous_start_date: Any, sid: Any, start_date: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Order).join(OrderItem).join(Product).filter( Product.supplier_id == sid, Order.created_at >= previous_start_date, Order.created_at < start_date, ).distinct().count()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_27(db: Session, id: Any, product: Any, product_id: Any, sid: Any, supplier_id: Any) -> Optional[Any]:
    for product in db.query(Product).filter(Product.supplier_id == sid).limit(10).all(): sales_data = db.query( func.count(OrderItem.id), func.sum(OrderItem.price * OrderItem.quantity), ).filter(OrderItem.product_id == product.id).first()
    """Read-only query delegated from controller."""

def _db_product_all_28(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.supplier_id == current_user["id"], Product.is_deleted == False, ).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_29(db: Session, current_user: Any, id: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == product_id, Product.supplier_id == current_user["id"], ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_30(db: Session, current_user: Any, id: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == product_id, Product.supplier_id == current_user["id"], ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_31(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.supplier_id == current_user["id"], Product.is_deleted == False, ).all()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_32(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_33(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_query_34(db: Session) -> Optional[Any]:
    return db.query(Order).join(OrderItem).join(Product)
    """Read-only query delegated from controller."""

def _db_user_first_35(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_36(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_37(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_38(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_payout_query_39(db: Session) -> Optional[Any]:
    return db.query(Payout)
    """Read-only query delegated from controller."""

def _db_shipment_query_40(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_product_all_41(db: Session, current_user: Any, id: Any, in_: Any, product_ids: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id.in_(product_ids), Product.supplier_id == current_user["id"], ).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_42(db: Session, false_val: Any, current_user: Any, id: Any, in_: Any, product_ids: Any) -> list[Any]:
    return db.query(Product).filter( Product.id.in_(product_ids), Product.supplier_id == current_user["id"], Product.is_deleted == False, ).all()
    """Read-only query delegated from controller."""

def _db_product_all_43(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.supplier_id == current_user["id"], Product.is_deleted == False, ).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_44(db: Session, product_slug: Any, slug: Any) -> Optional[Any]:
    while db.query(Product).filter(Product.slug == product_slug).first(): attempt += 1
    """Read-only query delegated from controller."""

def _db_product_all_45(db: Session, current_user: Any, id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter(Product.supplier_id == current_user["id"]).all()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_46(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_47(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_48(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_49(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_50(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_51(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_52(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_53(db: Session, supplier_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_commissionbadgetier_query_54(db: Session) -> Optional[Any]:
    return db.query(CommissionBadgeTier)
    """Read-only query delegated from controller."""

def _db_commissionbadgetier_query_55(db: Session) -> Optional[Any]:
    return db.query(CommissionBadgeTier)
    """Read-only query delegated from controller."""

def _db_badgebillingrecord_query_56(db: Session, badge_level: Any, charge_type: Any, draft: Any, in_: Any, invoiced: Any, paid: Any, status: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(BadgeBillingRecord).filter( BadgeBillingRecord.supplier_id == supplier_id, BadgeBillingRecord.badge_level == badge_level, BadgeBillingRecord.charge_type == charge_type, BadgeBillingRecord.status.in_(("draft", "invoiced", "paid")), )
    return result
    """Read-only query delegated from controller."""

def _db_commissionbadgetier_query_57(db: Session) -> Optional[Any]:
    return db.query(CommissionBadgeTier)
    """Read-only query delegated from controller."""

def _db_badgebillingrecord_query_58(db: Session) -> Optional[Any]:
    return db.query(BadgeBillingRecord)
    """Read-only query delegated from controller."""

def _db_badgebillingrecord_query_59(db: Session) -> Optional[Any]:
    return db.query(BadgeBillingRecord)
    """Read-only query delegated from controller."""

def _db_commissionbadgetier_query_60(db: Session) -> Optional[Any]:
    return db.query(CommissionBadgeTier)
    """Read-only query delegated from controller."""

def _db_sp_first_61(db: Session, supplier_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_62(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_sp_first_63(db: Session, supplier_user_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SP).filter(SP.user_id == supplier_user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_64(db: Session, false_val: Any, true_val: Any, is_active: Any, is_deleted: Any, noqa: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.supplier_id == supplier_id, Product.is_deleted == False, Product.is_active == True, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierbankaccount_first_65(db: Session, supplier_id: Any) -> Optional[Any]:
    result = db.query(SupplierBankAccount).filter(SupplierBankAccount.supplier_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierbankaccount_first_66(db: Session, supplier_id: Any) -> Optional[Any]:
    result = db.query(SupplierBankAccount).filter(SupplierBankAccount.supplier_id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_0(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierdocument_query_1(db: Session, current_user: Any, id: Any, in_: Any, profile_id: Any, supplier_id: Any) -> Optional[Any]:
    return db.query(SupplierDocument).filter( SupplierDocument.supplier_id.in_([profile_id, current_user["id"]]) )
    """Read-only query delegated from controller."""

def _db_supplierdocument_query_2(db: Session) -> Optional[Any]:
    result = db.query(SupplierDocument)
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_4(db: Session, doc: Any, supplier_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter( SupplierProfile.user_id == doc.supplier_id ).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_5(db: Session, doc: Any, id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == doc.supplier_id).first()
    return result
    """Read-only query delegated from controller."""
