"""User request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


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
