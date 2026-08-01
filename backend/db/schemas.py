"""Pydantic v2 schemas — ZOZI Marketplace."""
from __future__ import annotations
import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional, List, Any, Generic, TypeVar, Literal
from email_validator import EmailNotValidError, validate_email
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def _validate_email(value: str) -> str:
    # Like pydantic's EmailStr, but also allows RFC 2606 reserved/special-use
    # domains (.test, .example, .invalid, .localhost) so the test-suite can use
    # reserved domains without registration being rejected.
    if not isinstance(value, str):
        raise TypeError("string required")
    try:
        valid = validate_email(value, test_environment=True)
    except EmailNotValidError as exc:
        raise ValueError(str(exc))
    return valid.normalized


EmailStr = Annotated[
    str,
    AfterValidator(_validate_email),
    Field(json_schema_extra={"format": "email"}),
]


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Simple message response for status updates."""
    message: str = Field(description="Response message text")


class PaginatedResponse(BaseModel):
    """Standard paginated list response envelope.

    Used by all list endpoints to return paginated results with
    consistent metadata about the result set.
    """
    items: List[Any] = Field(description="List of items for the current page")
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number (1-based)", ge=1)
    size: int = Field(description="Number of items per page", ge=1, le=100)
    pages: int = Field(description="Total number of pages", ge=0)


# ── Auth ─────────────────────────────────────────────────────────────────────

PASSWORD_COMPLEXITY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?]).{8,}$"
)

def _validate_password_complexity(v: str) -> str:
    if not PASSWORD_COMPLEXITY_RE.match(v):
        raise ValueError(
            "Password must be at least 8 characters with at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character"
        )
    if len(v) > 72:
        import warnings
        warnings.warn(
            "Passwords longer than 72 characters are truncated to 72 characters by bcrypt.",
            UserWarning,
            stacklevel=2,
        )
    return v

class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password (min 8 chars)")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "customer"
    referral_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_complexity(v)

class TokenResponse(BaseModel):
    """JWT authentication token response."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: "UserOut" = Field(description="Authenticated user profile")

class RefreshRequest(BaseModel):
    refresh_token: str | None = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_complexity(v)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    def get_current_password(self) -> str:
        return self.current_password

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_complexity(v)


# ── Users ─────────────────────────────────────────────────────────────────────

class UserOut(OrmBase):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_email_verified: bool = False
    email_verified: bool = False
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    staff_permissions: Optional[Any] = None
    preferences: Optional[Any] = None
    referral_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _populate_is_email_verified(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "is_email_verified" not in data and "email_verified" in data:
                data["is_email_verified"] = data["email_verified"]
        elif hasattr(data, "email_verified") and not hasattr(data, "is_email_verified"):
            setattr(data, "is_email_verified", getattr(data, "email_verified"))
        return data

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Any] = None

class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_email_verified: Optional[bool] = None
    department: Optional[str] = None
    staff_permissions: Optional[Any] = None


def _normalize_image_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None

    normalized = str(path).strip().replace("\\", "/")
    if not normalized:
        return None
    if normalized.startswith(("http://", "https://", "data:", "/")):
        return normalized
    if normalized.startswith("uploads/"):
        return f"/{normalized}"
    return normalized


class CreateStaffAccount(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str
    role: str
    phone: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)
    staff_role_label: Optional[str] = None
    staff_title: Optional[str] = None
    staff_department: Optional[str] = None
    staff_area_of_operation: Optional[str] = None
    staff_hire_date: Optional[datetime] = None
    staff_experience_level: Optional[str] = None
    staff_performance_summary: Optional[str] = None
    staff_assigned_tasks: Optional[Any] = None
    staff_assigned_projects: Optional[Any] = None
    staff_notes: Optional[str] = None


