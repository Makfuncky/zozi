from __future__ import annotations

# -------------------------------------------------------------------
# FROM: logistics_partner_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/logistics_partner.py."""

from typing import List, Optional

from fastapi import Depends, File, Form, Query, Request, UploadFile

from pydantic import BaseModel

from sqlalchemy.orm import Session

import domains.logistics.services.partners.logistics_partner_service as ctrl

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



# -------------------------------------------------------------------
# FROM: logistics_partner_service__router_migration.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/logistics_partner.py."""

from typing import List, Optional

from fastapi import Depends, File, Form, Query, Request, UploadFile

from pydantic import BaseModel

from sqlalchemy.orm import Session

import domains.logistics.services.partners.logistics_partner_service as ctrl

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



# -------------------------------------------------------------------
# FROM: logistics_partner_pricing.py
# -------------------------------------------------------------------


from decimal import Decimal
from typing import Any, Optional, cast

from sqlalchemy import desc
from sqlalchemy.orm import Session

from domains.governance.models.core import CityDistanceMatrix
from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsCategoryPricingRule
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.orders.models.orders import Order
from kernel.money import round_money, to_decimal


APPROVED_PROFILE_STATUS = "approved"
APPROVED_AREA_STATUS = "approved"
APPROVED_PRICING_PROFILE_STATUS = "approved"
APPROVED_CATEGORY_RULE_STATUS = "approved"
APPROVED_VEHICLE_RULE_STATUS = "approved"
DEFAULT_VEHICLE_MULTIPLIERS = {
    "bike": Decimal("0.90"),
    "car": Decimal("1.00"),
    "van": Decimal("1.20"),
    "truck": Decimal("1.50"),
}


