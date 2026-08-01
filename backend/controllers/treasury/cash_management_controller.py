"""
Cash Management Controller — API-level business logic for financial operations.

Wraps the cash_management_service with request validation, auth checks,
pagination, and response formatting for the router layer.
"""
import logging
import json
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, selectinload

from dependencies.db import SessionLocal
from utils.audit_log import AuditAction, audit_log
from models import (
    BadgeBillingRecord,
    BankTransaction,
    CommissionLedgerEntry,
    FinanceBankAccount,
    LogisticsCODRemittanceReceipt,
    LogisticsPartner,
    LogisticsSettlement,
    Order,
    OrderItem,
    OrderLogisticsAllocation,
    PaymentGatewayConnection,
    Product,
    RefundLedger,
    SupplierProfile,
    SupplierSettlement,
    TransactionLedger,
    User,
    VATRemittance,
)
from services.cash_management_service import (
    auto_reconcile_bank_transactions,
    create_refund_ledger_entry,
    flag_bank_transaction,
    get_finance_bank_settings,
    get_financial_summary,
    get_logistics_financial_summary,
    get_reconciliation_summary,
    get_supplier_financial_summary,
    import_bank_transactions,
    log_bank_transaction,
    process_logistics_payout_batch,
    process_supplier_payout_batch,
    reconcile_bank_transaction,
    reject_cod_remittance_receipt,
    record_cod_remittance,
    record_vat_remittance,
    resolve_bank_transaction_exception,
    deserialize_pricing_breakdown_json,
    effective_allocation_delivery_amounts,
    serialize_cod_remittance_receipt,
    list_vat_remittances,
    list_cod_remittance_receipts,
    upsert_finance_bank_settings,
    verify_cod_remittance_receipt,
)
from services.finance_transfer_service import execute_transfer_batch, get_default_transfer_provider, list_transfer_export_providers, test_configured_bank_api_connection
from utils.money import to_decimal
from utils.background_jobs import enqueue_job

logger = logging.getLogger(__name__)


def _model_columns_dict(instance: Any) -> dict[str, Any]:
    table = getattr(instance, "__table__", None)
    if table is None:
        return {}
    return {column.name: getattr(instance, column.name) for column in table.columns}


def _serialize_finance_bank_settings(record: FinanceBankAccount | None) -> dict[str, Any]:
    if record is None:
        return {
            "configured": False,
            "scope": "zozi_primary",
            "account_label": None,
            "beneficiary_name": None,
            "bank_name": None,
            "branch_name": None,
            "account_number": None,
            "iban": None,
            "swift_code": None,
            "routing_number": None,
            "currency": "AED",
            "support_email": None,
            "support_phone": None,
            "remittance_reference_prefix": None,
            "instructions": None,
            "is_active": True,
            "updated_by": None,
            "updated_at": None,
        }
    return {
        "configured": True,
        "id": record.id,
        "scope": record.scope,
        "account_label": record.account_label,
        "beneficiary_name": record.beneficiary_name,
        "bank_name": record.bank_name,
        "branch_name": record.branch_name,
        "account_number": record.account_number,
        "iban": record.iban,
        "swift_code": record.swift_code,
        "routing_number": record.routing_number,
        "currency": record.currency,
        "support_email": record.support_email,
        "support_phone": record.support_phone,
        "remittance_reference_prefix": record.remittance_reference_prefix,
        "instructions": record.instructions,
        "is_active": record.is_active,
        "updated_by": record.updated_by,
        "updated_at": record.updated_at,
    }


