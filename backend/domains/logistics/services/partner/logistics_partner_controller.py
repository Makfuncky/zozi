"""logistics domain partner controller (AXIS 2).

Thin adapter: imports the real partner-management functions from the
orders-domain partner service and adapts the authenticated User ORM object
into the dict shape those functions expect. Module routers call this module
(the logistics domain entry point); it delegates across domains to orders.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from domains.orders.services.logistics_partner_controller import (
    accept_partner_terms,
    admin_review_lp_document,
    bulk_manage_partners,
    bulk_update_shipment_status_partner,
    create_city_distance,
    create_partner,
    create_shipment_confirmation_request_partner,
    delete_city_distance,
    delete_my_partner_category_rule,
    delete_my_partner_pricing_profile,
    delete_my_partner_service_area,
    delete_my_partner_vehicle_rule,
    delete_partner,
    delete_partner_document,
    get_my_partner_profile,
    get_partner_analytics,
    get_partner_bank_account,
    get_partner_dashboard,
    get_partner_payouts,
    get_partner_pricing_insights,
    get_partner_shipments,
    get_public_partner,
    list_city_distances,
    list_my_partner_category_rules,
    list_my_partner_pricing_profiles,
    list_my_partner_service_areas,
    list_my_partner_vehicle_rules,
    list_partner_cod_remittance_receipts,
    list_partner_documents,
    list_partners,
    list_pending_partner_payouts,
    list_public_partners,
    request_partner_payout,
    review_partner_category_rule,
    review_partner_pricing_profile,
    review_partner_profile,
    review_partner_service_area,
    review_partner_vehicle_rule,
    scan_lookup_shipment_partner,
    shipping_quote_for_customer,
    submit_partner_profile_for_review,
    update_city_distance,
    update_my_partner_profile,
    update_partner,
    update_shipment_status_partner,
    upload_partner_cod_remittance_receipt,
    upload_partner_document,
    upsert_my_partner_category_rule,
    upsert_my_partner_pricing_profile,
    upsert_my_partner_service_area,
    upsert_my_partner_vehicle_rule,
    upsert_partner_bank_account,
    verify_partner_payout,
)


def _user_dict(current_user: Any) -> dict:
    """Convert the authenticated User ORM object into the dict the orders service expects."""
    return {"id": current_user.id, "role": getattr(current_user, "role", None)}


def list_public_partners(db: Session, q=None, country=None, limit: int = 12):
    return list_public_partners(db, q=q, country=country, limit=limit)


def get_public_partner(partner_id: int, db: Session):
    return get_public_partner(partner_id, db)


def get_my_partner_profile(current_user, db: Session):
    return get_my_partner_profile(_user_dict(current_user), db)


def update_my_partner_profile(data: dict, current_user, db: Session):
    return update_my_partner_profile(data, _user_dict(current_user), db)


def accept_partner_terms(current_user, db: Session):
    return accept_partner_terms(_user_dict(current_user), db)


def submit_partner_profile_review(current_user, db: Session):
    return submit_partner_profile_review(_user_dict(current_user), db)


def list_my_partner_service_areas(current_user, db: Session, partner_id=None, approval_status=None):
    return list_my_partner_service_areas(_user_dict(current_user), db, partner_id=partner_id, approval_status=approval_status)


def list_my_partner_pricing_profiles(current_user, db: Session, partner_id=None, approval_status=None, service_area_id=None):
    return list_my_partner_pricing_profiles(_user_dict(current_user), db, partner_id=partner_id, approval_status=approval_status, service_area_id=service_area_id)


def list_my_partner_category_rules(current_user, db: Session, partner_id=None, approval_status=None, service_area_id=None):
    return list_my_partner_category_rules(_user_dict(current_user), db, partner_id=partner_id, approval_status=approval_status, service_area_id=service_area_id)


def list_my_partner_vehicle_rules(current_user, db: Session, partner_id=None, approval_status=None, service_area_id=None):
    return list_my_partner_vehicle_rules(_user_dict(current_user), db, partner_id=partner_id, approval_status=approval_status, service_area_id=service_area_id)


def get_partner_pricing_insights(current_user, db: Session, partner_id=None, service_area_id=None, limit: int = 12):
    return get_partner_pricing_insights(_user_dict(current_user), db, partner_id=partner_id, service_area_id=service_area_id, limit=limit)


def upsert_my_partner_pricing_profile(profile_id, data, current_user, db: Session):
    return upsert_my_partner_pricing_profile(profile_id, data, _user_dict(current_user), db)


def delete_my_partner_pricing_profile(profile_id, current_user, db: Session):
    return delete_my_partner_pricing_profile(profile_id, _user_dict(current_user), db)


def upsert_my_partner_category_rule(rule_id, data, current_user, db: Session):
    return upsert_my_partner_category_rule(rule_id, data, _user_dict(current_user), db)


def delete_my_partner_category_rule(rule_id, current_user, db: Session):
    return delete_my_partner_category_rule(rule_id, _user_dict(current_user), db)


def upsert_my_partner_vehicle_rule(rule_id, data, current_user, db: Session):
    return upsert_my_partner_vehicle_rule(rule_id, data, _user_dict(current_user), db)


def delete_my_partner_vehicle_rule(rule_id, current_user, db: Session):
    return delete_my_partner_vehicle_rule(rule_id, _user_dict(current_user), db)


def upsert_my_partner_service_area(area_id, data, current_user, db: Session):
    return upsert_my_partner_service_area(area_id, data, _user_dict(current_user), db)


def delete_my_partner_service_area(area_id, current_user, db: Session):
    return delete_my_partner_service_area(area_id, _user_dict(current_user), db)


def review_partner_profile(partner_id, data, current_user, db: Session):
    return review_partner_profile(partner_id, data, _user_dict(current_user), db)


def review_partner_service_area(area_id, data, current_user, db: Session):
    return review_partner_service_area(area_id, data, _user_dict(current_user), db)


def review_partner_pricing_profile(profile_id, data, current_user, db: Session):
    return review_partner_pricing_profile(profile_id, data, _user_dict(current_user), db)


def review_partner_category_rule(rule_id, data, current_user, db: Session):
    return review_partner_category_rule(rule_id, data, _user_dict(current_user), db)


def review_partner_vehicle_rule(rule_id, data, current_user, db: Session):
    return review_partner_vehicle_rule(rule_id, data, _user_dict(current_user), db)


def shipping_quote_for_customer(data, db: Session, current_user=None):
    return shipping_quote_for_customer(data, db)


def list_partners(current_user, db: Session):
    return list_partners(_user_dict(current_user), db)


def create_partner(data, current_user, db: Session):
    return create_partner(data, _user_dict(current_user), db)


def bulk_manage_partners(partner_ids, action, note, current_user, db: Session):
    return bulk_manage_partners(partner_ids, action, note, _user_dict(current_user), db)


def update_partner(partner_id, data, current_user, db: Session):
    return update_partner(partner_id, data, _user_dict(current_user), db)


def delete_partner(partner_id, current_user, db: Session):
    return delete_partner(partner_id, _user_dict(current_user), db)


def get_partner_dashboard(current_user, db: Session):
    return get_partner_dashboard(_user_dict(current_user), db)


def get_partner_analytics(current_user, db: Session, period: str = "30d"):
    return get_partner_analytics(_user_dict(current_user), db, period=period)


def get_partner_payouts(current_user, db: Session):
    return get_partner_payouts(_user_dict(current_user), db)


def request_partner_payout(data, current_user, db: Session):
    return request_partner_payout(data, _user_dict(current_user), db)


def list_pending_partner_payouts(current_user, db: Session):
    return list_pending_partner_payouts(_user_dict(current_user), db)


def verify_partner_payout(payout_id, data, current_user, db: Session):
    return verify_partner_payout(payout_id, data, _user_dict(current_user), db)


def scan_lookup_shipment(code, current_user, db: Session):
    return scan_lookup_shipment_partner(code, _user_dict(current_user), db)


def get_partner_shipments(current_user, db: Session, status=None, page=1, page_size=30):
    return get_partner_shipments(_user_dict(current_user), db, status=status, page=page, page_size=page_size)


def update_shipment_status_partner(shipment_id, data, current_user, db: Session):
    return update_shipment_status_partner(shipment_id, data, _user_dict(current_user), db)


def create_shipment_confirmation_request_partner(shipment_id, data, current_user, db: Session):
    return create_shipment_confirmation_request_partner(shipment_id, data, _user_dict(current_user), db)


def bulk_update_shipment_status_partner(shipment_ids, status, notes, current_user, db: Session):
    return bulk_update_shipment_status_partner(shipment_ids, status, notes, _user_dict(current_user), db)


def get_partner_bank_account(current_user, db: Session):
    return get_partner_bank_account(_user_dict(current_user), db)


def upsert_partner_bank_account(body, current_user, db: Session):
    return upsert_partner_bank_account(body, _user_dict(current_user), db)


def list_partner_cod_remittance_receipts(current_user, db: Session, status=None, settlement_id=None):
    return list_partner_cod_remittance_receipts(_user_dict(current_user), db, status=status, settlement_id=settlement_id)


async def upload_partner_cod_remittance_receipt(settlement_id, amount, file, bank_reference, notes, current_user, db: Session):
    return await upload_partner_cod_remittance_receipt(settlement_id, amount, file, bank_reference, notes, _user_dict(current_user), db)


def list_partner_documents(current_user, db: Session):
    return list_partner_documents(_user_dict(current_user), db)


async def upload_partner_document(file, document_type, document_name, expires_at, current_user, db: Session):
    return await upload_partner_document(file, document_type, document_name, expires_at, _user_dict(current_user), db)


def delete_partner_document(doc_id, current_user, db: Session):
    return delete_partner_document(doc_id, _user_dict(current_user), db)


def admin_review_lp_document(doc_id, body, current_user, db: Session):
    return admin_review_lp_document(doc_id, body, _user_dict(current_user), db)


def list_city_distances(current_user, db: Session, origin_country_code=None, destination_country_code=None, q=None, page=1, page_size=50):
    return list_city_distances(_user_dict(current_user), db, origin_country_code=origin_country_code, destination_country_code=destination_country_code, q=q, page=page, page_size=page_size)


def create_city_distance(body, current_user, db: Session):
    return create_city_distance(body, _user_dict(current_user), db)


def update_city_distance(matrix_id, body, current_user, db: Session):
    return update_city_distance(matrix_id, body, _user_dict(current_user), db)


def delete_city_distance(matrix_id, current_user, db: Session):
    return delete_city_distance(matrix_id, _user_dict(current_user), db)