def lookup_city_distance_km(
    db: Session,
    *,
    origin_country_code: str | None,
    origin_city_name: str | None,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> Decimal:
    """Return the distance in km between an origin/destination city pair.

    Matching is case-insensitive and whitespace-normalised.  Returns ``Decimal(0)``
    when no matching row exists in ``city_distance_matrix``.
    """
    if not (origin_country_code and origin_city_name and destination_country_code and destination_city_name):
        return Decimal("0")

    origin_cc = normalize_country_code(origin_country_code)
    dest_cc = normalize_country_code(destination_country_code)
    origin_key = normalize_city_name(origin_city_name)
    dest_key = normalize_city_name(destination_city_name)

    # SQLite stores text; we normalise both sides at query time.
    row = (
        db.query(CityDistanceMatrix)
        .filter(
            CityDistanceMatrix.origin_country_code == origin_cc,
            CityDistanceMatrix.destination_country_code == dest_cc,
        )
        .all()
    )
    for entry in row:
        if (
            normalize_city_name(cast(str | None, getattr(entry, "origin_city_name", None))) == origin_key
            and normalize_city_name(cast(str | None, getattr(entry, "destination_city_name", None))) == dest_key
        ):
            return to_decimal(getattr(entry, "distance_km", 0) or 0)
    return Decimal("0")


def serialize_pricing_profile(profile: LogisticsPricingProfile) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(profile, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(profile, "created_at", None))
    updated_at = cast(Optional[Any], getattr(profile, "updated_at", None))
    return {
        "id": profile.id,
        "partner_id": profile.partner_id,
        "service_area_id": profile.service_area_id,
        "profile_name": profile.profile_name,
        "base_in_city_fee": float(profile.base_in_city_fee) if getattr(profile, "base_in_city_fee", None) is not None else None,
        "base_inter_city_fee": float(profile.base_inter_city_fee) if getattr(profile, "base_inter_city_fee", None) is not None else None,
        "per_km_rate": float(profile.per_km_rate) if getattr(profile, "per_km_rate", None) is not None else None,
        "per_kg_rate": float(profile.per_kg_rate) if getattr(profile, "per_kg_rate", None) is not None else None,
        "minimum_charge": float(profile.minimum_charge) if getattr(profile, "minimum_charge", None) is not None else None,
        "maximum_charge": float(profile.maximum_charge) if getattr(profile, "maximum_charge", None) is not None else None,
        "fuel_multiplier": float(profile.fuel_multiplier) if getattr(profile, "fuel_multiplier", None) is not None else 1.0,
        "bulk_discount_threshold_kg": float(profile.bulk_discount_threshold_kg) if getattr(profile, "bulk_discount_threshold_kg", None) is not None else None,
        "bulk_discount_percent": float(profile.bulk_discount_percent) if getattr(profile, "bulk_discount_percent", None) is not None else None,
        "currency": profile.currency,
        "is_active": bool(profile.is_active),
        "approval_status": profile.approval_status,
        "review_note": profile.review_note,
        "reviewed_by": profile.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def normalize_category_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def normalize_vehicle_type(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def vehicle_baseline_multiplier(vehicle_type: str | None) -> Decimal:
    normalized = normalize_vehicle_type(vehicle_type)
    return DEFAULT_VEHICLE_MULTIPLIERS.get(normalized, Decimal("1.00"))


def normalize_pricing_breakdown_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    data = dict(payload)
    legacy_keys = {
        "applied_category_name",
        "applied_category_rule_id",
        "bulk_discount_amount",
        "bulk_discount_percent",
        "bulk_discount_threshold_kg",
        "category_adjustment_amount",
        "category_extra",
        "category_rule_ids",
        "dropoff_charge",
        "fuel_adjustment_amount",
        "fuel_multiplier",
        "matched_categories",
        "maximum_charge",
        "maximum_charge_applied",
        "minimum_charge",
        "minimum_charge_applied",
        "pickup_charge",
        "pricing_schema_version",
        "special_handling_fee",
        "subtotal_before_fuel",
        "total_category_extra",
        "vehicle_adjustment_amount",
        "vehicle_multiplier",
        "vehicle_rule_id",
        "vehicle_type",
    }
    normalized = {key: value for key, value in data.items() if key not in legacy_keys}

    handling_fee = data.get("handling_fee")
    if handling_fee is None:
        if data.get("total_category_extra") is not None:
            handling_fee = data.get("total_category_extra")
        elif data.get("category_adjustment_amount") is not None:
            handling_fee = data.get("category_adjustment_amount")
        else:
            handling_fee = max(float(data.get("category_extra") or 0), float(data.get("special_handling_fee") or 0))

    pricing_schema_version = str(data.get("pricing_schema_version") or "").strip().lower()
    pricing_model = data.get("pricing_model")
    if not pricing_model:
        pricing_model = "operational_load_fit" if pricing_schema_version == "v1_operational_vehicle_multiplier" else "customer_weight_route"

    load_fit_factor = data.get("load_fit_factor")
    if load_fit_factor is None:
        load_fit_factor = data.get("vehicle_multiplier")
    if load_fit_factor is None:
        load_fit_factor = 1.0

    surcharge_factor = data.get("surcharge_factor")
    if surcharge_factor is None:
        surcharge_factor = data.get("fuel_multiplier")
    if surcharge_factor is None:
        surcharge_factor = 1.0

    normalized.update({
        "base_fee": data.get("base_fee", 0.0),
        "pickup_fee": data.get("pickup_fee", data.get("pickup_charge", 0.0)),
        "dropoff_fee": data.get("dropoff_fee", data.get("dropoff_charge", 0.0)),
        "pickup_count": data.get("pickup_count", 1),
        "dropoff_count": data.get("dropoff_count", 1),
        "extra_pickup_count": data.get("extra_pickup_count", 0),
        "extra_dropoff_count": data.get("extra_dropoff_count", 0),
        "pickup_fee_per_stop": data.get("pickup_fee_per_stop", 0.0),
        "dropoff_fee_per_stop": data.get("dropoff_fee_per_stop", 0.0),
        "route_type": data.get("route_type", "in_city"),
        "is_in_city": bool(data.get("is_in_city", data.get("route_type") == "in_city")),
        "weight_fee": data.get("weight_fee", 0.0),
        "per_kg_rate": data.get("per_kg_rate"),
        "distance_km": data.get("distance_km"),
        "per_km_rate": data.get("per_km_rate"),
        "distance_fee": data.get("distance_fee", 0.0),
        "handling_fee": handling_fee,
        "subtotal_core": data.get("subtotal_core", 0.0),
        "load_fit_factor": load_fit_factor,
        "load_fit_adjustment_amount": data.get("load_fit_adjustment_amount", data.get("vehicle_adjustment_amount", 0.0)),
        "pricing_model": pricing_model,
        "subtotal_before_surcharge": data.get("subtotal_before_surcharge", data.get("subtotal_before_fuel", data.get("subtotal_core", 0.0))),
        "surcharge_factor": surcharge_factor,
        "surcharge_amount": data.get("surcharge_amount", data.get("fuel_adjustment_amount", 0.0)),
        "floor_charge": data.get("floor_charge", data.get("minimum_charge")),
        "floor_applied": bool(data.get("floor_applied", data.get("minimum_charge_applied", False))),
        "ceiling_charge": data.get("ceiling_charge", data.get("maximum_charge")),
        "ceiling_applied": bool(data.get("ceiling_applied", data.get("maximum_charge_applied", False))),
        "weight_discount_threshold_kg": data.get("weight_discount_threshold_kg", data.get("bulk_discount_threshold_kg")),
        "weight_discount_percent": data.get("weight_discount_percent", data.get("bulk_discount_percent")),
        "weight_discount_amount": data.get("weight_discount_amount", data.get("bulk_discount_amount", 0.0)),
        "pricing_profile_id": data.get("pricing_profile_id"),
        "handling_rule_ids": data.get("handling_rule_ids", data.get("category_rule_ids", [])),
        "applied_handling_rule_id": data.get("applied_handling_rule_id", data.get("applied_category_rule_id")),
        "applied_handling_label": data.get("applied_handling_label", data.get("applied_category_name")),
        "matched_handling_labels": data.get("matched_handling_labels", data.get("matched_categories", [])),
        "load_fit_rule_id": data.get("load_fit_rule_id", data.get("vehicle_rule_id")),
        "load_fit_label": data.get("load_fit_label", data.get("vehicle_type")),
        "total_weight_kg": data.get("total_weight_kg", 0.0),
        "total_volume_cm3": data.get("total_volume_cm3", 0.0),
        "shipping_amount": data.get("shipping_amount", 0.0),
    })
    return normalized


def parse_dimensions_to_volume_cm3(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    cleaned = str(value).lower().replace("cm", " ").replace("x", " ").replace("*", " ")
    parts: list[Decimal] = []
    for token in cleaned.split():
        try:
            parts.append(to_decimal(token))
        except Exception:
            continue
        if len(parts) == 3:
            break
    if len(parts) != 3:
        return Decimal("0")
    length, width, height = parts
    if length <= 0 or width <= 0 or height <= 0:
        return Decimal("0")
    return round_money(length * width * height)


def serialize_category_pricing_rule(rule: LogisticsCategoryPricingRule) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(rule, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(rule, "created_at", None))
    updated_at = cast(Optional[Any], getattr(rule, "updated_at", None))
    return {
        "id": rule.id,
        "partner_id": rule.partner_id,
        "service_area_id": rule.service_area_id,
        "category_name": rule.category_name,
        "flat_fee_override": float(rule.flat_fee_override) if getattr(rule, "flat_fee_override", None) is not None else None,
        "special_handling_fee": float(rule.special_handling_fee) if getattr(rule, "special_handling_fee", None) is not None else None,
        "currency": rule.currency,
        "is_active": bool(rule.is_active),
        "approval_status": rule.approval_status,
        "review_note": rule.review_note,
        "reviewed_by": rule.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def serialize_vehicle_rule(rule: LogisticsVehicleRule) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(rule, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(rule, "created_at", None))
    updated_at = cast(Optional[Any], getattr(rule, "updated_at", None))
    return {
        "id": rule.id,
        "partner_id": rule.partner_id,
        "service_area_id": rule.service_area_id,
        "route_scope": getattr(rule, "route_scope", "any"),
        "vehicle_type": rule.vehicle_type,
        "max_weight_kg": float(rule.max_weight_kg) if getattr(rule, "max_weight_kg", None) is not None else None,
        "max_volume_cm3": float(rule.max_volume_cm3) if getattr(rule, "max_volume_cm3", None) is not None else None,
        "cost_multiplier": float(rule.cost_multiplier),
        "priority_rank": rule.priority_rank,
        "is_active": bool(rule.is_active),
        "approval_status": rule.approval_status,
        "review_note": rule.review_note,
        "reviewed_by": rule.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def resolve_category_rules_for_area(
    db: Session,
    area: LogisticsPartnerServiceArea,
    categories: list[str] | None,
) -> list[LogisticsCategoryPricingRule]:
    normalized_categories = [normalize_category_name(category) for category in (categories or []) if normalize_category_name(category)]
    if not normalized_categories:
        return []

    rows = (
        db.query(LogisticsCategoryPricingRule)
        .filter(
            LogisticsCategoryPricingRule.partner_id == area.partner_id,
            LogisticsCategoryPricingRule.is_active == True,  # noqa: E712
            LogisticsCategoryPricingRule.approval_status == APPROVED_CATEGORY_RULE_STATUS,
        )
        .order_by(desc(LogisticsCategoryPricingRule.updated_at), desc(LogisticsCategoryPricingRule.id))
        .all()
    )

    resolved: dict[str, LogisticsCategoryPricingRule] = {}
    for category in normalized_categories:
        exact_match = next(
            (
                row for row in rows
                if getattr(row, "service_area_id", None) == area.id
                and normalize_category_name(cast(str | None, getattr(row, "category_name", None))) == category
            ),
            None,
        )
        if exact_match is not None:
            resolved[category] = exact_match
            continue
        fallback = next(
            (
                row for row in rows
                if getattr(row, "service_area_id", None) is None
                and normalize_category_name(cast(str | None, getattr(row, "category_name", None))) == category
            ),
            None,
        )
        if fallback is not None:
            resolved[category] = fallback

    return [resolved[category] for category in normalized_categories if category in resolved]


def resolve_vehicle_rule_for_area(
    db: Session,
    area: LogisticsPartnerServiceArea,
    *,
    route_type: str,
    total_weight_kg: Decimal | float | int | None,
    total_volume_cm3: Decimal | float | int | None,
    preferred_vehicle_type: str | None = None,
) -> LogisticsVehicleRule | None:
    weight = max(round_money(to_decimal(total_weight_kg or 0)), Decimal("0"))
    volume = max(round_money(to_decimal(total_volume_cm3 or 0)), Decimal("0"))
    preferred_vehicle_key = normalize_vehicle_type(preferred_vehicle_type)
    rows = (
        db.query(LogisticsVehicleRule)
        .filter(
            LogisticsVehicleRule.partner_id == area.partner_id,
            LogisticsVehicleRule.is_active == True,  # noqa: E712
            LogisticsVehicleRule.approval_status == APPROVED_VEHICLE_RULE_STATUS,
        )
        .all()
    )
    candidates = []
    for row in rows:
        service_area_id = getattr(row, "service_area_id", None)
        if service_area_id not in (None, area.id):
            continue
        row_route_scope = str(getattr(row, "route_scope", "any") or "any").strip().lower()
        if row_route_scope not in {"any", route_type}:
            continue
        if preferred_vehicle_key and normalize_vehicle_type(cast(str | None, getattr(row, "vehicle_type", None))) != preferred_vehicle_key:
            continue
        max_weight = cast(Decimal | float | int | None, getattr(row, "max_weight_kg", None))
        max_volume = cast(Decimal | float | int | None, getattr(row, "max_volume_cm3", None))
        if max_weight is not None and weight > round_money(to_decimal(max_weight)):
            continue
        if max_volume is not None and volume > round_money(to_decimal(max_volume)):
            continue
        candidates.append(row)

    if not candidates:
        return None

    candidates.sort(
        key=lambda row: (
            0 if getattr(row, "service_area_id", None) == area.id else 1,
            0 if str(getattr(row, "route_scope", "any") or "any").strip().lower() == route_type else 1,
            int(getattr(row, "priority_rank", 100) or 100),
            int(getattr(row, "id", 0) or 0),
        )
    )
    return candidates[0]


def resolve_pricing_profile_for_area(db: Session, area: LogisticsPartnerServiceArea) -> LogisticsPricingProfile | None:
    rows = (
        db.query(LogisticsPricingProfile)
        .filter(
            LogisticsPricingProfile.partner_id == area.partner_id,
            LogisticsPricingProfile.is_active == True,  # noqa: E712
            LogisticsPricingProfile.approval_status == APPROVED_PRICING_PROFILE_STATUS,
        )
        .order_by(desc(LogisticsPricingProfile.updated_at), desc(LogisticsPricingProfile.id))
        .all()
    )
    exact = [row for row in rows if getattr(row, "service_area_id", None) == area.id]
    if exact:
        return exact[0]
    fallback = [row for row in rows if getattr(row, "service_area_id", None) is None]
    return fallback[0] if fallback else None


def _resolve_route_context(
    area: LogisticsPartnerServiceArea,
    *,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> dict[str, Any]:
    origin_country_code = normalize_country_code(cast(str | None, getattr(area, "country_code", None)))
    origin_city_name = cast(str | None, getattr(area, "origin_city", None))
    destination_country = normalize_country_code(destination_country_code)
    origin_city_key = normalize_city_name(origin_city_name)
    destination_city_key = normalize_city_name(destination_city_name)
    is_in_city = bool(
        origin_country_code
        and destination_country
        and origin_country_code == destination_country
        and origin_city_key
        and destination_city_key
        and origin_city_key == destination_city_key
    )
    return {
        "origin_country_code": origin_country_code or None,
        "origin_city_name": origin_city_name,
        "destination_country_code": destination_country or None,
        "destination_city_name": destination_city_name,
        "is_in_city": is_in_city,
        "route_type": "in_city" if is_in_city else "inter_city",
    }


def _build_service_area_pricing_breakdown(
    area: LogisticsPartnerServiceArea,
    *,
    pricing_profile: LogisticsPricingProfile | None = None,
    category_rules: list[LogisticsCategoryPricingRule] | None = None,
    vehicle_rule: LogisticsVehicleRule | None = None,
    vehicle_type_override: str | None = None,
    vehicle_multiplier_override: Decimal | float | int | None = None,
    vehicle_rule_id_override: int | None = None,
    apply_vehicle_multiplier: bool = True,
    categories: list[str] | None = None,
    total_weight_kg: Decimal | float | int | None = None,
    total_volume_cm3: Decimal | float | int | None = None,
    pickup_count: int | None = None,
    dropoff_count: int | None = None,
    distance_km: Decimal | float | int | None = None,
    destination_country_code: str | None = None,
    destination_city_name: str | None = None,
) -> dict[str, Any]:
    route_context = _resolve_route_context(
        area,
        destination_country_code=destination_country_code,
        destination_city_name=destination_city_name,
    )
    raw_minimum_charge = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "minimum_charge", None) if getattr(pricing_profile, "minimum_charge", None) is not None else getattr(area, "minimum_charge", None),
    )
    raw_per_kg_rate = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "per_kg_rate", None) if getattr(pricing_profile, "per_kg_rate", None) is not None else getattr(area, "per_kg_rate", None),
    )
    raw_per_km_rate = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "per_km_rate", None) if getattr(pricing_profile, "per_km_rate", None) is not None else getattr(area, "per_km_rate", None),
    )
    raw_fuel_multiplier = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "fuel_multiplier", None) if getattr(pricing_profile, "fuel_multiplier", None) is not None else getattr(area, "fuel_multiplier", None),
    )
    raw_bulk_discount_threshold = cast(Decimal | float | int | None, getattr(pricing_profile, "bulk_discount_threshold_kg", None))
    raw_bulk_discount_percent = cast(Decimal | float | int | None, getattr(pricing_profile, "bulk_discount_percent", None))

    profile_base = None
    if pricing_profile is not None:
        profile_base = getattr(pricing_profile, "base_in_city_fee", None) if route_context["is_in_city"] else getattr(pricing_profile, "base_inter_city_fee", None)
    pickup_fee_per_stop = round_money(to_decimal(getattr(area, "pickup_charge", None) or 0))
    dropoff_fee_per_stop = round_money(to_decimal(getattr(area, "dropoff_charge", None) or 0))
    resolved_pickup_count = max(int(pickup_count if pickup_count is not None else 1), 0)
    resolved_dropoff_count = max(int(dropoff_count if dropoff_count is not None else 1), 0)
    # First pickup and first dropoff are included in the base fee; only extra stops are charged.
    extra_pickups = max(resolved_pickup_count - 1, 0)
    extra_dropoffs = max(resolved_dropoff_count - 1, 0)
    pickup_fee = round_money(pickup_fee_per_stop * to_decimal(extra_pickups))
    dropoff_fee = round_money(dropoff_fee_per_stop * to_decimal(extra_dropoffs))
    resolved_base_fee = round_money(to_decimal(profile_base if profile_base is not None else getattr(area, "charge_amount", None) or 0))
    total_weight = max(round_money(to_decimal(total_weight_kg or 0)), Decimal("0"))
    total_volume = max(round_money(to_decimal(total_volume_cm3 or 0)), Decimal("0"))

    category_rules = category_rules or []

    # Category handling is intentionally simplified for the business-facing rate card.
    # Legacy rules may still store two numbers (flat fee + handling fee), but the
    # customer-facing quote collapses them into one handling amount per rule by taking
    # the stronger configured charge. Across multiple matched rules, only the single
    # highest collapsed handling amount is applied.
    category_extra = Decimal("0")
    special_handling_fee = Decimal("0")
    applied_category_rule = None
    highest_category_total = Decimal("0")
    for rule in category_rules:
        rule_category_extra = round_money(to_decimal(getattr(rule, "flat_fee_override", None) or 0))
        rule_special_handling = round_money(to_decimal(getattr(rule, "special_handling_fee", None) or 0))
        rule_total = round_money(max(rule_category_extra, rule_special_handling))
        if rule_total > highest_category_total:
            highest_category_total = rule_total
            category_extra = Decimal("0")
            special_handling_fee = rule_total
            applied_category_rule = rule

    total_category_extra = round_money(category_extra + special_handling_fee)

    # STEP 1 — Base fee (in-city) or STEP 2 — Distance cost (inter-city).
    # resolved_base_fee is already set to base_in_city_fee (in-city) or base_inter_city_fee (inter-city)
    # by the profile_base lookup above. These two are mutually exclusive by route_type.
    base_fee = resolved_base_fee

    # STEP 3 — Weight cost. Calculated once from global per_kg_rate. Never overridden by category rules.
    per_kg_rate = round_money(to_decimal(raw_per_kg_rate or 0))
    weight_fee = round_money(total_weight * per_kg_rate) if total_weight > 0 and per_kg_rate > 0 else Decimal("0")

    # STEP 2 (distance component) — inter-city only.
    # When base_inter_city_fee is set and per_km_rate is null, distance_fee stays 0 (flat-rate mode).
    # When per_km_rate is set, distance_fee = distance_km x per_km_rate (per-km mode).
    resolved_distance = max(round_money(to_decimal(distance_km or 0)), Decimal("0"))
    per_km_rate = to_decimal(raw_per_km_rate or 0)
    distance_fee = round_money(resolved_distance * per_km_rate) if resolved_distance > 0 and per_km_rate > 0 else Decimal("0")

    # Core additive subtotal: (base OR distance) + weight + category.
    # base_fee and distance_fee are mutually exclusive by route_type — only one is non-zero at a time.
    subtotal_core = round_money(base_fee + distance_fee + weight_fee + total_category_extra)

    # Pickup / drop-off surcharges: additive exceptional access charges.
    # These are 0 for standard routes and non-zero only for explicitly configured exceptional areas.
    subtotal_before_multipliers = round_money(subtotal_core + pickup_fee + dropoff_fee)

    # STEP 5 — Vehicle multiplier is optional.
    # Customer-facing quotes keep the formula weight-first and route-first.
    # Operational acceptance flows can still opt in to multiplier-based snapshots.
    resolved_vehicle_multiplier = to_decimal(
        vehicle_multiplier_override
        if vehicle_multiplier_override is not None
        else getattr(vehicle_rule, "cost_multiplier", None) or 1
    )
    vehicle_multiplier = resolved_vehicle_multiplier if apply_vehicle_multiplier else Decimal("1")
    subtotal_after_vehicle = round_money(subtotal_before_multipliers * vehicle_multiplier)

    # STEP 6 — Fuel multiplier.
    fuel_multiplier = to_decimal(raw_fuel_multiplier or 1)
    fuel_adjusted_total = round_money(subtotal_after_vehicle * fuel_multiplier)

    # STEP 7 — Minimum charge floor.
    minimum_charge = round_money(to_decimal(raw_minimum_charge or 0))
    total_after_minimum = round_money(max(fuel_adjusted_total, minimum_charge))

    # Maximum charge ceiling (guardrail) — clamps the total from above when set.
    raw_maximum_charge = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "maximum_charge", None) if pricing_profile is not None else None,
    )
    maximum_charge_limit = round_money(to_decimal(raw_maximum_charge)) if raw_maximum_charge is not None else None
    maximum_charge_applied = False
    if maximum_charge_limit is not None and maximum_charge_limit > 0 and total_after_minimum > maximum_charge_limit:
        total_after_minimum = maximum_charge_limit
        maximum_charge_applied = True

    # Bulk discount (optional, applied after floor/ceiling guardrails).
    # The discount is restricted to the weight fee so route and stop charges stay stable.
    bulk_discount_threshold = round_money(to_decimal(raw_bulk_discount_threshold or 0))
    bulk_discount_percent = round_money(to_decimal(raw_bulk_discount_percent or 0))
    bulk_discount_amount = Decimal("0")
    if bulk_discount_threshold > 0 and bulk_discount_percent > 0 and total_weight >= bulk_discount_threshold:
        bulk_discount_amount = round_money(weight_fee * (bulk_discount_percent / Decimal("100")))
    final_charge = round_money(max(total_after_minimum - bulk_discount_amount, Decimal("0")))

    return normalize_pricing_breakdown_payload({
        "base_fee": float(base_fee),
        "pickup_count": resolved_pickup_count,
        "dropoff_count": resolved_dropoff_count,
        "extra_pickup_count": extra_pickups,
        "extra_dropoff_count": extra_dropoffs,
        "pickup_fee_per_stop": float(pickup_fee_per_stop),
        "dropoff_fee_per_stop": float(dropoff_fee_per_stop),
        "pickup_fee": float(pickup_fee),
        "dropoff_fee": float(dropoff_fee),
        "route_type": route_context["route_type"],
        "is_in_city": route_context["is_in_city"],
        "currency": getattr(pricing_profile, "currency", None) or getattr(area, "currency", None),
        "weight_fee": float(weight_fee),
        "per_kg_rate": float(per_kg_rate) if raw_per_kg_rate is not None else None,
        "distance_km": float(resolved_distance) if distance_km is not None else None,
        "per_km_rate": float(per_km_rate) if raw_per_km_rate is not None else None,
        "distance_fee": float(distance_fee),
        "category_extra": float(category_extra),
        "special_handling_fee": float(special_handling_fee),
        "total_category_extra": float(total_category_extra),
        "subtotal_core": float(subtotal_core),
        "vehicle_multiplier": float(vehicle_multiplier),
        "vehicle_adjustment_amount": float(round_money(subtotal_after_vehicle - subtotal_before_multipliers)),
        "pricing_schema_version": "v1_operational_vehicle_multiplier" if apply_vehicle_multiplier else "v2_weight_first_customer_charge",
        "subtotal_before_fuel": float(subtotal_after_vehicle),
        "fuel_multiplier": float(fuel_multiplier),
        "fuel_adjustment_amount": float(round_money(fuel_adjusted_total - subtotal_after_vehicle)),
        "minimum_charge": float(minimum_charge) if raw_minimum_charge is not None else None,
        "minimum_charge_applied": raw_minimum_charge is not None and total_after_minimum == minimum_charge and minimum_charge > fuel_adjusted_total,
        "maximum_charge": float(maximum_charge_limit) if maximum_charge_limit is not None else None,
        "maximum_charge_applied": maximum_charge_applied,
        "bulk_discount_threshold_kg": float(bulk_discount_threshold) if raw_bulk_discount_threshold is not None else None,
        "bulk_discount_percent": float(bulk_discount_percent) if raw_bulk_discount_percent is not None else None,
        "bulk_discount_amount": float(bulk_discount_amount),
        "pricing_profile_id": getattr(pricing_profile, "id", None),
        "category_rule_ids": [getattr(applied_category_rule, "id", None)] if applied_category_rule is not None else [],
        "applied_category_rule_id": getattr(applied_category_rule, "id", None) if applied_category_rule is not None else None,
        "applied_category_name": getattr(applied_category_rule, "category_name", None) if applied_category_rule is not None else None,
        "matched_categories": [normalize_category_name(category) for category in (categories or []) if normalize_category_name(category)],
        "vehicle_rule_id": vehicle_rule_id_override if vehicle_rule_id_override is not None else getattr(vehicle_rule, "id", None),
        "vehicle_type": vehicle_type_override if vehicle_type_override is not None else getattr(vehicle_rule, "vehicle_type", None),
        "total_weight_kg": float(total_weight),
        "total_volume_cm3": float(total_volume),
        "shipping_amount": float(final_charge),
    })


