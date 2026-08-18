"""
Country Admin Router
Endpoints for legal contracts, audit trails, and country management.
"""
from typing import Optional, Any, Dict

from fastapi import APIRouter, Depends, Path, Query, Body
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac import get_current_user
from domains.suppliers.services.legal_contract_service import LegalContractService
from domains.governance.services.audit_trail_service import AuditTrailService
from domains.country.services.country_audit_admin_service import add_city as svc_add_city
from domains.country.services.country_audit_admin_service import assign_staff as svc_assign_staff
from domains.country.services.country_audit_admin_service import delete_city as svc_delete_city
from domains.country.services.country_audit_admin_service import list_cities as svc_list_cities
from domains.country.services.country_audit_admin_service import list_communications as svc_list_communications
from domains.country.services.country_audit_admin_service import list_staff as svc_list_staff
from domains.country.services.country_audit_admin_service import list_tax_rates as svc_list_tax_rates
from domains.country.services.country_audit_admin_service import mark_communication_read as svc_mark_communication_read
from domains.country.services.country_audit_admin_service import remove_staff as svc_remove_staff
from domains.country.services.country_audit_admin_service import send_country_communication as svc_send_country_communication
from domains.country.services.country_audit_admin_service import set_tax_rate as svc_set_tax_rate
from domains.country.services.country_audit_admin_service import update_city as svc_update_city

router = APIRouter(tags=["country-admin"], prefix="/api/v1/admin")


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


@router.get("/{country_code}/audit-trail", response_model=list[dict])
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
    return svc_send_country_communication(
        country_code,
        current_user,
        to_user_id=to_user_id,
        subject=subject,
        body=body,
        priority=priority,
        category=category,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        db=db,
    )


@router.get("/communications")
def list_communications(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Inbox: list communications for the current user, filtered by role+country."""
    return svc_list_communications(
        current_user,
        status=status,
        priority=priority,
        limit=limit,
        db=db,
    )


@router.put("/communications/{comm_id}/read")
def mark_communication_read(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return svc_mark_communication_read(comm_id, db=db)


@router.get("/{country_code}/data-residency")
def get_data_residency(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get data residency tier for a country."""
    from domains.governance.services.audit_trail_service import DataResidencyService
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
    return svc_list_cities(country_code, active=active, limit=limit, db=db)


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
    return svc_add_city(
        country_code,
        name=name,
        name_local=name_local,
        population=population,
        is_capital=is_capital,
        latitude=latitude,
        longitude=longitude,
        db=db,
    )


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
    return svc_update_city(
        country_code,
        city_id,
        name=name,
        name_local=name_local,
        population=population,
        is_capital=is_capital,
        latitude=latitude,
        longitude=longitude,
        status=status,
        db=db,
    )


@router.delete("/{country_code}/cities/{city_id}")
def delete_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return svc_delete_city(country_code, city_id, db=db)


# ── Staff Assignment Management ───────────────────────────────────


@router.get("/{country_code}/staff")
def list_staff(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return svc_list_staff(country_code, db=db)


@router.post("/{country_code}/staff")
def assign_staff(
    country_code: str = Path(...),
    user_id: int = Body(...),
    role_in_country: str = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return svc_assign_staff(
        country_code,
        user_id=user_id,
        role_in_country=role_in_country,
        current_user=current_user,
        db=db,
    )


@router.delete("/{country_code}/staff/{staff_id}")
def remove_staff(
    country_code: str = Path(...),
    staff_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return svc_remove_staff(country_code, staff_id, db=db)


# ── Category Tax Rates ────────────────────────────────────────────


@router.get("/{country_code}/tax-rates")
def list_tax_rates(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return svc_list_tax_rates(country_code, db=db)


@router.post("/{country_code}/tax-rates")
def set_tax_rate(
    country_code: str = Path(...),
    category_id: int = Body(...),
    tax_rate: float = Body(...),
    tax_name: str = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return svc_set_tax_rate(
        country_code,
        category_id=category_id,
        tax_rate=tax_rate,
        tax_name=tax_name,
        db=db,
    )
