import logging
from typing import Any, Callable, TypeVar

from fastapi import HTTPException, Request
from sqlalchemy.orm import Query

logger = logging.getLogger(__name__)

T = TypeVar("T")


def ghost_record_404(result: T | None, request: Request | None = None, resource: str = "Resource") -> T:
    """Ghost Record Protocol — return 404 instead of 403.

    When RLS blocks access to a record (query returns None), this helper
    raises HTTP 404 instead of 403, making the resource mathematically
    invisible to the requester.

    Usage in controllers:
        order = db.query(Order).filter(Order.id == order_id).first()
        ghost_record_404(order, request, "Order")
        # If we reach here, the order exists AND is in the user's scope
    """
    if result is None:
        if request is not None:
            logger.info(
                "Ghost record: %s not found (or blocked by RLS) for %s %s",
                resource,
                request.method,
                request.url.path,
            )
        raise HTTPException(status_code=404, detail=f"{resource} not found")
    return result


def ghost_record_query(query: Query, request: Request | None = None, resource: str = "Resource") -> Any:
    """Execute a query and apply Ghost Record Protocol.

    Fetches the first result. If None, returns 404 instead of 403.
    """
    result = query.first()
    return ghost_record_404(result, request, resource)


def require_country_scope(request: Request, required_country: str | None = None) -> None:
    """Verify the request has the required country scope.

    Call this in controller endpoints that must ensure the user's
    country scope covers a specific country before proceeding.

    Raises 404 (not 403) if the scope doesn't include the required country.
    """
    scope: set[str] | None = getattr(request.state, "country_scope", None)
    is_restricted: bool = getattr(request.state, "country_is_restricted", True)

    if not is_restricted:
        return

    if required_country and scope and required_country.upper() not in scope:
        logger.info(
            "Country scope violation: required=%s scope=%s path=%s",
            required_country,
            scope,
            request.url.path,
        )
        raise HTTPException(status_code=404, detail="Not found")