_COUNTRY_CODE_ALIASES: dict[str, str] = {
    "AE": "AE",
    "UAE": "AE",
    "UNITEDARABEMIRATES": "AE",
    "EMIRATES": "AE",
    "PK": "PK",
    "PAKISTAN": "PK",
    "OM": "OM",
    "OMAN": "OM",
    "SA": "SA",
    "SAUDIARABIA": "SA",
    "KSA": "SA",
    "IN": "IN",
    "INDIA": "IN",
    "US": "US",
    "USA": "US",
    "UNITEDSTATES": "US",
    "UNITEDSTATESOFAMERICA": "US",
    "GB": "GB",
    "UK": "GB",
    "UNITEDKINGDOM": "GB",
    "KW": "KW",
    "KUWAIT": "KW",
    "QA": "QA",
    "QATAR": "QA",
    "BH": "BH",
    "BAHRAIN": "BH",
}


def normalize_country_code(value: str | None) -> str:
    if not value:
        return ""

    letters = "".join(ch for ch in str(value).upper() if ch.isalpha())
    if not letters:
        return ""

    aliased = _COUNTRY_CODE_ALIASES.get(letters)
    if aliased:
        return aliased

    if len(letters) == 2:
        return letters

    # Preserve backward compatibility for unknown country names/codes.
    return letters[:2]


def calculate_per_km_delivery(
    *,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str,
    vehicle_config: dict[str, dict[str, Decimal]],
    base_rate: Decimal,
    minimum_charge: Decimal,
    weight_surcharge_rate: Decimal,
    weight_surcharge_threshold_kg: Decimal,
    currency: str,
    country_code: str,
) -> dict[str, Any]:
    """Generic per-km delivery formula for any country configuration.

    total = max(base_rate + (distance_km * vehicle_rate) + weight_surcharge, minimum_charge)
    """
    vehicle_key = normalize_vehicle_type(vehicle_type) or "bike"
    vehicle = vehicle_config.get(vehicle_key)
    if vehicle is None:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")

    route_distance = round_money(to_decimal(distance_km))
    total_weight = round_money(to_decimal(weight_kg))
    max_weight = round_money(to_decimal(vehicle.get("max_weight_kg", 0) or 0))
    if max_weight > 0 and total_weight > max_weight:
        raise ValueError(f"{total_weight}kg exceeds vehicle capacity {max_weight}kg")

    per_km_rate = round_money(to_decimal(vehicle.get("per_km_rate", 0) or 0))
    surcharge_threshold = round_money(to_decimal(weight_surcharge_threshold_kg or 0))
    surcharge_rate = round_money(to_decimal(weight_surcharge_rate or 0))
    surcharge_weight = max(Decimal("0"), total_weight - surcharge_threshold)
    weight_surcharge = round_money(surcharge_weight * surcharge_rate)
    subtotal = round_money(round_money(to_decimal(base_rate or 0)) + (route_distance * per_km_rate) + weight_surcharge)
    resolved_minimum_charge = round_money(to_decimal(minimum_charge or 0))
    total = round_money(max(subtotal, resolved_minimum_charge))

    return {
        "country_code": normalize_country_code(country_code),
        "vehicle_type": vehicle_key,
        "distance_km": route_distance,
        "weight_kg": total_weight,
        "base_rate": round_money(to_decimal(base_rate or 0)),
        "per_km_rate": per_km_rate,
        "weight_surcharge": weight_surcharge,
        "minimum_charge": resolved_minimum_charge,
        "total": total,
        "currency": str(currency or ""),
    }


def _country_vehicle_config(config: CountryConfig) -> dict[str, dict[str, Decimal]]:
    base_per_km = round_money(to_decimal(getattr(config, "per_km_rate", 0) or 0))
    default_vehicle = normalize_vehicle_type(getattr(config, "default_vehicle_type", None)) or "bike"

    # Build a sensible multi-vehicle map for any country from a single country-level per_km_rate.
    config_map: dict[str, dict[str, Decimal]] = {}
    for vehicle_name, multiplier in DEFAULT_VEHICLE_MULTIPLIERS.items():
        max_weight = {
            "bike": Decimal("10"),
            "car": Decimal("30"),
            "van": Decimal("100"),
            "truck": Decimal("500"),
        }.get(vehicle_name, Decimal("100"))
        config_map[vehicle_name] = {
            "per_km_rate": round_money(base_per_km * multiplier),
            "max_weight_kg": max_weight,
        }

    # Keep configured default vehicle at exactly country per_km_rate.
    if default_vehicle in config_map:
        config_map[default_vehicle]["per_km_rate"] = base_per_km
    return config_map


def calculate_country_per_km_delivery(
    db: Session,
    *,
    country_code: str,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str | None = None,
) -> dict[str, Any]:
    """Resolve country delivery values from CountryConfig and compute per-km quote."""
    normalized_code = normalize_country_code(country_code)
    if not normalized_code:
        raise ValueError("Unknown country: empty code")

    config = (
        db.query(CountryConfig)
        .filter(CountryConfig.code == normalized_code, CountryConfig.is_active == True)  # noqa: E712
        .first()
    )
    if config is None:
        raise ValueError(f"Unknown country: {normalized_code}")

    model = str(getattr(config, "logistics_model", "") or "").strip().lower()
    if model not in {"per_km", "per-km", "distance", "distance_based"}:
        raise ValueError(f"Country {normalized_code} is not configured for per-km logistics")

    resolved_vehicle = normalize_vehicle_type(vehicle_type) or normalize_vehicle_type(getattr(config, "default_vehicle_type", None)) or "bike"
    vehicle_config = _country_vehicle_config(config)
    return calculate_per_km_delivery(
        distance_km=distance_km,
        weight_kg=weight_kg,
        vehicle_type=resolved_vehicle,
        vehicle_config=vehicle_config,
        base_rate=round_money(to_decimal(getattr(config, "base_rate", 0) or 0)),
        minimum_charge=round_money(to_decimal(getattr(config, "minimum_charge", 0) or 0)),
        weight_surcharge_rate=round_money(to_decimal(getattr(config, "weight_surcharge_rate", 0) or 0)),
        weight_surcharge_threshold_kg=round_money(to_decimal(getattr(config, "weight_surcharge_threshold_kg", 0) or 0)),
        currency=str(getattr(config, "currency", "") or ""),
        country_code=normalized_code,
    )


def calculate_pk_delivery(
    *,
    db: Session,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str = "bike",
) -> dict[str, Any]:
    """Pakistan-specific helper — reads per-km pricing from CountryConfig for PK."""
    return calculate_country_per_km_delivery(
        db=db,
        country_code="PK",
        distance_km=distance_km,
        weight_kg=weight_kg,
        vehicle_type=vehicle_type,
    )


def calculate_pk_delivery_for_cities(
    db: Session,
    *,
    origin_country_code: str,
    origin_city_name: str,
    destination_country_code: str,
    destination_city_name: str,
    weight_kg: Decimal,
    vehicle_type: str = "bike",
) -> dict[str, Any]:
    """Backward-compatible city-distance helper for Pakistan delivery quotes."""
    distance_km = lookup_city_distance_km(
        db,
        origin_country_code=origin_country_code,
        origin_city_name=origin_city_name,
        destination_country_code=destination_country_code,
        destination_city_name=destination_city_name,
    )
    return calculate_pk_delivery(db=db, distance_km=distance_km, weight_kg=weight_kg, vehicle_type=vehicle_type)


def normalize_city_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def partner_is_profile_approved(partner: LogisticsPartner | None) -> bool:
    if partner is None:
        return False
    return (
        cast(str | None, getattr(partner, "status", None)) == "active"
        and cast(str | None, getattr(partner, "verification_status", None)) == APPROVED_PROFILE_STATUS
    )


