from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="customer", index=True)  # customer, supplier, admin
    is_active = Column(Integer, default=1)
    # Extended profile
    phone = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    address_book = Column(Text, nullable=True)  # JSON-serialised list of address dicts
    preferred_language = Column(String, default="en")
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    category = Column(String, index=True)
    brand = Column(String, index=True)
    rating = Column(Float, default=0.0)
    image_url = Column(String)
    stock = Column(Integer, default=0)
    color = Column(String, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)  # soft delete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("User")
    reviews = relationship("Review", back_populates="product", lazy="dynamic")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    total_amount = Column(Float)
    status = Column(String, default="pending", index=True)
    shipping_address = Column(Text, nullable=True)
    tracking_number = Column(String, nullable=True)
    payment_intent_id = Column(String, nullable=True, index=True)  # Stripe PaymentIntent ID
    paid_at = Column(DateTime, nullable=True)                       # Set when payment succeeds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    quantity = Column(Integer)
    price = Column(Float)  # Price at time of order

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


class Review(Base):
    """Customer product reviews — used by Phase 2 /reviews router."""
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    rating = Column(Float, nullable=False)  # 1.0 – 5.0
    comment = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    is_verified_purchase = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User")


class Wishlist(Base):
    """Persisted per-user wishlist — enables cross-device sync."""
    __tablename__ = "wishlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    product = relationship("Product")


class Coupon(Base):
    """Discount coupons redeemable at checkout."""
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    discount_type = Column(String, default="percent")  # percent | fixed
    value = Column(Float)  # percentage (10 = 10%) or fixed AED amount
    min_order = Column(Float, default=0.0)
    max_uses = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    """In-app notifications for customers and suppliers."""
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(String)  # order_update | low_stock | payout | system
    title = Column(String)
    message = Column(Text)
    read = Column(Boolean, default=False)
    link = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class Category(Base):
    """Hierarchical product categories (supports parent/child tree)."""
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    icon = Column(String, nullable=True)  # e.g. emoji or icon name
    image_url = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class EmailVerificationToken(Base):
    """Single-use email verification tokens (TTL: 24 hours)."""
    __tablename__ = "email_verification_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class Payout(Base):
    """Supplier payout requests and history."""
    __tablename__ = "payouts"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending | processing | completed | rejected
    method = Column(String, default="bank")  # bank | paypal | stripe
    reference = Column(String, nullable=True)  # bank ref / PayPal txn id
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    supplier = relationship("User")
