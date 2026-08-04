"""
Country Admin Helpers — authorization guards and utility functions.

Canonical home for country-specific admin helpers that were previously in
controllers/country_controller.py. Routers now import from here instead of
crossing the controller→controller boundary.
"""

import json
from decimal import Decimal
from typing import Any, Set

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import CountryConfig


# ── Authorization guards ──────────────────────────────────────────────────

def require_admin(current_user: dict) -> None:
    """Check that the user has a staff-level role."""
    role = str(current_user.get("role") or "").lower()
    allowed = {"admin", "country_head", "country_manager", "sub_admin"}
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Staff access required")


def require_full_admin(current_user: dict) -> None:
    """Strict admin-only check for operations like creating/deleting countries."""
    role = str(current_user.get("role") or "").lower()
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required for this operation")


def require_country_access(country_code: str, current_user: dict) -> None:
    """Check country-scoped access for country_head/country_manager roles."""
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return
    if role not in ("country_head", "country_manager"):
        raise HTTPException(status_code=403, detail="Country-level access required")
    codes = current_user.get("staff_country_codes", None)
    if not codes or not isinstance(codes, (list, tuple)):
        raise HTTPException(status_code=403, detail="You are not assigned to any country")
    if country_code.upper() not in [str(c).strip().upper() for c in codes]:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to country '{country_code}'",
        )


# ── Data helpers ──────────────────────────────────────────────────────────

def to_json(value: Any) -> str:
    return json.dumps(value, default=str)


def from_json(raw: str | None, *, default: Any) -> Any:
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default
    return parsed


def to_decimal(value: Any, *, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid decimal for {field}") from exc


def get_country_or_404(code: str, db: Session) -> CountryConfig:
    from utils.country_code import normalize_country_code
    normalized = normalize_country_code(code)
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country config not found")
    return country


def record_country_admin_change(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity: str,
    entity_key: str | None,
    before: Any,
    after: Any,
    notes: str | None = None,
) -> None:
    from utils.audit import record_admin_change
    record_admin_change(
        db,
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_key=entity_key,
        before=before,
        after=after,
        notes=notes,
    )
