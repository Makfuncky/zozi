from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models import (
    GatewaySettlementSchedule,
    Order,
    BankStatementLine,
    PaymentGatewayConnection,
    FinanceAutomationLog,
    FinanceAuditLog,
)
from db.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

GATEWAY_FEE_RATES = {
    "tap": Decimal("0.025"),
    "stripe": Decimal("0.029"),
    "thawani": Decimal("0.020"),
    "omannet": Decimal("0.015"),
    "mada": Decimal("0.015"),
}


def _get_gateway_name(db: Session, gateway_id: int) -> str:
    gw = db.query(PaymentGatewayConnection).get(gateway_id)
    return gw.name if gw else "unknown"


def _calculate_gateway_fee(gateway_id: int, gross_amount: Decimal, db: Session) -> Decimal:
    gw = db.query(PaymentGatewayConnection).get(gateway_id)
    gw_name = (gw.name or "tap") if gw else "tap"
    rate = GATEWAY_FEE_RATES.get(gw_name.lower(), Decimal("0.025"))
    return (gross_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def match_gateway_settlement(
    db: Session,
    settlement_id: int,
    country_code: str = None,
) -> dict:
    settlement = db.query(GatewaySettlementSchedule).get(settlement_id)
    if not settlement:
        raise ValueError(f"Settlement #{settlement_id} not found")

    if settlement.status == "reconciled":
        return {"status": "already_reconciled", "settlement_id": settlement_id}

    gateway_name = _get_gateway_name(db, settlement.gateway_id)
    matching_orders = _find_orders_for_settlement(db, settlement)
    expected_gross = sum(Decimal(str(o.total or 0)) for o in matching_orders)
    expected_fee = _calculate_gateway_fee(settlement.gateway_id, expected_gross, db)
    expected_net = expected_gross - expected_fee

    gateway_amount = settlement.amount or Decimal("0")
    gateway_fee = settlement.gateway_fee or expected_fee
    gateway_net = settlement.net_amount or (gateway_amount - gateway_fee)

    amount_diff = abs(gateway_amount - expected_gross)
    fee_diff = abs(gateway_fee - expected_fee)

    if amount_diff <= Decimal("0.01") and fee_diff <= Decimal("0.01"):
        result = _auto_post_gateway_settlement(
            db, settlement, matching_orders, gateway_amount, gateway_fee, gateway_net,
            settlement.country_code, gateway_name,
        )
        settlement.status = "reconciled"
        db.commit()
        return {
            "status": "reconciled",
            "settlement_id": settlement_id,
            "journal_entry_id": result.get("journal_entry_id"),
            "gateway_amount": float(gateway_amount),
            "gateway_fee": float(gateway_fee),
            "net_deposited": float(gateway_net),
            "orders_matched": len(matching_orders),
        }
    else:
        settlement.status = "exception"
        db.commit()
        return {
            "status": "exception",
            "settlement_id": settlement_id,
            "expected_gross": float(expected_gross),
            "gateway_amount": float(gateway_amount),
            "difference": float(amount_diff),
            "fee_difference": float(fee_diff),
        }


def _find_orders_for_settlement(db: Session, settlement: GatewaySettlementSchedule):
    gateway = db.query(PaymentGatewayConnection).get(settlement.gateway_id)
    settlement_days = 2
    if gateway and gateway.settlement_cycle == "daily":
        settlement_days = 1

    window_start = settlement.settlement_date - timedelta(days=settlement_days + 1)
    window_end = settlement.settlement_date

    return db.query(Order).filter(
        Order.payment_method.in_(["card", "online"]),
        Order.status.in_(["paid", "delivered", "completed"]),
        Order.created_at >= window_start,
        Order.created_at <= window_end,
        Order.country_code == settlement.country_code,
    ).all()


def _auto_post_gateway_settlement(
    db: Session, settlement, orders, gross_amount, fee, net_amount,
    country_code, gateway_name,
) -> dict:
    cc = country_code or settlement.country_code
    lines = [
        JournalLineInput(account_code="1010", side="debit", amount=net_amount,
                         description=f"Gateway settlement net deposit - {gateway_name}"),
        JournalLineInput(account_code="5010", side="debit", amount=fee,
                         description=f"Gateway fee - {gateway_name} ({fee/gross_amount*100:.1f}%)"),
        JournalLineInput(account_code="1020", side="credit", amount=gross_amount,
                         description=f"Gateway clearing - settlement #{settlement.id}"),
    ]
    entry_data = JournalEntryCreate(
        entry_date=settlement.settlement_date or _utcnow(),
        reference_type="gateway_settlement",
        reference_id=settlement.id,
        reference_number=f"GS-{settlement.id:06d}",
        description=f"Gateway settlement - {gateway_name} - {gross_amount}",
        currency=settlement.currency or "OMR",
        country_code=cc,
        lines=lines,
    )
    result = gl.create_journal_entry(db, entry_data)
    return {"journal_entry_id": result.id, "status": "posted"}


def reconcile_cod_deposit(
    db: Session,
    order_id: int,
    deposited_amount: Decimal,
    country_code: str = None,
) -> dict:
    order = db.query(Order).get(order_id)
    if not order:
        raise ValueError(f"Order #{order_id} not found")
    if order.payment_method != "cod":
        raise ValueError(f"Order #{order_id} is not COD")

    expected = Decimal(str(order.total or 0))
    deposited = Decimal(str(deposited_amount))

    if deposited == expected:
        entry_data = JournalEntryCreate(
            entry_date=_utcnow(),
            reference_type="cod_reconciliation",
            reference_id=order.id,
            reference_number=f"COD-{order.id:06d}",
            description=f"COD deposit reconciled - Order #{order.id}",
            currency=order.currency or "OMR",
            country_code=country_code or order.country_code,
            lines=[
                JournalLineInput(account_code="1010", side="debit", amount=deposited,
                                 description=f"COD cash received - Order #{order.id}"),
                JournalLineInput(account_code="1030", side="credit", amount=deposited,
                                 description=f"COD receivable cleared - Order #{order.id}"),
            ],
        )
        result = gl.create_journal_entry(db, entry_data)
        _log_reconciliation(db, "cod_match", order_id, {
            "expected": float(expected), "deposited": float(deposited),
            "journal_entry_id": result.id,
        }, country_code)
        return {"status": "reconciled", "order_id": order_id,
                "expected": float(expected), "deposited": float(deposited),
                "journal_entry_id": result.id}
    else:
        variance = deposited - expected
        _log_reconciliation(db, "cod_exception", order_id, {
            "expected": float(expected), "deposited": float(deposited),
            "variance": float(variance),
        }, country_code)
        return {"status": "exception", "order_id": order_id,
                "expected": float(expected), "deposited": float(deposited),
                "variance": float(variance)}


def run_gateway_3way_reconciliation(db: Session, country_code: str = None) -> dict:
    results = {"processed": 0, "reconciled": 0, "exceptions": 0, "items": []}

    q = db.query(GatewaySettlementSchedule).filter(
        GatewaySettlementSchedule.status.in_(["pending", "captured"]),
        GatewaySettlementSchedule.status != "reconciled",
    )
    if country_code:
        q = q.filter(GatewaySettlementSchedule.country_code == country_code)

    for settlement in q.all():
        results["processed"] += 1
        try:
            result = match_gateway_settlement(db, settlement.id, country_code)
            if result["status"] == "reconciled":
                results["reconciled"] += 1
            else:
                results["exceptions"] += 1
            results["items"].append(result)
        except Exception as e:
            logger.warning("Gateway reconciliation failed for #%s: %s", settlement.id, e)
            results["exceptions"] += 1
            results["items"].append({"status": "error", "settlement_id": settlement.id,
                                      "error": str(e)})

    _log_reconciliation(db, "gateway_3way_batch", 0, results, country_code)
    return results


def reconcile_all_cod_deposits(db: Session, country_code: str = None) -> dict:
    results = {"processed": 0, "reconciled": 0, "exceptions": 0}

    orders = db.query(Order).filter(
        Order.payment_method == "cod",
        Order.status == "delivered",
        Order.paid_at.is_(None),
    )
    if country_code:
        orders = orders.filter(Order.country_code == country_code)

    results["processed"] = orders.count()

    for order in orders.all():
        try:
            expected = Decimal(str(order.total or 0))
            entry_data = JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="cod_batch_reconciliation",
                reference_id=order.id,
                reference_number=f"COD-REC-{order.id:06d}",
                description=f"COD batch reconciliation - Order #{order.id}",
                currency=order.currency or "OMR",
                country_code=country_code or order.country_code,
                lines=[
                    JournalLineInput(account_code="1010", side="debit", amount=expected,
                                     description=f"COD cash received - Order #{order.id}"),
                    JournalLineInput(account_code="1030", side="credit", amount=expected,
                                     description=f"COD receivable cleared - Order #{order.id}"),
                ],
            )
            gl.create_journal_entry(db, entry_data)
            results["reconciled"] += 1
        except Exception as e:
            logger.warning("COD reconciliation failed for order %s: %s", order.id, e)
            results["exceptions"] += 1

    db.commit()
    return results


def _log_reconciliation(db: Session, kind: str, entity_id: int, detail: dict,
                         country_code: str = None):
    try:
        db.add(FinanceAutomationLog(kind=kind, records_processed=1,
                                     records_changed=1, detail={**detail, "entity_id": entity_id},
                                     country_code=country_code))
        db.add(FinanceAuditLog(action="reconciliation", entity_type="gateway_settlement",
                                entity_id=entity_id, detail=detail, country_code=country_code))
        db.commit()
    except Exception as e:
        logger.warning("Reconciliation log failed: %s", e)
        db.rollback()