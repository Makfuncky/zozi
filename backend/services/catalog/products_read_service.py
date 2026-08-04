"""Service methods for catalog read operations."""
from typing import Any, Optional
from sqlalchemy.orm import Session
from data.models import Product, Category


def get_all_products(db: Session, skip: int = 0, limit: int = 20) -> list[Product]:
    """Get all active products with pagination."""
    return (
        db.query(Product)
        .filter(Product.is_active == True)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    """Get product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def search_products(
    db: Session,
    query: str | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    brand: str | None = None,
    in_stock: bool | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Product]:
    """Search products with filters."""
    q = db.query(Product)
    if query:
        q = q.filter(Product.name.contains(query) | Product.description.contains(query))
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if min_price:
        q = q.filter(Product.price >= min_price)
    if max_price:
        q = q.filter(Product.price <= max_price)
    if brand:
        q = q.filter(Product.brand == brand)
    if in_stock:
        q = q.filter(Product.stock_quantity > 0)
    return q.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


def get_product_categories(db: Session) -> list[Category]:
    """Get all product categories."""
    return db.query(Category).filter(Category.parent_id.is_(None)).all()

def get_productverification_first(db: Session, **filters) -> Optional[ProductVerification]:
    query = db.query(ProductVerification)
    for key, value in filters.items():
        query = query.filter(getattr(ProductVerification, key) == value)
    return query.limit(1).first()


def get_productverification_by_id(db: Session, record_id: int) -> Optional[ProductVerification]:
    return db.query(ProductVerification).filter(ProductVerification.id == record_id).first()


def list_product(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.offset(skip).limit(limit).all()


def get_product_first(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.limit(1).first()


def get_order_first(db: Session, **filters) -> Optional[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.limit(1).first()


def count_product(db: Session, **filters) -> int:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.count()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def get_category_by_id(db: Session, record_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == record_id).first()


def get_category_first(db: Session, **filters) -> Optional[Category]:
    query = db.query(Category)
    for key, value in filters.items():
        query = query.filter(getattr(Category, key) == value)
    return query.limit(1).first()


def get_flashsale_first(db: Session, **filters) -> Optional[FlashSale]:
    query = db.query(FlashSale)
    for key, value in filters.items():
        query = query.filter(getattr(FlashSale, key) == value)
    return query.limit(1).first()


def get_countryconfig_first(db: Session, **filters) -> Optional[CountryConfig]:
    query = db.query(CountryConfig)
    for key, value in filters.items():
        query = query.filter(getattr(CountryConfig, key) == value)
    return query.limit(1).first()


def get_supplierprofile_first(db: Session, **filters) -> Optional[SupplierProfile]:
    query = db.query(SupplierProfile)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierProfile, key) == value)
    return query.limit(1).first()


def get_usermodel_by_id(db: Session, record_id: int) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.id == record_id).first()




def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_productvariant_first(db: Session, **filters) -> Optional[ProductVariant]:
    query = db.query(ProductVariant)
    for key, value in filters.items():
        query = query.filter(getattr(ProductVariant, key) == value)
    return query.limit(1).first()


def get_user_first(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.limit(1).first()

def _db_productverification_query_0(db: Session) -> Optional[Any]:
    result = db.query(ProductVerification)
    return result
    """Read-only query delegated from controller."""

def _db_productverification_first_1(db: Session, id: Any, v_id: Any) -> Optional[Any]:
    result = db.query(ProductVerification).filter(ProductVerification.id == v_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_productverification_first_2(db: Session, id: Any, verification_id: Any) -> Optional[Any]:
    result = db.query(ProductVerification).filter(ProductVerification.id == verification_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_productverification_first_3(db: Session, id: Any, v_id: Any) -> Optional[Any]:
    result = db.query(ProductVerification).filter(ProductVerification.id == v_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_4(db: Session, id: Any, product_id: Any, v: Any) -> Optional[Any]:
    result = db.query(Product).filter(Product.id == v.product_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_0(db: Session, id: Any, in_: Any, product_ids: Any) -> Optional[Any]:
    result = db.query(Product).options(selectinload(Product.variants), selectinload(Product.reviews)).filter(Product.id.in_(product_ids)).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_1(db: Session, id: Any, in_: Any, product_ids: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id.in_(product_ids), Product.is_deleted.is_(False), ).all()
    return result
    """Read-only query delegated from controller."""

def _db_product_query_2(db: Session) -> Optional[Any]:
    result = db.query(Product).options(selectinload(Product.variants))
    return result
    """Read-only query delegated from controller."""

def _db_order_query_3(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_product_query_4(db: Session, is_: Any, is_approved: Any) -> Optional[Any]:
    result = db.query(Product).filter(Product.is_approved.is_(False), Product.is_deleted.is_(False))
    return result
    """Read-only query delegated from controller."""

def _db_product_first_5(db: Session, id: Any, is_: Any, is_deleted: Any, product_id: Any) -> Optional[Any]:
    result = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_6(db: Session, id: Any, is_: Any, is_deleted: Any, product_id: Any) -> Optional[Any]:
    result = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    return result
    """Read-only query delegated from controller."""

def _db_user_first_7(db: Session, id: Any, product: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == product.supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_8(db: Session, id: Any, is_: Any, is_deleted: Any, product_id: Any) -> Optional[Any]:
    result = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    return result
    """Read-only query delegated from controller."""

def _db_category_first_0(db: Session, lookup_tokens: Any, lower: Any, name: Any) -> Optional[Any]:
    result = db.query(Category).filter( or_(func.lower(Category.name).in_(lookup_tokens), func.lower(Category.slug).in_(lookup_tokens)) ).first()
    return result
    """Read-only query delegated from controller."""

def _db_flashsale_query_1(db: Session, true_val: Any, ends_at: Any, is_active: Any, noqa: Any, now: Any, starts_at: Any) -> Optional[Any]:
    result = db.query(FlashSale).filter( FlashSale.is_active == True,  # noqa: E712
        FlashSale.starts_at <= now, FlashSale.ends_at >= now, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_countryconfig_first_2(db: Session, true_val: Any, code: Any, is_active: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter( CountryConfig.code == code, CountryConfig.is_active == True, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_query_3(db: Session, false_val: Any, is_active: Any, is_deleted: Any, is_not_val: Any, noqa: Any) -> Optional[Any]:
    result = db.query(Product).options(selectinload(Product.variants)).filter(Product.is_deleted == False, Product.is_active.isnot(False), Product.is_approved.isnot(False)).all() == False, Product.is_active.isnot(False),
    return result
    """Read-only query delegated from controller."""

def _db_countryconfig_first_4(db: Session, true_val: Any, code: Any, is_active: Any) -> Optional[Any]:
    result = db.query(CountryConfig).filter( CountryConfig.code == code, CountryConfig.is_active == True, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_first_7(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == product_id, Product.supplier_id == current_user["id"], Product.is_deleted == False, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_query_8(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_product_first_9(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == product_id, Product.supplier_id == current_user["id"], Product.is_deleted == False, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_supplierprofile_first_10(db: Session, current_user: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(SupplierProfile).filter( SupplierProfile.user_id == current_user["id"] ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_query_11(db: Session, false_val: Any, id: Any, is_deleted: Any, noqa: Any, product_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == product_id, Product.is_deleted == False, )
    return result
    """Read-only query delegated from controller."""

def _db_usermodel_first_12(db: Session, id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(UserModel).filter(UserModel.id == supplier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_13(db: Session, false_val: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, supplier_id: Any) -> list[Any]:
    return db.query(Product).filter( Product.supplier_id == current_user["id"], Product.is_deleted == False, ).all()
    """Read-only query delegated from controller."""

def _db_category_first_14(db: Session, lower: Any, name: Any) -> Optional[Any]:
    result = db.query(Category).filter( or_(func.lower(Category.name) == category.strip().casefold(), func.lower(Category.slug) == category.strip().casefold()) ).first() if category and category.strip() else None
    return result
    """Read-only query delegated from controller."""

def _db_product_first_15(db: Session, false_val: Any, true_val: Any, id: Any, is_active: Any, is_approved: Any, is_deleted: Any, noqa: Any, product_id: Any) -> Optional[Any]:
    result = db.query(Product).options(selectinload(Product.variants)).filter( Product.id == product_id, Product.is_deleted == False, Product.is_active == True, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_productvariant_query_16(db: Session) -> Optional[Any]:
    return db.query(ProductVariant)
    """Read-only query delegated from controller."""

def _db_user_query_17(db: Session) -> Optional[Any]:
    return db.query(User)
    """Read-only query delegated from controller."""

def _db_product_query_18(db: Session) -> Optional[Any]:
    return db.query(Product)
    """Read-only query delegated from controller."""

def _db_product_query_19(db: Session, false_val: Any, true_val: Any, is_active: Any, is_approved: Any, is_deleted: Any, noqa: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.is_deleted == False, Product.is_active == True, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_query_0(db: Session, false_val: Any, is_active: Any, is_deleted: Any, is_not_val: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.is_deleted == False, Product.is_active.isnot(False), Product.is_approved.isnot(False), Product.stock > 0, )
    return result
    """Read-only query delegated from controller."""


def autocomplete_product_names(db: Session, term: str, limit: int = 10) -> list[str]:
    """Return product names matching a search term — delegated from controller."""
    results = db.query(Product.name).filter(Product.name.ilike(term)).limit(limit).all()
    return [r[0] for r in results]


def get_supplier_name_choices(db: Session) -> list[tuple]:
    """Return supplier usernames and storefront business names for filtering — delegated from controller."""
    results = (
        db.query(User.username, SupplierProfile.business_name)
        .join(Product, Product.supplier_id == User.id)
        .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
        .filter(
            User.role == "supplier",
            Product.is_deleted == False,  # noqa: E712
            Product.is_active.isnot(False),
            Product.is_approved.isnot(False),
        )
        .order_by(User.username)
        .all()
    )
    return results
