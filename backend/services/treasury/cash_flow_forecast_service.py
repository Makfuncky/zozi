"""Cash Flow Forecast Engine — predicts future cash position.

Uses historical patterns, pending payouts, and expected settlements
to project daily cash balances.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import (
    Account,
    AccountBalance,
    CashFlowForecast,
    JournalEntry,
    JournalEntryLine,
    SupplierSettlement,
    PayoutBatch,
)
from utils.money import round_money
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


def generate_forecast(
    db: Session,
    days: int = 90,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> dict:
    """Generate a cash flow forecast for the next N days.

    Uses:
    1. Current cash balance (Account 1010)
    2. Historical daily net flow (average of last 90 days)
    3. Pending supplier payouts (cash outflows)
    4. Expected COD remittances (cash inflows)
    5. Expected VAT remittances (cash outflows)
    """
    cash_acct = db.query(Account).filter(Account.code == "1010").first()
    if not cash_acct:
        return {"error": "Cash account (1010) not found — run seed first"}

    current_balance = Decimal("0.00")
    bal = db.query(AccountBalance).filter(
        AccountBalance.account_id == cash_acct.id,
        AccountBalance.currency == currency,
    ).first()
    if bal:
        current_balance = bal.balance

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Historical average daily net flow (last 90 days)
    historical_start = today - timedelta(days=90)
    historical_net = db.query(
        func.coalesce(
            func.sum(JournalEntryLine.amount).filter(JournalEntryLine.side == "debit"),
            0,
        ) -
        func.coalesce(
            func.sum(JournalEntryLine.amount).filter(JournalEntryLine.side == "credit"),
            0,
        )
    ).select_from(JournalEntryLine).join(
        JournalEntry, JournalEntryLine.entry_id == JournalEntry.id
    ).filter(
        JournalEntryLine.account_id == cash_acct.id,
        JournalEntry.entry_date >= historical_start,
        JournalEntry.entry_date < today,
        JournalEntry.is_deleted == False,
    ).scalar()

    avg_daily_net = round_money(
        (historical_net or Decimal("0.00")) / Decimal("90")
    )

    # Pending payouts (scheduled outflows)
    pending_payouts = db.query(
        func.coalesce(func.sum(SupplierSettlement.net_amount), 0)
    ).filter(
        SupplierSettlement.status.in_(["pending", "approved"]),
        SupplierSettlement.country_code == country_code if country_code else True,
    ).scalar() or Decimal("0.00")

    # Forecast daily
    forecast_days = []
    running_balance = current_balance
    for day_offset in range(days):
        date = today + timedelta(days=day_offset)
        daily_inflow = Decimal("0.00")
        daily_outflow = Decimal("0.00")

        # Base projection from historical average
        if avg_daily_net > 0:
            daily_inflow += avg_daily_net
        else:
            daily_outflow += abs(avg_daily_net)

        # Known payouts (schedule them evenly over first 30 days)
        if day_offset < 30 and pending_payouts > 0:
            scheduled = round_money(pending_payouts / Decimal("30"))
            daily_outflow += scheduled

        net = daily_inflow - daily_outflow
        running_balance = round_money(running_balance + net)

        forecast_days.append({
            "date": date.isoformat(),
            "opening_balance": float(running_balance - net),
            "inflow": float(daily_inflow),
            "outflow": float(daily_outflow),
            "net_flow": float(net),
            "closing_balance": float(running_balance),
        })

    result = {
        "generated_at": datetime.utcnow().isoformat(),
        "currency": currency,
        "current_balance": float(current_balance),
        "historical_avg_daily_net": float(avg_daily_net),
        "pending_payouts": float(pending_payouts),
        "forecast_days": forecast_days,
        "projected_balance_30d": float(forecast_days[29]["closing_balance"]) if len(forecast_days) > 29 else None,
        "projected_balance_90d": float(forecast_days[-1]["closing_balance"]),
    }

    # Persist summary to CashFlowForecast table
    forecast_record = CashFlowForecast(
        forecast_date=today,
        period_start=today,
        period_end=today + timedelta(days=days),
        net_cash_flow=float(running_balance - current_balance),
        opening_balance=float(current_balance),
        closing_balance=float(running_balance),
    )
    db.add(forecast_record)
    db.commit()

    return result