def _serialize_allocation(allocation: OrderLogisticsAllocation) -> dict[str, Any]:
    supplier = getattr(allocation, "supplier", None)
    effective_amounts = effective_allocation_delivery_amounts(allocation)
    return {
        "supplier_id": allocation.supplier_id,
        "supplier_name": getattr(supplier, "username", None) if supplier else None,
        "partner_id": allocation.partner_id,
        "partner_name": allocation.partner_name_snapshot,
        "partner_code": allocation.partner_code_snapshot,
        "service_area_id": allocation.service_area_id,
        "service_area_label": allocation.service_area_label_snapshot,
        "allocation_source": allocation.allocation_source,
        "destination_country": allocation.destination_country,
        "destination_city": allocation.destination_city,
        "shipping_amount": float(to_decimal(allocation.shipping_amount or 0)),
        "pickup_charge": float(to_decimal(allocation.pickup_charge or 0)),
        "dropoff_charge": float(to_decimal(allocation.dropoff_charge or 0)),
        "accepted_load_fit_label": allocation.accepted_vehicle_type,
        "accepted_load_fit_factor": float(to_decimal(allocation.accepted_vehicle_multiplier or 0)) if allocation.accepted_vehicle_multiplier is not None else None,
        "accepted_vehicle_type": allocation.accepted_vehicle_type,
        "accepted_vehicle_multiplier": float(to_decimal(allocation.accepted_vehicle_multiplier or 0)) if allocation.accepted_vehicle_multiplier is not None else None,
        "accepted_shipping_amount": float(to_decimal(allocation.accepted_shipping_amount or 0)) if allocation.accepted_shipping_amount is not None else None,
        "accepted_pickup_charge": float(to_decimal(allocation.accepted_pickup_charge or 0)) if allocation.accepted_pickup_charge is not None else None,
        "accepted_dropoff_charge": float(to_decimal(allocation.accepted_dropoff_charge or 0)) if allocation.accepted_dropoff_charge is not None else None,
        "effective_shipping_amount": float(effective_amounts["shipping_amount"]),
        "effective_pickup_charge": float(effective_amounts["pickup_charge"]),
        "effective_dropoff_charge": float(effective_amounts["dropoff_charge"]),
        "estimated_delivery_min": allocation.estimated_delivery_min,
        "estimated_delivery_max": allocation.estimated_delivery_max,
        "currency": allocation.currency,
        "pricing_breakdown": deserialize_pricing_breakdown_json(allocation.pricing_breakdown_json),
        "accepted_pricing_breakdown": deserialize_pricing_breakdown_json(allocation.accepted_pricing_breakdown_json),
    }


def _latest_refund_for_order(order_id: int, db: Session) -> RefundLedger | None:
    return (
        db.query(RefundLedger)
        .filter(RefundLedger.order_id == order_id)
        .order_by(desc(RefundLedger.created_at))
        .first()
    )


def _decorate_supplier_settlement(settlement: SupplierSettlement, db: Session) -> dict[str, Any]:
    ledger = settlement.ledger_entry or db.query(TransactionLedger).filter(TransactionLedger.id == settlement.ledger_id).first()
    allocation = (
        db.query(OrderLogisticsAllocation)
        .filter(
            OrderLogisticsAllocation.order_id == settlement.order_id,
            OrderLogisticsAllocation.supplier_id == settlement.supplier_id,
        )
        .order_by(desc(OrderLogisticsAllocation.id))
        .first()
    )
    refund = _latest_refund_for_order(settlement.order_id, db)

    # Resolve gateway info from the order
    order = db.query(Order).filter(Order.id == settlement.order_id).first()
    gateway_code: Optional[str] = None
    settlement_cycle: Optional[str] = None
    gateway_fee_deducted: Optional[float] = None
    if order:
        gateway_code = str(getattr(order, "payment_gateway_code", "") or "").strip() or None
        raw_fee = getattr(order, "payment_gateway_fee_amount", None)
        fee_passed = bool(getattr(order, "payment_gateway_fee_passed_to_customer", False))
        if gateway_code and raw_fee and not fee_passed:
            # calculate this supplier's proportional share of the gateway fee
            gross = float(settlement.gross_amount or 0)
            order_subtotal = float(getattr(order, "subtotal_amount", 0) or 0)
            if order_subtotal > 0 and gross > 0:
                gateway_fee_deducted = round(float(raw_fee) * (gross / order_subtotal), 4)
        if gateway_code:
            gw_record = db.query(PaymentGatewayConnection).filter(
                PaymentGatewayConnection.provider_code == gateway_code
            ).first()
            if gw_record:
                settlement_cycle = str(getattr(gw_record, "settlement_cycle", "") or "").strip() or None

    return {
        **_model_columns_dict(settlement),
        "payment_method": getattr(ledger, "payment_method", None),
        "vat_amount": getattr(ledger, "vat_amount", None),
        "delivery_total": getattr(ledger, "delivery_total", None),
        "delivery_pickup_charge": getattr(ledger, "delivery_pickup_charge", None),
        "delivery_dropoff_charge": getattr(ledger, "delivery_dropoff_charge", None),
        "destination_country": getattr(allocation, "destination_country", None),
        "destination_city": getattr(allocation, "destination_city", None),
        "partner_id": getattr(allocation, "partner_id", None),
        "partner_name": getattr(allocation, "partner_name_snapshot", None),
        "partner_code": getattr(allocation, "partner_code_snapshot", None),
        "service_area_label": getattr(allocation, "service_area_label_snapshot", None),
        "allocation_source": getattr(allocation, "allocation_source", None),
        "refund_status": getattr(refund, "status", None),
        "supplier_reversal_amount": getattr(refund, "supplier_reversal", None),
        "customer_refund_amount": getattr(refund, "customer_refund_amount", None),
        "gateway_code": gateway_code,
        "settlement_cycle": settlement_cycle,
        "gateway_fee_deducted": gateway_fee_deducted,
    }


