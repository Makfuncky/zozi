"""Auto-migrated service logic from routers/country_admin.py."""
from __future__ import annotations

from datetime import datetime, timezone

from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, HTTPException, Path, Query

from sqlalchemy import desc

from sqlalchemy.orm import Session

from domains.governance.services.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

from domains.country.models.countries import CountryCommunication
from domains.country.models.country_enhancements import CountryStaffAssignment

from domains.country.models.country_enhancements import CountryCategoryTaxRate, CountryCity

from domains.governance.services.audit_trail_service import AuditTrailService

from domains.suppliers.services.legal_contract_service import LegalContractService




def send_country_communication(country_code: str, to_user_id: int, subject: str, body: str, priority: str, category: str, related_entity_type: str, related_entity_id: int, db: Session, current_user):
    """Send an internal communication within a country."""
    comm = CountryCommunication(
        country_code=country_code,
        from_user_id=current_user.get("id"),
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

def list_communications(status: Optional[str], priority: Optional[str], limit: int, db: Session, current_user):
    """Inbox: list communications for the current user, filtered by role+country."""
    user_id = current_user.get("id")
    query = db.query(CountryCommunication).filter(
        (CountryCommunication.to_user_id == user_id) |
        (CountryCommunication.to_user_id.is_(None))
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

def mark_communication_read(comm_id: int, db: Session, current_user):
    comm = db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    comm.status = "read"
    comm.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "read", "read_at": comm.read_at.isoformat()}


def list_cities(country_code: str, active: bool, limit: int, db: Session, current_user):
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

def add_city(country_code: str, name: str, name_local: str, population: int, is_capital: bool, latitude: float, longitude: float, db: Session, current_user):
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

def update_city(country_code: str, city_id: int, name: str, name_local: str, population: int, is_capital: bool, latitude: float, longitude: float, status: str, db: Session, current_user):
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == country_code.upper()).first()
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

def delete_city(country_code: str, city_id: int, db: Session, current_user):
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == country_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    city.status = "inactive"
    db.commit()
    return {"status": "deleted"}

def list_staff(country_code: str, db: Session, current_user):
    assignments = (
        db.query(CountryStaffAssignment)
        .filter(CountryStaffAssignment.country_code == country_code.upper(), CountryStaffAssignment.is_active == True)
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

def assign_staff(country_code: str, user_id: int, role_in_country: str, db: Session, current_user):
    if role_in_country not in ("country_head", "country_manager", "country_moderator", "country_finance"):
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
        assigned_by=current_user.get("id"),
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    return {"id": assignment.id, "status": "assigned"}

def remove_staff(country_code: str, staff_id: int, db: Session, current_user):
    assignment = (
        db.query(CountryStaffAssignment)
        .filter(CountryStaffAssignment.id == staff_id, CountryStaffAssignment.country_code == country_code.upper())
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Staff assignment not found")
    assignment.is_active = False
    db.commit()
    return {"status": "removed"}

def list_tax_rates(country_code: str, db: Session, current_user):
    rates = (
        db.query(CountryCategoryTaxRate)
        .filter(CountryCategoryTaxRate.country_code == country_code.upper(), CountryCategoryTaxRate.is_active == True)
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

def set_tax_rate(country_code: str, category_id: int, tax_rate: float, tax_name: str, db: Session, current_user):
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


from domains.governance.services.admin_geography_audit_service import get_audit_trail






















from domains.governance.services.admin_geography_audit_service import log_financial_change














from domains.governance.services.admin_geography_audit_service import get_data_residency













