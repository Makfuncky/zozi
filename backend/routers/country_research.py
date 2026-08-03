"""Country Research endpoint — returns the full 20-module e-commerce research report."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from data.db import get_db
from routers.auth import get_current_user
from services.country_auto_populate import auto_populate_country
from services.country_research import build_country_research

logger = logging.getLogger(__name__)

router = APIRouter(tags=["country-research"])


@router.get("/{code}/research")
async def get_country_research(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return the full 20-module e-commerce research report for a country.

    Builds the report from auto-populate data + heuristic/default modules.
    Modules 4–20 require AI or manual research for high-confidence data.
    """
    try:
        auto_data = await auto_populate_country(code)
        if not auto_data or auto_data.get("error"):
            raise HTTPException(
                status_code=404,
                detail=auto_data.get("error", f"Country {code} not found"),
            )

        research = build_country_research(auto_data)

        return {
            "status": "success",
            "fetched_at": auto_data.get("fetched_at"),
            "cached": auto_data.get("cached", False),
            "data": research,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Country research failed for %s", code)
        raise HTTPException(status_code=500, detail=str(exc))