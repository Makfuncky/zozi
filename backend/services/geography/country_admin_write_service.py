"""Country Administration write/persistence service (Country Administration domain).

Owns the DB reads (Q1) and writes (W1) for ``routers.public_country_admin_access``:
internal communications, city management, staff assignments, and category
tax rates. Router handlers become thin HTTP adapters that preserve the exact
return shapes used by the frontend Ghost Rows.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from data.models import CountryCommunication, CountryStaffAssignment
from data.models_country_enhancements import CountryCategoryTaxRate, CountryCity
import structlog
logger = structlog.get_logger(__name__)

_VALID_STAFF_ROLES = (
    "country_head",
    "country_manager",
    "country_moderator",
    "country_finance",
)


# ── Internal Communications ─────────────────────────────────────────


def create_country_communication(
    db: Session,
    *,
    country_code: str,
    from_user_id: Optional[int],
    to_user_id: int,
    subject: str,
    body: str,
    priority: str = "normal",
    category: Optional[str] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
) -> dict:
    comm = CountryCommunication(
        country_code=country_code,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        subject=subject,
        body=body,
        priority=priority,
        category=category,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        status="sent",
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return {
        "id": comm.id,
        "subject": comm.subject,
        "priority": comm.priority,
        "status": comm.status,
        "created_at": comm.created_at.isoformat(),
    }


def list_country_communications(
    db: Session,
    *,
    user_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
) -> List[dict]:
    query = db.query(CountryCommunication).filter(
        (CountryCommunication.to_user_id == user_id)
        | (CountryCommunication.to_user_id.is_(None))
    )
    if status:
        query = query.filter(CountryCommunication.status == status)
    if priority:
        query = query.filter(CountryCommunication.priority == priority)
    comms = query.order_by(desc(CountryCommunication.created_at)).limit(limit).all()
    return [
        {
            "id": c.id,
            "country_code": c.country_code,
            "from_user_id": c.from_user_id,
            "subject": c.subject,
            "body": c.body,
            "priority": c.priority,
            "category": c.category,
            "related_entity_type": c.related_entity_type,
            "related_entity_id": c.related_entity_id,
            "status": c.status,
            "read_at": c.read_at.isoformat() if c.read_at else None,
            "created_at": c.created_at.isoformat(),
        }
        for c in comms
    ]


def mark_communication_read(db: Session, *, comm_id: int) -> dict:
    from fastapi import HTTPException

    comm = db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    comm.status = "read"
    comm.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "read", "read_at": comm.read_at.isoformat()}


# ── City Management ─────────────────────────────────────────────────


def list_cities(
    db: Session,
    *,
    country_code: str,
    active: bool = True,
    limit: int = 100,
) -> List[dict]:
    query = db.query(CountryCity).filter(CountryCity.country_code == country_code.upper())
    if active:
        query = query.filter(CountryCity.status == "active")
    cities = query.order_by(CountryCity.population.desc()).limit(limit).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "name_local": c.name_local,
            "population": c.population,
            "is_capital": c.is_capital,
            "latitude": float(c.latitude) if c.latitude else None,
            "longitude": float(c.longitude) if c.longitude else None,
            "postal_code_prefix": c.postal_code_prefix,
            "status": c.status,
        }
        for c in cities
    ]


def create_city(
    db: Session,
    *,
    country_code: str,
    name: str,
    name_local: Optional[str] = None,
    population: int = 0,
    is_capital: bool = False,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict:
    city = CountryCity(
        country_code=country_code.upper(),
        name=name,
        name_local=name_local,
        population=population,
        is_capital=is_capital,
        latitude=latitude,
        longitude=longitude,
        status="active",
    )
    db.add(city)
    db.commit()
    db.refresh(city)
    return {"id": city.id, "name": city.name, "status": "created"}


def update_city(
    db: Session,
    *,
    country_code: str,
    city_id: int,
    name: Optional[str] = None,
    name_local: Optional[str] = None,
    population: Optional[int] = None,
    is_capital: Optional[bool] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    status: Optional[str] = None,
) -> dict:
    from fastapi import HTTPException

    city = (
        db.query(CountryCity)
        .filter(CountryCity.id == city_id, CountryCity.country_code == country_code.upper())
        .first()
    )
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    if name is not None:
        city.name = name
    if name_local is not None:
        city.name_local = name_local
    if population is not None:
        city.population = population
    if is_capital is not None:
        city.is_capital = is_capital
    if latitude is not None:
        city.latitude = latitude
    if longitude is not None:
        city.longitude = longitude
    if status is not None:
        city.status = status
    db.commit()
    return {"id": city.id, "name": city.name, "status": "updated"}


def delete_city(db: Session, *, country_code: str, city_id: int) -> dict:
    from fastapi import HTTPException

    city = (
        db.query(CountryCity)
        .filter(CountryCity.id == city_id, CountryCity.country_code == country_code.upper())
        .first()
    )
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    city.status = "inactive"
    db.commit()
    return {"status": "deleted"}


# ── Staff Assignment Management ────────────────────────────────────


def list_staff(db: Session, *, country_code: str) -> List[dict]:
    assignments = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.country_code == country_code.upper(),
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "role_in_country": a.role_in_country,
            "assigned_by": a.assigned_by,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assignments
    ]


def assign_staff(
    db: Session,
    *,
    country_code: str,
    user_id: int,
    role_in_country: str,
    assigned_by: Optional[int] = None,
) -> dict:
    from fastapi import HTTPException

    if role_in_country not in _VALID_STAFF_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    existing = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.country_code == country_code.upper(),
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.role_in_country == role_in_country,
            CountryStaffAssignment.is_active == True,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Staff already assigned with this role")
    assignment = CountryStaffAssignment(
        country_code=country_code.upper(),
        user_id=user_id,
        role_in_country=role_in_country,
        assigned_by=assigned_by,
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    return {"id": assignment.id, "status": "assigned"}


def remove_staff(db: Session, *, country_code: str, staff_id: int) -> dict:
    from fastapi import HTTPException

    assignment = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.id == staff_id,
            CountryStaffAssignment.country_code == country_code.upper(),
        )
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Staff assignment not found")
    assignment.is_active = False
    db.commit()
    return {"status": "removed"}


# ── Category Tax Rates ──────────────────────────────────────────────


def list_tax_rates(db: Session, *, country_code: str) -> List[dict]:
    rates = (
        db.query(CountryCategoryTaxRate)
        .filter(
            CountryCategoryTaxRate.country_code == country_code.upper(),
            CountryCategoryTaxRate.is_active == True,
        )
        .all()
    )
    return [
        {
            "id": r.id,
            "category_id": r.category_id,
            "tax_rate": float(r.tax_rate),
            "tax_name": r.tax_name,
        }
        for r in rates
    ]


def set_tax_rate(
    db: Session,
    *,
    country_code: str,
    category_id: int,
    tax_rate: float,
    tax_name: Optional[str] = None,
) -> dict:
    existing = (
        db.query(CountryCategoryTaxRate)
        .filter(
            CountryCategoryTaxRate.country_code == country_code.upper(),
            CountryCategoryTaxRate.category_id == category_id,
        )
        .first()
    )
    if existing:
        existing.tax_rate = tax_rate
        existing.tax_name = tax_name
        existing.is_active = True
    else:
        rate = CountryCategoryTaxRate(
            country_code=country_code.upper(),
            category_id=category_id,
            tax_rate=tax_rate,
            tax_name=tax_name,
            is_active=True,
        )
        db.add(rate)
    db.commit()
    return {"status": "saved", "category_id": category_id, "tax_rate": tax_rate}
