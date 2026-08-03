"""
Logistics Partner Router — partner management and partner dashboard.
All business logic in controllers/logistics_partner_controller.py.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.db import get_db
from routers.auth import get_current_user
import controllers.logistics_partner_controller as ctrl

router = APIRouter()


@router.get("/public")
def list_public_logistics_partners(
    request: Request,
    q: Optional[str] = Query(None),
    country: Optional[str] = Query(None, min_length=2, max_length=10),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    resolved_country = (
        country
        or request.headers.get("X-Country-Code")
        or getattr(request.state, "country_code", None)
    )
    return ctrl.list_public_partners(db, q=q, country=resolved_country, limit=limit)


@router.get("/public/{partner_id}")
def get_public_logistics_partner(
    partner_id: int,
    db: Session = Depends(get_db),
):
    return ctrl.get_public_partner(partner_id, db)


@router.get("/profile")
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_my_partner_profile(current_user, db)


@router.put("/profile")
def update_partner_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.update_my_partner_profile(data, current_user, db)


@router.post("/profile/terms/accept")
def accept_partner_profile_terms(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.accept_partner_terms(current_user, db)


@router.post("/profile/submit-review")
def submit_partner_profile_review(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.submit_partner_profile_for_review(current_user, db)


@router.get("/service-areas")
def get_partner_service_areas(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_service_areas(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
    )


@router.get("/pricing-profiles")
def get_partner_pricing_profiles(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_pricing_profiles(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/category-rules")
def get_partner_category_rules(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_category_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/vehicle-rules")
def get_partner_vehicle_rules(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_vehicle_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/pricing-insights")
def get_partner_pricing_insights(
    partner_id: Optional[int] = Query(None),
    service_area_id: Optional[int] = Query(None),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_pricing_insights(
        current_user,
        db,
        partner_id=partner_id,
        service_area_id=service_area_id,
        limit=limit,
    )


@router.post("/pricing-profiles")
def create_partner_pricing_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_pricing_profile(None, data, current_user, db)


@router.put("/pricing-profiles/{profile_id}")
def update_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_pricing_profile(profile_id, data, current_user, db)


@router.delete("/pricing-profiles/{profile_id}")
def delete_partner_pricing_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_pricing_profile(profile_id, current_user, db)


@router.post("/category-rules")
def create_partner_category_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_category_rule(None, data, current_user, db)


@router.put("/category-rules/{rule_id}")
def update_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_category_rule(rule_id, data, current_user, db)


@router.delete("/category-rules/{rule_id}")
def delete_partner_category_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_category_rule(rule_id, current_user, db)


@router.post("/vehicle-rules")
def create_partner_vehicle_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_vehicle_rule(None, data, current_user, db)


@router.put("/vehicle-rules/{rule_id}")
def update_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_vehicle_rule(rule_id, data, current_user, db)


@router.delete("/vehicle-rules/{rule_id}")
def delete_partner_vehicle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_vehicle_rule(rule_id, current_user, db)


@router.post("/service-areas")
def create_partner_service_area(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_service_area(None, data, current_user, db)


@router.put("/service-areas/{area_id}")
def update_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_service_area(area_id, data, current_user, db)


@router.delete("/service-areas/{area_id}")
def delete_partner_service_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_service_area(area_id, current_user, db)


@router.post("/review/profile/{partner_id}")
def review_logistics_partner_profile(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_profile(partner_id, data, current_user, db)


@router.post("/review/service-areas/{area_id}")
def review_logistics_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_service_area(area_id, data, current_user, db)


@router.post("/review/pricing-profiles/{profile_id}")
def review_logistics_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_pricing_profile(profile_id, data, current_user, db)


@router.post("/review/category-rules/{rule_id}")
def review_logistics_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_category_rule(rule_id, data, current_user, db)


@router.post("/review/vehicle-rules/{rule_id}")
def review_logistics_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_vehicle_rule(rule_id, data, current_user, db)


@router.post("/shipping-quote")
def get_logistics_shipping_quote(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.shipping_quote_for_customer(data, db)


# ── Admin: manage partners ────────────────────────────────────────────────────

@router.get("/")
def list_partners(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: list all logistics partners."""
    return ctrl.list_partners(current_user, db)


