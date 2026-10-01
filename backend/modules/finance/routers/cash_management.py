"""Finance cash-management controller functions (thin HTTP-layer helpers).

Per ARCHITECTURE_STACK.md Law 2 and Law 14, controller logic lives in module
routers, not in domain services.  This module is the canonical home for the
cash-management controller functions that were previously embedded in
``domains.finance.services.finance_service``.

Existing callers in ``modules.logistics.routers.finance`` still import these
names from ``domains.finance.services.finance_service``; that module re-exports
lazy wrappers so the import graph does not break during the migration.
"""

from __future__ import annotations

from typing import Optional

from starlette.exceptions import HTTPException
from sqlalchemy.orm import Session

from domains.finance.services.treasury.cash_management_service import CashManagementService

ctrl = CashManagementService(None)

# ── Admin controllers ────────────────────────────────────────────────────────

def admin_financial_summary(db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_financial_summary(db)


def admin_reconciliation_summary(db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_reconciliation_summary(db)


def admin_list_ledger(skip: int, limit: int, order_id: Optional[int], supplier_id: Optional[int], settlement_status: Optional[str], payment_method: Optional[str], category_slug: Optional[str], badge_level: Optional[str], calculation_method: Optional[str], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_ledger_entries(
        db, skip=skip, limit=limit,
        order_id=order_id, supplier_id=supplier_id,
        settlement_status=settlement_status, payment_method=payment_method,
        category_slug=category_slug, badge_level=badge_level, calculation_method=calculation_method,
    )


def admin_list_badge_billings(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], badge_level: Optional[str], charge_type: Optional[str], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_badge_billing_records(
        db,
        skip=skip,
        limit=limit,
        supplier_id=supplier_id,
        status=status,
        badge_level=badge_level,
        charge_type=charge_type,
    )


def admin_record_badge_billing_payment(billing_id: int, body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_badge_billing_payment(
        billing_id=billing_id,
        payment_method=body.payment_method,
        current_admin=current_admin,
        db=db,
        transaction_ref=body.transaction_ref,
        notes=body.notes,
    )
    db.commit()
    return result


def admin_list_supplier_settlements(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_supplier_settlements(db, skip=skip, limit=limit, supplier_id=supplier_id, status=status)


def admin_list_logistics_settlements(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_logistics_settlements(db, skip=skip, limit=limit, partner_id=partner_id, status=status)


def admin_list_bank_transactions(skip: int, limit: int, source: Optional[str], category: Optional[str], reconciled: Optional[bool], flagged: Optional[bool], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_bank_transactions(
        db, skip=skip, limit=limit,
        source=source, category=category,
        reconciled=reconciled, flagged=flagged,
    )


def admin_list_refunds(skip: int, limit: int, status: Optional[str], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_refunds(db, skip=skip, limit=limit, status=status)


def admin_list_vat_remittances(skip: int, limit: int, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_vat_remittance_records(db, skip=skip, limit=limit)


def admin_get_bank_settings(db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_finance_bank_settings(db)


def admin_list_transfer_providers(db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_transfer_providers(db)


def admin_test_bank_settings_connection(db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_test_finance_bank_connection(db)


def admin_upsert_bank_settings(body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_upsert_finance_bank_settings(body.model_dump(), current_admin, db)
    db.commit()
    return result


def admin_record_vat_remittance(body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_vat_remittance(body.model_dump(), current_admin, db)
    db.commit()
    return result


def admin_create_bank_transaction(data, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_create_bank_transaction(data.model_dump(), db)
    db.commit()
    return result


def admin_import_bank_transactions(items: list, auto_reconcile: bool, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_import_bank_transactions(
        [item.model_dump() for item in items],
        current_admin,
        db,
        auto_reconcile=auto_reconcile,
    )
    db.commit()
    return result


def admin_reconcile_transaction(txn_id: int, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reconcile_transaction(txn_id, current_admin, db)
    db.commit()
    return result


def admin_flag_transaction(txn_id: int, body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_flag_transaction(txn_id, body.reason, db)
    db.commit()
    return result


def admin_resolve_transaction(txn_id: int, body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_resolve_transaction_exception(txn_id, body.model_dump(), current_admin, db)
    db.commit()
    return result


def admin_auto_reconcile_transactions(limit: int, source: Optional[str], category: Optional[str], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_auto_reconcile_transactions(
        current_admin,
        db,
        limit=limit,
        source=source,
        category=category,
    )
    db.commit()
    return result


def admin_trigger_supplier_payouts(body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_supplier_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}


def admin_trigger_logistics_payouts(body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_logistics_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}


def admin_dispatch_payouts(kind: str, provider: Optional[str], dry_run: bool, background: bool, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    if background:
        return ctrl.admin_queue_dispatch_transfer_batch(
            kind,
            current_admin,
            provider=provider,
            dry_run=dry_run,
        )

    result = ctrl.admin_dispatch_transfer_batch(
        kind,
        current_admin,
        db,
        provider=provider,
        dry_run=dry_run,
    )
    db.commit()
    return result


def admin_record_cod_remittance(settlement_id: int, body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_cod_remittance(settlement_id, body.amount, current_admin, db)
    db.commit()
    return {"status": "ok", "settlement_id": result.id, "cod_remittance_status": result.cod_remittance_status}


def admin_list_cod_remittance_receipts(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_cod_remittance_receipts(db, skip=skip, limit=limit, partner_id=partner_id, status=status)


def admin_verify_cod_remittance_receipt(receipt_id: int, body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_verify_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note if body else None)
    db.commit()
    return result


def admin_reject_cod_remittance_receipt(receipt_id: int, body, db: Session, current_admin: dict):
    from infrastructure.utils.auth import require_permission
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reject_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note or "")
    db.commit()
    return result


# ── Supplier controllers ─────────────────────────────────────────────────────

def supplier_financial_summary(db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    return ctrl.supplier_get_financial_summary(current_user["id"], db)


def supplier_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    return ctrl.supplier_list_settlements(current_user["id"], db, skip=skip, limit=limit, status=status)


def supplier_list_ledger(skip: int, limit: int, db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    return ctrl.supplier_list_ledger_entries(current_user["id"], db, skip=skip, limit=limit)


# ── Logistics controllers ────────────────────────────────────────────────────

def logistics_financial_summary(db: Session, current_user: dict):
    from domains.logistics.ports import get_logistics_partner_by_user_id
    partner = get_logistics_partner_by_user_id(db, int(current_user["id"]))
    if not partner:
        return {"error": "Logistics partner not found"}, 404
    return ctrl.logistics_get_financial_summary(partner.id, db)


def logistics_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):
    from domains.logistics.ports import get_logistics_partner_by_user_id
    partner = get_logistics_partner_by_user_id(db, int(current_user["id"]))
    if not partner:
        return []
    return ctrl.logistics_list_settlements(partner.id, db, skip=skip, limit=limit, status=status)


def logistics_list_ledger(skip: int, limit: int, db: Session, current_user: dict):
    from domains.logistics.ports import get_logistics_partner_by_user_id
    partner = get_logistics_partner_by_user_id(db, int(current_user["id"]))
    if not partner:
        return []
    return ctrl.logistics_list_ledger_entries(partner.id, db, skip=skip, limit=limit)


# ── Geography / commission controllers ──────────────────────────────────────

from domains.finance.services.ledger.general_ledger_service import (
    get_global_config, update_global_config, list_category_rates, update_category_rate,
    list_badge_tiers, update_badge_tier, list_ledger_entries, create_ledger_adjustment,
    preview_commission, list_all_supplier_commissions, get_supplier_commission,
    set_supplier_commission, delete_supplier_commission_override,
    get_product_commission_override, list_product_commission_overrides,
    set_product_commission_override, delete_product_commission_override,
)

from infrastructure.database.schemas import ListPage


def list_rates(country_code: str, current_user, db: Session, page: int, page_size: int):
    from infrastructure.utils.country_rls import get_country_or_404
    from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_category_rates(db, country_code, page, page_size)
    finally:
        clear_rls_context()


def create_rate(country_code: str, payload, current_user, db: Session):
    from infrastructure.utils.country_rls import get_country_or_404
    from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_category_rate(db, payload, country_code)
    finally:
        clear_rls_context()


def update_rate(country_code: str, rate_id: int, payload, current_user, db: Session):
    from infrastructure.utils.country_rls import get_country_or_404
    get_country_or_404(country_code.upper(), db)
    return update_category_rate(db, rate_id, country_code, payload)


def list_badge_tiers_route(country_code: str, current_user, db: Session, page: int, page_size: int):
    from infrastructure.utils.country_rls import get_country_or_404
    from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_badge_tiers(db, country_code, page, page_size)
    finally:
        clear_rls_context()


def create_badge_tier_route(country_code: str, payload, current_user, db: Session):
    from infrastructure.utils.country_rls import get_country_or_404
    from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_badge_tier(db, payload, country_code)
    finally:
        clear_rls_context()


def update_badge_tier_route(country_code: str, tier_id: int, payload, current_user, db: Session):
    from infrastructure.utils.country_rls import get_country_or_404
    get_country_or_404(country_code.upper(), db)
    return update_badge_tier(db, tier_id, country_code, payload)


# ── Commission / ledger wrappers (controller-shaped, moved from service) ─────

from domains.finance.services.ledger.general_ledger_service import (
    get_global_config as _get_global_config,
    update_global_config as _update_global_config,
    list_category_rates as _list_category_rates,
    update_category_rate as _update_category_rate,
    list_badge_tiers as _list_badge_tiers,
    update_badge_tier as _update_badge_tier,
    list_ledger_entries as _list_ledger_entries,
    create_ledger_adjustment,
    preview_commission,
    list_all_supplier_commissions,
    get_supplier_commission,
    set_supplier_commission,
    delete_supplier_commission_override,
    get_product_commission_override,
    list_product_commission_overrides,
    set_product_commission_override,
    delete_product_commission_override,
)


def get_global_config(db: Session, current_user: dict):
    return _get_global_config(db)


def update_global_config(body, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return _update_global_config(payload, current_user, db)


def list_category_rates(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return _list_category_rates(db, limit=page_size, offset=(page - 1) * page_size, search=search)


def update_category_rate(category_slug: str, body, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return _update_category_rate(category_slug, payload, current_user, db)


def list_badge_tiers(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return _list_badge_tiers(db, limit=page_size, offset=(page - 1) * page_size, search=search)


def update_badge_tier(badge_level: str, body, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return _update_badge_tier(badge_level, payload, current_user, db)


def list_ledger_entries(supplier_id: Optional[int], order_id: Optional[int], skip: int, limit: int, db: Session, current_user: dict):
    return _list_ledger_entries(db, supplier_id, order_id, skip, limit)


def adjust_ledger_entry(ledger_id: int, body, db: Session, current_user: dict):
    return create_ledger_adjustment(
        ledger_id=ledger_id,
        new_amount=body.new_amount,
        reason=body.reason,
        acting_user=current_user,
        db=db,
    )


def preview_commission(body, db: Session, current_user: dict):
    return preview_commission(
        supplier_id=body.supplier_id,
        order_value=body.order_value,
        category_slug=body.category_slug,
        db=db,
    )


def list_supplier_commissions(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return list_all_supplier_commissions(db, limit=page_size, offset=(page - 1) * page_size, search=search)


def get_supplier_commission(supplier_id: int, db: Session, current_user: dict):
    return get_supplier_commission(supplier_id, db)


def set_supplier_commission(supplier_id: int, body, db: Session, current_user: dict):
    return set_supplier_commission(
        supplier_id=supplier_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )


def delete_supplier_commission_override(supplier_id: int, db: Session, current_user: dict):
    return delete_supplier_commission_override(
        supplier_id=supplier_id,
        acting_user=current_user,
        db=db,
    )


def get_product_commission_override(product_id: int, db: Session, current_user: dict):
    result = get_product_commission_override(product_id, db)
    if result is None:
        return {"override": None, "message": "No override - using category/badge/default rate"}
    return result


def list_product_commission_overrides(search: Optional[str], supplier_id: Optional[int], limit: int, db: Session, current_user: dict):
    return list_product_commission_overrides(
        db,
        search=search,
        supplier_id=supplier_id,
        limit=limit,
    )


def set_product_commission_override(product_id: int, body, db: Session, current_user: dict):
    return set_product_commission_override(
        product_id=product_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )


def delete_product_commission_override(product_id: int, db: Session, current_user: dict):
    return delete_product_commission_override(
        product_id=product_id,
        acting_user=current_user,
        db=db,
    )


# ── FastAPI router (for registration by a future finance module) ──────────────

from fastapi import APIRouter, Depends, Query, Path, Body

router = APIRouter(prefix="/api/v1/finance/cash-management", tags=["finance", "cash-management"])
