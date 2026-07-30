from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, text as sa_text
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["Category", "Product", "ProductVariant", "Review", "WishlistItem", "Wishlist", "ProductVideo", "VideoAnalytics", "ProductFilterMetadata", "ProductFilterOption"]


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    icon = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    commission_rate = Column(Numeric(5, 4), nullable=True)
    meta_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    # Materialized path (Phase 3a): derived from parent_id. e.g. "/1/", "/1/15/",
    # "/1/15/42/". Enables O(1) sub-tree queries without recursive CTEs.
    path = Column(String(255), nullable=True, index=True)
    depth = Column(Integer, default=0)
    products = relationship("Product", back_populates="category_rel")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(Text, nullable=True)
    ai_description = Column(Text, nullable=True)
    sku = Column(String, unique=True, nullable=True)
    barcode = Column(String, unique=True, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    compare_price = Column(Numeric(10, 2), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=True)
    stock = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    weight = Column(Numeric(10, 2), nullable=True)
    dimensions = Column(String, nullable=True)
    materials = Column(JSON, nullable=True)
    image_url = Column(String, nullable=True)
    images = Column(JSON, nullable=True)
    category = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tags = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_digital = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=True)
    moderation_status = Column(String, default="approved")
    brand = Column(String, nullable=True)
    color = Column(String, nullable=True)
    sizes = Column(JSON, nullable=True)
    rating = Column(Numeric(3, 2), default=0)
    sales_count = Column(Integer, default=0)
    meta_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    discount_starts_at = Column(DateTime, nullable=True)
    discount_ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    filter_attributes = Column(JSON, nullable=True)
    search_vector = Column(JSON, nullable=True)
    video_count = Column(Integer, default=0)
    variant_axes = Column(JSON, nullable=True)
    bg_preset = Column(String, nullable=True)
    visibility_regions = Column(Text, nullable=True)
    slug_hash = Column(String(32), unique=True, nullable=True, index=True)
    subcategory = Column(String, nullable=True)
    return_window_days = Column(Integer, default=10)
    is_new = Column(Boolean, default=False)
    supplier = relationship("User", back_populates="products")
    category_rel = relationship("Category", back_populates="products")
    country = relationship("CountryConfig", foreign_keys=[country_code])
    reviews = relationship("Review", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")
    wishlists = relationship("Wishlist", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    variants = relationship(
        "ProductVariant", back_populates="product",
        order_by="ProductVariant.id", cascade="all, delete-orphan",
    )
    videos = relationship("ProductVideo", back_populates="product", order_by="ProductVideo.created_at.desc()")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_verified_purchase = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")


class Wishlist(Base):
    __tablename__ = "wishlists"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="wishlists")
    product = relationship("Product", back_populates="wishlists")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String, unique=True, nullable=True)
    title = Column(String, nullable=True)
    size = Column(String, nullable=True, index=True)
    color = Column(String, nullable=True, index=True)
    material = Column(String, nullable=True, index=True)
    pattern = Column(String, nullable=True, index=True)
    gender = Column(String, nullable=True, index=True)
    barcode = Column(String, unique=True, nullable=True)
    product_code = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    stock = Column(Integer, default=0)
    media_url = Column(String, nullable=True)
    attributes_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])
    # Deterministic variant identity (Phase 3b). sha256 of the normalized
    # product_id + axes. Enables idempotent upserts and prevents duplicate
    # rows on AI re-runs.
    variant_key = Column(String(64), nullable=True, index=True)
    product = relationship("Product", back_populates="variants")

    __table_args__ = (
        UniqueConstraint("product_id", "variant_key", name="uq_product_variant_key"), {"schema": "commerce"})


class ProductVideo(Base):
    __tablename__ = "product_videos"
    __table_args__ = ({"schema": "media"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    video_type = Column(String(50), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    views_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    upload_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    product = relationship("Product", back_populates="videos")


class VideoAnalytics(Base):
    __tablename__ = "video_analytics"
    __table_args__ = ({"schema": "media"},)
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("product_videos.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    watch_duration_seconds = Column(Integer, nullable=True)
    device_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class ProductFilterMetadata(Base):
    __tablename__ = "product_filter_metadata"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    filter_name = Column(String(100), nullable=False)
    filter_type = Column(String(50), nullable=False)
    display_order = Column(Integer, nullable=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default=sa_text("true"))
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    category = relationship("Category")
    options = relationship("ProductFilterOption", back_populates="filter_metadata", order_by="ProductFilterOption.sort_order")


class ProductFilterOption(Base):
    __tablename__ = "product_filter_options"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    filter_metadata_id = Column(Integer, ForeignKey("product_filter_metadata.id"), nullable=False, index=True)
    option_value = Column(String(255), nullable=False)
    option_display_name = Column(String(255), nullable=False)
    product_count = Column(Integer, nullable=False, server_default="0")
    sort_order = Column(Integer, nullable=False, server_default="0")
    country_code = Column(String(10), nullable=True, index=True)
    filter_metadata = relationship("ProductFilterMetadata", back_populates="options")


Product.variants = relationship(
    "ProductVariant", back_populates="product",
    order_by="ProductVariant.id", cascade="all, delete-orphan",
)
