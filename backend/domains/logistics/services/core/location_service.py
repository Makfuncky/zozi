from __future__ import annotations

"""Location service — city distance matrix management."""

from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.governance.models.core import CityDistanceMatrix
from domains.logistics.services.partners.pricing_service import normalize_city_name, normalize_country_code
from infrastructure.utils.datetime_utils import utcnow as _utcnow


def _sanitize_optional_string(value: Any, *, max_length: int = 500) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_length]


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


def _serialize_city_distance(entry: CityDistanceMatrix) -> dict[str, Any]:
    created_at = cast(Optional[datetime], getattr(entry, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(entry, "updated_at", None))
    return {
        "id": entry.id,
        "origin_country_code": entry.origin_country_code,
        "origin_city_name": entry.origin_city_name,
        "destination_country_code": entry.destination_country_code,
        "destination_city_name": entry.destination_city_name,
        "distance_km": float(entry.distance_km),
        "notes": entry.notes,
        "created_by": entry.created_by,
        "updated_by": entry.updated_by,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def list_city_distances(
    current_user: dict,
    db: Session,
    *,
    origin_country_code: str | None = None,
    destination_country_code: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    _require_admin(current_user)
    query = db.query(CityDistanceMatrix)
    if origin_country_code:
        query = query.filter(CityDistanceMatrix.origin_country_code == origin_country_code.upper())
    if destination_country_code:
        query = query.filter(CityDistanceMatrix.destination_country_code == destination_country_code.upper())
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            func.lower(CityDistanceMatrix.origin_city_name).like(like)
            | func.lower(CityDistanceMatrix.destination_city_name).like(like)
        )
    total = query.count()
    items = (
        query.order_by(CityDistanceMatrix.origin_country_code, CityDistanceMatrix.origin_city_name, CityDistanceMatrix.destination_city_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "page_size": page_size, "items": [_serialize_city_distance(e) for e in items]}


def create_city_distance(data: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    origin_cc = normalize_country_code(str(data.get("origin_country_code") or ""))
    dest_cc = normalize_country_code(str(data.get("destination_country_code") or ""))
    origin_city = _sanitize_optional_string(data.get("origin_city_name"), max_length=120)
    dest_city = _sanitize_optional_string(data.get("destination_city_name"), max_length=120)
    if not origin_cc or not dest_cc or not origin_city or not dest_city:
        raise HTTPException(status_code=422, detail="origin_country_code, origin_city_name, destination_country_code, destination_city_name are all required")
    try:
        distance_km = float(data.get("distance_km") or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="distance_km must be a positive number") from exc
    if distance_km <= 0:
        raise HTTPException(status_code=422, detail="distance_km must be greater than 0")
    existing = (
        db.query(CityDistanceMatrix)
        .filter(
            CityDistanceMatrix.origin_country_code == origin_cc,
            CityDistanceMatrix.destination_country_code == dest_cc,
        )
        .all()
    )
    origin_key = normalize_city_name(origin_city)
    dest_key = normalize_city_name(dest_city)
    for row in existing:
        if (
            normalize_city_name(cast(str | None, getattr(row, "origin_city_name", None))) == origin_key
            and normalize_city_name(cast(str | None, getattr(row, "destination_city_name", None))) == dest_key
        ):
            raise HTTPException(status_code=409, detail="A distance entry for this route already exists. Use PUT to update it.")
    entry = CityDistanceMatrix(
        origin_country_code=origin_cc,
        origin_city_name=origin_city,
        destination_country_code=dest_cc,
        destination_city_name=dest_city,
        distance_km=distance_km,
        notes=_sanitize_optional_string(data.get("notes"), max_length=1000),
        created_by=current_user["id"],
        updated_by=current_user["id"],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _serialize_city_distance(entry)


def update_city_distance(matrix_id: int, data: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    entry = db.query(CityDistanceMatrix).filter(CityDistanceMatrix.id == matrix_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="City distance entry not found")
    try:
        distance_km = float(data.get("distance_km") or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="distance_km must be a positive number") from exc
    if distance_km <= 0:
        raise HTTPException(status_code=422, detail="distance_km must be greater than 0")
    setattr(entry, "distance_km", distance_km)
    if "notes" in data:
        setattr(entry, "notes", _sanitize_optional_string(data.get("notes"), max_length=1000))
    setattr(entry, "updated_by", current_user["id"])
    setattr(entry, "updated_at", _utcnow())
    db.commit()
    db.refresh(entry)
    return _serialize_city_distance(entry)


def delete_city_distance(matrix_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    entry = db.query(CityDistanceMatrix).filter(CityDistanceMatrix.id == matrix_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="City distance entry not found")
    db.delete(entry)
    db.commit()
    return {"detail": "City distance entry deleted"}