def _decorate_logistics_settlement(settlement: LogisticsSettlement, db: Session) -> dict[str, Any]:
    ledger = settlement.ledger_entry or db.query(TransactionLedger).filter(TransactionLedger.id == settlement.ledger_id).first()
    allocations = (
        db.query(OrderLogisticsAllocation)
        .filter(
            OrderLogisticsAllocation.order_id == settlement.order_id,
            OrderLogisticsAllocation.partner_id == settlement.partner_id,
        )
        .order_by(OrderLogisticsAllocation.supplier_id.asc())
        .all()
    )
    refund = _latest_refund_for_order(settlement.order_id, db)
    lead_allocation = allocations[0] if allocations else None
    return {
        **_model_columns_dict(settlement),
        "payment_method": getattr(ledger, "payment_method", None),
        "destination_country": getattr(lead_allocation, "destination_country", None),
        "destination_city": getattr(lead_allocation, "destination_city", None),
        "partner_name": getattr(lead_allocation, "partner_name_snapshot", None),
        "partner_code": getattr(lead_allocation, "partner_code_snapshot", None),
        "service_area_label": getattr(lead_allocation, "service_area_label_snapshot", None),
        "allocation_source": getattr(lead_allocation, "allocation_source", None),
        "refund_status": getattr(refund, "status", None),
        "logistics_reversal_amount": getattr(refund, "logistics_reversal", None),
        "customer_refund_amount": getattr(refund, "customer_refund_amount", None),
        "allocations": [_serialize_allocation(allocation) for allocation in allocations],
    }


def _decorate_refund(refund: RefundLedger, db: Session) -> dict[str, Any]:
    order = getattr(refund, "order", None)
    txn = db.query(BankTransaction).filter(BankTransaction.id == refund.bank_transaction_id).first() if refund.bank_transaction_id else None
    allocations = (
        db.query(OrderLogisticsAllocation)
        .filter(OrderLogisticsAllocation.order_id == refund.order_id)
        .order_by(OrderLogisticsAllocation.supplier_id.asc())
        .all()
    )
    return {
        **_model_columns_dict(refund),
        "payment_method": getattr(order, "payment_method", None),
        "order_status": getattr(order, "status", None),
        "bank_transaction_ref": getattr(txn, "transaction_ref", None),
        "allocations": [_serialize_allocation(allocation) for allocation in allocations],
    }


def _commission_metadata_for_entry(entry: TransactionLedger, db: Session) -> dict[str, Optional[str]]:
    rows = (
        db.query(
            CommissionLedgerEntry.category_slug,
            CommissionLedgerEntry.badge_level,
            CommissionLedgerEntry.calculation_method,
        )
        .filter(
            CommissionLedgerEntry.order_id == entry.order_id,
            CommissionLedgerEntry.supplier_id == entry.supplier_id,
        )
        .all()
    )

    def _collapse(values: list[object]) -> Optional[str]:
        normalized = sorted({str(value) for value in values if value not in (None, "")})
        if not normalized:
            return None
        return normalized[0] if len(normalized) == 1 else "mixed"

    return {
        "category_slug": _collapse([row[0] for row in rows]),
        "badge_level": _collapse([row[1] for row in rows]),
        "calculation_method": _collapse([row[2] for row in rows]),
    }


