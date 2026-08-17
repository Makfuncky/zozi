"""Service layer for the inline country-configuration database operations that lived
in ``routers/public_geography_configuration.py`` and ``routers/admin_geography_configuration.py``.

These two routers were (except for their URL prefix) identical copies of the same
country CRUD surface. Their inline ``db.query/add/commit/delete`` blocks are moved
here so the routers become thin HTTP delegators. Permission checks and admin-change
audit recording are kept alongside the data access (they need ``current_user`` and
the session) but are implemented as thin calls into the existing helpers in
``services.geography.country_service`` so behavior is preserved exactly.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from _legacy.models import CountryCity, CountryCommissionRate, CountryConfig, CountryFeatureFlag

from services.geography.country_service import (
    _get_country_or_404,
    _record_admin_change,
    _require_admin,
    _require_country_access,
    _require_full_admin,
)


def create_feature_flag(code: str, body: dict, db: Session) -> dict:
    flag = CountryFeatureFlag(
        country_code=code.upper(),
        feature_key=str(body.get("feature_key", "")).strip(),
        feature_name=body.get("feature_name"),
        is_enabled=bool(body.get("is_enabled", True)),
        config=body.get("config"),
        rollout_audience=body.get("rollout_audience"),
        notes=body.get("notes"),
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return {"id": flag.id, "feature_key": flag.feature_key, "is_enabled": flag.is_enabled}


def update_feature_flag(code: str, key: str, body: dict, db: Session) -> dict:
    flag = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == code.upper(), CountryFeatureFlag.feature_key == key)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    if "is_enabled" in body:
        flag.is_enabled = bool(body["is_enabled"])
    if "config" in body:
        flag.config = body["config"]
    if "feature_name" in body:
        flag.feature_name = body["feature_name"]
    if "rollout_audience" in body:
        flag.rollout_audience = body["rollout_audience"]
    if "notes" in body:
        flag.notes = body["notes"]
    db.commit()
    db.refresh(flag)
    return {"id": flag.id, "feature_key": flag.feature_key, "is_enabled": flag.is_enabled}


def delete_feature_flag(code: str, key: str, db: Session) -> dict:
    flag = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == code.upper(), CountryFeatureFlag.feature_key == key)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    db.delete(flag)
    db.commit()
    return {"message": "Feature flag deleted", "feature_key": key}


def add_country_city(code: str, body: dict, db: Session) -> dict:
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    city = CountryCity(
        country_code=code.upper(),
        name=str(body.get("name", "")).strip(),
        region=str(body.get("region", "")).strip() or None,
        latitude=float(body["lat"]) if body.get("lat") is not None else None,
        longitude=float(body["lng"]) if body.get("lng") is not None else None,
        population=int(body["population"]) if body.get("population") is not None else None,
        source=str(body.get("source", "manual")),
    )
    db.add(city)
    db.commit()
    db.refresh(city)
    return {"id": city.id, "name": city.name, "region": city.region, "is_active": city.is_active}


def patch_country_city(code: str, city_id: int, body: dict, db: Session) -> dict:
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    for field in ("name", "region", "is_active", "sort_order"):
        if field in body:
            setattr(city, field, body[field])
    db.commit()
    return {"id": city.id, "name": city.name}


def delete_country_city(code: str, city_id: int, db: Session) -> None:
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    db.delete(city)
    db.commit()


def toggle_country_active(code: str, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_active = not c.is_active
    db.commit()
    return {"message": f"Country {'enabled' if c.is_active else 'disabled'}"}


def archive_country(code: str, current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = True
    _record_admin_change(db, actor_id=current_user.get("id"), action="archive", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": "Country archived"}


def restore_country(code: str, current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = False
    _record_admin_change(db, actor_id=current_user.get("id"), action="restore", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": "Country restored"}


def bulk_archive_countries(ids: list[str], current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(ids)).all()
    for c in rows:
        c.is_deleted = True
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_archive", entity="country_config",
                             entity_key=c.code, before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": f"{len(rows)} countries archived"}


def bulk_restore_countries(ids: list[str], current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(ids)).all()
    for c in rows:
        c.is_deleted = False
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_restore", entity="country_config",
                             entity_key=c.code, before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": f"{len(rows)} countries restored"}


def hard_delete_country(code: str, current_user: dict, db: Session) -> None:
    _require_full_admin(current_user)
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    db.delete(c)
    db.commit()


def list_country_commission_rates(code: str, current_user: dict, db: Session) -> list[dict]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    rows = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper()
    ).order_by(CountryCommissionRate.supplier_tier, CountryCommissionRate.name).all()
    return [
        {
            "supplier_tier": r.supplier_tier,
            "name": r.name,
            "commission_percentage": float(r.rate_percent) * 100,
            "fixed_fee": float(r.fixed_fee) if r.fixed_fee else 0.0,
        }
        for r in rows
    ]


def create_country_commission_rate(code: str, body: Any, current_user: dict, db: Session) -> dict:
    from pydantic import BaseModel

    _require_admin(current_user)
    _require_country_access(code, current_user)
    _get_country_or_404(code, db)
    existing = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper(),
        CountryCommissionRate.supplier_tier == body.supplier_tier,
        CountryCommissionRate.name == body.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Commission rate already exists for this tier and name")
    rate = CountryCommissionRate(
        country_code=code.upper(),
        supplier_tier=body.supplier_tier,
        name=body.name,
        rate_percent=Decimal(str(body.commission_percentage / 100)),
    )
    if body.fixed_fee:
        rate.fixed_fee = Decimal(str(body.fixed_fee))
    db.add(rate)
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_commission_rate",
                        entity="country_commission_rate", entity_key=f"{code}:{body.supplier_tier}:{body.name}",
                        before=None, after=body.model_dump())
    db.commit()
    db.refresh(rate)
    return {"id": rate.id, **body.model_dump()}


def delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    rate = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper(),
        CountryCommissionRate.supplier_tier == tier,
        CountryCommissionRate.name == name,
    ).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Commission rate not found")
    db.delete(rate)
    _record_admin_change(db, actor_id=current_user.get("id"), action="delete_commission_rate",
                        entity="country_commission_rate", entity_key=f"{code}:{tier}:{name}",
                        before={"commission_percentage": float(rate.rate_percent)}, after=None)
    db.commit()
    return {"message": "Commission rate deleted"}
