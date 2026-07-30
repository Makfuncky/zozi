from pydantic import BaseModel, validator, field_validator
from typing import Optional, List
from datetime import datetime
import re

PASSWORD_COMPLEXITY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?]).{8,}$"
)


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    brand: Optional[str] = None
    rating: Optional[float] = 0.0
    image_url: Optional[str] = None
    stock: int = 0
    color: Optional[str] = None
    supplier_id: int

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @validator('stock')
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v

    @validator('name')
    def name_max_length(cls, v):
        if len(v) > 250:
            raise ValueError('Name must be 250 characters or fewer')
        return v.strip()

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    username: str
    role: str = "user"

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:\'",./<>?' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

class User(UserBase):
    id: int
    is_active: bool
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    preferred_language: str = "en"
    email_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    address_book: Optional[str] = None
    profile_image: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None
    preferred_country: Optional[str] = None

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderItem(OrderItemBase):
    id: int
    product: Product

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    total_amount: float
    status: str = "pending"

class OrderCreate(OrderBase):
    items: List[OrderItemBase]
    shipping_address: Optional[str] = None
    payment_intent_id: Optional[str] = None

class Order(OrderBase):
    id: int
    user_id: int
    shipping_address: Optional[str] = None
    tracking_number: Optional[str] = None
    payment_intent_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    old_password: str = ""       # legacy field name
    current_password: str = ""   # preferred field name (frontend uses this)
    new_password: str

    def get_current_password(self) -> str:
        """Accept either 'current_password' or 'old_password'."""
        return self.current_password or self.old_password

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:\'",./<>?' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v


# ── Reviews ──────────────────────────────────────────────────────────────────
class ReviewBase(BaseModel):
    rating: float
    comment: Optional[str] = None
    image_url: Optional[str] = None

    @validator('rating')
    def rating_range(cls, v):
        if not (1.0 <= v <= 5.0):
            raise ValueError('Rating must be between 1 and 5')
        return round(v, 1)


class ReviewCreate(ReviewBase):
    pass


class ReviewSchema(ReviewBase):
    id: int
    product_id: int
    user_id: int
    is_verified_purchase: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Wishlist ──────────────────────────────────────────────────────────────────
class WishlistItem(BaseModel):
    id: int
    product_id: int
    product: Product
    created_at: datetime

    class Config:
        from_attributes = True


# ── Notifications ─────────────────────────────────────────────────────────────
class NotificationSchema(BaseModel):
    id: int
    type: str
    title: str
    message: str
    read: bool
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Categories ────────────────────────────────────────────────────────────────
class CategorySchema(BaseModel):
    id: int
    name: str
    slug: str
    icon: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0


# ── Coupon ────────────────────────────────────────────────────────────────────
class CouponSchema(BaseModel):
    id: int
    code: str
    discount_type: str
    value: float
    min_order: float
    max_uses: Optional[int] = None
    uses_count: int
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class CouponValidate(BaseModel):
    code: str
    order_total: float