def _serialize_finance_order_summary(order: Order | None) -> dict[str, Any] | None:
    if order is None:
        return None

    customer = getattr(order, "user", None)
    items_payload: list[dict[str, Any]] = []
    for item in getattr(order, "items", []) or []:
        product = getattr(item, "product", None)
        items_payload.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": float(to_decimal(item.price or 0)) if getattr(item, "price", None) is not None else None,
            "selected_size": item.selected_size,
            "selected_color": item.selected_color,
            "product": {
                "id": product.id,
                "name": product.name,
                "supplier_id": product.supplier_id,
            } if product is not None else None,
        })

    return {
        "id": order.id,
        "user_id": order.user_id,
        "customer_username": getattr(customer, "username", None),
        "payment_status": "paid" if getattr(order, "paid_at", None) else "unpaid",
        "payment_method": order.payment_method,
        "status": order.status,
        "created_at": order.created_at,
        "total_amount": float(to_decimal(order.total_amount or 0)) if getattr(order, "total_amount", None) is not None else None,
        "shipping_address": order.shipping_address,
        "items": items_payload,
    }


def _serialize_finance_supplier_summary(user: User | None, profile: SupplierProfile | None) -> dict[str, Any] | None:
    if user is None and profile is None:
        return None

    supplier_id = user.id if user is not None else profile.user_id
    return {
        "id": supplier_id,
        "username": getattr(user, "username", None),
        "profile": {
            "business_name": getattr(profile, "business_name", None),
            "badge_level": getattr(profile, "badge_level", None),
            "verification_status": getattr(profile, "verification_status", None),
        } if profile is not None else None,
    }


def _decorate_ledger_entry(
    entry: TransactionLedger,
    db: Session,
    *,
    order_map: dict[int, Order] | None = None,
    supplier_user_map: dict[int, User] | None = None,
    supplier_profile_map: dict[int, SupplierProfile] | None = None,
) -> dict[str, Any]:
    metadata = _commission_metadata_for_entry(entry, db)
    order = order_map.get(entry.order_id) if order_map is not None else getattr(entry, "order", None)
    supplier_user = supplier_user_map.get(entry.supplier_id) if supplier_user_map is not None else getattr(entry, "supplier", None)
    supplier_profile = supplier_profile_map.get(entry.supplier_id) if supplier_profile_map is not None else None
    return {
        "id": entry.id,
        "order_id": entry.order_id,
        "supplier_id": entry.supplier_id,
        "logistics_partner_id": entry.logistics_partner_id,
        "category_slug": metadata["category_slug"],
        "badge_level": metadata["badge_level"],
        "calculation_method": metadata["calculation_method"],
        "payment_method": entry.payment_method,
        "product_subtotal": entry.product_subtotal,
        "discount_amount": entry.discount_amount,
        "delivery_pickup_charge": entry.delivery_pickup_charge,
        "delivery_dropoff_charge": entry.delivery_dropoff_charge,
        "delivery_total": entry.delivery_total,
        "vat_amount": entry.vat_amount,
        "zozi_commission_rate": entry.zozi_commission_rate,
        "zozi_commission": entry.zozi_commission,
        "net_supplier_amount": entry.net_supplier_amount,
        "net_logistics_amount": entry.net_logistics_amount,
        "net_zozi_amount": entry.net_zozi_amount,
        "cod_collected_amount": entry.cod_collected_amount,
        "cod_remittance_due": entry.cod_remittance_due,
        "settlement_status": entry.settlement_status,
        "currency": entry.currency,
        "created_at": entry.created_at,
        "order": _serialize_finance_order_summary(order),
        "supplier": _serialize_finance_supplier_summary(supplier_user, supplier_profile),
    }


