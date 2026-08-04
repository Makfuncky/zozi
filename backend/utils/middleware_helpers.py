"""Middleware helpers for standardized error handling and response formatting.

Provides decorators and utility functions that routers can use to:
- Consistently wrap paginated responses
- Catch and format errors using the RFC 7807 Problem Details format
- Standardize exception-to-status-code mapping
"""

import functools
import logging
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from data.db import get_db
from data.schemas import PaginatedResponse
from utils.pagination import paginated_query, safe_page
from utils.error_handler import ErrorCategory, _build_problem_response
from utils.logging_config import get_request_id

logger = logging.getLogger(__name__)


def as_paginated_response(
    max_size: int = 100,
):
    """Decorator that wraps a route handler's return value into a PaginatedResponse.

    The decorated function must return a tuple of ``(items, total)``.

    Example::

        @router.get("/items")
        @as_paginated_response()
        def list_items(page: int = 1, size: int = 20, db: Session = Depends(get_db)):
            q = db.query(Item)
            total = q.count()
            items = q.offset((page-1)*size).limit(size).all()
            return items, total
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            page, size = safe_page(
                kwargs.get("page", 1),
                kwargs.get("size", 20),
                max_size,
            )
            kwargs["page"] = page
            kwargs["size"] = size
            items, total = func(*args, **kwargs)
            pages = max(1, (total + size - 1) // size) if total > 0 else 0
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
            }
        return wrapper
    return decorator


def handle_service_error(
    default_status: int = 500,
    default_message: str = "Internal server error",
):
    """Decorator that catches exceptions and returns RFC 7807 Problem Details.

    Example::

        @router.get("/items/{id}")
        @handle_service_error(default_status=404, default_message="Item not found")
        def get_item(id: int, db: Session = Depends(get_db)):
            item = db.query(Item).filter(Item.id == id).first()
            if not item:
                raise HTTPException(404)
            return item
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Unhandled error in %s", func.__name__)
                body = _build_problem_response(
                    status=default_status,
                    title="Service Error",
                    detail=str(e) if str(e) else default_message,
                    error_type=f"https://zozi.com/errors/service-{default_status}",
                    category=ErrorCategory.INTERNAL,
                )
                return JSONResponse(status_code=default_status, content=body)
        return wrapper
    return decorator


def raise_not_found(entity: str, entity_id: int | str) -> None:
    """Raise a standardized 404 HTTPException."""
    raise HTTPException(
        status_code=404,
        detail=f"{entity} with id '{entity_id}' not found",
    )


def raise_bad_request(message: str) -> None:
    """Raise a standardized 400 HTTPException."""
    raise HTTPException(status_code=400, detail=message)


def raise_unauthorized(message: str = "Not authenticated") -> None:
    """Raise a standardized 401 HTTPException."""
    raise HTTPException(status_code=401, detail=message)


def raise_forbidden(message: str = "Insufficient permissions") -> None:
    """Raise a standardized 403 HTTPException."""
    raise HTTPException(status_code=403, detail=message)
