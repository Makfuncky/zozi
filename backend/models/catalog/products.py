from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, text as sa_text
from sqlalchemy.orm import relationship, foreign
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "Category", "Product", "ProductVariant", "ProductImage", "Review",
    "WishlistItem", "Wishlist", "ProductVideo", "VideoAnalytics",
    "ProductFilterMetadata", "ProductFilterOption",
    # Trading models
    "Warehouse", "StockMovement",
    "PurchaseOrder", "PurchaseOrderLine",
    "GoodsReceiptNote", "GoodsReceiptLine",
    "SalesOrder", "SalesOrderLine",
    # Finance / Trading-config models
    "TradeDeal", "TradeDealItem", "TradeSettlement", "TradingConfig",
    "FinanceReport", "FinanceDashboardMetrics",
    # Logistics models
    "LogisticsRate", "LogisticsZone", "LogisticsPricingRule",
]


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("commerce.categories.id"), nullable=True)
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
    category_id = Column(Integer, ForeignKey("commerce.categories.id"), nullable=True)
    tags = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
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
    images_rel = relationship("ProductImage", back_populates="product", order_by="ProductImage.sort_order")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
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
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")


class Wishlist(Base):
    __tablename__ = "wishlists"
    __table_args__ = ({"schema": "customer"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    user = relationship("User", back_populates="wishlists")
    product = relationship("Product", back_populates="wishlists")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
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
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])
    # Deterministic variant identity (Phase 3b). sha256 of the normalized
    # product_id + axes. Enables idempotent upserts and prevents duplicate
    # rows on AI re-runs.
    variant_key = Column(String(64), nullable=True, index=True)
    product = relationship("Product", back_populates="variants")

    __table_args__ = (
        UniqueConstraint("product_id", "variant_key", name="uq_product_variant_key"), {"schema": "commerce"})


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    product = relationship("Product", back_populates="images_rel")


