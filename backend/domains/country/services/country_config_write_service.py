from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from _legacy.models import CountryCity, CountryCommissionRate, CountryConfig
from _legacy.models.country_enhancements import CountryFeatureFlag
from services.geography.country_write_service import record_admin_change
import structlog
logger = structlog.get_logger(__name__)


def create_country_feature_flag(db: Session, code: str, body: dict) -> dict:
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


def update_country_feature_flag(db: Session, code: str, key: str, body: dict) -> dict:
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


def delete_country_feature_flag(db: Session, code: str, key: str) -> dict:
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


def add_country_city(db: Session, code: str, body: dict) -> dict:
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


def patch_country_city(db: Session, code: str, city_id: int, body: dict) -> dict:
    city = (
        db.query(CountryCity)
        .filter(CountryCity.id == city_id, CountryCity.country_code == code.upper())
        .first()
    )
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    for field in ("name", "region", "is_active", "sort_order"):
        if field in body:
            setattr(city, field, body[field])
    db.commit()
    return {"id": city.id, "name": city.name}


def delete_country_city(db: Session, code: str, city_id: int) -> None:
    city = (
        db.query(CountryCity)
        .filter(CountryCity.id == city_id, CountryCity.country_code == code.upper())
        .first()
    )
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    db.delete(city)
    db.commit()


def toggle_country_active(db: Session, code: str) -> dict:
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_active = not c.is_active
    db.commit()
    return {"message": f"Country {'enabled' if c.is_active else 'disabled'}"}


def archive_country(db: Session, code: str, actor_id: Any) -> dict:
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_deleted = True
    record_admin_change(
        db,
        actor_id=actor_id,
        action="archive",
        entity="country_config",
        entity_key=code.upper(),
        before={"is_deleted": False},
        after={"is_deleted": True},
    )
    db.commit()
    return {"message": "Country archived"}


def restore_country(db: Session, code: str, actor_id: Any) -> dict:
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_deleted = False
    record_admin_change(
        db,
        actor_id=actor_id,
        action="restore",
        entity="country_config",
        entity_key=code.upper(),
        before={"is_deleted": True},
        after={"is_deleted": False},
    )
    db.commit()
    return {"message": "Country restored"}


def bulk_archive_countries(db: Session, ids: list[str], actor_id: Any) -> dict:
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(ids)).all()
    for c in rows:
        c.is_deleted = True
        record_admin_change(
            db,
            actor_id=actor_id,
            action="bulk_archive",
            entity="country_config",
            entity_key=c.code,
            before={"is_deleted": False},
            after={"is_deleted": True},
        )
    db.commit()
    return {"message": f"{len(rows)} countries archived"}


def bulk_restore_countries(db: Session, ids: list[str], actor_id: Any) -> dict:
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(ids)).all()
    for c in rows:
        c.is_deleted = False
        record_admin_change(
            db,
            actor_id=actor_id,
            action="bulk_restore",
            entity="country_config",
            entity_key=c.code,
            before={"is_deleted": True},
            after={"is_deleted": False},
        )
    db.commit()
    return {"message": f"{len(rows)} countries restored"}


def hard_delete_country(db: Session, code: str) -> None:
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    db.delete(c)
    db.commit()


def create_country_commission_rate(db: Session, code: str, body: Any, actor_id: Any) -> dict:
    existing = (
        db.query(CountryCommissionRate)
        .filter(
            CountryCommissionRate.country_code == code.upper(),
            CountryCommissionRate.supplier_tier == body.supplier_tier,
            CountryCommissionRate.name == body.name,
        )
        .first()
    )
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
    record_admin_change(
        db,
        actor_id=actor_id,
        action="create_commission_rate",
        entity="country_commission_rate",
        entity_key=f"{code}:{body.supplier_tier}:{body.name}",
        before=None,
        after=body.model_dump(),
    )
    db.commit()
    db.refresh(rate)
    return {"id": rate.id, **body.model_dump()}


def delete_country_commission_rate(db: Session, code: str, tier: str, name: str, actor_id: Any) -> dict:
    rate = (
        db.query(CountryCommissionRate)
        .filter(
            CountryCommissionRate.country_code == code.upper(),
            CountryCommissionRate.supplier_tier == tier,
            CountryCommissionRate.name == name,
        )
        .first()
    )
    if not rate:
        raise HTTPException(status_code=404, detail="Commission rate not found")
    db.delete(rate)
    record_admin_change(
        db,
        actor_id=actor_id,
        action="delete_commission_rate",
        entity="country_commission_rate",
        entity_key=f"{code}:{tier}:{name}",
        before={"commission_percentage": float(rate.rate_percent)},
        after=None,
    )
    db.commit()
    return {"message": "Commission rate deleted"}
