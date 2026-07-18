"""
Country Admin Router
Endpoints for legal contracts, audit trails, and country management.
"""
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.database import get_db
from models import CountryConfig, CountryCommunication, User, CountryStaffAssignment
from models.country_enhancements import CountryCity, CountryCategoryTaxRate
from controllers.auth_controller import get_current_user
from services.legal_contract_service import LegalContractService
from services.audit_trail_service import AuditTrailService

router = APIRouter(tags=["country-admin"])


@router.get("/{country_code}/legal-contracts/generate")
def generate_legal_contract(
    country_code: str = Path(..., description="Country code"),
    template_type: str = Query("terms", description="Template type (terms, privacy, refund)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate a legal contract for a country."""
    result = LegalContractService.generate_contract(country_code, template_type, db=db)
    return result


@router.get("/{country_code}/audit-trail", response_model=List[dict])
def get_audit_trail(
    country_code: str = Path(..., description="Country code"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    record_id: Optional[int] = Query(None, description="Filter by record ID"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get audit trail for a country."""
    trail = AuditTrailService.get_audit_trail(
        country_code,
        table_name=table_name,
        record_id=record_id,
        limit=limit
    )
    return trail


@router.post("/{country_code}/audit-trail/log")
def log_financial_change(
    country_code: str = Path(..., description="Country code"),
    table_name: str = Body(..., description="Table name"),
    record_id: int = Body(..., description="Record ID"),
    field_name: str = Body(..., description="Field name"),
    old_value: Any = Body(..., description="Old value"),
    new_value: Any = Body(..., description="New value"),
    reason: str = Body(..., description="Reason for change"),
    user_id: Optional[int] = Body(None, description="User ID"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Log a financial change for audit purposes."""
    audit_record = AuditTrailService.log_financial_change(
        country_code=country_code,
        table_name=table_name,
        record_id=record_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        user_id=user_id,
        metadata=metadata
    )
    return audit_record


# ── Internal Communication Endpoints (Spec Section 7) ─────────────


@router.post("/{country_code}/communications")
def send_country_communication(
    country_code: str = Path(...),
    to_user_id: int = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
    priority: str = Body("normal"),
    category: str = Body(None),
    related_entity_type: str = Body(None),
    related_entity_id: int = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.get("/communications")
def list_communications(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.put("/communications/{comm_id}/read")
def mark_communication_read(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    comm = db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    comm.status = "read"
    comm.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "read", "read_at": comm.read_at.isoformat()}


@router.get("/{country_code}/data-residency")
def get_data_residency(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get data residency tier for a country."""
    from services.audit_trail_service import DataResidencyService
    tier = DataResidencyService.get_data_residency_tier(country_code)
    requires_encryption = DataResidencyService.requires_local_encryption(country_code)
    return {
        "country_code": country_code,
        "data_residency_tier": tier,
        "requires_local_encryption": requires_encryption
    }


# ── City Management (Normalized) ──────────────────────────────────


@router.get("/{country_code}/cities")
def list_cities(
    country_code: str = Path(...),
    active: bool = Query(True),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.post("/{country_code}/cities")
def add_city(
    country_code: str = Path(...),
    name: str = Body(...),
    name_local: str = Body(None),
    population: int = Body(0),
    is_capital: bool = Body(False),
    latitude: float = Body(None),
    longitude: float = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.put("/{country_code}/cities/{city_id}")
def update_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    name: str = Body(None),
    name_local: str = Body(None),
    population: int = Body(None),
    is_capital: bool = Body(None),
    latitude: float = Body(None),
    longitude: float = Body(None),
    status: str = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.delete("/{country_code}/cities/{city_id}")
def delete_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == country_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    city.status = "inactive"
    db.commit()
    return {"status": "deleted"}


# ── Staff Assignment Management ───────────────────────────────────


@router.get("/{country_code}/staff")
def list_staff(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.post("/{country_code}/staff")
def assign_staff(
    country_code: str = Path(...),
    user_id: int = Body(...),
    role_in_country: str = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.delete("/{country_code}/staff/{staff_id}")
def remove_staff(
    country_code: str = Path(...),
    staff_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


# ── Category Tax Rates ────────────────────────────────────────────


@router.get("/{country_code}/tax-rates")
def list_tax_rates(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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


@router.post("/{country_code}/tax-rates")
def set_tax_rate(
    country_code: str = Path(...),
    category_id: int = Body(...),
    tax_rate: float = Body(...),
    tax_name: str = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
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
