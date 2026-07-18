"""
Recovery script Phase 2b: Rebuild schemas.py (all 96 Pydantic schemas)
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(BASE)

def write_file(rel_path, content):
    fp = os.path.join(PROJECT, rel_path)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  RESTORED: {rel_path}")

write_file("backend/db/schemas.py", r'''"""Pydantic schemas for the ZOZI e-commerce platform."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field


T = TypeVar("T")


# ═════════════════════════════════════════════════════════════════════
#  GENERIC
# ═════════════════════════════════════════════════════════════════════
class MessageResponse(BaseModel):
    message: str


class ListPage(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20


# ═════════════════════════════════════════════════════════════════════
#  AUTH
# ═════════════════════════════════════════════════════════════════════
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    phone: Optional[str] = None
    role: str = "customer"
    referral_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# ═════════════════════════════════════════════════════════════════════
#  USER
# ═════════════════════════════════════════════════════════════════════
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: str = "en"
    preferred_currency: str = "SAR"
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


# Alias for admin.py: from db.schemas import User as UserSchema
User = UserOut


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None


class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class CreateStaffAccount(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    role: str = "staff"
    permissions: Optional[List[str]] = None


class UpdateStaffAccount(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None


class BulkUpdateStaffBody(BaseModel):
    user_ids: List[int]
    updates: dict


# ═════════════════════════════════════════════════════════════════════
#  ADDRESS
# ═════════════════════════════════════════════════════════════════════
class AddressCreate(BaseModel):
    label: str = "Home"
    full_name: str
    phone: Optional[str] = None
    street: str
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "SA"
    is_default: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    label: str
    full_name: str
    phone: Optional[str] = None
    street: str
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    is_default: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  CATEGORY
# ═════════════════════════════════════════════════════════════════════
class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  PRODUCT
# ═════════════════════════════════════════════════════════════════════
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    compare_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    currency: str = "SAR"
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None
    video_url: Optional[str] = None
    stock: int = 0
    weight: Optional[float] = None
    tags: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    visibility_regions: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    compare_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    currency: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None
    video_url: Optional[str] = None
    stock: Optional[int] = None
    weight: Optional[float] = None
    is_active: Optional[bool] = None
    tags: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    visibility_regions: Optional[str] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: int
    name: str
    slug: str
    description: Optional[str] = None
    price: Decimal
    compare_price: Optional[Decimal] = None
    currency: str
    sku: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None
    stock: int
    is_active: bool
    is_verified: bool
    moderation_status: str
    moderation_notes: Optional[str] = None
    badge: Optional[str] = None
    tags: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Alias for admin.py: from db.schemas import Product as ProductSchema
Product = ProductOut


class ProductListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    price: Decimal
    image_url: Optional[str] = None
    is_active: bool


# ═════════════════════════════════════════════════════════════════════
#  CART
# ═════════════════════════════════════════════════════════════════════
class CartItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = 1


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    product_id: int
    variant_id: Optional[int] = None
    quantity: int
    product: Optional[ProductListOut] = None
    created_at: Optional[datetime] = None


class CartOut(BaseModel):
    items: List[CartItemOut] = []
    subtotal: Decimal = Decimal("0")
    item_count: int = 0


# ═════════════════════════════════════════════════════════════════════
#  ORDER
# ═════════════════════════════════════════════════════════════════════
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    variant_id: Optional[int] = None


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    coupon_code: Optional[str] = None
    payment_method: Optional[str] = None
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    product_id: int
    supplier_id: Optional[int] = None
    product_name: str
    product_image: Optional[str] = None
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    customer_id: int
    status: str
    payment_status: str
    payment_method: Optional[str] = None
    payment_intent_id: Optional[str] = None
    payment_provider: Optional[str] = None
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    subtotal: Decimal
    discount_amount: Decimal
    vat_amount: Decimal = Decimal("0")
    shipping_amount: Decimal = Decimal("0")
    total: Decimal
    currency: str = "SAR"
    coupon_code: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[OrderItemOut] = []


# Alias for admin.py
Order = OrderOut


class OrderStatusUpdate(BaseModel):
    status: str


# ═════════════════════════════════════════════════════════════════════
#  PAYMENT
# ═════════════════════════════════════════════════════════════════════
class PaymentIntentCreate(BaseModel):
    order_id: int
    currency: str = "SAR"


class PaymentIntentOut(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: Decimal
    currency: str


# ═════════════════════════════════════════════════════════════════════
#  COUPON
# ═════════════════════════════════════════════════════════════════════
class CouponCreate(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str = "percentage"
    discount_value: Decimal
    maximum_discount: Optional[Decimal] = None
    minimum_order: Decimal = Decimal("0")
    usage_limit: Optional[int] = None
    is_active: bool = True
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    maximum_discount: Optional[Decimal] = None
    minimum_order: Decimal
    usage_limit: Optional[int] = None
    usage_count: int
    is_active: bool
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# Alias for admin.py
CouponSchema = CouponOut


class CouponValidateRequest(BaseModel):
    code: str
    order_total: Decimal


class CouponValidateResponse(BaseModel):
    valid: bool
    discount_amount: Decimal = Decimal("0")
    message: Optional[str] = None
    coupon: Optional[CouponOut] = None


# ═════════════════════════════════════════════════════════════════════
#  REVIEW
# ═════════════════════════════════════════════════════════════════════
class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    is_approved: bool
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  BANNER
# ═════════════════════════════════════════════════════════════════════
class BannerCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    image_url: str
    link_url: Optional[str] = None
    position: str = "home_hero"
    sort_order: int = 0
    is_active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    appearance: Optional[str] = None
    text_color: Optional[str] = None
    bg_color: Optional[str] = None


class BannerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    subtitle: Optional[str] = None
    image_url: str
    link_url: Optional[str] = None
    position: str
    sort_order: int
    is_active: bool
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  NOTIFICATION
# ═════════════════════════════════════════════════════════════════════
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    link: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  SUPPLIER PROFILE
# ═════════════════════════════════════════════════════════════════════
class SupplierProfileCreate(BaseModel):
    business_name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    city: Optional[str] = None
    country: str = "SA"
    operating_regions: Optional[str] = None
    tax_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_iban: Optional[str] = None


class SupplierProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    operating_regions: Optional[str] = None
    tax_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_iban: Optional[str] = None


class SupplierProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    business_name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    country: str
    verification_status: str
    is_active: bool
    badge: Optional[str] = None
    commission_override: Optional[Decimal] = None
    created_at: Optional[datetime] = None


class SupplierReturnReviewUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


# ═════════════════════════════════════════════════════════════════════
#  LOGISTICS PARTNER
# ═════════════════════════════════════════════════════════════════════
class LogisticsPartnerProfileCreate(BaseModel):
    company_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_areas: Optional[str] = None
    vehicle_types: Optional[str] = None
    origin_city: Optional[str] = None
    bank_name: Optional[str] = None
    bank_iban: Optional[str] = None


class LogisticsPartnerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    company_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_areas: Optional[str] = None
    vehicle_types: Optional[str] = None
    verification_status: str
    is_active: bool
    origin_city: Optional[str] = None
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  SHIPMENT
# ═════════════════════════════════════════════════════════════════════
class ShipmentCreate(BaseModel):
    order_id: int
    tracking_number: str
    carrier: Optional[str] = None
    logistics_partner_id: Optional[int] = None
    estimated_delivery: Optional[datetime] = None
    weight: Optional[float] = None
    package_count: int = 1
    notes: Optional[str] = None


class ShipmentUpdate(BaseModel):
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    status: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    weight: Optional[float] = None
    notes: Optional[str] = None


class ShipmentEventCreate(BaseModel):
    status: str
    location: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ShipmentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: int
    status: str
    location: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[datetime] = None


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    tracking_number: str
    carrier: Optional[str] = None
    status: str
    logistics_partner_id: Optional[int] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    weight: Optional[float] = None
    package_count: int
    notes: Optional[str] = None
    events: List[ShipmentEventOut] = []
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  RETURN REQUEST
# ═════════════════════════════════════════════════════════════════════
class ReturnRequestCreate(BaseModel):
    order_id: int
    reason: str


class ReturnRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    customer_id: int
    reason: str
    status: str
    resolution_notes: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  SUPPORT TICKET
# ═════════════════════════════════════════════════════════════════════
class TicketCreate(BaseModel):
    subject: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = "normal"


class TicketMessageCreate(BaseModel):
    content: str


class TicketMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    sender_id: int
    content: str
    is_staff: bool
    created_at: Optional[datetime] = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    subject: str
    description: Optional[str] = None
    status: str
    priority: str
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    messages: List[TicketMessageOut] = []


# ═════════════════════════════════════════════════════════════════════
#  FLASH SALE
# ═════════════════════════════════════════════════════════════════════
class FlashSaleItemCreate(BaseModel):
    product_id: int
    discount_percentage: Decimal
    max_quantity: Optional[int] = None


class FlashSaleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    starts_at: datetime
    ends_at: datetime
    items: List[FlashSaleItemCreate] = []


class FlashSaleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    flash_sale_id: int
    product_id: int
    discount_percentage: Decimal
    max_quantity: Optional[int] = None
    sold_count: int = 0


class FlashSaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    starts_at: datetime
    ends_at: datetime
    items: List[FlashSaleItemOut] = []
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  EMAIL CAMPAIGN
# ═════════════════════════════════════════════════════════════════════
class EmailCampaignCreate(BaseModel):
    name: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    audience: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    variant_label: Optional[str] = None


class EmailCampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    subject: str
    body_html: Optional[str] = None
    status: str
    audience: Optional[str] = None
    sent_count: int
    opened_count: int
    clicked_count: int
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    variant_label: Optional[str] = None
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  COMMISSION
# ═════════════════════════════════════════════════════════════════════
class CommissionCategoryRateCreate(BaseModel):
    category: str
    rate: Decimal
    is_active: bool = True


class CommissionCategoryRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: str
    rate: Decimal
    is_active: bool
    created_at: Optional[datetime] = None


class CommissionBadgeTierCreate(BaseModel):
    badge_name: str
    min_sales: int = 0
    rate_discount: Decimal = Decimal("0")
    monthly_fee: Decimal = Decimal("0")
    is_active: bool = True


class CommissionBadgeTierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    badge_name: str
    min_sales: int
    rate_discount: Decimal
    monthly_fee: Decimal
    is_active: bool
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  CASH MANAGEMENT
# ═════════════════════════════════════════════════════════════════════
class CashAccountCreate(BaseModel):
    name: str
    account_type: str = "operating"
    balance: Decimal = Decimal("0")
    currency: str = "SAR"
    is_active: bool = True
    description: Optional[str] = None


class CashAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    account_type: str
    balance: Decimal
    currency: str
    is_active: bool
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class CashTransactionCreate(BaseModel):
    account_id: int
    transaction_type: str
    amount: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None


class CashTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None
    performed_by: Optional[int] = None
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  PAYOUT
# ═════════════════════════════════════════════════════════════════════
class PayoutCreate(BaseModel):
    supplier_id: Optional[int] = None
    logistics_partner_id: Optional[int] = None
    amount: Decimal
    currency: str = "SAR"
    payout_method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PayoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: Optional[int] = None
    logistics_partner_id: Optional[int] = None
    amount: Decimal
    currency: str
    status: str
    payout_method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  REFERRAL
# ═════════════════════════════════════════════════════════════════════
class ReferralOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    referrer_id: int
    referral_code: str
    status: str
    total_referrals: int
    total_points: int
    created_at: Optional[datetime] = None


# ═════════════════════════════════════════════════════════════════════
#  AUDIT LOG
# ═════════════════════════════════════════════════════════════════════
class AuditLogSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None


class AuditLogPage(ListPage[AuditLogSchema]):
    pass


# ═════════════════════════════════════════════════════════════════════
#  FINANCE / CASH MANAGEMENT (advanced schemas)
# ═════════════════════════════════════════════════════════════════════
class FinancialSummaryOut(BaseModel):
    total_revenue: Decimal = Decimal("0")
    total_orders: int = 0
    total_commission: Decimal = Decimal("0")
    total_payouts: Decimal = Decimal("0")
    total_vat: Decimal = Decimal("0")
    net_income: Decimal = Decimal("0")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class LedgerEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entry_type: str
    amount: Decimal
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_at: Optional[datetime] = None


class ReconciliationSummaryOut(BaseModel):
    total_expected: Decimal = Decimal("0")
    total_received: Decimal = Decimal("0")
    discrepancy: Decimal = Decimal("0")
    unmatched_count: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class RefundLedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: Optional[int] = None
    amount: Decimal
    status: str
    reason: Optional[str] = None
    created_at: Optional[datetime] = None


class SupplierFinancialSummaryOut(BaseModel):
    supplier_id: int
    total_sales: Decimal = Decimal("0")
    total_commission: Decimal = Decimal("0")
    total_payouts: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")


class SupplierSettlementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: int
    amount: Decimal
    status: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: Optional[datetime] = None


class LogisticsFinancialSummaryOut(BaseModel):
    partner_id: int
    total_deliveries: int = 0
    total_earnings: Decimal = Decimal("0")
    total_payouts: Decimal = Decimal("0")
    balance: Decimal = Decimal("0")


class LogisticsSettlementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    partner_id: int
    amount: Decimal
    status: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: Optional[datetime] = None


class LogisticsCODRemittanceReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    partner_id: int
    amount: Decimal
    receipt_number: str
    status: str
    verified_at: Optional[datetime] = None
    proof_url: Optional[str] = None
    created_at: Optional[datetime] = None


class BadgeBillingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: int
    badge_tier_id: int
    amount: Decimal
    period_start: datetime
    period_end: datetime
    status: str
    created_at: Optional[datetime] = None


class BankTransactionCreate(BaseModel):
    amount: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None
    transaction_date: Optional[datetime] = None


class BankTransactionImportItem(BaseModel):
    amount: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None
    transaction_date: Optional[datetime] = None


class BankTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None
    status: str = "unmatched"
    transaction_date: Optional[datetime] = None
    created_at: Optional[datetime] = None


class BankTransactionResolutionIn(BaseModel):
    status: str
    notes: Optional[str] = None
    matched_order_id: Optional[int] = None


class FinanceBankSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    is_active: bool = False
    auto_reconcile: bool = False


class FinanceBankSettingsUpdate(BaseModel):
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    is_active: Optional[bool] = None
    auto_reconcile: Optional[bool] = None


class FinanceBankConnectionTestOut(BaseModel):
    connected: bool
    message: Optional[str] = None


class VATRemittanceCreate(BaseModel):
    period_start: datetime
    period_end: datetime
    total_vat: Decimal
    notes: Optional[str] = None


class VATRemittanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    period_start: datetime
    period_end: datetime
    total_vat: Decimal
    status: str
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# ─── Forward reference resolution ─────────────────────────────────
TokenResponse.model_rebuild()
CartItemOut.model_rebuild()
ShipmentOut.model_rebuild()
TicketOut.model_rebuild()
FlashSaleOut.model_rebuild()
OrderOut.model_rebuild()
''')

print("\n=== Phase 2b: schemas.py restored (96 schemas) ===")