def serialize_service_area(area: LogisticsPartnerServiceArea) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(area, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(area, "created_at", None))
    updated_at = cast(Optional[Any], getattr(area, "updated_at", None))
    charge_amount = cast(Decimal | float | int | None, getattr(area, "charge_amount", None))
    minimum_charge = cast(Decimal | float | int | None, getattr(area, "minimum_charge", None))
    per_kg_rate = cast(Decimal | float | int | None, getattr(area, "per_kg_rate", None))
    per_km_rate = cast(Decimal | float | int | None, getattr(area, "per_km_rate", None))
    fuel_multiplier = cast(Decimal | float | int | None, getattr(area, "fuel_multiplier", None))
    pickup_charge = cast(Decimal | float | int | None, getattr(area, "pickup_charge", None))
    dropoff_charge = cast(Decimal | float | int | None, getattr(area, "dropoff_charge", None))
    return {
        "id": area.id,
        "partner_id": area.partner_id,
        "country_code": area.country_code,
        "country_name": area.country_name,
        "city_name": area.city_name,
        "origin_city": getattr(area, "origin_city", None),
        "zone_label": area.zone_label,
        "charge_amount": float(charge_amount or 0),
        "minimum_charge": float(minimum_charge) if minimum_charge is not None else None,
        "per_kg_rate": float(per_kg_rate) if per_kg_rate is not None else None,
        "per_km_rate": float(per_km_rate) if per_km_rate is not None else None,
        "fuel_multiplier": float(fuel_multiplier) if fuel_multiplier is not None else 1.0,
        "pickup_charge": float(pickup_charge) if pickup_charge is not None else None,
        "dropoff_charge": float(dropoff_charge) if dropoff_charge is not None else None,
        "currency": area.currency,
        "latitude": getattr(area, "latitude", None),
        "longitude": getattr(area, "longitude", None),
        "delivery_days_min": area.delivery_days_min,
        "delivery_days_max": area.delivery_days_max,
        "is_active": bool(area.is_active),
        "approval_status": area.approval_status,
        "review_note": area.review_note,
        "reviewed_by": area.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def resolve_destination(*, country: str | None = None, city: str | None = None, shipping_address: str | None = None, order: Order | None = None) -> dict[str, str | None]:
    resolved_country = (country or "").strip()
    resolved_city = (city or "").strip()
    shipping_text = (shipping_address or "").strip()

    if order is not None:
        resolved_country = resolved_country or str(getattr(order, "shipping_country", "") or "").strip()
        resolved_city = resolved_city or str(getattr(order, "shipping_city", "") or "").strip()
        shipping_text = shipping_text or str(getattr(order, "shipping_address", "") or "").strip()

    if shipping_text:
        parts = [part.strip() for part in shipping_text.split(",") if part.strip()]
        if not resolved_country and parts:
            resolved_country = parts[-1]
        if not resolved_city:
            if len(parts) >= 3:
                resolved_city = parts[-3]
            elif parts:
                resolved_city = parts[0]

    return {
        "country": resolved_country or None,
        "country_code": normalize_country_code(resolved_country),
        "city": resolved_city or None,
        "city_key": normalize_city_name(resolved_city),
    }


def approved_service_areas_query(db: Session):
    return (
        db.query(LogisticsPartnerServiceArea)
        .join(LogisticsPartner, LogisticsPartner.id == LogisticsPartnerServiceArea.partner_id)
        .filter(
            LogisticsPartner.status == "active",
            LogisticsPartner.verification_status == APPROVED_PROFILE_STATUS,
            LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
            LogisticsPartnerServiceArea.approval_status == APPROVED_AREA_STATUS,
        )
    )


def find_matching_service_areas(
    db: Session,
    *,
    country: str | None,
    city: str | None = None,
    partner_id: int | None = None,
    supplier_city: str | None = None,
) -> list[LogisticsPartnerServiceArea]:
    destination = resolve_destination(country=country, city=city)
    if not destination["country_code"]:
        return []

    query = approved_service_areas_query(db).filter(
        LogisticsPartnerServiceArea.country_code == destination["country_code"],
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerServiceArea.partner_id == partner_id)

    rows = query.order_by(LogisticsPartnerServiceArea.updated_at.desc(), LogisticsPartnerServiceArea.id.desc()).all()
    if not rows:
        return []

    city_key = cast(str, destination["city_key"] or "")
    if not city_key:
        country_rows = [row for row in rows if not normalize_city_name(cast(str | None, getattr(row, "city_name", None)))]
        rows = country_rows or rows
    else:
        exact_rows = [
            row
            for row in rows
            if normalize_city_name(cast(str | None, getattr(row, "city_name", None))) == city_key
        ]
        if exact_rows:
            rows = exact_rows
        else:
            rows = [row for row in rows if not normalize_city_name(cast(str | None, getattr(row, "city_name", None)))]

    # Filter by origin_city (pickup city): NULL origin means any pickup city is accepted
    if supplier_city:
        normalized_supplier = normalize_city_name(supplier_city)
        rows = [
            row for row in rows
            if not getattr(row, "origin_city", None)
            or normalize_city_name(cast(str | None, getattr(row, "origin_city", None))) == normalized_supplier
        ]

    return rows


def quote_shipping_for_destination(
    db: Session,
    *,
    country: str | None,
    city: str | None = None,
    partner_id: int | None = None,
    supplier_city: str | None = None,
    total_weight_kg: Decimal | float | int | None = None,
    categories: list[str] | None = None,
    total_volume_cm3: Decimal | float | int | None = None,
    pickup_count: int | None = None,
    dropoff_count: int | None = None,
) -> dict[str, Any] | None:
    matches = find_matching_service_areas(db, country=country, city=city, partner_id=partner_id, supplier_city=supplier_city)
    if not matches:
        return None

    destination = resolve_destination(country=country, city=city)
    dest_city = cast(str | None, destination.get("city"))
    dest_cc = cast(str | None, destination.get("country_code"))

    ranked = sorted(
        (
            (
                area,
                resolve_pricing_profile_for_area(db, area),
                _resolve_route_context(area, destination_country_code=dest_cc, destination_city_name=dest_city),
            )
            for area in matches
        ),
        key=lambda item: item[0].id,
    )

    resolved_quotes: list[tuple[LogisticsPartnerServiceArea, LogisticsPricingProfile | None, dict[str, Any]]] = []
    for area, pricing_profile, route_context in ranked:
        effective_per_km_rate = getattr(pricing_profile, "per_km_rate", None) if getattr(pricing_profile, "per_km_rate", None) is not None else getattr(area, "per_km_rate", None)
        category_rules = resolve_category_rules_for_area(db, area, categories)
        distance_km = None
        if effective_per_km_rate and not route_context["is_in_city"]:
            distance_km = lookup_city_distance_km(
                db,
                origin_country_code=cast(str | None, route_context["origin_country_code"]),
                origin_city_name=cast(str | None, route_context["origin_city_name"]),
                destination_country_code=dest_cc,
                destination_city_name=dest_city,
            )
        vehicle_rule = resolve_vehicle_rule_for_area(
            db,
            area,
            route_type=cast(str, route_context["route_type"]),
            total_weight_kg=total_weight_kg,
            total_volume_cm3=total_volume_cm3,
        )
        pricing_breakdown = _build_service_area_pricing_breakdown(
            area,
            pricing_profile=pricing_profile,
            category_rules=category_rules,
            vehicle_rule=vehicle_rule,
            apply_vehicle_multiplier=False,
            categories=categories,
            total_weight_kg=total_weight_kg,
            total_volume_cm3=total_volume_cm3,
            pickup_count=pickup_count,
            dropoff_count=dropoff_count,
            distance_km=distance_km,
            destination_country_code=dest_cc,
            destination_city_name=dest_city,
        )
        resolved_quotes.append((area, pricing_profile, pricing_breakdown))

    selected, pricing_profile, pricing_breakdown = sorted(
        resolved_quotes,
        key=lambda item: (item[2]["shipping_amount"], item[0].id),
    )[0]
    partner = cast(LogisticsPartner | None, getattr(selected, "partner", None))
    return {
        "shipping_amount": pricing_breakdown["shipping_amount"],
        "currency": selected.currency,
        "partner_id": selected.partner_id,
        "partner_name": getattr(partner, "name", None) if partner else None,
        "partner_code": getattr(partner, "code", None) if partner else None,
        "service_area": serialize_service_area(selected),
        "pricing_profile": serialize_pricing_profile(pricing_profile) if pricing_profile is not None else None,
        "category_rules": [serialize_category_pricing_rule(rule) for rule in resolve_category_rules_for_area(db, selected, categories)],
        "vehicle_rule": serialize_vehicle_rule(resolve_vehicle_rule_for_area(db, selected, route_type=cast(str, pricing_breakdown["route_type"]), total_weight_kg=total_weight_kg, total_volume_cm3=total_volume_cm3)) if resolve_vehicle_rule_for_area(db, selected, route_type=cast(str, pricing_breakdown["route_type"]), total_weight_kg=total_weight_kg, total_volume_cm3=total_volume_cm3) is not None else None,
        "pricing_breakdown": pricing_breakdown,
        "destination": resolve_destination(country=country, city=city),
    }


def partner_can_service_order(partner: LogisticsPartner, order: Order, db: Session) -> bool:
    if not partner_is_profile_approved(partner):
        return False
    destination = resolve_destination(order=order)
    if not destination["country_code"]:
        return False
    quote = quote_shipping_for_destination(
        db,
        country=cast(str | None, destination["country"]),
        city=cast(str | None, destination["city"]),
        partner_id=cast(int, getattr(partner, "id")),
    )
    return quote is not None

# -------------------------------------------------------------------
# FROM: logistics_partner_write_service.py
# -------------------------------------------------------------------

"""Logistics-partner write operations.

This module centralises the ORM write helpers that the logistics partner
controller depends on. It replaces the previous re-export shim that only
forwarded a handful of symbols and raised ``NotImplementedError`` for every
other referenced handler.

Writes belong in the ``services`` layer (W1), so these helpers are permitted
to call ``db.add`` / ``db.flush`` / ``db.delete``. They deliberately do NOT
commit: the surrounding request/transaction boundary commits once. A few
backward-compatible symbols are still re-exported lazily to avoid the
import-time circular cycles that originally motivated the shim.
"""

from datetime import datetime, timezone
from typing import Any, Type

import importlib
from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.core import CityDistanceMatrix
from domains.comms.models.communication import Notification
from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.finance.models.finance import TransactionLedger
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.accounts.models.banking import LogisticsPartnerBankAccount
from domains.governance.models.admin import LogisticsPartnerDocument
from domains.governance.models.admin import LogisticsSettlement
from domains.governance.models.admin import ShipmentConfirmation
from domains.logistics.models.logistics import LogisticsCategoryPricingRule
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderLogisticsAllocation
from domains.finance.models.payments import LogisticsPartnerPayout
from infrastructure.utils.datetime_utils import utcnow as _utcnow  # noqa: F401
import structlog
logger = structlog.get_logger(__name__)

# Backward-compatible lazy re-exports. These targets live in modules that
# previously imported this shim, so resolving them lazily breaks the cycle.
_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_shipment": ("controllers.orders.logistics_controller", "create_shipment"),
    "create_logistics_partner": ("services.security.auth_write_service", "create_logistics_partner"),
    "delete_notification": ("services.comms.communication_write_service", "delete_notification"),
    "create_notification": ("services.comms.tickets_write_service", "create_notification"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _column_names(model: Type[Any]) -> set[str]:
    return {c.name for c in model.__table__.columns}


# Field-name aliases where the controller passes a key that does not match the
# underlying column (e.g. the document model stores ``doc_type``).
_ALIASES: dict[Type[Any], dict[str, str]] = {
    LogisticsPartnerDocument: {"document_type": "doc_type"},
}


def _new(model: Type[Any], db: Session, *, partner_id: int | None = None, **kwargs: Any) -> Any:
    """Instantiate ``model`` from ``kwargs`` (filtered to real columns, with
    alias resolution), set ``partner_id`` when applicable, stage and flush."""
    cols = _column_names(model)
    aliases = _ALIASES.get(model, {})
    data: dict[str, Any] = {}
    for key, value in kwargs.items():
        target = aliases.get(key, key)
        if target in cols:
            data[target] = value
    if partner_id is not None and "partner_id" in cols:
        data["partner_id"] = partner_id
    obj = model(**data)
    db.add(obj)
    db.flush()
    return obj


def _apply(obj: Any, model: Type[Any], updates: dict[str, Any]) -> Any:
    """Apply ``updates`` to ``obj``, writing only keys that map to real columns
    (alias-aware)."""
    cols = _column_names(model)
    aliases = _ALIASES.get(model, {})
    for key, value in updates.items():
        target = aliases.get(key, key)
        if target in cols:
            setattr(obj, target, value)
    return obj


def _save(db: Session, obj: Any) -> Any:
    db.flush()
    return obj


def _hard_delete(db: Session, obj: Any) -> None:
    db.delete(obj)
    db.flush()


def _soft_delete(db: Session, obj: Any) -> None:
    # Route through the canonical soft-delete util so soft-delete fields,
    # actor bookkeeping and audit semantics stay consistent across the app.
    # ``skip_audit=True`` keeps this helper commit-free to honour the
    # module's single-transaction-boundary contract; the surrounding request
    # transaction commits once.
    from infrastructure.utils.soft_delete import soft_delete

    soft_delete(db, type(obj), obj.id, None, skip_audit=True)


# ── LogisticsPartnerServiceArea ──────────────────────────────────────────────
def create_logistics_partner_service_area(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsPartnerServiceArea, db, partner_id=partner_id, **payload)


def update_logistics_partner_service_area(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPartnerServiceArea, payload))


def delete_logistics_partner_service_area(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsPricingProfile ──────────────────────────────────────────────────
def create_pricing_profile(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsPricingProfile, db, partner_id=partner_id, **payload)


def update_pricing_profile(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPricingProfile, payload))


def delete_pricing_profile(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsCategoryPricingRule ─────────────────────────────────────────────
def create_pricing_rule(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsCategoryPricingRule, db, partner_id=partner_id, **payload)


def update_pricing_rule(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsCategoryPricingRule, payload))


def delete_pricing_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


def delete_category_pricing_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsVehicleRule ─────────────────────────────────────────────────────
def create_vehicle_rule(db: Session, *, partner_id: int, **payload: Any) -> Any:
    return _new(LogisticsVehicleRule, db, partner_id=partner_id, **payload)


def update_vehicle_rule(db: Session, obj: Any, payload: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsVehicleRule, payload))


def delete_vehicle_rule(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsPartnerPayout ───────────────────────────────────────────────────
def create_logistics_partner_payout(
    db: Session,
    *,
    partner_id: int,
    amount: Any,
    method: str | None = None,
    notes: str | None = None,
    **kwargs: Any,
) -> Any:
    return _new(
        LogisticsPartnerPayout,
        db,
        partner_id=partner_id,
        amount=amount,
        method=method,
        notes=notes,
        **kwargs,
    )


def update_logistics_partner_payout(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsPartnerPayout, updates))


