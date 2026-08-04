"""Auto-populate endpoint for the Country Control Plane.

Wires the heuristic engine and external data fetchers to database persistence.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from data.db import get_db
from data.dependencies_auth import get_current_user
from routers.auth import get_current_user as auth_get_current_user
from services.country_auto_populate import auto_populate_country
from services.country.country_router_service import save_country_from_suggestion

logger = logging.getLogger(__name__)


def _user_role(user: object) -> str:
    if hasattr(user, "role"):
        return str(getattr(user, "role") or "")
    if isinstance(user, dict):
        return str(user.get("role") or "")
    return ""


router = APIRouter(tags=["country-auto-populate"])


@router.post("/auto-populate")
async def auto_populate(
    search_term: str = Query(..., min_length=2, description="Country name or ISO code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Search and auto-populate country data from external APIs + heuristic engine.

    Returns the full suggested payload the frontend Ghost Row can render.
    Data is NOT persisted — admin must call POST /admin/countries/{code}/save to commit.
    """
    if _user_role(current_user).lower() not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        result = await auto_populate_country(search_term)
        if not result or result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("error", "Country not found"))

        return {
            "status": "success",
            "cached": result.get("cached", False),
            "fetched_at": result.get("fetched_at"),
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Auto-populate failed for %s", search_term)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{country_code}/save")
def save_country_from_suggestion_endpoint(
    country_code: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Persist auto-populated country suggestion to the database.

    Accepts the full payload from POST /admin/countries/auto-populate
    and writes it into CountryConfig + related tables.
    """
    if _user_role(current_user).lower() not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return save_country_from_suggestion(db, country_code, payload, current_user)