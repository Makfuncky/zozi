"""Service methods for promotion engine data access."""
from __future__ import annotations
from sqlalchemy.orm import Session
from db.base import Base
from data.models import PromotionEngineConfig, Coupon, FlashSale, Banner, PromotionOrderTier


def ensure_promotion_tables(db: Session) -> None:
    """Create promotion tables if they don't exist (idempotent)."""
    bind = db.get_bind()
    Base.metadata.create_all(
        bind=bind,
        tables=[
            PromotionEngineConfig.__table__,
            PromotionOrderTier.__table__,
        ],
        checkfirst=True,
    )


def get_promotion_config(db: Session) -> PromotionEngineConfig | None:
    """Get the promotion engine config."""
    return db.query(PromotionEngineConfig).first()


def get_promotion_config_by_id(db: Session, config_id: int) -> PromotionEngineConfig | None:
    """Get promotion config by ID."""
    return db.query(PromotionEngineConfig).filter(PromotionEngineConfig.id == config_id).first()


def list_coupons(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    country: str | None = None,
    include_deleted: bool = False,
) -> list[Coupon]:
    """List coupons with optional country filter."""
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if country and country != "*":
        q = q.filter(Coupon.country_code == country.upper())
    return q.offset(skip).limit(limit).all()


def get_coupon_by_code(db: Session, code: str) -> Coupon | None:
    """Get coupon by code."""
    return db.query(Coupon).filter(Coupon.code == code).first()


def create_coupon_record(
    db: Session,
    code: str,
    discount_type: str = "percentage",
    discount_value: float = 0,
    minimum_order: float | None = None,
    maximum_discount: float | None = None,
    usage_limit: int | None = None,
    starts_at: str | None = None,
    expires_at: str | None = None,
    is_active: bool = True,
    country_code: str | None = None,
) -> Coupon:
    """Create a coupon record."""
    from datetime import datetime

    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        minimum_order=minimum_order,
        maximum_discount=maximum_discount,
        usage_limit=usage_limit,
        starts_at=datetime.fromisoformat(starts_at) if starts_at else None,
        expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
        is_active=is_active,
        country_code=country_code.upper() if country_code else None,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def list_flash_sales(
    db: Session,
    country: str | None = None,
    active_only: bool = False,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> list[FlashSale]:
    """List flash sales with optional country and active filter."""
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.deleted_at.is_(None))
    if country and country != "*":
        q = q.filter(FlashSale.country_code == country.upper())
    if active_only:
        q = q.filter(FlashSale.is_active == True)
    return q.offset(skip).limit(limit).all()


def get_flash_sale_by_id(db: Session, sale_id: int) -> FlashSale | None:
    """Get a flash sale by ID."""
    return db.query(FlashSale).filter(FlashSale.id == sale_id).first()


def get_active_flash_sales(db: Session) -> list[FlashSale]:
    """Return all currently-active flash sales ordered by end date."""
    from utils.datetime_utils import utcnow
    now = utcnow()
    return (
        db.query(FlashSale)
        .filter(
            FlashSale.is_active.is_(True),
            FlashSale.starts_at <= now,
            FlashSale.ends_at >= now,
        )
        .order_by(FlashSale.ends_at)
        .all()
    )


