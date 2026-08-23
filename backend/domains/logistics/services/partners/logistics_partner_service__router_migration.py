"""Auto-migrated service logic from routers/logistics_partner.py."""
from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, File, Form, Query, Request, UploadFile

from pydantic import BaseModel

from sqlalchemy.orm import Session

import domains.orders.services.logistics_partner_controller as ctrl

from infrastructure.database.database import get_db

from infrastructure.utils.dependencies import get_current_user

class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None

class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None

def list_public_logistics_partners(request: Request, q: Optional[str], country: Optional[str], limit: int, db: Session):
    resolved_country = (
        country
        or request.headers.get("X-Country-Code")
        or getattr(request.state, "country_code", None)
    )
    return ctrl.list_public_partners(db, q=q, country=resolved_country, limit=limit)

def get_public_logistics_partner(partner_id: int, db: Session):
    return ctrl.get_public_partner(partner_id, db)

def get_partner_profile(db: Session, current_user: dict):
    return ctrl.get_my_partner_profile(current_user, db)

def update_partner_profile(data: dict, db: Session, current_user: dict):
    return ctrl.update_my_partner_profile(data, current_user, db)

def accept_partner_profile_terms(db: Session, current_user: dict):
    return ctrl.accept_partner_terms(current_user, db)

def submit_partner_profile_review(db: Session, current_user: dict):
    return ctrl.submit_partner_profile_for_review(current_user, db)

def get_partner_service_areas(partner_id: Optional[int], approval_status: Optional[str], db: Session, current_user: dict):
    return ctrl.list_my_partner_service_areas(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
    )

def get_partner_pricing_profiles(partner_id: Optional[int], approval_status: Optional[str], service_area_id: Optional[int], db: Session, current_user: dict):
    return ctrl.list_my_partner_pricing_profiles(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )

def get_partner_category_rules(partner_id: Optional[int], approval_status: Optional[str], service_area_id: Optional[int], db: Session, current_user: dict):
    return ctrl.list_my_partner_category_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )

def get_partner_vehicle_rules(partner_id: Optional[int], approval_status: Optional[str], service_area_id: Optional[int], db: Session, current_user: dict):
    return ctrl.list_my_partner_vehicle_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )

def get_partner_pricing_insights(partner_id: Optional[int], service_area_id: Optional[int], limit: int, db: Session, current_user: dict):
    return ctrl.get_partner_pricing_insights(
        current_user,
        db,
        partner_id=partner_id,
        service_area_id=service_area_id,
        limit=limit,
    )