def _decorate_badge_billing(record: BadgeBillingRecord) -> dict[str, Any]:
    supplier = getattr(record, "supplier", None)
    txn = getattr(record, "bank_transaction", None)
    return {
        "id": record.id,
        "billing_reference": record.billing_reference,
        "supplier_id": record.supplier_id,
        "supplier_name": getattr(supplier, "username", None),
        "badge_level": record.badge_level,
        "charge_type": record.charge_type,
        "charge_source": record.charge_source,
        "status": record.status,
        "amount": record.amount,
        "currency": record.currency,
        "period_start": record.period_start,
        "period_end": record.period_end,
        "due_at": record.due_at,
        "billed_at": record.billed_at,
        "paid_at": record.paid_at,
        "payment_method": record.payment_method,
        "bank_transaction_id": record.bank_transaction_id,
        "transaction_ref": getattr(txn, "transaction_ref", None),
        "notes": record.notes,
        "created_by": record.created_by,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


# ── Admin: Financial Dashboard ────────────────────────────────────────────────

def admin_get_financial_summary(db: Session) -> dict:
    """Return aggregate financial dashboard metrics."""
    return get_financial_summary(db)


def admin_get_reconciliation_summary(db: Session) -> dict:
    """Return bank reconciliation workload and exception metrics."""
    return get_reconciliation_summary(db)


def admin_list_ledger_entries(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    order_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    settlement_status: Optional[str] = None,
    payment_method: Optional[str] = None,
    category_slug: Optional[str] = None,
    badge_level: Optional[str] = None,
    calculation_method: Optional[str] = None,
) -> list[dict[str, Any]]:
    """List transaction ledger entries with filters."""
    q = db.query(TransactionLedger)
    if order_id:
        q = q.filter(TransactionLedger.order_id == order_id)
    if supplier_id:
        q = q.filter(TransactionLedger.supplier_id == supplier_id)
    if settlement_status:
        q = q.filter(TransactionLedger.settlement_status == settlement_status)
    if payment_method:
        q = q.filter(TransactionLedger.payment_method == payment_method)

    if category_slug or badge_level or calculation_method:
        commission_pairs = db.query(
            CommissionLedgerEntry.order_id.label("order_id"),
            CommissionLedgerEntry.supplier_id.label("supplier_id"),
        )
        if category_slug:
            commission_pairs = commission_pairs.filter(CommissionLedgerEntry.category_slug == category_slug)
        if badge_level:
            commission_pairs = commission_pairs.filter(CommissionLedgerEntry.badge_level == badge_level)
        if calculation_method:
            commission_pairs = commission_pairs.filter(CommissionLedgerEntry.calculation_method == calculation_method)
        commission_pairs = commission_pairs.distinct().subquery()
        q = q.join(
            commission_pairs,
            and_(
                TransactionLedger.order_id == commission_pairs.c.order_id,
                TransactionLedger.supplier_id == commission_pairs.c.supplier_id,
            ),
        )

    entries = q.order_by(desc(TransactionLedger.created_at)).offset(skip).limit(limit).all()
    if not entries:
        return []

    order_ids = sorted({int(entry.order_id) for entry in entries if entry.order_id is not None})
    supplier_ids = sorted({int(entry.supplier_id) for entry in entries if entry.supplier_id is not None})

    order_map = {
        int(order.id): order
        for order in (
            db.query(Order)
            .options(
                selectinload(Order.user),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .filter(Order.id.in_(order_ids))
            .all()
        )
    }
    supplier_user_map = {
        int(user.id): user
        for user in db.query(User).filter(User.id.in_(supplier_ids)).all()
    }
    supplier_profile_map = {
        int(profile.user_id): profile
        for profile in db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(supplier_ids)).all()
    }

    return [
        _decorate_ledger_entry(
            entry,
            db,
            order_map=order_map,
            supplier_user_map=supplier_user_map,
            supplier_profile_map=supplier_profile_map,
        )
        for entry in entries
    ]


def admin_list_badge_billing_records(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    badge_level: Optional[str] = None,
    charge_type: Optional[str] = None,
) -> list[dict[str, Any]]:
    q = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.supplier), selectinload(BadgeBillingRecord.bank_transaction))
    )
    if supplier_id:
        q = q.filter(BadgeBillingRecord.supplier_id == supplier_id)
    if status:
        q = q.filter(BadgeBillingRecord.status == status)
    if badge_level:
        q = q.filter(BadgeBillingRecord.badge_level == badge_level)
    if charge_type:
        q = q.filter(BadgeBillingRecord.charge_type == charge_type)
    rows = q.order_by(desc(BadgeBillingRecord.created_at)).offset(skip).limit(limit).all()
    return [_decorate_badge_billing(row) for row in rows]


