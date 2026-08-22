"""Admin auth view models (serializers).

Routers shape responses through these rather than inline Pydantic models.
Core shared models (TokenResponse, UserOut, RegisterRequest) are re-exported
from ``infrastructure.database.schemas``.
"""
from __future__ import annotations

from infrastructure.database.schemas import RegisterRequest, TokenResponse, UserOut

__all__ = ["RegisterRequest", "TokenResponse", "UserOut"]