@router.post("/", status_code=201)
def create_partner(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: onboard a new logistics partner."""
    return ctrl.create_partner(data, current_user, db)


class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None


@router.post("/bulk")
def bulk_manage_logistics_partners(
    body: BulkPartnerAdminActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin bulk actions for logistics partner review and portal lifecycle."""
    return ctrl.bulk_manage_partners(body.partner_ids, body.action, body.note, current_user, db)


@router.put("/{partner_id}")
def update_partner(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: update partner details or status."""
    return ctrl.update_partner(partner_id, data, current_user, db)


@router.delete("/{partner_id}")
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin-only: remove a logistics partner."""
    return ctrl.delete_partner(partner_id, current_user, db)


# ── Partner Dashboard ─────────────────────────────────────────────────────────

@router.get("/dashboard")
def partner_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Dashboard stats for logistics partner or admin."""
    return ctrl.get_partner_dashboard(current_user, db)


@router.get("/analytics")
def partner_analytics(
    period: str = Query("30d", description="Analytics lookback window: 7d, 30d, or 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_analytics(current_user, db, period=period)


@router.get("/payouts")
def partner_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_payouts(current_user, db)


@router.post("/payouts/request")
def request_payout(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.request_partner_payout(data, current_user, db)


@router.get("/payouts/pending")
def pending_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_pending_partner_payouts(current_user, db)


@router.post("/payouts/{payout_id}/verify")
def verify_payout(
    payout_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.verify_partner_payout(payout_id, data, current_user, db)


@router.get("/shipments/scan")
def scan_lookup_shipment(
    code: str = Query(..., description="Scan code or tracking number to look up"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Look up a shipment by scan code or tracking number (logistics partners and admins)."""
    return ctrl.scan_lookup_shipment_partner(code, current_user, db)


@router.get("/shipments")
def list_partner_shipments(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List shipments assigned to (or visible by) this logistics partner."""
    return ctrl.get_partner_shipments(current_user, db, status=status, page=page, page_size=page_size)


@router.put("/shipments/{shipment_id}/status")
def update_shipment_status(
    shipment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Partner updates the status of a shipment (e.g., in_transit, delivered)."""
    return ctrl.update_shipment_status_partner(shipment_id, data, current_user, db)


@router.post("/shipments/{shipment_id}/confirmation-request")
def create_shipment_confirmation_request(
    shipment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Partner creates a pending pickup or delivery confirmation request."""
    return ctrl.create_shipment_confirmation_request_partner(shipment_id, data, current_user, db)


class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None


@router.put("/shipments/bulk-status")
def bulk_update_shipments_status(
    body: BulkShipmentStatusRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Bulk-update shipment status for multiple shipments (up to 100).
    Partners can only update their own assigned shipments.
    Note: 'delivered' requires signature — use the single-shipment endpoint instead.
    """
    return ctrl.bulk_update_shipment_status_partner(
        body.shipment_ids, body.status, body.notes, current_user, db
    )


# ── Logistics Partner Bank Account (Payout Beneficiary) ───────────────────────

@router.get("/me/bank-account")
def get_partner_bank_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the logistics partner's saved payout bank account."""
    return ctrl.get_partner_bank_account(current_user, db)


@router.put("/me/bank-account")
def upsert_partner_bank_account(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit or update the logistics partner's payout bank account. Triggers admin verification."""
    return ctrl.upsert_partner_bank_account(body, current_user, db)


@router.get("/me/cod-remittance-receipts")
def list_my_cod_remittance_receipts(
    status: Optional[str] = Query(None),
    settlement_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_partner_cod_remittance_receipts(current_user, db, status=status, settlement_id=settlement_id)


@router.post("/me/cod-remittance-receipts", status_code=201)
async def upload_my_cod_remittance_receipt(
    settlement_id: int = Form(...),
    amount: float = Form(...),
    bank_reference: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.upload_partner_cod_remittance_receipt(
        settlement_id,
        amount,
        file,
        bank_reference,
        notes,
        current_user,
        db,
    )


# ── Logistics Partner Documents ───────────────────────────────────────────────

@router.get("/me/docs")
def list_lp_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all KYC/compliance documents submitted by the authenticated logistics partner."""
    return ctrl.list_partner_documents(current_user, db)


@router.post("/me/docs/upload")
async def upload_lp_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(""),
    expires_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload a KYC/compliance document (multipart/form-data)."""
    return await ctrl.upload_partner_document(file, document_type, document_name, expires_at, current_user, db)


@router.delete("/me/docs/{doc_id}")
def delete_lp_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a pending or rejected document."""
    return ctrl.delete_partner_document(doc_id, current_user, db)


@router.post("/admin/docs/{doc_id}/review")
def admin_review_lp_document(
    doc_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin reviews a logistics partner document — approve/reject."""
    return ctrl.admin_review_lp_document(doc_id, body, current_user, db)


# ── City Distance Matrix (admin only) ─────────────────────────────────────────

@router.get("/city-distances")
def list_city_distances(
    origin_country_code: Optional[str] = Query(None),
    destination_country_code: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: list city distance matrix entries with optional filtering."""
    return ctrl.list_city_distances(current_user, db, origin_country_code=origin_country_code, destination_country_code=destination_country_code, q=q, page=page, page_size=page_size)


@router.post("/city-distances")
def create_city_distance(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: create a new city distance matrix entry."""
    return ctrl.create_city_distance(body, current_user, db)


@router.put("/city-distances/{matrix_id}")
def update_city_distance(
    matrix_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: update distance_km (and optional notes) for an existing entry."""
    return ctrl.update_city_distance(matrix_id, body, current_user, db)


@router.delete("/city-distances/{matrix_id}")
def delete_city_distance(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: delete a city distance matrix entry."""
    return ctrl.delete_city_distance(matrix_id, current_user, db)