def admin_record_badge_billing_payment(
    billing_id: int,
    payment_method: str,
    current_admin: dict,
    db: Session,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    import controllers.supplier_controller as supplier_ctrl

    return supplier_ctrl.record_badge_billing_payment(
        billing_id=billing_id,
        payment_method=payment_method,
        current_user=current_admin,
        db=db,
        transaction_ref=transaction_ref,
        notes=notes,
    )


def admin_list_supplier_settlements(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    """List supplier settlements with filters."""
    q = db.query(SupplierSettlement)
    if supplier_id:
        q = q.filter(SupplierSettlement.supplier_id == supplier_id)
    if status:
        q = q.filter(SupplierSettlement.status == status)
    settlements = q.order_by(desc(SupplierSettlement.created_at)).offset(skip).limit(limit).all()
    return [_decorate_supplier_settlement(settlement, db) for settlement in settlements]


def admin_list_logistics_settlements(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    partner_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[LogisticsSettlement]:
    """List logistics settlements with filters."""
    q = db.query(LogisticsSettlement)
    if partner_id:
        q = q.filter(LogisticsSettlement.partner_id == partner_id)
    if status:
        q = q.filter(LogisticsSettlement.status == status)
    settlements = q.order_by(desc(LogisticsSettlement.created_at)).offset(skip).limit(limit).all()
    return [_decorate_logistics_settlement(settlement, db) for settlement in settlements]


def admin_list_bank_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    source: Optional[str] = None,
    category: Optional[str] = None,
    reconciled: Optional[bool] = None,
    flagged: Optional[bool] = None,
) -> list[BankTransaction]:
    """List bank transactions for reconciliation."""
    q = db.query(BankTransaction)
    if source:
        q = q.filter(BankTransaction.source == source)
    if category:
        q = q.filter(BankTransaction.category == category)
    if reconciled is not None:
        q = q.filter(BankTransaction.reconciled == reconciled)
    if flagged is not None:
        q = q.filter(BankTransaction.flagged == flagged)
    return q.order_by(desc(BankTransaction.transaction_date)).offset(skip).limit(limit).all()


def admin_list_refunds(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
) -> list[RefundLedger]:
    """List refund ledger entries."""
    q = db.query(RefundLedger)
    if status:
        q = q.filter(RefundLedger.status == status)
    refunds = q.order_by(desc(RefundLedger.created_at)).offset(skip).limit(limit).all()
    return [_decorate_refund(refund, db) for refund in refunds]


def admin_list_vat_remittance_records(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[VATRemittance]:
    return list_vat_remittances(db, skip=skip, limit=limit)


def admin_get_finance_bank_settings(db: Session) -> dict[str, Any]:
    return _serialize_finance_bank_settings(get_finance_bank_settings(db))


def admin_upsert_finance_bank_settings(data: dict, admin_user: dict, db: Session) -> dict[str, Any]:
    record = upsert_finance_bank_settings(data=data, admin_id=admin_user.get("id"), db=db)
    return _serialize_finance_bank_settings(record)


def admin_record_vat_remittance(data: dict, admin_user: dict, db: Session) -> VATRemittance:
    return record_vat_remittance(
        period_start=data["period_start"],
        period_end=data["period_end"],
        amount_remitted=to_decimal(data["amount_remitted"]),
        admin_id=admin_user.get("id"),
        db=db,
        notes=data.get("notes"),
        transaction_ref=data.get("transaction_ref"),
        remitted_at=data.get("remitted_at"),
    )


def admin_reconcile_transaction(txn_id: int, admin_user: dict, db: Session) -> BankTransaction:
    """Mark a bank transaction as reconciled."""
    try:
        return reconcile_bank_transaction(txn_id, admin_user["id"], db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def admin_flag_transaction(txn_id: int, reason: str, db: Session) -> BankTransaction:
    """Flag a bank transaction for manual review."""
    try:
        return flag_bank_transaction(txn_id, reason, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def admin_create_bank_transaction(data: dict, db: Session) -> BankTransaction:
    """Manually create a bank transaction entry."""
    return log_bank_transaction(
        source=data["source"],
        transaction_type=data["transaction_type"],
        category=data["category"],
        amount=to_decimal(data["amount"]),
        db=db,
        currency=data.get("currency", "OMR"),
        order_id=data.get("linked_order_id"),
        supplier_id=data.get("linked_supplier_id"),
        logistics_id=data.get("linked_logistics_id"),
        payout_id=data.get("linked_payout_id"),
        refund_id=data.get("linked_refund_id"),
        description=data.get("description"),
        transaction_ref=data.get("transaction_ref"),
        transaction_date=data.get("transaction_date"),
    )


def admin_import_bank_transactions(
    items: list[dict],
    admin_user: dict,
    db: Session,
    *,
    auto_reconcile: bool = False,
) -> dict:
    return import_bank_transactions(
        items,
        db,
        admin_id=admin_user.get("id"),
        auto_reconcile=auto_reconcile,
    )


def admin_trigger_supplier_payouts(db: Session, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Trigger batch payout processing for eligible supplier settlements."""
    return process_supplier_payout_batch(db, settlement_ids=settlement_ids)


def admin_trigger_logistics_payouts(db: Session, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Trigger batch payout processing for eligible logistics settlements."""
    return process_logistics_payout_batch(db, settlement_ids=settlement_ids)


def admin_record_cod_remittance(settlement_id: int, amount: float, admin_user: dict, db: Session):
    """Record COD cash remittance from logistics partner."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Remittance amount must be positive")
    try:
        return record_cod_remittance(settlement_id, amount, admin_user["id"], db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def admin_list_cod_remittance_receipts(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    partner_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    receipts = list_cod_remittance_receipts(db, partner_id=partner_id, status=status, skip=skip, limit=limit)
    return [serialize_cod_remittance_receipt(receipt, db) for receipt in receipts]


def admin_verify_cod_remittance_receipt(receipt_id: int, admin_user: dict, db: Session, note: Optional[str] = None) -> dict[str, Any]:
    try:
        receipt = verify_cod_remittance_receipt(receipt_id, admin_user["id"], db, review_note=note)
        return serialize_cod_remittance_receipt(receipt, db)
    except ValueError as e:
        detail = str(e)
        status_code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail)


def admin_reject_cod_remittance_receipt(receipt_id: int, admin_user: dict, db: Session, note: str) -> dict[str, Any]:
    try:
        receipt = reject_cod_remittance_receipt(receipt_id, admin_user["id"], db, review_note=note)
        return serialize_cod_remittance_receipt(receipt, db)
    except ValueError as e:
        detail = str(e)
        status_code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail)


def admin_auto_reconcile_transactions(
    admin_user: dict,
    db: Session,
    *,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    return auto_reconcile_bank_transactions(
        admin_user["id"],
        db,
        limit=limit,
        source=source,
        category=category,
    )


def admin_list_transfer_providers(db: Session) -> dict[str, Any]:
    return {
        "default_provider": get_default_transfer_provider(),
        "providers": list_transfer_export_providers(db),
    }


def admin_test_finance_bank_connection(db: Session) -> dict[str, Any]:
    return test_configured_bank_api_connection(db)


def _normalize_dispatch_kind(kind: str) -> tuple[str, str]:
    normalized_kind = kind.strip().lower()
    if normalized_kind not in {"supplier", "logistics"}:
        raise HTTPException(status_code=422, detail="kind must be 'supplier' or 'logistics'")
    export_type = "supplier-payout-transfers" if normalized_kind == "supplier" else "logistics-payout-transfers"
    return normalized_kind, export_type


def _dispatch_transfer_batch_with_audit(
    kind: str,
    admin_user: dict,
    db: Session,
    *,
    provider: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_kind, export_type = _normalize_dispatch_kind(kind)
    result = execute_transfer_batch(
        export_type,
        db=db,
        provider=provider,
        dry_run=dry_run,
    )
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_user.get("id"),
        username=admin_user.get("username"),
        user_role=admin_user.get("role"),
        resource_type=f"{normalized_kind}_payout_dispatch",
        details={
            "provider": result.get("provider"),
            "status": result.get("status"),
            "dry_run": dry_run,
            "dispatchable_count": result.get("dispatchable_count"),
            "skipped_count": result.get("skipped_count"),
            "batch_reference": result.get("batch_reference"),
        },
    )
    return result


def admin_dispatch_transfer_batch(
    kind: str,
    admin_user: dict,
    db: Session,
    *,
    provider: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    return _dispatch_transfer_batch_with_audit(
        kind,
        admin_user,
        db,
        provider=provider,
        dry_run=dry_run,
    )


def admin_queue_dispatch_transfer_batch(
    kind: str,
    admin_user: dict,
    *,
    provider: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    normalized_kind, _export_type = _normalize_dispatch_kind(kind)
    effective_provider = (provider or get_default_transfer_provider()).strip().lower() or get_default_transfer_provider()

    def _runner() -> dict[str, Any]:
        session = SessionLocal()
        try:
            result = _dispatch_transfer_batch_with_audit(
                normalized_kind,
                admin_user,
                session,
                provider=effective_provider,
                dry_run=dry_run,
            )
            session.commit()
            return result
        except Exception as exc:
            session.rollback()
            raise
        finally:
            session.close()

    return enqueue_job(
        kind="finance-payout-dispatch",
        owner_user_id=admin_user.get("id"),
        owner_role=admin_user.get("role"),
        func=_runner,
        metadata={
            "payout_kind": normalized_kind,
            "provider": effective_provider,
            "dry_run": dry_run,
        },
    )


def admin_resolve_transaction_exception(
    txn_id: int,
    data: dict,
    admin_user: dict,
    db: Session,
) -> BankTransaction:
    try:
        return resolve_bank_transaction_exception(
            txn_id,
            db,
            admin_id=admin_user.get("id"),
            order_id=data.get("linked_order_id"),
            supplier_id=data.get("linked_supplier_id"),
            logistics_id=data.get("linked_logistics_id"),
            payout_id=data.get("linked_payout_id"),
            refund_id=data.get("linked_refund_id"),
            resolution_note=data.get("resolution_note"),
            mark_reconciled=data.get("mark_reconciled", True),
            clear_flag=data.get("clear_flag", True),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Supplier: Financial Dashboard ─────────────────────────────────────────────

def supplier_get_financial_summary(supplier_id: int, db: Session) -> dict:
    """Return financial summary for a supplier."""
    return get_supplier_financial_summary(supplier_id, db)


def supplier_list_settlements(
    supplier_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
) -> list[SupplierSettlement]:
    """List settlements for a specific supplier."""
    q = db.query(SupplierSettlement).filter(SupplierSettlement.supplier_id == supplier_id)
    if status:
        q = q.filter(SupplierSettlement.status == status)
    settlements = q.order_by(desc(SupplierSettlement.created_at)).offset(skip).limit(limit).all()
    return [_decorate_supplier_settlement(settlement, db) for settlement in settlements]


def supplier_list_ledger_entries(
    supplier_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[TransactionLedger]:
    """List ledger entries for a specific supplier."""
    return (
        db.query(TransactionLedger)
        .filter(TransactionLedger.supplier_id == supplier_id)
        .order_by(desc(TransactionLedger.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Logistics Partner: Financial Dashboard ────────────────────────────────────

def logistics_get_financial_summary(partner_id: int, db: Session) -> dict:
    """Return financial summary for a logistics partner."""
    return get_logistics_financial_summary(partner_id, db)


def logistics_list_settlements(
    partner_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
) -> list[LogisticsSettlement]:
    """List settlements for a specific logistics partner."""
    q = db.query(LogisticsSettlement).filter(LogisticsSettlement.partner_id == partner_id)
    if status:
        q = q.filter(LogisticsSettlement.status == status)
    settlements = q.order_by(desc(LogisticsSettlement.created_at)).offset(skip).limit(limit).all()
    return [_decorate_logistics_settlement(settlement, db) for settlement in settlements]


def logistics_list_ledger_entries(
    partner_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[TransactionLedger]:
    """List ledger entries for a specific logistics partner."""
    return (
        db.query(TransactionLedger)
        .filter(TransactionLedger.logistics_partner_id == partner_id)
        .order_by(desc(TransactionLedger.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


