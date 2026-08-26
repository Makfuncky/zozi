from __future__ import annotations

"""Admin audit router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .compliance import router as compliance_router
from modules.admin.routers.audit import audit_actions, audit_log_page
from modules.admin.routers.accounts import get_current_user
from infrastructure.database.database import get_db
from domains.audit.services.ediscovery import get_ediscovery_service
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import require_admin
from domains.audit.services.logs.audit_trail_service import AuditTrailService
from domains.audit.services.logs.audit_trail_service import DataResidencyService
from domains.suppliers.services.legal_contract_service import LegalContractService
from sqlalchemy.orm import Session
from typing import Optional
from typing import Optional, Any, Dict

router = APIRouter(prefix="/api/v1/admin/audit", tags=["admin", "audit"])

@router.get("/audit/{country_code}", status_code=200, tags=['admin-audit'])
def audit_log_page_route(
    country_code: str,
    page: int = Query(1),
    page_size: int = Query(50),
    action_filter: Optional[str] = Query(None),
    user_id_filter: Optional[int] = Query(None),
    resource_type_filter: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.get("/audit/{country_code}/actions", status_code=200, tags=['admin-audit'])
def audit_actions_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.get("/search")
async def search_audit_trail(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = get_ediscovery_service(db)
    return service.search_audit_trail(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_entity_timeline(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = get_ediscovery_service(db)
    return service.get_entity_timeline(entity_type, entity_id)


@router.get("/export/{entity_type}/{entity_id}")
async def export_for_legal(
    entity_type: str,
    entity_id: int,
    format: str = Query("json"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = get_ediscovery_service(db)
    return service.export_for_legal(entity_type, entity_id, format)


@router.get("/{country_code}/legal-contracts/generate")
def generate_legal_contract(
    country_code: str = Path(..., description="Country code"),
    template_type: str = Query("terms", description="Template type (terms, privacy, refund)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.get("/{country_code}/audit-trail", response_model=list[dict])
def get_audit_trail(
    country_code: str = Path(..., description="Country code"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    record_id: Optional[int] = Query(None, description="Filter by record ID"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


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


@router.get("/communications")
def list_communications(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.put("/communications/{comm_id}/read")
def mark_communication_read(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/data-residency")
def get_data_residency(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.get("/{country_code}/cities")
def list_cities(
    country_code: str = Path(...),
    active: bool = Query(True),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


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


@router.delete("/{country_code}/cities/{city_id}")
def delete_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/staff")
def list_staff(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/staff")
def assign_staff(
    country_code: str = Path(...),
    user_id: int = Body(...),
    role_in_country: str = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.delete("/{country_code}/staff/{staff_id}")
def remove_staff(
    country_code: str = Path(...),
    staff_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/tax-rates")
def list_tax_rates(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/tax-rates")
def set_tax_rate(
    country_code: str = Path(...),
    category_id: int = Body(...),
    tax_rate: float = Body(...),
    tax_name: str = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),

