"""Search controller — HTTP/service boundary for search and recommendations.

The recommendation algorithm and smart-search parsing live in
``domains.catalog.services.search.search_service``; this module is the thin
controller layer the router depends on. Keeping the logic in the service keeps
the controller importable and testable and avoids duplicating the recommendation
engine.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Response
from sqlalchemy.orm import Session

# TODO: Law 1 violation - infrastructure importing domain service functions.
# This should be refactored to use a search ports layer or the catalog domain
# should expose search via a sanctioned cross-domain interface.
from domains.catalog.services.search.search_service import (
    get_recommendations as _get_recommendations,
)
from domains.catalog.services.search.search_service import (
    smart_search as _smart_search,
)
from infrastructure.routing.route_contract import get

@get("/search", skip=True)
def smart_search(
    q: str,
    limit: int,
    db: Session,
    response: Optional[Response] = None,
    supplier_id: Optional[int] = None,
) -> dict:
    """Delegate a free-text / product search to the search service."""
    return _smart_search(q=q, limit=limit, db=db, response=response, supplier_id=supplier_id)

@get("/search/recommendations", skip=True)
def get_recommendations(
    user_id: Optional[int],
    db: Session,
    limit: int = 8,
    recent_categories: Optional[list[str]] = None,
) -> dict:
    """Delegate personalized product recommendations to the search service."""
    return _get_recommendations(
        user_id=user_id, db=db, limit=limit, recent_categories=recent_categories
    )
