"""User request/response DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

from infrastructure.database.schemas import _validate_password_complexity


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Request DTO for creating a user."""
    email: str
    username: str
    password: str
    role: str = "customer"


class UserResponse(BaseModel):
    """Response DTO for a user."""
    id: int
    email: str
    username: str
    role: str
    is_active: bool


class UserUpdate(BaseModel):
    """Request DTO for updating a user."""
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class RegisterRequest(BaseModel):
    """Registration request DTO."""
    email: str
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
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(OrmBase):
    """User profile response DTO."""
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_email_verified: bool = False
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    referral_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


TokenResponse.model_rebuild()