class ProductVideo(Base):
    __tablename__ = "product_videos"
    __table_args__ = ({"schema": "media"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False, index=True)
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
    video_id = Column(Integer, ForeignKey("media.product_videos.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    watch_duration_seconds = Column(Integer, nullable=True)
    device_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class ProductFilterMetadata(Base):
    __tablename__ = "product_filter_metadata"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("commerce.categories.id"), nullable=True, index=True)
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
    filter_metadata_id = Column(Integer, ForeignKey("commerce.product_filter_metadata.id"), nullable=False, index=True)
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


# ── Trading Models ──────────────────────────────────────────────────────────────


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_stock_movements_product_id", "product_id"),
        Index("ix_stock_movements_warehouse_id", "warehouse_id"),
        Index("ix_stock_movements_reference", "reference_type", "reference_id"), {"schema": "logistics"})
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("logistics.warehouses.id"), nullable=True)
    movement_type = Column(String(50), nullable=False)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    quantity_change = Column(Numeric(14, 4), nullable=False)
    quantity_after = Column(Numeric(14, 4), nullable=False)
    unit_cost = Column(Numeric(14, 4), nullable=True)
    total_cost = Column(Numeric(14, 4), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)
    product = relationship("Product")
    warehouse = relationship("Warehouse")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_supplier", "supplier_id"),
        Index("ix_po_status", "status"),
        Index("ix_po_country", "country_code"), {"schema": "trading"})
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(80), unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("finance.vendors.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("finance.vendors.id"), nullable=True, index=True)
    supplier_name = Column(String(255), nullable=True)
    order_date = Column(DateTime, nullable=False, default=_utcnow)
    expected_delivery_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    warehouse_id = Column(Integer, ForeignKey("logistics.warehouses.id"), nullable=True)
    currency = Column(String(3), default="OMR")
    subtotal = Column(Numeric(14, 2), default=0)
    discount_total = Column(Numeric(14, 2), default=0)
    tax_total = Column(Numeric(14, 2), default=0)
    grand_total = Column(Numeric(14, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    warehouse = relationship("Warehouse")
    country = relationship("CountryConfig", foreign_keys=[country_code])
    vendor = relationship("Vendor", foreign_keys=[supplier_id])


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    __table_args__ = ({"schema": "trading"})
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("trading.purchase_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=True)
    product_name = Column(String(255), nullable=True)
    sku = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    quantity_ordered = Column(Numeric(14, 4), nullable=False, default=0)
    quantity_received = Column(Numeric(14, 4), default=0)
    unit_price = Column(Numeric(14, 4), nullable=False, default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    line_total = Column(Numeric(14, 2), default=0)
    weight = Column(Numeric(10, 3), nullable=True)
    volume = Column(Numeric(10, 3), nullable=True)
    country_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")


class GoodsReceiptNote(Base):
    __tablename__ = "goods_receipt_notes"
    __table_args__ = (
        Index("ix_grn_po_id", "po_id"),
        Index("ix_grn_supplier", "supplier_id"),
        Index("ix_grn_status", "status"), {"schema": "trading"})
    id = Column(Integer, primary_key=True, index=True)
    grn_number = Column(String(80), unique=True, index=True)
    po_id = Column(Integer, ForeignKey("trading.purchase_orders.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("finance.vendors.id"), nullable=True, index=True)
    receipt_date = Column(DateTime, nullable=False, default=_utcnow)
    warehouse_id = Column(Integer, ForeignKey("logistics.warehouses.id"), nullable=True)
    status = Column(String(50), default="draft")
    notes = Column(Text, nullable=True)
    received_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    purchase_order = relationship("PurchaseOrder")
    warehouse = relationship("Warehouse")
    lines = relationship("GoodsReceiptLine", back_populates="grn", cascade="all, delete-orphan")


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"
    __table_args__ = ({"schema": "trading"})
    id = Column(Integer, primary_key=True, index=True)
    grn_id = Column(Integer, ForeignKey("trading.goods_receipt_notes.id"), nullable=False, index=True)
    po_line_id = Column(Integer, ForeignKey("trading.purchase_order_lines.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=True)
    product_name = Column(String(255), nullable=True)
    sku = Column(String(100), nullable=True)
    quantity_received = Column(Numeric(14, 4), default=0)
    quantity_accepted = Column(Numeric(14, 4), default=0)
    quantity_rejected = Column(Numeric(14, 4), default=0)
    rejection_reason = Column(String(255), nullable=True)
    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    unit_cost = Column(Numeric(14, 4), nullable=True)
    country_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    grn = relationship("GoodsReceiptNote", back_populates="lines")
    po_line = relationship("PurchaseOrderLine")
    product = relationship("Product")


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    __table_args__ = (
        Index("ix_so_customer", "customer_id"),
        Index("ix_so_status", "status"),
        Index("ix_so_country", "country_code"), {"schema": "trading"})
    id = Column(Integer, primary_key=True, index=True)
    so_number = Column(String(80), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("finance.customers.id"), nullable=False, index=True)
    customer_name = Column(String(255), nullable=True)
    customer_po_number = Column(String(100), nullable=True)
    order_date = Column(DateTime, nullable=False, default=_utcnow)
    expected_delivery_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    warehouse_id = Column(Integer, ForeignKey("logistics.warehouses.id"), nullable=True)
    currency = Column(String(3), default="OMR")
    subtotal = Column(Numeric(14, 2), default=0)
    discount_total = Column(Numeric(14, 2), default=0)
    tax_total = Column(Numeric(14, 2), default=0)
    grand_total = Column(Numeric(14, 2), default=0)
    shipping_address = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    lines = relationship("SalesOrderLine", back_populates="sales_order", cascade="all, delete-orphan")
    warehouse = relationship("Warehouse")
    country = relationship("CountryConfig", foreign_keys=[country_code])
    customer = relationship("Customer", foreign_keys=[customer_id])


class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"
    __table_args__ = ({"schema": "trading"})
    id = Column(Integer, primary_key=True, index=True)
    so_id = Column(Integer, ForeignKey("trading.sales_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=True)
    product_name = Column(String(255), nullable=True)
    sku = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    quantity_ordered = Column(Numeric(14, 4), nullable=False, default=0)
    quantity_dispatched = Column(Numeric(14, 4), default=0)
    unit_price = Column(Numeric(14, 4), nullable=False, default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    line_total = Column(Numeric(14, 2), default=0)
    weight = Column(Numeric(10, 3), nullable=True)
    volume = Column(Numeric(10, 3), nullable=True)
    country_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    sales_order = relationship("SalesOrder", back_populates="lines")
    product = relationship("Product")


# ── Financial Trading & Reporting Models ────────────────────────────────────────


class TradeDeal(Base):
    __tablename__ = "trade_deals"
    __table_args__ = (
        Index("ix_trade_deals_counterparty", "counterparty_id"),
        Index("ix_trade_deals_status", "status"),
        Index("ix_trade_deals_country", "country_code"), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    deal_number = Column(String(80), unique=True, index=True)
    counterparty_id = Column(Integer, ForeignKey("finance.vendors.id"), nullable=False, index=True)
    counterparty_legal_name = Column(String(255), nullable=True)
    status = Column(String(50), default="draft")
    deal_date = Column(DateTime, nullable=False, default=_utcnow)
    settlement_date = Column(DateTime, nullable=True)
    buy_currency = Column(String(3), nullable=True)
    sell_currency = Column(String(3), nullable=True)
    buy_amount = Column(Numeric(14, 2), default=0)
    sell_amount = Column(Numeric(14, 2), default=0)
    rate = Column(Numeric(14, 6), nullable=True)
    total_value = Column(Numeric(14, 2), default=0)
    description = Column(Text, nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    items = relationship("TradeDealItem", back_populates="deal", cascade="all, delete-orphan")
    settlements = relationship("TradeSettlement", back_populates="deal", cascade="all, delete-orphan")
    counterparty = relationship("Vendor", foreign_keys=[counterparty_id])
    country = relationship("CountryConfig", primaryjoin="TradeDeal.country_code == foreign(CountryConfig.code)")


class TradeDealItem(Base):
    __tablename__ = "trade_deal_items"
    __table_args__ = ({"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("finance.trade_deals.id"), nullable=False, index=True)
    asset_code = Column(String(50), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False, default=0)
    unit_price = Column(Numeric(14, 4), nullable=False, default=0)
    total_value = Column(Numeric(14, 2), default=0)
    country_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    deal = relationship("TradeDeal", back_populates="items")


class TradeSettlement(Base):
    __tablename__ = "trade_settlements"
    __table_args__ = (
        Index("ix_trade_settlements_deal", "deal_id"),
        Index("ix_trade_settlements_status", "status"), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("finance.trade_deals.id"), nullable=False, index=True)
    settlement_date = Column(DateTime, nullable=False, default=_utcnow)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="OMR")
    status = Column(String(50), default="pending")
    reference_number = Column(String(100), nullable=True)
    payment_method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deal = relationship("TradeDeal", back_populates="settlements")


class TradingConfig(Base):
    __tablename__ = "trading_configs"
    __table_args__ = (
        UniqueConstraint("config_key", "country_code", name="uq_trading_configs_key_country"),
        Index("ix_trading_configs_country", "country_code"), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), nullable=False)
    config_value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class FinanceReport(Base):
    __tablename__ = "finance_reports"
    __table_args__ = (
        Index("ix_finance_reports_type", "report_type"),
        Index("ix_finance_reports_period", "period_start", "period_end"),
        Index("ix_finance_reports_status", "status"), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(100), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    generated_at = Column(DateTime, default=_utcnow)
    generated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    status = Column(String(50), default="generated")
    payload_json = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class FinanceDashboardMetrics(Base):
    __tablename__ = "finance_dashboard_metrics"
    __table_args__ = (
        UniqueConstraint("metric_key", "country_code", name="uq_finance_metrics_key_country"),
        Index("ix_finance_metrics_country", "country_code"), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    metric_key = Column(String(100), nullable=False)
    metric_value = Column(Numeric(18, 4), nullable=True)
    metric_label = Column(String(255), nullable=True)
    category = Column(String(50), nullable=True)
    computed_at = Column(DateTime, default=_utcnow, index=True)
    country_code = Column(String(10), nullable=True, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


# ── Logistics Models ────────────────────────────────────────────────────────────


class LogisticsZone(Base):
    __tablename__ = "logistics_zones"
    __table_args__ = (
        UniqueConstraint("zone_code", name="uq_logistics_zones_code"), {"schema": "logistics"})
    id = Column(Integer, primary_key=True, index=True)
    zone_name = Column(String(255), nullable=False)
    zone_code = Column(String(50), unique=True, nullable=False, index=True)
    country_codes = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    pricing_rules = relationship("LogisticsPricingRule", back_populates="zone", cascade="all, delete-orphan")


class LogisticsRate(Base):
    __tablename__ = "logistics_rates"
    __table_args__ = (
        Index("ix_logistics_rates_zone", "zone_id"),
        Index("ix_logistics_rates_carrier", "carrier_id"),
        Index("ix_logistics_rates_country", "country_code"), {"schema": "logistics"})
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("logistics.logistics_zones.id"), nullable=False, index=True)
    carrier_id = Column(Integer, ForeignKey("logistics.shipping_carriers.id"), nullable=True, index=True)
    service_level = Column(String(50), nullable=True)
    rate = Column(Numeric(14, 4), nullable=False)
    currency = Column(String(3), default="OMR")
    estimated_days_min = Column(Integer, nullable=True)
    estimated_days_max = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    zone = relationship("LogisticsZone")


class LogisticsPricingRule(Base):
    __tablename__ = "logistics_pricing_rules"
    __table_args__ = (
        Index("ix_logistics_pricing_zone", "zone_id"),
        Index("ix_logistics_pricing_vehicle", "vehicle_type"), {"schema": "logistics"})
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("logistics.logistics_zones.id"), nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False)
    distance_band_start = Column(Numeric(10, 2), nullable=True)
    distance_band_end = Column(Numeric(10, 2), nullable=True)
    weight_band_start = Column(Numeric(10, 2), nullable=True)
    weight_band_end = Column(Numeric(10, 2), nullable=True)
    base_rate = Column(Numeric(14, 4), nullable=False, default=0)
    per_km_rate = Column(Numeric(14, 4), default=0)
    per_kg_rate = Column(Numeric(14, 4), default=0)
    fuel_surcharge_percent = Column(Numeric(5, 2), default=0)
    currency = Column(String(3), default="OMR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    zone = relationship("LogisticsZone", back_populates="pricing_rules")
