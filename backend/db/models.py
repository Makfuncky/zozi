from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, BigInteger, Time
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base
from utils.encryption import EncryptedString
from utils.datetime_utils import utcnow as _utcnow


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String(160), nullable=True)
    hashed_password = Column(String)
    role = Column(String, default="customer", index=True)  # customer, supplier, admin
    is_active = Column(Integer, default=1)
    # Extended profile
    phone = Column(EncryptedString(100), nullable=True)
    profile_image = Column(String, nullable=True)
    # Address information is stored in the Address table (replaces JSON address_book field)
    preferred_language = Column(String, default="en")
    preferred_currency = Column(String(10), default="OMR")
    preferred_country = Column(String(10), default="OM")
    # Browsing history is stored in the user_browsing_history table (replaces JSON browsing_history_json)
    referral_code = Column(String(24), unique=True, index=True, nullable=True)
    referred_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    referral_points = Column(Integer, default=0)
    sharing_points = Column(Integer, default=0)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)          # supplier KYC/verification status
    staff_role_label = Column(String(120), nullable=True)
    staff_title = Column(String(120), nullable=True)
    staff_department = Column(String(120), nullable=True)
    staff_area_of_operation = Column(String(200), nullable=True)
    staff_hire_date = Column(Date, nullable=True)
    staff_experience_level = Column(String(80), nullable=True)
    staff_performance_summary = Column(String(255), nullable=True)
    staff_assigned_tasks = Column(JSON, nullable=True)
    staff_assigned_projects = Column(JSON, nullable=True)
    staff_permissions = Column(JSON, nullable=True)
    staff_notes = Column(Text, nullable=True)
    staff_country_codes = Column(JSON, nullable=True)  # ["SA", "AE", ...] — which countries this staff member manages
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class UserDevice(Base):
    """Tracks user devices for session management and security."""
    __tablename__ = "user_devices"
    __table_args__ = (
        Index("ix_user_devices_user_created", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(255), nullable=False, index=True)
    device_type = Column(String(50), nullable=True)
    device_name = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    last_seen = Column(DateTime, default=_utcnow, index=True)
    is_trusted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class UserBrowsingHistory(Base):
    """Tracks user's browsing history for recently viewed products."""
    __tablename__ = "user_browsing_history"
    __table_args__ = (
        Index("ix_user_browsing_history_user_created", "user_id", "viewed_at"),
        Index("ix_user_browsing_history_product_created", "product_id", "viewed_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    viewed_at = Column(DateTime, default=_utcnow, index=True)

    user = relationship("User")
    product = relationship("Product")


class ReferralPointEvent(Base):
    """Immutable referral/share points ledger for customer growth actions."""
    __tablename__ = "referral_point_events"
    __table_args__ = (
        Index("ix_referral_point_events_user_created", "user_id", "created_at"),
        Index("ix_referral_point_events_type_created", "event_type", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(40), nullable=False, index=True)
    points = Column(Integer, nullable=False)
    channel = Column(String(40), nullable=True)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)

    user = relationship("User", foreign_keys=[user_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_supplier_deleted_created", "supplier_id", "is_deleted", "created_at"),
        Index("ix_products_category_deleted_created", "category", "is_deleted", "created_at"),
        Index("ix_products_category_id_deleted_created", "category_id", "is_deleted", "created_at"),
        Index("ix_products_brand_deleted", "brand", "is_deleted"),
        Index("ix_products_public_visibility_created", "is_deleted", "is_active", "is_approved", "created_at"),
        Index("ix_products_public_visibility_sales", "is_deleted", "is_active", "is_approved", "sales_count"),
        Index("ix_products_public_visibility_rating", "is_deleted", "is_active", "is_approved", "rating"),
        CheckConstraint("price >= 0", name="ck_products_price_nonnegative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_nonnegative"),
        CheckConstraint("compare_price IS NULL OR compare_price >= 0", name="ck_products_compare_price_nonnegative"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_products_rating_range"),
        CheckConstraint("sales_count >= 0", name="ck_products_sales_count_nonnegative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String(180), nullable=True, unique=True, index=True)
    sku = Column(String(120), nullable=True, index=True)
    description = Column(Text)
    short_description = Column(Text, nullable=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2))
    cost_price = Column(Numeric(12, 2), nullable=True)
    category = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    subcategory = Column(String, nullable=True, index=True)
    brand = Column(String, index=True)
    rating = Column(Float, default=0.0)
    image_url = Column(String)
    images = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    stock = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, nullable=True)
    minimum_stock = Column(Integer, nullable=True, default=0)
    maximum_stock = Column(Integer, nullable=True, default=0)
    view_count = Column(Integer, default=0)
    color = Column(String, index=True)
    attributes = Column(Text, nullable=True)
    tags = Column(String, nullable=True)           # comma-separated AI-generated tags
    ai_description = Column(Text, nullable=True)   # AI-generated description
    sizes = Column(Text, nullable=True)             # JSON array: ["S","M","L","XL"]
    materials = Column(String, nullable=True)       # e.g. "Cotton, Polyester"
    visibility_regions = Column(Text, nullable=True) # JSON array of customer-visible regions/countries
    additional_images = Column(Text, nullable=True) # JSON array of image paths/URLs
    weight = Column(Float, nullable=True)           # in kg
    dimensions = Column(String, nullable=True)      # e.g. "30x20x10 cm"
    compare_price = Column(Numeric(12, 2), nullable=True)     # original / compare-at price; discount % derived from this
    discount_starts_at = Column(DateTime, nullable=True)
    discount_ends_at = Column(DateTime, nullable=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), index=True)
    is_deleted = Column(Boolean, default=False)   # soft delete
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)      # can be deactivated without deletion
    is_digital = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)    # admin moderation: False = awaiting approval
    moderation_status = Column(String(40), nullable=True)
    sales_count = Column(Integer, default=0)       # incremented on order confirmed
    is_hot = Column(Boolean, nullable=True, default=None)       # admin: pin HOT badge
    is_featured = Column(Boolean, nullable=True, default=None)  # admin: pin FEATURED badge
    is_new = Column(Boolean, nullable=True, default=None)       # supplier/admin: pin NEW badge
    return_window_days = Column(Integer, nullable=True, default=10)  # days customer can request return (min 10)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])
    category_node = relationship("Category", foreign_keys=[category_id])
    reviews = relationship("Review", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")
    commission_override = relationship("ProductCommissionOverride", back_populates="product", uselist=False)
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan", order_by="ProductVariant.sort_order")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        Index("ix_product_variants_product_sort", "product_id", "sort_order"),
        Index("ix_product_variants_product_active", "product_id", "is_active"),
        UniqueConstraint("sku", name="uq_product_variants_sku"),
        UniqueConstraint("barcode", name="uq_product_variants_barcode"),
        UniqueConstraint("product_code", name="uq_product_variants_product_code"),
        CheckConstraint("stock >= 0", name="ck_product_variants_stock_nonnegative"),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_product_variants_price_nonnegative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(160), nullable=True)
    size = Column(String(100), nullable=True)
    color = Column(String(100), nullable=True)
    material = Column(String(160), nullable=True)
    sku = Column(String(120), nullable=True, index=True)
    barcode = Column(String(160), nullable=True, index=True)
    product_code = Column(String(120), nullable=True, index=True)
    price = Column(Numeric(12, 2), nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    media_url = Column(String(500), nullable=True)
    attributes_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    product = relationship("Product", back_populates="variants")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_created", "user_id", "created_at"),
        Index("ix_orders_status_created", "status", "created_at"),
        CheckConstraint("subtotal_amount IS NULL OR subtotal_amount >= 0", name="ck_orders_subtotal_nonnegative"),
        CheckConstraint("discount_amount >= 0", name="ck_orders_discount_nonnegative"),
        CheckConstraint("vat_amount >= 0", name="ck_orders_vat_nonnegative"),
        CheckConstraint("shipping_amount >= 0", name="ck_orders_shipping_nonnegative"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_nonnegative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    order_number = Column(String(120), nullable=True, unique=True, index=True)
    currency = Column(String(10), nullable=True, default="AED")
    subtotal_amount = Column(Numeric(12, 2), nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=True)
    discount_amount = Column(Numeric(12, 2), default=0.0)
    vat_amount = Column(Numeric(12, 2), default=0.0)      # Server-computed VAT (e.g. 5% UAE VAT)
    tax_amount = Column(Numeric(12, 2), nullable=True)
    shipping_amount = Column(Numeric(12, 2), default=0.0) # Server-computed shipping cost
    shipping_fee = Column(Numeric(12, 2), nullable=True)
    total_amount = Column(Numeric(12, 2))                 # subtotal - discount + vat + shipping
    total = Column(Numeric(12, 2), nullable=True)
    coupon_code = Column(String, nullable=True, index=True)
    payment_method = Column(String(20), nullable=False, default="card", server_default="card")
    payment_status = Column(String(30), nullable=True, default="pending")
    status = Column(String, default="pending", index=True)
    shipping_address = Column(EncryptedString(), nullable=True)
    shipping_city = Column(String(120), nullable=True)
    shipping_country = Column(String(120), nullable=True)
    shipping_postal_code = Column(String(40), nullable=True)
    customer_phone = Column(EncryptedString(60), nullable=True)
    delivery_location = Column(String(255), nullable=True)
    delivery_note = Column(Text, nullable=True)
    tracking_number = Column(String, nullable=True)
    payment_intent_id = Column(String, nullable=True, index=True)  # Stripe/Tap payment ID
    payment_gateway_code = Column(String(60), nullable=True, index=True)
    payment_gateway_fee_amount = Column(Numeric(12, 2), default=0.0)
    payment_customer_total_amount = Column(Numeric(12, 2), nullable=True)
    payment_gateway_fee_passed_to_customer = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)                       # Set when payment succeeds
    selected_partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=True)  # Partner used for shipping quote
    selected_service_area_id = Column(Integer, ForeignKey("logistics_partner_service_areas.id"), nullable=True)
    estimated_delivery_min = Column(Integer, nullable=True)  # Days from service area at order time
    estimated_delivery_max = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    selected_partner = relationship("LogisticsPartner", foreign_keys=[selected_partner_id])
    logistics_allocations = relationship("OrderLogisticsAllocation", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_product_order", "product_id", "order_id"),
        Index("ix_order_items_order_product", "order_id", "product_id"),
        Index("ix_order_items_variant_order", "variant_id", "order_id"),
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("price >= 0", name="ck_order_items_price_nonnegative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True, index=True)
    quantity = Column(Integer)
    price = Column(Numeric(12, 2))  # Price at time of order
    unit_price = Column(Numeric(12, 2), nullable=True)
    total_price = Column(Numeric(12, 2), nullable=True)
    product_name = Column(String(255), nullable=True)
    product_image = Column(String(500), nullable=True)
    selected_size = Column(String(100), nullable=False, default="")
    selected_color = Column(String(100), nullable=False, default="")

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")


class Review(Base):
    """Customer product reviews — used by Phase 2 /reviews router."""
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    rating = Column(Float, nullable=False)  # 1.0 – 5.0
    comment = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    is_verified_purchase = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", foreign_keys=[user_id])


class Wishlist(Base):
    """Persisted per-user wishlist — enables cross-device sync."""
    __tablename__ = "wishlists"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")
    product = relationship("Product")


class ChatbotQueryEvent(Base):
    """Assistant query and engagement analytics for shopping conversations."""
    __tablename__ = "chatbot_query_events"
    __table_args__ = (
        Index("ix_chatbot_events_user_created", "user_id", "created_at"),
        Index("ix_chatbot_events_session_created", "session_id", "created_at"),
        Index("ix_chatbot_events_type_created", "event_type", "created_at"),
        Index("ix_chatbot_events_intent_created", "intent", "created_at"),
        CheckConstraint("result_count >= 0", name="ck_chatbot_events_result_count_nonnegative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(30), nullable=False, default="query")  # query | product_click
    message = Column(Text, nullable=True)
    normalized_query = Column(String(500), nullable=True, index=True)
    intent = Column(String(100), nullable=True, index=True)
    filters_json = Column(Text, nullable=True)
    result_count = Column(Integer, default=0)
    product_ids_json = Column(Text, nullable=True)
    clicked_product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow, index=True)

    user = relationship("User", foreign_keys=[user_id])
    clicked_product = relationship("Product", foreign_keys=[clicked_product_id])


class Coupon(Base):
    """Discount coupons redeemable at checkout."""
    __tablename__ = "coupons"
    __table_args__ = (
        CheckConstraint("value >= 0", name="ck_coupons_value_nonnegative"),
        CheckConstraint("min_order >= 0", name="ck_coupons_min_order_nonnegative"),
        CheckConstraint("uses_count >= 0", name="ck_coupons_uses_count_nonnegative"),
        CheckConstraint("max_uses IS NULL OR max_uses >= 0", name="ck_coupons_max_uses_nonnegative"),
        CheckConstraint("discount_type IN ('percent','fixed')", name="ck_coupons_discount_type_valid"),
    )
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    applicable_to = Column(String(60), nullable=True)
    discount_type = Column(String, default="percent")  # percent | fixed
    value = Column(Numeric(12, 2))  # percentage (10 = 10%) or fixed AED amount
    discount_value = Column(Numeric(12, 2), nullable=True)
    min_order = Column(Numeric(12, 2), default=0.0)
    minimum_order = Column(Numeric(12, 2), nullable=True)
    maximum_discount = Column(Numeric(12, 2), nullable=True)
    max_uses = Column(Integer, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    per_user_limit = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class Notification(Base):
    """In-app notifications for customers and suppliers."""
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_user_read_created", "user_id", "read", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(String)  # order_update | low_stock | payout | system
    title = Column(String)
    message = Column(Text)
    read = Column(Boolean, default=False)
    link = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class SupplierNotificationPreference(Base):
    """Supplier-configurable notification channels and event preferences."""
    __tablename__ = "supplier_notification_preferences"
    __table_args__ = (
        UniqueConstraint("supplier_id", name="uq_supplier_notification_preferences_supplier"),
        Index("ix_supplier_notification_preferences_supplier", "supplier_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notify_new_order = Column(Boolean, nullable=False, default=True)
    notify_low_stock = Column(Boolean, nullable=False, default=True)
    notify_payout_processed = Column(Boolean, nullable=False, default=True)
    notify_doc_expiry = Column(Boolean, nullable=False, default=True)
    notify_return_updates = Column(Boolean, nullable=False, default=True)
    notify_dispute_updates = Column(Boolean, nullable=False, default=True)
    in_app_enabled = Column(Boolean, nullable=False, default=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    push_enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])


class Category(Base):
    """Hierarchical product categories (supports parent/child tree)."""
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_active_parent_sort_name", "is_active", "parent_id", "sort_order", "name"),
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # e.g. emoji or icon name
    image_url = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    commission_rate = Column(Float, nullable=True)
    meta_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    children = relationship("Category", back_populates="parent", lazy="dynamic")
    parent = relationship("Category", back_populates="children", remote_side=[id])


class PasswordResetToken(Base):
    """Single-use password reset tokens (TTL: 1 hour)."""
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class SupplierProfile(Base):
    """Extended business registration & location profile for supplier accounts."""
    __tablename__ = "supplier_profiles"
    __table_args__ = (Index("ix_supplier_profiles_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    slug = Column(String(180), nullable=True, unique=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    # Business identity
    business_name = Column(String(200), nullable=True)
    business_type = Column(String(50), default="individual")  # individual | company | partnership | llc
    # Location
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)    # state / province / emirate
    city = Column(String(100), nullable=True)
    address = Column(EncryptedString(), nullable=True)
    postal_code = Column(EncryptedString(50), nullable=True)
    # Contact
    phone_business = Column(EncryptedString(60), nullable=True)
    website = Column(String(300), nullable=True)
    # Compliance
    tax_id = Column(EncryptedString(150), nullable=True)
    bank_details_json = Column(EncryptedString(), nullable=True)  # Encrypted bank account details
    bio = Column(Text, nullable=True)
    operating_regions = Column(Text, nullable=True)   # JSON list of country/region names
    is_terms_accepted = Column(Boolean, default=False)
    terms_version = Column(String(20), nullable=True)
    terms_accepted_at = Column(DateTime, nullable=True)
    # Admin review
    verification_status = Column(String(30), default="pending")  # pending | under_review | approved | rejected
    verified_at = Column(DateTime, nullable=True)
    # Credibility badge system
    credibility_score = Column(Integer, default=0)   # 0-100 computed score
    badge_level = Column(String(20), nullable=True)  # none/bronze/silver/gold/verified
    badge_granted_at = Column(DateTime, nullable=True)
    verified_documents = Column(Text, nullable=True)  # JSON list of document URLs
    document_expires_at = Column(DateTime, nullable=True)
    # Customer-facing supplier page fields
    about_us = Column(Text, nullable=True)            # long-form About Us shown to customers
    logo_url = Column(String(500), nullable=True)     # supplier logo image URL
    banner_url = Column(String(500), nullable=True)   # supplier cover/banner image URL
    video_url = Column(String(500), nullable=True)    # YouTube/Vimeo embed URL
    certifications = Column(Text, nullable=True)      # JSON list of {title, issuer, year, image_url}
    social_links = Column(Text, nullable=True)        # JSON dict: {instagram, facebook, twitter, linkedin, youtube}
    established_year = Column(Integer, nullable=True) # year business was founded
    max_return_days = Column(Integer, nullable=True, default=30)  # max return window supplier can grant
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    country = relationship("CountryConfig", foreign_keys=[country_code])


class EmailVerificationToken(Base):
    """Single-use email verification tokens (TTL: 24 hours)."""
    __tablename__ = "email_verification_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class AdminAnalyticsSnapshot(Base):
    __tablename__ = "admin_analytics_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_key", name="uq_admin_analytics_snapshots_key"),
        Index("ix_admin_analytics_snapshots_group_computed", "snapshot_group", "computed_at"),
        Index("ix_admin_analytics_snapshots_expires", "expires_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    snapshot_key = Column(String(120), nullable=False, index=True)
    snapshot_group = Column(String(80), nullable=False, index=True)
    period = Column(String(40), nullable=True)
    payload_json = Column(Text, nullable=False)
    computed_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)


class Payout(Base):
    """Supplier payout requests and history."""
    __tablename__ = "payouts"
    __table_args__ = (
        Index("ix_payouts_supplier_created", "supplier_id", "created_at"),
        Index("ix_payouts_country", "country_code"),
        CheckConstraint("amount >= 0", name="ck_payouts_amount_nonnegative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="pending")  # pending | processing | completed | rejected
    method = Column(String, default="bank")  # bank | paypal | stripe
    reference = Column(EncryptedString(255), nullable=True)  # bank ref / PayPal txn id
    notes = Column(Text, nullable=True)
    provider = Column(String(50), nullable=True)
    provider_recipient_id = Column(String(255), nullable=True)
    provider_quote_id = Column(String(255), nullable=True)
    provider_transfer_id = Column(String(255), nullable=True)
    provider_payment_id = Column(String(255), nullable=True)
    provider_status = Column(String(50), nullable=True)
    last_provider_sync_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    processed_at = Column(DateTime, nullable=True)

    supplier = relationship("User", foreign_keys=[supplier_id])
    country = relationship("CountryConfig", foreign_keys=[country_code])


class LogisticsPartnerPayout(Base):
    """Logistics partner payout requests and settlement history."""
    __tablename__ = "logistics_partner_payouts"
    __table_args__ = (
        Index("ix_logistics_partner_payouts_partner_created", "partner_id", "created_at"),
        Index("ix_logistics_partner_payouts_country", "country_code"),
        CheckConstraint("amount >= 0", name="ck_logistics_partner_payouts_amount_nonnegative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="OMR")
    status = Column(String, default="pending")
    reference = Column(EncryptedString(255), nullable=True)
    notes = Column(Text, nullable=True)
    provider = Column(String(50), nullable=True)
    provider_recipient_id = Column(String(255), nullable=True)
    provider_quote_id = Column(String(255), nullable=True)
    provider_transfer_id = Column(String(255), nullable=True)
    provider_payment_id = Column(String(255), nullable=True)
    provider_status = Column(String(50), nullable=True)
    last_provider_sync_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="payouts")
    country = relationship("CountryConfig", foreign_keys=[country_code])


class ReturnRequest(Base):
    """Customer return requests for order items."""
    __tablename__ = "return_requests"
    __table_args__ = (
        Index("ix_return_requests_user_order_status", "user_id", "order_id", "status"),
        Index("ix_return_requests_order_item_status", "order_item_id", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True, nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    intent = Column(String(30), default="return", nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="pending", index=True)  # pending | approved | rejected | completed
    resolution_notes = Column(Text, nullable=True)
    supplier_review_state = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    resolved_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    order = relationship("Order")
    order_item = relationship("OrderItem")


class SupplierDispute(Base):
    """Supplier-filed dispute workflow for return, verification, invoice, and payout issues."""
    __tablename__ = "supplier_disputes"
    __table_args__ = (
        Index("ix_supplier_disputes_supplier_status", "supplier_id", "status"),
        Index("ix_supplier_disputes_priority_created", "priority", "created_at"),
        CheckConstraint(
            "dispute_type IN ('return','verification','invoice','payout','other')",
            name="ck_supplier_disputes_type_valid",
        ),
        CheckConstraint(
            "priority IN ('low','medium','high','urgent')",
            name="ck_supplier_disputes_priority_valid",
        ),
        CheckConstraint(
            "status IN ('pending','under_review','resolved','rejected','closed')",
            name="ck_supplier_disputes_status_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    dispute_type = Column(String(40), nullable=False, default="other", index=True)
    priority = Column(String(20), nullable=False, default="medium", index=True)
    status = Column(String(30), nullable=False, default="pending", index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    return_request_id = Column(Integer, ForeignKey("return_requests.id"), nullable=True, index=True)
    verification_id = Column(Integer, ForeignKey("product_verifications.id"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True, index=True)
    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)

    evidence_urls = Column(Text, nullable=True)  # JSON list of URL strings
    metadata_json = Column(Text, nullable=True)  # JSON object
    supplier_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])
    creator = relationship("User", foreign_keys=[created_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    return_request = relationship("ReturnRequest")
    verification = relationship("ProductVerification")
    invoice = relationship("Invoice")
    order = relationship("Order", foreign_keys=[related_order_id])


class Address(Base):
    """Normalised address book entry per user (replaces JSON address_book field)."""
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    label = Column(String, default="Home")          # Home | Work | Other
    street = Column(EncryptedString(), nullable=False)
    city = Column(EncryptedString(120), nullable=False)
    state = Column(EncryptedString(120), nullable=True)
    postal_code = Column(EncryptedString(50), nullable=True)
    country = Column(String, default="AE")          # ISO 3166-1 alpha-2
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class CouponUsage(Base):
    """Tracks which user has used which coupon — enforces per-user usage limits."""
    __tablename__ = "coupon_usages"
    __table_args__ = (
        UniqueConstraint("user_id", "coupon_id", name="uq_coupon_usage_user_coupon"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), index=True)
    used_at = Column(DateTime, default=_utcnow)

    user = relationship("User")
    coupon = relationship("Coupon")


class FlashSale(Base):
    """Time-limited discount campaigns surfaced on the homepage and offers page."""
    __tablename__ = "flash_sales"
    __table_args__ = (
        Index("ix_flash_sales_active_window", "is_active", "ends_at", "starts_at"),
        CheckConstraint("discount_pct >= 0 AND discount_pct <= 100", name="ck_flash_sales_discount_pct_range"),
    )
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    discount_pct = Column(Float, nullable=False)        # e.g. 20.0 = 20% off
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    product_ids = Column(Text, nullable=True)           # JSON array of product IDs in the sale
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class PromotionEngineConfig(Base):
    """Global promotion engine controls managed from the admin Promotion Builder."""
    __tablename__ = "promotion_engine_configs"
    __table_args__ = (
        CheckConstraint(
            "stacking_mode IN ('best_only', 'stack_all', 'custom')",
            name="ck_promotion_engine_configs_stacking_mode_valid",
        ),
        CheckConstraint(
            "max_combined_discount_percent >= 0 AND max_combined_discount_percent <= 100",
            name="ck_promotion_engine_configs_max_discount_pct_range",
        ),
        CheckConstraint("max_combined_discount_amount >= 0", name="ck_promotion_engine_configs_max_discount_amount_nonnegative"),
        CheckConstraint("points_per_omr > 0", name="ck_promotion_engine_configs_points_per_omr_positive"),
        CheckConstraint("referral_referrer_points >= 0", name="ck_promotion_engine_configs_referrer_points_nonnegative"),
        CheckConstraint("referral_referee_points >= 0", name="ck_promotion_engine_configs_referee_points_nonnegative"),
        CheckConstraint("points_expiry_months >= 0", name="ck_promotion_engine_configs_points_expiry_nonnegative"),
        CheckConstraint("referral_monthly_cap >= 0", name="ck_promotion_engine_configs_referral_cap_nonnegative"),
        CheckConstraint("referral_verification_delay_days >= 0", name="ck_promotion_engine_configs_verification_delay_nonnegative"),
        CheckConstraint("min_points_redeem >= 0", name="ck_promotion_engine_configs_min_points_redeem_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    engine_enabled = Column(Boolean, default=False)
    allow_product_coupons = Column(Boolean, default=True)
    allow_category_coupons = Column(Boolean, default=True)
    allow_order_tier_discounts = Column(Boolean, default=True)
    allow_referral_rewards = Column(Boolean, default=True)
    allow_supplier_promotions = Column(Boolean, default=True)
    allow_global_coupons = Column(Boolean, default=True)
    stacking_mode = Column(String(20), nullable=False, default="best_only")
    max_combined_discount_percent = Column(Numeric(5, 2), nullable=False, default=Decimal("50.00"))
    max_combined_discount_amount = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    show_savings_line_item = Column(Boolean, default=True)
    tier_discount_visible = Column(Boolean, default=True)

    points_per_omr = Column(Integer, nullable=False, default=1000)
    referral_referrer_points = Column(Integer, nullable=False, default=100)
    referral_referee_points = Column(Integer, nullable=False, default=100)
    points_expiry_months = Column(Integer, nullable=False, default=12)
    referral_monthly_cap = Column(Integer, nullable=False, default=20)
    referral_verification_delay_days = Column(Integer, nullable=False, default=7)
    min_points_redeem = Column(Integer, nullable=False, default=1000)
    allow_partial_points_redemption = Column(Boolean, default=True)

    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])


class PromotionOrderTier(Base):
    """Order-value tier discount bands managed by admins."""
    __tablename__ = "promotion_order_tiers"
    __table_args__ = (
        Index("ix_promotion_order_tiers_active_sort", "is_active", "sort_order", "min_order"),
        CheckConstraint("min_order >= 0", name="ck_promotion_order_tiers_min_order_nonnegative"),
        CheckConstraint("max_order IS NULL OR max_order >= min_order", name="ck_promotion_order_tiers_max_ge_min"),
        CheckConstraint("discount_type IN ('fixed','percent')", name="ck_promotion_order_tiers_discount_type_valid"),
        CheckConstraint("discount_value >= 0", name="ck_promotion_order_tiers_discount_value_nonnegative"),
        CheckConstraint("sort_order >= 0", name="ck_promotion_order_tiers_sort_order_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tier_name = Column(String(80), nullable=False)
    min_order = Column(Numeric(12, 3), nullable=False)
    max_order = Column(Numeric(12, 3), nullable=True)
    discount_type = Column(String(20), nullable=False, default="fixed")
    discount_value = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    stacking_allowed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])


class PromotionLedgerEntry(Base):
    """Immutable promotion application rows for order audit/reconciliation."""
    __tablename__ = "promotion_ledger_entries"
    __table_args__ = (
        Index("ix_promotion_ledger_order_created", "order_id", "created_at"),
        Index("ix_promotion_ledger_user_created", "user_id", "created_at"),
        CheckConstraint("discount_amount >= 0", name="ck_promotion_ledger_discount_amount_nonnegative"),
        CheckConstraint("points_awarded >= 0", name="ck_promotion_ledger_points_awarded_nonnegative"),
        CheckConstraint("points_redeemed >= 0", name="ck_promotion_ledger_points_redeemed_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    promotion_type = Column(String(40), nullable=False, default="order_tier")
    promotion_code = Column(String(80), nullable=True)
    tier_id = Column(Integer, ForeignKey("promotion_order_tiers.id"), nullable=True, index=True)
    discount_amount = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    points_awarded = Column(Integer, nullable=False, default=0)
    points_redeemed = Column(Integer, nullable=False, default=0)
    stacking_flag = Column(Boolean, default=False)
    source = Column(String(80), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    order = relationship("Order", foreign_keys=[order_id])
    user = relationship("User", foreign_keys=[user_id])
    tier = relationship("PromotionOrderTier", foreign_keys=[tier_id])


class ProcessedWebhookEvent(Base):
    """Idempotency log for inbound webhook events."""
    __tablename__ = "processed_webhook_events"
    __table_args__ = (
        Index("ix_processed_webhook_processor_event", "processor", "event_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, nullable=False, index=True)   # e.g. Stripe event ID
    processor = Column(String, nullable=False)              # stripe | tap
    processed_at = Column(DateTime, default=_utcnow)


class PaymentReconciliationRun(Base):
    __tablename__ = "payment_reconciliation_runs"
    __table_args__ = (
        Index("ix_payment_reconciliation_runs_started", "started_at"),
        Index("ix_payment_reconciliation_runs_status", "status", "started_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(30), nullable=False, default="running")
    processed_count = Column(Integer, nullable=False, default=0)
    reconciled_count = Column(Integer, nullable=False, default=0)
    unmatched_count = Column(Integer, nullable=False, default=0)
    stale_pending_orders = Column(Integer, nullable=False, default=0)
    recent_webhook_count = Column(Integer, nullable=False, default=0)
    result_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)


class RetentionJobRun(Base):
    __tablename__ = "retention_job_runs"
    __table_args__ = (
        Index("ix_retention_job_runs_target_started", "target_name", "started_at"),
        Index("ix_retention_job_runs_status", "status", "started_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    target_name = Column(String(80), nullable=False, index=True)
    cutoff_days = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="running")
    archived_count = Column(Integer, nullable=False, default=0)
    deleted_count = Column(Integer, nullable=False, default=0)
    artifact_path = Column(String(500), nullable=True)
    result_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)


class SupportTicket(Base):
    """Customer support tickets — raised by customers or suppliers."""
    __tablename__ = "support_tickets"
    __table_args__ = (
        Index("ix_support_tickets_user_created", "user_id", "created_at"),
        Index("ix_support_tickets_status_created", "status", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="open", index=True)  # open | in_progress | closed
    priority = Column(String, default="normal")          # low | normal | high | urgent
    ticket_category = Column(String(30), nullable=True, default="customer")  # customer | supplier | logistics_partner
    raised_by_role = Column(String(30), nullable=True)   # snapshot of creator role
    related_entity_type = Column(String(30), nullable=True)  # order | product | shipment | payout
    related_entity_id = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    replies = relationship("TicketReply", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")


class TicketReply(Base):
    """Replies to a support ticket (from admin or customer)."""
    __tablename__ = "ticket_replies"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    message = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    ticket = relationship("SupportTicket", back_populates="replies")
    user = relationship("User")
    attachments = relationship("TicketAttachment", back_populates="reply", cascade="all, delete-orphan")

    @property
    def sender_id(self):
        return self.user_id

    @sender_id.setter
    def sender_id(self, value):
        self.user_id = value


# ── Email Marketing ───────────────────────────────────────────────────────────

class PaymentGatewayConnection(Base):
    """Runtime-managed payment gateway connection settings and fee profile."""
    __tablename__ = "payment_gateway_connections"
    __table_args__ = (
        UniqueConstraint("provider_code", name="uq_payment_gateway_connections_provider_code"),
        CheckConstraint(
            "provider_kind IN ('stripe', 'tap', 'custom')",
            name="ck_payment_gateway_connections_provider_kind_valid",
        ),
        CheckConstraint(
            "mode IN ('test', 'live')",
            name="ck_payment_gateway_connections_mode_valid",
        ),
        CheckConstraint(
            "test_status IN ('untested', 'passed', 'failed')",
            name="ck_payment_gateway_connections_test_status_valid",
        ),
        CheckConstraint(
            "settlement_cycle IN ('daily', 'weekly', 'monthly')",
            name="ck_payment_gateway_connections_settlement_cycle_valid",
        ),
        CheckConstraint(
            "fee_percent >= 0",
            name="ck_payment_gateway_connections_fee_percent_nonnegative",
        ),
        CheckConstraint(
            "fixed_fee_amount >= 0",
            name="ck_payment_gateway_connections_fixed_fee_nonnegative",
        ),
        CheckConstraint(
            "payout_fee_percent >= 0",
            name="ck_payment_gateway_connections_payout_fee_percent_nonnegative",
        ),
        CheckConstraint(
            "payout_fixed_fee_amount >= 0",
            name="ck_payment_gateway_connections_payout_fixed_fee_nonnegative",
        ),
    )
    id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(String(60), nullable=False, index=True)
    provider_kind = Column(String(20), nullable=False, default="custom")
    display_name = Column(String(120), nullable=False)
    is_enabled = Column(Boolean, default=True)
    supports_customer_checkout = Column(Boolean, default=False)
    supports_payouts = Column(Boolean, default=False)
    mode = Column(String(20), nullable=False, default="test")
    public_key = Column(String(500), nullable=True)
    secret_key = Column(EncryptedString(1000), nullable=True)
    webhook_secret = Column(EncryptedString(1000), nullable=True)
    merchant_id = Column(String(255), nullable=True)
    api_base_url = Column(String(500), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    test_url = Column(String(500), nullable=True)
    supported_currencies_json = Column(Text, nullable=True)
    extra_config_json = Column(EncryptedString(), nullable=True)
    notes = Column(Text, nullable=True)
    fee_percent = Column(Numeric(8, 4), nullable=False, default=0)
    fixed_fee_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payout_fee_percent = Column(Numeric(8, 4), nullable=False, default=0)
    payout_fixed_fee_amount = Column(Numeric(12, 2), nullable=False, default=0)
    pass_fee_to_customer = Column(Boolean, default=False)
    settlement_cycle = Column(String(20), nullable=False, default="weekly")
    test_status = Column(String(20), nullable=False, default="untested")
    test_message = Column(String(500), nullable=True)
    last_tested_at = Column(DateTime, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])


class PaymentProviderConfig(Base):
    """Runtime-managed checkout provider visibility for online payments."""
    __tablename__ = "payment_provider_configs"
    __table_args__ = (
        CheckConstraint(
            "online_provider IN ('stripe', 'tap', 'both')",
            name="ck_payment_provider_configs_online_provider_valid",
        ),
    )
    id = Column(Integer, primary_key=True, index=True)
    online_provider = Column(String(20), default="stripe", nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])

class EmailProviderConfig(Base):
    """Runtime-managed email transport and sender identity configuration."""
    __tablename__ = "email_provider_configs"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('environment', 'resend', 'smtp', 'disabled')",
            name="ck_email_provider_configs_provider_valid",
        ),
    )
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(30), default="environment", nullable=False)
    resend_api_key = Column(EncryptedString(500), nullable=True)
    resend_webhook_secret = Column(EncryptedString(500), nullable=True)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587, nullable=False)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(EncryptedString(500), nullable=True)
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)
    smtp_timeout_seconds = Column(Integer, default=15, nullable=False)
    email_from_default = Column(String(255), nullable=True)
    email_from_promotional = Column(String(255), nullable=True)
    email_from_transactional = Column(String(255), nullable=True)
    email_from_notification = Column(String(255), nullable=True)
    email_from_alert = Column(String(255), nullable=True)
    email_from_verification = Column(String(255), nullable=True)
    email_from_login_verification = Column(String(255), nullable=True)
    email_from_password_reset = Column(String(255), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])


class EmailSuppression(Base):
    """Normalized suppression list used to block future outbound sends."""
    __tablename__ = "email_suppressions"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive')", name="ck_email_suppressions_status_valid"),
    )
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    reason = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False, default="system")
    provider = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    notes = Column(Text, nullable=True)
    first_event_id = Column(String(255), nullable=True)
    last_event_id = Column(String(255), nullable=True)
    suppressed_at = Column(DateTime, default=_utcnow)
    last_event_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class EmailDeliveryEvent(Base):
    """Outbound send attempts and provider feedback captured for support and analytics."""
    __tablename__ = "email_delivery_events"
    __table_args__ = (
        Index("ix_email_delivery_events_recipient_created", "recipient_email", "created_at"),
        Index("ix_email_delivery_events_processor_event", "processor", "event_id"),
        Index("ix_email_delivery_events_event_type_created", "event_type", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), nullable=True, index=True)
    processor = Column(String(50), nullable=False)
    message_id = Column(String(255), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=True)
    purpose = Column(String(50), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    source = Column(String(50), nullable=False, default="application")
    campaign_recipient_id = Column(Integer, ForeignKey("campaign_recipients.id"), nullable=True)
    payload = Column(Text, nullable=True)
    occurred_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    campaign_recipient = relationship("CampaignRecipient")

class NewsletterSubscriber(Base):
    """Email newsletter subscribers with opt-in tracking."""
    __tablename__ = "newsletter_subscribers"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    source = Column(String(50), default="website")  # website | import | referral
    preferences = Column(Text, nullable=True)       # JSON: {"categories": ["fashion", "electronics"], "frequency": "weekly"}
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=_utcnow)
    unsubscribed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class EmailTemplate(Base):
    """Reusable email templates for campaigns and automated emails."""
    __tablename__ = "email_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)     # Plain text version
    template_type = Column(String(50), default="marketing")  # marketing | transactional | promotional
    variables = Column(Text, nullable=True)        # JSON: ["{{first_name}}", "{{unsubscribe_url}}"]
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    creator = relationship("User")


class EmailCampaign(Base):
    """Email marketing campaigns with scheduling and tracking."""
    __tablename__ = "email_campaigns"
    __table_args__ = (
        Index("ix_email_campaigns_status_send_at", "status", "send_at"),
        Index("ix_email_campaigns_created_at", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    status = Column(String(30), default="draft")   # draft | scheduled | sending | sent | cancelled
    send_at = Column(DateTime, nullable=True)      # When to send (NULL = send immediately)
    sent_at = Column(DateTime, nullable=True)      # When actually sent
    target_audience = Column(String(50), default="all")  # all | subscribers | customers | suppliers
    recipient_count = Column(Integer, default=0)   # Total recipients targeted
    sent_count = Column(Integer, default=0)        # Successfully sent
    opened_count = Column(Integer, default=0)      # Unique opens
    clicked_count = Column(Integer, default=0)     # Unique clicks
    bounced_count = Column(Integer, default=0)     # Bounces
    unsubscribed_count = Column(Integer, default=0) # Unsubscribes from this campaign
    # A/B subject-line testing
    subject_b = Column(String(500), nullable=True)          # Variant B subject (None = no A/B test)
    ab_test_enabled = Column(Boolean, default=False)        # When True, split 50/50 across subject and subject_b
    ab_winner_variant = Column(String(1), nullable=True)    # "A" or "B" — set after analysis
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    template = relationship("EmailTemplate")
    creator = relationship("User")
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")


class CampaignRecipient(Base):
    """Individual recipients of an email campaign with tracking."""
    __tablename__ = "campaign_recipients"
    __table_args__ = (
        Index("ix_campaign_recipients_campaign_email", "campaign_id", "email"),
        Index("ix_campaign_recipients_campaign_status", "campaign_id", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("email_campaigns.id"), index=True)
    email = Column(String, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # If recipient is a registered user
    status = Column(String(20), default="pending")  # pending | sent | delivered | opened | clicked | bounced | unsubscribed
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    unsubscribed_at = Column(DateTime, nullable=True)
    tracking_id = Column(String, unique=True, index=True)  # UUID for open/click tracking
    created_at = Column(DateTime, default=_utcnow)

    campaign = relationship("EmailCampaign", back_populates="recipients")
    user = relationship("User")


# ── Logistics ─────────────────────────────────────────────────────────────────

class ShippingCarrier(Base):
    """Shipping carrier definitions — global defaults or supplier-specific."""
    __tablename__ = "shipping_carriers"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL = platform default
    name = Column(String(100), nullable=False)            # "DHL Express", "Aramex", "FedEx"
    code = Column(String(30), nullable=False)             # "dhl", "aramex", "fedex"
    tracking_url = Column(String(500), nullable=True)     # URL template with {number} placeholder
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ShippingZone(Base):
    """Supplier-defined shipping zones with rates per destination region."""
    __tablename__ = "shipping_zones"
    __table_args__ = (
        Index("ix_shipping_zones_supplier_active", "supplier_id", "is_active"),
        CheckConstraint("base_price >= 0", name="ck_shipping_zones_base_price_nonnegative"),
        CheckConstraint("price_per_kg >= 0", name="ck_shipping_zones_price_per_kg_nonnegative"),
        CheckConstraint(
            "free_shipping_above IS NULL OR free_shipping_above >= 0",
            name="ck_shipping_zones_free_shipping_above_nonnegative",
        ),
        CheckConstraint(
            "estimated_days_min IS NULL OR estimated_days_min >= 0",
            name="ck_shipping_zones_estimated_days_min_nonnegative",
        ),
        CheckConstraint(
            "estimated_days_max IS NULL OR estimated_days_max >= 0",
            name="ck_shipping_zones_estimated_days_max_nonnegative",
        ),
        CheckConstraint(
            "estimated_days_min IS NULL OR estimated_days_max IS NULL OR estimated_days_min <= estimated_days_max",
            name="ck_shipping_zones_estimated_days_min_le_max",
        ),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)            # "UAE", "GCC", "Europe", "Worldwide"
    countries = Column(Text, nullable=False)              # JSON list of ISO country codes
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id"), nullable=True)
    carrier_name = Column(String(100), nullable=True)     # free-text if no carrier record
    base_price = Column(Float, nullable=False, default=0.0)
    price_per_kg = Column(Float, nullable=False, default=0.0)
    free_shipping_above = Column(Float, nullable=True)   # free shipping when order value exceeds this
    estimated_days_min = Column(Integer, nullable=True)
    estimated_days_max = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User")
    carrier = relationship("ShippingCarrier")


class Shipment(Base):
    """Tracks fulfilment for an individual order — one per order-supplier pair."""
    __tablename__ = "shipments"
    __table_args__ = (
        Index("ix_shipments_supplier_status", "supplier_id", "status"),
        Index("ix_shipments_order_supplier", "order_id", "supplier_id"),
        Index("ix_shipments_partner_status", "assigned_partner_id", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=True, index=True)
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id"), nullable=True)
    carrier_name = Column(String(100), nullable=True)    # free-text carrier name
    tracking_number = Column(String(200), nullable=True, index=True)
    status = Column(String(50), default="pending", index=True)
    # pending | processing | shipped | in_transit | delivered | failed | returned
    distribution_channel = Column(String(100), nullable=True)  # e.g. air_freight | ground | sea_freight | local_courier
    current_hub = Column(String(200), nullable=True)           # location-wise checkpoint / warehouse / city
    scan_code = Column(String(120), nullable=True, index=True) # canonical QR/barcode payload for this shipment
    accepted_vehicle_rule_id = Column(Integer, ForeignKey("logistics_vehicle_rules.id"), nullable=True)
    accepted_vehicle_type = Column(String(50), nullable=True)
    accepted_vehicle_multiplier = Column(Numeric(8, 4), nullable=True)
    accepted_vehicle_selected_at = Column(DateTime, nullable=True)
    package_count = Column(Integer, nullable=True)
    package_weight_kg = Column(Float, nullable=True)
    package_dimensions = Column(String(120), nullable=True)
    packaged_at = Column(DateTime, nullable=True)
    packaged_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    packaging_notes = Column(Text, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    delivery_signature_name = Column(String(200), nullable=True)
    delivery_signature_data_url = Column(Text, nullable=True)
    delivery_signature_captured_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    order = relationship("Order")
    supplier = relationship("User", foreign_keys=[supplier_id])
    assigned_partner = relationship("LogisticsPartner", foreign_keys=[assigned_partner_id])
    accepted_vehicle_rule = relationship("LogisticsVehicleRule", foreign_keys=[accepted_vehicle_rule_id])
    carrier = relationship("ShippingCarrier")
    packaged_by = relationship("User", foreign_keys=[packaged_by_user_id])


class ShipmentEvent(Base):
    """Immutable scan/event trail for each shipment across the supply chain."""
    __tablename__ = "shipment_events"
    __table_args__ = (
        Index("ix_shipment_events_shipment_created", "shipment_id", "created_at"),
        Index("ix_shipment_events_order_created", "order_id", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_role = Column(String(50), nullable=False, default="system")
    event_type = Column(String(80), nullable=False, index=True)
    status = Column(String(50), nullable=True, index=True)
    status_after = Column(String(50), nullable=True, index=True)
    distribution_channel = Column(String(100), nullable=True)
    location = Column(EncryptedString(255), nullable=True)
    latitude = Column(Float, nullable=True)   # GPS latitude for map widget
    longitude = Column(Float, nullable=True)  # GPS longitude for map widget
    scan_code = Column(String(120), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)

    shipment = relationship("Shipment")
    order = relationship("Order")
    supplier = relationship("User", foreign_keys=[supplier_id])
    actor = relationship("User", foreign_keys=[actor_user_id])
    creator = relationship("User", foreign_keys=[created_by])


class ShipmentConfirmation(Base):
    """Pending pickup/delivery confirmation requests awaiting supplier or customer approval."""
    __tablename__ = "shipment_confirmations"
    __table_args__ = (
        Index("ix_shipment_confirmations_shipment_created", "shipment_id", "created_at"),
        Index("ix_shipment_confirmations_target_status", "target_user_id", "status"),
        Index("ix_shipment_confirmations_order_status", "order_id", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    requester_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    requester_role = Column(String(50), nullable=False, default="logistics_partner")
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_role = Column(String(50), nullable=False)
    confirmation_type = Column(String(30), nullable=False, index=True)  # pickup | delivery
    status = Column(String(30), nullable=False, default="pending", index=True)  # pending | accepted | rejected | cancelled
    requested_status = Column(String(50), nullable=False)
    requested_event_type = Column(String(80), nullable=False)
    current_hub = Column(EncryptedString(200), nullable=True)
    tracking_number = Column(String(200), nullable=True)
    delivery_signature_name = Column(String(200), nullable=True)
    delivery_signature_data_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    response_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)
    responded_at = Column(DateTime, nullable=True)

    shipment = relationship("Shipment")
    order = relationship("Order")
    supplier = relationship("User", foreign_keys=[supplier_id])
    requester = relationship("User", foreign_keys=[requester_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])


class CartItem(Base):
    """Server-side cart for logged-in users — enables cross-device cart sync."""
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", "selected_size", "selected_color", name="uq_cart_user_product_variant"),
        Index("ix_cart_items_user_updated", "user_id", "updated_at"),
        CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    quantity = Column(Integer, nullable=False, default=1)
    selected_size = Column(String(100), nullable=False, default="")
    selected_color = Column(String(50), nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    user = relationship("User")
    product = relationship("Product")


class PushNotificationToken(Base):
    """Mobile push notification tokens for FCM/APNs/Expo delivery."""
    __tablename__ = "push_notification_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "token", name="uq_push_token_user"),
        Index("ix_push_tokens_user", "user_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String(512), nullable=False, index=True)
    platform = Column(String(20), nullable=False, default="expo")  # expo, fcm, apns
    device_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User")


class RevokedToken(Base):
    """Blacklisted JWT tokens for secure logout. Cleaned up by a periodic task."""
    __tablename__ = "revoked_tokens"
    __table_args__ = (
        Index("ix_revoked_tokens_jti", "jti"),
        Index("ix_revoked_tokens_expires", "expires_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), nullable=False, unique=True)               # JWT ID claim; indexed via __table_args__
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class Banner(Base):
    """Promotional banner slots — replaces the file-based banner.json."""
    __tablename__ = "banners"
    __table_args__ = (
        Index("ix_banners_active_type", "is_active", "banner_type"),
        Index("ix_banners_public_feed", "is_active", "banner_type", "sort_order", "starts_at", "ends_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    cta_label = Column(String(100), nullable=True)       # e.g. "Shop Now"
    cta_url = Column(String(500), nullable=True)         # internal path or external URL
    banner_type = Column(String(50), default="hero")     # hero | seasonal | promotional | flash
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    starts_at = Column(DateTime, nullable=True)          # null = always show when active
    ends_at = Column(DateTime, nullable=True)
    # ── Admin appearance controls (all optional — fallbacks applied in frontend) ──
    bg_color = Column(String(20), nullable=True)         # e.g. "#32CD32" — overrides banner_type default
    text_color = Column(String(20), nullable=True)       # title text colour, default "#ffffff"
    subtitle_color = Column(String(20), nullable=True)   # subtitle colour, default "rgba(255,255,255,0.88)"
    btn_bg_color = Column(String(20), nullable=True)     # CTA button background
    btn_text_color = Column(String(20), nullable=True)   # CTA button text colour
    badge_text = Column(String(100), nullable=True)      # badge label e.g. "Flash Sale"
    badge_color = Column(String(20), nullable=True)      # badge background colour
    effect = Column(String(50), nullable=True)           # web canvas effect: balloons|aurora|ramadan|eid|poppers
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    creator = relationship("User", foreign_keys=[created_by])


# ── Supplier Documents (Papers Verification) ──────────────────────────────────

class SupplierDocument(Base):
    """Documents submitted by suppliers for KYC/papers verification.
    Admins review and update status; documents can expire and be re-submitted."""
    __tablename__ = "supplier_documents"
    __table_args__ = (
        Index("ix_supplier_docs_supplier_status", "supplier_id", "status"),
        Index("ix_supplier_docs_doc_type", "document_type", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_type = Column(String(80), nullable=False)
    # trade_license | vat_certificate | passport | company_registration | bank_statement | other
    document_name = Column(String(200), nullable=False)
    file_url = Column(String(500), nullable=False)
    status = Column(String(30), default="pending", index=True)
    # pending | under_review | approved | rejected | expired
    expires_at = Column(DateTime, nullable=True)          # when this doc needs renewal
    review_note = Column(Text, nullable=True)             # admin feedback
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# ── Invoices (Supply Chain) ────────────────────────────────────────────────────

class Invoice(Base):
    """Supply chain invoice linking supplier → logistics → customer receipt."""
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_order_supplier", "order_id", "supplier_id"),
        Index("ix_invoices_status_created", "status", "created_at"),
        CheckConstraint("total_amount >= 0", name="ck_invoices_total_nonneg"),
    )
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True, index=True)
    # Status: draft | issued | in_transit | delivered | cancelled
    status = Column(String(30), default="draft", index=True)
    invoice_type = Column(String(30), default="sale")  # sale | return | credit_note
    subtotal = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    shipping_amount = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="AED")
    issued_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    # Supply chain phase timestamps
    picked_at = Column(DateTime, nullable=True)          # picked from supplier
    dispatched_at = Column(DateTime, nullable=True)      # handed to logistics
    delivered_at = Column(DateTime, nullable=True)       # received by customer
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    order = relationship("Order")
    supplier = relationship("User", foreign_keys=[supplier_id])
    shipment = relationship("Shipment")
    items = relationship("InvoiceItem", back_populates="invoice")


class InvoiceItem(Base):
    """Line items on an invoice — mirrors order items with invoice-specific pricing."""
    __tablename__ = "invoice_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_invoice_items_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_invoice_items_price_nonneg"),
    )
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_rate = Column(Float, default=0.0)               # e.g. 5.0 for 5% VAT
    line_total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")


# ── Product Verification (Spec Check) ─────────────────────────────────────────

class ProductVerification(Base):
    """Records spec verification checks for products at key supply chain points."""
    __tablename__ = "product_verifications"
    __table_args__ = (
        Index("ix_product_verify_product_type", "product_id", "verification_type"),
        Index("ix_product_verify_order", "order_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    # supplier_dispatch | logistics_receipt | customer_receipt
    verification_type = Column(String(50), nullable=False, index=True)
    # passed | failed | partial
    result = Column(String(20), nullable=False, default="passed")
    expected_specs = Column(Text, nullable=True)         # JSON: expected attributes
    actual_specs = Column(Text, nullable=True)           # JSON: scanned/checked attributes
    discrepancies = Column(Text, nullable=True)          # JSON: list of spec mismatches
    scan_code = Column(String(200), nullable=True, index=True)
    image_urls = Column(Text, nullable=True)             # JSON: photos taken at verification
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    product = relationship("Product")
    order = relationship("Order")
    verifier = relationship("User")


# ── Logistics Partners ─────────────────────────────────────────────────────────

class LogisticsPartner(Base):
    """External logistics partner companies with their own dashboard access."""
    __tablename__ = "logistics_partners"
    __table_args__ = (
        Index("ix_logistics_partners_status", "status"),
        Index("ix_logistics_partners_verification_status", "verification_status"),
        Index("ix_logistics_partners_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    contact_name = Column(String(200), nullable=True)
    contact_email = Column(EncryptedString(255), nullable=True)
    contact_phone = Column(EncryptedString(80), nullable=True)
    website = Column(String(300), nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    # Operational details
    coverage_regions = Column(Text, nullable=True)       # JSON list of country/region codes
    service_types = Column(Text, nullable=True)          # JSON: ["air","ground","sea"]
    business_type = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    postal_code = Column(String(40), nullable=True)
    tax_id = Column(String(120), nullable=True)
    bank_details_json = Column(EncryptedString(), nullable=True)
    bio = Column(Text, nullable=True)
    about_us = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    social_links = Column(Text, nullable=True)           # JSON object
    is_terms_accepted = Column(Boolean, default=False)
    terms_version = Column(String(30), nullable=True)
    terms_accepted_at = Column(DateTime, nullable=True)
    verification_status = Column(String(30), default="pending")  # pending | under_review | approved | rejected
    verification_note = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(30), default="pending_onboarding")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    api_key_hash = Column(String(200), nullable=True)
    notes = Column(EncryptedString(), nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[verified_by])
    country = relationship("CountryConfig", foreign_keys=[country_code])
    payouts = relationship("LogisticsPartnerPayout", back_populates="partner")
    service_areas = relationship("LogisticsPartnerServiceArea", back_populates="partner", cascade="all, delete-orphan")
    pricing_profiles = relationship("LogisticsPricingProfile", back_populates="partner", cascade="all, delete-orphan")
    category_pricing_rules = relationship("LogisticsCategoryPricingRule", back_populates="partner", cascade="all, delete-orphan")
    vehicle_rules = relationship("LogisticsVehicleRule", back_populates="partner", cascade="all, delete-orphan")
    documents = relationship("LogisticsPartnerDocument", back_populates="partner", cascade="all, delete-orphan")


class LogisticsPartnerDocument(Base):
    """KYC and business documents submitted by logistics partners for admin verification."""
    __tablename__ = "logistics_partner_documents"
    __table_args__ = (
        Index("ix_lp_docs_partner_status", "partner_id", "status"),
        Index("ix_lp_docs_doc_type", "document_type", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    document_type = Column(String(80), nullable=False)
    # business_license | trade_license | tax_certificate | national_id | bank_statement | insurance | other
    document_name = Column(String(200), nullable=False)
    file_url = Column(String(500), nullable=False)
    status = Column(String(30), default="pending", index=True)
    # pending | under_review | approved | rejected | expired
    expires_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="documents")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class LogisticsPartnerServiceArea(Base):
    """Admin-reviewed destination coverage and delivery charges for logistics partners."""
    __tablename__ = "logistics_partner_service_areas"
    __table_args__ = (
        Index("ix_lp_service_areas_partner_status", "partner_id", "approval_status"),
        Index("ix_lp_service_areas_destination", "country_code", "city_name", "approval_status"),
        CheckConstraint("charge_amount >= 0", name="ck_lp_service_areas_charge_nonnegative"),
        CheckConstraint(
            "minimum_charge IS NULL OR minimum_charge >= 0",
            name="ck_lp_service_areas_minimum_charge_nonnegative",
        ),
        CheckConstraint(
            "per_kg_rate IS NULL OR per_kg_rate >= 0",
            name="ck_lp_service_areas_per_kg_nonnegative",
        ),
        CheckConstraint(
            "fuel_multiplier IS NULL OR fuel_multiplier > 0",
            name="ck_lp_service_areas_fuel_multiplier_positive",
        ),
        CheckConstraint(
            "per_km_rate IS NULL OR per_km_rate >= 0",
            name="ck_lp_service_areas_per_km_nonnegative",
        ),
        CheckConstraint(
            "delivery_days_min IS NULL OR delivery_days_min >= 0",

            name="ck_lp_service_areas_days_min_nonnegative",
        ),
        CheckConstraint(
            "delivery_days_max IS NULL OR delivery_days_max >= 0",
            name="ck_lp_service_areas_days_max_nonnegative",
        ),
        CheckConstraint(
            "delivery_days_min IS NULL OR delivery_days_max IS NULL OR delivery_days_min <= delivery_days_max",
            name="ck_lp_service_areas_days_min_le_max",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    country_code = Column(String(10), nullable=False, index=True)
    country_name = Column(String(120), nullable=False)
    origin_city = Column(String(120), nullable=True, index=True)  # Supplier pickup/origin city; NULL = any origin
    city_name = Column(String(120), nullable=True, index=True)    # Customer delivery destination city
    zone_label = Column(String(120), nullable=True)
    charge_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    minimum_charge = Column(Numeric(12, 2), nullable=True)
    per_kg_rate = Column(Numeric(12, 2), nullable=True)
    per_km_rate = Column(Numeric(12, 4), nullable=True)   # Distance-based fee per km
    fuel_multiplier = Column(Numeric(8, 4), nullable=True, default=1.0)
    pickup_charge = Column(Numeric(12, 2), nullable=True)    # Optional pickup fee split
    dropoff_charge = Column(Numeric(12, 2), nullable=True)   # Optional dropoff fee split
    currency = Column(String(10), nullable=False, default="AED")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    delivery_days_min = Column(Integer, nullable=True)
    delivery_days_max = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    approval_status = Column(String(30), nullable=False, default="pending")  # pending | approved | rejected
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="service_areas")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    pricing_profiles = relationship("LogisticsPricingProfile", back_populates="service_area", cascade="all, delete-orphan")
    category_pricing_rules = relationship("LogisticsCategoryPricingRule", back_populates="service_area", cascade="all, delete-orphan")
    vehicle_rules = relationship("LogisticsVehicleRule", back_populates="service_area", cascade="all, delete-orphan")


class LogisticsPricingProfile(Base):
    """Admin-reviewed pricing defaults and overrides for a partner or service area."""
    __tablename__ = "logistics_pricing_profiles"
    __table_args__ = (
        Index("ix_lp_pricing_profiles_partner_status", "partner_id", "approval_status"),
        Index("ix_lp_pricing_profiles_service_area", "service_area_id", "approval_status"),
        CheckConstraint(
            "base_in_city_fee IS NULL OR base_in_city_fee >= 0",
            name="ck_lp_pricing_profiles_base_in_city_nonnegative",
        ),
        CheckConstraint(
            "base_inter_city_fee IS NULL OR base_inter_city_fee >= 0",
            name="ck_lp_pricing_profiles_base_inter_city_nonnegative",
        ),
        CheckConstraint(
            "per_km_rate IS NULL OR per_km_rate >= 0",
            name="ck_lp_pricing_profiles_per_km_nonnegative",
        ),
        CheckConstraint(
            "per_kg_rate IS NULL OR per_kg_rate >= 0",
            name="ck_lp_pricing_profiles_per_kg_nonnegative",
        ),
        CheckConstraint(
            "minimum_charge IS NULL OR minimum_charge >= 0",
            name="ck_lp_pricing_profiles_minimum_charge_nonnegative",
        ),
        CheckConstraint(
            "maximum_charge IS NULL OR maximum_charge >= 0",
            name="ck_lp_pricing_profiles_maximum_charge_nonnegative",
        ),
        CheckConstraint(
            "fuel_multiplier IS NULL OR fuel_multiplier > 0",
            name="ck_lp_pricing_profiles_fuel_multiplier_positive",
        ),
        CheckConstraint(
            "bulk_discount_threshold_kg IS NULL OR bulk_discount_threshold_kg >= 0",
            name="ck_lp_pricing_profiles_bulk_threshold_nonnegative",
        ),
        CheckConstraint(
            "bulk_discount_percent IS NULL OR (bulk_discount_percent >= 0 AND bulk_discount_percent <= 100)",
            name="ck_lp_pricing_profiles_bulk_percent_range",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    service_area_id = Column(Integer, ForeignKey("logistics_partner_service_areas.id"), nullable=True, index=True)
    profile_name = Column(String(120), nullable=True)
    base_in_city_fee = Column(Numeric(12, 2), nullable=True)
    base_inter_city_fee = Column(Numeric(12, 2), nullable=True)
    per_km_rate = Column(Numeric(12, 4), nullable=True)
    per_kg_rate = Column(Numeric(12, 2), nullable=True)
    minimum_charge = Column(Numeric(12, 2), nullable=True)
    maximum_charge = Column(Numeric(12, 2), nullable=True)
    fuel_multiplier = Column(Numeric(8, 4), nullable=True, default=1.0)
    bulk_discount_threshold_kg = Column(Numeric(12, 2), nullable=True)
    bulk_discount_percent = Column(Numeric(5, 2), nullable=True)
    currency = Column(String(10), nullable=False, default="AED")
    is_active = Column(Boolean, default=True)
    approval_status = Column(String(30), nullable=False, default="pending")
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="pricing_profiles")
    service_area = relationship("LogisticsPartnerServiceArea", back_populates="pricing_profiles")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class LogisticsCategoryPricingRule(Base):
    """Admin-reviewed category-based charge adjustments for logistics pricing."""
    __tablename__ = "logistics_category_pricing_rules"
    __table_args__ = (
        Index("ix_lp_category_rules_partner_status", "partner_id", "approval_status"),
        Index("ix_lp_category_rules_service_area", "service_area_id", "approval_status"),
        Index("ix_lp_category_rules_category", "category_name", "approval_status"),
        CheckConstraint(
            "flat_fee_override IS NULL OR flat_fee_override >= 0",
            name="ck_lp_category_rules_flat_fee_nonnegative",
        ),
        CheckConstraint(
            "special_handling_fee IS NULL OR special_handling_fee >= 0",
            name="ck_lp_category_rules_special_handling_nonnegative",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    service_area_id = Column(Integer, ForeignKey("logistics_partner_service_areas.id"), nullable=True, index=True)
    category_name = Column(String(120), nullable=False, index=True)
    flat_fee_override = Column(Numeric(12, 2), nullable=True)
    special_handling_fee = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), nullable=False, default="AED")
    is_active = Column(Boolean, default=True)
    approval_status = Column(String(30), nullable=False, default="pending")
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="category_pricing_rules")
    service_area = relationship("LogisticsPartnerServiceArea", back_populates="category_pricing_rules")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class LogisticsVehicleRule(Base):
    """Admin-reviewed vehicle selection rules for route-aware logistics pricing."""
    __tablename__ = "logistics_vehicle_rules"
    __table_args__ = (
        Index("ix_lp_vehicle_rules_partner_status", "partner_id", "approval_status"),
        Index("ix_lp_vehicle_rules_service_area", "service_area_id", "approval_status"),
        Index("ix_lp_vehicle_rules_route_scope", "route_scope", "approval_status"),
        CheckConstraint(
            "max_weight_kg IS NULL OR max_weight_kg >= 0",
            name="ck_lp_vehicle_rules_max_weight_nonnegative",
        ),
        CheckConstraint(
            "max_volume_cm3 IS NULL OR max_volume_cm3 >= 0",
            name="ck_lp_vehicle_rules_max_volume_nonnegative",
        ),
        CheckConstraint(
            "cost_multiplier > 0",
            name="ck_lp_vehicle_rules_cost_multiplier_positive",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    service_area_id = Column(Integer, ForeignKey("logistics_partner_service_areas.id"), nullable=True, index=True)
    route_scope = Column(String(20), nullable=False, default="any")  # any | in_city | inter_city
    vehicle_type = Column(String(50), nullable=False)
    max_weight_kg = Column(Numeric(12, 2), nullable=True)
    max_volume_cm3 = Column(Numeric(14, 2), nullable=True)
    cost_multiplier = Column(Numeric(8, 4), nullable=False, default=1.0)
    priority_rank = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, default=True)
    approval_status = Column(String(30), nullable=False, default="pending")
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="vehicle_rules")
    service_area = relationship("LogisticsPartnerServiceArea", back_populates="vehicle_rules")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class OrderLogisticsAllocation(Base):
    """Immutable per-supplier shipping allocation captured at order time."""
    __tablename__ = "order_logistics_allocations"
    __table_args__ = (
        UniqueConstraint("order_id", "supplier_id", name="uq_order_logistics_allocations_order_supplier"),
        Index("ix_order_logistics_allocations_order", "order_id"),
        Index("ix_order_logistics_allocations_partner", "partner_id"),
        CheckConstraint("shipping_amount >= 0", name="ck_order_logistics_allocations_shipping_nonnegative"),
        CheckConstraint("pickup_charge >= 0", name="ck_order_logistics_allocations_pickup_nonnegative"),
        CheckConstraint("dropoff_charge >= 0", name="ck_order_logistics_allocations_dropoff_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=True, index=True)
    service_area_id = Column(Integer, ForeignKey("logistics_partner_service_areas.id"), nullable=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True, index=True)

    allocation_source = Column(String(40), nullable=False, default="fallback")
    partner_name_snapshot = Column(String(200), nullable=True)
    partner_code_snapshot = Column(String(50), nullable=True)
    service_area_label_snapshot = Column(String(120), nullable=True)
    destination_country = Column(String(120), nullable=True)
    destination_city = Column(String(120), nullable=True)

    shipping_amount = Column(Numeric(12, 2), nullable=False, default=0)
    pickup_charge = Column(Numeric(12, 2), nullable=False, default=0)
    dropoff_charge = Column(Numeric(12, 2), nullable=False, default=0)
    accepted_vehicle_rule_id = Column(Integer, ForeignKey("logistics_vehicle_rules.id"), nullable=True, index=True)
    accepted_vehicle_type = Column(String(50), nullable=True)
    accepted_vehicle_multiplier = Column(Numeric(8, 4), nullable=True)
    accepted_shipping_amount = Column(Numeric(12, 2), nullable=True)
    accepted_pickup_charge = Column(Numeric(12, 2), nullable=True)
    accepted_dropoff_charge = Column(Numeric(12, 2), nullable=True)
    estimated_delivery_min = Column(Integer, nullable=True)
    estimated_delivery_max = Column(Integer, nullable=True)
    currency = Column(String(10), nullable=False, default="AED")
    pricing_breakdown_json = Column(Text, nullable=True)  # JSON snapshot of pricing breakdown at order time
    accepted_pricing_breakdown_json = Column(Text, nullable=True)
    accepted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    order = relationship("Order", back_populates="logistics_allocations")
    supplier = relationship("User", foreign_keys=[supplier_id])
    partner = relationship("LogisticsPartner", foreign_keys=[partner_id])
    service_area = relationship("LogisticsPartnerServiceArea", foreign_keys=[service_area_id])
    shipment = relationship("Shipment", foreign_keys=[shipment_id])
    accepted_vehicle_rule = relationship("LogisticsVehicleRule", foreign_keys=[accepted_vehicle_rule_id])


class CityDistanceMatrix(Base):
    """Admin-managed lookup table for straight-line distances between city pairs.

    Used by the logistics pricing engine to compute per-km delivery fees.
    The (origin, destination) pair is unique and case-insensitively normalised
    at query time via ``normalize_city_name`` in the pricing service.
    """
    __tablename__ = "city_distance_matrix"
    __table_args__ = (
        UniqueConstraint(
            "origin_country_code",
            "origin_city_name",
            "destination_country_code",
            "destination_city_name",
            name="uq_city_distance_matrix_route",
        ),
        Index("ix_city_distance_matrix_origin", "origin_country_code", "origin_city_name"),
        Index("ix_city_distance_matrix_dest", "destination_country_code", "destination_city_name"),
        CheckConstraint("distance_km > 0", name="ck_city_distance_km_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    origin_country_code = Column(String(10), nullable=False)
    origin_city_name = Column(String(120), nullable=False)
    destination_country_code = Column(String(10), nullable=False)
    destination_city_name = Column(String(120), nullable=False)
    distance_km = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


# ── Country Control Plane ─────────────────────────────────────────────────────

class CountryConfig(Base):
    """Admin-managed country configuration for tax, logistics, and payments."""

    __tablename__ = "country_configs"
    __table_args__ = (
        UniqueConstraint("code", name="uq_country_configs_code"),
        Index("ix_country_configs_active_code", "is_active", "code"),
        CheckConstraint("tax_rate >= 0 AND tax_rate <= 1", name="ck_country_configs_tax_rate_valid"),
        CheckConstraint("base_rate IS NULL OR base_rate >= 0", name="ck_country_configs_base_rate_nonneg"),
        CheckConstraint("per_km_rate IS NULL OR per_km_rate >= 0", name="ck_country_configs_per_km_nonneg"),
        CheckConstraint("minimum_charge IS NULL OR minimum_charge >= 0", name="ck_country_configs_min_charge_nonneg"),
        CheckConstraint("weight_surcharge_rate IS NULL OR weight_surcharge_rate >= 0", name="ck_country_configs_weight_rate_nonneg"),
        CheckConstraint(
            "weight_surcharge_threshold_kg IS NULL OR weight_surcharge_threshold_kg >= 0",
            name="ck_country_configs_weight_threshold_nonneg",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    timezone = Column(String(60), nullable=False, default="UTC")
    tax_type = Column(String(20), nullable=False, default="VAT")
    tax_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    tax_name = Column(String(50), nullable=False, default="Tax")
    tax_inclusive = Column(Boolean, nullable=False, default=False)
    tax_exempt_categories_json = Column(Text, nullable=True)
    tax_reduced_rates_json = Column(Text, nullable=True)
    logistics_model = Column(String(20), nullable=False, default="fixed")
    default_vehicle_type = Column(String(30), nullable=True)
    base_rate = Column(Numeric(12, 2), nullable=True)
    per_km_rate = Column(Numeric(12, 4), nullable=True)
    minimum_charge = Column(Numeric(12, 2), nullable=True)
    weight_surcharge_rate = Column(Numeric(12, 2), nullable=True)
    weight_surcharge_threshold_kg = Column(Numeric(8, 2), nullable=True)
    payment_methods_json = Column(Text, nullable=True)
    # Extended GCC country configuration fields
    currency_symbol = Column(String(10), nullable=True)
    phone_code = Column(String(10), nullable=True)
    language = Column(String(10), nullable=True, default="en")
    # JSON config blobs for dynamic per-country settings
    payment_gateways_json = Column(Text, nullable=True)       # [{gateway_id, name, type, enabled, credential_ref, fee_pct, fee_fixed, ...}]
    logistics_providers_json = Column(Text, nullable=True)    # [{provider_id, name, enabled, sla_standard, sla_express, base_rate, ...}]
    legal_rules_json = Column(Text, nullable=True)            # {min_age, return_window_days, max_returns, product_restrictions, ...}
    regions_json = Column(Text, nullable=True)                # [{region_id, name, cities:[...]}]
    supplier_requirements_json = Column(Text, nullable=True)  # {kyc_level, required_documents, approval_required}
    date_format = Column(String(20), nullable=True, default="DD/MM/YYYY")
    address_format_json = Column(Text, nullable=True)              # {line1, line2, city, state, zip, country} or custom template
    product_restrictions_json = Column(Text, nullable=True)        # ["electronics", "perfumes", ...] — restricted category slugs
    payout_settings_json = Column(Text, nullable=True)        # {minimum_payout_amount, payout_schedule, payout_day, batch_size, currency}
    commission_tiers_json = Column(Text, nullable=True)       # [{min_order_value, max_order_value, commission_percentage, fixed_fee}]
    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, default=False)
    # Macro indicators (populated by auto-populate from World Bank)
    population = Column(Integer, nullable=True)
    internet_penetration_pct = Column(Numeric(5, 2), nullable=True)
    gdp_per_capita_usd = Column(Numeric(12, 2), nullable=True)
    urbanization_pct = Column(Numeric(5, 2), nullable=True)
    mobile_subs_per_100 = Column(Numeric(5, 2), nullable=True)
    public_holidays_json = Column(Text, nullable=True)
    macro_indicators_json = Column(Text, nullable=True)
    # ── Phase 1: Heuristic fields ──────────────────────────────────────────────
    economic_tier = Column(String(20), nullable=True)
    fraud_risk_tier = Column(String(20), nullable=True)
    gateway_ranking_score = Column(Numeric(5, 2), nullable=True)
    fraud_risk_score = Column(Numeric(5, 2), nullable=True)
    logistics_efficiency_score = Column(Numeric(5, 2), nullable=True)
    suggested_logistics_model = Column(String(20), nullable=True)
    suggested_commission_ranges_json = Column(Text, nullable=True)
    suggested_gateway_rankings_json = Column(Text, nullable=True)
    consumer_behavior_profile_json = Column(Text, nullable=True)
    # ── Phase 1: Expanded identity ─────────────────────────────────────────────
    official_name = Column(String(150), nullable=True)
    alpha3 = Column(String(3), nullable=True)
    flag_url = Column(String(500), nullable=True)
    currency_name = Column(String(50), nullable=True)
    exchange_rate_to_usd = Column(Numeric(12, 6), nullable=True)
    # ── Phase 1: COD / settlement ──────────────────────────────────────────────
    cod_enabled = Column(Boolean, default=True)
    cod_max_amount = Column(Numeric(12, 2), nullable=True)
    cod_verification_required = Column(Boolean, default=False)
    cod_remittance_days = Column(Integer, nullable=True)
    settlement_hold_days = Column(Integer, default=3)
    minimum_payout_amount = Column(Numeric(12, 2), nullable=True)
    payout_currency = Column(String(10), nullable=True)
    # ── Phase 1: Supplier ──────────────────────────────────────────────────────
    supplier_kyc_tier = Column(String(20), nullable=True)
    supplier_onboarding_fee = Column(Numeric(12, 2), nullable=True)
    supplier_monthly_fee = Column(Numeric(12, 2), nullable=True)
    supplier_rating_threshold = Column(Numeric(3, 2), nullable=True)
    # ── Phase 1: Legal / consumer ────────────────────────────────────────────
    legal_entity_required = Column(Boolean, default=False)
    consumer_protection_days = Column(Integer, default=14)
    data_privacy_framework = Column(String(50), nullable=True)
    # ── Phase 1: Logistics expansion ───────────────────────────────────────────
    max_package_weight_kg = Column(Numeric(8, 2), nullable=True)
    max_package_dimensions_cm = Column(String(100), nullable=True)
    signature_required_threshold = Column(Numeric(8, 2), nullable=True)
    # ── Phase 1: Locale ───────────────────────────────────────────────────────
    measurement_system = Column(String(10), default="metric")
    working_days_json = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    restore_at = Column(DateTime, nullable=True)
    restore_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class CountryGatewayCredentials(Base):
    """Encrypted credential storage per country + gateway + environment."""

    __tablename__ = "country_gateway_credentials"
    __table_args__ = (
        UniqueConstraint(
            "country_code", "gateway_id", "environment",
            name="uq_country_gateway_creds_triplet",
        ),
        Index("ix_country_gateway_credentials_country", "country_code", "gateway_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False, index=True)
    gateway_id = Column(String(60), nullable=False, index=True)
    environment = Column(String(20), nullable=False, default="test")  # test | live
    encrypted_credentials = Column(EncryptedString(), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_rotated_at = Column(DateTime, nullable=True)
    rotated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])
    rotator = relationship("User", foreign_keys=[rotated_by])


class SupplierCountryCommission(Base):
    """Country+category commission overrides managed by admin users."""

    __tablename__ = "supplier_country_commissions"
    __table_args__ = (
        UniqueConstraint("country_code", "category_slug", name="uq_supplier_country_commissions_country_category"),
        Index("ix_supplier_country_commissions_country_active", "country_code", "is_active"),
        CheckConstraint("commission_rate >= 0 AND commission_rate <= 1", name="ck_supplier_country_commission_rate_valid"),
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False, index=True)
    category_slug = Column(String(60), nullable=False, index=True)
    commission_rate = Column(Numeric(5, 4), nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])


class CountryCity(Base):
    """First-class city/region records per country — powers type-ahead dropdown."""

    __tablename__ = "country_cities"
    __table_args__ = (
        UniqueConstraint("country_code", "name", name="uq_country_cities_code_name"),
        Index("ix_country_cities_code_name", "country_code", "name"),
        Index("ix_country_cities_code_active", "country_code", "is_active"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    country_code = Column(String(10), ForeignKey("country_configs.code", ondelete="CASCADE"), nullable=False, index=True)
    region = Column(String(120), nullable=True)
    name = Column(String(120), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    population = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    source = Column(String(24), nullable=False, default="manual")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code], backref="cities")


class CountryCategoryTaxRate(Base):
    """Country-level regulatory tax rate per product category (VAT/GST, not commission)."""

    __tablename__ = "country_category_tax_rates"
    __table_args__ = (
        UniqueConstraint("country_code", "category_slug", name="uq_country_cat_tax_code_slug"),
        Index("ix_country_cat_tax_code_slug", "country_code", "category_slug"),
        CheckConstraint("rate >= 0 AND rate <= 1", name="ck_country_cat_tax_rate_valid"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    country_code = Column(String(10), ForeignKey("country_configs.code", ondelete="CASCADE"), nullable=False, index=True)
    category_slug = Column(String(60), nullable=False, index=True)
    rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    is_exempt = Column(Boolean, nullable=False, default=False)
    is_reduced = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    source = Column(String(24), nullable=False, default="curated")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code], backref="category_tax_rates")


class OmanDeliveryZone(Base):
    """Fixed zone definitions for Oman delivery pricing."""

    __tablename__ = "oman_delivery_zones"
    __table_args__ = (
        UniqueConstraint("zone_code", name="uq_oman_delivery_zones_code"),
        Index("ix_oman_delivery_zones_active_order", "is_active", "sort_order"),
        CheckConstraint("car_rate >= 0", name="ck_oman_delivery_zones_car_nonneg"),
        CheckConstraint("van_rate >= 0", name="ck_oman_delivery_zones_van_nonneg"),
        CheckConstraint("truck_rate >= 0", name="ck_oman_delivery_zones_truck_nonneg"),
        CheckConstraint(
            "weight_surcharge_rate IS NULL OR weight_surcharge_rate >= 0",
            name="ck_oman_delivery_zones_weight_rate_nonneg",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(20), nullable=False, unique=True, index=True)
    zone_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    car_rate = Column(Numeric(12, 3), nullable=False)
    van_rate = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    truck_rate = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    weight_surcharge_rate = Column(Numeric(12, 3), nullable=True)
    weight_surcharge_threshold_kg = Column(Numeric(8, 2), nullable=True)
    cities_json = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class CountryFeatureFlag(Base):
    """Per-country feature flags toggled via admin control plane."""

    __tablename__ = "country_feature_flags"
    __table_args__ = (
        UniqueConstraint("country_code", "feature_key", name="uq_country_feature_flags_country_feature"),
        Index("ix_country_feature_flags_country_enabled", "country_code", "is_enabled"),
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False, index=True)
    feature_key = Column(String(100), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, default=False)
    rollout_audience = Column(String(80), nullable=True)
    notes = Column(Text, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])
    updater = relationship("User", foreign_keys=[updated_by])


class CountryCommunicationTemplate(Base):
    """Communication templates per country."""

    __tablename__ = "country_communication_templates"
    __table_args__ = (
        UniqueConstraint("country_code", "template_key", name="uq_country_communication_templates"),
        Index("ix_country_communication_templates_country_key", "country_code", "template_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False)
    template_key = Column(String(50), nullable=False)
    template_type = Column(String(20), nullable=False)
    subject = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])


class PayoutRuleCategory(Base):
    """Per-category payout rules for a country.

    These define what suppliers earn per sale in a specific category,
    overriding the country-level default payout rate.
    """
    __tablename__ = "payout_rule_categories"
    __table_args__ = (
        UniqueConstraint("country_code", "category_slug", name="uq_payout_rule_cat"),
        CheckConstraint("payout_rate >= 0 AND payout_rate <= 1", name="ck_payout_rule_cat_rate"),
    )
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), nullable=False, index=True)
    category_slug = Column(String(120), nullable=False)
    payout_rate = Column(Numeric(5, 4), nullable=False)  # 0 to 1
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class PayoutRuleProduct(Base):
    """Per-product payout rules for a country.

    Fine-grained overrides at the individual product level,
    taking precedence over category-level and country-level rules.
    """
    __tablename__ = "payout_rule_products"
    __table_args__ = (
        UniqueConstraint("country_code", "product_id", name="uq_payout_rule_product"),
    )
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    payout_rate = Column(Numeric(5, 4), nullable=False)  # 0 to 1
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    product = relationship("Product")


class CountryConfigVersion(Base):
    """Versioned snapshots for draft/approve/publish country settings workflows."""

    __tablename__ = "country_config_versions"
    __table_args__ = (
        Index("ix_country_config_versions_country_type", "country_code", "config_type"),
        Index("ix_country_config_versions_status_created", "status", "created_at"),
        UniqueConstraint("country_code", "config_type", "version", name="uq_country_config_versions_triplet"),
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False, index=True)
    config_type = Column(String(40), nullable=False)  # tax | logistics | commission | payments | flags
    version = Column(Integer, nullable=False, default=1)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft | approved | published | rolled_back
    draft_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    published_at = Column(DateTime, nullable=True)
    effective_from = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])
    drafter = relationship("User", foreign_keys=[draft_by])
    approver = relationship("User", foreign_keys=[approved_by])


class AdminChangeAuditLog(Base):
    """Dedicated audit rows for admin control-plane changes."""

    __tablename__ = "admin_change_audit_logs"
    __table_args__ = (
        Index("ix_admin_change_audit_actor_created", "actor_id", "created_at"),
        Index("ix_admin_change_audit_entity", "entity", "entity_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(40), nullable=False, index=True)  # create | update | approve | publish | rollback
    entity = Column(String(60), nullable=False)
    entity_key = Column(String(120), nullable=True)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    actor = relationship("User", foreign_keys=[actor_id])


# ── Cash Management / Financial Ledger ──────────────────────────────────────────

class TransactionLedger(Base):
    """Per-order financial breakdown — single source of truth for revenue splits.

    Created when an order is confirmed (COD) or payment succeeds (card/tap).
    Each row captures the full breakdown: product revenue, delivery charges,
    VAT, Zozi commission, and net amounts owed to supplier and logistics.
    """
    __tablename__ = "transaction_ledger"
    __table_args__ = (
        Index("ix_txn_ledger_order", "order_id"),
        Index("ix_txn_ledger_supplier", "supplier_id"),
        Index("ix_txn_ledger_logistics", "logistics_partner_id"),
        Index("ix_txn_ledger_status_created", "settlement_status", "created_at"),
        CheckConstraint("product_subtotal >= 0", name="ck_txn_ledger_product_subtotal_nonneg"),
        CheckConstraint("zozi_commission >= 0", name="ck_txn_ledger_commission_nonneg"),
        CheckConstraint("vat_amount >= 0", name="ck_txn_ledger_vat_nonneg"),
    )
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    logistics_partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True, index=True)

    # Payment info
    payment_method = Column(String(20), nullable=False)  # cod | card | tap

    # Revenue breakdown
    product_subtotal = Column(Numeric(12, 2), nullable=False, default=0)  # product price * quantity
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0)   # coupon/promo discount share
    delivery_pickup_charge = Column(Numeric(12, 2), nullable=False, default=0)   # logistics pickup charge
    delivery_dropoff_charge = Column(Numeric(12, 2), nullable=False, default=0)  # logistics dropoff charge
    delivery_total = Column(Numeric(12, 2), nullable=False, default=0)           # pickup + dropoff
    vat_amount = Column(Numeric(12, 2), nullable=False, default=0)        # VAT on product + delivery
    zozi_commission_rate = Column(Numeric(5, 4), nullable=False, default=0.10)  # e.g. 0.1000 = 10%
    zozi_commission = Column(Numeric(12, 2), nullable=False, default=0)   # commission amount

    # Computed net amounts
    net_supplier_amount = Column(Numeric(12, 2), nullable=False, default=0)   # product - discount - commission
    net_logistics_amount = Column(Numeric(12, 2), nullable=False, default=0)  # delivery charges (retained)
    net_zozi_amount = Column(Numeric(12, 2), nullable=False, default=0)       # commission + VAT

    # COD-specific: what logistics partner collected and must remit
    cod_collected_amount = Column(Numeric(12, 2), nullable=True)        # total COD collected by logistics
    cod_remittance_due = Column(Numeric(12, 2), nullable=True)          # amount logistics must remit to Zozi

    # Settlement tracking
    settlement_status = Column(String(30), nullable=False, default="pending")
    # pending | supplier_settled | logistics_settled | fully_settled | refunded
    currency = Column(String(10), nullable=False, default="OMR")

    created_at = Column(DateTime, default=_utcnow, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    order = relationship("Order")
    order_item = relationship("OrderItem")
    supplier = relationship("User", foreign_keys=[supplier_id])
    logistics_partner = relationship("LogisticsPartner")
    shipment = relationship("Shipment")


class SupplierSettlement(Base):
    """Calculated supplier earnings per delivered order — drives automated payouts."""
    __tablename__ = "supplier_settlements"
    __table_args__ = (
        Index("ix_supplier_settlements_supplier_status", "supplier_id", "status"),
        Index("ix_supplier_settlements_order", "order_id"),
        CheckConstraint("gross_amount >= 0", name="ck_supplier_settlements_gross_nonneg"),
        CheckConstraint("commission_deducted >= 0", name="ck_supplier_settlements_commission_nonneg"),
        CheckConstraint("net_amount >= 0", name="ck_supplier_settlements_net_nonneg"),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    ledger_id = Column(Integer, ForeignKey("transaction_ledger.id"), nullable=True, index=True)
    payout_id = Column(Integer, ForeignKey("payouts.id"), nullable=True, index=True)

    gross_amount = Column(Numeric(12, 2), nullable=False)      # product subtotal − discount
    commission_rate = Column(Numeric(5, 4), nullable=False)     # snapshot of commission rate
    commission_deducted = Column(Numeric(12, 2), nullable=False)
    vat_on_commission = Column(Numeric(12, 2), nullable=False, default=0)
    net_amount = Column(Numeric(12, 2), nullable=False)         # gross − commission

    status = Column(String(30), nullable=False, default="pending")
    # pending | eligible | processing | settled | reversed
    eligible_at = Column(DateTime, nullable=True)   # when order was delivered
    settled_at = Column(DateTime, nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)

    currency = Column(String(10), nullable=False, default="OMR")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])
    order = relationship("Order")
    ledger_entry = relationship("TransactionLedger")
    payout = relationship("Payout")


class LogisticsSettlement(Base):
    """Calculated logistics partner earnings per delivered order."""
    __tablename__ = "logistics_settlements"
    __table_args__ = (
        Index("ix_logistics_settlements_partner_status", "partner_id", "status"),
        Index("ix_logistics_settlements_order", "order_id"),
        CheckConstraint("pickup_charge >= 0", name="ck_logistics_settlements_pickup_nonneg"),
        CheckConstraint("dropoff_charge >= 0", name="ck_logistics_settlements_dropoff_nonneg"),
    )
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    ledger_id = Column(Integer, ForeignKey("transaction_ledger.id"), nullable=True, index=True)
    payout_id = Column(Integer, ForeignKey("logistics_partner_payouts.id"), nullable=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True, index=True)

    pickup_charge = Column(Numeric(12, 2), nullable=False, default=0)
    dropoff_charge = Column(Numeric(12, 2), nullable=False, default=0)
    total_delivery_fee = Column(Numeric(12, 2), nullable=False, default=0)

    # COD handling
    cod_collected = Column(Numeric(12, 2), nullable=True)        # total COD this partner collected
    cod_remitted = Column(Numeric(12, 2), nullable=True)         # amount already remitted to Zozi
    cod_retained = Column(Numeric(12, 2), nullable=True)         # delivery fee retained from COD
    cod_remittance_status = Column(String(30), nullable=True)    # pending | partial | complete

    status = Column(String(30), nullable=False, default="pending")
    # pending | eligible | processing | settled | reversed
    eligible_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)

    currency = Column(String(10), nullable=False, default="OMR")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner")
    order = relationship("Order")
    ledger_entry = relationship("TransactionLedger")
    payout = relationship("LogisticsPartnerPayout")
    shipment = relationship("Shipment")


class LogisticsCODRemittanceReceipt(Base):
    """Partner-submitted COD remittance proof pending finance review."""
    __tablename__ = "logistics_cod_remittance_receipts"
    __table_args__ = (
        Index("ix_logistics_cod_receipts_partner_status", "partner_id", "status"),
        Index("ix_logistics_cod_receipts_settlement", "settlement_id", "created_at"),
        CheckConstraint("amount > 0", name="ck_logistics_cod_receipts_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    settlement_id = Column(Integer, ForeignKey("logistics_settlements.id"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    bank_reference = Column(String(200), nullable=True)
    receipt_file_url = Column(String(500), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="pending")
    review_note = Column(Text, nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    settlement = relationship("LogisticsSettlement", foreign_keys=[settlement_id])
    partner = relationship("LogisticsPartner", foreign_keys=[partner_id])
    bank_transaction = relationship("BankTransaction", foreign_keys=[bank_transaction_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class BankTransaction(Base):
    """Bank statement entries for reconciliation — imported or auto-created."""
    __tablename__ = "bank_transactions"
    __table_args__ = (
        Index("ix_bank_txn_source_type", "source", "transaction_type"),
        Index("ix_bank_txn_reconciled", "reconciled"),
        Index("ix_bank_txn_date", "transaction_date"),
    )
    id = Column(Integer, primary_key=True, index=True)
    transaction_ref = Column(String(200), unique=True, nullable=False, index=True)   # bank ref / gateway ID
    source = Column(String(50), nullable=False)           # stripe | tap | cod_remittance | bank_transfer | manual
    transaction_type = Column(String(50), nullable=False)  # inflow | outflow
    category = Column(String(50), nullable=False)
    # card_payment | cod_remittance | supplier_payout | logistics_payout | refund | vat_remittance | manual
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    linked_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    linked_supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    linked_logistics_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=True)
    linked_payout_id = Column(Integer, nullable=True)            # supplier or logistics payout ID
    linked_refund_id = Column(Integer, ForeignKey("return_requests.id"), nullable=True)
    description = Column(Text, nullable=True)
    reconciled = Column(Boolean, nullable=False, default=False)
    reconciled_at = Column(DateTime, nullable=True)
    reconciled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    flagged = Column(Boolean, default=False)              # flagged for manual review
    flag_reason = Column(Text, nullable=True)
    transaction_date = Column(DateTime, nullable=False, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    order = relationship("Order", foreign_keys=[linked_order_id])
    supplier = relationship("User", foreign_keys=[linked_supplier_id])
    logistics_partner = relationship("LogisticsPartner", foreign_keys=[linked_logistics_id])
    reconciler = relationship("User", foreign_keys=[reconciled_by])


class RefundLedger(Base):
    """Tracks refund impact across supplier, logistics, and Zozi — reverse ledger entries."""
    __tablename__ = "refund_ledger"
    __table_args__ = (
        Index("ix_refund_ledger_order", "order_id"),
        Index("ix_refund_ledger_status", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    return_request_id = Column(Integer, ForeignKey("return_requests.id"), nullable=True, index=True)
    ledger_id = Column(Integer, ForeignKey("transaction_ledger.id"), nullable=True, index=True)

    refund_reason = Column(String(100), nullable=False)   # cancellation | return | dispute | admin_override
    refund_method = Column(String(30), nullable=False)     # card_reversal | cod_cash | wallet_credit | bank_transfer

    # Amounts reversed
    customer_refund_amount = Column(Numeric(12, 2), nullable=False)   # total refunded to customer
    supplier_reversal = Column(Numeric(12, 2), nullable=False, default=0)   # clawed back from supplier
    logistics_reversal = Column(Numeric(12, 2), nullable=False, default=0)  # clawed back from logistics
    commission_reversal = Column(Numeric(12, 2), nullable=False, default=0) # Zozi commission reversed
    vat_adjustment = Column(Numeric(12, 2), nullable=False, default=0)      # VAT adjustment

    status = Column(String(30), nullable=False, default="pending")
    # pending | processing | completed | failed
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    currency = Column(String(10), nullable=False, default="OMR")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    order = relationship("Order")
    return_request = relationship("ReturnRequest")
    ledger_entry = relationship("TransactionLedger")
    processor = relationship("User", foreign_keys=[processed_by])


class VATRemittance(Base):
    """Recorded VAT remittance periods for finance and compliance reporting."""
    __tablename__ = "vat_remittances"
    __table_args__ = (
        Index("ix_vat_remittances_period", "period_start", "period_end"),
        Index("ix_vat_remittances_status", "status", "created_at"),
        CheckConstraint("vat_collected_amount >= 0", name="ck_vat_remittances_collected_nonnegative"),
        CheckConstraint("vat_adjustment_amount >= 0", name="ck_vat_remittances_adjustment_nonnegative"),
        CheckConstraint("amount_due >= 0", name="ck_vat_remittances_due_nonnegative"),
        CheckConstraint("amount_remitted >= 0", name="ck_vat_remittances_remitted_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    vat_collected_amount = Column(Numeric(12, 2), nullable=False, default=0)
    vat_adjustment_amount = Column(Numeric(12, 2), nullable=False, default=0)
    amount_due = Column(Numeric(12, 2), nullable=False, default=0)
    amount_remitted = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="pending")
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)
    remitted_at = Column(DateTime, nullable=True)
    remitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    currency = Column(String(10), nullable=False, default="OMR")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    bank_transaction = relationship("BankTransaction", foreign_keys=[bank_transaction_id])
    remitter = relationship("User", foreign_keys=[remitted_by])


class SupplierBankAccount(Base):
    """Supplier-submitted bank account for payout transfers — admin must verify before use in exports."""
    __tablename__ = "supplier_bank_accounts"
    __table_args__ = (
        UniqueConstraint("supplier_id", name="uq_supplier_bank_accounts_supplier"),
        Index("ix_supplier_bank_accounts_status", "verification_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    # Beneficiary details (encrypted at rest)
    beneficiary_name = Column(EncryptedString(255), nullable=True)
    bank_name = Column(String(200), nullable=True)
    branch_name = Column(String(200), nullable=True)
    account_number = Column(EncryptedString(120), nullable=True)
    iban = Column(EncryptedString(120), nullable=True)
    swift_code = Column(EncryptedString(120), nullable=True)
    routing_number = Column(EncryptedString(120), nullable=True)
    currency = Column(String(10), nullable=False, default="OMR")
    bank_country = Column(String(100), nullable=True)
    # Admin review
    verification_status = Column(String(30), nullable=False, default="pending")
    # pending | verified | rejected
    verification_note = Column(Text, nullable=True)
    provider = Column(String(50), nullable=True)
    provider_recipient_id = Column(String(255), nullable=True)
    provider_status = Column(String(50), nullable=True)
    provider_last_synced_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])
    reviewer = relationship("User", foreign_keys=[verified_by])


class LogisticsPartnerBankAccount(Base):
    """Logistics partner bank account for payout transfers — admin must verify before use in exports."""
    __tablename__ = "logistics_partner_bank_accounts"
    __table_args__ = (
        UniqueConstraint("partner_id", name="uq_logistics_partner_bank_accounts_partner"),
        Index("ix_logistics_partner_bank_accounts_status", "verification_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, unique=True, index=True)
    beneficiary_name = Column(EncryptedString(255), nullable=True)
    bank_name = Column(String(200), nullable=True)
    branch_name = Column(String(200), nullable=True)
    account_number = Column(EncryptedString(120), nullable=True)
    iban = Column(EncryptedString(120), nullable=True)
    swift_code = Column(EncryptedString(120), nullable=True)
    routing_number = Column(EncryptedString(120), nullable=True)
    currency = Column(String(10), nullable=False, default="OMR")
    bank_country = Column(String(100), nullable=True)
    # Admin review
    verification_status = Column(String(30), nullable=False, default="pending")
    # pending | verified | rejected
    verification_note = Column(Text, nullable=True)
    provider = Column(String(50), nullable=True)
    provider_recipient_id = Column(String(255), nullable=True)
    provider_status = Column(String(50), nullable=True)
    provider_last_synced_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", foreign_keys=[partner_id])
    reviewer = relationship("User", foreign_keys=[verified_by])


class FinanceBankAccount(Base):
    """Admin-managed bank details for Zozi treasury, VAT, and remittance operations."""
    __tablename__ = "finance_bank_accounts"
    __table_args__ = (
        UniqueConstraint("scope", name="uq_finance_bank_accounts_scope"),
        Index("ix_finance_bank_accounts_scope_active", "scope", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(50), nullable=False, default="zozi_primary")
    account_label = Column(String(150), nullable=True)
    beneficiary_name = Column(EncryptedString(255), nullable=True)
    bank_name = Column(String(200), nullable=True)
    branch_name = Column(String(200), nullable=True)
    account_number = Column(EncryptedString(120), nullable=True)
    iban = Column(EncryptedString(120), nullable=True)
    swift_code = Column(EncryptedString(120), nullable=True)
    routing_number = Column(EncryptedString(120), nullable=True)
    currency = Column(String(10), nullable=False, default="AED")
    support_email = Column(EncryptedString(255), nullable=True)
    support_phone = Column(EncryptedString(80), nullable=True)
    remittance_reference_prefix = Column(String(50), nullable=True)
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class RolePermissionSetting(Base):
    """Persisted overrides for the in-memory ROLE_PERMISSION_MAP.

    An admin can add/remove permissions per role via the Hierarchy tab in the
    dashboard.  On startup the application loads these rows and merges them
    into the active permission map so every in-process guard is up to date.
    """

    __tablename__ = "role_permission_settings"
    __table_args__ = (
        UniqueConstraint("role", name="uq_role_permission_settings_role"),
        Index("ix_role_permission_settings_role", "role"),
    )

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, unique=True)
    permissions = Column(JSON, nullable=False, default=list)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    updated_by = relationship("User", foreign_keys=[updated_by_id])


# ── Integrated Communication: Ticket Attachments ──────────────────────────────

class TicketAttachment(Base):
    """File attachments for support ticket messages — uploaded via multipart."""
    __tablename__ = "ticket_attachments"
    __table_args__ = (
        Index("ix_ticket_attachments_ticket", "ticket_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    reply_id = Column(Integer, ForeignKey("ticket_replies.id", ondelete="CASCADE"), nullable=True, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=False)        # server-relative path
    original_name = Column(String(255), nullable=False)    # original client filename
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    ticket = relationship("SupportTicket", back_populates="attachments")
    reply = relationship("TicketReply", back_populates="attachments")
    uploader = relationship("User")


class CountryStaffAssignment(Base):
    """Links staff members to countries they manage for RLS enforcement."""
    __tablename__ = "country_staff_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "country_code", name="uq_country_staff_assignment"),
        Index("ix_country_staff_assignments_user_active", "user_id", "is_active"),
        Index("ix_country_staff_assignments_country_active", "country_code", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    assigned_at = Column(DateTime, default=_utcnow)
    deactivated_at = Column(DateTime, nullable=True)
    deactivated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    country = relationship("CountryConfig", foreign_keys=[country_code])
    assigner = relationship("User", foreign_keys=[assigned_by])
    deactivator = relationship("User", foreign_keys=[deactivated_by])


class CountryCommunication(Base):
    """Communications between admins and country staff."""
    __tablename__ = "country_communications"
    __table_args__ = (
        Index("ix_country_comms_country_status", "country_code", "status"),
        Index("ix_country_comms_recipient", "to_user_id", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="normal")
    status = Column(String(20), nullable=False, default="unread")
    category = Column(String(40), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    read_at = Column(DateTime, nullable=True)

    country = relationship("CountryConfig")
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])


class CrossCountryCustomerSession(Base):
    """Tracks customer sessions crossing country boundaries."""
    __tablename__ = "cross_country_customer_sessions"
    __table_args__ = (
        Index("ix_cc_customer_sessions_source", "source_country_code"),
        Index("ix_cc_customer_sessions_target", "target_country_code"),
        Index("ix_cc_customer_sessions_user", "user_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False)
    target_country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False)
    session_data = Column(Text, nullable=True)
    conversion = Column(Boolean, default=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")
    source_country = relationship("CountryConfig", foreign_keys=[source_country_code])
    target_country = relationship("CountryConfig", foreign_keys=[target_country_code])


class CommissionAgreement(Base):
    """Versioned supplier-level commission rate agreements set by admin.

    Only one row per supplier should have is_active=True at a time.
    When a new rate is set, the previous active row gets effective_to set
    and a new row is inserted.
    """
    __tablename__ = "commission_agreements"
    __table_args__ = (
        Index("ix_commission_agreements_supplier_active", "supplier_id", "is_active"),
        Index("ix_commission_agreements_country", "country_code"),
        CheckConstraint("rate >= 0 AND rate <= 1", name="ck_commission_agreements_rate_valid"),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    rate = Column(Numeric(5, 4), nullable=False)           # e.g. 0.1200 = 12%
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)         # NULL = currently active
    is_active = Column(Boolean, nullable=False, default=True)
    set_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])
    set_by_admin = relationship("User", foreign_keys=[set_by_admin_id])
    country = relationship("CountryConfig", foreign_keys=[country_code])


class ProductCommissionOverride(Base):
    """Per-product commission rate override — takes precedence over supplier agreement."""
    __tablename__ = "product_commission_overrides"
    __table_args__ = (
        Index("ix_product_commission_overrides_supplier", "supplier_id"),
        CheckConstraint("rate >= 0 AND rate <= 1", name="ck_product_commission_rate_valid"),
    )
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rate = Column(Numeric(5, 4), nullable=False)           # e.g. 0.0800 = 8%
    is_active = Column(Boolean, nullable=False, default=True)
    set_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    product = relationship("Product", back_populates="commission_override")
    supplier = relationship("User", foreign_keys=[supplier_id])
    set_by_admin = relationship("User", foreign_keys=[set_by_admin_id])


# ── Full Commission Engine Models ─────────────────────────────────────────────

class CommissionGlobalConfig(Base):
    """Platform-wide commission defaults — singleton row (id=1).

    Precedence: Admin Override → Category Rate → Badge Rate → this default.
    """
    __tablename__ = "commission_global_config"
    __table_args__ = (
        CheckConstraint("default_rate >= 0 AND default_rate <= 1", name="ck_cgc_default_rate_valid"),
        CheckConstraint("low_value_threshold >= 0", name="ck_cgc_low_value_threshold_nonneg"),
        CheckConstraint("fixed_cap_amount >= 0", name="ck_cgc_fixed_cap_amount_nonneg"),
    )
    id = Column(Integer, primary_key=True, index=True)
    # Global fallback rate if no override / category / badge rate applies
    default_rate = Column(Numeric(5, 4), nullable=False, default=Decimal("0.1500"))  # 15%
    # Low-value order cap rule
    low_value_threshold = Column(Numeric(12, 2), nullable=False, default=Decimal("5.00"))   # 5 OMR
    fixed_cap_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.50"))       # 0.500 OMR
    fixed_cap_enabled = Column(Boolean, nullable=False, default=True)
    # Margin protection (optional flag)
    margin_protection_enabled = Column(Boolean, nullable=False, default=False)
    margin_threshold = Column(Numeric(5, 4), nullable=True, default=Decimal("0.10"))   # 10%
    # Audit
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])


class CommissionCategoryRate(Base):
    """Admin-configured commission rate per product category.

    When active, takes precedence over the supplier badge rate but is
    overridden by a per-supplier admin override (CommissionAgreement).
    """
    __tablename__ = "commission_category_rates"
    __table_args__ = (
        UniqueConstraint("category_slug", name="uq_commission_category_rates_slug"),
        Index("ix_commission_category_rates_active", "is_active", "category_slug"),
        CheckConstraint("rate >= 0 AND rate <= 1", name="ck_ccr_rate_valid"),
    )
    id = Column(Integer, primary_key=True, index=True)
    category_slug = Column(String(100), nullable=False, unique=True, index=True)
    category_display_name = Column(String(150), nullable=False)
    rate = Column(Numeric(5, 4), nullable=False)            # e.g. 0.0800 = 8%
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])


class CommissionBadgeTier(Base):
    """Badge tier definitions — commission rates and supplier badge fees.

    Suppliers pay setup_fee (one-time) and recurring_fee to obtain a badge,
    which in turn lowers their commission rate.
    badge_level: none | bronze | silver | gold | platinum | membership
    """
    __tablename__ = "commission_badge_tiers"
    __table_args__ = (
        UniqueConstraint("badge_level", name="uq_commission_badge_tiers_level"),
        CheckConstraint("commission_rate >= 0 AND commission_rate <= 1", name="ck_cbt_rate_valid"),
        CheckConstraint("setup_fee >= 0", name="ck_cbt_setup_fee_nonneg"),
        CheckConstraint("recurring_fee >= 0", name="ck_cbt_recurring_fee_nonneg"),
    )
    id = Column(Integer, primary_key=True, index=True)
    badge_level = Column(String(30), nullable=False, unique=True, index=True)
    badge = Column(String(30), nullable=True)
    # none | bronze | silver | gold | platinum | membership
    commission_rate = Column(Numeric(5, 4), nullable=False)    # e.g. 0.15 = 15%
    setup_fee = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    recurring_fee = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    recurring_interval = Column(String(20), nullable=True)     # monthly | annual | None
    benefits_json = Column(Text, nullable=True)                # JSON list of benefit strings
    # Badge qualification thresholds (for display/reference; auto-upgrade job may use these)
    min_fulfilled_orders = Column(Integer, nullable=True)      # e.g. 50 for Silver
    min_monthly_revenue = Column(Numeric(12, 2), nullable=True)  # e.g. 2000 OMR for Silver
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    updater = relationship("User", foreign_keys=[updated_by])


class BadgeBillingRecord(Base):
    """Supplier badge charges tracked as first-class finance records."""
    __tablename__ = "badge_billing_records"
    __table_args__ = (
        Index("ix_badge_billing_supplier_status", "supplier_id", "status"),
        Index("ix_badge_billing_badge_charge", "badge_level", "charge_type"),
        UniqueConstraint("billing_reference", name="uq_badge_billing_reference"),
        CheckConstraint("amount >= 0", name="ck_badge_billing_amount_nonneg"),
        CheckConstraint(
            "charge_type IN ('setup','recurring','adjustment')",
            name="ck_badge_billing_charge_type_valid",
        ),
        CheckConstraint(
            "status IN ('draft','invoiced','paid','waived','cancelled')",
            name="ck_badge_billing_status_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    billing_reference = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_level = Column(String(30), nullable=False, index=True)
    charge_type = Column(String(20), nullable=False, default="setup")
    charge_source = Column(String(30), nullable=False, default="manual_purchase")
    status = Column(String(20), nullable=False, default="invoiced")

    amount = Column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    currency = Column(String(10), nullable=False, default="AED")
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    billed_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    payment_method = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    supplier = relationship("User", foreign_keys=[supplier_id])
    bank_transaction = relationship("BankTransaction", foreign_keys=[bank_transaction_id])
    creator = relationship("User", foreign_keys=[created_by])


class CommissionLedgerEntry(Base):
    """Immutable commission ledger — one row per order-item per supplier.

    Records the full audit trail of how commission was calculated:
    which rate was applied, why, the raw amount, and whether the low-value
    cap was triggered.  Disputes/adjustments create new rows with
    is_adjusted=True rather than mutating the original row.
    """
    __tablename__ = "commission_ledger_entries"
    __table_args__ = (
        Index("ix_cle_order_supplier", "order_id", "supplier_id"),
        Index("ix_cle_supplier_created", "supplier_id", "created_at"),
        Index("ix_cle_order_item", "order_item_id"),
        CheckConstraint("applied_rate >= 0 AND applied_rate <= 1", name="ck_cle_applied_rate_valid"),
        CheckConstraint("order_value >= 0", name="ck_cle_order_value_nonneg"),
        CheckConstraint("commission_amount >= 0", name="ck_cle_commission_amount_nonneg"),
        CheckConstraint(
            "calculation_method IN ('override','category','badge','global_default')",
            name="ck_cle_calc_method_valid",
        ),
    )
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    category_slug = Column(String(100), nullable=True)
    badge_level = Column(String(30), nullable=True)

    # Rate snapshot at calculation time
    global_default_rate = Column(Numeric(5, 4), nullable=True)
    category_rate = Column(Numeric(5, 4), nullable=True)
    badge_rate = Column(Numeric(5, 4), nullable=True)
    override_rate = Column(Numeric(5, 4), nullable=True)
    applied_rate = Column(Numeric(5, 4), nullable=False)
    calculation_method = Column(String(30), nullable=False)
    # override | category | badge | global_default

    # Commission amounts
    order_value = Column(Numeric(12, 2), nullable=False)
    commission_pct = Column(Numeric(12, 3), nullable=False)   # before low-value cap
    cap_applied = Column(Boolean, nullable=False, default=False)
    commission_amount = Column(Numeric(12, 3), nullable=False)  # final after cap
    low_value_threshold_used = Column(Numeric(12, 2), nullable=True)
    fixed_cap_used = Column(Numeric(12, 3), nullable=True)

    override_flag = Column(Boolean, nullable=False, default=False)

    # Adjustment tracking (disputes create a new row; this row is never mutated)
    is_adjusted = Column(Boolean, nullable=False, default=False)
    adjusted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    adjusted_at = Column(DateTime, nullable=True)
    adjustment_reason = Column(Text, nullable=True)
    original_commission_amount = Column(Numeric(12, 3), nullable=True)

    currency = Column(String(10), nullable=False, default="OMR")
    created_at = Column(DateTime, default=_utcnow, index=True)

    order = relationship("Order")
    order_item = relationship("OrderItem")
    supplier = relationship("User", foreign_keys=[supplier_id])
    product = relationship("Product")
    adjuster = relationship("User", foreign_keys=[adjusted_by])


# ---------------------------------------------------------------------------
# Legacy compatibility exports
# ---------------------------------------------------------------------------

class FlashSaleItem(Base):
    """Legacy flash-sale item rows used by lightweight flash sales router."""
    __tablename__ = "flash_sale_items"
    id = Column(Integer, primary_key=True, index=True)
    flash_sale_id = Column(Integer, ForeignKey("flash_sales.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    sale_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    stock_limit = Column(Integer, nullable=True)
    sold_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)


class CashAccount(Base):
    """Legacy admin cash account model used by admin_cash router."""
    __tablename__ = "cash_accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False)
    account_type = Column(String(60), nullable=False)
    currency = Column(String(10), nullable=False, default="AED")
    balance = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_utcnow)


class CashTransaction(Base):
    """Legacy admin cash transaction model used by admin_cash router."""
    __tablename__ = "cash_transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("cash_accounts.id"), nullable=False, index=True)
    transaction_type = Column(String(30), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    reference = Column(String(120), nullable=True)
    category = Column(String(80), nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class Referral(Base):
    """Legacy referral-code mapping used by referrals router."""
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    referral_code = Column(String(40), nullable=False, unique=True, index=True)
    status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime, default=_utcnow)


# ── General Ledger — Double-Entry Accounting ─────────────────────────────

class AccountGroup(Base):
    """Hierarchical grouping for Chart of Accounts (e.g. Current Assets, Liabilities)."""
    __tablename__ = "account_groups"
    __table_args__ = (
        UniqueConstraint("code", name="uq_account_groups_code"),
    )
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("account_groups.id"), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    children = relationship("AccountGroup", backref="parent", remote_side=[id])
    accounts = relationship("Account", back_populates="group")


class Account(Base):
    """A single account in the Chart of Accounts.

    Follows standard accounting: Assets (1xxx), Liabilities (2xxx),
    Equity (3xxx), Revenue (4xxx), Expenses (5xxx).
    """
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("code", name="uq_accounts_code"),
        CheckConstraint("normal_side IN ('debit', 'credit')", name="ck_accounts_normal_side"),
    )
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    normal_side = Column(String(10), nullable=False)   # debit | credit
    currency = Column(String(10), nullable=False, default="OMR")
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    group = relationship("AccountGroup", back_populates="accounts")


class JournalEntry(Base):
    """Core double-entry record. Every financial movement is recorded here."""
    __tablename__ = "journal_entries"
    __table_args__ = (
        Index("ix_journal_entries_date", "entry_date"),
        Index("ix_journal_entries_reference", "reference_type", "reference_id"),
    )
    id = Column(Integer, primary_key=True)
    entry_date = Column(DateTime, nullable=False, index=True)
    reference_type = Column(String(40), nullable=False)   # order | payout | refund | vat | fee | adjustment
    reference_id = Column(Integer, nullable=False)
    reference_number = Column(String(100), nullable=True)
    description = Column(String(500), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    fx_rate = Column(Numeric(12, 6), nullable=True, default=Decimal("1.000000"))
    is_reconciled = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")


class JournalEntryLine(Base):
    """Individual debit/credit line within a journal entry."""
    __tablename__ = "journal_entry_lines"
    __table_args__ = (
        Index("ix_jel_account", "account_id"),
        Index("ix_jel_entry", "entry_id"),
        CheckConstraint("amount > 0", name="ck_jel_amount_positive"),
        CheckConstraint("side IN ('debit', 'credit')", name="ck_jel_side"),
    )
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    side = Column(String(10), nullable=False)       # debit | credit
    amount = Column(Numeric(12, 2), nullable=False)  # always positive
    description = Column(String(300), nullable=True)
    entity_type = Column(String(40), nullable=True)  # supplier | customer | logistics | system
    entity_id = Column(Integer, nullable=True)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")


class AccountBalance(Base):
    """Materialized running balance per account (updated on each journal entry)."""
    __tablename__ = "account_balances"
    __table_args__ = (
        UniqueConstraint("account_id", "currency", name="uq_account_balances_account_currency"),
    )
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    currency = Column(String(10), nullable=False, default="OMR")
    balance = Column(Numeric(16, 2), nullable=False, default=Decimal("0.00"))
    last_entry_id = Column(Integer, nullable=True)
    last_entry_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


# ── Treasury Management ────────────────────────────────────────────────────

class TreasuryAccount(Base):
    """Cash position buckets for treasury management."""
    __tablename__ = "treasury_accounts"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_treasury_accounts_slug"),
        CheckConstraint("account_type IN ('cash','reserve','receivable','payable')",
                        name="ck_treasury_accounts_type"),
        Index("ix_treasury_employee", "employee_id"),
    )
    id = Column(Integer, primary_key=True)
    slug = Column(String(60), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    account_type = Column(String(30), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    currency = Column(String(10), nullable=False, default="OMR")
    gl_account_code = Column(String(20), nullable=True)
    balance = Column(Numeric(16, 2), nullable=False, default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee")


class CashPositionSnapshot(Base):
    """Daily cash position record for audit and analysis."""
    __tablename__ = "cash_position_snapshots"
    __table_args__ = (
        Index("ix_cps_date", "snapshot_date"),
        UniqueConstraint("snapshot_date", "currency", name="uq_cps_date_currency"),
    )
    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date, nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    cash_operating = Column(Numeric(16, 2), nullable=False, default=0)
    cash_gateway_settlement = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_supplier_payable = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_logistics_payable = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_refund = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_vat = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_commission = Column(Numeric(16, 2), nullable=False, default=0)
    receivable_customer = Column(Numeric(16, 2), nullable=False, default=0)
    total_cash = Column(Numeric(16, 2), nullable=False, default=0)
    total_reserves = Column(Numeric(16, 2), nullable=False, default=0)
    free_cash = Column(Numeric(16, 2), nullable=False, default=0)
    net_working_capital = Column(Numeric(16, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)


class CashFlowForecast(Base):
    """Projected cash inflow/outflow for a future period."""
    __tablename__ = "cash_flow_forecasts"
    __table_args__ = (Index("ix_cff_date", "forecast_date"),)
    id = Column(Integer, primary_key=True)
    forecast_date = Column(Date, nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    forecast_category = Column(String(40), nullable=False)  # settlement_inflow | payout_outflow | vat_outflow | refund_outflow
    forecast_type = Column(String(10), nullable=False)       # inflow | outflow
    expected_amount = Column(Numeric(16, 2), nullable=False)
    confidence = Column(String(20), nullable=False, default="medium")  # high | medium | low
    source_entity = Column(String(40), nullable=True)
    source_id = Column(Integer, nullable=True)
    description = Column(String(300), nullable=True)
    expected_settlement_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class GatewaySettlementSchedule(Base):
    """Expected settlements from payment gateways (funds in transit)."""
    __tablename__ = "gateway_settlement_schedules"
    __table_args__ = (Index("ix_gwss_date", "expected_settlement_date"),)
    id = Column(Integer, primary_key=True)
    gateway_code = Column(String(60), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    transaction_id = Column(String(255), nullable=False)
    amount = Column(Numeric(16, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    gateway_fee = Column(Numeric(12, 2), nullable=False, default=0)
    net_amount = Column(Numeric(16, 2), nullable=False)     # amount - fee
    transaction_date = Column(DateTime, nullable=False)
    expected_settlement_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="pending")   # pending | settled | failed
    settled_at = Column(DateTime, nullable=True)
    settlement_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class TreasuryTransaction(Base):
    """Audit trail for movements between treasury accounts."""
    __tablename__ = "treasury_transactions"
    id = Column(Integer, primary_key=True)
    from_account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    amount = Column(Numeric(16, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    transaction_type = Column(String(40), nullable=False)
    description = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class AuditLog(Base):
    """Immutable audit trail for all sensitive operations."""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_event_type_occurred", "event_type", "occurred_at"),
        Index("ix_audit_logs_actor_occurred", "user_id", "occurred_at"),
        Index("ix_audit_logs_resource_occurred", "resource_type", "resource_id", "occurred_at"),
        Index("ix_audit_logs_country_occurred", "country_code", "occurred_at"),
        CheckConstraint(
            "severity IN ('debug', 'info', 'warning', 'error', 'critical')",
            name="ck_audit_logs_severity_valid",
        ),
    )
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(160), nullable=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=True, index=True)
    country_code = Column(String(10), nullable=True, index=True)
    details_json = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default="info")
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(64), nullable=True)
    occurred_at = Column(DateTime, nullable=False, default=_utcnow, index=True)
    status = Column(String(30), nullable=True)
    details = Column(Text, nullable=True)

    actor = relationship("User", foreign_keys=[user_id])


# ── Fraud Detection Models ──────────────────────────────────────────────────────

class FraudEvent(Base):
    """Immutable fraud detection event log."""
    __tablename__ = "fraud_events"
    __table_args__ = (
        Index("ix_fraud_events_user_created", "user_id", "created_at"),
        Index("ix_fraud_events_ip_created", "ip_address", "created_at"),
        Index("ix_fraud_events_score_created", "fraud_score", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    device_hash = Column(String(64), nullable=True)
    fraud_score = Column(Integer, nullable=False, default=0)
    triggered_rules = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)

    user = relationship("User", foreign_keys=[user_id])


class FraudBlacklist(Base):
    """Blacklisted entities for fraud prevention."""
    __tablename__ = "fraud_blacklist"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_value", name="uq_fraud_blacklist_entity"),
        Index("ix_fraud_blacklist_type_status", "entity_type", "is_active"),
    )
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), nullable=False)  # ip | device | user | email
    entity_value = Column(String(255), nullable=False, index=True)
    reason = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    blacklisted_at = Column(DateTime, default=_utcnow)
    blacklisted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)

    blocker = relationship("User", foreign_keys=[blacklisted_by])


class FraudRule(Base):
    """Configurable fraud detection rules."""
    __tablename__ = "fraud_rules"
    __table_args__ = (
        UniqueConstraint("rule_key", name="uq_fraud_rules_key"),
        Index("ix_fraud_rules_active_score", "is_active", "threshold_score"),
    )
    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String(50), nullable=False, unique=True)
    rule_name = Column(String(100), nullable=False)
    threshold_score = Column(Integer, nullable=False, default=50)
    is_active = Column(Boolean, default=True)
    action = Column(String(20), default="review")  # allow | review | block
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class ManualReviewQueue(Base):
    """Queue for fraud reviews requiring manual intervention."""
    __tablename__ = "manual_review_queue"
    __table_args__ = (
        Index("ix_manual_review_status_priority", "status", "priority", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    fraud_event_id = Column(Integer, ForeignKey("fraud_events.id"), nullable=True)
    entity_type = Column(String(30), nullable=False)  # order | user | payment
    entity_id = Column(Integer, nullable=False)
    fraud_score = Column(Integer, nullable=False)
    triggered_rules = Column(Text, nullable=True)
    priority = Column(String(20), default="medium")  # low | medium | high | urgent
    status = Column(String(30), default="pending")  # pending | assigned | in_review | approved | rejected
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    fraud_event = relationship("FraudEvent")
    assignee = relationship("User", foreign_keys=[assigned_to])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class IPReputation(Base):
    """IP reputation tracking."""
    __tablename__ = "ip_reputation"
    __table_args__ = (
        UniqueConstraint("ip_address", name="uq_ip_reputation_ip"),
        Index("ix_ip_reputation_score", "reputation_score"),
    )
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, unique=True)
    is_proxy = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_vpn = Column(Boolean, default=False)
    is_hosting = Column(Boolean, default=False)
    asn = Column(String(20), nullable=True)
    country_code = Column(String(10), nullable=True)
    last_seen_at = Column(DateTime, default=_utcnow)
    reputation_score = Column(Integer, default=0)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class DeviceFingerprint(Base):
    """Device fingerprint tracking for fraud detection."""
    __tablename__ = "device_fingerprints"
    __table_args__ = (
        UniqueConstraint("fingerprint_hash", name="uq_device_fingerprint_hash"),
        Index("ix_device_fingerprints_user_created", "user_id", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    fingerprint_hash = Column(String(64), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_addresses = Column(Text, nullable=True)  # JSON list
    risk_score = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    headless_attempts = Column(Integer, default=0)
    account_count = Column(Integer, default=0)
    last_seen = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class UserLoginHistory(Base):
    """User login history for fraud detection."""
    __tablename__ = "user_login_history"
    __table_args__ = (
        Index("ix_user_login_user_timestamp", "user_id", "timestamp"),
        Index("ix_user_login_ip", "ip_address"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    success = Column(Boolean, default=True)
    location = Column(String(255), nullable=True)


class CreditCardBin(Base):
    """Credit card BIN database for fraud detection."""
    __tablename__ = "credit_card_bins"
    __table_args__ = (
        UniqueConstraint("bin", name="uq_credit_card_bins_bin"),
        Index("ix_credit_card_bins_country", "country"),
    )
    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(10), nullable=False, unique=True)
    brand = Column(String(50), nullable=True)
    bank = Column(String(100), nullable=True)
    country = Column(String(10), nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)


class ReturnAbusePattern(Base):
    """Return abuse patterns tracked per user."""
    __tablename__ = "return_abuse_patterns"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_return_abuse_pattern_user"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    return_rate = Column(Numeric(5, 2), default=0)
    total_orders = Column(Integer, default=0)
    total_returns = Column(Integer, default=0)
    is_abuser = Column(Boolean, default=False)
    first_detected = Column(DateTime, default=_utcnow)
    last_detected = Column(DateTime, default=_utcnow)


class SupplierFraudIndicator(Base):
    """Fraud indicators for suppliers."""
    __tablename__ = "supplier_fraud_indicators"
    __table_args__ = (
        UniqueConstraint("supplier_id", name="uq_supplier_fraud_indicator_supplier"),
        Index("ix_supplier_fraud_risk", "risk_score"),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    risk_score = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    disputed_orders = Column(Integer, default=0)
    refund_rate = Column(Numeric(5, 2), default=0)
    is_flagged = Column(Boolean, default=False)
    flagged_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class LogisticsFraudIndicator(Base):
    """Fraud indicators for logistics partners."""
    __tablename__ = "logistics_fraud_indicators"
    __table_args__ = (
        UniqueConstraint("partner_id", name="uq_logistics_fraud_indicator_partner"),
        Index("ix_logistics_fraud_risk", "risk_score"),
    )
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False, unique=True)
    risk_score = Column(Integer, default=0)
    total_shipments = Column(Integer, default=0)
    disputed_shipments = Column(Integer, default=0)
    is_flagged = Column(Boolean, default=False)
    flagged_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class FraudAlert(Base):
    """Fraud alerts for dashboard."""
    __tablename__ = "fraud_alerts"
    __table_args__ = (
        Index("ix_fraud_alerts_status_created", "status", "created_at"),
        Index("ix_fraud_alerts_priority_created", "priority", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(30), nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(Integer, nullable=False)
    fraud_score = Column(Integer, nullable=False)
    triggered_rules = Column(Text, nullable=True)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="new")  # new | acknowledged | resolved
    details = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    assignee = relationship("User", foreign_keys=[assigned_to])
    resolver = relationship("User", foreign_keys=[resolved_by])


class IPAccountLinkage(Base):
    """IP-to-account linkage for fraud detection."""
    __tablename__ = "ip_account_linkages"
    __table_args__ = (
        Index("ix_ip_linkage_ip_user", "ip_address", "user_id"),
        Index("ix_ip_linkage_ip_suspicious", "ip_address", "is_suspicious"),
    )
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_fingerprint = Column(String(64), nullable=True)
    session_id = Column(String(64), nullable=True)
    interaction_count = Column(Integer, default=1)
    is_suspicious = Column(Boolean, default=False)
    first_seen = Column(DateTime, default=_utcnow)
    last_seen = Column(DateTime, default=_utcnow)


class ExecutiveNews(Base):
    __tablename__ = "executive_news"
    __table_args__ = (
        Index("ix_executive_news_published_created", "published_at", "created_at"),
        Index("ix_executive_news_category", "category"),
    )
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    priority = Column(String(20), default="normal")
    country_code = Column(String(10), nullable=True)
    published_at = Column(DateTime, nullable=True)
    ai_sentiment = Column(String(20), default="neutral")
    ai_tags = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class SystemAlert(Base):
    __tablename__ = "system_alerts"
    __table_args__ = (
        Index("ix_system_alerts_status_severity", "status", "severity", "created_at"),
        Index("ix_system_alerts_type", "alert_type"),
    )
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    country_code = Column(String(10), nullable=True)
    status = Column(String(20), default="open")
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    assignee = relationship("User", foreign_keys=[assigned_to])
    resolver = relationship("User", foreign_keys=[resolved_by])


class CommandCenterView(Base):
    __tablename__ = "command_center_views"
    __table_args__ = (
        UniqueConstraint("user_id", "view_name", name="uq_command_center_view_user_name"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    view_name = Column(String(100), nullable=False)
    config_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User")


# Compatibility aliases expected by legacy routers.
WishlistItem = Wishlist
TicketMessage = TicketReply
LogisticsPartnerProfile = LogisticsPartner


class Employee(Base):
    """Employee record linked to a platform user."""
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_code = Column(String(20), nullable=True)
    office_id = Column(Integer, nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    employment_type = Column(String(30), nullable=True)
    employment_status = Column(String(30), nullable=True)
    salary = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), nullable=True)
    country_code = Column(String(10), nullable=True)
    hire_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    is_verified = Column(Boolean, default=False)
    gender = Column(String(20), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    performance_score = Column(Integer, nullable=True)
    education_level = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    reporting_manager_id = Column(Integer, nullable=True)
    hiring_manager_id = Column(Integer, nullable=True)
    authority_level = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User")