def create_partner_pricing_profile(data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_pricing_profile(None, data, current_user, db)

def update_partner_pricing_profile(profile_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_pricing_profile(profile_id, data, current_user, db)

def delete_partner_pricing_profile(profile_id: int, db: Session, current_user: dict):
    return ctrl.delete_my_partner_pricing_profile(profile_id, current_user, db)

def create_partner_category_rule(data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_category_rule(None, data, current_user, db)

def update_partner_category_rule(rule_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_category_rule(rule_id, data, current_user, db)

def delete_partner_category_rule(rule_id: int, db: Session, current_user: dict):
    return ctrl.delete_my_partner_category_rule(rule_id, current_user, db)

def create_partner_vehicle_rule(data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_vehicle_rule(None, data, current_user, db)

def update_partner_vehicle_rule(rule_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_vehicle_rule(rule_id, data, current_user, db)

def delete_partner_vehicle_rule(rule_id: int, db: Session, current_user: dict):
    return ctrl.delete_my_partner_vehicle_rule(rule_id, current_user, db)

def create_partner_service_area(data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_service_area(None, data, current_user, db)

def update_partner_service_area(area_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.upsert_my_partner_service_area(area_id, data, current_user, db)

def delete_partner_service_area(area_id: int, db: Session, current_user: dict):
    return ctrl.delete_my_partner_service_area(area_id, current_user, db)

def review_logistics_partner_profile(partner_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.review_partner_profile(partner_id, data, current_user, db)

def review_logistics_partner_service_area(area_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.review_partner_service_area(area_id, data, current_user, db)

def review_logistics_partner_pricing_profile(profile_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.review_partner_pricing_profile(profile_id, data, current_user, db)

def review_logistics_partner_category_rule(rule_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.review_partner_category_rule(rule_id, data, current_user, db)

def review_logistics_partner_vehicle_rule(rule_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.review_partner_vehicle_rule(rule_id, data, current_user, db)

def get_logistics_shipping_quote(data: dict, db: Session, current_user: dict):
    return ctrl.shipping_quote_for_customer(data, db)

def list_partners(db: Session, current_user: dict):
    """Admin: list all logistics partners."""
    return ctrl.list_partners(current_user, db)

def create_partner(data: dict, db: Session, current_user: dict):
    """Admin: onboard a new logistics partner."""
    return ctrl.create_partner(data, current_user, db)

def bulk_manage_logistics_partners(body: BulkPartnerAdminActionRequest, db: Session, current_user: dict):
    """Admin bulk actions for logistics partner review and portal lifecycle."""
    return ctrl.bulk_manage_partners(body.partner_ids, body.action, body.note, current_user, db)

def update_partner(partner_id: int, data: dict, db: Session, current_user: dict):
    """Admin: update partner details or status."""
    return ctrl.update_partner(partner_id, data, current_user, db)

def delete_partner(partner_id: int, db: Session, current_user: dict):
    """Admin-only: remove a logistics partner."""
    return ctrl.delete_partner(partner_id, current_user, db)

def partner_dashboard(db: Session, current_user: dict):
    """Dashboard stats for logistics partner or admin."""
    return ctrl.get_partner_dashboard(current_user, db)

def partner_analytics(period: str, db: Session, current_user: dict):
    return ctrl.get_partner_analytics(current_user, db, period=period)

def partner_payouts(db: Session, current_user: dict):
    return ctrl.get_partner_payouts(current_user, db)

def request_payout(data: dict, db: Session, current_user: dict):
    return ctrl.request_partner_payout(data, current_user, db)

def pending_payouts(db: Session, current_user: dict):
    return ctrl.list_pending_partner_payouts(current_user, db)

def verify_payout(payout_id: int, data: dict, db: Session, current_user: dict):
    return ctrl.verify_partner_payout(payout_id, data, current_user, db)

def scan_lookup_shipment(code: str, db: Session, current_user: dict):
    """Look up a shipment by scan code or tracking number (logistics partners and admins)."""
    return ctrl.scan_lookup_shipment_partner(code, current_user, db)

def list_partner_shipments(status: Optional[str], page: int, page_size: int, db: Session, current_user: dict):
    """List shipments assigned to (or visible by) this logistics partner."""
    return ctrl.get_partner_shipments(current_user, db, status=status, page=page, page_size=page_size)

def update_shipment_status(shipment_id: int, data: dict, db: Session, current_user: dict):
    """Partner updates the status of a shipment (e.g., in_transit, delivered)."""
    return ctrl.update_shipment_status_partner(shipment_id, data, current_user, db)

def create_shipment_confirmation_request(shipment_id: int, data: dict, db: Session, current_user: dict):
    """Partner creates a pending pickup or delivery confirmation request."""
    return ctrl.create_shipment_confirmation_request_partner(shipment_id, data, current_user, db)

def bulk_update_shipments_status(body: BulkShipmentStatusRequest, db: Session, current_user: dict):
    """Bulk-update shipment status for multiple shipments (up to 100).
    Partners can only update their own assigned shipments.
    Note: 'delivered' requires signature — use the single-shipment endpoint instead.
    """
    return ctrl.bulk_update_shipment_status_partner(
        body.shipment_ids, body.status, body.notes, current_user, db
    )

def get_partner_bank_account(db: Session, current_user: dict):
    """Get the logistics partner's saved payout bank account."""
    return ctrl.get_partner_bank_account(current_user, db)

def upsert_partner_bank_account(body: dict, db: Session, current_user: dict):
    """Submit or update the logistics partner's payout bank account. Triggers admin verification."""
    return ctrl.upsert_partner_bank_account(body, current_user, db)

def list_my_cod_remittance_receipts(status: Optional[str], settlement_id: Optional[int], db: Session, current_user: dict):
    return ctrl.list_partner_cod_remittance_receipts(current_user, db, status=status, settlement_id=settlement_id)

async def upload_my_cod_remittance_receipt(settlement_id: int, amount: float, bank_reference: Optional[str], notes: Optional[str], file: UploadFile, db: Session, current_user: dict):
    return await ctrl.upload_partner_cod_remittance_receipt(
        settlement_id,
        amount,
        file,
        bank_reference,
        notes,
        current_user,
        db,
    )

def list_lp_documents(db: Session, current_user: dict):
    """List all KYC/compliance documents submitted by the authenticated logistics partner."""
    return ctrl.list_partner_documents(current_user, db)

async def upload_lp_document(file: UploadFile, document_type: str, document_name: str, expires_at: Optional[str], db: Session, current_user: dict):
    """Upload a KYC/compliance document (multipart/form-data)."""
    return await ctrl.upload_partner_document(file, document_type, document_name, expires_at, current_user, db)

def delete_lp_document(doc_id: int, db: Session, current_user: dict):
    """Delete a pending or rejected document."""
    return ctrl.delete_partner_document(doc_id, current_user, db)

def admin_review_lp_document(doc_id: int, body: dict, db: Session, current_user: dict):
    """Admin reviews a logistics partner document — approve/reject."""
    return ctrl.admin_review_lp_document(doc_id, body, current_user, db)

def list_city_distances(origin_country_code: Optional[str], destination_country_code: Optional[str], q: Optional[str], page: int, page_size: int, db: Session, current_user: dict):
    """Admin: list city distance matrix entries with optional filtering."""
    return ctrl.list_city_distances(current_user, db, origin_country_code=origin_country_code, destination_country_code=destination_country_code, q=q, page=page, page_size=page_size)

def create_city_distance(body: dict, db: Session, current_user: dict):
    """Admin: create a new city distance matrix entry."""
    return ctrl.create_city_distance(body, current_user, db)

def update_city_distance(matrix_id: int, body: dict, db: Session, current_user: dict):
    """Admin: update distance_km (and optional notes) for an existing entry."""
    return ctrl.update_city_distance(matrix_id, body, current_user, db)

def delete_city_distance(matrix_id: int, db: Session, current_user: dict):
    """Admin: delete a city distance matrix entry."""
    return ctrl.delete_city_distance(matrix_id, current_user, db)


