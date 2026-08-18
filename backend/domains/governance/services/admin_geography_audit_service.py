"""Auto-migrated service logic from routers/admin_geography_audit.py."""
from __future__ import annotations

from typing import Optional, Any, Dict

from fastapi import Depends, Path, Query, Body

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.governance.services.auth_controller_service import get_current_user

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

def generate_legal_contract(country_code: str, template_type: str, db: Session, current_user):
    """Generate a legal contract for a country."""
    result = LegalContractService.generate_contract(country_code, template_type, db=db)
    return result

def get_audit_trail(country_code: str, table_name: Optional[str], record_id: Optional[int], limit: int, db: Session, current_user):
    """Get audit trail for a country."""
    trail = AuditTrailService.get_audit_trail(
        country_code,
        table_name=table_name,
        record_id=record_id,
        limit=limit
    )
    return trail

def log_financial_change(country_code: str, table_name: str, record_id: int, field_name: str, old_value: Any, new_value: Any, reason: str, user_id: Optional[int], metadata: Optional[Dict[str, Any]], db: Session, current_user):
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

def send_country_communication(country_code: str, to_user_id: int, subject: str, body: str, priority: str, category: str, related_entity_type: str, related_entity_id: int, db: Session, current_user):
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

def list_communications(status: Optional[str], priority: Optional[str], limit: int, db: Session, current_user):
    """Inbox: list communications for the current user, filtered by role+country."""
    return svc_list_communications(
        current_user,
        status=status,
        priority=priority,
        limit=limit,
        db=db,
    )

def mark_communication_read(comm_id: int, db: Session, current_user):
    return svc_mark_communication_read(comm_id, db=db)

def get_data_residency(country_code: str, db: Session, current_user):
    """Get data residency tier for a country."""
    from domains.governance.services.audit_trail_service import DataResidencyService
    tier = DataResidencyService.get_data_residency_tier(country_code)
    requires_encryption = DataResidencyService.requires_local_encryption(country_code)
    return {
        "country_code": country_code,
        "data_residency_tier": tier,
        "requires_local_encryption": requires_encryption
    }

def list_cities(country_code: str, active: bool, limit: int, db: Session, current_user):
    return svc_list_cities(country_code, active=active, limit=limit, db=db)

def add_city(country_code: str, name: str, name_local: str, population: int, is_capital: bool, latitude: float, longitude: float, db: Session, current_user):
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

def update_city(country_code: str, city_id: int, name: str, name_local: str, population: int, is_capital: bool, latitude: float, longitude: float, status: str, db: Session, current_user):
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

def delete_city(country_code: str, city_id: int, db: Session, current_user):
    return svc_delete_city(country_code, city_id, db=db)

def list_staff(country_code: str, db: Session, current_user):
    return svc_list_staff(country_code, db=db)

def assign_staff(country_code: str, user_id: int, role_in_country: str, db: Session, current_user):
    return svc_assign_staff(
        country_code,
        user_id=user_id,
        role_in_country=role_in_country,
        current_user=current_user,
        db=db,
    )

def remove_staff(country_code: str, staff_id: int, db: Session, current_user):
    return svc_remove_staff(country_code, staff_id, db=db)

def list_tax_rates(country_code: str, db: Session, current_user):
    return svc_list_tax_rates(country_code, db=db)

def set_tax_rate(country_code: str, category_id: int, tax_rate: float, tax_name: str, db: Session, current_user):
    return svc_set_tax_rate(
        country_code,
        category_id=category_id,
        tax_rate=tax_rate,
        tax_name=tax_name,
        db=db,
    )