class UpdateStaffAccount(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[list[str]] = None
    staff_role_label: Optional[str] = None
    staff_title: Optional[str] = None
    staff_department: Optional[str] = None
    staff_area_of_operation: Optional[str] = None
    staff_hire_date: Optional[datetime] = None
    staff_experience_level: Optional[str] = None
    staff_performance_summary: Optional[str] = None
    staff_assigned_tasks: Optional[Any] = None
    staff_assigned_projects: Optional[Any] = None
    staff_notes: Optional[str] = None


# ── Addresses ─────────────────────────────────────────────────────────────────

class AddressCreate(BaseModel):
    label: Optional[str] = None
    full_name: str
    phone: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"
    is_default: bool = False

class AddressOut(OrmBase):
    id: int
    label: Optional[str] = None
    full_name: str
    phone: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    is_default: bool
    created_at: datetime


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True
    is_featured: bool = False
    commission_rate: Optional[float] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    commission_rate: Optional[float] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class CategoryOut(OrmBase):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int
    is_active: bool
    is_featured: bool
    commission_rate: Optional[float] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ── Suppliers ─────────────────────────────────────────────────────────────────

class SupplierProfileCreate(BaseModel):
    business_name: str
    about_us: Optional[str] = None
    bio: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    business_type: Optional[str] = None
    tax_id: Optional[str] = None
    website: Optional[str] = None
    address: Optional[Any] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    phone_business: Optional[str] = None

class SupplierProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    about_us: Optional[str] = None
    bio: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    business_type: Optional[str] = None
    tax_id: Optional[str] = None
    website: Optional[str] = None
    address: Optional[Any] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    phone_business: Optional[str] = None
    verification_status: Optional[str] = None

class SupplierProfileOut(OrmBase):
    id: int
    user_id: int
    business_name: str
    slug: Optional[str] = None
    about_us: Optional[str] = None
    bio: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    business_type: Optional[str] = None
    tax_id: Optional[str] = None
    website: Optional[str] = None
    address: Optional[Any] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    verification_status: Optional[str] = None
    badge_level: Optional[str] = None
    credibility_score: Optional[int] = None
    is_active: bool = True
    is_terms_accepted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SupplierProfilePublicOut(OrmBase):
    id: int
    business_name: str
    slug: Optional[str] = None
    about_us: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    website: Optional[str] = None
    country_code: Optional[str] = None
    badge_level: Optional[str] = None
    credibility_score: Optional[int] = None
    is_active: bool = True


# ── Products ──────────────────────────────────────────────────────────────────

class ProductVariantCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    price: Optional[float] = None
    stock: int = 0
    attributes: Optional[Any] = None
    image_url: Optional[str] = None
    is_active: bool = True

class ProductVariantOut(OrmBase):
    id: int
    product_id: int
    name: Optional[str] = None
    title: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    pattern: Optional[str] = None
    gender: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    product_code: Optional[str] = None
    price: Optional[float] = None
    stock: int
    attributes: Optional[Any] = None
    image_url: Optional[str] = None
    media_url: Optional[str] = None
    is_active: bool
    sort_order: Optional[int] = None
    country_code: Optional[str] = None
    created_at: datetime

    @model_validator(mode='after')
    def derive_name_from_title(self) -> 'ProductVariantOut':
        if not self.name:
            self.name = self.title or ""
        return self

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    sku: Optional[str] = None
    price: float
    compare_price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: int = 0
    low_stock_threshold: int = 5
    weight: Optional[float] = None
    dimensions: Optional[Any] = None
    image_url: Optional[str] = None
    images: Optional[Any] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[Any] = None
    attributes: Optional[Any] = None
    is_active: bool = True
    is_featured: bool = False
    is_digital: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    variants: Optional[List[ProductVariantCreate]] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[float] = None
    compare_price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    weight: Optional[float] = None
    dimensions: Optional[Any] = None
    image_url: Optional[str] = None
    images: Optional[Any] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[Any] = None
    attributes: Optional[Any] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class ProductListOut(OrmBase):
    id: int
    name: str
    slug: Optional[str] = None
    short_description: Optional[str] = None
    price: float
    compare_price: Optional[float] = None
    stock: int
    image_url: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    is_active: bool
    is_featured: Optional[bool] = False
    moderation_status: Optional[str] = None
    badge: Optional[str] = None
    rating: float = 0.0
    rating_count: int = 0
    view_count: int = 0
    sales_count: int = 0
    offer_type: Optional[str] = None
    offer_title: Optional[str] = None
    offer_discount_pct: Optional[float] = None
    offer_starts_at: Optional[datetime] = None
    offer_ends_at: Optional[datetime] = None
    flash_sale_id: Optional[int] = None
    created_at: datetime

class ProductOut(OrmBase):
    id: int
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    sku: Optional[str] = None
    price: float
    compare_price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: int
    low_stock_threshold: Optional[int] = None
    weight: Optional[float] = None
    dimensions: Optional[Any] = None
    image_url: Optional[str] = None
    images: Optional[Any] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[Any] = None
    attributes: Optional[Any] = None
    supplier_id: Optional[int] = None
    is_active: bool
    is_featured: Optional[bool] = False
    is_digital: Optional[bool] = False
    is_verified: Optional[bool] = False
    moderation_status: Optional[str] = None
    moderation_notes: Optional[str] = None
    badge: Optional[str] = None
    view_count: int = 0
    sales_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    ai_tags: Optional[Any] = None
    ai_description: Optional[str] = None
    offer_type: Optional[str] = None
    offer_title: Optional[str] = None
    offer_discount_pct: Optional[float] = None
    offer_starts_at: Optional[datetime] = None
    offer_ends_at: Optional[datetime] = None
    flash_sale_id: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    slug_hash: Optional[str] = None
    variants: List[ProductVariantOut] = []

class PaginatedProducts(BaseModel):
    """Paginated list of products."""
    items: List[ProductListOut] = Field(description="Product list")
    total: int = Field(description="Total products")
    page: int = Field(description="Current page")
    size: int = Field(description="Page size")
    pages: int = Field(description="Total pages")


# ── Cart ──────────────────────────────────────────────────────────────────────

class CartItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = 1
    selected_size: Optional[str] = ""
    selected_color: Optional[str] = None

class CartItemOut(OrmBase):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    quantity: int
    available_stock: Optional[int] = None
    is_available: Optional[bool] = None
    availability_reason: Optional[str] = None
    product: Optional[ProductListOut] = None
    created_at: datetime

class CartOut(BaseModel):
    items: List[CartItemOut]
    total_items: int
    subtotal: float


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int
    selected_size: Optional[str] = None
    selected_color: Optional[str] = None

class OrderCreate(BaseModel):
    items: Optional[List[OrderItemCreate]] = None
    shipping_address_id: Optional[int] = None
    shipping_address: Optional[Any] = None
    billing_address: Optional[Any] = None
    delivery_location: Optional[Any] = None
    delivery_note: Optional[str] = None
    full_name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    customer_phone: Optional[str] = None
    save_to_profile: bool = False
    payment_method: Optional[str] = None
    coupon_code: Optional[str] = None
    notes: Optional[str] = None
    country_id: Optional[int] = None
    currency: Optional[str] = None
    tax_breakdown: Optional[dict[str, Any]] = None


class OrderPreviewOut(BaseModel):
    subtotal_amount: float
    discount_amount: float
    tax_amount: float
    vat_amount: float
    shipping_amount: float
    total_amount: float
    currency: str
    coupon_code: Optional[str] = None
    payment_method: str
    payment_gateway_code: Optional[str] = None
    payment_gateway_fee_amount: float
    payment_customer_total_amount: float
    payment_gateway_fee_passed_to_customer: bool
    country_id: Optional[int] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    shipment_groups: list[dict[str, Any]] = Field(default_factory=list)
    tax_breakdown: dict[str, Any] = Field(default_factory=dict)

class OrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class OrderItemOut(OrmBase):
    id: int
    product_id: Optional[int] = None
    product_name: str
    product_image: Optional[str] = None
    variant_info: Optional[Any] = None
    quantity: int
    unit_price: float
    total_price: float
    commission_amount: Optional[float] = None
    commission_rate: Optional[float] = None

class OrderOut(OrmBase):
    id: int
    order_number: Optional[str] = None
    customer_id: Optional[int] = None
    status: str
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_provider: Optional[str] = None
    shipping_address: Optional[Any] = None
    billing_address: Optional[Any] = None
    subtotal: Optional[float] = None
    shipping_fee: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    total: Optional[float] = None
    currency: Optional[str] = None
    coupon_code: Optional[str] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    fraud_score: int = 0
    fraud_action: Optional[str] = "allow"
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    items: List[OrderItemOut] = []

class OrderListOut(OrmBase):
    id: int
    order_number: str
    status: str
    payment_status: str
    total: float
    currency: str
    created_at: datetime
    items: List[OrderItemOut] = []

class PaginatedOrders(BaseModel):
    """Paginated list of orders."""
    items: List[OrderListOut] = Field(description="Order list")
    total: int = Field(description="Total orders")
    page: int = Field(description="Current page")
    size: int = Field(description="Page size")
    pages: int = Field(description="Total pages")


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentIntentCreate(BaseModel):
    order_id: int
    provider: str = "stripe"

class PaymentIntentOut(BaseModel):
    client_secret: Optional[str] = None
    payment_intent_id: Optional[str] = None
    provider: str


# ── Shipments ─────────────────────────────────────────────────────────────────

class ShipmentCreate(BaseModel):
    order_id: int
    logistics_partner_id: Optional[int] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    carrier_tracking_url: Optional[str] = None
    pickup_address: Optional[Any] = None
    delivery_address: Optional[Any] = None
    estimated_delivery: Optional[datetime] = None
    shipping_fee: Optional[float] = None
    cod_amount: Optional[float] = None
    is_cod: bool = False
    notes: Optional[str] = None

class ShipmentUpdate(BaseModel):
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    carrier_tracking_url: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    delivery_proof_url: Optional[str] = None
    notes: Optional[str] = None

class ShipmentEventCreate(BaseModel):
    status: str
    description: Optional[str] = None
    location: Optional[str] = None

class ShipmentEventOut(OrmBase):
    id: int
    status: str
    description: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

class ShipmentOut(OrmBase):
    id: int
    order_id: int
    logistics_partner_id: Optional[int] = None
    tracking_number: Optional[str] = None
    status: str
    carrier: Optional[str] = None
    carrier_tracking_url: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    delivery_proof_url: Optional[str] = None
    shipping_fee: Optional[float] = None
    cod_amount: Optional[float] = None
    is_cod: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    events: List[ShipmentEventOut] = []


# ── Reviews ───────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    product_id: int
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    images: Optional[Any] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v

class ReviewOut(OrmBase):
    id: int
    product_id: int
    user_id: int
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    is_approved: bool
    created_at: datetime


# ── Coupons ───────────────────────────────────────────────────────────────────

class CouponCreate(BaseModel):
    code: str
    title: Optional[str] = None
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    maximum_discount: Optional[float] = None
    minimum_order: float = 0
    usage_limit: Optional[int] = None
    per_user_limit: Optional[int] = None
    applicable_to: Optional[Any] = None
    is_active: bool = True
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class CouponOut(OrmBase):
    id: int
    code: str
    title: Optional[str] = None
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    maximum_discount: Optional[float] = None
    minimum_order: float = 0
    usage_limit: Optional[int] = None
    usage_count: int = 0
    per_user_limit: Optional[int] = None
    applicable_to: Optional[Any] = None
    is_active: bool
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

class CouponValidateRequest(BaseModel):
    code: str
    order_subtotal: float

class CouponValidateResponse(BaseModel):
    valid: bool
    discount_amount: float
    message: Optional[str] = None
    coupon: Optional[CouponOut] = None


CouponSchema = CouponOut


# ── Supplier Documents ─────────────────────────────────────────────────────────

class SupplierDocumentOut(OrmBase):
    id: int
    supplier_id: int
    document_type: str
    document_url: str
    status: str
    review_note: Optional[str] = None
    reviewed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── Banners ───────────────────────────────────────────────────────────────────

class BannerCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    image_url: str
    mobile_image_url: Optional[str] = None
    link_url: Optional[str] = None
    position: str = "hero"
    sort_order: int = 0
    is_active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

class BannerOut(OrmBase):
    id: int
    title: str
    subtitle: Optional[str] = None
    image_url: str
    mobile_image_url: Optional[str] = None
    link_url: Optional[str] = None
    position: str
    sort_order: int
    is_active: bool
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_at: datetime


# ── Flash Sales ───────────────────────────────────────────────────────────────

class FlashSaleItemCreate(BaseModel):
    product_id: int
    sale_price: float
    stock_limit: Optional[int] = None

class FlashSaleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    banner_url: Optional[str] = None
    discount_pct: float = 0
    discount_type: str = "percentage"
    discount_value: float = 0
    starts_at: datetime
    ends_at: datetime
    is_active: bool = True
    product_ids: Optional[List[int]] = None
    items: Optional[List[FlashSaleItemCreate]] = None

class FlashSaleItemOut(OrmBase):
    id: int
    product_id: int
    sale_price: float
    stock_limit: Optional[int] = None
    sold_count: int

class FlashSaleOut(OrmBase):
    id: int
    title: str
    description: Optional[str] = None
    banner_url: Optional[str] = None
    discount_pct: float = 0
    discount_type: str = "percentage"
    discount_value: float = 0
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    product_ids: Optional[List[int]] = None
    created_at: datetime
    items: List[FlashSaleItemOut] = []

    @field_validator("product_ids", mode="before")
    @classmethod
    def normalize_product_ids(cls, value: Any) -> Optional[List[int]]:
        if value in (None, ""):
            return None
        if isinstance(value, list):
            normalized: List[int] = []
            for item in value:
                try:
                    normalized.append(int(item))
                except (TypeError, ValueError):
                    continue
            return normalized
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return None
            if not isinstance(parsed, list):
                return None
            normalized = []
            for item in parsed:
                try:
                    normalized.append(int(item))
                except (TypeError, ValueError):
                    continue
            return normalized
        return None


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationOut(OrmBase):
    id: int
    title: str
    body: Optional[str] = None
    type: str
    link_url: Optional[str] = None
    is_read: bool
    data: Optional[Any] = None
    created_at: datetime


NotificationSchema = NotificationOut


# ── Support Tickets ───────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    subject: str
    body: str
    category: Optional[str] = None
    priority: str = "normal"
    order_id: Optional[int] = None

class TicketMessageCreate(BaseModel):
    body: str
    attachments: Optional[Any] = None
    is_internal: bool = False

class TicketMessageOut(OrmBase):
    id: int
    ticket_id: int
    sender_id: int
    body: str
    attachments: Optional[Any] = None
    is_internal: bool
    created_at: datetime

class TicketOut(OrmBase):
    id: int
    ticket_number: str
    user_id: int
    subject: str
    body: str
    category: Optional[str] = None
    priority: str
    status: str
    assigned_to: Optional[int] = None
    order_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    messages: List[TicketMessageOut] = []


# ── Returns ───────────────────────────────────────────────────────────────────

class ReturnRequestCreate(BaseModel):
    order_id: int
    order_item_id: Optional[int] = None
    intent: str = "return"
    reason: str
    description: Optional[str] = None
    images: Optional[Any] = None

class ReturnRequestOut(OrmBase):
    id: int
    order_id: int
    order_item_id: Optional[int] = None
    customer_id: int
    intent: str = "return"
    reason: str
    description: Optional[str] = None
    images: Optional[Any] = None
    status: str
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None
    refund_amount: Optional[float] = None
    items: Optional[Any] = None
    return_window_days: Optional[int] = None
    delivered_at: Optional[datetime] = None
    return_deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ── Commission ────────────────────────────────────────────────────────────────

class CommissionCategoryRateCreate(BaseModel):
    category_id: Optional[int] = None
    category_slug: Optional[str] = None
    category_display_name: Optional[str] = None
    rate: float
    is_active: bool = True

class CommissionCategoryRateOut(OrmBase):
    id: int
    category_id: Optional[int] = None
    category_slug: Optional[str] = None
    category_display_name: Optional[str] = None
    rate_percent: float = 0
    rate: float = 0
    is_active: bool = True
    country_code: Optional[str] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _sync_rate(cls, obj):
        # The ORM column is `rate_percent`; expose it as `rate` for the UI.
        if hasattr(obj, "rate_percent"):
            try:
                obj.rate = float(obj.rate_percent)
            except (TypeError, ValueError):
                obj.rate = 0.0
        elif isinstance(obj, dict):
            if "rate" not in obj and "rate_percent" in obj:
                obj["rate"] = obj["rate_percent"]
        return obj

class CommissionBadgeTierCreate(BaseModel):
    badge_level: str
    commission_rate: float
    min_fulfilled_orders: Optional[int] = 0
    is_active: bool = True

class CommissionBadgeTierOut(OrmBase):
    id: int
    name: Optional[str] = None
    badge_level: str
    commission_rate: float
    min_fulfilled_orders: Optional[int] = 0
    min_monthly_revenue: Optional[float] = None
    is_active: bool = True
    country_code: Optional[str] = None
    created_at: datetime


# ── Payouts ───────────────────────────────────────────────────────────────────

class PayoutCreate(BaseModel):
    supplier_id: int
    amount: float
    currency: str = "USD"
    method: str = "bank_transfer"
    reference: Optional[str] = None
    bank_account_id: Optional[int] = None
    notes: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

class PayoutOut(OrmBase):
    id: int
    supplier_id: int
    amount: float
    currency: str
    status: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[int] = None


# ── Cash Management ───────────────────────────────────────────────────────────

class CashAccountCreate(BaseModel):
    name: str
    account_type: str
    currency: str = "USD"
    description: Optional[str] = None

class CashAccountOut(OrmBase):
    id: int
    name: str
    account_type: str
    currency: str
    balance: float
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

class CashTransactionCreate(BaseModel):
    account_id: int
    transaction_type: str
    amount: float
    description: Optional[str] = None
    reference: Optional[str] = None
    category: Optional[str] = None

class CashTransactionOut(OrmBase):
    id: int
    account_id: int
    transaction_type: str
    amount: float
    balance_after: float
    description: Optional[str] = None
    reference: Optional[str] = None
    category: Optional[str] = None
    performed_by: Optional[int] = None
    created_at: datetime


# ── General Ledger ─────────────────────────────────────────────────────────

class JournalLineInput(BaseModel):
    account_code: str
    side: Literal["debit", "credit"]
    amount: Decimal = Field(gt=0)
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class JournalEntryCreate(BaseModel):
    entry_date: datetime
    reference_type: str
    reference_id: int
    reference_number: Optional[str] = None
    description: str
    currency: str = "OMR"
    country_code: Optional[str] = None
    lines: List[JournalLineInput]

class AccountOut(OrmBase):
    id: int
    code: str
    name: str
    group_name: Optional[str] = None
    normal_side: str
    currency: str
    is_active: bool

class AccountBalanceOut(OrmBase):
    account_code: str
    account_name: str
    group_name: Optional[str] = None
    normal_side: str
    currency: str
    balance: Decimal

class TrialBalanceOut(BaseModel):
    as_of: datetime
    accounts: List[AccountBalanceOut]
    total_debit_balances: Decimal
    total_credit_balances: Decimal

class JournalEntryLineOut(OrmBase):
    id: int
    account_code: str
    account_name: str
    side: str
    amount: Decimal
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    country_code: Optional[str] = None

class JournalEntryOut(OrmBase):
    id: int
    entry_date: datetime
    reference_type: str
    reference_id: int
    reference_number: Optional[str] = None
    description: str
    currency: str
    country_code: Optional[str] = None
    is_reconciled: bool
    created_by: Optional[int] = None
    created_at: datetime
    lines: List[JournalEntryLineOut]


# ── Treasury ───────────────────────────────────────────────────────────────

class TreasuryAccountCreate(BaseModel):
    slug: str
    name: str
    account_type: str
    currency: str = "OMR"
    gl_account_code: Optional[str] = None
    description: Optional[str] = None

class CashFlowForecastCreate(BaseModel):
    forecast_date: date
    currency: str = "OMR"
    forecast_category: str
    forecast_type: str
    expected_amount: Decimal
    confidence: str = "medium"
    source_entity: Optional[str] = None
    source_id: Optional[int] = None
    description: Optional[str] = None
    expected_settlement_date: Optional[date] = None

class GatewaySettlementCreate(BaseModel):
    gateway_code: str
    order_id: int
    transaction_id: str
    amount: Decimal = Field(gt=0)
    currency: str = "OMR"
    gateway_fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    transaction_date: datetime
    expected_settlement_date: date

class TreasuryTransferCreate(BaseModel):
    from_account_slug: str
    to_account_slug: str
    amount: Decimal = Field(gt=0)
    currency: str = "OMR"
    transaction_type: str = "transfer"
    description: Optional[str] = None

class TreasuryAccountOut(OrmBase):
    id: int
    slug: str
    name: str
    account_type: str
    currency: str
    gl_account_code: Optional[str] = None
    balance: Decimal
    is_active: bool

class CashPositionSnapshotOut(OrmBase):
    id: int
    snapshot_date: date
    currency: str
    cash_operating: Decimal
    cash_gateway_settlement: Decimal
    reserve_supplier_payable: Decimal
    reserve_logistics_payable: Decimal
    reserve_refund: Decimal
    reserve_vat: Decimal
    reserve_commission: Decimal
    receivable_customer: Decimal
    total_cash: Decimal
    total_reserves: Decimal
    free_cash: Decimal
    net_working_capital: Decimal

class CashFlowForecastOut(OrmBase):
    id: int
    forecast_date: date
    currency: str
    forecast_category: str
    forecast_type: str
    expected_amount: Decimal
    confidence: str
    source_entity: Optional[str] = None
    source_id: Optional[int] = None
    description: Optional[str] = None
    expected_settlement_date: Optional[date] = None

class GatewaySettlementScheduleOut(OrmBase):
    id: int
    gateway_code: str
    order_id: int
    transaction_id: str
    amount: Decimal
    currency: str
    gateway_fee: Decimal
    net_amount: Decimal
    status: str
    expected_settlement_date: date
    settled_at: Optional[datetime] = None
    created_at: datetime

class TreasuryDashboardOut(BaseModel):
    current_position: Optional[CashPositionSnapshotOut] = None
    pending_settlements: Decimal
    pending_payouts: Decimal
    free_cash: Decimal
    reserves_breakdown: dict[str, Decimal]
    forecast: List[CashFlowForecastOut]
    recent_journal_entries: List[JournalEntryOut]


# ── Email Campaigns ───────────────────────────────────────────────────────────

class EmailCampaignCreate(BaseModel):
    name: str
    subject: str
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    recipients: Optional[Any] = None
    target_audience: Optional[Any] = None
    audience: Optional[Any] = None
    scheduled_at: Optional[datetime] = None
    send_at: Optional[datetime] = None
    template_id: Optional[int] = None
    subject_b: Optional[str] = None
    ab_test_enabled: bool = False
    status: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_audience_aliases(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if payload.get("target_audience") is None and payload.get("audience") is None:
            recipients = payload.get("recipients")
            if recipients is not None:
                payload["audience"] = recipients
        return payload

class EmailCampaignOut(OrmBase):
    id: int
    name: str
    subject: str
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    target_audience: Optional[Any] = None
    status: str
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    sent_count: Optional[int] = 0
    open_count: Optional[int] = 0
    click_count: Optional[int] = 0
    created_at: datetime
    created_by: Optional[int] = None


# ── Logistics ─────────────────────────────────────────────────────────────────

class LogisticsPartnerProfileCreate(BaseModel):
    company_name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_areas: Optional[Any] = None
    vehicle_types: Optional[Any] = None
    max_weight_kg: Optional[float] = None
    base_rate: Optional[float] = None
    per_km_rate: Optional[float] = None
    bank_account: Optional[Any] = None

class LogisticsPartnerProfileOut(OrmBase):
    id: int
    user_id: int
    company_name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_areas: Optional[Any] = None
    vehicle_types: Optional[Any] = None
    max_weight_kg: Optional[float] = None
    base_rate: Optional[float] = None
    per_km_rate: Optional[float] = None
    verification_status: str
    rating: float
    is_active: bool
    bank_account: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


# Email / Newsletter schemas
class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    template_type: Optional[str] = None
    variables: Optional[Any] = None
    is_active: bool = True


class EmailTemplateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    template_type: Optional[str] = None
    variables: Optional[Any] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EmailCampaignSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    status: str = "draft"
    audience: Optional[str] = None
    target_audience: Optional[str] = None
    template_id: Optional[int] = None
    sent_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    subject_b: Optional[str] = None
    ab_test_enabled: bool = False
    ab_winner_variant: Optional[str] = None
    created_at: Optional[datetime] = None


class EmailCampaignUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    recipients: Optional[str] = None
    audience: Optional[str] = None
    target_audience: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    send_at: Optional[datetime] = None
    template_id: Optional[int] = None
    subject_b: Optional[str] = None
    ab_test_enabled: Optional[bool] = None
    variant_label: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_update_audience_aliases(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if payload.get("target_audience") is None and payload.get("audience") is None:
            recipients = payload.get("recipients")
            if recipients is not None:
                payload["audience"] = recipients
        return payload


class EmailProviderConfigSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    provider: str
    active_provider: Optional[str] = None
    source: Optional[str] = None
    available: bool = False
    live: bool = False
    preview_only: bool = False
    supports_webhooks: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_use_ssl: Optional[bool] = None
    smtp_timeout_seconds: Optional[int] = None
    email_from_default: Optional[str] = None
    email_from_promotional: Optional[str] = None
    email_from_transactional: Optional[str] = None
    email_from_notification: Optional[str] = None
    email_from_alert: Optional[str] = None
    email_from_verification: Optional[str] = None
    email_from_login_verification: Optional[str] = None
    email_from_password_reset: Optional[str] = None
    resend_api_key_configured: bool = False
    resend_webhook_secret_configured: bool = False
    smtp_password_configured: bool = False
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EmailProviderConfigUpdate(BaseModel):
    provider: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_use_ssl: Optional[bool] = None
    smtp_timeout_seconds: Optional[int] = None
    email_from_default: Optional[str] = None
    email_from_promotional: Optional[str] = None
    email_from_transactional: Optional[str] = None
    email_from_notification: Optional[str] = None
    email_from_alert: Optional[str] = None
    email_from_verification: Optional[str] = None
    email_from_login_verification: Optional[str] = None
    email_from_password_reset: Optional[str] = None
    resend_api_key: Optional[str] = None
    resend_webhook_secret: Optional[str] = None


class EmailTestSendRequest(BaseModel):
    to_email: str
    subject: Optional[str] = None
    body_html: Optional[str] = None
    html_content: Optional[str] = None
    template_id: Optional[int] = None
    purpose: str = "default"


class NewsletterSubscriberCreate(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferences: Optional[dict] = None


class NewsletterSubscriberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_subscribed: bool = True
    preferences: Optional[dict] = None
    created_at: Optional[datetime] = None


class CampaignAnalytics(BaseModel):
    campaign_id: int
    sent_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    unsubscribed_count: int = 0
    bounced_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0


# ─── [recovery] Missing schema stubs appended for compatibility ───────────────
# These permissive stubs keep imports working; tighten fields over time.


class _PermissiveBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")


# Re-use existing Out schemas where sensible
User = UserOut
Order = OrderOut
Product = ProductOut


class BulkUpdateStaffBody(BaseModel):
    user_ids: List[int] = Field(default_factory=list)
    updates: UpdateStaffAccount


class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_complexity(v)
    phone: Optional[str] = None
    role: Optional[str] = "customer"
    referral_code: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    country: Optional[str] = None
    website_url: Optional[str] = None
    trade_license_no: Optional[str] = None
    tax_reg_no: Optional[str] = None
    instagram_handle: Optional[str] = None
    terms_accepted: bool = False
    business_type: Optional[str] = None
    country: Optional[str] = None
    website_url: Optional[str] = None
    trade_license_no: Optional[str] = None
    tax_reg_no: Optional[str] = None
    instagram_handle: Optional[str] = None


class ProfileUpdate(_PermissiveBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address_book: Optional[Any] = None
    profile_image: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None
    preferred_country: Optional[str] = None


class AddressUpdate(_PermissiveBase):
    label: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    is_default: Optional[bool] = None


_ListPageItem = TypeVar("_ListPageItem")


class ListPage(BaseModel, Generic[_ListPageItem]):
    """Generic paginated list wrapper."""
    model_config = ConfigDict(from_attributes=True, extra="allow")
    data: List[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    pageSize: int = 20


_CursorPageItem = TypeVar("_CursorPageItem")


class CursorPage(BaseModel, Generic[_CursorPageItem]):
    """Cursor-based pagination response.

    Use cursor (nextCursor) to fetch subsequent pages.
    Pass nextCursor as 'cursor' query parameter for next page.
    """

    model_config = ConfigDict(from_attributes=True, extra="allow")
    items: List[Any] = Field(default_factory=list)
    nextCursor: Optional[str] = None
    hasMore: bool = False
    pageSize: int = 20


# Audit log
class AuditLogSchema(_PermissiveBase):
    id: Optional[int] = None
    action: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Any] = None
    status: Optional[str] = None
    occurred_at: Optional[datetime] = None


class AuditLogPage(BaseModel):
    data: List[AuditLogSchema] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    pageSize: int = 20
    unique_actions: List[str] = Field(default_factory=list)


# Category
class CategorySchema(_PermissiveBase):
    id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = True


# Bank transactions
class BankTransactionCreate(_PermissiveBase):
    bank_account_id: Optional[int] = None
    amount: Decimal = Decimal("0.00")
    currency: str = "OMR"
    direction: str = "credit"
    reference: Optional[str] = None
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None


class BankTransactionImportItem(_PermissiveBase):
    reference: Optional[str] = None
    amount: Decimal = Decimal("0.00")
    currency: str = "OMR"
    direction: str = "credit"
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None


class BankTransactionOut(_PermissiveBase):
    id: Optional[int] = None
    bank_account_id: Optional[int] = None
    transaction_ref: Optional[str] = None
    source: Optional[str] = None
    transaction_type: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    linked_order_id: Optional[int] = None
    linked_supplier_id: Optional[int] = None
    linked_logistics_id: Optional[int] = None
    linked_payout_id: Optional[int] = None
    linked_refund_id: Optional[int] = None
    reconciled: Optional[bool] = False
    reconciled_at: Optional[datetime] = None
    reconciled_by: Optional[int] = None
    flagged: Optional[bool] = False
    flag_reason: Optional[str] = None
    transaction_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    direction: Optional[str] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    resolved: Optional[bool] = False


class BankTransactionResolutionIn(_PermissiveBase):
    resolved: bool = True
    notes: Optional[str] = None


# Badge billing
class BadgeBillingOut(_PermissiveBase):
    id: Optional[int] = None
    supplier_id: Optional[int] = None
    badge_tier_id: Optional[int] = None
    amount: Optional[Decimal] = None
    billed_at: Optional[datetime] = None


# Campaign recipient
class CampaignRecipientSchema(_PermissiveBase):
    id: Optional[int] = None
    campaign_id: Optional[int] = None
    user_id: Optional[int] = None
    email: Optional[str] = None
    status: Optional[str] = None


# Coupon validation
class CouponValidate(BaseModel):
    code: str
    order_total: Optional[Decimal] = None


# Finance bank
class FinanceBankConnectionTestOut(_PermissiveBase):
    success: bool = False
    message: Optional[str] = None


class FinanceBankSettingsOut(_PermissiveBase):
    id: Optional[int] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    currency: Optional[str] = None


class FinanceBankSettingsUpdate(_PermissiveBase):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    currency: Optional[str] = None


class FinancialSummaryOut(_PermissiveBase):
    total_revenue: Optional[Decimal] = None
    total_expenses: Optional[Decimal] = None
    net: Optional[Decimal] = None


class LogisticsCODRemittanceReceiptOut(_PermissiveBase):
    id: Optional[int] = None
    partner_id: Optional[int] = None
    amount: Optional[Decimal] = None
    received_at: Optional[datetime] = None


class LogisticsFinancialSummaryOut(_PermissiveBase):
    total_cod_collected: Optional[Decimal] = None
    total_settlements: Optional[Decimal] = None


class LogisticsSettlementOut(_PermissiveBase):
    id: Optional[int] = None
    partner_id: Optional[int] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None


class SupplierFinancialSummaryOut(_PermissiveBase):
    supplier_id: Optional[int] = None
    total_sales: Optional[Decimal] = None
    total_payouts: Optional[Decimal] = None


class SupplierReturnReviewUpdate(_PermissiveBase):
    status: Optional[str] = None
    notes: Optional[str] = None


class SupplierSettlementOut(_PermissiveBase):
    id: Optional[int] = None
    supplier_id: Optional[int] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None


class LedgerEntryOut(_PermissiveBase):
    id: Optional[int] = None
    entry_type: Optional[str] = None
    amount: Optional[Decimal] = None
    reference: Optional[str] = None
    created_at: Optional[datetime] = None


class OrderItemBase(_PermissiveBase):
    product_id: int
    quantity: int = 1


class ReconciliationSummaryOut(_PermissiveBase):
    matched: int = 0
    unmatched: int = 0
    total: int = 0


class ReferralDashboardSchema(_PermissiveBase):
    total_referrals: int = 0
    total_points: int = 0
    recent_events: List[Any] = Field(default_factory=list)


class ReferralPointEventSchema(_PermissiveBase):
    id: Optional[int] = None
    user_id: Optional[int] = None
    points: Optional[int] = None
    event_type: Optional[str] = None
    created_at: Optional[datetime] = None


class ReferralShareRequest(BaseModel):
    channel: Optional[str] = None
    target_email: Optional[EmailStr] = None


class RefundLedgerOut(_PermissiveBase):
    id: Optional[int] = None
    order_id: Optional[int] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None


class ReturnRequestUpdate(_PermissiveBase):
    status: Optional[str] = None
    notes: Optional[str] = None
    resolution_notes: Optional[str] = None


class VATRemittanceCreate(_PermissiveBase):
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    amount_remitted: Decimal = Decimal("0.00")
    transaction_ref: Optional[str] = None
    remitted_at: Optional[datetime] = None
    notes: Optional[str] = None
    # Legacy compatibility fields.
    period: Optional[str] = None
    amount: Optional[Decimal] = None

    @model_validator(mode="after")
    def apply_legacy_amount_aliases(self) -> "VATRemittanceCreate":
        if self.amount is not None and (self.amount_remitted is None or self.amount_remitted == Decimal("0.00")):
            self.amount_remitted = self.amount
        return self


class VATRemittanceOut(_PermissiveBase):
    id: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    vat_collected_amount: Optional[float] = None
    vat_adjustment_amount: Optional[float] = None
    amount_due: Optional[float] = None
    amount_remitted: Optional[float] = None
    period: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    bank_transaction_id: Optional[int] = None
    remitted_at: Optional[datetime] = None
    remitted_by: Optional[int] = None
    notes: Optional[str] = None
    currency: Optional[str] = None
    created_at: Optional[datetime] = None

    @model_validator(mode="after")
    def apply_legacy_period_amount_fields(self) -> "VATRemittanceOut":
        if self.period_start and self.period_end and not self.period:
            self.period = f"{self.period_start.date().isoformat()} to {self.period_end.date().isoformat()}"
        if self.amount is None and self.amount_remitted is not None:
            self.amount = self.amount_remitted
        return self


# ── Admin Archive / Restore / Bulk Operations ────────────────────────────────

class ArchiveRequest(BaseModel):
    reason: Optional[str] = None


class RestoreRequest(BaseModel):
    pass


class BulkActionRequest(BaseModel):
    ids: List[int]
    reason: Optional[str] = None


class BulkCategoryChangeRequest(BaseModel):
    ids: List[int]
    category_id: int
    reason: Optional[str] = None


class BulkStatusUpdateRequest(BaseModel):
    ids: List[int]
    status: str
    reason: Optional[str] = None


class HardDeleteRequest(BaseModel):
    ids: List[int]
    reason: Optional[str] = None


class BulkArchiveRestoreResponse(BaseModel):
    archived: int = 0
    restored: int = 0
    errors: List[dict] = []


class BulkActionResponse(BaseModel):
    success_count: int = 0
    error_count: int = 0
    errors: List[dict] = []


# ── Fraud Detection ─────────────────────────────────────────────────────────────

class FraudScoreRequest(BaseModel):
    user_id: Optional[int] = None
    ip_address: str
    device_hash: Optional[str] = None
    event_type: str
    amount: Optional[float] = None
    headers: Optional[dict[str, str]] = None


class FraudScoreResponse(BaseModel):
    score: int
    triggered_rules: List[str] = []
    is_blocked: bool = False
    is_review: bool = False
    action: str


class FraudEventOut(OrmBase):
    id: int
    user_id: Optional[int] = None
    event_type: str
    ip_address: Optional[str] = None
    device_hash: Optional[str] = None
    session_id: Optional[str] = None
    fraud_score: int
    triggered_rules: Optional[List[str]] = None
    details: Optional[dict[str, Any]] = None
    status: str
    created_at: datetime


class FraudBlacklistCreate(BaseModel):
    entity_type: str
    entity_value: str
    reason: str
    expires_at: Optional[datetime] = None


class FraudBlacklistOut(OrmBase):
    id: int
    entity_type: str
    entity_value: str
    entity_value_hash: str
    reason: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime


class FraudRuleCreate(BaseModel):
    rule_key: str
    name: str
    description: Optional[str] = None
    weight: int = Field(default=10, ge=0, le=100)
    condition_json: Optional[dict[str, Any]] = None
    is_active: bool = True
    is_global: bool = True
    country_code: Optional[str] = None


class FraudRuleOut(OrmBase):
    id: int
    rule_key: str
    name: str
    description: Optional[str] = None
    weight: int
    condition_json: Optional[dict[str, Any]] = None
    is_active: bool
    is_global: bool
    country_code: Optional[str] = None
    created_at: datetime


class ManualReviewOut(OrmBase):
    id: int
    entity_type: str
    entity_id: int
    fraud_score: int
    triggered_rules: Optional[List[str]] = None
    reason: str
    priority: str
    status: str
    assigned_to: Optional[int] = None
    admin_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    created_at: datetime


class ManualReviewAssign(BaseModel):
    admin_notes: Optional[str] = None


class ManualReviewResolve(BaseModel):
    status: str
    admin_notes: Optional[str] = None


class IPReputationOut(OrmBase):
    id: int
    ip_address: str
    is_proxy: bool
    is_vpn: bool
    is_tor: bool
    is_hosting: bool
    asn: Optional[str] = None
    country_code: Optional[str] = None
    reputation_score: int
    updated_at: datetime


class DeviceFingerprintOut(OrmBase):
    id: int
    fingerprint_hash: str
    user_id: Optional[int] = None
    risk_score: int
    is_trusted: bool
    is_blocked: bool
    headless_attempts: int
    account_count: int
    first_seen_at: datetime
    last_seen_at: datetime


class ThreatFeedStatus(BaseModel):
    tor_count: int
    proxy_count: int
    hosting_asn_count: int
    last_updated: Optional[datetime] = None


class FraudDashboardStats(BaseModel):
    total_events_24h: int
    blocked_events_24h: int
    review_queue_count: int
    blacklisted_ips: int


class ImpossibleTravelCheck(BaseModel):
    is_impossible: bool
    distance_km: Optional[float] = None
    speed_kmh: Optional[float] = None
    previous_ip: Optional[str] = None
    current_ip: Optional[str] = None


class DeviceStackingCheck(BaseModel):
    account_count: int
    risk_level: str


class ReturnAbuseCheck(BaseModel):
    return_rate: float
    total_orders: int
    total_returns: int
    is_abuse: bool


class FraudScoreRequest(BaseModel):
    user_id: Optional[int] = None
    ip_address: str
    device_hash: Optional[str] = None
    event_type: str
    amount: Optional[float] = None
    headers: Optional[dict[str, str]] = None
    additional_signals: Optional[dict[str, Any]] = None


class FraudScoreResponse(BaseModel):
    score: int
    triggered_rules: List[str] = []
    is_blocked: bool = False
    is_review: bool = False
    action: str


class IPAccountCheck(BaseModel):
    account_count: int
    device_count: int
    user_device_count: int
    is_suspicious: bool


class BINCheck(BaseModel):
    is_blacklisted: bool
    bin_info: Optional[dict[str, str]] = None
    country_mismatch: bool


class LogisticsFraudCheck(BaseModel):
    gps_mismatch: bool
    time_anomaly: bool
    missing_proof: bool
    score: int