def delete_logistics_partner_payout(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── ShipmentConfirmation ────────────────────────────────────────────────────
def create_shipment_confirmation(db: Session, **kwargs: Any) -> Any:
    return _new(ShipmentConfirmation, db, **kwargs)


# ── ShipmentEvent ────────────────────────────────────────────────────────────
def create_shipment_event(db: Session, **kwargs: Any) -> Any:
    return _new(ShipmentEvent, db, **kwargs)


# ── LogisticsPartnerBankAccount ──────────────────────────────────────────────
def create_logistics_partner_bank_account(db: Session, *, partner_id: int, **updates: Any) -> Any:
    return _new(LogisticsPartnerBankAccount, db, partner_id=partner_id, **updates)


def update_logistics_partner_bank_account(db: Session, account: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(account, LogisticsPartnerBankAccount, updates))


def delete_logistics_partner_bank_account(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsPartnerDocument ─────────────────────────────────────────────────
def create_logistics_partner_document(db: Session, *, partner_id: int, **kwargs: Any) -> Any:
    return _new(LogisticsPartnerDocument, db, partner_id=partner_id, **kwargs)


def update_logistics_partner_document(db: Session, doc: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(doc, LogisticsPartnerDocument, updates))


def delete_logistics_partner_document(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── CityDistanceMatrix ──────────────────────────────────────────────────────
def create_city_distance_matrix(db: Session, **kwargs: Any) -> Any:
    return _new(CityDistanceMatrix, db, **kwargs)


def update_city_distance_matrix(db: Session, matrix: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(matrix, CityDistanceMatrix, updates))


def delete_city_distance_matrix(db: Session, obj: Any) -> None:
    _hard_delete(db, obj)


# ── LogisticsSettlement ──────────────────────────────────────────────────────
def create_settlement(db: Session, **kwargs: Any) -> Any:
    return _new(LogisticsSettlement, db, **kwargs)


def update_settlement(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, LogisticsSettlement, updates))


# ── TransactionLedger ───────────────────────────────────────────────────────
def create_transaction_ledger_entry(db: Session, **kwargs: Any) -> Any:
    return _new(TransactionLedger, db, **kwargs)


def update_transaction_ledger(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, TransactionLedger, updates))


# ── LogisticsCODRemittanceReceipt ───────────────────────────────────────────
def create_coding_remittance_receipt(db: Session, **kwargs: Any) -> Any:
    return _new(LogisticsCODRemittanceReceipt, db, **kwargs)


# ── LogisticsPartner (soft-delete) ──────────────────────────────────────────
def update_logistics_partner(db: Session, partner: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(partner, LogisticsPartner, updates))


def delete_logistics_partner(db: Session, partner: Any) -> None:
    _soft_delete(db, partner)


# ── Shipment (soft-delete) ──────────────────────────────────────────────────
def update_shipment(db: Session, shipment: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(shipment, Shipment, updates))


def delete_shipment(db: Session, shipment: Any) -> None:
    _soft_delete(db, shipment)


# ── Order ───────────────────────────────────────────────────────────────────
def update_order(db: Session, order: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(order, Order, updates))


# ── OrderLogisticsAllocation ────────────────────────────────────────────────
def update_order_logistics_allocation(db: Session, obj: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(obj, OrderLogisticsAllocation, updates))


# ── Notification ─────────────────────────────────────────────────────────────
def update_notification(db: Session, notification: Any, updates: dict[str, Any]) -> Any:
    return _save(db, _apply(notification, Notification, updates))


# ── LogisticsPartnerLocation ─────────────────────────────────────────────────
def create_logistics_partner_location(db: Session, country_code: str, payload: dict[str, Any]) -> dict:
    """Create a location for a logistics partner in ``country_code``.

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_locations_create.create_logistics_partner_location``:
    validates the country and partner, stages the row and commits once.
    """
    config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    partner_id = payload.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=422, detail="partner_id is required")
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found")
    location = LogisticsPartnerLocation(
        country_code=country_code.upper(),
        partner_id=partner_id,
        location_type=payload.get("location_type", "warehouse"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        address=payload.get("address"),
        is_active=payload.get("is_active", True),
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return {"id": location.id, "message": "Logistics partner location created"}


def list_logistics_partner_locations(
    db: Session,
    country_code: str,
    partner_id: int | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    """List logistics-partner locations for a country (optionally filtered).

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_locations_create.list_logistics_partner_locations``.
    """
    query = db.query(LogisticsPartnerLocation).filter(
        LogisticsPartnerLocation.country_code == country_code.upper()
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(
        LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at
    ).all()
    return [
        {
            "id": loc.id,
            "partner_id": loc.partner_id,
            "location_type": loc.location_type,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": loc.address,
            "is_active": loc.is_active,
            "created_at": loc.created_at,
        }
        for loc in locations
    ]


# ── Shipment (admin status update) ────────────────────────────────────────────
def admin_update_shipment_status(db: Session, shipment_id: int, data: dict[str, Any], current_user: Any) -> dict:
    """Admin-only direct shipment status update (bypasses supplier check).

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_logistics_status.admin_update_shipment_status``: enforces
    the admin role gate, records a ``ShipmentEvent``, commits once and returns the
    same response shape.
    """
    role = (current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)) or ""
    if str(role).lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    new_status = data.get("status")
    if new_status:
        shipment.status = new_status
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if new_status == "delivered" and not shipment.actual_delivery:
            shipment.actual_delivery = now
        elif new_status == "shipped" and not shipment.shipped_at:
            shipment.shipped_at = now
        event = ShipmentEvent(
            shipment_id=shipment_id,
            event_type="status_change",
            status_after=new_status,
            location=shipment.current_hub,
            notes=data.get("note", "Admin status update"),
            created_at=now,
        )
        db.add(event)
    db.commit()
    db.refresh(shipment)
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
    }

# -------------------------------------------------------------------
# FROM: partner_geography_service.py
# -------------------------------------------------------------------

"""Country-scoped logistics partner read/write operations.

Owns the DB reads/writes for the inline partner endpoints in
``admin_logistics_geography`` so the router stays free of ``db.query``/``db.commit``.
Archive/restore/hard-delete are delegated to the admin controller.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.logistics.models.logistics import LogisticsPartner
import structlog
logger = structlog.get_logger(__name__)


def list_partners(db: Session, country_code: str, include_deleted: bool, page: int, page_size: int, cursor: Optional[int] = None) -> dict:
    q = db.query(LogisticsPartner).filter(LogisticsPartner.country_code == country_code.upper())
    if not include_deleted:
        q = q.filter(LogisticsPartner.is_deleted == False)  # noqa: E712
    total = q.count()
    if cursor is not None:
        q = q.filter(LogisticsPartner.id < cursor)
    else:
        q = q.offset((page - 1) * page_size)
    rows = q.order_by(LogisticsPartner.id.desc()).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def _get_partner(db: Session, partner_id: int, country_code: str) -> LogisticsPartner:
    p = (
        db.query(LogisticsPartner)
        .filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper())
        .first()
    )
    if not p:
        raise HTTPException(404)
    return p


def approve_partner(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.verification_status = "approved"
    db.commit()
    return {"message": "Partner approved"}


def reject_partner(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.verification_status = "rejected"
    db.commit()
    return {"message": "Partner rejected"}


def toggle_partner_active(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.status = "suspended" if p.status == "active" else "active"
    db.commit()
    return {"message": f"Partner {'suspended' if p.status == 'suspended' else 'activated'}"}

# -------------------------------------------------------------------
# FROM: partner_blocker_service.py
# -------------------------------------------------------------------

"""Partner delete-precondition checks.

Relocated from ``controllers/logistics/logistics_partner_controller.py`` so the
raw SQL execution stays in the service layer (architectural W1 fix).
"""


from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domains.finance.models.finance import TransactionLedger
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.accounts.models.banking import LogisticsPartnerBankAccount
from domains.governance.models.admin import LogisticsSettlement
from domains.logistics.models.logistics import Shipment
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderLogisticsAllocation
from domains.finance.models.payments import LogisticsPartnerPayout
import structlog
logger = structlog.get_logger(__name__)

_PARTNER_DELETE_BLOCKING_MODELS: list[tuple[Any, Any, str]] = [
    (LogisticsSettlement, LogisticsSettlement.partner_id, "logistics settlement record(s)"),
    (LogisticsPartnerPayout, LogisticsPartnerPayout.partner_id, "partner payout record(s)"),
    (LogisticsCODRemittanceReceipt, LogisticsCODRemittanceReceipt.partner_id, "COD remittance receipt(s)"),
    (TransactionLedger, TransactionLedger.logistics_partner_id, "transaction ledger record(s)"),
    (OrderLogisticsAllocation, OrderLogisticsAllocation.partner_id, "order logistics allocation(s)"),
    (Shipment, Shipment.assigned_partner_id, "shipment assignment(s)"),
    (Order, Order.selected_partner_id, "order quote selection(s)"),
    (LogisticsPartnerBankAccount, LogisticsPartnerBankAccount.partner_id, "partner bank account record(s)"),
]


def build_partner_delete_blocker(partner_id: int, db: Session) -> Optional[tuple[int, str]]:
    """Return (status_code, message) if the partner cannot be deleted, else None."""
    count_columns = [
        select(func.count())
        .select_from(model)
        .where(column == partner_id)
        .correlate(None)
        .scalar_subquery()
        for model, column, _label in _PARTNER_DELETE_BLOCKING_MODELS
    ]
    if not count_columns:
        return None
    related_counts = db.execute(select(*count_columns)).one()
    for (_model, _column, label), raw_count in zip(_PARTNER_DELETE_BLOCKING_MODELS, related_counts):
        related_count = raw_count or 0
        if related_count > 0:
            return 409, f"Partner has {related_count} {label}. Suspend the partner instead of deleting."
    return None

# -------------------------------------------------------------------
# FROM: logistics_partner_verify_service.py
# -------------------------------------------------------------------

"""
Logistics Partner Router — partner management and partner dashboard.
All business logic in controllers/logistics_partner_controller.py.
"""
from typing import List, Optional
from fastapi import Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user
import domains.logistics.services.partners.logistics_partner_service as ctrl

class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None

class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None

# -------------------------------------------------------------------
# FROM: logistics_partner_admin_write_service.py
# -------------------------------------------------------------------

"""Logistics partner admin write service.

Owns the DB mutations behind the country-scoped admin logistics partner
endpoints (approve / reject / toggle-active) so the router and controller
layers stay write-free (W1 layer contract).

Each function takes ``db: Session`` first, mutates, commits, and raises
``HTTPException`` exactly as the original router code did.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.logistics.models.logistics import LogisticsPartner
import structlog
logger = structlog.get_logger(__name__)


def _get_partner_or_404(db: Session, country_code: str, partner_id: int) -> LogisticsPartner:
    partner = (
        db.query(LogisticsPartner)
        .filter(
            LogisticsPartner.id == partner_id,
            LogisticsPartner.country_code == country_code,
        )
        .first()
    )
    if not partner:
        raise HTTPException(404)
    return partner


def approve_logistics_partner(db: Session, *, country_code: str, partner_id: int) -> dict:
    """Set a logistics partner's verification status to ``approved``."""
    partner = _get_partner_or_404(db, country_code, partner_id)
    partner.verification_status = "approved"
    db.commit()
    return {"message": "Partner approved"}


def reject_logistics_partner(db: Session, *, country_code: str, partner_id: int) -> dict:
    """Set a logistics partner's verification status to ``rejected``."""
    partner = _get_partner_or_404(db, country_code, partner_id)
    partner.verification_status = "rejected"
    db.commit()
    return {"message": "Partner rejected"}


def toggle_logistics_partner_active(db: Session, *, country_code: str, partner_id: int) -> dict:
    """Flip a logistics partner between ``active`` and ``suspended``."""
    partner = _get_partner_or_404(db, country_code, partner_id)
    partner.status = "suspended" if partner.status == "active" else "active"
    db.commit()
    return {"message": f"Partner {'suspended' if partner.status == 'suspended' else 'activated'}"}

# -------------------------------------------------------------------
# FROM: partner\admin_operations_service.py
# -------------------------------------------------------------------

"""Admin logistics / email-marketing aggregation service.

Holds the read-only DB aggregation that was previously inlined in
``routers/admin_logistics_operations.py`` for three admin endpoints:
``/email/stats``, ``/logistics/overview``, and the payout-verify amount lookup.
"""

from typing import Optional

from sqlalchemy import func as sqlfunc, case as sql_case
from sqlalchemy.orm import Session

from domains.comms.models.marketing import CampaignRecipient
from domains.comms.models.marketing import EmailCampaign
from domains.comms.models.marketing import NewsletterSubscriber
from domains.governance.models.admin import ShippingCarrier
from domains.governance.models.admin import ShippingZone
from domains.logistics.models.logistics import Shipment
from domains.finance.models.payments import Payout


def get_payout_amount(db: Session, payout_id: int) -> Optional[float]:
    """Return the payout amount (or None) used for 2FA approval gating."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if payout and payout.amount is not None:
        return float(payout.amount)
    return None


def get_email_stats(db: Session) -> dict:
    """Real email marketing statistics from the database."""
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.is_active == True
    ).scalar() or 0

    campaign_stats = db.query(
        sqlfunc.count(EmailCampaign.id).label("total"),
        sqlfunc.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
    ).first()

    total_sent = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.sent_at.isnot(None)
    ).scalar() or 0
    total_opened = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.opened_at.isnot(None)
    ).scalar() or 0
    total_clicked = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.clicked_at.isnot(None)
    ).scalar() or 0

    open_rate = round((total_opened / total_sent * 100), 1) if total_sent else 0
    click_rate = round((total_clicked / total_opened * 100), 1) if total_opened else 0

    recent_campaigns = db.query(EmailCampaign).order_by(
        EmailCampaign.created_at.desc()
    ).limit(10).all()

    # Pre-aggregate recipient counts in a single query (avoid N+1 per campaign).
    campaign_ids = [c.id for c in recent_campaigns]
    recipient_counts = {}
    if campaign_ids:
        rows = (
            db.query(
                CampaignRecipient.campaign_id,
                sqlfunc.count(CampaignRecipient.id).label("recipient_count"),
                sqlfunc.sum(sql_case((CampaignRecipient.sent_at.isnot(None), 1), else_=0)).label("sent_count"),
                sqlfunc.sum(sql_case((CampaignRecipient.opened_at.isnot(None), 1), else_=0)).label("opened_count"),
                sqlfunc.sum(sql_case((CampaignRecipient.clicked_at.isnot(None), 1), else_=0)).label("clicked_count"),
            )
            .filter(CampaignRecipient.campaign_id.in_(campaign_ids))
            .group_by(CampaignRecipient.campaign_id)
            .all()
        )
        for r in rows:
            recipient_counts[r.campaign_id] = {
                "recipient_count": int(r.recipient_count or 0),
                "sent_count": int(r.sent_count or 0),
                "opened_count": int(r.opened_count or 0),
                "clicked_count": int(r.clicked_count or 0),
            }

    def _ser_campaign(c: EmailCampaign) -> dict:
        counts = recipient_counts.get(c.id, {})
        return {
            "id": c.id,
            "name": c.name,
            "subject": c.subject,
            "status": c.status,
            "recipient_count": counts.get("recipient_count", 0),
            "sent_count": counts.get("sent_count", 0),
            "opened_count": counts.get("opened_count", 0),
            "clicked_count": counts.get("clicked_count", 0),
            "send_at": c.send_at.isoformat() if c.send_at else None,
            "sent_at": c.send_at.isoformat() if c.send_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }

    return {
        "total_subscribers": total_subscribers,
        "active_campaigns": int(campaign_stats.active or 0),
        "total_campaigns": int(campaign_stats.total or 0),
        "total_sent": total_sent,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "recent_campaigns": [_ser_campaign(c) for c in recent_campaigns],
    }


def get_logistics_overview(db: Session) -> dict:
    """Admin overview of all shipments, carriers, and distribution channels."""
    shipment_counts = db.query(
        Shipment.status,
        sqlfunc.count(Shipment.id).label("count"),
    ).group_by(Shipment.status).all()

    channel_counts = db.query(
        Shipment.distribution_channel,
        sqlfunc.count(Shipment.id).label("count"),
    ).filter(Shipment.distribution_channel.isnot(None)).group_by(
        Shipment.distribution_channel
    ).all()

    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()

    recent_shipments = db.query(Shipment).order_by(
        Shipment.updated_at.desc()
    ).limit(20).all()

    def _ser_shipment(s: Shipment) -> dict:
        return {
            "id": s.id,
            "order_id": s.order_id,
            "supplier_id": s.supplier_id,
            "carrier_name": s.carrier_name,
            "tracking_number": s.tracking_number,
            "status": s.status,
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": s.scan_code,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
        }

    return {
        "shipment_by_status": {s: c for s, c in shipment_counts},
        "shipment_by_channel": {ch: c for ch, c in channel_counts},
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code, "is_global": c.supplier_id is None}
            for c in carriers
        ],
        "active_zones": zones,
        "recent_shipments": [_ser_shipment(s) for s in recent_shipments],
    }

# -------------------------------------------------------------------
# FROM: partner\logistics_partner_pricing.py
# -------------------------------------------------------------------


from decimal import Decimal
from typing import Any, Optional, TYPE_CHECKING, cast

from sqlalchemy import desc
from sqlalchemy.orm import Session

from domains.logistics.models.logistics_schema_models import CityDistanceMatrix
from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsCategoryPricingRule
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from kernel.money import round_money, to_decimal

if TYPE_CHECKING:
    from domains.orders.models.orders import Order


APPROVED_PROFILE_STATUS = "approved"
APPROVED_AREA_STATUS = "approved"
APPROVED_PRICING_PROFILE_STATUS = "approved"
APPROVED_CATEGORY_RULE_STATUS = "approved"
APPROVED_VEHICLE_RULE_STATUS = "approved"
DEFAULT_VEHICLE_MULTIPLIERS = {
    "bike": Decimal("0.90"),
    "car": Decimal("1.00"),
    "van": Decimal("1.20"),
    "truck": Decimal("1.50"),
}


def lookup_city_distance_km(
    db: Session,
    *,
    origin_country_code: str | None,
    origin_city_name: str | None,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> Decimal:
    """Return the distance in km between an origin/destination city pair.

    Matching is case-insensitive and whitespace-normalised.  Returns ``Decimal(0)``
    when no matching row exists in ``city_distance_matrix``.
    """
    if not (origin_country_code and origin_city_name and destination_country_code and destination_city_name):
        return Decimal("0")

    origin_cc = normalize_country_code(origin_country_code)
    dest_cc = normalize_country_code(destination_country_code)
    origin_key = normalize_city_name(origin_city_name)
    dest_key = normalize_city_name(destination_city_name)

    # SQLite stores text; we normalise both sides at query time.
    row = (
        db.query(CityDistanceMatrix)
        .filter(
            CityDistanceMatrix.origin_country_code == origin_cc,
            CityDistanceMatrix.destination_country_code == dest_cc,
        )
        .all()
    )
    for entry in row:
        if (
            normalize_city_name(cast(str | None, getattr(entry, "origin_city_name", None))) == origin_key
            and normalize_city_name(cast(str | None, getattr(entry, "destination_city_name", None))) == dest_key
        ):
            return to_decimal(getattr(entry, "distance_km", 0) or 0)
    return Decimal("0")


def serialize_pricing_profile(profile: LogisticsPricingProfile) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(profile, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(profile, "created_at", None))
    updated_at = cast(Optional[Any], getattr(profile, "updated_at", None))
    return {
        "id": profile.id,
        "partner_id": profile.partner_id,
        "service_area_id": profile.service_area_id,
        "profile_name": profile.profile_name,
        "base_in_city_fee": float(profile.base_in_city_fee) if getattr(profile, "base_in_city_fee", None) is not None else None,
        "base_inter_city_fee": float(profile.base_inter_city_fee) if getattr(profile, "base_inter_city_fee", None) is not None else None,
        "per_km_rate": float(profile.per_km_rate) if getattr(profile, "per_km_rate", None) is not None else None,
        "per_kg_rate": float(profile.per_kg_rate) if getattr(profile, "per_kg_rate", None) is not None else None,
        "minimum_charge": float(profile.minimum_charge) if getattr(profile, "minimum_charge", None) is not None else None,
        "maximum_charge": float(profile.maximum_charge) if getattr(profile, "maximum_charge", None) is not None else None,
        "fuel_multiplier": float(profile.fuel_multiplier) if getattr(profile, "fuel_multiplier", None) is not None else 1.0,
        "bulk_discount_threshold_kg": float(profile.bulk_discount_threshold_kg) if getattr(profile, "bulk_discount_threshold_kg", None) is not None else None,
        "bulk_discount_percent": float(profile.bulk_discount_percent) if getattr(profile, "bulk_discount_percent", None) is not None else None,
        "currency": profile.currency,
        "is_active": bool(profile.is_active),
        "approval_status": profile.approval_status,
        "review_note": profile.review_note,
        "reviewed_by": profile.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def normalize_category_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def normalize_vehicle_type(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def vehicle_baseline_multiplier(vehicle_type: str | None) -> Decimal:
    normalized = normalize_vehicle_type(vehicle_type)
    return DEFAULT_VEHICLE_MULTIPLIERS.get(normalized, Decimal("1.00"))


def normalize_pricing_breakdown_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    data = dict(payload)
    legacy_keys = {
        "applied_category_name",
        "applied_category_rule_id",
        "bulk_discount_amount",
        "bulk_discount_percent",
        "bulk_discount_threshold_kg",
        "category_adjustment_amount",
        "category_extra",
        "category_rule_ids",
        "dropoff_charge",
        "fuel_adjustment_amount",
        "fuel_multiplier",
        "matched_categories",
        "maximum_charge",
        "maximum_charge_applied",
        "minimum_charge",
        "minimum_charge_applied",
        "pickup_charge",
        "pricing_schema_version",
        "special_handling_fee",
        "subtotal_before_fuel",
        "total_category_extra",
        "vehicle_adjustment_amount",
        "vehicle_multiplier",
        "vehicle_rule_id",
        "vehicle_type",
    }
    normalized = {key: value for key, value in data.items() if key not in legacy_keys}

    handling_fee = data.get("handling_fee")
    if handling_fee is None:
        if data.get("total_category_extra") is not None:
            handling_fee = data.get("total_category_extra")
        elif data.get("category_adjustment_amount") is not None:
            handling_fee = data.get("category_adjustment_amount")
        else:
            handling_fee = max(float(data.get("category_extra") or 0), float(data.get("special_handling_fee") or 0))

    pricing_schema_version = str(data.get("pricing_schema_version") or "").strip().lower()
    pricing_model = data.get("pricing_model")
    if not pricing_model:
        pricing_model = "operational_load_fit" if pricing_schema_version == "v1_operational_vehicle_multiplier" else "customer_weight_route"

    load_fit_factor = data.get("load_fit_factor")
    if load_fit_factor is None:
        load_fit_factor = data.get("vehicle_multiplier")
    if load_fit_factor is None:
        load_fit_factor = 1.0

    surcharge_factor = data.get("surcharge_factor")
    if surcharge_factor is None:
        surcharge_factor = data.get("fuel_multiplier")
    if surcharge_factor is None:
        surcharge_factor = 1.0

    normalized.update({
        "base_fee": data.get("base_fee", 0.0),
        "pickup_fee": data.get("pickup_fee", data.get("pickup_charge", 0.0)),
        "dropoff_fee": data.get("dropoff_fee", data.get("dropoff_charge", 0.0)),
        "pickup_count": data.get("pickup_count", 1),
        "dropoff_count": data.get("dropoff_count", 1),
        "extra_pickup_count": data.get("extra_pickup_count", 0),
        "extra_dropoff_count": data.get("extra_dropoff_count", 0),
        "pickup_fee_per_stop": data.get("pickup_fee_per_stop", 0.0),
        "dropoff_fee_per_stop": data.get("dropoff_fee_per_stop", 0.0),
        "route_type": data.get("route_type", "in_city"),
        "is_in_city": bool(data.get("is_in_city", data.get("route_type") == "in_city")),
        "weight_fee": data.get("weight_fee", 0.0),
        "per_kg_rate": data.get("per_kg_rate"),
        "distance_km": data.get("distance_km"),
        "per_km_rate": data.get("per_km_rate"),
        "distance_fee": data.get("distance_fee", 0.0),
        "handling_fee": handling_fee,
        "subtotal_core": data.get("subtotal_core", 0.0),
        "load_fit_factor": load_fit_factor,
        "load_fit_adjustment_amount": data.get("load_fit_adjustment_amount", data.get("vehicle_adjustment_amount", 0.0)),
        "pricing_model": pricing_model,
        "subtotal_before_surcharge": data.get("subtotal_before_surcharge", data.get("subtotal_before_fuel", data.get("subtotal_core", 0.0))),
        "surcharge_factor": surcharge_factor,
        "surcharge_amount": data.get("surcharge_amount", data.get("fuel_adjustment_amount", 0.0)),
        "floor_charge": data.get("floor_charge", data.get("minimum_charge")),
        "floor_applied": bool(data.get("floor_applied", data.get("minimum_charge_applied", False))),
        "ceiling_charge": data.get("ceiling_charge", data.get("maximum_charge")),
        "ceiling_applied": bool(data.get("ceiling_applied", data.get("maximum_charge_applied", False))),
        "weight_discount_threshold_kg": data.get("weight_discount_threshold_kg", data.get("bulk_discount_threshold_kg")),
        "weight_discount_percent": data.get("weight_discount_percent", data.get("bulk_discount_percent")),
        "weight_discount_amount": data.get("weight_discount_amount", data.get("bulk_discount_amount", 0.0)),
        "pricing_profile_id": data.get("pricing_profile_id"),
        "handling_rule_ids": data.get("handling_rule_ids", data.get("category_rule_ids", [])),
        "applied_handling_rule_id": data.get("applied_handling_rule_id", data.get("applied_category_rule_id")),
        "applied_handling_label": data.get("applied_handling_label", data.get("applied_category_name")),
        "matched_handling_labels": data.get("matched_handling_labels", data.get("matched_categories", [])),
        "load_fit_rule_id": data.get("load_fit_rule_id", data.get("vehicle_rule_id")),
        "load_fit_label": data.get("load_fit_label", data.get("vehicle_type")),
        "total_weight_kg": data.get("total_weight_kg", 0.0),
        "total_volume_cm3": data.get("total_volume_cm3", 0.0),
        "shipping_amount": data.get("shipping_amount", 0.0),
    })
    return normalized


def parse_dimensions_to_volume_cm3(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    cleaned = str(value).lower().replace("cm", " ").replace("x", " ").replace("*", " ")
    parts: list[Decimal] = []
    for token in cleaned.split():
        try:
            parts.append(to_decimal(token))
        except Exception:
            continue
        if len(parts) == 3:
            break
    if len(parts) != 3:
        return Decimal("0")
    length, width, height = parts
    if length <= 0 or width <= 0 or height <= 0:
        return Decimal("0")
    return round_money(length * width * height)


def serialize_category_pricing_rule(rule: LogisticsCategoryPricingRule) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(rule, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(rule, "created_at", None))
    updated_at = cast(Optional[Any], getattr(rule, "updated_at", None))
    return {
        "id": rule.id,
        "partner_id": rule.partner_id,
        "service_area_id": rule.service_area_id,
        "category_name": rule.category_name,
        "flat_fee_override": float(rule.flat_fee_override) if getattr(rule, "flat_fee_override", None) is not None else None,
        "special_handling_fee": float(rule.special_handling_fee) if getattr(rule, "special_handling_fee", None) is not None else None,
        "currency": rule.currency,
        "is_active": bool(rule.is_active),
        "approval_status": rule.approval_status,
        "review_note": rule.review_note,
        "reviewed_by": rule.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def serialize_vehicle_rule(rule: LogisticsVehicleRule) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(rule, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(rule, "created_at", None))
    updated_at = cast(Optional[Any], getattr(rule, "updated_at", None))
    return {
        "id": rule.id,
        "partner_id": rule.partner_id,
        "service_area_id": rule.service_area_id,
        "route_scope": getattr(rule, "route_scope", "any"),
        "vehicle_type": rule.vehicle_type,
        "max_weight_kg": float(rule.max_weight_kg) if getattr(rule, "max_weight_kg", None) is not None else None,
        "max_volume_cm3": float(rule.max_volume_cm3) if getattr(rule, "max_volume_cm3", None) is not None else None,
        "cost_multiplier": float(rule.cost_multiplier),
        "priority_rank": rule.priority_rank,
        "is_active": bool(rule.is_active),
        "approval_status": rule.approval_status,
        "review_note": rule.review_note,
        "reviewed_by": rule.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def resolve_category_rules_for_area(
    db: Session,
    area: LogisticsPartnerServiceArea,
    categories: list[str] | None,
) -> list[LogisticsCategoryPricingRule]:
    normalized_categories = [normalize_category_name(category) for category in (categories or []) if normalize_category_name(category)]
    if not normalized_categories:
        return []

    rows = (
        db.query(LogisticsCategoryPricingRule)
        .filter(
            LogisticsCategoryPricingRule.partner_id == area.partner_id,
            LogisticsCategoryPricingRule.is_active == True,  # noqa: E712
            LogisticsCategoryPricingRule.approval_status == APPROVED_CATEGORY_RULE_STATUS,
        )
        .order_by(desc(LogisticsCategoryPricingRule.updated_at), desc(LogisticsCategoryPricingRule.id))
        .all()
    )

    resolved: dict[str, LogisticsCategoryPricingRule] = {}
    for category in normalized_categories:
        exact_match = next(
            (
                row for row in rows
                if getattr(row, "service_area_id", None) == area.id
                and normalize_category_name(cast(str | None, getattr(row, "category_name", None))) == category
            ),
            None,
        )
        if exact_match is not None:
            resolved[category] = exact_match
            continue
        fallback = next(
            (
                row for row in rows
                if getattr(row, "service_area_id", None) is None
                and normalize_category_name(cast(str | None, getattr(row, "category_name", None))) == category
            ),
            None,
        )
        if fallback is not None:
            resolved[category] = fallback

    return [resolved[category] for category in normalized_categories if category in resolved]


def resolve_vehicle_rule_for_area(
    db: Session,
    area: LogisticsPartnerServiceArea,
    *,
    route_type: str,
    total_weight_kg: Decimal | float | int | None,
    total_volume_cm3: Decimal | float | int | None,
    preferred_vehicle_type: str | None = None,
) -> LogisticsVehicleRule | None:
    weight = max(round_money(to_decimal(total_weight_kg or 0)), Decimal("0"))
    volume = max(round_money(to_decimal(total_volume_cm3 or 0)), Decimal("0"))
    preferred_vehicle_key = normalize_vehicle_type(preferred_vehicle_type)
    rows = (
        db.query(LogisticsVehicleRule)
        .filter(
            LogisticsVehicleRule.partner_id == area.partner_id,
            LogisticsVehicleRule.is_active == True,  # noqa: E712
            LogisticsVehicleRule.approval_status == APPROVED_VEHICLE_RULE_STATUS,
        )
        .all()
    )
    candidates = []
    for row in rows:
        service_area_id = getattr(row, "service_area_id", None)
        if service_area_id not in (None, area.id):
            continue
        row_route_scope = str(getattr(row, "route_scope", "any") or "any").strip().lower()
        if row_route_scope not in {"any", route_type}:
            continue
        if preferred_vehicle_key and normalize_vehicle_type(cast(str | None, getattr(row, "vehicle_type", None))) != preferred_vehicle_key:
            continue
        max_weight = cast(Decimal | float | int | None, getattr(row, "max_weight_kg", None))
        max_volume = cast(Decimal | float | int | None, getattr(row, "max_volume_cm3", None))
        if max_weight is not None and weight > round_money(to_decimal(max_weight)):
            continue
        if max_volume is not None and volume > round_money(to_decimal(max_volume)):
            continue
        candidates.append(row)

    if not candidates:
        return None

    candidates.sort(
        key=lambda row: (
            0 if getattr(row, "service_area_id", None) == area.id else 1,
            0 if str(getattr(row, "route_scope", "any") or "any").strip().lower() == route_type else 1,
            int(getattr(row, "priority_rank", 100) or 100),
            int(getattr(row, "id", 0) or 0),
        )
    )
    return candidates[0]


def resolve_pricing_profile_for_area(db: Session, area: LogisticsPartnerServiceArea) -> LogisticsPricingProfile | None:
    rows = (
        db.query(LogisticsPricingProfile)
        .filter(
            LogisticsPricingProfile.partner_id == area.partner_id,
            LogisticsPricingProfile.is_active == True,  # noqa: E712
            LogisticsPricingProfile.approval_status == APPROVED_PRICING_PROFILE_STATUS,
        )
        .order_by(desc(LogisticsPricingProfile.updated_at), desc(LogisticsPricingProfile.id))
        .all()
    )
    exact = [row for row in rows if getattr(row, "service_area_id", None) == area.id]
    if exact:
        return exact[0]
    fallback = [row for row in rows if getattr(row, "service_area_id", None) is None]
    return fallback[0] if fallback else None


def _resolve_route_context(
    area: LogisticsPartnerServiceArea,
    *,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> dict[str, Any]:
    origin_country_code = normalize_country_code(cast(str | None, getattr(area, "country_code", None)))
    origin_city_name = cast(str | None, getattr(area, "origin_city", None))
    destination_country = normalize_country_code(destination_country_code)
    origin_city_key = normalize_city_name(origin_city_name)
    destination_city_key = normalize_city_name(destination_city_name)
    is_in_city = bool(
        origin_country_code
        and destination_country
        and origin_country_code == destination_country
        and origin_city_key
        and destination_city_key
        and origin_city_key == destination_city_key
    )
    return {
        "origin_country_code": origin_country_code or None,
        "origin_city_name": origin_city_name,
        "destination_country_code": destination_country or None,
        "destination_city_name": destination_city_name,
        "is_in_city": is_in_city,
        "route_type": "in_city" if is_in_city else "inter_city",
    }


def _build_service_area_pricing_breakdown(
    area: LogisticsPartnerServiceArea,
    *,
    pricing_profile: LogisticsPricingProfile | None = None,
    category_rules: list[LogisticsCategoryPricingRule] | None = None,
    vehicle_rule: LogisticsVehicleRule | None = None,
    vehicle_type_override: str | None = None,
    vehicle_multiplier_override: Decimal | float | int | None = None,
    vehicle_rule_id_override: int | None = None,
    apply_vehicle_multiplier: bool = True,
    categories: list[str] | None = None,
    total_weight_kg: Decimal | float | int | None = None,
    total_volume_cm3: Decimal | float | int | None = None,
    pickup_count: int | None = None,
    dropoff_count: int | None = None,
    distance_km: Decimal | float | int | None = None,
    destination_country_code: str | None = None,
    destination_city_name: str | None = None,
) -> dict[str, Any]:
    route_context = _resolve_route_context(
        area,
        destination_country_code=destination_country_code,
        destination_city_name=destination_city_name,
    )
    raw_minimum_charge = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "minimum_charge", None) if getattr(pricing_profile, "minimum_charge", None) is not None else getattr(area, "minimum_charge", None),
    )
    raw_per_kg_rate = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "per_kg_rate", None) if getattr(pricing_profile, "per_kg_rate", None) is not None else getattr(area, "per_kg_rate", None),
    )
    raw_per_km_rate = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "per_km_rate", None) if getattr(pricing_profile, "per_km_rate", None) is not None else getattr(area, "per_km_rate", None),
    )
    raw_fuel_multiplier = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "fuel_multiplier", None) if getattr(pricing_profile, "fuel_multiplier", None) is not None else getattr(area, "fuel_multiplier", None),
    )
    raw_bulk_discount_threshold = cast(Decimal | float | int | None, getattr(pricing_profile, "bulk_discount_threshold_kg", None))
    raw_bulk_discount_percent = cast(Decimal | float | int | None, getattr(pricing_profile, "bulk_discount_percent", None))

    profile_base = None
    if pricing_profile is not None:
        profile_base = getattr(pricing_profile, "base_in_city_fee", None) if route_context["is_in_city"] else getattr(pricing_profile, "base_inter_city_fee", None)
    pickup_fee_per_stop = round_money(to_decimal(getattr(area, "pickup_charge", None) or 0))
    dropoff_fee_per_stop = round_money(to_decimal(getattr(area, "dropoff_charge", None) or 0))
    resolved_pickup_count = max(int(pickup_count if pickup_count is not None else 1), 0)
    resolved_dropoff_count = max(int(dropoff_count if dropoff_count is not None else 1), 0)
    # First pickup and first dropoff are included in the base fee; only extra stops are charged.
    extra_pickups = max(resolved_pickup_count - 1, 0)
    extra_dropoffs = max(resolved_dropoff_count - 1, 0)
    pickup_fee = round_money(pickup_fee_per_stop * to_decimal(extra_pickups))
    dropoff_fee = round_money(dropoff_fee_per_stop * to_decimal(extra_dropoffs))
    resolved_base_fee = round_money(to_decimal(profile_base if profile_base is not None else getattr(area, "charge_amount", None) or 0))
    total_weight = max(round_money(to_decimal(total_weight_kg or 0)), Decimal("0"))
    total_volume = max(round_money(to_decimal(total_volume_cm3 or 0)), Decimal("0"))

    category_rules = category_rules or []

    # Category handling is intentionally simplified for the business-facing rate card.
    # Legacy rules may still store two numbers (flat fee + handling fee), but the
    # customer-facing quote collapses them into one handling amount per rule by taking
    # the stronger configured charge. Across multiple matched rules, only the single
    # highest collapsed handling amount is applied.
    category_extra = Decimal("0")
    special_handling_fee = Decimal("0")
    applied_category_rule = None
    highest_category_total = Decimal("0")
    for rule in category_rules:
        rule_category_extra = round_money(to_decimal(getattr(rule, "flat_fee_override", None) or 0))
        rule_special_handling = round_money(to_decimal(getattr(rule, "special_handling_fee", None) or 0))
        rule_total = round_money(max(rule_category_extra, rule_special_handling))
        if rule_total > highest_category_total:
            highest_category_total = rule_total
            category_extra = Decimal("0")
            special_handling_fee = rule_total
            applied_category_rule = rule

    total_category_extra = round_money(category_extra + special_handling_fee)

    # STEP 1 — Base fee (in-city) or STEP 2 — Distance cost (inter-city).
    # resolved_base_fee is already set to base_in_city_fee (in-city) or base_inter_city_fee (inter-city)
    # by the profile_base lookup above. These two are mutually exclusive by route_type.
    base_fee = resolved_base_fee

    # STEP 3 — Weight cost. Calculated once from global per_kg_rate. Never overridden by category rules.
    per_kg_rate = round_money(to_decimal(raw_per_kg_rate or 0))
    weight_fee = round_money(total_weight * per_kg_rate) if total_weight > 0 and per_kg_rate > 0 else Decimal("0")

    # STEP 2 (distance component) — inter-city only.
    # When base_inter_city_fee is set and per_km_rate is null, distance_fee stays 0 (flat-rate mode).
    # When per_km_rate is set, distance_fee = distance_km x per_km_rate (per-km mode).
    resolved_distance = max(round_money(to_decimal(distance_km or 0)), Decimal("0"))
    per_km_rate = to_decimal(raw_per_km_rate or 0)
    distance_fee = round_money(resolved_distance * per_km_rate) if resolved_distance > 0 and per_km_rate > 0 else Decimal("0")

    # Core additive subtotal: (base OR distance) + weight + category.
    # base_fee and distance_fee are mutually exclusive by route_type — only one is non-zero at a time.
    subtotal_core = round_money(base_fee + distance_fee + weight_fee + total_category_extra)

    # Pickup / drop-off surcharges: additive exceptional access charges.
    # These are 0 for standard routes and non-zero only for explicitly configured exceptional areas.
    subtotal_before_multipliers = round_money(subtotal_core + pickup_fee + dropoff_fee)

    # STEP 5 — Vehicle multiplier is optional.
    # Customer-facing quotes keep the formula weight-first and route-first.
    # Operational acceptance flows can still opt in to multiplier-based snapshots.
    resolved_vehicle_multiplier = to_decimal(
        vehicle_multiplier_override
        if vehicle_multiplier_override is not None
        else getattr(vehicle_rule, "cost_multiplier", None) or 1
    )
    vehicle_multiplier = resolved_vehicle_multiplier if apply_vehicle_multiplier else Decimal("1")
    subtotal_after_vehicle = round_money(subtotal_before_multipliers * vehicle_multiplier)

    # STEP 6 — Fuel multiplier.
    fuel_multiplier = to_decimal(raw_fuel_multiplier or 1)
    fuel_adjusted_total = round_money(subtotal_after_vehicle * fuel_multiplier)

    # STEP 7 — Minimum charge floor.
    minimum_charge = round_money(to_decimal(raw_minimum_charge or 0))
    total_after_minimum = round_money(max(fuel_adjusted_total, minimum_charge))

    # Maximum charge ceiling (guardrail) — clamps the total from above when set.
    raw_maximum_charge = cast(
        Decimal | float | int | None,
        getattr(pricing_profile, "maximum_charge", None) if pricing_profile is not None else None,
    )
    maximum_charge_limit = round_money(to_decimal(raw_maximum_charge)) if raw_maximum_charge is not None else None
    maximum_charge_applied = False
    if maximum_charge_limit is not None and maximum_charge_limit > 0 and total_after_minimum > maximum_charge_limit:
        total_after_minimum = maximum_charge_limit
        maximum_charge_applied = True

    # Bulk discount (optional, applied after floor/ceiling guardrails).
    # The discount is restricted to the weight fee so route and stop charges stay stable.
    bulk_discount_threshold = round_money(to_decimal(raw_bulk_discount_threshold or 0))
    bulk_discount_percent = round_money(to_decimal(raw_bulk_discount_percent or 0))
    bulk_discount_amount = Decimal("0")
    if bulk_discount_threshold > 0 and bulk_discount_percent > 0 and total_weight >= bulk_discount_threshold:
        bulk_discount_amount = round_money(weight_fee * (bulk_discount_percent / Decimal("100")))
    final_charge = round_money(max(total_after_minimum - bulk_discount_amount, Decimal("0")))

    return normalize_pricing_breakdown_payload({
        "base_fee": float(base_fee),
        "pickup_count": resolved_pickup_count,
        "dropoff_count": resolved_dropoff_count,
        "extra_pickup_count": extra_pickups,
        "extra_dropoff_count": extra_dropoffs,
        "pickup_fee_per_stop": float(pickup_fee_per_stop),
        "dropoff_fee_per_stop": float(dropoff_fee_per_stop),
        "pickup_fee": float(pickup_fee),
        "dropoff_fee": float(dropoff_fee),
        "route_type": route_context["route_type"],
        "is_in_city": route_context["is_in_city"],
        "currency": getattr(pricing_profile, "currency", None) or getattr(area, "currency", None),
        "weight_fee": float(weight_fee),
        "per_kg_rate": float(per_kg_rate) if raw_per_kg_rate is not None else None,
        "distance_km": float(resolved_distance) if distance_km is not None else None,
        "per_km_rate": float(per_km_rate) if raw_per_km_rate is not None else None,
        "distance_fee": float(distance_fee),
        "category_extra": float(category_extra),
        "special_handling_fee": float(special_handling_fee),
        "total_category_extra": float(total_category_extra),
        "subtotal_core": float(subtotal_core),
        "vehicle_multiplier": float(vehicle_multiplier),
        "vehicle_adjustment_amount": float(round_money(subtotal_after_vehicle - subtotal_before_multipliers)),
        "pricing_schema_version": "v1_operational_vehicle_multiplier" if apply_vehicle_multiplier else "v2_weight_first_customer_charge",
        "subtotal_before_fuel": float(subtotal_after_vehicle),
        "fuel_multiplier": float(fuel_multiplier),
        "fuel_adjustment_amount": float(round_money(fuel_adjusted_total - subtotal_after_vehicle)),
        "minimum_charge": float(minimum_charge) if raw_minimum_charge is not None else None,
        "minimum_charge_applied": raw_minimum_charge is not None and total_after_minimum == minimum_charge and minimum_charge > fuel_adjusted_total,
        "maximum_charge": float(maximum_charge_limit) if maximum_charge_limit is not None else None,
        "maximum_charge_applied": maximum_charge_applied,
        "bulk_discount_threshold_kg": float(bulk_discount_threshold) if raw_bulk_discount_threshold is not None else None,
        "bulk_discount_percent": float(bulk_discount_percent) if raw_bulk_discount_percent is not None else None,
        "bulk_discount_amount": float(bulk_discount_amount),
        "pricing_profile_id": getattr(pricing_profile, "id", None),
        "category_rule_ids": [getattr(applied_category_rule, "id", None)] if applied_category_rule is not None else [],
        "applied_category_rule_id": getattr(applied_category_rule, "id", None) if applied_category_rule is not None else None,
        "applied_category_name": getattr(applied_category_rule, "category_name", None) if applied_category_rule is not None else None,
        "matched_categories": [normalize_category_name(category) for category in (categories or []) if normalize_category_name(category)],
        "vehicle_rule_id": vehicle_rule_id_override if vehicle_rule_id_override is not None else getattr(vehicle_rule, "id", None),
        "vehicle_type": vehicle_type_override if vehicle_type_override is not None else getattr(vehicle_rule, "vehicle_type", None),
        "total_weight_kg": float(total_weight),
        "total_volume_cm3": float(total_volume),
        "shipping_amount": float(final_charge),
    })


_COUNTRY_CODE_ALIASES: dict[str, str] = {
    "AE": "AE",
    "UAE": "AE",
    "UNITEDARABEMIRATES": "AE",
    "EMIRATES": "AE",
    "PK": "PK",
    "PAKISTAN": "PK",
    "OM": "OM",
    "OMAN": "OM",
    "SA": "SA",
    "SAUDIARABIA": "SA",
    "KSA": "SA",
    "IN": "IN",
    "INDIA": "IN",
    "US": "US",
    "USA": "US",
    "UNITEDSTATES": "US",
    "UNITEDSTATESOFAMERICA": "US",
    "GB": "GB",
    "UK": "GB",
    "UNITEDKINGDOM": "GB",
    "KW": "KW",
    "KUWAIT": "KW",
    "QA": "QA",
    "QATAR": "QA",
    "BH": "BH",
    "BAHRAIN": "BH",
}


def normalize_country_code(value: str | None) -> str:
    if not value:
        return ""

    letters = "".join(ch for ch in str(value).upper() if ch.isalpha())
    if not letters:
        return ""

    aliased = _COUNTRY_CODE_ALIASES.get(letters)
    if aliased:
        return aliased

    if len(letters) == 2:
        return letters

    # Preserve backward compatibility for unknown country names/codes.
    return letters[:2]


def calculate_per_km_delivery(
    *,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str,
    vehicle_config: dict[str, dict[str, Decimal]],
    base_rate: Decimal,
    minimum_charge: Decimal,
    weight_surcharge_rate: Decimal,
    weight_surcharge_threshold_kg: Decimal,
    currency: str,
    country_code: str,
) -> dict[str, Any]:
    """Generic per-km delivery formula for any country configuration.

    total = max(base_rate + (distance_km * vehicle_rate) + weight_surcharge, minimum_charge)
    """
    vehicle_key = normalize_vehicle_type(vehicle_type) or "bike"
    vehicle = vehicle_config.get(vehicle_key)
    if vehicle is None:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")

    route_distance = round_money(to_decimal(distance_km))
    total_weight = round_money(to_decimal(weight_kg))
    max_weight = round_money(to_decimal(vehicle.get("max_weight_kg", 0) or 0))
    if max_weight > 0 and total_weight > max_weight:
        raise ValueError(f"{total_weight}kg exceeds vehicle capacity {max_weight}kg")

    per_km_rate = round_money(to_decimal(vehicle.get("per_km_rate", 0) or 0))
    surcharge_threshold = round_money(to_decimal(weight_surcharge_threshold_kg or 0))
    surcharge_rate = round_money(to_decimal(weight_surcharge_rate or 0))
    surcharge_weight = max(Decimal("0"), total_weight - surcharge_threshold)
    weight_surcharge = round_money(surcharge_weight * surcharge_rate)
    subtotal = round_money(round_money(to_decimal(base_rate or 0)) + (route_distance * per_km_rate) + weight_surcharge)
    resolved_minimum_charge = round_money(to_decimal(minimum_charge or 0))
    total = round_money(max(subtotal, resolved_minimum_charge))

    return {
        "country_code": normalize_country_code(country_code),
        "vehicle_type": vehicle_key,
        "distance_km": route_distance,
        "weight_kg": total_weight,
        "base_rate": round_money(to_decimal(base_rate or 0)),
        "per_km_rate": per_km_rate,
        "weight_surcharge": weight_surcharge,
        "minimum_charge": resolved_minimum_charge,
        "total": total,
        "currency": str(currency or ""),
    }


def _country_vehicle_config(config: CountryConfig) -> dict[str, dict[str, Decimal]]:
    base_per_km = round_money(to_decimal(getattr(config, "per_km_rate", 0) or 0))
    default_vehicle = normalize_vehicle_type(getattr(config, "default_vehicle_type", None)) or "bike"

    # Build a sensible multi-vehicle map for any country from a single country-level per_km_rate.
    config_map: dict[str, dict[str, Decimal]] = {}
    for vehicle_name, multiplier in DEFAULT_VEHICLE_MULTIPLIERS.items():
        max_weight = {
            "bike": Decimal("10"),
            "car": Decimal("30"),
            "van": Decimal("100"),
            "truck": Decimal("500"),
        }.get(vehicle_name, Decimal("100"))
        config_map[vehicle_name] = {
            "per_km_rate": round_money(base_per_km * multiplier),
            "max_weight_kg": max_weight,
        }

    # Keep configured default vehicle at exactly country per_km_rate.
    if default_vehicle in config_map:
        config_map[default_vehicle]["per_km_rate"] = base_per_km
    return config_map


def calculate_country_per_km_delivery(
    db: Session,
    *,
    country_code: str,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str | None = None,
) -> dict[str, Any]:
    """Resolve country delivery values from CountryConfig and compute per-km quote."""
    normalized_code = normalize_country_code(country_code)
    if not normalized_code:
        raise ValueError("Unknown country: empty code")

    config = (
        db.query(CountryConfig)
        .filter(CountryConfig.code == normalized_code, CountryConfig.is_active == True)  # noqa: E712
        .first()
    )
    if config is None:
        raise ValueError(f"Unknown country: {normalized_code}")

    model = str(getattr(config, "logistics_model", "") or "").strip().lower()
    if model not in {"per_km", "per-km", "distance", "distance_based"}:
        raise ValueError(f"Country {normalized_code} is not configured for per-km logistics")

    resolved_vehicle = normalize_vehicle_type(vehicle_type) or normalize_vehicle_type(getattr(config, "default_vehicle_type", None)) or "bike"
    vehicle_config = _country_vehicle_config(config)
    return calculate_per_km_delivery(
        distance_km=distance_km,
        weight_kg=weight_kg,
        vehicle_type=resolved_vehicle,
        vehicle_config=vehicle_config,
        base_rate=round_money(to_decimal(getattr(config, "base_rate", 0) or 0)),
        minimum_charge=round_money(to_decimal(getattr(config, "minimum_charge", 0) or 0)),
        weight_surcharge_rate=round_money(to_decimal(getattr(config, "weight_surcharge_rate", 0) or 0)),
        weight_surcharge_threshold_kg=round_money(to_decimal(getattr(config, "weight_surcharge_threshold_kg", 0) or 0)),
        currency=str(getattr(config, "currency", "") or ""),
        country_code=normalized_code,
    )


def calculate_pk_delivery(
    *,
    db: Session,
    distance_km: Decimal,
    weight_kg: Decimal,
    vehicle_type: str = "bike",
) -> dict[str, Any]:
    """Pakistan-specific helper — reads per-km pricing from CountryConfig for PK."""
    return calculate_country_per_km_delivery(
        db=db,
        country_code="PK",
        distance_km=distance_km,
        weight_kg=weight_kg,
        vehicle_type=vehicle_type,
    )


def calculate_pk_delivery_for_cities(
    db: Session,
    *,
    origin_country_code: str,
    origin_city_name: str,
    destination_country_code: str,
    destination_city_name: str,
    weight_kg: Decimal,
    vehicle_type: str = "bike",
) -> dict[str, Any]:
    """Backward-compatible city-distance helper for Pakistan delivery quotes."""
    distance_km = lookup_city_distance_km(
        db,
        origin_country_code=origin_country_code,
        origin_city_name=origin_city_name,
        destination_country_code=destination_country_code,
        destination_city_name=destination_city_name,
    )
    return calculate_pk_delivery(db=db, distance_km=distance_km, weight_kg=weight_kg, vehicle_type=vehicle_type)


def normalize_city_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


def partner_is_profile_approved(partner: LogisticsPartner | None) -> bool:
    if partner is None:
        return False
    return (
        cast(str | None, getattr(partner, "status", None)) == "active"
        and cast(str | None, getattr(partner, "verification_status", None)) == APPROVED_PROFILE_STATUS
    )


def serialize_service_area(area: LogisticsPartnerServiceArea) -> dict[str, Any]:
    reviewed_at = cast(Optional[Any], getattr(area, "reviewed_at", None))
    created_at = cast(Optional[Any], getattr(area, "created_at", None))
    updated_at = cast(Optional[Any], getattr(area, "updated_at", None))
    charge_amount = cast(Decimal | float | int | None, getattr(area, "charge_amount", None))
    minimum_charge = cast(Decimal | float | int | None, getattr(area, "minimum_charge", None))
    per_kg_rate = cast(Decimal | float | int | None, getattr(area, "per_kg_rate", None))
    per_km_rate = cast(Decimal | float | int | None, getattr(area, "per_km_rate", None))
    fuel_multiplier = cast(Decimal | float | int | None, getattr(area, "fuel_multiplier", None))
    pickup_charge = cast(Decimal | float | int | None, getattr(area, "pickup_charge", None))
    dropoff_charge = cast(Decimal | float | int | None, getattr(area, "dropoff_charge", None))
    return {
        "id": area.id,
        "partner_id": area.partner_id,
        "country_code": area.country_code,
        "country_name": area.country_name,
        "city_name": area.city_name,
        "origin_city": getattr(area, "origin_city", None),
        "zone_label": area.zone_label,
        "charge_amount": float(charge_amount or 0),
        "minimum_charge": float(minimum_charge) if minimum_charge is not None else None,
        "per_kg_rate": float(per_kg_rate) if per_kg_rate is not None else None,
        "per_km_rate": float(per_km_rate) if per_km_rate is not None else None,
        "fuel_multiplier": float(fuel_multiplier) if fuel_multiplier is not None else 1.0,
        "pickup_charge": float(pickup_charge) if pickup_charge is not None else None,
        "dropoff_charge": float(dropoff_charge) if dropoff_charge is not None else None,
        "currency": area.currency,
        "latitude": getattr(area, "latitude", None),
        "longitude": getattr(area, "longitude", None),
        "delivery_days_min": area.delivery_days_min,
        "delivery_days_max": area.delivery_days_max,
        "is_active": bool(area.is_active),
        "approval_status": area.approval_status,
        "review_note": area.review_note,
        "reviewed_by": area.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def resolve_destination(*, country: str | None = None, city: str | None = None, shipping_address: str | None = None, order: Order | None = None) -> dict[str, str | None]:
    resolved_country = (country or "").strip()
    resolved_city = (city or "").strip()
    shipping_text = (shipping_address or "").strip()

    if order is not None:
        resolved_country = resolved_country or str(getattr(order, "shipping_country", "") or "").strip()
        resolved_city = resolved_city or str(getattr(order, "shipping_city", "") or "").strip()
        shipping_text = shipping_text or str(getattr(order, "shipping_address", "") or "").strip()

    if shipping_text:
        parts = [part.strip() for part in shipping_text.split(",") if part.strip()]
        if not resolved_country and parts:
            resolved_country = parts[-1]
        if not resolved_city:
            if len(parts) >= 3:
                resolved_city = parts[-3]
            elif parts:
                resolved_city = parts[0]

    return {
        "country": resolved_country or None,
        "country_code": normalize_country_code(resolved_country),
        "city": resolved_city or None,
        "city_key": normalize_city_name(resolved_city),
    }


def approved_service_areas_query(db: Session):
    return (
        db.query(LogisticsPartnerServiceArea)
        .join(LogisticsPartner, LogisticsPartner.id == LogisticsPartnerServiceArea.partner_id)
        .filter(
            LogisticsPartner.status == "active",
            LogisticsPartner.verification_status == APPROVED_PROFILE_STATUS,
            LogisticsPartnerServiceArea.is_active == True,  # noqa: E712
            LogisticsPartnerServiceArea.approval_status == APPROVED_AREA_STATUS,
        )
    )


def find_matching_service_areas(
    db: Session,
    *,
    country: str | None,
    city: str | None = None,
    partner_id: int | None = None,
    supplier_city: str | None = None,
) -> list[LogisticsPartnerServiceArea]:
    destination = resolve_destination(country=country, city=city)
    if not destination["country_code"]:
        return []

    query = approved_service_areas_query(db).filter(
        LogisticsPartnerServiceArea.country_code == destination["country_code"],
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerServiceArea.partner_id == partner_id)

    rows = query.order_by(LogisticsPartnerServiceArea.updated_at.desc(), LogisticsPartnerServiceArea.id.desc()).all()
    if not rows:
        return []

    city_key = cast(str, destination["city_key"] or "")
    if not city_key:
        country_rows = [row for row in rows if not normalize_city_name(cast(str | None, getattr(row, "city_name", None)))]
        rows = country_rows or rows
    else:
        exact_rows = [
            row
            for row in rows
            if normalize_city_name(cast(str | None, getattr(row, "city_name", None))) == city_key
        ]
        if exact_rows:
            rows = exact_rows
        else:
            rows = [row for row in rows if not normalize_city_name(cast(str | None, getattr(row, "city_name", None)))]

    # Filter by origin_city (pickup city): NULL origin means any pickup city is accepted
    if supplier_city:
        normalized_supplier = normalize_city_name(supplier_city)
        rows = [
            row for row in rows
            if not getattr(row, "origin_city", None)
            or normalize_city_name(cast(str | None, getattr(row, "origin_city", None))) == normalized_supplier
        ]

    return rows


def quote_shipping_for_destination(
    db: Session,
    *,
    country: str | None,
    city: str | None = None,
    partner_id: int | None = None,
    supplier_city: str | None = None,
    total_weight_kg: Decimal | float | int | None = None,
    categories: list[str] | None = None,
    total_volume_cm3: Decimal | float | int | None = None,
    pickup_count: int | None = None,
    dropoff_count: int | None = None,
) -> dict[str, Any] | None:
    matches = find_matching_service_areas(db, country=country, city=city, partner_id=partner_id, supplier_city=supplier_city)
    if not matches:
        return None

    destination = resolve_destination(country=country, city=city)
    dest_city = cast(str | None, destination.get("city"))
    dest_cc = cast(str | None, destination.get("country_code"))

    ranked = sorted(
        (
            (
                area,
                resolve_pricing_profile_for_area(db, area),
                _resolve_route_context(area, destination_country_code=dest_cc, destination_city_name=dest_city),
            )
            for area in matches
        ),
        key=lambda item: item[0].id,
    )

    resolved_quotes: list[tuple[LogisticsPartnerServiceArea, LogisticsPricingProfile | None, dict[str, Any]]] = []
    for area, pricing_profile, route_context in ranked:
        effective_per_km_rate = getattr(pricing_profile, "per_km_rate", None) if getattr(pricing_profile, "per_km_rate", None) is not None else getattr(area, "per_km_rate", None)
        category_rules = resolve_category_rules_for_area(db, area, categories)
        distance_km = None
        if effective_per_km_rate and not route_context["is_in_city"]:
            distance_km = lookup_city_distance_km(
                db,
                origin_country_code=cast(str | None, route_context["origin_country_code"]),
                origin_city_name=cast(str | None, route_context["origin_city_name"]),
                destination_country_code=dest_cc,
                destination_city_name=dest_city,
            )
        vehicle_rule = resolve_vehicle_rule_for_area(
            db,
            area,
            route_type=cast(str, route_context["route_type"]),
            total_weight_kg=total_weight_kg,
            total_volume_cm3=total_volume_cm3,
        )
        pricing_breakdown = _build_service_area_pricing_breakdown(
            area,
            pricing_profile=pricing_profile,
            category_rules=category_rules,
            vehicle_rule=vehicle_rule,
            apply_vehicle_multiplier=False,
            categories=categories,
            total_weight_kg=total_weight_kg,
            total_volume_cm3=total_volume_cm3,
            pickup_count=pickup_count,
            dropoff_count=dropoff_count,
            distance_km=distance_km,
            destination_country_code=dest_cc,
            destination_city_name=dest_city,
        )
        resolved_quotes.append((area, pricing_profile, pricing_breakdown))

    selected, pricing_profile, pricing_breakdown = sorted(
        resolved_quotes,
        key=lambda item: (item[2]["shipping_amount"], item[0].id),
    )[0]
    partner = cast(LogisticsPartner | None, getattr(selected, "partner", None))
    return {
        "shipping_amount": pricing_breakdown["shipping_amount"],
        "currency": selected.currency,
        "partner_id": selected.partner_id,
        "partner_name": getattr(partner, "name", None) if partner else None,
        "partner_code": getattr(partner, "code", None) if partner else None,
        "service_area": serialize_service_area(selected),
        "pricing_profile": serialize_pricing_profile(pricing_profile) if pricing_profile is not None else None,
        "category_rules": [serialize_category_pricing_rule(rule) for rule in resolve_category_rules_for_area(db, selected, categories)],
        "vehicle_rule": serialize_vehicle_rule(resolve_vehicle_rule_for_area(db, selected, route_type=cast(str, pricing_breakdown["route_type"]), total_weight_kg=total_weight_kg, total_volume_cm3=total_volume_cm3)) if resolve_vehicle_rule_for_area(db, selected, route_type=cast(str, pricing_breakdown["route_type"]), total_weight_kg=total_weight_kg, total_volume_cm3=total_volume_cm3) is not None else None,
        "pricing_breakdown": pricing_breakdown,
        "destination": resolve_destination(country=country, city=city),
    }


def partner_can_service_order(partner: LogisticsPartner, order: Order, db: Session) -> bool:
    if not partner_is_profile_approved(partner):
        return False
    destination = resolve_destination(order=order)
    if not destination["country_code"]:
        return False
    quote = quote_shipping_for_destination(
        db,
        country=cast(str | None, destination["country"]),
        city=cast(str | None, destination["city"]),
        partner_id=cast(int, getattr(partner, "id")),
    )
    return quote is not None

# -------------------------------------------------------------------
# FROM: partner\partner_geography_service.py
# -------------------------------------------------------------------

"""Country-scoped logistics partner read/write operations.

Owns the DB reads/writes for the inline partner endpoints in
``admin_logistics_geography`` so the router stays free of ``db.query``/``db.commit``.
Archive/restore/hard-delete are delegated to the admin controller.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.logistics.models.logistics import LogisticsPartner
from infrastructure.utils.pagination import keyset_paginated_response
import structlog
logger = structlog.get_logger(__name__)


def list_partners(db: Session, country_code: str, include_deleted: bool, cursor: str | None, page_size: int) -> dict:
    """Return a keyset (cursor) page of logistics partners for a country (diagram §6: never OFFSET)."""
    q = db.query(LogisticsPartner).filter(LogisticsPartner.country_code == country_code.upper())
    if not include_deleted:
        q = q.filter(LogisticsPartner.is_deleted == False)  # noqa: E712
    total = q.count()
    return keyset_paginated_response(
        q, sort_keys=[(LogisticsPartner.id, "asc")], cursor=cursor, page_size=page_size, total=total,
    )


def _get_partner(db: Session, partner_id: int, country_code: str) -> LogisticsPartner:
    p = (
        db.query(LogisticsPartner)
        .filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper())
        .first()
    )
    if not p:
        raise HTTPException(404)
    return p


def approve_partner(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.verification_status = "approved"
    db.commit()
    return {"message": "Partner approved"}


def reject_partner(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.verification_status = "rejected"
    db.commit()
    return {"message": "Partner rejected"}


def toggle_partner_active(db: Session, partner_id: int, country_code: str) -> dict:
    p = _get_partner(db, partner_id, country_code)
    p.status = "suspended" if p.status == "active" else "active"
    db.commit()
    return {"message": f"Partner {'suspended' if p.status == 'suspended' else 'activated'}"}