def get_all_flash_sales(
    db: Session,
    search: str | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> tuple[list[FlashSale], int]:
    """Return flash sales with optional search, with total count."""
    query = db.query(FlashSale)
    if search and search.strip():
        query = query.filter(FlashSale.title.ilike(f"%{search.strip()}%"))
    total = query.count()
    query = query.order_by(FlashSale.created_at.desc(), FlashSale.id.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all(), total


def list_banners(
    db: Session,
    country: str | None = None,
    active_only: bool = False,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> list[Banner]:
    """List banners with optional country and active filter."""
    q = db.query(Banner)
    if not include_deleted:
        q = q.filter(Banner.deleted_at.is_(None))
    if country and country != "*":
        q = q.filter(Banner.country_code == country.upper())
    if active_only:
        q = q.filter(Banner.is_active == True)
    return q.order_by(Banner.sort_order).offset(skip).limit(limit).all()


def count_banners(
    db: Session,
    country: str | None = None,
    include_deleted: bool = False,
) -> int:
    """Count banners with optional country filter."""
    q = db.query(Banner)
    if not include_deleted:
        q = q.filter(Banner.deleted_at.is_(None))
    if country and country != "*":
        q = q.filter(Banner.country_code == country.upper())
    return q.count()


def get_banner_by_id(db: Session, banner_id: int) -> Banner | None:
    """Get a banner by ID."""
    return db.query(Banner).filter(Banner.id == banner_id).first()


def list_promotion_order_tiers(
    db: Session,
    country: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[PromotionOrderTier]:
    """List promotion order tiers with optional country filter."""
    q = db.query(PromotionOrderTier)
    if country:
        q = q.filter(PromotionOrderTier.country_code == country)
    return q.offset(skip).limit(limit).all()


def update_flash_sale(db: Session, sale_id: int, **kwargs) -> FlashSale | None:
    """Update a flash sale."""
    sale = get_flash_sale_by_id(db, sale_id)
    if not sale:
        return None
    for key, value in kwargs.items():
        if hasattr(sale, key):
            setattr(sale, key, value)
    db.commit()
    db.refresh(sale)
    return sale


def update_banner(db: Session, banner_id: int, **kwargs) -> Banner | None:
    """Update a banner."""
    banner = get_banner_by_id(db, banner_id)
    if not banner:
        return None
    for key, value in kwargs.items():
        if hasattr(banner, key):
            setattr(banner, key, value)
    db.commit()
    db.refresh(banner)
    return banner

def get_coupon_first(db: Session, **filters) -> Optional[Coupon]:
    query = db.query(Coupon)
    for key, value in filters.items():
        query = query.filter(getattr(Coupon, key) == value)
    return query.limit(1).first()


def get_coupon_by_condition(db: Session, **filters) -> Optional[Coupon]:
    query = db.query(Coupon)
    for key, value in filters.items():
        query = query.filter(getattr(Coupon, key) == value)
    return query.first()


def get_coupon_by_id(db: Session, record_id: int) -> Optional[Coupon]:
    return db.query(Coupon).filter(Coupon.id == record_id).first()


def get_unknown_scalar(db: Session, column: str, **filters) -> Any:
    query = db.query(getattr(Unknown, column))
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.scalar()


def get_product_first(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.limit(1).first()


def count_couponusage(db: Session, **filters) -> int:
    query = db.query(CouponUsage)
    for key, value in filters.items():
        query = query.filter(getattr(CouponUsage, key) == value)
    return query.count()


def get_wishlist_first(db: Session, **filters) -> Optional[Wishlist]:
    query = db.query(Wishlist)
    for key, value in filters.items():
        query = query.filter(getattr(Wishlist, key) == value)
    return query.limit(1).first()


def get_product_by_id(db: Session, record_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == record_id).first()


def get_review_first(db: Session, **filters) -> Optional[Review]:
    query = db.query(Review)
    for key, value in filters.items():
        query = query.filter(getattr(Review, key) == value)
    return query.limit(1).first()


def get_orderitem_first(db: Session, **filters) -> Optional[OrderItem]:
    query = db.query(OrderItem)
    for key, value in filters.items():
        query = query.filter(getattr(OrderItem, key) == value)
    return query.limit(1).first()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_review_by_id(db: Session, record_id: int) -> Optional[Review]:
    return db.query(Review).filter(Review.id == record_id).first()


def get_address_first(db: Session, **filters) -> Optional[Address]:
    query = db.query(Address)
    for key, value in filters.items():
        query = query.filter(getattr(Address, key) == value)
    return query.limit(1).first()


def get_category_first(db: Session, **filters) -> Optional[Category]:
    query = db.query(Category)
    for key, value in filters.items():
        query = query.filter(getattr(Category, key) == value)
    return query.limit(1).first()


def get_category_by_condition(db: Session, **filters) -> Optional[Category]:
    query = db.query(Category)
    for key, value in filters.items():
        query = query.filter(getattr(Category, key) == value)
    return query.first()


def get_category_by_id(db: Session, record_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == record_id).first()


def get_promotionengineconfig_by_condition(db: Session, **filters) -> Optional[PromotionEngineConfig]:
    query = db.query(PromotionEngineConfig)
    for key, value in filters.items():
        query = query.filter(getattr(PromotionEngineConfig, key) == value)
    return query.first()


def count_promotionordertier(db: Session, **filters) -> int:
    query = db.query(PromotionOrderTier)
    for key, value in filters.items():
        query = query.filter(getattr(PromotionOrderTier, key) == value)
    return query.count()


def get_promotionordertier_first(db: Session, **filters) -> Optional[PromotionOrderTier]:
    query = db.query(PromotionOrderTier)
    for key, value in filters.items():
        query = query.filter(getattr(PromotionOrderTier, key) == value)
    return query.limit(1).first()


def get_promotionordertier_by_id(db: Session, record_id: int) -> Optional[PromotionOrderTier]:
    return db.query(PromotionOrderTier).filter(PromotionOrderTier.id == record_id).first()


def get_flashsale_first(db: Session, **filters) -> Optional[FlashSale]:
    query = db.query(FlashSale)
    for key, value in filters.items():
        query = query.filter(getattr(FlashSale, key) == value)
    return query.limit(1).first()


def get_flashsale_by_id(db: Session, record_id: int) -> Optional[FlashSale]:
    return db.query(FlashSale).filter(FlashSale.id == record_id).first()

def _db_coupon_query_0(db: Session) -> Optional[Any]:
    result = db.query(Coupon)
    return result
    """Read-only query delegated from controller."""

def _db_coupon_first_1(db: Session, code: Any) -> Optional[Any]:
    return if db.query(Coupon).filter(Coupon.code == code).first(): raise HTTPException(status_code=409, detail="Coupon code already exists")
    """Read-only query delegated from controller."""

def _db_coupon_first_0(db: Session, _normalize_coupon_code: Any, code: Any) -> Optional[Any]:
    result = db.query(Coupon).filter( Coupon.code == _normalize_coupon_code(code), Coupon.is_active.is_(True), ).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_1(db: Session, id: Any, in_: Any, product_ids: Any) -> list[Any]:
    return for product in db.query(Product).filter( Product.id.in_(product_ids), Product.is_deleted.is_(False), ).all()
    """Read-only query delegated from controller."""

def _db_coupon_all_2(db: Session) -> list[Any]:
    return return db.query(Coupon).order_by(Coupon.created_at.desc()).all()
    """Read-only query delegated from controller."""

def _db_coupon_first_3(db: Session, code: Any) -> Optional[Any]:
    return if db.query(Coupon).filter(Coupon.code == code).first(): raise HTTPException(status_code=409, detail="Coupon code already exists")
    """Read-only query delegated from controller."""

def _db_coupon_first_4(db: Session, code: Any, upper: Any) -> Optional[Any]:
    result = db.query(Coupon).filter(Coupon.code == code.upper()).first()
    return result
    """Read-only query delegated from controller."""

def _db_wishlist_query_0(db: Session) -> Optional[Any]:
    return db.query(Wishlist)
    """Read-only query delegated from controller."""

def _db_wishlist_first_1(db: Session, current_user: Any, id: Any, product_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(Wishlist).filter( Wishlist.user_id == current_user["id"], Wishlist.product_id == product_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_wishlist_first_2(db: Session, current_user: Any, id: Any, product_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(Wishlist).filter( Wishlist.user_id == current_user["id"], Wishlist.product_id == product_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_review_query_3(db: Session) -> Optional[Any]:
    return db.query(Review)
    """Read-only query delegated from controller."""

def _db_review_first_4(db: Session, False: Any, current_user: Any, id: Any, is_deleted: Any, noqa: Any, product_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(Review).filter( Review.product_id == product_id, Review.user_id == current_user["id"], Review.is_deleted == False,  # noqa: E712 ).first()
    return result
    """Read-only query delegated from controller."""

def _db_orderitem_query_5(db: Session) -> Optional[Any]:
    return db.query(OrderItem)
    """Read-only query delegated from controller."""

def _db_product_query_6(db: Session, id: Any, product_id: Any) -> Optional[Any]:
    return db.query(Product).filter(Product.id == product_id).update({"rating": round(avg, 2)})
    """Read-only query delegated from controller."""

def _db_review_first_7(db: Session, False: Any, id: Any, is_deleted: Any, review_id: Any) -> Optional[Any]:
    result = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    return result
    """Read-only query delegated from controller."""

def _db_review_first_8(db: Session, False: Any, id: Any, is_deleted: Any, review_id: Any) -> Optional[Any]:
    result = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    return result
    """Read-only query delegated from controller."""

def _db_address_query_9(db: Session) -> Optional[Any]:
    return db.query(Address)
    """Read-only query delegated from controller."""

def _db_address_query_10(db: Session, True: Any, is_default: Any, noqa: Any, user_id: Any) -> Optional[Any]:
    return db.query(Address).filter( Address.user_id == user_id, Address.is_default == True  # noqa: E712 ).update({"is_default": False})
    """Read-only query delegated from controller."""

def _db_address_query_11(db: Session, True: Any, is_default: Any, noqa: Any, user_id: Any) -> Optional[Any]:
    return db.query(Address).filter( Address.user_id == user_id, Address.is_default == True  # noqa: E712 ).update({"is_default": False})
    """Read-only query delegated from controller."""

def _db_address_query_12(db: Session, True: Any, is_default: Any, noqa: Any, user_id: Any) -> Optional[Any]:
    return db.query(Address).filter( Address.user_id == user_id, Address.is_default == True  # noqa: E712 ).update({"is_default": False})
    """Read-only query delegated from controller."""

def _db_address_first_13(db: Session, address_id: Any, id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(Address).filter( Address.id == address_id, Address.user_id == user_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_category_query_14(db: Session) -> Optional[Any]:
    return db.query(Category)
    """Read-only query delegated from controller."""

def _db_category_first_15(db: Session, is_: Any, is_active: Any, slug: Any) -> Optional[Any]:
    result = db.query(Category).filter(Category.slug == slug, Category.is_active.is_(True)).first()
    return result
    """Read-only query delegated from controller."""

def _db_category_first_16(db: Session, category: Any, slug: Any) -> Optional[Any]:
    return if db.query(Category).filter(Category.slug == category.slug).first(): raise HTTPException(status_code=409, detail="Slug already exists")
    """Read-only query delegated from controller."""

def _db_promotionengineconfig_first_0(db: Session) -> Optional[Any]:
    result = db.query(PromotionEngineConfig).order_by(PromotionEngineConfig.id.asc()).first()
    return result
    """Read-only query delegated from controller."""

def _db_promotionordertier_count_1(db: Session) -> int:
    return if db.query(PromotionOrderTier).count() > 0: return
    """Read-only query delegated from controller."""

def _db_promotionordertier_query_2(db: Session) -> Optional[Any]:
    return db.query(PromotionOrderTier)
    """Read-only query delegated from controller."""

def _db_promotionordertier_first_3(db: Session, id: Any, tier_id: Any) -> Optional[Any]:
    result = db.query(PromotionOrderTier).filter(PromotionOrderTier.id == tier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_promotionordertier_first_4(db: Session, id: Any, tier_id: Any) -> Optional[Any]:
    result = db.query(PromotionOrderTier).filter(PromotionOrderTier.id == tier_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_promotionordertier_query_5(db: Session) -> Optional[Any]:
    return db.query(PromotionOrderTier)
    """Read-only query delegated from controller."""

def _db_flashsale_query_0(db: Session) -> Optional[Any]:
    return db.query(FlashSale)
    """Read-only query delegated from controller."""

def _db_flashsale_query_1(db: Session) -> Optional[Any]:
    result = db.query(FlashSale)
    return result
    """Read-only query delegated from controller."""
