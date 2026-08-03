"""Products write service — DB write operations for products and catalog entities."""
from typing import Optional, cast

from sqlalchemy.orm import Session

from data.models import (
    CartItem,
    Category,
    Coupon,
    CouponUsage,
    FlashSale,
    FlashSaleItem,
    Product,
    ProductImage,
    ProductVerification,
    ProductVariant,
    Review,
    Wishlist,
    WishlistItem,
)


def create_product(db: Session, **product_data) -> Product:
    product = Product(**product_data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, updates: dict) -> Product:
    for key, value in updates.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()


def update_product_rating(db: Session, product: Product, rating: float) -> Product:
    product.rating = rating
    db.commit()
    db.refresh(product)
    return product


def create_product_variant(db: Session, product_id: int, **variant_data) -> ProductVariant:
    variant = ProductVariant(product_id=product_id, **variant_data)
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def update_product_variant(db: Session, variant: ProductVariant, updates: dict) -> ProductVariant:
    for key, value in updates.items():
        setattr(variant, key, value)
    db.commit()
    db.refresh(variant)
    return variant


def delete_product_variant(db: Session, variant: ProductVariant) -> None:
    db.delete(variant)
    db.commit()


def create_product_image(db: Session, product_id: int, **image_data) -> ProductImage:
    image = ProductImage(product_id=product_id, **image_data)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def delete_product_image(db: Session, image: ProductImage) -> None:
    db.delete(image)
    db.commit()


def create_category(db: Session, **category_data) -> Category:
    category = Category(**category_data)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: Category, updates: dict) -> Category:
    for key, value in updates.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()


def reorder_categories(db: Session, category_updates: dict[int, int], country_code: str | None = None) -> None:
    for cid, pos in category_updates.items():
        query = db.query(Category).filter(Category.id == cid)
        if country_code:
            query = query.filter(Category.country_code == country_code)
        cat = query.first()
        if cat:
            cat.sort_order = pos
    db.commit()


def update_category_sort_order(db: Session, category_id: int, sort_order: int) -> Category:
    cat = db.query(Category).filter(Category.id == category_id).first()
    if cat:
        cat.sort_order = sort_order
        db.commit()
        db.refresh(cat)
    return cat


def create_coupon(db: Session, **coupon_data) -> Coupon:
    coupon = Coupon(**coupon_data)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(db: Session, coupon: Coupon, updates: dict) -> Coupon:
    for key, value in updates.items():
        setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    db.delete(coupon)
    db.commit()


def mark_coupon_as_used(order: "Order", db: Session) -> None:
    from data.models import Coupon
    coupon_code = cast(Optional[str], getattr(order, "coupon_code", None))
    if not coupon_code:
        return
    coupon = db.query(Coupon).filter(Coupon.code == coupon_code).first()
    if coupon:
        uses_count = cast(Optional[int], getattr(coupon, "uses_count", None))
        setattr(coupon, "uses_count", (uses_count or 0) + 1)
        db.commit()


def create_flash_sale(db: Session, **sale_data) -> FlashSale:
    sale = FlashSale(**sale_data)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def update_flash_sale(db: Session, sale: FlashSale, updates: dict) -> FlashSale:
    for key, value in updates.items():
        setattr(sale, key, value)
    db.commit()
    db.refresh(sale)
    return sale


def delete_flash_sale(db: Session, sale: FlashSale) -> None:
    db.delete(sale)
    db.commit()


def create_flash_sale_item(db: Session, flash_sale_id: int, **item_data) -> FlashSaleItem:
    item = FlashSaleItem(flash_sale_id=flash_sale_id, **item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def clear_product_carts(db: Session, product_id: int) -> None:
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)
    db.commit()


def clear_product_wishlists(db: Session, product_id: int) -> None:
    db.query(Wishlist).filter(Wishlist.product_id == product_id).delete(synchronize_session=False)
    db.commit()


def archive_product_reviews(db: Session, product_id: int) -> None:
    db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_deleted == False,
    ).update({"is_deleted": True}, synchronize_session=False)
    db.commit()


def create_product_verification(db: Session, **verification_data) -> ProductVerification:
    verification = ProductVerification(**verification_data)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def update_product_verification(db: Session, verification: ProductVerification, updates: dict) -> ProductVerification:
    for key, value in updates.items():
        setattr(verification, key, value)
    db.commit()
    db.refresh(verification)
    return verification


def delete_product_verification(db: Session, verification: ProductVerification) -> None:
    db.delete(verification)
    db.commit()


def get_product_by_slug(db: Session, slug: str) -> Product | None:
    return db.query(Product).filter(Product.slug == slug).first()


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_slug_hash(db: Session, slug_hash: str) -> Product | None:
    return db.query(Product).filter(Product.slug_hash == slug_hash).first()


def get_category_by_slug(db: Session, slug: str) -> Category | None:
    return db.query(Category).filter(Category.slug == slug).first()


def get_category_by_id(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def build_category_query(db: Session, active_only: bool = True, parent_id: int | None = None):
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    return query


def get_coupon_by_code(db: Session, code: str) -> Coupon | None:
    return db.query(Coupon).filter(Coupon.code == code).first()


def get_active_coupon_by_code(db: Session, code: str) -> Coupon | None:
    return db.query(Coupon).filter(Coupon.code == code, Coupon.is_active == True).first()


def get_category_by_slug_excluding(db: Session, slug: str, exclude_id: int) -> Category | None:
    return db.query(Category).filter(Category.slug == slug, Category.id != exclude_id).first()


def build_coupon_query(db: Session):
    from sqlalchemy import desc
    return db.query(Coupon).order_by(desc(Coupon.id))


def get_coupon_by_code(db: Session, code: str) -> Coupon | None:
    return db.query(Coupon).filter(Coupon.code == code).first()


def get_coupon_by_code_or_id(db: Session, coupon_id: str) -> Coupon | None:
    from sqlalchemy import or_
    filters = [Coupon.code == coupon_id]
    if coupon_id.isdigit():
        filters.append(Coupon.id == int(coupon_id))
    return db.query(Coupon).filter(or_(*filters)).first()


def coupon_has_usage(db: Session, coupon_id: int) -> bool:
    return db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon_id).first() is not None


def get_wishlist_item(db: Session, user_id: int, product_id: int) -> WishlistItem | None:
    return db.query(WishlistItem).filter(
        WishlistItem.user_id == user_id, WishlistItem.product_id == product_id
    ).first()


def list_wishlist_items(db: Session, user_id: int, offset: int = 0, limit: int = 200) -> list[WishlistItem]:
    from sqlalchemy.orm import selectinload
    return (
        db.query(WishlistItem)
        .options(selectinload(WishlistItem.product))
        .filter(WishlistItem.user_id == user_id)
        .offset(max(0, offset))
        .limit(min(max(1, limit), 200))
        .all()
    )