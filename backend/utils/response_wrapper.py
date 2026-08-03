"""Standard API response wrapper for Zozi backend.

Provides PaginatedResponse base model and response wrapper utilities to standardize
API responses across all endpoints. Ensures consistent response format across the
platform with pagination support and error handling.
"""
from __future__ import annotations

from typing import Any, List, Optional, Generic, TypeVar
from fastapi.responses import JSONResponse

from data.schemas import PaginatedResponse as SchemaPaginatedResponse
T = TypeVar("T")


class PaginatedResponseWrapper(SchemaPaginatedResponse, Generic[T]):
    """Standardized paginated response wrapper.

    This class extends the base PaginatedResponse schema with generic typing
    to provide type-safe pagination responses across all API endpoints.

    Attributes:
        items: List of items in the current page (generic type T)
        total: Total number of items across all pages
        page: Current page number (1-based)
        size: Number of items per page
        pages: Total number of pages
    """

    items: List[T]

    @classmethod
    def from_query(
        cls,
        items: List[T],
        total: int,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponseWrapper[T]:
        """Create a paginated response from a query result.

        Args:
            items: List of items for the current page
            total: Total count of items
            page: Current page number (1-based)
            size: Number of items per page

        Returns:
            PaginatedResponseWrapper instance
        """
        if total <= 0:
            pages = 0
        else:
            pages = max(1, (total + size - 1) // size)

        return cls(items=items, total=total, page=page, size=size, pages=pages)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the response
        """
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "size": self.size,
            "pages": self.pages,
        }


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    size: int = 20,
) -> JSONResponse:
    """Create a standardized paginated response.

    Args:
        items: List of items for the response
        total: Total count of items
        page: Current page number (1-based)
        size: Number of items per page

    Returns:
        JSONResponse with standardized paginated format
    """
    return JSONResponse(
        content={
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": max(1, (total + size - 1) // size) if total > 0 else 0,
        },
        status_code=200,
    )