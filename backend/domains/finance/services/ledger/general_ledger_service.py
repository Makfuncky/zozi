from __future__ import annotations
import cachetools
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Protocol
from uuid import uuid4
from providers.finance import bank_api
from typing import Any
from sqlalchemy.orm import Session
from infrastructure.utils.config import settings
from kernel.money import round_money, to_decimal
import logging
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
# Product model imported lazily to avoid cross-domain import (Law 3 compliance)
from domains.finance.models.erp import LandedCostAllocation
from domains.finance.models.erp import CustomsEntry
from domains.finance.models.erp import ImportCostTemplate
from domains.logistics.models.erp import Warehouse
from domains.finance.models.finance import Vendor
from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountGroup
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.logistics.models.erp import ImportShipment
from domains.logistics.models.erp import ImportShipmentLine
from domains.logistics.models.erp import PurchaseOrder
from domains.logistics.models.erp import PurchaseOrderLine
from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput
# Removed circular self-import
from infrastructure.utils.datetime_utils import utcnow as _utcnow
from infrastructure.utils.pagination import keyset_offset_window
from datetime import datetime
from typing import Optional, List


from domains.finance.models.commission import CommissionLedgerEntry
from domains.finance.models.finance import TransactionLedger
from domains.finance.models.finance import RefundLedger
from domains.finance.models.finance import VATRemittance
from domains.finance.models.finance import TreasuryAccount
from domains.finance.models.payments import Payout
from infrastructure.database.schemas import (
    AccountBalanceOut,
    AccountOut,
    JournalEntryCreate,
    JournalEntryLineOut,
    JournalEntryOut,
    JournalLineInput,
    TrialBalanceOut,
)
from infrastructure.utils.datetime_utils import utcnow
from kernel.money import round_money


# ── Chart of Accounts ─────────────────────────────────────────────────────


def seed_chart_of_accounts(db: Session) -> list[Account]:
    """GCC E-COMMERCE Chart of Accounts - Standard for GCC marketplace operations.

    Idempotent AND additive: existing accounts/groups are preserved, while any
    missing accounts (e.g. new EPR-level accounts added in later releases) are
    appended. This allows the COA to grow without wiping prior data.
    """
    existing_accounts = {a.code for a in db.query(Account.code).limit(1000).all()}
    existing_groups = {g.code for g in db.query(AccountGroup.code).limit(1000).all()}

    # GCC Tenant Configuration Groups
    groups = {
        "current_assets": AccountGroup(
            name="Current Assets (GCC)", code="1.1",
            description="GCC operating cash, gateway settlement, COD receivables",
            account_type="Asset", normal_side="debit",
        ),
        "current_liabilities": AccountGroup(
            name="Current Liabilities (GCC)", code="2.1",
            description="GCC supplier payables, logistics payables, VAT, commission",
            account_type="Liability", normal_side="credit",
        ),
        "equity": AccountGroup(
            name="Equity (GCC)", code="3.1",
            description="GCC retained earnings, owner equity",
            account_type="Equity", normal_side="credit",
        ),
        "revenue": AccountGroup(
            name="Revenue (GCC)", code="4.1",
            description="GCC platform revenue: commission, delivery, badge fees",
            account_type="Revenue", normal_side="credit",
        ),
        "operating_expenses": AccountGroup(
            name="Operating Expenses (GCC)", code="5.2",
            description="GCC: gateway fees, logistics, marketing, salaries, other expenses",
            account_type="Expense", normal_side="debit",
        ),
        "fixed_assets": AccountGroup(
            name="Fixed Assets (GCC)", code="1.2",
            description="GCC: office equipment, vehicles, IT, accumulated depreciation",
            account_type="Asset", normal_side="debit",
        ),
        "cogs": AccountGroup(
            name="Cost of Goods Sold (GCC)", code="6.0",
            description="GCC: direct cost of goods sold and fulfilment",
            account_type="Expense", normal_side="debit",
        ),
    }
    for g in groups.values():
        if g.code not in existing_groups:
            db.add(g)
    db.flush()

    # GCC E-COMMERCE Chart of Accounts
    # Following GCC accounting standards for multi-currency marketplace
    # Extended to full EPR-level: COGS, Other Sales/Income/Expenses,
    # Fixed Assets, Accumulated Depreciation, Accruals, Prepayments.
    accounts_data = [
        # ASSETS (debit-normal) - GCC Focused
        ("1010", "Cash - Operating", groups["current_assets"], "debit"),
        ("1020", "Cash - Gateway Settlement", groups["current_assets"], "debit"),
        ("1030", "Accounts Receivable (COD)", groups["current_assets"], "debit"),
        ("1035", "Accounts Receivable - Trade", groups["current_assets"], "debit"),
        ("1040", "Gateway Settlement Receivable", groups["current_assets"], "debit"),
        ("1045", "Prepayments", groups["current_assets"], "debit"),
        ("1050", "Supplier Prepayments", groups["current_assets"], "debit"),
        ("1060", "Inventory", groups["current_assets"], "debit"),
        # FIXED ASSETS (debit-normal)
        ("1100", "Fixed Assets - Office Equipment", groups.get("fixed_assets", groups["current_assets"]), "debit"),
        ("1110", "Fixed Assets - Vehicles", groups.get("fixed_assets", groups["current_assets"]), "debit"),
        ("1120", "Fixed Assets - IT Infrastructure", groups.get("fixed_assets", groups["current_assets"]), "debit"),
        ("1190", "Accumulated Depreciation", groups.get("fixed_assets", groups["current_assets"]), "credit"),
        # LIABILITIES (credit-normal) - GCC Focused
        ("2010", "Supplier Payables (GCC)", groups["current_liabilities"], "credit"),
        ("2020", "Logistics Payables (GCC)", groups["current_liabilities"], "credit"),
        ("2030", "Customer Refund Reserve (GCC)", groups["current_liabilities"], "credit"),
        ("2040", "VAT Payable (GCC)", groups["current_liabilities"], "credit"),
        ("2050", "Commission Payable (GCC)", groups["current_liabilities"], "credit"),
        ("2060", "Deferred Revenue (GCC)", groups["current_liabilities"], "credit"),
        ("2070", "Gateway Settlement Payable (GCC)", groups["current_liabilities"], "credit"),
        ("2080", "Accrued Expenses", groups["current_liabilities"], "credit"),
        ("2090", "Salaries & Wages Payable", groups["current_liabilities"], "credit"),
        # REVENUE (credit-normal) - GCC Marketplace
        ("4010", "Platform Commission Revenue (GCC)", groups["revenue"], "credit"),
        ("4020", "Badge Fee Revenue (GCC)", groups["revenue"], "credit"),
        ("4030", "Delivery Fee Revenue (GCC)", groups["revenue"], "credit"),
        ("4040", "Other Sales (GCC)", groups["revenue"], "credit"),
        ("4050", "Other Income (GCC)", groups["revenue"], "credit"),
        # EQUITY (credit-normal) - GCC Marketplace
        ("3010", "Retained Earnings (GCC)", groups["equity"], "credit"),
        ("3020", "Owner's Equity (GCC)", groups["equity"], "credit"),
        # COST OF GOODS SOLD (debit-normal)
        ("6000", "Cost of Goods Sold", groups.get("cogs", groups["operating_expenses"]), "debit"),
        ("6010", "Shipping & Fulfilment Cost", groups.get("cogs", groups["operating_expenses"]), "debit"),
        # EXPENSES (debit-normal) - GCC Marketplace
        ("5010", "Payment Gateway Fees (GCC)", groups["operating_expenses"], "debit"),
        ("5020", "Bank Charges (GCC)", groups["operating_expenses"], "debit"),
        ("5030", "Operating Expenses (GCC)", groups["operating_expenses"], "debit"),
        ("5040", "Salaries & Wages", groups["operating_expenses"], "debit"),
        ("5050", "Rent & Utilities", groups["operating_expenses"], "debit"),
        ("5060", "Marketing & Advertising", groups["operating_expenses"], "debit"),
        ("5070", "Depreciation Expense", groups["operating_expenses"], "debit"),
        ("5080", "Other Expenses (GCC)", groups["operating_expenses"], "debit"),
    ]

    # Resolve group ids by code (works for both newly-added and pre-existing groups).
    group_by_code = {g.code: g.id for g in db.query(AccountGroup).limit(1000).all()}

    accounts = []
    for code, name, group, normal_side in accounts_data:
        if code in existing_accounts:
            continue
        grp_id = group_by_code.get(group.code) if hasattr(group, "code") else group_by_code.get(group)
        if grp_id is None:
            # Fall back to the group object's id (newly added in this run).
            grp_id = getattr(group, "id", None)
        acct = Account(
            code=code,
            name=name,
            group_id=grp_id,
            normal_side=normal_side,
            currency="OMR",
        )
        db.add(acct)
        accounts.append(acct)

    db.flush()

    for acct in accounts:
        balance = AccountBalance(account_id=acct.id, currency="OMR", balance=Decimal("0.00"))
        db.add(balance)

    db.commit()
    return db.query(Account).limit(1000).all()


def repair_chart_of_accounts(db: Session) -> dict:
    """Update existing chart of accounts with missing account_type/equity groups.

    Idempotent — safe to run on already-seeded databases.
    """
    result = {"groups_updated": 0, "accounts_added": 0}

    # 1. Update existing groups with account_type and normal_side
    group_fixes = {
        "1.1": ("Asset", "debit"),
        "2.1": ("Liability", "credit"),
        "4.1": ("Revenue", "credit"),
        "5.2": ("Expense", "debit"),
    }
    group_codes = list(group_fixes.keys())
    grp_by_code = {}
    if group_codes:
        grp_rows = db.query(AccountGroup).filter(AccountGroup.code.in_(group_codes)).limit(1000).all()
        for g in grp_rows:
            grp_by_code[g.code] = g
    for code, (acct_type, normal_side) in group_fixes.items():
        grp = grp_by_code.get(code)
        if grp:
            changed = False
            if not grp.account_type or grp.account_type == "":
                grp.account_type = acct_type
                changed = True
            if not grp.normal_side or grp.normal_side == "":
                grp.normal_side = normal_side
                changed = True
            if changed:
                result["groups_updated"] += 1

    # 2. Add equity group if missing
    equity_group = db.query(AccountGroup).filter(AccountGroup.code == "3.1").first()
    if not equity_group:
        equity_group = AccountGroup(
            name="Equity (GCC)", code="3.1",
            description="GCC retained earnings, owner equity",
            account_type="Equity", normal_side="credit",
        )
        db.add(equity_group)
        db.flush()
        result["groups_updated"] += 1

    # 3. Add equity accounts if missing
    equity_accounts = [
        ("3010", "Retained Earnings (GCC)", "credit"),
        ("3020", "Owner's Equity (GCC)", "credit"),
    ]
    equity_codes = [c[0] for c in equity_accounts]
    acct_by_code = {}
    if equity_codes:
        acct_rows = db.query(Account).filter(Account.code.in_(equity_codes)).limit(1000).all()
        for a in acct_rows:
            acct_by_code[a.code] = a
    for code, name, normal_side in equity_accounts:
        existing = acct_by_code.get(code)
        if not existing and equity_group:
            acct = Account(
                code=code, name=name,
                group_id=equity_group.id,
                normal_side=normal_side,
                currency="OMR",
            )
            db.add(acct)
            db.flush()
            balance = AccountBalance(account_id=acct.id, currency="OMR", balance=Decimal("0.00"))
            db.add(balance)
            result["accounts_added"] += 1

    db.commit()
    return result


def get_account_by_code(db: Session, code: str) -> Optional[Account]:
    return db.query(Account).filter(Account.code == code).first()


def list_accounts(db: Session) -> list[AccountOut]:
    rows = (
        db.query(Account, AccountGroup.name.label("group_name"))
        .join(AccountGroup, Account.group_id == AccountGroup.id)
        .order_by(Account.code)
        .all()
    )
    return [
        AccountOut(
            id=a.Account.id,
            code=a.Account.code,
            name=a.Account.name,
            group_name=a.group_name,
            normal_side=a.Account.normal_side,
            currency=a.Account.currency,
            is_active=a.Account.is_active,
        )
        for a in rows
    ]


# ── Journal Entries ────────────────────────────────────────────────────────


def _update_account_balance(
    db: Session, account_id: int, currency: str, amount: Decimal, side: str, entry_id: int,
    country_code: Optional[str] = None,
) -> None:
    bal = (
        db.query(AccountBalance)
        .filter(
            AccountBalance.account_id == account_id,
            AccountBalance.currency == currency,
        )
        .first()
    )
    if not bal:
        bal = AccountBalance(
            account_id=account_id, currency=currency, balance=Decimal("0.00"),
            country_code=country_code,
        )
        db.add(bal)
        db.flush()

    acct = db.query(Account).filter(Account.id == account_id).first()
    if not acct:
        raise ValueError(f"Account {account_id} not found")

    if side == acct.normal_side:
        bal.balance = round_money(bal.balance + amount)
    else:
        bal.balance = round_money(bal.balance - amount)

    bal.last_entry_id = entry_id
    bal.last_entry_at = utcnow()
    bal.updated_at = utcnow()
    if country_code:
        bal.country_code = country_code


def create_journal_entry(
    db: Session,
    entry_data: JournalEntryCreate,
    user_id: Optional[int] = None,
) -> JournalEntryOut:
    if not entry_data.lines:
        raise ValueError("Journal entry must have at least one line")

    total_debits = sum(
        round_money(line.amount) for line in entry_data.lines if line.side == "debit"
    )
    total_credits = sum(
        round_money(line.amount) for line in entry_data.lines if line.side == "credit"
    )

    if total_debits != total_credits:
        raise ValueError(
            f"Journal entry not balanced: debits={total_debits} credits={total_credits}"
        )

    cc = entry_data.country_code

    ref_number = entry_data.reference_number
    if not ref_number:
        ref_number = f"JE-{uuid.uuid4().hex[:12].upper()}"

    # Validate all referenced accounts exist and are active BEFORE touching the
    # session. Otherwise a missing account raises after `entry` has already been
    # added/flushed, leaving a half-built object pending in the unit of work that
    # re-raises on the next commit (turning a recoverable error into a 500).
    account_cache: dict[str, "Account"] = cachetools.TTLCache(maxsize=1000, ttl=300)
    for line in entry_data.lines:
        acct = get_account_by_code(db, line.account_code)
        if not acct:
            raise ValueError(f"Account code '{line.account_code}' not found")
        if not acct.is_active:
            raise ValueError(f"Account '{line.account_code}' is inactive")
        account_cache[line.account_code] = acct

    entry = JournalEntry(
        entry_date=entry_data.entry_date,
        reference_type=entry_data.reference_type,
        reference_id=entry_data.reference_id,
        reference_number=ref_number,
        description=entry_data.description,
        currency=entry_data.currency,
        country_code=cc,
        created_by=user_id,
    )
    db.add(entry)
    db.flush()

    lines_out = []
    for line in entry_data.lines:
        acct = account_cache[line.account_code]

        jel = JournalEntryLine(
            entry_id=entry.id,
            account_id=acct.id,
            side=line.side,
            amount=round_money(line.amount),
            description=line.description,
            entity_type=line.entity_type,
            entity_id=line.entity_id,
            country_code=cc,
        )
        db.add(jel)
        db.flush()

        _update_account_balance(db, acct.id, entry_data.currency, jel.amount, line.side, entry.id, cc)

        lines_out.append(
            JournalEntryLineOut(
                id=jel.id,
                account_code=acct.code,
                account_name=acct.name,
                side=jel.side,
                amount=jel.amount,
                description=jel.description,
                entity_type=jel.entity_type,
                entity_id=jel.entity_id,
                country_code=cc,
            )
        )

    db.commit()
    db.refresh(entry)

    return JournalEntryOut(
        id=entry.id,
        entry_date=entry.entry_date,
        reference_type=entry.reference_type,
        reference_id=entry.reference_id,
        reference_number=entry.reference_number,
        description=entry.description,
        currency=entry.currency,
        country_code=cc,
        is_reconciled=entry.is_reconciled,
        created_by=entry.created_by,
        created_at=entry.created_at,
        lines=lines_out,
    )


def get_journal_entry(db: Session, entry_id: int) -> Optional[JournalEntryOut]:
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        return None

    lines = (
        db.query(JournalEntryLine, Account.code, Account.name)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .filter(JournalEntryLine.entry_id == entry_id)
        .all()
    )
    lines_out = [
        JournalEntryLineOut(
            id=l.JournalEntryLine.id,
            account_code=l.code,
            account_name=l.name,
            side=l.JournalEntryLine.side,
            amount=l.JournalEntryLine.amount,
            description=l.JournalEntryLine.description,
            entity_type=l.JournalEntryLine.entity_type,
            entity_id=l.JournalEntryLine.entity_id,
            country_code=l.JournalEntryLine.country_code,
        )
        for l in lines
    ]

    return JournalEntryOut(
        id=entry.id,
        entry_date=entry.entry_date,
        reference_type=entry.reference_type,
        reference_id=entry.reference_id,
        reference_number=entry.reference_number,
        description=entry.description,
        currency=entry.currency,
        country_code=entry.country_code,
        is_reconciled=entry.is_reconciled,
        created_by=entry.created_by,
        created_at=entry.created_at,
        lines=lines_out,
    )


def list_journal_entries(
    db: Session,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[JournalEntryOut]:
    q = db.query(JournalEntry)
    if reference_type:
        q = q.filter(JournalEntry.reference_type == reference_type)
    if reference_id is not None:
        q = q.filter(JournalEntry.reference_id == reference_id)
    if country_code:
        q = q.filter(JournalEntry.country_code == country_code)
    entries = q.order_by(JournalEntry.id.desc()).limit(min(limit, 1000)).all()
    if not entries:
        return []

    # Bulk-load all lines + accounts in two queries (avoids N+1 per entry).
    entry_ids = [e.id for e in entries]
    line_rows = (
        db.query(JournalEntryLine, Account.code, Account.name)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .filter(JournalEntryLine.entry_id.in_(entry_ids))
        .all()
    )
    lines_by_entry: dict[int, list] = {eid: [] for eid in entry_ids}
    for l, code, name in line_rows:
        lines_by_entry[l.entry_id].append(
            JournalEntryLineOut(
                id=l.id,
                account_code=code,
                account_name=name,
                side=l.side,
                amount=l.amount,
                description=l.description,
                entity_type=l.entity_type,
                entity_id=l.entity_id,
                country_code=l.country_code,
            )
        )

    return [
        JournalEntryOut(
            id=e.id,
            entry_date=e.entry_date,
            reference_type=e.reference_type,
            reference_id=e.reference_id,
            reference_number=e.reference_number,
            description=e.description,
            currency=e.currency,
            country_code=e.country_code,
            is_reconciled=e.is_reconciled,
            created_by=e.created_by,
            created_at=e.created_at,
            lines=lines_by_entry.get(e.id, []),
        )
        for e in entries
    ]


# ── Account Balances & Trial Balance ───────────────────────────────────────


def get_account_balance(db: Session, account_id: int, currency: str = "OMR") -> Optional[AccountBalanceOut]:
    bal = (
        db.query(AccountBalance)
        .filter(
            AccountBalance.account_id == account_id,
            AccountBalance.currency == currency,
        )
        .first()
    )
    if not bal:
        return None

    acct = db.query(Account).filter(Account.id == account_id).first()
    group_name = None
    if acct:
        grp = db.query(AccountGroup).filter(AccountGroup.id == acct.group_id).first()
        group_name = grp.name if grp else None

    return AccountBalanceOut(
        account_code=acct.code if acct else "",
        account_name=acct.name if acct else "",
        group_name=group_name,
        normal_side=acct.normal_side if acct else "",
        currency=currency,
        balance=bal.balance,
    )


# ── GCC E-Commerce Financial Event Journal Handlers ─────────────────────────────


def post_order_payment_journal(db: Session, order_id: int, total_amount: Decimal, currency: str = "OMR") -> JournalEntryOut:
    """
    Handle CUSTOMER PAYMENT event for GCC marketplace.
    Dr. Gateway Settlement Receivable | Customer payment captured
    Cr.  Deferred Revenue (GCC)         | Obligation to deliver order
    """
    from domains.orders.models.orders import Order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Order {order_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="order_payment",
            reference_id=order_id,
            description=f"Customer payment for order {order.order_number or order_id}",
            currency=currency,
            lines=[
                JournalLineInput(
                    account_code="1040",
                    side="debit",
                    amount=total_amount,
                    description=f"Gateway settlement for order {order.order_number or order_id}",
                    entity_type="order",
                    entity_id=order_id,
                ),
                JournalLineInput(
                    account_code="2060",
                    side="credit",
                    amount=total_amount,
                    description=f"Deferred revenue recognition for order {order.order_number or order_id}",
                    entity_type="order",
                    entity_id=order_id,
                ),
            ],
            user_id=order.user_id,
        ),
        user_id=order.user_id,
    )


def post_delivery_revenue_journal(db: Session, transaction_ledger: TransactionLedger) -> JournalEntryOut:
    """
    Handle ORDER DELIVERY event for GCC marketplace.
    Dr.  Deferred Revenue (GCC)
    Cr.  Commission Revenue (GCC)
    Cr.  Delivery Fee Revenue (GCC)
    Cr.  VAT Payable (GCC)
    Cr.  Supplier Payables (GCC)
    Cr.  Logistics Payables (GCC)
    
    Uses TransactionLedger for computed revenue/splits
    """
    from domains.orders.models.orders import Order
    order = db.query(Order).filter(Order.id == transaction_ledger.order_id).first()
    if not order:
        raise ValueError(f"Order {transaction_ledger.order_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=transaction_ledger.created_at,
            reference_type="order_delivery",
            reference_id=transaction_ledger.id,
            description=f"Revenue recognition for order {order.order_number or transaction_ledger.order_id} - delivered",
            currency=transaction_ledger.currency,
            lines=[
                JournalLineInput(
                    account_code="2060",
                    side="debit",
                    amount=transaction_ledger.total_amount,
                    description=f"Deferred revenue clearing for order {order.order_number or transaction_ledger.order_id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                # Commission Revenue (Zozi's cut)
                JournalLineInput(
                    account_code="4010",
                    side="credit",
                    amount=transaction_ledger.platform_commission,
                    description=f"Platform commission earned for order {order.order_number or transaction_ledger.order_id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                # Delivery Fee Revenue
                JournalLineInput(
                    account_code="4030",
                    side="credit",
                    amount=transaction_ledger.delivery_fee,
                    description=f"Delivery fee revenue for order {order.order_number or transaction_ledger.order_id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                # VAT Payable (GCC - actual tax rate)
                JournalLineInput(
                    account_code="2040",
                    side="credit",
                    amount=transaction_ledger.vat_amount,
                    description=f"VAT payable (GCC) for order {order.order_number or transaction_ledger.order_id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                # Supplier Payable (after platform fee)
                JournalLineInput(
                    account_code="2010",
                    side="credit",
                    amount=transaction_ledger.net_supplier_amount,
                    description=f"Supplier payable for order {order.order_number or transaction_ledger.order_id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                # Logistics Payable
                JournalLineInput(
                    account_code="2020",
                    side="credit",
                    amount=transaction_ledger.logistics_fee,
                    description=f"Logistics payable for order {order.order_number or transaction_ledger.order_id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
            ],
            user_id=transaction_ledger.performed_by,
        ),
        user_id=transaction_ledger.performed_by,
    )


def post_refund_journal(db: Session, refund_ledger: RefundLedger) -> JournalEntryOut:
    """
    Handle ORDER REFUND event for GCC marketplace.
    Reverses all revenue entries created on delivery.
    """
    from domains.orders.models.orders import Order
    order = db.query(Order).filter(Order.id == refund_ledger.order_id).first()
    if not order:
        raise ValueError(f"Order {refund_ledger.order_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="order_refund",
            reference_id=refund_ledger.id,
            description=f"Refund reversal for order {order.order_number or refund_ledger.order_id}",
            currency=refund_ledger.currency,
            lines=[
                # Reversal of Commission Revenue
                JournalLineInput(
                    account_code="4010",
                    side="debit",
                    amount=refund_ledger.commission_reversal,
                    description=f"Commission revenue reversal for refund {refund_ledger.id}",
                    entity_type="refund",
                    entity_id=refund_ledger.id,
                ),
                # Reversal of Delivery Fee Revenue
                JournalLineInput(
                    account_code="4030",
                    side="debit",
                    amount=refund_ledger.delivery_fee_reversal,
                    description=f"Delivery fee revenue reversal for refund {refund_ledger.id}",
                    entity_type="refund",
                    entity_id=refund_ledger.id,
                ),
                # Reversal of VAT Payable
                JournalLineInput(
                    account_code="2040",
                    side="debit",
                    amount=refund_ledger.vat_reversal,
                    description=f"VAT payable reversal for refund {refund_ledger.id}",
                    entity_type="refund",
                    entity_id=refund_ledger.id,
                ),
                # Reversal of Supplier Payable
                JournalLineInput(
                    account_code="2010",
                    side="debit",
                    amount=refund_ledger.supplier_reversal,
                    description=f"Supplier payable reversal for refund {refund_ledger.id}",
                    entity_type="refund",
                    entity_id=refund_ledger.id,
                ),
                # Reversal of Logistics Payable
                JournalLineInput(
                    account_code="2020",
                    side="debit",
                    amount=refund_ledger.logistics_reversal,
                    description=f"Logistics payable reversal for refund {refund_ledger.id}",
                    entity_type="refund",
                    entity_id=refund_ledger.id,
                ),
                # Cash / Gateway Settlement (refund to customer)
                JournalLineInput(
                    account_code="1020",
                    side="credit",
                    amount=refund_ledger.customer_refund_amount,
                    description=f"Customer refund payment for refund {refund_ledger.id}",
                    entity_type="refund",
                    entity_id=refund_ledger.id,
                ),
            ],
            user_id=refund_ledger.performed_by,
        ),
        user_id=refund_ledger.performed_by,
    )


def post_payout_journal(db: Session, payout: Payout, amount: Decimal) -> JournalEntryOut:
    """
    Handle SUPPLIER PAYOUT event for GCC marketplace.
    Dr. Supplier Payables (GCC)
    Cr.  Cash - Operating (GCC)
    """

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="supplier_payout",
            reference_id=payout.id,
            description=f"Payout to supplier for order {payout.id}",
            currency=payout.currency or "OMR",
            lines=[
                JournalLineInput(
                    account_code="2010",
                    side="debit",
                    amount=amount,
                    description=f"Supplier payable settlement for payout {payout.id}",
                    entity_type="payout",
                    entity_id=payout.id,
                ),
                JournalLineInput(
                    account_code="1010",
                    side="credit",
                    amount=amount,
                    description=f"Cash operating payment for supplier payout {payout.id}",
                    entity_type="payout",
                    entity_id=payout.id,
                ),
            ],
            user_id=payout.supplier_id,
        ),
        user_id=payout.supplier_id,
    )


def post_gateway_fee_journal(db: Session, order_id: int, fee_amount: Decimal, gateway_code: str, transaction_id: str) -> JournalEntryOut:
    """
    Handle GATEWAY FEE event for GCC marketplace.
    Dr.  Payment Gateway Fees (GCC)
    Cr.  Gateway Settlement Receivable
    """
    from domains.orders.models.orders import Order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Order {order_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="gateway_fee",
            reference_id=order_id,
            description=f"Payment gateway fee {gateway_code} #{transaction_id}",
            currency=order.currency or "OMR",
            lines=[
                JournalLineInput(
                    account_code="5010",
                    side="debit",
                    amount=fee_amount,
                    description=f"Payment gateway fee for order {order.order_number or order_id}",
                    entity_type="gateway_fee",
                    entity_id=order_id,
                ),
                JournalLineInput(
                    account_code="1040",
                    side="credit",
                    amount=fee_amount,
                    description=f"Gateway settlement reduction for fee {transaction_id}",
                    entity_type="gateway_fee",
                    entity_id=order_id,
                ),
            ],
            user_id=order.user_id,
        ),
        user_id=order.user_id,
    )


def post_vat_remittance_journal(db: Session, vat_remittance: VATRemittance) -> JournalEntryOut:
    """
    Handle VAT REMITTANCE event for GCC marketplace.
    Dr.  VAT Payable (GCC)
    Cr.  Cash - Operating (GCC)
    """

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="vat_remittance",
            reference_id=vat_remittance.id,
            description=f"VAT remittance to government for period ending {vat_remittance.period_end}",
            currency=vat_remittance.currency or "OMR",
            lines=[
                JournalLineInput(
                    account_code="2040",
                    side="debit",
                    amount=vat_remittance.amount,
                    description=f"VAT liability settlement for period {vat_remittance.period}",
                    entity_type="vat_remittance",
                    entity_id=vat_remittance.id,
                ),
                JournalLineInput(
                    account_code="1010",
                    side="credit",
                    amount=vat_remittance.amount,
                    description=f"Cash payment for VAT remittance {vat_remittance.id}",
                    entity_type="vat_remittance",
                    entity_id=vat_remittance.id,
                ),
            ],
            user_id=None,  # System entry
        ),
        user_id=None,
    )


def post_badge_fee_journal(db: Session, user_id: int, badge_fee_amount: Decimal, badge_id: int) -> JournalEntryOut:
    """
    Handle BADGE FEE event for GCC marketplace.
    Dr.  Accounts Receivable (Customer)
    Cr.  Badge Fee Revenue (GCC)
    """
    from domains.accounts.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="badge_fee",
            reference_id=badge_id,
            description=f"Badge fee for user {user_id}",
            currency=user.preferred_currency or "OMR",
            lines=[
                JournalLineInput(
                    account_code="1030",
                    side="debit",
                    amount=badge_fee_amount,
                    description=f"Customer receivable for badge fee {badge_id}",
                    entity_type="badge",
                    entity_id=badge_id,
                ),
                JournalLineInput(
                    account_code="4020",
                    side="credit",
                    amount=badge_fee_amount,
                    description=f"Badge fee revenue for badge {badge_id}",
                    entity_type="badge",
                    entity_id=badge_id,
                ),
            ],
            user_id=user_id,
        ),
        user_id=user_id,
    )


def post_logistics_cod_remittance_journal(
    db: Session, logistics_settlement_id: int, amount: Decimal, country_code: Optional[str] = None
) -> JournalEntryOut:
    """
    Handle COD REMITTANCE event for GCC marketplace.
    Dr.  COD Receivable
    Cr.  Cash - Operating (GCC)
    """
    # This would link to logistics settlement data

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="cod_remittance",
            reference_id=logistics_settlement_id,
            description=f"COD remittance from logistics for settlement {logistics_settlement_id}",
            currency="OMR",
            country_code=country_code,
            lines=[
                JournalLineInput(
                    account_code="1030",
                    side="debit",
                    amount=amount,
                    description=f"COD receivable clearing for logistics settlement {logistics_settlement_id}",
                    entity_type="logistics_cod",
                    entity_id=logistics_settlement_id,
                ),
                JournalLineInput(
                    account_code="1010",
                    side="credit",
                    amount=amount,
                    description=f"Cash receipt from COD remittance {logistics_settlement_id}",
                    entity_type="logistics_cod",
                    entity_id=logistics_settlement_id,
                ),
            ],
            user_id=None,  # System entry
        ),
        user_id=None,
    )


def post_supplier_settlement_journal(
    db: Session,
    settlement_id: int,
    amount: Decimal,
    supplier_id: Optional[int] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> JournalEntryOut:
    """
    Handle SUPPLIER SETTLEMENT PAYMENT event for GCC marketplace.
    Completes the reconciliation flow: Order → COD → Logistics → Treasury → Supplier.
    Dr.  Supplier Payables (GCC)
    Cr.  Cash - Operating (GCC)
    """
    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=utcnow(),
            reference_type="supplier_settlement",
            reference_id=settlement_id,
            description=f"Supplier settlement payment for settlement {settlement_id}",
            currency=currency,
            country_code=country_code,
            lines=[
                JournalLineInput(
                    account_code="2010",
                    side="debit",
                    amount=amount,
                    description=f"Supplier payable cleared for settlement {settlement_id}",
                    entity_type="supplier_settlement",
                    entity_id=settlement_id,
                ),
                JournalLineInput(
                    account_code="1010",
                    side="credit",
                    amount=amount,
                    description=f"Treasury cash paid to supplier for settlement {settlement_id}",
                    entity_type="supplier_settlement",
                    entity_id=settlement_id,
                ),
            ],
            user_id=supplier_id,
        ),
        user_id=supplier_id,
    )


def get_account_balance_by_code(db: Session, account_code: str, currency: str = "OMR") -> Optional[Decimal]:
    """
    Return current balance for an account by code.
    Convenience method for API/controllers.
    """
    account = get_account_by_code(db, account_code)
    if not account:
        return None

    bal = get_account_balance(db, account.id, currency)
    return bal.balance if bal else Decimal("0.00")


def get_trial_balance(
    db: Session,
    as_of_date: Optional[datetime] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> TrialBalanceOut:
    """
    Return all account balances (trial balance report).
    Includes both debit and credit side totals.

    Optimized: fetches all account balances in a single bulk query (no N+1 loop).
    """
    rows = (
        db.query(Account, AccountGroup.name.label("group_name"))
        .join(AccountGroup, Account.group_id == AccountGroup.id)
        .filter(Account.is_active == True)
        .order_by(Account.code)
        .all()
    )

    # Bulk load balances once instead of one query per account.
    account_ids = [r.Account.id for r in rows]
    bal_q = db.query(AccountBalance).filter(
        AccountBalance.account_id.in_(account_ids),
        AccountBalance.currency == currency,
    )
    if country_code:
        bal_q = bal_q.filter(AccountBalance.country_code == country_code)
    balance_map = {b.account_id: b.balance for b in bal_q.limit(1000).all()}

    accounts_out = []
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    for r in rows:
        acct = r.Account
        balance = balance_map.get(acct.id, Decimal("0.00"))

        if acct.normal_side == "debit":
            total_debit += balance
        else:
            total_credit += balance

        accounts_out.append(
            AccountBalanceOut(
                account_code=acct.code,
                account_name=acct.name,
                group_name=r.group_name,
                normal_side=acct.normal_side,
                currency=currency,
                balance=balance,
            )
        )

    return TrialBalanceOut(
        as_of=as_of_date or utcnow(),
        accounts=accounts_out,
        total_debit_balances=round_money(total_debit),
        total_credit_balances=round_money(total_credit),
    )


def validate_entry_balanced(lines: list[JournalLineInput]) -> bool:
    """
    Ensure sum(debits) == sum(credits) before journal entry creation.
    Used for validation in controllers.
    """
    total_debits = sum(round_money(line.amount) for line in lines if line.side == "debit")
    total_credits = sum(round_money(line.amount) for line in lines if line.side == "credit")

    return total_debits == total_credits

# === MERGED from period_close_service.py ===

"""Period Close Service — fiscal period management, year-end procedures.

Handles opening/closing accounting periods, transferring P&L balances
to retained earnings, and locking periods against further edits.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import AccountGroup
from domains.finance.models.finance import FiscalPeriod
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.finance.services.ledger.general_ledger_service import create_journal_entry
from domains.finance.services.ledger.general_ledger_service import get_account_by_code
from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput
from infrastructure.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


def get_or_create_fiscal_period(
    db: Session,
    country_code: str,
    year: int,
    month: int,
) -> FiscalPeriod:
    """Get existing period or create a new open one."""
    period = (
        db.query(FiscalPeriod)
        .filter(
            FiscalPeriod.country_code == country_code,
            FiscalPeriod.period_year == year,
            FiscalPeriod.period_month == month,
        )
        .first()
    )
    if period:
        return period

    from calendar import monthrange
    period_start = datetime(year, month, 1)
    _, last_day = monthrange(year, month)
    period_end = datetime(year, month, last_day, 23, 59, 59)

    period = FiscalPeriod(
        country_code=country_code,
        period_year=year,
        period_month=month,
        period_start=period_start,
        period_end=period_end,
        status="open",
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def get_current_fiscal_period(
    db: Session,
    country_code: str,
) -> Optional[FiscalPeriod]:
    """Get the current open fiscal period for a country."""
    now = utcnow()
    return (
        db.query(FiscalPeriod)
        .filter(
            FiscalPeriod.country_code == country_code,
            FiscalPeriod.period_start <= now,
            FiscalPeriod.period_end >= now,
        )
        .first()
    )


def close_period(
    db: Session,
    period_id: int,
    closed_by: int,
    notes: Optional[str] = None,
    transfer_to_retained_earnings: bool = True,
) -> dict:
    """Close a fiscal period.

    1. Validates no entries are pending/un-posted
    2. Transfers P&L balances to Retained Earnings
    3. Locks the period against further edits
    """
    period = db.query(FiscalPeriod).filter(FiscalPeriod.id == period_id).first()
    if not period:
        raise ValueError(f"Period {period_id} not found")
    if period.status == "closed":
        raise ValueError(f"Period {period_id} is already closed")
    if period.is_locked:
        raise ValueError(f"Period {period_id} is locked")

    country = period.country_code

    # 1. Check for pending journal entries in period
    pending = db.query(JournalEntry).filter(
        JournalEntry.period_id == period_id,
        JournalEntry.is_deleted == False,
    ).count()

    if pending == 0:
        # Period might have unassigned entries — assign them
        db.query(JournalEntry).filter(
            JournalEntry.entry_date >= period.period_start,
            JournalEntry.entry_date <= period.period_end,
            JournalEntry.period_id.is_(None),
            JournalEntry.is_deleted == False,
        ).update({"period_id": period_id})
        db.commit()

    # 2. Transfer P&L to retained earnings if requested
    transfer_result = None
    if transfer_to_retained_earnings:
        transfer_result = _transfer_pnl_to_retained_earnings(
            db, country, period, closed_by
        )

    # 3. Lock the period
    period.status = "closed"
    period.is_locked = True
    period.closed_at = utcnow()
    period.closed_by = closed_by
    period.notes = notes
    db.commit()

    return {
        "period_id": period.id,
        "country_code": country,
        "period_label": f"{period.period_year}-{period.period_month:02d}",
        "status": "closed",
        "closed_at": period.closed_at.isoformat(),
        "transfer_to_retained_earnings": transfer_result,
    }


def _transfer_pnl_to_retained_earnings(
    db: Session,
    country_code: str,
    period: FiscalPeriod,
    user_id: int,
) -> dict:
    """Close P&L accounts by transferring net income to Retained Earnings."""
    # Aggregate revenue & expense balances for this period
    revenue_accounts = (
        db.query(Account)
        .join(AccountGroup)
        .filter(AccountGroup.account_type == "Revenue")
        .all()
    )
    expense_accounts = (
        db.query(Account)
        .join(AccountGroup)
        .filter(AccountGroup.account_type == "Expense")
        .all()
    )

    total_revenue = Decimal("0.00")
    revenue_lines = []
    for acct in revenue_accounts:
        bal = _get_period_balance(db, acct.id, period)
        if bal != 0:
            total_revenue += bal
            revenue_lines.append({
                "account_code": acct.code,
                "account_name": acct.name,
                "balance": float(bal),
            })

    total_expenses = Decimal("0.00")
    expense_lines = []
    for acct in expense_accounts:
        bal = _get_period_balance(db, acct.id, period)
        if bal != 0:
            total_expenses += bal
            expense_lines.append({
                "account_code": acct.code,
                "account_name": acct.name,
                "balance": float(bal),
            })

    net_income = round_money(total_revenue - total_expenses)

    if net_income == 0:
        return {"net_income": 0, "message": "No P&L balance to transfer"}

    # Create closing journal entry
    retained = get_account_by_code(db, "3010")
    if not retained:
        raise ValueError("Retained Earnings (3010) account not found — run seed/repair first")

    lines = []
    if net_income > 0:
        # Dr. Revenue accounts, Cr. Retained Earnings
        for acct in revenue_accounts:
            bal = _get_period_balance(db, acct.id, period)
            if bal != 0:
                lines.append(JournalLineInput(
                    account_code=acct.code,
                    side="debit",
                    amount=bal,
                    description=f"Period close transfer for {period.period_year}-{period.period_month:02d}",
                ))
        lines.append(JournalLineInput(
            account_code="3010",
            side="credit",
            amount=net_income,
            description=f"Net income transfer for {period.period_year}-{period.period_month:02d}",
        ))
    else:
        # Net loss: Dr. Retained Earnings, Cr. Expense accounts
        lines.append(JournalLineInput(
            account_code="3010",
            side="debit",
            amount=abs(net_income),
            description=f"Net loss transfer for {period.period_year}-{period.period_month:02d}",
        ))
        for acct in expense_accounts:
            bal = _get_period_balance(db, acct.id, period)
            if bal != 0:
                lines.append(JournalLineInput(
                    account_code=acct.code,
                    side="credit",
                    amount=bal,
                    description=f"Period close expense clearing for {period.period_year}-{period.period_month:02d}",
                ))

    ref = f"CLOSE-{country_code}-{period.period_year}-{period.period_month:02d}"
    journal_entry = create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=period.period_end,
            reference_type="period_close",
            reference_id=period.id,
            reference_number=ref,
            description=f"Period closing entry for {period.period_year}-{period.period_month:02d} ({country_code})",
            currency="OMR",
            lines=lines,
        ),
        user_id=user_id,
    )

    return {
        "net_income": float(net_income),
        "total_revenue": float(total_revenue),
        "total_expenses": float(total_expenses),
        "journal_entry_id": journal_entry.id,
        "revenue_accounts": revenue_lines,
        "expense_accounts": expense_lines,
    }


def _get_period_balance(db: Session, account_id: int, period: FiscalPeriod) -> Decimal:
    """Get the net change for an account within a fiscal period."""
    result = db.query(
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
        JournalEntryLine.account_id == account_id,
        JournalEntry.entry_date >= period.period_start,
        JournalEntry.entry_date <= period.period_end,
        JournalEntry.is_deleted == False,
        JournalEntry.reversal_of_id.is_(None),
    ).scalar()

    acct = db.query(Account).filter(Account.id == account_id).first()
    amount = result or Decimal("0.00")
    if acct and acct.normal_side == "credit":
        return -amount
    return amount


def list_periods(
    db: Session,
    country_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 24,
) -> list[FiscalPeriod]:
    """List fiscal periods with optional filters."""
    q = db.query(FiscalPeriod).order_by(FiscalPeriod.period_year.desc(), FiscalPeriod.period_month.desc())
    if country_code:
        q = q.filter(FiscalPeriod.country_code == country_code)
    if status:
        q = q.filter(FiscalPeriod.status == status)
    return q.limit(min(limit, 1000)).all()

# === MERGED from finance_transfer_service.py ===

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.governance.models.admin import FinanceBankAccount
from domains.accounts.models.banking import LogisticsPartnerBankAccount
from domains.governance.models.admin import LogisticsSettlement
from domains.accounts.models.banking import SupplierBankAccount
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.payments import Payout
from infrastructure.utils.config import settings
from kernel.money import round_money, to_decimal

TransferExportType = Literal[
    "supplier-payout-transfers",
    "logistics-payout-transfers",
    "cod-remittance-transfers",
]

DispatchableTransferType = Literal[
    "supplier-payout-transfers",
    "logistics-payout-transfers",
]

TransferReferenceKind = Literal[
    "supplier_payout",
    "logistics_payout",
    "cod_remittance",
]


def get_active_finance_bank_settings(db: Session) -> FinanceBankAccount | None:
    record = (
        db.query(FinanceBankAccount)
        .filter(FinanceBankAccount.is_active == True)
        .order_by(FinanceBankAccount.id.desc())
        .first()
    )
    if record is None or not bool(getattr(record, "is_active", True)):
        return None
    return record


def _clean_reference_prefix(value: str | None) -> str:
    raw = (value or "ZOZI").strip().upper()
    sanitized = re.sub(r"[^A-Z0-9]+", "-", raw)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    return sanitized or "ZOZI"


def _mask_value(value: str | None, *, visible: int = 4) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    if len(normalized) <= visible:
        return "*" * len(normalized)
    mask_length = max(len(normalized) - visible, 4)
    return f"{'*' * mask_length}{normalized[-visible:]}"


def build_transfer_reference(
    db: Session,
    *,
    kind: TransferReferenceKind,
    entity_id: int,
    record_id: int | None = None,
) -> str:
    record = get_active_finance_bank_settings(db)
    prefix = _clean_reference_prefix(getattr(record, "remittance_reference_prefix", None))
    kind_code = {
        "supplier_payout": "SUP",
        "logistics_payout": "LOG",
        "cod_remittance": "COD",
    }[kind]
    parts = [prefix, kind_code, str(entity_id)]
    if record_id is not None:
        parts.append(str(record_id))
    return "-".join(parts)[:96]


def _has_bank_details(record: FinanceBankAccount | None) -> bool:
    if record is None:
        return False
    return any(
        bool(getattr(record, field, None))
        for field in (
            "account_label",
            "beneficiary_name",
            "bank_name",
            "account_number",
            "iban",
        )
    )


def _serialize_bank_instruction(
    record: FinanceBankAccount | None,
    *,
    title: str,
    direction: str,
    reference_value: str,
    reference_help: str,
    include_sensitive_details: bool,
    fallback_instructions: str,
) -> dict[str, Any]:
    if record is None:
        return {
            "configured": False,
            "title": title,
            "direction": direction,
            "account_label": None,
            "beneficiary_name": None,
            "bank_name": None,
            "branch_name": None,
            "account_number": None,
            "iban": None,
            "swift_code": None,
            "routing_number": None,
            "currency": settings.default_currency,
            "support_email": None,
            "support_phone": None,
            "remittance_reference_prefix": _clean_reference_prefix(None),
            "reference_value": reference_value,
            "reference_help": reference_help,
            "instructions": fallback_instructions,
            "details_visible": include_sensitive_details,
        }

    account_number = record.account_number if include_sensitive_details else _mask_value(record.account_number)
    iban = record.iban if include_sensitive_details else _mask_value(record.iban)
    swift_code = record.swift_code if include_sensitive_details else _mask_value(record.swift_code)
    routing_number = record.routing_number if include_sensitive_details else _mask_value(record.routing_number)

    return {
        "configured": _has_bank_details(record),
        "title": title,
        "direction": direction,
        "account_label": record.account_label,
        "beneficiary_name": record.beneficiary_name,
        "bank_name": record.bank_name,
        "branch_name": record.branch_name,
        "account_number": account_number,
        "iban": iban,
        "swift_code": swift_code,
        "routing_number": routing_number,
        "currency": record.currency or settings.default_currency,
        "support_email": record.support_email,
        "support_phone": record.support_phone,
        "remittance_reference_prefix": _clean_reference_prefix(record.remittance_reference_prefix),
        "reference_value": reference_value,
        "reference_help": reference_help,
        "instructions": record.instructions or fallback_instructions,
        "details_visible": include_sensitive_details,
    }


def build_supplier_payout_instruction(supplier_id: int, db: Session) -> dict[str, Any]:
    reference_value = build_transfer_reference(
        db,
        kind="supplier_payout",
        entity_id=supplier_id,
    )
    return _serialize_bank_instruction(
        get_active_finance_bank_settings(db),
        title="Payout Reference Guide",
        direction="incoming_payout",
        reference_value=reference_value,
        reference_help="Quote this reference when asking Zozi finance to trace a supplier payout.",
        include_sensitive_details=False,
        fallback_instructions="Use the payout reference on support tickets or bank trace requests so finance can reconcile your transfer quickly.",
    )


def build_logistics_cod_remittance_instruction(partner_id: int, db: Session) -> dict[str, Any]:
    reference_value = build_transfer_reference(
        db,
        kind="cod_remittance",
        entity_id=partner_id,
    )
    return _serialize_bank_instruction(
        get_active_finance_bank_settings(db),
        title="COD Remittance Instructions",
        direction="outbound_remittance",
        reference_value=reference_value,
        reference_help="Include this remittance reference on every COD bank transfer so Zozi can match the deposit to your settlement ledger.",
        include_sensitive_details=True,
        fallback_instructions="Configure Zozi treasury bank details before asking logistics partners to remit collected COD balances.",
    )


class TransferExportProvider(Protocol):
    key: str
    name: str
    description: str
    supports_direct_execution: bool

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        ...

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        ...


class ManualCsvTransferProvider:
    key = "manual_csv"
    name = "Manual CSV Transfer"
    description = "Creates CSV transfer files for bank portal upload or finance operations review."
    supports_direct_execution = False

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        if export_type == "supplier-payout-transfers":
            return self._build_supplier_payout_export(db)
        if export_type == "logistics-payout-transfers":
            return self._build_logistics_payout_export(db)
        if export_type == "cod-remittance-transfers":
            return self._build_cod_remittance_export(db)
        raise HTTPException(status_code=404, detail="Unknown transfer export type")

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        raise HTTPException(
            status_code=422,
            detail="The manual_csv provider creates bank-upload files only and cannot dispatch transfers directly.",
        )

    def _build_supplier_payout_export(
        self,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        payouts = (
            db.query(Payout)
            .filter(Payout.status == "processing")
            .order_by(Payout.created_at.asc(), Payout.id.asc())
            .all()
        )
        bank = get_active_finance_bank_settings(db)

        # Pre-load all verified supplier bank accounts for payouts in-flight
        supplier_ids = {int(p.supplier_id) for p in payouts if p.supplier_id}
        recipient_map: dict[int, SupplierBankAccount] = {}
        if supplier_ids:
            records = (
                db.query(SupplierBankAccount)
                .filter(
                    SupplierBankAccount.supplier_id.in_(supplier_ids),
                    SupplierBankAccount.verification_status == "verified",
                )
                .all()
            )
            recipient_map = {int(r.supplier_id): r for r in records}

        rows = []
        for payout in payouts:
            supplier_id = int(payout.supplier_id or 0)
            recipient = recipient_map.get(supplier_id)
            if recipient:
                recipient_status = "verified"
                recipient_note = ""
            else:
                recipient_status = "missing_in_zozi"
                recipient_note = "Supplier has not submitted a verified bank account. Add via /supplier/bank-account."

            rows.append({
                "payout_id": payout.id,
                "supplier_id": supplier_id,
                "supplier_username": getattr(payout.supplier, "username", None),
                "amount": float(round_money(to_decimal(payout.amount or 0))),
                "currency": (recipient.currency if recipient else None) or getattr(bank, "currency", None) or settings.default_currency,
                "reference": payout.reference or build_transfer_reference(
                    db,
                    kind="supplier_payout",
                    entity_id=supplier_id,
                    record_id=int(payout.id),
                ),
                "method": payout.method or "bank",
                "status": payout.status,
                "created_at": payout.created_at.isoformat() if payout.created_at else "",
                "processed_at": payout.processed_at.isoformat() if payout.processed_at else "",
                "source_account_label": getattr(bank, "account_label", None) or "Zozi treasury",
                "source_bank_name": getattr(bank, "bank_name", None) or "",
                # Recipient bank details (from verified SupplierBankAccount or empty)
                "recipient_beneficiary_name": recipient.beneficiary_name if recipient else "",
                "recipient_bank_name": recipient.bank_name if recipient else "",
                "recipient_branch_name": recipient.branch_name if recipient else "",
                "recipient_account_number": recipient.account_number if recipient else "",
                "recipient_iban": recipient.iban if recipient else "",
                "recipient_swift_code": recipient.swift_code if recipient else "",
                "recipient_routing_number": recipient.routing_number if recipient else "",
                "recipient_bank_country": recipient.bank_country if recipient else "",
                "recipient_account_status": recipient_status,
                "ops_note": recipient_note,
                "notes": payout.notes or "",
            })

        fieldnames = [
            "payout_id",
            "supplier_id",
            "supplier_username",
            "amount",
            "currency",
            "reference",
            "method",
            "status",
            "created_at",
            "processed_at",
            "source_account_label",
            "source_bank_name",
            "recipient_beneficiary_name",
            "recipient_bank_name",
            "recipient_branch_name",
            "recipient_account_number",
            "recipient_iban",
            "recipient_swift_code",
            "recipient_routing_number",
            "recipient_bank_country",
            "recipient_account_status",
            "ops_note",
            "notes",
        ]
        return rows, fieldnames, f"supplier_payout_transfers_{self.key}.csv", {
            "resource_type": "supplier_payout_transfers",
            "details": {
                "count": len(rows),
                "provider": self.key,
                "with_recipient_details": sum(1 for r in rows if r["recipient_account_status"] == "verified"),
            },
        }

    def _build_logistics_payout_export(
        self,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        payouts = (
            db.query(LogisticsPartnerPayout)
            .filter(LogisticsPartnerPayout.status == "processing")
            .order_by(LogisticsPartnerPayout.created_at.asc(), LogisticsPartnerPayout.id.asc())
            .all()
        )
        bank = get_active_finance_bank_settings(db)

        partner_ids = {int(p.partner_id) for p in payouts if p.partner_id}
        recipient_map: dict[int, LogisticsPartnerBankAccount] = {}
        if partner_ids:
            records = (
                db.query(LogisticsPartnerBankAccount)
                .filter(
                    LogisticsPartnerBankAccount.partner_id.in_(partner_ids),
                    LogisticsPartnerBankAccount.verification_status == "verified",
                )
                .all()
            )
            recipient_map = {int(r.partner_id): r for r in records}

        rows = []
        for payout in payouts:
            partner_id = int(payout.partner_id or 0)
            recipient = recipient_map.get(partner_id)
            if recipient:
                recipient_status = "verified"
                recipient_note = ""
            else:
                recipient_status = "missing_in_zozi"
                recipient_note = "Partner has not submitted a verified bank account. Add via /logistics-partners/me/bank-account."

            rows.append({
                "payout_id": payout.id,
                "partner_id": partner_id,
                "partner_name": getattr(payout.partner, "name", None),
                "partner_code": getattr(payout.partner, "code", None),
                "amount": float(round_money(to_decimal(payout.amount or 0))),
                "currency": (recipient.currency if recipient else None) or getattr(bank, "currency", None) or settings.default_currency,
                "reference": payout.reference or build_transfer_reference(
                    db,
                    kind="logistics_payout",
                    entity_id=partner_id,
                    record_id=int(payout.id),
                ),
                "method": payout.method or "bank",
                "status": payout.status,
                "created_at": payout.created_at.isoformat() if payout.created_at else "",
                "processed_at": payout.processed_at.isoformat() if payout.processed_at else "",
                "source_account_label": getattr(bank, "account_label", None) or "Zozi treasury",
                "source_bank_name": getattr(bank, "bank_name", None) or "",
                "recipient_beneficiary_name": recipient.beneficiary_name if recipient else "",
                "recipient_bank_name": recipient.bank_name if recipient else "",
                "recipient_branch_name": recipient.branch_name if recipient else "",
                "recipient_account_number": recipient.account_number if recipient else "",
                "recipient_iban": recipient.iban if recipient else "",
                "recipient_swift_code": recipient.swift_code if recipient else "",
                "recipient_routing_number": recipient.routing_number if recipient else "",
                "recipient_bank_country": recipient.bank_country if recipient else "",
                "recipient_account_status": recipient_status,
                "ops_note": recipient_note,
                "notes": payout.notes or "",
            })

        fieldnames = [
            "payout_id",
            "partner_id",
            "partner_name",
            "partner_code",
            "amount",
            "currency",
            "reference",
            "method",
            "status",
            "created_at",
            "processed_at",
            "source_account_label",
            "source_bank_name",
            "recipient_beneficiary_name",
            "recipient_bank_name",
            "recipient_branch_name",
            "recipient_account_number",
            "recipient_iban",
            "recipient_swift_code",
            "recipient_routing_number",
            "recipient_bank_country",
            "recipient_account_status",
            "ops_note",
            "notes",
        ]
        return rows, fieldnames, f"logistics_payout_transfers_{self.key}.csv", {
            "resource_type": "logistics_payout_transfers",
            "details": {
                "count": len(rows),
                "provider": self.key,
                "with_recipient_details": sum(1 for r in rows if r["recipient_account_status"] == "verified"),
            },
        }

    def _build_cod_remittance_export(
        self,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        settlements = (
            db.query(LogisticsSettlement)
            .filter(LogisticsSettlement.cod_remittance_status.in_(["pending", "partial"]))
            .order_by(LogisticsSettlement.partner_id.asc(), LogisticsSettlement.id.asc())
            .all()
        )
        bank = get_active_finance_bank_settings(db)
        aggregated: dict[int, dict[str, Any]] = {}

        for settlement in settlements:
            partner_id = int(settlement.partner_id)
            amount_due = round_money(
                to_decimal(settlement.cod_collected or 0)
                - to_decimal(settlement.cod_retained or 0)
                - to_decimal(settlement.cod_remitted or 0)
            )
            if amount_due <= Decimal("0"):
                continue

            bucket = aggregated.setdefault(
                partner_id,
                {
                    "partner_id": partner_id,
                    "partner_name": getattr(settlement.partner, "name", None),
                    "partner_code": getattr(settlement.partner, "code", None),
                    "currency": settlement.currency or getattr(bank, "currency", None) or settings.default_currency,
                    "outstanding_cod_due": Decimal("0"),
                    "settlement_ids": [],
                    "order_ids": [],
                },
            )
            bucket["outstanding_cod_due"] = round_money(bucket["outstanding_cod_due"] + amount_due)
            bucket["settlement_ids"].append(str(settlement.id))
            bucket["order_ids"].append(str(settlement.order_id))

        rows = [
            {
                "partner_id": partner_id,
                "partner_name": payload["partner_name"],
                "partner_code": payload["partner_code"],
                "outstanding_cod_due": float(round_money(payload["outstanding_cod_due"])),
                "currency": payload["currency"],
                "reference": build_transfer_reference(
                    db,
                    kind="cod_remittance",
                    entity_id=partner_id,
                ),
                "settlement_ids": ",".join(payload["settlement_ids"]),
                "order_ids": ",".join(payload["order_ids"]),
                "beneficiary_name": getattr(bank, "beneficiary_name", None) or "",
                "bank_name": getattr(bank, "bank_name", None) or "",
                "branch_name": getattr(bank, "branch_name", None) or "",
                "account_number": getattr(bank, "account_number", None) or "",
                "iban": getattr(bank, "iban", None) or "",
                "swift_code": getattr(bank, "swift_code", None) or "",
                "routing_number": getattr(bank, "routing_number", None) or "",
                "support_email": getattr(bank, "support_email", None) or "",
                "support_phone": getattr(bank, "support_phone", None) or "",
                "instructions": getattr(bank, "instructions", None)
                or "Use the generated remittance reference on the bank transfer so Zozi can reconcile COD correctly.",
            }
            for partner_id, payload in aggregated.items()
        ]
        fieldnames = [
            "partner_id",
            "partner_name",
            "partner_code",
            "outstanding_cod_due",
            "currency",
            "reference",
            "settlement_ids",
            "order_ids",
            "beneficiary_name",
            "bank_name",
            "branch_name",
            "account_number",
            "iban",
            "swift_code",
            "routing_number",
            "support_email",
            "support_phone",
            "instructions",
        ]
        return rows, fieldnames, f"cod_remittance_transfers_{self.key}.csv", {
            "resource_type": "cod_remittance_transfers",
            "details": {"count": len(rows), "provider": self.key},
        }


def _treasury_dispatch_ready(record: FinanceBankAccount | None) -> bool:
    if record is None or not bool(getattr(record, "is_active", True)):
        return False
    return bool(
        getattr(record, "beneficiary_name", None)
        and getattr(record, "bank_name", None)
        and (getattr(record, "account_number", None) or getattr(record, "iban", None))
    )


def _provider_missing_requirements(provider_key: str, db: Session | None = None) -> list[str]:
    if provider_key == ManualCsvTransferProvider.key:
        return []

    if provider_key == ConfiguredBankApiTransferProvider.key:
        missing: list[str] = []
        if not settings.bank_api_enabled:
            missing.append("Enable BANK_API_ENABLED")
        if not settings.bank_api_base_url.strip():
            missing.append("Set BANK_API_BASE_URL")
        if not settings.bank_api_batch_path.strip():
            missing.append("Set BANK_API_BATCH_PATH")
        if not settings.bank_api_auth_token.strip():
            missing.append("Set BANK_API_AUTH_TOKEN")
        if not settings.bank_api_source_account_id.strip():
            missing.append("Set BANK_API_SOURCE_ACCOUNT_ID")
        if db is not None and not _treasury_dispatch_ready(get_active_finance_bank_settings(db)):
            missing.append("Configure active treasury bank details in Finance Bank Settings")
        return missing

    if provider_key == StripeConnectTransferProvider.key:
        missing: list[str] = []
        if not settings.stripe_secret_key.strip():
            missing.append("Set STRIPE_SECRET_KEY")
        return missing

    return ["Unknown transfer provider"]


def _provider_is_configured(provider_key: str, db: Session | None = None) -> bool:
    return len(_provider_missing_requirements(provider_key, db)) == 0


def test_configured_bank_api_connection(db: Session) -> dict[str, Any]:
    endpoint = None
    if settings.bank_api_base_url.strip() and settings.bank_api_batch_path.strip():
        endpoint = f"{settings.bank_api_base_url.rstrip('/')}/{settings.bank_api_batch_path.lstrip('/')}"

    missing_requirements = _provider_missing_requirements(ConfiguredBankApiTransferProvider.key, db)
    if missing_requirements:
        return {
            "provider": ConfiguredBankApiTransferProvider.key,
            "endpoint": endpoint,
            "ok": False,
            "reachable": False,
            "status_code": None,
            "detail": "Complete the treasury and bank API requirements before testing the connection.",
            "missing_requirements": missing_requirements,
        }

    conn = bank_api.test_connection(
        settings.bank_api_base_url,
        settings.bank_api_batch_path,
        settings.bank_api_auth_token,
        settings.bank_api_timeout_seconds,
    )
    return {
        "provider": ConfiguredBankApiTransferProvider.key,
        "endpoint": endpoint,
        **conn,
        "missing_requirements": [],
    }


def _build_dispatch_manifest(
    export_type: DispatchableTransferType,
    rows: list[dict[str, Any]],
    bank: FinanceBankAccount | None,
) -> dict[str, Any]:
    kind_label = "supplier" if export_type == "supplier-payout-transfers" else "logistics"
    batch_reference = f"{_clean_reference_prefix(getattr(bank, 'remittance_reference_prefix', None))}-BATCH-{kind_label[:3].upper()}-{uuid4().hex[:10].upper()}"
    dispatchable: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for row in rows:
        record_id = int(row.get("payout_id") or 0)
        recipient_status = str(row.get("recipient_account_status") or "").strip() or "missing_in_zozi"
        if recipient_status != "verified":
            skipped.append({
                "record_id": record_id,
                "reference": row.get("reference"),
                "reason": row.get("ops_note") or f"Recipient bank account is {recipient_status}.",
            })
            continue

        dispatchable.append({
            "record_id": record_id,
            "reference": row.get("reference"),
            "amount": row.get("amount"),
            "currency": row.get("currency") or settings.default_currency,
            "beneficiary_name": row.get("recipient_beneficiary_name"),
            "bank_name": row.get("recipient_bank_name"),
            "branch_name": row.get("recipient_branch_name"),
            "account_number": row.get("recipient_account_number"),
            "iban": row.get("recipient_iban"),
            "swift_code": row.get("recipient_swift_code"),
            "routing_number": row.get("recipient_routing_number"),
            "bank_country": row.get("recipient_bank_country"),
            "metadata": {
                "transfer_kind": kind_label,
                "source_account_label": row.get("source_account_label"),
                "source_bank_name": row.get("source_bank_name"),
                "notes": row.get("notes") or "",
            },
        })

    return {
        "export_type": export_type,
        "batch_reference": batch_reference,
        "source_account": {
            "account_label": getattr(bank, "account_label", None),
            "beneficiary_name": getattr(bank, "beneficiary_name", None),
            "bank_name": getattr(bank, "bank_name", None),
            "currency": getattr(bank, "currency", None) or settings.default_currency,
            "source_account_id": settings.bank_api_source_account_id or None,
        },
        "dispatchable_transfers": dispatchable,
        "skipped_transfers": skipped,
        "dispatchable_count": len(dispatchable),
        "skipped_count": len(skipped),
        "total_candidates": len(rows),
    }


def _mark_dispatch_submitted(
    export_type: DispatchableTransferType,
    db: Session,
    *,
    dispatchable_transfers: list[dict[str, Any]],
    provider_key: str,
    provider_batch_id: str,
    provider_status: str,
) -> None:
    """Persist provider dispatch metadata on payout rows for later reconciliation/UI visibility."""
    payout_ids = [int(item.get("record_id", 0)) for item in dispatchable_transfers if int(item.get("record_id", 0))]
    if not payout_ids:
        return

    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    note_line = f"Dispatched via {provider_key} batch {provider_batch_id}"

    if export_type == "supplier-payout-transfers":
        rows = db.query(Payout).filter(Payout.id.in_(payout_ids)).limit(1000).all()
    else:
        rows = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.id.in_(payout_ids)).limit(1000).all()

    for row in rows:
        row.provider = provider_key
        row.provider_payment_id = provider_batch_id
        row.provider_status = provider_status
        row.last_provider_sync_at = synced_at
        existing_notes = (row.notes or "").strip()
        if note_line not in existing_notes:
            row.notes = f"{existing_notes}\n{note_line}".strip() if existing_notes else note_line

    db.flush()


class ConfiguredBankApiTransferProvider:
    key = "configured_bank_api"
    name = "Configured Bank API"
    description = "Submits supplier or logistics payout batches to a configured treasury or bank API using secret-managed credentials."
    supports_direct_execution = True

    def __init__(self) -> None:
        self._csv_provider = ManualCsvTransferProvider()

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        rows, fieldnames, filename, audit_meta = self._csv_provider.build_export_payload(export_type, db)
        return rows, fieldnames, filename.replace("manual_csv", self.key), {
            **audit_meta,
            "details": {**audit_meta["details"], "provider": self.key},
        }

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        rows, _fieldnames, _filename, _audit_meta = self._csv_provider.build_export_payload(export_type, db)
        bank = get_active_finance_bank_settings(db)
        manifest = _build_dispatch_manifest(export_type, rows, bank)
        base_result = {
            "provider": self.key,
            "provider_name": self.name,
            "supports_direct_execution": True,
            "configured": _provider_is_configured(self.key, db),
            **manifest,
        }

        if dry_run:
            return {
                **base_result,
                "status": "dry_run",
                "submitted": False,
                "preview": manifest["dispatchable_transfers"][:10],
            }

        if not settings.bank_api_enabled:
            raise HTTPException(status_code=503, detail="BANK_API_ENABLED must be true before live payout dispatch is allowed.")
        if not settings.bank_api_base_url.strip() or not settings.bank_api_batch_path.strip():
            raise HTTPException(status_code=503, detail="BANK_API_BASE_URL and BANK_API_BATCH_PATH must be configured for live payout dispatch.")
        if not settings.bank_api_auth_token.strip():
            raise HTTPException(status_code=503, detail="BANK_API_AUTH_TOKEN must be configured for live payout dispatch.")
        if not settings.bank_api_source_account_id.strip():
            raise HTTPException(status_code=503, detail="BANK_API_SOURCE_ACCOUNT_ID must be configured for live payout dispatch.")
        if not _treasury_dispatch_ready(bank):
            raise HTTPException(status_code=503, detail="Finance Bank Settings must include an active beneficiary, bank name, and account number or IBAN before live payout dispatch is allowed.")
        if manifest["dispatchable_count"] == 0:
            return {
                **base_result,
                "status": "no_dispatchable_transfers",
                "submitted": False,
                "preview": [],
            }

        payload = {
            "batch_reference": manifest["batch_reference"],
            "source_account": manifest["source_account"],
            "transfers": manifest["dispatchable_transfers"],
            "metadata": {
                "app": settings.app_name,
                "export_type": export_type,
                "currency": manifest["source_account"]["currency"],
            },
        }

        try:
            conn = bank_api.dispatch_batch(
                settings.bank_api_base_url,
                settings.bank_api_batch_path,
                settings.bank_api_auth_token,
                manifest["batch_reference"],
                payload,
                settings.bank_api_timeout_seconds,
            )
        except bank_api.BankApiError as exc:
            raise HTTPException(status_code=502, detail=f"Bank API dispatch failed: {exc}") from exc

        response_body: dict[str, Any] = conn["body"]
        response_status_code = conn["status_code"]

        provider_batch_id = response_body.get("batch_id") or response_body.get("id") or manifest["batch_reference"]
        provider_status = response_body.get("status") or "submitted"
        _mark_dispatch_submitted(
            export_type,
            db,
            dispatchable_transfers=manifest["dispatchable_transfers"],
            provider_key=self.key,
            provider_batch_id=provider_batch_id,
            provider_status=provider_status,
        )

        return {
            **base_result,
            "status": "submitted",
            "submitted": True,
            "provider_batch_id": provider_batch_id,
            "provider_status": provider_status,
            "provider_http_status": response_status_code,
            "preview": [],
        }


class StripeConnectTransferProvider:
    """Pays out supplier balances via Stripe Connect transfers.

    For each ``processing`` Payout the provider will:
    1. Look up a verified SupplierBankAccount for the supplier.
    2. Optionally auto-create a Stripe Express account if none exists yet
       (controlled by ``STRIPE_CONNECT_AUTO_CREATE_ACCOUNTS``).
    3. Issue a ``stripe.Transfer`` to the connected account.
    4. Persist the Stripe IDs back onto the Payout and SupplierBankAccount rows.
    """

    key = "stripe_connect"
    name = "Stripe Connect"
    description = (
        "Disburses payouts directly to supplier Stripe Connect accounts. "
        "Supports automatic account creation when STRIPE_CONNECT_AUTO_CREATE_ACCOUNTS is enabled."
    )
    supports_direct_execution = True

    def __init__(self) -> None:
        self._csv_provider = ManualCsvTransferProvider()

    def build_export_payload(
        self,
        export_type: TransferExportType,
        db: Session,
    ) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
        rows, fieldnames, filename, audit_meta = self._csv_provider.build_export_payload(export_type, db)
        return rows, fieldnames, filename.replace("manual_csv", self.key), {
            **audit_meta,
            "details": {**audit_meta["details"], "provider": self.key},
        }

    def execute_transfer_batch(
        self,
        export_type: DispatchableTransferType,
        db: Session,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        if export_type != "supplier-payout-transfers":
            raise HTTPException(status_code=400, detail="Stripe Connect only supports supplier payout dispatch.")

        if not settings.stripe_secret_key or not settings.stripe_secret_key.strip():
            raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY must be configured for Stripe Connect payout dispatch.")

        configure_stripe_connect(settings.stripe_secret_key, getattr(settings, "stripe_api_version", None))

        # Fetch processing payouts that haven't been dispatched yet
        payouts = (
            db.query(Payout)
            .filter(
                Payout.status == "processing",
                Payout.method == "bank",
                Payout.provider.is_(None),
            )
            .all()
        )

        base_result: dict[str, Any] = {
            "provider": self.key,
            "provider_name": self.name,
            "supports_direct_execution": True,
            "configured": _provider_is_configured(self.key, db),
            "dispatchable_count": len(payouts),
            "batch_reference": f"STRIPE-CONNECT-{uuid4().hex[:10].upper()}",
        }

        if dry_run:
            preview = []
            for payout in payouts[:10]:
                bank = (
                    db.query(SupplierBankAccount)
                    .filter(
                        SupplierBankAccount.supplier_id == payout.supplier_id,
                        SupplierBankAccount.verification_status == "verified",
                    )
                    .first()
                )
                preview.append({
                    "reference": payout.reference,
                    "supplier_id": payout.supplier_id,
                    "amount": float(payout.amount),
                    "has_bank_account": bank is not None,
                })
            return {
                **base_result,
                "status": "dry_run",
                "submitted": False,
                "preview": preview,
            }

        submitted_count = 0
        failed_count = 0
        skipped_count = 0
        failed_references: list[str] = []

        for payout in payouts:
            try:
                bank = (
                    db.query(SupplierBankAccount)
                    .filter(
                        SupplierBankAccount.supplier_id == payout.supplier_id,
                        SupplierBankAccount.verification_status == "verified",
                    )
                    .first()
                )
                if bank is None:
                    skipped_count += 1
                    continue

                # Resolve or create the Stripe Account
                connect_account_id: str | None = bank.provider_recipient_id if bank.provider == "stripe_connect" else None

                if not connect_account_id and settings.stripe_connect_auto_create_accounts:
                    country = getattr(settings, "stripe_connect_default_country", "US") or "US"
                    business_url = getattr(settings, "stripe_connect_default_business_url", "") or ""
                    tos_ip = getattr(settings, "stripe_connect_tos_acceptance_ip", "127.0.0.1") or "127.0.0.1"
                    create_kwargs: dict[str, Any] = {
                        "type": "express",
                        "country": country,
                        "capabilities": {"transfers": {"requested": True}},
                        "metadata": {
                            "supplier_id": str(payout.supplier_id),
                            "beneficiary_name": bank.beneficiary_name or "",
                            "zozi_reference": payout.reference,
                        },
                        "tos_acceptance": {"ip": tos_ip, "date": int(datetime.now(timezone.utc).timestamp())},
                    }
                    if business_url:
                        create_kwargs["business_profile"] = {"url": business_url}
                    acct = create_connect_account(**create_kwargs)
                    connect_account_id = acct.id

                    # Activate transfers capability
                    modify_connect_account(
                        connect_account_id,
                        capabilities={"transfers": {"requested": True}},
                    )

                    bank.provider = "stripe_connect"
                    bank.provider_recipient_id = connect_account_id
                    bank.provider_status = "active"
                    db.add(bank)

                if not connect_account_id:
                    skipped_count += 1
                    continue

                currency = (bank.currency or "usd").lower()
                amount_cents = int(round(float(payout.amount) * 100))
                transfer = create_connect_transfer(
                    amount=amount_cents,
                    currency=currency,
                    destination=connect_account_id,
                    metadata={
                        "payout_reference": payout.reference,
                        "supplier_id": str(payout.supplier_id),
                    },
                    transfer_group=base_result["batch_reference"],
                )

                payout.provider = "stripe_connect"
                payout.provider_recipient_id = connect_account_id
                payout.provider_transfer_id = transfer.id
                payout.provider_status = getattr(transfer, "status", "pending")
                payout.last_provider_sync_at = datetime.now(timezone.utc)
                db.add(payout)
                submitted_count += 1

            except Exception:
                failed_count += 1
                failed_references.append(payout.reference)

        db.commit()

        return {
            **base_result,
            "status": "submitted",
            "submitted": True,
            "submitted_count": submitted_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "failed_references": failed_references,
        }


_TRANSFER_PROVIDERS: dict[str, TransferExportProvider] = {
    ManualCsvTransferProvider.key: ManualCsvTransferProvider(),
    ConfiguredBankApiTransferProvider.key: ConfiguredBankApiTransferProvider(),
    StripeConnectTransferProvider.key: StripeConnectTransferProvider(),
}


def get_default_transfer_provider() -> str:
    configured = str(getattr(settings, "payout_transfer_provider", ManualCsvTransferProvider.key) or "").strip().lower()
    if configured in _TRANSFER_PROVIDERS:
        return configured
    return ManualCsvTransferProvider.key


def list_transfer_export_providers(db: Session | None = None) -> list[dict[str, Any]]:
    return [
        {
            "key": provider.key,
            "name": provider.name,
            "description": provider.description,
            "supports_direct_execution": provider.supports_direct_execution,
            "configured": _provider_is_configured(provider.key, db),
            "missing_requirements": _provider_missing_requirements(provider.key, db),
            "is_default": provider.key == get_default_transfer_provider(),
        }
        for provider in _TRANSFER_PROVIDERS.values()
    ]


def build_transfer_export_payload(
    export_type: TransferExportType,
    *,
    db: Session,
    provider: str = ManualCsvTransferProvider.key,
) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
    adapter = _TRANSFER_PROVIDERS.get(provider)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Unknown transfer provider")
    return adapter.build_export_payload(export_type, db)


def execute_transfer_batch(
    export_type: DispatchableTransferType,
    *,
    db: Session,
    provider: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    adapter_key = provider or get_default_transfer_provider()
    adapter = _TRANSFER_PROVIDERS.get(adapter_key)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Unknown transfer provider")
    if not adapter.supports_direct_execution:
        raise HTTPException(status_code=422, detail="Selected transfer provider does not support direct execution")
    return adapter.execute_transfer_batch(export_type, db, dry_run=dry_run)


# ── Country-specific payout settings ─────────────────────────────────────────

def get_country_payout_settings(country_code: str, db: Session) -> dict[str, Any]:
    """Read payout settings from a country's ``CountryConfig.payout_settings_json``.

    Returns default values if the country or its settings are not configured.
    """
    from domains.logistics.ports import normalize_country_code

    code = normalize_country_code(country_code)
    if not code:
        return _default_payout_settings()

    country = db.query(CountryConfig).filter(
        CountryConfig.code == code,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        return _default_payout_settings()

    raw = country.payout_settings_json
    if not raw:
        return _default_payout_settings()
    try:
        settings_dict = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return _default_payout_settings()

    if not isinstance(settings_dict, dict):
        return _default_payout_settings()

    return {
        "minimum_payout_amount": float(settings_dict.get("minimum_payout_amount", 10)),
        "payout_schedule": str(settings_dict.get("payout_schedule", "weekly")).lower(),
        "payout_day": str(settings_dict.get("payout_day", "sunday")).lower(),
        "batch_size": int(settings_dict.get("batch_size", 50)),
        "currency": str(settings_dict.get("currency") or "").upper() or None,
        "country_code": code,
    }


def _default_payout_settings() -> dict[str, Any]:
    return {
        "minimum_payout_amount": 10.0,
        "payout_schedule": "weekly",
        "payout_day": "sunday",
        "batch_size": 50,
        "currency": None,
        "country_code": None,
    }

# === MERGED from admin_finance_creation_service.py ===

"""Accounting Router — General Ledger API and Financial Report endpoints."""
from datetime import date, datetime
from typing import Optional
from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import require_admin
# Lazy imports to avoid circular dependency
def _get_finance_ports():
    from domains.finance.ports import accounting_controller, FinancialReportingService, get_or_create_fiscal_period, get_current_fiscal_period, close_period
    return accounting_controller, FinancialReportingService, get_or_create_fiscal_period, get_current_fiscal_period, close_period
# Lazy import: list_periods
# Lazy import: reverse_journal_entry
# Lazy import: generate_forecast
# Lazy import: controller_get_ar_summary
# Lazy import: controller_get_ap_summary
# Lazy import: controller_post_ar_invoice
# Lazy import: controller_post_ar_payment
# Lazy import: controller_post_ap_payable
# Lazy import: controller_post_ap_payment
from domains.audit.ports import AuditAction, audit_log
from infrastructure.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context

class ReportPeriod(BaseModel):
    period_start: datetime
    period_end: datetime
    currency: str = 'OMR'
    persist: bool = False
    country_code: Optional[str] = None

class ClosePeriodBody(BaseModel):
    period_id: int
    notes: Optional[str] = None
    transfer_to_retained_earnings: bool = True

class ReversalBody(BaseModel):
    entry_id: int
    reason: str

class ARInvoiceBody(BaseModel):
    customer_id: int
    amount: float
    order_id: Optional[int] = None
    invoice_id: Optional[int] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None

class ARPaymentBody(BaseModel):
    customer_id: int
    amount: float
    invoice_id: Optional[int] = None
    order_id: Optional[int] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None

class APPayableBody(BaseModel):
    supplier_id: int
    amount: float
    order_id: Optional[int] = None
    settlement_id: Optional[int] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None

class APPaymentBody(BaseModel):
    supplier_id: int
    amount: float
    settlement_id: Optional[int] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None

# === MERGED from sub_ledger_service.py ===

"""Sub-Ledger Service — per-customer (AR) and per-supplier (AP) tracking.

Bridges GL account balances to entity-level outstanding amounts.
Allows drill-down from GL account 1030 (AR) and 2010 (AP) to individual
customer/supplier sub-ledger entries.
"""
from infrastructure.utils.datetime_utils import utcnow

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

# User imported lazily to avoid circular import
_User_model = None

def _get_User():
    global _User_model
    if _User_model is None:
        from domains.governance.ports import User as _U
        _User_model = _U
    return _User_model

from domains.finance.models.finance import ARLedgerEntry
from domains.finance.models.finance import APLedger
from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import Invoice
from domains.finance.models.finance import SupplierSettlement
from domains.orders.models.orders import Order
from domains.finance.models.finance import APLedger as _APLedger
from kernel.money import round_money

logger = logging.getLogger(__name__)


# ── AR (Accounts Receivable) Sub-Ledger ────────────────────────────────────


def post_ar_invoice(
    db: Session,
    customer_id: int,
    amount: Decimal,
    order_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    due_date: Optional[datetime] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> ARLedgerEntry:
    """Post an invoice to the AR sub-ledger (customer owes money)."""
    current_balance = _get_ar_balance(db, customer_id, currency)
    entry = ARLedgerEntry(
        customer_id=customer_id,
        order_id=order_id,
        invoice_id=invoice_id,
        reference_type="invoice" if invoice_id else "order",
        reference_id=invoice_id or order_id,
        entry_type="invoice",
        amount=amount,
        balance_after=round_money(current_balance + amount),
        currency=currency,
        status="open",
        due_date=due_date,
        description=description or f"Invoice for customer #{customer_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def post_ar_payment(
    db: Session,
    customer_id: int,
    amount: Decimal,
    invoice_id: Optional[int] = None,
    order_id: Optional[int] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> ARLedgerEntry:
    """Post a payment to the AR sub-ledger (customer paid)."""
    current_balance = _get_ar_balance(db, customer_id, currency)
    entry = ARLedgerEntry(
        customer_id=customer_id,
        order_id=order_id,
        invoice_id=invoice_id,
        reference_type="payment",
        reference_id=invoice_id or order_id,
        entry_type="payment",
        amount=amount,
        balance_after=round_money(current_balance - amount),
        currency=currency,
        status="paid",
        settled_at=utcnow(),
        description=description or f"Payment from customer #{customer_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Update related invoice status if provided
    if invoice_id:
        _update_ar_invoice_status(db, invoice_id)
    return entry


def get_ar_summary(
    db: Session,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Get AR sub-ledger summary with outstanding balance."""
    q = db.query(ARLedgerEntry).filter(ARLedgerEntry.is_deleted == False)
    if customer_id:
        q = q.filter(ARLedgerEntry.customer_id == customer_id)
    if status:
        q = q.filter(ARLedgerEntry.status == status)
    if country_code:
        q = q.filter(ARLedgerEntry.country_code == country_code)

    entries = q.order_by(ARLedgerEntry.created_at.desc()).limit(min(limit, 1000)).all()

    total_outstanding = db.query(
        func.coalesce(func.sum(ARLedgerEntry.amount).filter(ARLedgerEntry.status.in_(["open", "partially_paid"])), 0)
    ).filter(ARLedgerEntry.is_deleted == False).scalar() or Decimal("0.00")

    return {
        "total_outstanding": float(total_outstanding),
        "entry_count": len(entries),
        "entries": [
            {
                "id": e.id,
                "customer_id": e.customer_id,
                "entry_type": e.entry_type,
                "amount": float(e.amount),
                "balance_after": float(e.balance_after) if e.balance_after else None,
                "currency": e.currency,
                "status": e.status,
                "due_date": e.due_date.isoformat() if e.due_date else None,
                "created_at": e.created_at.isoformat(),
                "description": e.description,
            }
            for e in entries
        ],
    }


def _get_ar_balance(db: Session, customer_id: int, currency: str) -> Decimal:
    result = db.query(
        func.coalesce(
            func.sum(ARLedgerEntry.amount).filter(ARLedgerEntry.entry_type == "invoice"),
            0,
        ) -
        func.coalesce(
            func.sum(ARLedgerEntry.amount).filter(ARLedgerEntry.entry_type == "payment"),
            0,
        )
    ).filter(
        ARLedgerEntry.customer_id == customer_id,
        ARLedgerEntry.currency == currency,
        ARLedgerEntry.is_deleted == False,
        ARLedgerEntry.status != "written_off",
    ).scalar()
    return result or Decimal("0.00")


def _update_ar_invoice_status(db: Session, invoice_id: int) -> None:
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return
    total_paid = db.query(
        func.coalesce(func.sum(ARLedgerEntry.amount), 0)
    ).filter(
        ARLedgerEntry.invoice_id == invoice_id,
        ARLedgerEntry.entry_type == "payment",
        ARLedgerEntry.is_deleted == False,
    ).scalar() or Decimal("0.00")

    if total_paid >= (invoice.total_amount or Decimal("0.00")):
        invoice.status = "paid"
        # Update AR entries
        db.query(ARLedgerEntry).filter(
            ARLedgerEntry.invoice_id == invoice_id,
            ARLedgerEntry.entry_type == "invoice",
        ).update({"status": "paid", "settled_at": utcnow()})
        db.commit()


# ── AP (Accounts Payable) Sub-Ledger ───────────────────────────────────────


def post_ap_payable(
    db: Session,
    supplier_id: int,
    amount: Decimal,
    order_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    settlement_id: Optional[int] = None,
    due_date: Optional[datetime] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> APLedger:
    """Post a supplier payable (we owe supplier money)."""
    current_balance = _get_ap_balance(db, supplier_id, currency)
    entry = APLedger(
        supplier_id=supplier_id,
        order_id=order_id,
        invoice_id=invoice_id,
        settlement_id=settlement_id,
        reference_type="settlement" if settlement_id else "invoice",
        reference_id=settlement_id or invoice_id or order_id,
        entry_type="payable",
        amount=amount,
        balance_after=round_money(current_balance + amount),
        currency=currency,
        status="open",
        due_date=due_date,
        description=description or f"Payable to supplier #{supplier_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def post_ap_payment(
    db: Session,
    supplier_id: int,
    amount: Decimal,
    settlement_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> APLedger:
    """Record a payment to a supplier (we paid)."""
    current_balance = _get_ap_balance(db, supplier_id, currency)
    entry = APLedger(
        supplier_id=supplier_id,
        settlement_id=settlement_id,
        invoice_id=invoice_id,
        reference_type="payment",
        reference_id=settlement_id or invoice_id,
        entry_type="payment",
        amount=amount,
        balance_after=round_money(current_balance - amount),
        currency=currency,
        status="closed",
        paid_at=utcnow(),
        description=description or f"Payment to supplier #{supplier_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    if settlement_id:
        db.query(SupplierSettlement).filter(
            SupplierSettlement.id == settlement_id
        ).update({"status": "paid", "settled_at": utcnow()})
        db.commit()
    return entry


def get_ap_summary(
    db: Session,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Get AP sub-ledger with outstanding balance."""
    q = db.query(APLedger).filter(APLedger.is_deleted == False)
    if supplier_id:
        q = q.filter(APLedger.supplier_id == supplier_id)
    if status:
        q = q.filter(APLedger.status == status)
    if country_code:
        q = q.filter(APLedger.country_code == country_code)

    entries = q.order_by(APLedger.created_at.desc()).limit(min(limit, 1000)).all()

    total_outstanding = db.query(
        func.coalesce(func.sum(APLedger.amount).filter(APLedger.status.in_(["open", "partially_paid"])), 0)
    ).filter(APLedger.is_deleted == False).scalar() or Decimal("0.00")

    return {
        "total_outstanding": float(total_outstanding),
        "entry_count": len(entries),
        "entries": [
            {
                "id": e.id,
                "supplier_id": e.supplier_id,
                "entry_type": e.entry_type,
                "amount": float(e.amount),
                "balance_after": float(e.balance_after) if e.balance_after else None,
                "currency": e.currency,
                "status": e.status,
                "due_date": e.due_date.isoformat() if e.due_date else None,
                "paid_at": e.paid_at.isoformat() if e.paid_at else None,
                "created_at": e.created_at.isoformat(),
                "description": e.description,
            }
            for e in entries
        ],
    }


def _get_ap_balance(db: Session, supplier_id: int, currency: str) -> Decimal:
    result = db.query(
        func.coalesce(
            func.sum(APLedger.amount).filter(APLedger.entry_type == "payable"),
            0,
        ) -
        func.coalesce(
            func.sum(APLedger.amount).filter(APLedger.entry_type == "payment"),
            0,
        )
    ).filter(
        APLedger.supplier_id == supplier_id,
        APLedger.currency == currency,
        APLedger.is_deleted == False,
        APLedger.status != "disputed",
    ).scalar()
    return result or Decimal("0.00")

# === MERGED from commission_service.py ===

"""
Commission Controller — admin-managed supplier and product-level commission rates.

Combined lookup flow:
    1. Supplier component comes from an active supplier override or the supplier badge tier.
    2. Base component comes from a product override, else category rate, else global default.
    3. Final commission rate = supplier component + resolved base component.

Low-value cap: if order_value < low_value_threshold (5 OMR):
    final_commission = min(rate * order_value, fixed_cap_amount)
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, cast

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from domains.governance.ports import User
from domains.catalog.ports import Product
from domains.comms.models.suppliers import SupplierProfile
from domains.finance.models.commission import CommissionAgreement
from domains.finance.models.commission import CommissionCategoryRate
from domains.finance.models.commission import CommissionLedgerEntry
from domains.finance.models.commission import ProductCommissionOverride
from domains.governance.models.admin import CommissionBadgeTier
from domains.governance.models.admin import CommissionGlobalConfig


def _get_commission_engine():
    """Lazy import to break circular dependency."""
    from domains.finance.services.finance_service import commission_engine
    return commission_engine


def _build_list_page_payload(items: list[Any], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict[str, Any]:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }


def _float_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _category_to_slug(raw_value: Any) -> Optional[str]:
    raw = str(raw_value or "").strip().lower()
    if not raw:
        return None
    return raw.replace(" & ", "-").replace(" ", "-")


def _supplier_rate_snapshot(supplier_id: int, db: Session):
    return _get_commission_engine().get_effective_rate(
        supplier_id=supplier_id,
        product_id=None,
        category_slug=None,
        db=db,
    )


# ── Effective rate lookup ────────────────────────────────────────────────────

def get_effective_rate(
    supplier_id: int,
    product_id: Optional[int],
    db: Session,
) -> Decimal:
    """Return the effective commission rate for a supplier/product combo."""
    from domains.catalog.ports import Product
    category_slug: Optional[str] = None
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
        category_slug = _category_to_slug(getattr(product, "category", None) if product else None)

    return _get_commission_engine().get_effective_rate(
        supplier_id=supplier_id,
        product_id=product_id,
        category_slug=category_slug,
        db=db,
    ).applied_rate


# ── Supplier-level commission ────────────────────────────────────────────────

def get_supplier_commission(supplier_id: int, db: Session) -> dict:
    """Return active commission agreement and full history for a supplier."""
    supplier = db.query(User).filter(User.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    active = (
        db.query(CommissionAgreement)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .first()
    )

    history = (
        db.query(CommissionAgreement)
        .filter(CommissionAgreement.supplier_id == supplier_id)
        .order_by(CommissionAgreement.effective_from.desc())
        .all()
    )

    current_snapshot = _supplier_rate_snapshot(supplier_id, db)

    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.full_name or supplier.username,
        "current_rate": float(current_snapshot.supplier_rate),
        "using_default": active is None,
        "calculation_method": current_snapshot.supplier_rate_source,
        "badge_level": current_snapshot.badge_level,
        "default_base_rate": float(current_snapshot.global_default_rate),
        "combined_default_rate": float(current_snapshot.applied_rate),
        "active_agreement": _serialize_agreement(active) if active else None,
        "history": [_serialize_agreement(a) for a in history],
    }


def set_supplier_commission(
    supplier_id: int,
    rate: float,
    note: Optional[str],
    acting_user: dict,
    db: Session,
) -> dict:
    """
    Set a new supplier-level commission rate.

    Deactivates any previous active agreement, then inserts a new one.
    Rate must be in 0.0–1.0 range (e.g. 0.12 for 12%).
    """
    _require_admin(acting_user)
    if not (0.0 <= rate <= 1.0):
        raise HTTPException(status_code=422, detail="Rate must be between 0.0 and 1.0")

    supplier = db.query(User).filter(User.id == supplier_id, User.role == "supplier").first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    now = datetime.now(timezone.utc)

    # Deactivate previous active agreement
    prev = (
        db.query(CommissionAgreement)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .first()
    )
    if prev:
        prev.is_active = False  # type: ignore[assignment]
        prev.effective_to = now  # type: ignore[assignment]

    new_agreement = CommissionAgreement(
        supplier_id=supplier_id,
        rate=Decimal(str(rate)),
        effective_from=now,
        effective_to=None,
        is_active=True,
        set_by_admin_id=acting_user["id"],
        note=note,
    )
    db.add(new_agreement)
    db.commit()
    db.refresh(new_agreement)

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="commission_agreement",
        resource_id=cast(int, getattr(new_agreement, "id")),
        details={"supplier_id": supplier_id, "new_rate": rate, "note": note},
        status="success",
    )

    return {"message": "Commission rate updated", "agreement_id": new_agreement.id}


def delete_supplier_commission_override(
    supplier_id: int,
    acting_user: dict,
    db: Session,
) -> dict:
    """Remove any active supplier-level commission override and revert to badge/default logic."""
    _require_admin(acting_user)

    active_agreements = (
        db.query(CommissionAgreement)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .order_by(CommissionAgreement.created_at.desc(), CommissionAgreement.id.desc())
        .all()
    )
    if not active_agreements:
        raise HTTPException(status_code=404, detail="No active supplier commission override found")

    deleted_ids = [cast(int, getattr(agreement, "id")) for agreement in active_agreements]
    for agreement in active_agreements:
        db.delete(agreement)
    db.commit()

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="commission_agreement",
        resource_id=supplier_id,
        details={"action": "removed_supplier_override", "supplier_id": supplier_id, "agreement_ids": deleted_ids},
        status="success",
    )

    return {"message": "Supplier commission override removed", "deleted": len(deleted_ids)}


# ── Product-level commission override ────────────────────────────────────────

def get_product_commission_override(product_id: int, db: Session) -> Optional[dict]:
    """Return the active commission override for a product, or None."""
    override = (
        db.query(ProductCommissionOverride)
        .filter(ProductCommissionOverride.product_id == product_id)
        .first()
    )
    return _serialize_override(override) if override else None


def set_product_commission_override(
    product_id: int,
    rate: float,
    note: Optional[str],
    acting_user: dict,
    db: Session,
) -> dict:
    """
    Create or update the product-level commission override.
    Rate must be in 0.0–1.0 range.
    """
    from domains.catalog.ports import Product
    _require_admin(acting_user)
    if not (0.0 <= rate <= 1.0):
        raise HTTPException(status_code=422, detail="Rate must be between 0.0 and 1.0")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(ProductCommissionOverride)
        .filter(ProductCommissionOverride.product_id == product_id)
        .first()
    )

    if existing:
        existing.rate = Decimal(str(rate))  # type: ignore[assignment]
        existing.is_active = True  # type: ignore[assignment]
        existing.set_by_admin_id = acting_user["id"]  # type: ignore[assignment]
        existing.note = note  # type: ignore[assignment]
        existing.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        override_id = existing.id
    else:
        override = ProductCommissionOverride(
            product_id=product_id,
            supplier_id=product.supplier_id,
            rate=Decimal(str(rate)),
            is_active=True,
            set_by_admin_id=acting_user["id"],
            note=note,
        )
        db.add(override)
        db.flush()
        override_id = override.id

    db.commit()

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product_commission_override",
        resource_id=product_id,
        details={"rate": rate, "note": note},
        status="success",
    )

    return {"message": "Product commission override saved", "override_id": override_id}


def delete_product_commission_override(
    product_id: int,
    acting_user: dict,
    db: Session,
) -> dict:
    """Remove the product-level commission override (revert to supplier agreement)."""
    _require_admin(acting_user)

    override = (
        db.query(ProductCommissionOverride)
        .filter(ProductCommissionOverride.product_id == product_id)
        .first()
    )
    if not override:
        raise HTTPException(status_code=404, detail="No commission override found for this product")

    db.delete(override)
    db.commit()

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product_commission_override",
        resource_id=product_id,
        details={"action": "removed"},
        status="success",
    )

    return {"message": "Commission override removed"}


def list_product_commission_overrides(
    db: Session,
    *,
    search: Optional[str] = None,
    supplier_id: Optional[int] = None,
    limit: int = 100,
) -> list[dict]:
    """Return product-level overrides with product and supplier context for admin operations."""
    from domains.catalog.ports import Product
    q = (
        db.query(ProductCommissionOverride, Product, User)
        .join(Product, Product.id == ProductCommissionOverride.product_id)
        .join(User, User.id == ProductCommissionOverride.supplier_id)
        .order_by(ProductCommissionOverride.updated_at.desc(), ProductCommissionOverride.id.desc())
    )

    if supplier_id:
        q = q.filter(ProductCommissionOverride.supplier_id == supplier_id)
    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            (Product.name.ilike(term)) |
            (User.email.ilike(term)) |
            (User.full_name.ilike(term)) |
            (Product.category.ilike(term))
        )

    rows = q.limit(min(limit, 1000)).all()
    return [
        {
            **cast(dict[str, Any], _serialize_override(override)),
            "product_name": getattr(product, "name", None),
            "product_category": getattr(product, "category", None),
            "supplier_name": getattr(supplier, "full_name", None) or getattr(supplier, "username", None),
        }
        for override, product, supplier in rows
    ]


def list_all_supplier_commissions(
    db: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict:
    """Return current commission rate for every active supplier."""
    resolved_limit = 100 if limit is None else max(1, min(limit, 500))
    query = db.query(User).filter(User.role == "supplier", User.is_active == True)  # noqa: E712
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.email.ilike(term), User.full_name.ilike(term), User.email.ilike(term)))
    total = query.count()
    suppliers = (
        query.order_by(User.full_name, User.email, User.id)
        .limit(min(resolved_limit, 1000))
        .all()
    )
    supplier_ids = [cast(int, getattr(supplier, "id")) for supplier in suppliers]
    agreements: dict[int, CommissionAgreement] = {}
    if supplier_ids:
        for agreement in (
            db.query(CommissionAgreement)
            .filter(
                CommissionAgreement.supplier_id.in_(supplier_ids),
                CommissionAgreement.is_active == True,  # noqa: E712
            )
            .order_by(CommissionAgreement.created_at.desc(), CommissionAgreement.id.desc())
            .all()
        ):
            supplier_id = cast(int, getattr(agreement, "supplier_id"))
            agreements.setdefault(supplier_id, agreement)

    results = []
    for s in suppliers:
        active = agreements.get(cast(int, getattr(s, "id")))
        current_snapshot = _supplier_rate_snapshot(cast(int, getattr(s, "id")), db)
        results.append({
            "supplier_id": cast(int, getattr(s, "id")),
            "supplier_name": s.full_name or s.username,
            "current_rate": float(current_snapshot.supplier_rate),
            "using_default": active is None,
            "agreement_id": cast(int, getattr(active, "id")) if active else None,
            "calculation_method": current_snapshot.supplier_rate_source,
            "badge_level": current_snapshot.badge_level,
            "default_base_rate": float(current_snapshot.global_default_rate),
            "combined_default_rate": float(current_snapshot.applied_rate),
        })

    return _build_list_page_payload(results, total, offset=offset, page_size=resolved_limit)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _require_admin(user: dict) -> None:
    if user.get("role") not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required")


def _serialize_agreement(a: CommissionAgreement | None) -> Optional[dict]:
    if a is None:
        return None
    return {
        "id": cast(int, getattr(a, "id")),
        "supplier_id": cast(int, getattr(a, "supplier_id")),
        "rate": float(getattr(a, "rate")),
        "effective_from": getattr(a, "effective_from"),
        "effective_to": getattr(a, "effective_to"),
        "is_active": bool(getattr(a, "is_active")),
        "set_by_admin_id": getattr(a, "set_by_admin_id"),
        "note": getattr(a, "note"),
        "created_at": getattr(a, "created_at"),
    }


def _serialize_override(o: ProductCommissionOverride | None) -> Optional[dict]:
    if o is None:
        return None
    return {
        "id": cast(int, getattr(o, "id")),
        "product_id": cast(int, getattr(o, "product_id")),
        "supplier_id": cast(int, getattr(o, "supplier_id")),
        "rate": float(getattr(o, "rate")),
        "is_active": bool(getattr(o, "is_active")),
        "set_by_admin_id": getattr(o, "set_by_admin_id"),
        "note": getattr(o, "note"),
        "created_at": getattr(o, "created_at"),
        "updated_at": getattr(o, "updated_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Global Config
# ══════════════════════════════════════════════════════════════════════════════

def get_global_config(db: Session) -> dict:
    config = _get_commission_engine().get_global_config(db)
    return _serialize_global_config(config)


def get_supplier_policy_snapshot(current_user: dict, db: Session) -> dict:
    config = get_global_config(db)
    active_categories = [
        row for row in cast(list[dict[str, Any]], list_category_rates(db, limit=500)["data"])
        if bool(row.get("is_active"))
    ]
    active_badge_tiers = [
        row for row in cast(list[dict[str, Any]], list_badge_tiers(db, limit=500)["data"])
        if bool(row.get("is_active"))
    ]

    supplier_id = current_user.get("id") if current_user.get("role") == "supplier" else None
    supplier_rate: Optional[dict[str, Any]] = None
    current_badge_level: Optional[str] = None

    if supplier_id is not None:
        snapshot = _supplier_rate_snapshot(int(supplier_id), db)
        supplier_rate = {
            "current_rate": float(snapshot.supplier_rate),
            "calculation_method": snapshot.supplier_rate_source,
            "badge_level": snapshot.badge_level,
            "using_default": snapshot.supplier_rate_source != "override",
            "combined_default_rate": float(snapshot.applied_rate),
            "default_base_rate": float(snapshot.global_default_rate),
        }
        current_badge_level = snapshot.badge_level

    resolution_order = [
        {
            "order": 1,
            "label": "Product exception",
            "state": "available",
            "detail": "A product-specific base rate replaces the category base rate when a product override exists.",
        },
        {
            "order": 2,
            "label": "Category base rate",
            "state": "available",
            "detail": f"{len(active_categories)} active category rates feed the base commission component when no product exception exists.",
        },
        {
            "order": 3,
            "label": "Supplier commission component",
            "state": "active" if supplier_rate is not None else "available",
            "detail": (
                f"Current supplier component uses {supplier_rate['calculation_method']} with badge {current_badge_level}."
                if current_badge_level and supplier_rate is not None
                else f"{len(active_badge_tiers)} active badge tiers can apply when supplier qualification is met."
            ),
        },
        {
            "order": 4,
            "label": "Guardrails",
            "state": "fallback",
            "detail": "Low-value cap applies after the combined rate is calculated, and margin protection remains an admin guardrail.",
        },
    ]

    return {
        "updated_at": config.get("updated_at"),
        "global_config": config,
        "supplier_rate": supplier_rate,
        "active_categories": [
            {
                "category_slug": row.get("category_slug"),
                "category_display_name": row.get("category_display_name"),
                "rate": row.get("rate"),
                "notes": row.get("notes"),
            }
            for row in active_categories
        ],
        "active_badge_tiers": [
            {
                "badge_level": row.get("badge_level"),
                "commission_rate": row.get("commission_rate"),
                "setup_fee": row.get("setup_fee"),
                "recurring_fee": row.get("recurring_fee"),
                "recurring_interval": row.get("recurring_interval"),
                "min_fulfilled_orders": row.get("min_fulfilled_orders"),
                "min_monthly_revenue": row.get("min_monthly_revenue"),
            }
            for row in active_badge_tiers
        ],
        "resolution_order": resolution_order,
    }


def update_global_config(payload: dict, acting_user: dict, db: Session) -> dict:
    _require_admin(acting_user)
    config = _get_commission_engine().get_global_config(db)

    allowed = {
        "default_rate", "low_value_threshold", "fixed_cap_amount",
        "fixed_cap_enabled", "margin_protection_enabled", "margin_threshold",
    }
    for key, value in payload.items():
        if key not in allowed:
            continue
        if key in {"default_rate", "margin_threshold"} and value is not None:
            if not (0.0 <= float(value) <= 1.0):
                raise HTTPException(status_code=422, detail=f"{key} must be between 0.0 and 1.0")
        normalized = value
        if key in {"default_rate", "low_value_threshold", "fixed_cap_amount", "margin_threshold"}:
            normalized = None if value is None else Decimal(str(value))
        setattr(config, key, normalized)

    setattr(config, "updated_by", acting_user["id"])
    setattr(config, "updated_at", datetime.now(timezone.utc))
    db.commit()
    db.refresh(config)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_global_config",
        resource_id=1, details=payload, status="success",
    )
    return _serialize_global_config(config)


def _serialize_global_config(c: CommissionGlobalConfig) -> dict:
    return {
        "id": cast(int, getattr(c, "id")),
        "default_rate": float(getattr(c, "default_rate")),
        "low_value_threshold": float(getattr(c, "low_value_threshold")),
        "fixed_cap_amount": float(getattr(c, "fixed_cap_amount")),
        "fixed_cap_enabled": bool(getattr(c, "fixed_cap_enabled")),
        "margin_protection_enabled": bool(getattr(c, "margin_protection_enabled")),
        "margin_threshold": _float_or_none(getattr(c, "margin_threshold")),
        "updated_by": getattr(c, "updated_by"),
        "updated_at": getattr(c, "updated_at"),
        "created_at": getattr(c, "created_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Category Rates
# ══════════════════════════════════════════════════════════════════════════════

def list_category_rates(
    db: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict:
    """Return all category rates, seeding defaults on first call."""
    query = db.query(CommissionCategoryRate)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                CommissionCategoryRate.category_slug.ilike(term),
                CommissionCategoryRate.category_display_name.ilike(term),
            )
        )
    rows = query.order_by(CommissionCategoryRate.category_display_name, CommissionCategoryRate.id).all()
    if not rows:
        _get_commission_engine().seed_defaults(db)
        query = db.query(CommissionCategoryRate)
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    CommissionCategoryRate.category_slug.ilike(term),
                    CommissionCategoryRate.category_display_name.ilike(term),
                )
            )
        rows = query.order_by(CommissionCategoryRate.category_display_name, CommissionCategoryRate.id).all()
    total = len(rows)
    resolved_limit = total if limit is None else max(1, min(limit, 500))
    sliced_rows = rows[max(0, offset):max(0, offset) + resolved_limit]
    return _build_list_page_payload([_serialize_category_rate(row) for row in sliced_rows], total, offset=offset, page_size=resolved_limit)


def update_category_rate(
    category_slug: str, payload: dict, acting_user: dict, db: Session
) -> dict:
    _require_admin(acting_user)
    row = db.query(CommissionCategoryRate).filter(
        CommissionCategoryRate.category_slug == category_slug
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Category rate not found: {category_slug}")

    if "rate" in payload:
        r = float(payload["rate"])
        if not (0.0 <= r <= 1.0):
            raise HTTPException(status_code=422, detail="Rate must be between 0.0 and 1.0")
        setattr(row, "rate", Decimal(str(r)))
    if "is_active" in payload:
        setattr(row, "is_active", bool(payload["is_active"]))
    if "notes" in payload:
        setattr(row, "notes", payload["notes"])
    if "category_display_name" in payload:
        setattr(row, "category_display_name", payload["category_display_name"])

    setattr(row, "updated_by", acting_user["id"])
    setattr(row, "updated_at", datetime.now(timezone.utc))
    db.commit()
    db.refresh(row)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_category_rate",
        resource_id=cast(int, getattr(row, "id")), details={"category_slug": category_slug, **payload}, status="success",
    )
    return _serialize_category_rate(row)


def _serialize_category_rate(r: CommissionCategoryRate) -> dict:
    return {
        "id": cast(int, getattr(r, "id")),
        "category_id": getattr(r, "category_id"),
        "category_slug": str(getattr(r, "category_slug")),
        "category_display_name": str(getattr(r, "category_display_name")),
        "rate": float(getattr(r, "rate_percent", 0) or 0),
        "is_active": bool(getattr(r, "is_active")),
        "notes": getattr(r, "notes", None),
        "country_code": getattr(r, "country_code"),
        "created_at": getattr(r, "created_at"),
        "updated_at": getattr(r, "updated_at", None),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Badge Tiers
# ══════════════════════════════════════════════════════════════════════════════

def list_badge_tiers(
    db: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict:
    query = db.query(CommissionBadgeTier)
    if search and search.strip():
        query = query.filter(CommissionBadgeTier.badge_level.ilike(f"%{search.strip()}%"))
    rows = query.order_by(CommissionBadgeTier.sort_order, CommissionBadgeTier.id).all()
    if not rows:
        _get_commission_engine().seed_defaults(db)
        query = db.query(CommissionBadgeTier)
        if search and search.strip():
            query = query.filter(CommissionBadgeTier.badge_level.ilike(f"%{search.strip()}%"))
        rows = query.order_by(CommissionBadgeTier.sort_order, CommissionBadgeTier.id).all()
    total = len(rows)
    resolved_limit = total if limit is None else max(1, min(limit, 500))
    sliced_rows = rows[max(0, offset):max(0, offset) + resolved_limit]
    return _build_list_page_payload([_serialize_badge_tier(row) for row in sliced_rows], total, offset=offset, page_size=resolved_limit)


def update_badge_tier(
    badge_level: str, payload: dict, acting_user: dict, db: Session
) -> dict:
    _require_admin(acting_user)
    row = db.query(CommissionBadgeTier).filter(
        CommissionBadgeTier.badge_level == badge_level
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Badge tier not found: {badge_level}")

    if "commission_rate" in payload:
        r = float(payload["commission_rate"])
        if not (0.0 <= r <= 1.0):
            raise HTTPException(status_code=422, detail="commission_rate must be between 0.0 and 1.0")
        setattr(row, "commission_rate", Decimal(str(r)))
    for field in ("setup_fee", "recurring_fee"):
        if field in payload:
            if float(payload[field]) < 0:
                raise HTTPException(status_code=422, detail=f"{field} must be >= 0")
            setattr(row, field, Decimal(str(payload[field])))
    for field in ("recurring_interval", "benefits_json", "is_active", "sort_order",
                  "min_fulfilled_orders"):
        if field in payload:
            setattr(row, field, payload[field])
    if "min_monthly_revenue" in payload:
        setattr(
            row,
            "min_monthly_revenue",
            None if payload["min_monthly_revenue"] is None else Decimal(str(payload["min_monthly_revenue"])),
        )

    setattr(row, "updated_by", acting_user["id"])
    setattr(row, "updated_at", datetime.now(timezone.utc))
    db.commit()
    db.refresh(row)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_badge_tier",
        resource_id=cast(int, getattr(row, "id")), details={"badge_level": badge_level, **payload}, status="success",
    )
    return _serialize_badge_tier(row)


def _serialize_badge_tier(t: CommissionBadgeTier) -> dict:
    import json as _json
    benefits = None
    raw_benefits = getattr(t, "benefits_json")
    if raw_benefits not in (None, ""):
        try:
            benefits = _json.loads(str(raw_benefits))
        except Exception:
            benefits = raw_benefits
    return {
        "id": cast(int, getattr(t, "id")),
        "badge_level": str(getattr(t, "badge_level")),
        "commission_rate": float(getattr(t, "commission_rate")),
        "setup_fee": float(getattr(t, "setup_fee")),
        "recurring_fee": float(getattr(t, "recurring_fee")),
        "recurring_interval": getattr(t, "recurring_interval"),
        "benefits": benefits,
        "min_fulfilled_orders": getattr(t, "min_fulfilled_orders"),
        "min_monthly_revenue": _float_or_none(getattr(t, "min_monthly_revenue")),
        "sort_order": getattr(t, "sort_order"),
        "is_active": bool(getattr(t, "is_active")),
        "updated_by": getattr(t, "updated_by"),
        "created_at": getattr(t, "created_at"),
        "updated_at": getattr(t, "updated_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Ledger
# ══════════════════════════════════════════════════════════════════════════════

def list_ledger_entries(
    db: Session,
    supplier_id: Optional[int] = None,
    order_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(CommissionLedgerEntry)
    if supplier_id:
        q = q.filter(CommissionLedgerEntry.supplier_id == supplier_id)
    if order_id:
        q = q.filter(CommissionLedgerEntry.order_id == order_id)
    total = q.count()
    rows = q.order_by(CommissionLedgerEntry.created_at.desc()).limit(limit).all()
    return {"total": total, "items": [_serialize_ledger_entry(e) for e in rows]}


def create_ledger_adjustment(
    ledger_id: int, new_amount: float, reason: str, acting_user: dict, db: Session
) -> dict:
    """Create an adjustment entry when a dispute is resolved."""
    _require_admin(acting_user)
    original = db.query(CommissionLedgerEntry).filter(CommissionLedgerEntry.id == ledger_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    if bool(getattr(original, "is_adjusted")):
        raise HTTPException(status_code=409, detail="Entry already adjusted")

    now = datetime.now(timezone.utc)
    setattr(original, "is_adjusted", True)
    setattr(original, "adjusted_by", acting_user["id"])
    setattr(original, "adjusted_at", now)
    setattr(original, "adjustment_reason", reason)
    setattr(original, "original_commission_amount", getattr(original, "commission_amount"))
    setattr(original, "commission_amount", Decimal(str(new_amount)))
    db.commit()
    db.refresh(original)

    audit_log(
        db=db, action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"], username=acting_user.get("username"),
        user_role=acting_user.get("role"), resource_type="commission_ledger_entry",
        resource_id=ledger_id,
        details={"new_amount": new_amount, "reason": reason},
        status="success",
    )
    return _serialize_ledger_entry(original)


def _serialize_ledger_entry(e: CommissionLedgerEntry) -> dict:
    return {
        "id": cast(int, getattr(e, "id")),
        "order_id": cast(int, getattr(e, "order_id")),
        "order_item_id": getattr(e, "order_item_id"),
        "supplier_id": cast(int, getattr(e, "supplier_id")),
        "product_id": getattr(e, "product_id"),
        "category_slug": getattr(e, "category_slug"),
        "badge_level": getattr(e, "badge_level"),
        "global_default_rate": _float_or_none(getattr(e, "global_default_rate")),
        "category_rate": _float_or_none(getattr(e, "category_rate")),
        "badge_rate": _float_or_none(getattr(e, "badge_rate")),
        "override_rate": _float_or_none(getattr(e, "override_rate")),
        "applied_rate": float(getattr(e, "applied_rate")),
        "calculation_method": str(getattr(e, "calculation_method")),
        "order_value": float(getattr(e, "order_value")),
        "commission_pct": float(getattr(e, "commission_pct")),
        "cap_applied": bool(getattr(e, "cap_applied")),
        "commission_amount": float(getattr(e, "commission_amount")),
        "low_value_threshold_used": _float_or_none(getattr(e, "low_value_threshold_used")),
        "fixed_cap_used": _float_or_none(getattr(e, "fixed_cap_used")),
        "override_flag": bool(getattr(e, "override_flag")),
        "is_adjusted": bool(getattr(e, "is_adjusted")),
        "adjusted_by": getattr(e, "adjusted_by"),
        "adjusted_at": getattr(e, "adjusted_at", getattr(e, "created_at", None)),
        "adjustment_reason": getattr(e, "adjustment_reason", None),
        "original_commission_amount": _float_or_none(getattr(e, "original_commission_amount", getattr(e, "amount", None))),
        "currency": str(getattr(e, "currency")),
        "created_at": getattr(e, "created_at"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Commission Engine — Preview Calculator (no DB writes)
# ══════════════════════════════════════════════════════════════════════════════

def preview_commission(
    supplier_id: int,
    order_value: float,
    category_slug: Optional[str],
    db: Session,
) -> dict:
    return _get_commission_engine().preview_commission(
        supplier_id=supplier_id,
        order_value=order_value,
        category_slug=category_slug,
        db=db,
    )

# === Merged from accounts/services/commission_service.py ===

class BadgeTierBody(BaseModel):

    commission_rate: Optional[float] = Field(None, ge=0.0, le=1.0)

    setup_fee: Optional[float] = Field(None, ge=0.0)

    recurring_fee: Optional[float] = Field(None, ge=0.0)

    recurring_interval: Optional[str] = Field(None, max_length=20)

    benefits_json: Optional[str] = None

    min_fulfilled_orders: Optional[int] = None

    min_monthly_revenue: Optional[float] = None

    sort_order: Optional[int] = None

    is_active: Optional[bool] = None




class CategoryRateBody(BaseModel):

    rate: Optional[float] = Field(None, ge=0.0, le=1.0)

    is_active: Optional[bool] = None

    notes: Optional[str] = Field(None, max_length=500)

    category_display_name: Optional[str] = Field(None, max_length=150)




class CommissionRateBody(BaseModel):

    rate: float = Field(..., ge=0.0, le=1.0, description="Commission rate as decimal, e.g. 0.12 for 12%")

    note: Optional[str] = Field(None, max_length=500)




class GlobalConfigBody(BaseModel):

    default_rate: Optional[float] = Field(None, ge=0.0, le=1.0)

    low_value_threshold: Optional[float] = Field(None, ge=0.0)

    fixed_cap_amount: Optional[float] = Field(None, ge=0.0)

    fixed_cap_enabled: Optional[bool] = None

    margin_protection_enabled: Optional[bool] = None

    margin_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)




class LedgerAdjustmentBody(BaseModel):

    new_amount: float = Field(..., ge=0.0)

    reason: str = Field(..., min_length=5, max_length=1000)




class PreviewBody(BaseModel):

    supplier_id: int

    order_value: float = Field(..., gt=0.0)

    category_slug: Optional[str] = None




def adjust_ledger_entry(ledger_id: int, body: LedgerAdjustmentBody, db: Session, current_user: dict):

    return commission_controller.create_ledger_adjustment(

        ledger_id=ledger_id,

        new_amount=body.new_amount,

        reason=body.reason,

        acting_user=current_user,

        db=db,

    )




def list_supplier_commissions(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):

    return commission_controller.list_all_supplier_commissions(db, limit=page_size, offset=(page - 1) * page_size, search=search)

# === MERGED from commission_admin_write_service.py ===

"""Country-scoped commission admin write service.

Owns DB writes for the admin commission management router
(`backend/routers/admin_commission.py`). Kept independent of the legacy
`services.finance.commission_write_service` re-export shim to avoid the
controller<->service circular import in that module.

Functions are db-param (the session is passed in by the calling controller),
per the backend grid-line contract: routers/controllers must not issue
`db.add`/`db.commit` directly (W1).
"""

from typing import Optional

from sqlalchemy.orm import Session

from domains.finance.models.commission import CommissionCategoryRate
from domains.governance.models.admin import CommissionBadgeTier
# TODO: commission_write_service not yet created`n# # TODO: Module not yet created
# from domains.finance.services.commission.commission_write_service import apply_changes
import structlog
logger = structlog.get_logger(__name__)


def create_commission_category_rate(payload: dict, country_code: str, db: Session) -> CommissionCategoryRate:
    data = payload or {}
    rate = CommissionCategoryRate(
        category_id=data.get("category_id"),
        category_slug=data.get("category_slug"),
        category_display_name=data.get("category_display_name"),
        rate_percent=data.get("rate", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def update_commission_category_rate_by_id(
    rate_id: int, country_code: str, payload: dict, db: Session
) -> Optional[CommissionCategoryRate]:
    data = payload or {}
    rate = (
        db.query(CommissionCategoryRate)
        .filter(
            CommissionCategoryRate.id == rate_id,
            CommissionCategoryRate.country_code == country_code.upper(),
        )
        .first()
    )
    if rate is None:
        return None
    changes = dict(data)
    if "rate" in changes:
        changes["rate_percent"] = changes.pop("rate")
    _apply_changes(rate, changes)
    db.commit()
    db.refresh(rate)
    return rate


def create_commission_badge_tier(payload: dict, country_code: str, db: Session) -> CommissionBadgeTier:
    data = payload or {}
    tier = CommissionBadgeTier(
        badge_level=data.get("badge_level"),
        commission_rate=data.get("commission_rate", 0),
        min_fulfilled_orders=data.get("min_fulfilled_orders", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def update_commission_badge_tier_by_id(
    tier_id: int, country_code: str, payload: dict, db: Session
) -> Optional[CommissionBadgeTier]:
    data = payload or {}
    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.id == tier_id,
            CommissionBadgeTier.country_code == country_code.upper(),
        )
        .first()
    )
    if tier is None:
        return None
    _apply_changes(tier, data)
    db.commit()
    db.refresh(tier)
    return tier

# === MERGED from commission_write_service.py ===

"""Commission write operations (canonical module).

Implements the commission domain write surface. Previously stubbed with
``_missing_symbol`` placeholders after a refactor; now contains the real
DB-write logic, consistent with the platform contract (``data.models``,
soft-delete via ``infrastructure.utils.soft_delete``).
"""

from sqlalchemy.orm import Session

from domains.finance.models.commission import CommissionAgreement
from domains.finance.models.commission import CommissionCategoryRate
from domains.finance.models.commission import CommissionLedgerEntry
from domains.finance.models.commission import ProductCommissionOverride
from domains.governance.models.admin import CommissionBadgeTier
from domains.governance.models.admin import CommissionGlobalConfig
from infrastructure.utils.soft_delete import soft_delete
import structlog
logger = structlog.get_logger(__name__)


def apply_changes(record, changes: dict) -> None:
    for key, value in changes.items():
        if value is not None:
            setattr(record, key, value)


def _resolve_and_update(db: Session, model, record_or_id, changes, label: str):
    """Update ``record_or_id`` (an ORM instance or its integer id) with ``changes``.

    Accepts both the keyword form (``rate_id=..., **changes``) used by some
    callers and the positional form (``row, updates``) used by the controllers.
    """
    merged = dict(changes or {})
    if isinstance(record_or_id, int):
        obj = db.get(model, record_or_id)
    else:
        obj = record_or_id
    if obj is None:
        raise ValueError(f"{label} {record_or_id} not found")
    apply_changes(obj, merged)
    db.commit()
    db.refresh(obj)
    return obj


def create_commission_agreement(
    db: Session,
    *,
    supplier_id: int,
    tier: str,
    rate: float,
    country_code: str | None = None,
    set_by_admin_id: int | None = None,
    is_active: bool = True,
    effective_from=None,
    effective_to=None,
    note: str | None = None,
) -> CommissionAgreement:
    obj = CommissionAgreement(
        supplier_id=supplier_id,
        tier=tier,
        rate=rate,
        country_code=country_code,
        set_by_admin_id=set_by_admin_id,
        is_active=is_active,
        effective_from=effective_from,
        effective_to=effective_to,
        note=note,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_product_commission_override(
    db: Session,
    *,
    product_id: int,
    supplier_id: int,
    rate_percent: float,
    set_by_admin_id: int | None = None,
    is_active: bool = True,
    country_code: str | None = None,
) -> ProductCommissionOverride:
    obj = ProductCommissionOverride(
        product_id=product_id,
        supplier_id=supplier_id,
        rate_percent=rate_percent,
        set_by_admin_id=set_by_admin_id,
        is_active=is_active,
        country_code=country_code,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_commission_badge_tier(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionBadgeTier:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionBadgeTier, record_or_id, merged, "CommissionBadgeTier")


def update_commission_category_rate(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionCategoryRate:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionCategoryRate, record_or_id, merged, "CommissionCategoryRate")


def update_commission_global_config(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionGlobalConfig:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionGlobalConfig, record_or_id, merged, "CommissionGlobalConfig")


def update_commission_ledger_entry(db: Session, record_or_id, changes: dict | None = None, **kw) -> CommissionLedgerEntry:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, CommissionLedgerEntry, record_or_id, merged, "CommissionLedgerEntry")


def update_product_commission_override(db: Session, record_or_id, changes: dict | None = None, **kw) -> ProductCommissionOverride:
    merged = dict(changes or {})
    merged.update(kw)
    return _resolve_and_update(db, ProductCommissionOverride, record_or_id, merged, "ProductCommissionOverride")


def delete_product_commission_override(db: Session, override: ProductCommissionOverride) -> None:
    """Hard-delete a product-level commission override (revert to supplier agreement)."""
    db.delete(override)
    db.commit()


def delete_commission_agreement(db: Session, agreement_id: int, acting_user: int | None = None, reason: str | None = None) -> None:
    soft_delete(db, CommissionAgreement, agreement_id, acting_user, reason=reason)

# === MERGED from commission_geography_service.py ===

"""Country-scoped commission (category rate + badge tier) read/write operations.

Owns the DB reads/writes for ``admin_finance_geography`` so the router stays
free of ``db.query``/``db.add``/``db.commit``.
"""

from sqlalchemy.orm import Session

from domains.finance.models.commission import CommissionCategoryRate
from domains.governance.models.admin import CommissionBadgeTier
import structlog
logger = structlog.get_logger(__name__)


class FinanceDomainError(Exception):
    """Domain-level error for finance operations. Routers map this to HTTP responses."""
    pass


def build_category_rate(payload, country_code: str) -> CommissionCategoryRate:
    data = payload.model_dump() if payload else {}
    return CommissionCategoryRate(
        category_id=data.get("category_id"),
        category_slug=data.get("category_slug"),
        category_display_name=data.get("category_display_name"),
        rate_percent=data.get("rate", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )


def build_badge_tier(payload, country_code: str) -> CommissionBadgeTier:
    data = payload.model_dump() if payload else {}
    return CommissionBadgeTier(
        badge_level=data.get("badge_level"),
        commission_rate=data.get("commission_rate", 0),
        min_fulfilled_orders=data.get("min_fulfilled_orders", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )


def list_category_rates(db: Session, country_code: str, page: int, page_size: int) -> dict:
    q = db.query(CommissionCategoryRate).filter(CommissionCategoryRate.country_code == country_code.upper())
    total = q.count()
    rows = q.order_by(CommissionCategoryRate.id.desc()).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def create_category_rate(db: Session, payload, country_code: str) -> CommissionCategoryRate:
    r = build_category_rate(payload, country_code)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_category_rate(db: Session, rate_id: int, country_code: str, payload) -> CommissionCategoryRate:
    r = (
        db.query(CommissionCategoryRate)
        .filter(CommissionCategoryRate.id == rate_id, CommissionCategoryRate.country_code == country_code.upper())
        .first()
    )
    if not r:
        raise FinanceDomainError("Category rate not found")
    data = payload.model_dump() if payload else {}
    r.category_id = data.get("category_id", r.category_id)
    r.category_slug = data.get("category_slug", r.category_slug)
    r.category_display_name = data.get("category_display_name", r.category_display_name)
    if "rate" in data:
        r.rate_percent = data["rate"]
    r.is_active = data.get("is_active", r.is_active)
    db.commit()
    db.refresh(r)
    return r


def list_badge_tiers(db: Session, country_code: str, page: int, page_size: int) -> dict:
    q = db.query(CommissionBadgeTier).filter(CommissionBadgeTier.country_code == country_code.upper())
    total = q.count()
    rows = q.order_by(CommissionBadgeTier.sort_order.asc()).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def create_badge_tier(db: Session, payload, country_code: str) -> CommissionBadgeTier:
    t = build_badge_tier(payload, country_code)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def update_badge_tier(db: Session, tier_id: int, country_code: str, payload) -> CommissionBadgeTier:
    t = (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.id == tier_id, CommissionBadgeTier.country_code == country_code.upper())
        .first()
    )
    if not t:
        raise FinanceDomainError("Badge tier not found")
    data = payload.model_dump() if payload else {}
    t.badge_level = data.get("badge_level", t.badge_level)
    t.commission_rate = data.get("commission_rate", t.commission_rate)
    t.min_fulfilled_orders = data.get("min_fulfilled_orders", t.min_fulfilled_orders)
    t.is_active = data.get("is_active", t.is_active)
    db.commit()
    db.refresh(t)
    return t

# === MERGED from supplier_finance_service.py ===

"""
Supplier Finance Service
=======================
Read/write helpers for supplier payment-status and payout-status endpoints.

This module owns the DB work that previously lived in ``routers/supplier/
supplier_finance.py`` so the router stays a thin delegator (layering: LC1/W1).

Integrates with:
  - ``SupplierSettlement`` — per-order settlement record
  - ``LogisticsSettlement`` — per-order logistics settlement
  - ``Payout`` — actual payout to supplier bank account
  - ``TransactionLedger`` — detailed financial breakdown
  - ``SupplierBankAccount`` — linked bank account for payouts
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import TransactionLedger
from domains.accounts.models.banking import SupplierBankAccount
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.finance.models.payments import Payout
from infrastructure.utils.pagination import cursor_paginate_desc
# TODO: comms utility not yet created`n# # TODO: Module not yet created
# from domains.comms.services.utility.write_helpers import add_and_flush
# TODO: Module not yet created
# from domains.comms.services.utility.write_helpers import commit_and_refresh
import structlog
logger = structlog.get_logger(__name__)


def _get_user_id(current_user) -> int:
    """Normalise current_user to an int ID (supports both dict and ORM)."""
    if isinstance(current_user, dict):
        uid = current_user.get("id") or current_user.get("user_id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid user session")
        return int(uid)
    return current_user.id


def _payout_eligible_at(completed_at) -> Optional["datetime"]:  # noqa: F821
    """Return the date when payout becomes eligible (10 days after completion)."""
    from datetime import timedelta

    if not completed_at:
        return None
    return completed_at + timedelta(days=10)


def get_payout_summary(db: Session, current_user, skip: int = 0, limit: int = 20) -> dict:
    """Return aggregate payout stats for the supplier dashboard."""
    user_id = _get_user_id(current_user)

    pending_settlements = (
        db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.status.in_(["pending", "eligible"]),
        )
        .limit(limit)
        .all()
    )
    total_pending = sum(float(s.net_amount or 0) for s in pending_settlements)

    paid_payouts = (
        db.query(Payout)
        .filter(
            Payout.user_id == user_id,
            Payout.status == "completed",
        )
        .limit(limit)
        .all()
    )
    total_paid = sum(float(p.amount or 0) for p in paid_payouts)

    bank_account = (
        db.query(SupplierBankAccount)
        .filter(
            SupplierBankAccount.supplier_id == user_id,
            SupplierBankAccount.is_active == True,
        )
        .first()
    )

    return {
        "total_pending_payout": round(total_pending, 3),
        "total_paid_out": round(total_paid, 3),
        "pending_count": len(pending_settlements),
        "paid_count": len(paid_payouts),
        "bank_account_configured": bank_account is not None,
        "bank_account_verified": bool(bank_account and bank_account.verification_status == "verified"),
        "bank_account": {
            "bank_name": bank_account.bank_name if bank_account else None,
            "beneficiary_name": bank_account.beneficiary_name if bank_account else None,
            "iban_last4": bank_account.iban[-4:] if bank_account and bank_account.iban else None,
            "currency": bank_account.currency if bank_account else None,
        } if bank_account else None,
    }


def get_order_payment_status(db: Session, current_user, order_id: int) -> dict:
    """Return detailed payment + payout status for a single order."""
    from datetime import datetime, timezone

    user_id = _get_user_id(current_user)

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")

    settlement = (
        db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.order_id == order_id,
        )
        .first()
    )

    payout = None
    if settlement and settlement.payout_id:
        payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first()

    ledger = (
        db.query(TransactionLedger)
        .filter(
            TransactionLedger.order_id == order_id,
            TransactionLedger.supplier_id == user_id,
        )
        .first()
    )

    completed_at = getattr(order, "completed_at", None) or getattr(order, "delivered_at", None)
    eligible_at = _payout_eligible_at(completed_at)
    now = datetime.now(timezone.utc)
    days_until_eligible = None
    if eligible_at and eligible_at > now:
        days_until_eligible = (eligible_at - now).days

    return {
        "order_id": order.id,
        "order_number": getattr(order, "order_number", f"ORD-{order.id}"),
        "order_status": order.status,
        "payment_method": getattr(order, "payment_method", "unknown"),
        "payment_status": getattr(order, "payment_status", "unpaid"),
        "total_amount": float(order.total or 0),
        "completed_at": completed_at.isoformat() if completed_at else None,
        "settlement": {
            "id": settlement.id if settlement else None,
            "gross_amount": float(settlement.gross_amount) if settlement else None,
            "commission_amount": float(settlement.commission_amount) if settlement else None,
            "vat_amount": float(getattr(settlement, "vat_on_commission", 0) or 0),
            "net_amount": float(settlement.net_amount) if settlement else None,
            "status": settlement.status if settlement else "not_settled",
            "eligible_at": settlement.eligible_at.isoformat() if settlement and settlement.eligible_at else eligible_at.isoformat() if eligible_at else None,
            "created_at": settlement.created_at.isoformat() if settlement else None,
        } if settlement else None,
        "payout": {
            "id": payout.id if payout else None,
            "amount": float(payout.amount) if payout else None,
            "status": payout.status if payout else "not_initiated",
            "created_at": payout.created_at.isoformat() if payout else None,
            "completed_at": payout.completed_at.isoformat() if payout and hasattr(payout, "completed_at") and payout.completed_at else None,
        } if payout else None,
        "payout_eligibility": {
            "eligible_at": eligible_at.isoformat() if eligible_at else None,
            "days_remaining": days_until_eligible if days_until_eligible is not None else 0,
            "is_eligible": eligible_at is not None and now >= eligible_at if eligible_at else False,
            "hold_days": 10,
        },
        "financial_breakdown": {
            "product_subtotal": float(ledger.product_subtotal) if ledger and ledger.product_subtotal else 0,
            "discount_amount": float(ledger.discount_amount) if ledger and ledger.discount_amount else 0,
            "delivery_pickup_charge": float(ledger.delivery_pickup_charge) if ledger and ledger.delivery_pickup_charge else 0,
            "delivery_dropoff_charge": float(ledger.delivery_dropoff_charge) if ledger and ledger.delivery_dropoff_charge else 0,
            "vat_amount": float(ledger.vat_amount) if ledger and ledger.vat_amount else 0,
            "zozi_commission": float(ledger.zozi_commission) if ledger and ledger.zozi_commission else 0,
            "net_supplier_amount": float(ledger.net_supplier_amount) if ledger and ledger.net_supplier_amount else 0,
        } if ledger else None,
    }


def list_orders_with_payout_status(
    db: Session,
    current_user,
    cursor: Optional[str] = None,
    limit: int = 20,
    status_filter: Optional[str] = None,
):
    """Return all orders for this supplier with their payment + payout status."""
    from datetime import datetime, timezone

    user_id = _get_user_id(current_user)

    base = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == user_id)
        .distinct()
    )

    page = cursor_paginate_desc(base.order_by(Order.id.desc()), cursor=cursor, page_size=limit)

    orders = page.items

    order_ids = [o.id for o in orders]
    settlements = {
        s.order_id: s
        for s in db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.order_id.in_(order_ids),
        )
        .limit(SAFE_QUERY_LIMIT).all()
    }
    payout_ids = [s.payout_id for s in settlements.values() if s.payout_id]
    payouts = {
        p.id: p
        for p in db.query(Payout)
        .filter(Payout.id.in_(payout_ids))
        .limit(SAFE_QUERY_LIMIT).all()
    } if payout_ids else {}

    now = datetime.now(timezone.utc)

    items = []
    for order in orders:
        settlement = settlements.get(order.id)
        payout = payouts.get(settlement.payout_id) if settlement and settlement.payout_id else None

        completed_at = getattr(order, "completed_at", None) or getattr(order, "delivered_at", None)
        eligible_at = _payout_eligible_at(completed_at)

        items.append({
            "order_id": order.id,
            "order_number": getattr(order, "order_number", f"ORD-{order.id}"),
            "order_status": order.status,
            "payment_method": getattr(order, "payment_method", "unknown"),
            "payment_status": getattr(order, "payment_status", "unpaid"),
            "total_amount": float(order.total or 0),
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
            "settlement_status": settlement.status if settlement else "not_settled",
            "settlement_net_amount": float(settlement.net_amount) if settlement else None,
            "payout_status": payout.status if payout else ("pending_settlement" if settlement else "not_settled"),
            "payout_amount": float(payout.amount) if payout else None,
            "payout_eligible_at": eligible_at.isoformat() if eligible_at else None,
            "payout_days_remaining": max(0, (eligible_at - now).days) if eligible_at and eligible_at > now else 0,
        })

    if status_filter:
        items = [i for i in items if i.get("settlement_status") == status_filter or i.get("payout_status") == status_filter]

    page.items = items
    return page


def get_bank_account(db: Session, current_user) -> dict:
    """Return the supplier's bank account details."""
    user_id = _get_user_id(current_user)
    account = (
        db.query(SupplierBankAccount)
        .filter(
            SupplierBankAccount.supplier_id == user_id,
            SupplierBankAccount.is_active == True,
        )
        .first()
    )
    if not account:
        return {"configured": False, "account": None}
    return {
        "configured": True,
        "account": {
            "id": account.id,
            "bank_name": account.bank_name,
            "beneficiary_name": account.beneficiary_name,
            "account_number": f"****{account.account_number[-4:]}" if account.account_number else None,
            "iban": f"****{account.iban[-4:]}" if account.iban else None,
            "swift_code": account.swift_code,
            "currency": account.currency,
            "bank_country": account.bank_country,
            "verification_status": account.verification_status,
            "is_active": account.is_active,
        },
    }


def upsert_bank_account(db: Session, current_user, payload: dict) -> dict:
    """Create or update the supplier's bank account."""
    user_id = _get_user_id(current_user)

    account = (
        db.query(SupplierBankAccount)
        .filter(SupplierBankAccount.supplier_id == user_id)
        .first()
    )

    if not account:
        account = SupplierBankAccount(supplier_id=user_id)
        add_and_flush(db, account)

    for field in ["bank_name", "beneficiary_name", "account_number", "iban",
                  "swift_code", "routing_number", "branch_name", "currency", "bank_country"]:
        if field in payload:
            setattr(account, field, str(payload[field]).strip())

    account.is_active = True
    commit_and_refresh(db, account)

    return {
        "status": "success",
        "message": "Bank account updated",
        "verification_status": account.verification_status,
    }

# === Merged from accounts/services/supplier_finance_service.py ===

def get_supplier_bank_account(current_user: User, db: Session):

    """Return the supplier's bank account details."""

    user_id = _get_user_id(current_user)

    account = (

        db.query(SupplierBankAccount)

        .filter(

            SupplierBankAccount.supplier_id == user_id,

            SupplierBankAccount.is_active == True,

        )

        .first()

    )

    if not account:

        return {"configured": False, "account": None}

    return {

        "configured": True,

        "account": {

            "id": account.id,

            "bank_name": account.bank_name,

            "beneficiary_name": account.beneficiary_name,

            "account_number": f"****{account.account_number[-4:]}" if account.account_number else None,

            "iban": f"****{account.iban[-4:]}" if account.iban else None,

            "swift_code": account.swift_code,

            "currency": account.currency,

            "bank_country": account.bank_country,

            "verification_status": account.verification_status,

            "is_active": account.is_active,

        },

    }




def get_supplier_payout_summary(current_user: User, db: Session):

    """Return aggregate payout stats for the supplier dashboard."""

    user_id = _get_user_id(current_user)



    # Total pending payout amount (completed orders not yet paid out)

    pending_settlements = (

        db.query(SupplierSettlement)

        .filter(

            SupplierSettlement.supplier_id == user_id,

            SupplierSettlement.status.in_(["pending", "eligible"]),

        )

        .all()

    )

    total_pending = sum(float(s.net_amount or 0) for s in pending_settlements)



    # Total paid out

    paid_payouts = (

        db.query(Payout)

        .filter(

            Payout.user_id == user_id,

            Payout.status == "completed",

        )

        .all()

    )

    total_paid = sum(float(p.amount or 0) for p in paid_payouts)



    # Bank account status

    bank_account = (

        db.query(SupplierBankAccount)

        .filter(

            SupplierBankAccount.supplier_id == user_id,

            SupplierBankAccount.is_active == True,

        )

        .first()

    )



    return {

        "total_pending_payout": round(total_pending, 3),

        "total_paid_out": round(total_paid, 3),

        "pending_count": len(pending_settlements),

        "paid_count": len(paid_payouts),

        "bank_account_configured": bank_account is not None,

        "bank_account_verified": bool(bank_account and bank_account.verification_status == "verified"),

        "bank_account": {

            "bank_name": bank_account.bank_name if bank_account else None,

            "beneficiary_name": bank_account.beneficiary_name if bank_account else None,

            "iban_last4": bank_account.iban[-4:] if bank_account and bank_account.iban else None,

            "currency": bank_account.currency if bank_account else None,

        } if bank_account else None,

    }




def list_supplier_orders_with_payout_status(page: int, page_size: int, status_filter: Optional[str], current_user: User, db: Session):

    """Return all orders for this supplier with their payment + payout status.



    Used by the supplier panel payout page and order page to show:

      - Which orders are paid / unpaid

      - Which payouts are completed / pending

      - Settlement details for each order

    """

    user_id = _get_user_id(current_user)



    # Base query: orders with items for this supplier
    base = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == user_id)
        .distinct()
    )
    total = base.count()

    orders = (
        base
        .order_by(desc(Order.created_at))
        .limit(page_size)
        .all()
    )



    # Collect settlement + payout data for these orders

    order_ids = [o.id for o in orders]

    settlements = {

        s.order_id: s

        for s in db.query(SupplierSettlement)

        .filter(

            SupplierSettlement.supplier_id == user_id,

            SupplierSettlement.order_id.in_(order_ids),

        )

        .all()

    }

    payout_ids = [s.payout_id for s in settlements.values() if s.payout_id]

    payouts = {

        p.id: p

        for p in db.query(Payout)

        .filter(Payout.id.in_(payout_ids))

        .all()

    } if payout_ids else {}



    now = datetime.now(timezone.utc)



    items = []

    for order in orders:

        settlement = settlements.get(order.id)

        payout = payouts.get(settlement.payout_id) if settlement and settlement.payout_id else None



        completed_at = getattr(order, "completed_at", None) or getattr(order, "delivered_at", None)

        eligible_at = _payout_eligible_at(completed_at)



        items.append({

            "order_id": order.id,

            "order_number": getattr(order, "order_number", f"ORD-{order.id}"),

            "order_status": order.status,

            "payment_method": getattr(order, "payment_method", "unknown"),

            "payment_status": getattr(order, "payment_status", "unpaid"),

            "total_amount": float(order.total or 0),

            "created_at": order.created_at.isoformat() if order.created_at else None,

            "completed_at": completed_at.isoformat() if completed_at else None,

            "settlement_status": settlement.status if settlement else "not_settled",

            "settlement_net_amount": float(settlement.net_amount) if settlement else None,

            "payout_status": payout.status if payout else ("pending_settlement" if settlement else "not_settled"),

            "payout_amount": float(payout.amount) if payout else None,

            "payout_eligible_at": eligible_at.isoformat() if eligible_at else None,

            "payout_days_remaining": max(0, (eligible_at - now).days) if eligible_at and eligible_at > now else 0,

        })



    # Apply client-side filter if status_filter set

    if status_filter:

        items = [i for i in items if i.get("settlement_status") == status_filter or i.get("payout_status") == status_filter]



    return {

        "data": items,

        "total": len(orders),

        "page": page,

        "page_size": page_size,

        "filters_applied": bool(status_filter),

    }




def upsert_supplier_bank_account(payload: dict, current_user: User, db: Session):

    """Create or update the supplier's bank account."""

    user_id = _get_user_id(current_user)



    account = (

        db.query(SupplierBankAccount)

        .filter(SupplierBankAccount.supplier_id == user_id)

        .first()

    )



    if not account:

        account = SupplierBankAccount(supplier_id=user_id)

        db.add(account)



    # Update fields from payload

    for field in ["bank_name", "beneficiary_name", "account_number", "iban",

                  "swift_code", "routing_number", "branch_name", "currency", "bank_country"]:

        if field in payload:

            setattr(account, field, str(payload[field]).strip())



    account.is_active = True

    db.commit()

    db.refresh(account)



    return {

        "status": "success",

        "message": "Bank account updated",

        "verification_status": account.verification_status,

    }

# === MERGED from supplier_payouts_service.py ===

"""Auto-migrated service logic from routers/supplier_payouts.py."""

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import PayoutOut

from domains.governance.ports import User
from domains.comms.models.suppliers import SupplierProfile
from domains.finance.models.payments import Payout

from infrastructure.utils.dependencies import require_supplier

def list_payouts(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404)
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier.id)
        .order_by(Payout.created_at.desc())
        .all()
    )

def request_payout(payload: dict, current_user: User, db: Session):
    """Create a payout request from the supplier.

    Body:
      amount (float): Payout amount
      method (str, optional): Payment method, default "bank"
      notes (str, optional): Supplier notes
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")

    amount = payload.get("amount")
    if not amount or float(amount) <= 0:
        raise HTTPException(400, "A positive payout amount is required")

    payout = Payout(
        supplier_id=supplier.id,
        amount=float(amount),
        method=payload.get("method", "bank"),
        notes=payload.get("notes", "Supplier-initiated payout request"),
        status="pending",
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return {"status": "success", "payout": {"id": payout.id, "amount": float(payout.amount), "status": payout.status}}

# === MERGED from admin_finance_geography_service.py ===

"""Auto-migrated service logic from routers/admin_finance_geography.py."""

from fastapi import Depends, Path, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.accounts.models.user import User

from infrastructure.database.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context

# Lazy import: create_badge_tier
# Lazy import: create_category_rate
# Lazy import: list_badge_tiers
# Lazy import: list_category_rates
# Lazy import: update_badge_tier
# Lazy import: update_category_rate

def list_rates(country_code: str, _: User, db: Session, page: int, page_size: int):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_category_rates(db, country_code, page, page_size)
    finally:
        clear_rls_context()

def create_rate(country_code: str, payload: CommissionCategoryRateCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_category_rate(db, payload, country_code)
    finally:
        clear_rls_context()

def update_rate(country_code: str, rate_id: int, payload: CommissionCategoryRateCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    return update_category_rate(db, rate_id, country_code, payload)

def list_badge_tiers_route(country_code: str, _: User, db: Session, page: int, page_size: int):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_badge_tiers(db, country_code, page, page_size)
    finally:
        clear_rls_context()

def create_badge_tier_route(country_code: str, payload: CommissionBadgeTierCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_badge_tier(db, payload, country_code)
    finally:
        clear_rls_context()

def update_badge_tier_route(country_code: str, tier_id: int, payload: CommissionBadgeTierCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    return update_badge_tier(db, tier_id, country_code, payload)

# === MERGED from _get_commission_engine().py ===

"""
Commission Engine — deterministic hybrid commission calculation.

Combined flow:
    1. Resolve supplier commission component from active supplier override or badge tier.
    2. Resolve base commission component from product override, else category rate, else global default.
    3. Final commission rate = supplier component + base component.

After combining the rate, the low-value cap is applied:
  If order_item_value < low_value_threshold (5 OMR):
      final_commission = min(rate * order_value, fixed_cap_amount)

Also seeds the default category rates and badge tiers on first use (idempotent).
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from domains.finance.models.commission import CommissionAgreement
from domains.finance.models.commission import CommissionCategoryRate
from domains.finance.models.commission import CommissionLedgerEntry
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Cross-domain model imports for read-only query building (same session).
# These are sanctioned per DOMAIN_ALLOWLIST.yaml — will be routed through
# governance.ports and comms.ports in a future migration.
from domains.comms.models.suppliers import SupplierProfile  # noqa: F401
from domains.governance.models.admin import CommissionBadgeTier
from domains.governance.models.admin import CommissionGlobalConfig

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Default seed data (applied once if tables are empty)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_CATEGORY_RATES: list[dict] = [
    {"category_slug": "electronics",   "category_display_name": "Electronics",   "rate": Decimal("0.0800"), "notes": "High ticket — low % to stay competitive"},
    {"category_slug": "fashion",       "category_display_name": "Fashion",       "rate": Decimal("0.1400"), "notes": "Mid margin; supports promotions"},
    {"category_slug": "accessories",   "category_display_name": "Accessories",   "rate": Decimal("0.1400"), "notes": "Similar to fashion"},
    {"category_slug": "furniture",     "category_display_name": "Furniture",     "rate": Decimal("0.0800"), "notes": "High ticket; lower % preserves supplier margin"},
    {"category_slug": "beauty",        "category_display_name": "Beauty",        "rate": Decimal("0.1200"), "notes": "Mid margin; frequent promotions"},
    {"category_slug": "sports",        "category_display_name": "Sports",        "rate": Decimal("0.1200"), "notes": "Mid margin"},
    {"category_slug": "home-living",   "category_display_name": "Home & Living", "rate": Decimal("0.1000"), "notes": "Mixed margins"},
    {"category_slug": "books",         "category_display_name": "Books",         "rate": Decimal("0.0600"), "notes": "Low margin — keep low to avoid price increases"},
    {"category_slug": "baby-kids",     "category_display_name": "Baby & Kids",   "rate": Decimal("0.1200"), "notes": "Stable mid margin"},
    {"category_slug": "automotive",    "category_display_name": "Automotive",    "rate": Decimal("0.0800"), "notes": "High ticket, lower %"},
    {"category_slug": "crafts",        "category_display_name": "Crafts",        "rate": Decimal("0.1800"), "notes": "Higher margin, smaller volumes"},
    {"category_slug": "grocery",       "category_display_name": "Grocery",       "rate": Decimal("0.0500"), "notes": "Very low margin — minimize % or rely on cap"},
]

_DEFAULT_BADGE_TIERS: list[dict] = [
    {
        "badge_level": "none", "commission_rate": Decimal("0.1600"),
        "setup_fee": Decimal("0.000"), "recurring_fee": Decimal("0.000"),
        "recurring_interval": None, "sort_order": 0,
        "benefits_json": json.dumps(["Basic listing", "Monthly payouts", "Basic support"]),
        "min_fulfilled_orders": None, "min_monthly_revenue": None,
    },
    {
        "badge_level": "bronze", "commission_rate": Decimal("0.1500"),
        "setup_fee": Decimal("0.000"), "recurring_fee": Decimal("0.000"),
        "recurring_interval": None, "sort_order": 1,
        "benefits_json": json.dumps(["Standard listing", "Monthly payouts", "Basic analytics"]),
        "min_fulfilled_orders": 0, "min_monthly_revenue": None,
    },
    {
        "badge_level": "silver", "commission_rate": Decimal("0.1200"),
        "setup_fee": Decimal("50.000"), "recurring_fee": Decimal("5.000"),
        "recurring_interval": "monthly", "sort_order": 2,
        "benefits_json": json.dumps(["Priority search placement", "Weekly payouts", "Reduced gateway fee share"]),
        "min_fulfilled_orders": 50, "min_monthly_revenue": Decimal("2000.00"),
    },
    {
        "badge_level": "gold", "commission_rate": Decimal("0.1000"),
        "setup_fee": Decimal("100.000"), "recurring_fee": Decimal("10.000"),
        "recurring_interval": "monthly", "sort_order": 3,
        "benefits_json": json.dumps(["Featured promotions", "Advanced analytics", "Faster dispute handling"]),
        "min_fulfilled_orders": 200, "min_monthly_revenue": Decimal("10000.00"),
    },
    {
        "badge_level": "platinum", "commission_rate": Decimal("0.0800"),
        "setup_fee": Decimal("200.000"), "recurring_fee": Decimal("20.000"),
        "recurring_interval": "monthly", "sort_order": 4,
        "benefits_json": json.dumps(["Next-day payouts", "Dedicated account manager", "Exclusive campaigns"]),
        "min_fulfilled_orders": 500, "min_monthly_revenue": Decimal("25000.00"),
    },
    {
        "badge_level": "membership", "commission_rate": Decimal("0.0800"),
        "setup_fee": Decimal("0.000"), "recurring_fee": Decimal("0.000"),
        "recurring_interval": None, "sort_order": 5,
        "benefits_json": json.dumps(["Negotiated lower rate", "Co-op marketing", "SLA", "Premium placement"]),
        "min_fulfilled_orders": None, "min_monthly_revenue": None,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Seeding
# ─────────────────────────────────────────────────────────────────────────────

def seed_defaults(db: Session) -> None:
    """Idempotently seed global config, default category rates, and badge tiers."""
    # Global config singleton
    config = db.query(CommissionGlobalConfig).filter(CommissionGlobalConfig.id == 1).first()
    if not config:
        db.add(CommissionGlobalConfig(
            id=1,
            default_rate=Decimal("0.1500"),
            low_value_threshold=Decimal("5.00"),
            fixed_cap_amount=Decimal("0.500"),
            fixed_cap_enabled=True,
            margin_protection_enabled=False,
            margin_threshold=Decimal("0.10"),
        ))
        logger.info("Commission engine: seeded global config")

    # Category rates
    existing_slugs = {r[0] for r in db.query(CommissionCategoryRate.category_slug).all()}
    for cr in _DEFAULT_CATEGORY_RATES:
        if cr["category_slug"] not in existing_slugs:
            db.add(CommissionCategoryRate(
                category_slug=cr["category_slug"],
                category_display_name=cr["category_display_name"],
                rate_percent=cr["rate"],
                is_active=True,
            ))
    if len(existing_slugs) < len(_DEFAULT_CATEGORY_RATES):
        logger.info("Commission engine: seeded category rates")

    # Badge tiers
    existing_badges = {r[0] for r in db.query(CommissionBadgeTier.badge_level).all()}
    for bt in _DEFAULT_BADGE_TIERS:
        if bt["badge_level"] not in existing_badges:
            db.add(CommissionBadgeTier(
                name=bt["badge_level"],
                badge_level=bt["badge_level"],
                commission_rate=bt["commission_rate"],
                setup_fee=bt["setup_fee"],
                recurring_fee=bt["recurring_fee"],
                recurring_interval=bt.get("recurring_interval"),
                benefits_json=bt.get("benefits_json"),
                min_fulfilled_orders=bt.get("min_fulfilled_orders"),
                min_monthly_revenue=bt.get("min_monthly_revenue"),
                sort_order=bt.get("sort_order", 0),
                is_active=True,
            ))
    if len(existing_badges) < len(_DEFAULT_BADGE_TIERS):
        logger.info("Commission engine: seeded badge tiers")

    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Global config helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_global_config(db: Session) -> CommissionGlobalConfig:
    """Return the singleton global commission config, seeding it if absent."""
    config = db.query(CommissionGlobalConfig).filter(CommissionGlobalConfig.id == 1).first()
    if not config:
        seed_defaults(db)
        config = db.query(CommissionGlobalConfig).filter(CommissionGlobalConfig.id == 1).first()
    return config  # type: ignore[return-value]


# ─────────────────────────────────────────────────────────────────────────────
# Rate resolution
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RateResult:
    """Result of rate resolution for a single supplier/product/category combo."""
    applied_rate: Decimal
    calculation_method: str          # override | badge
    override_rate: Optional[Decimal]
    category_rate: Optional[Decimal]
    country_rate: Optional[Decimal]
    badge_rate: Optional[Decimal]
    global_default_rate: Decimal
    badge_level: Optional[str]
    category_slug: Optional[str]
    country_code: Optional[str]
    override_flag: bool
    supplier_rate: Decimal
    supplier_rate_source: str
    base_rate: Decimal
    base_rate_source: str
    product_override_rate: Optional[Decimal]


def get_effective_rate(
    supplier_id: int,
    product_id: Optional[int],
    category_slug: Optional[str],
    db: Session,
    country_code: Optional[str] = None,
) -> RateResult:
    """
    Resolve the effective commission rate for a supplier/product/category.

    Final rate = supplier commission component + base commission component.
    """
    config = get_global_config(db)
    global_default = Decimal(str(config.default_rate))

    # 1. Supplier commission component: active supplier override or badge tier.
    override_rate: Optional[Decimal] = None
    supplier_rate = Decimal("0.0000")
    supplier_rate_source = "badge"
    agreement = (
        db.query(CommissionAgreement)
        .filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,  # noqa: E712
        )
        .first()
    )
    badge_lvl = _get_supplier_badge_level(supplier_id, db)
    if agreement:
        override_rate = Decimal(str(agreement.rate))
        supplier_rate = override_rate
        supplier_rate_source = "override"

    # Badge still matters for reporting even when an override is active.
    badge_rate: Optional[Decimal] = None
    if badge_lvl:
        badge_row = (
            db.query(CommissionBadgeTier)
            .filter(
                CommissionBadgeTier.badge_level == badge_lvl,
                CommissionBadgeTier.is_active == True,  # noqa: E712
            )
            .first()
        )
        if badge_row:
            badge_rate = Decimal(str(badge_row.commission_rate))
            if override_rate is None:
                supplier_rate = badge_rate

    # 2. Base commission component: product override, else category, else global.
    product_override_rate = None
    if product_id is not None:
        from domains.finance.models.commission import ProductCommissionOverride

        product_override_row = (
            db.query(ProductCommissionOverride)
            .filter(
                ProductCommissionOverride.product_id == product_id,
                ProductCommissionOverride.is_active == True,  # noqa: E712
            )
            .first()
        )
        if product_override_row:
            product_override_rate = Decimal(str(product_override_row.rate))

    country_rate: Optional[Decimal] = None
    normalized_country_code = str(country_code or "").strip().upper() or None
    if normalized_country_code and category_slug:
        country_row = (
            db.query(CommissionCategoryRate)
            .filter(
                CommissionCategoryRate.country_code == normalized_country_code,
                CommissionCategoryRate.category_slug == category_slug,
                CommissionCategoryRate.is_active == True,
            )
            .first()
        )
        if country_row:
            country_rate = Decimal(str(country_row.rate_percent))

    cat_rate: Optional[Decimal] = None
    if category_slug and country_rate is None:
        cat_row = (
            db.query(CommissionCategoryRate)
            .filter(
                CommissionCategoryRate.country_code is None,
                CommissionCategoryRate.category_slug == category_slug,
                CommissionCategoryRate.is_active == True,
            )
            .first()
        )
        if cat_row:
            cat_rate = Decimal(str(cat_row.rate_percent))
    if product_override_rate is not None:
        base_rate = product_override_rate
        base_rate_source = "product_override"
    elif country_rate is not None:
        base_rate = country_rate
        base_rate_source = "country_category"
    elif cat_rate is not None:
        base_rate = cat_rate
        base_rate_source = "category"
    else:
        base_rate = global_default
        base_rate_source = "global_default"

    applied_rate = (supplier_rate + base_rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return RateResult(
        applied_rate=applied_rate,
        calculation_method="override" if override_rate is not None else "badge",
        override_rate=override_rate,
        category_rate=cat_rate,
        country_rate=country_rate,
        badge_rate=badge_rate,
        global_default_rate=global_default,
        badge_level=badge_lvl,
        category_slug=category_slug,
        country_code=normalized_country_code,
        override_flag=override_rate is not None,
        supplier_rate=supplier_rate,
        supplier_rate_source=supplier_rate_source,
        base_rate=base_rate,
        base_rate_source=base_rate_source,
        product_override_rate=product_override_rate,
    )


def _get_supplier_badge_level(supplier_id: int, db: Session) -> Optional[str]:
    profile = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == supplier_id)
        .first()
    )
    badge_level = getattr(profile, "badge_level", None) if profile is not None else None
    if badge_level not in (None, ""):
        return str(badge_level).lower()
    return "none"


# ─────────────────────────────────────────────────────────────────────────────
# Commission computation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CommissionResult:
    rate: Decimal
    calculation_method: str
    order_value: Decimal
    commission_pct_amount: Decimal      # rate * order_value (before cap)
    cap_applied: bool
    commission_amount: Decimal          # final after cap
    low_value_threshold_used: Optional[Decimal]
    fixed_cap_used: Optional[Decimal]
    rate_result: RateResult             # full metadata


def compute_commission(
    order_value: Decimal,
    rate_result: RateResult,
    global_config: CommissionGlobalConfig,
) -> CommissionResult:
    """
    Apply the rate to the order value and apply the low-value cap if needed.

    Low-value cap: if order_value < low_value_threshold AND fixed_cap_enabled:
        final_commission = min(rate * order_value, fixed_cap_amount)
    """
    rate = rate_result.applied_rate
    commission_pct = (rate * order_value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    cap_applied = False
    commission_amount = commission_pct
    low_value_threshold_used: Optional[Decimal] = None
    fixed_cap_used: Optional[Decimal] = None

    fixed_cap_enabled = bool(getattr(global_config, "fixed_cap_enabled"))
    if fixed_cap_enabled:
        threshold = Decimal(str(getattr(global_config, "low_value_threshold")))
        cap = Decimal(str(getattr(global_config, "fixed_cap_amount")))
        if order_value < threshold:
            commission_amount = min(commission_pct, cap)
            cap_applied = commission_amount < commission_pct
            low_value_threshold_used = threshold
            fixed_cap_used = cap

    return CommissionResult(
        rate=rate,
        calculation_method=rate_result.calculation_method,
        order_value=order_value,
        commission_pct_amount=commission_pct,
        cap_applied=cap_applied,
        commission_amount=commission_amount,
        low_value_threshold_used=low_value_threshold_used,
        fixed_cap_used=fixed_cap_used,
        rate_result=rate_result,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Persist ledger entry
# ─────────────────────────────────────────────────────────────────────────────

def create_commission_ledger_entry(
    order_id: int,
    supplier_id: int,
    order_value: Decimal,
    result: CommissionResult,
    db: Session,
    order_item_id: Optional[int] = None,
    product_id: Optional[int] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> CommissionLedgerEntry:
    """Persist an immutable CommissionLedgerEntry for a single order item."""
    rr = result.rate_result
    entry = CommissionLedgerEntry(
        order_id=order_id,
        order_item_id=order_item_id,
        supplier_id=supplier_id,
        product_id=product_id,
        category_slug=rr.category_slug,
        badge_level=rr.badge_level,
        global_default_rate=rr.global_default_rate,
        category_rate=rr.category_rate,
        badge_rate=rr.badge_rate,
        override_rate=rr.override_rate,
        applied_rate=result.rate,
        calculation_method=result.calculation_method,
        order_value=order_value,
        commission_pct=result.commission_pct_amount,
        cap_applied=result.cap_applied,
        commission_amount=result.commission_amount,
        low_value_threshold_used=result.low_value_threshold_used,
        fixed_cap_used=result.fixed_cap_used,
        override_flag=rr.override_flag,
        is_adjusted=False,
        currency=currency,
        country_code=country_code,
    )
    db.add(entry)
    return entry


# ─────────────────────────────────────────────────────────────────────────────
# Preview (no DB writes)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Country value-based commission tiers
# ─────────────────────────────────────────────────────────────────────────────

import json as _json

from domains.country.models.countries import CountryConfig


def resolve_country_commission_tiers(
    country_code: str,
    order_value: Decimal,
    db: Session,
) -> dict[str, Decimal | None] | None:
    """Resolve commission from a country's value-based ``commission_tiers_json``.

    Returns ``{commission_percentage, fixed_fee}`` if a matching tier is found,
    ``None`` if no tiers are configured for the country.
    """
    code = _normalize_country(country_code)
    if not code:
        return None
    country = db.query(CountryConfig).filter(
        CountryConfig.code == code,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        return None
    raw = country.commission_tiers_json
    if not raw:
        return None
    try:
        tiers = _json.loads(raw) if isinstance(raw, str) else raw
    except (_json.JSONDecodeError, TypeError):
        return None
    if not isinstance(tiers, list):
        return None

    for tier in tiers:
        if not isinstance(tier, dict):
            continue
        min_val = Decimal(str(tier.get("min_order_value", 0)))
        max_raw = tier.get("max_order_value")
        max_val = Decimal(str(max_raw)) if max_raw is not None else None
        if order_value >= min_val:
            if max_val is None or order_value <= max_val:
                pct = Decimal(str(tier.get("commission_percentage", 0)))
                fee = Decimal(str(tier.get("fixed_fee", 0)))
                return {
                    "commission_percentage": pct / Decimal("100"),
                    "fixed_fee": fee,
                    "min_order_value": min_val,
                    "max_order_value": max_val,
                }
    return None


def preview_commission(
    supplier_id: int,
    order_value: float,
    category_slug: Optional[str],
    db: Session,
) -> dict:
    """Preview commission calculation without persisting anything."""
    ov = Decimal(str(order_value))
    rate_result = get_effective_rate(supplier_id=supplier_id, product_id=None, category_slug=category_slug, db=db)
    config = get_global_config(db)
    result = compute_commission(ov, rate_result, config)
    fixed_cap_enabled = bool(getattr(config, "fixed_cap_enabled"))

    return {
        "order_value": float(ov),
        "applied_rate": float(result.rate),
        "applied_rate_pct": f"{float(result.rate) * 100:.2f}%",
        "calculation_method": result.calculation_method,
        "commission_pct_amount": float(result.commission_pct_amount),
        "cap_applied": result.cap_applied,
        "commission_amount": float(result.commission_amount),
        "low_value_threshold": float(getattr(config, "low_value_threshold")) if fixed_cap_enabled else None,
        "fixed_cap": float(getattr(config, "fixed_cap_amount")) if fixed_cap_enabled else None,
        "snapshot": {
            "supplier_rate": float(rate_result.supplier_rate),
            "supplier_rate_source": rate_result.supplier_rate_source,
            "base_rate": float(rate_result.base_rate),
            "base_rate_source": rate_result.base_rate_source,
            "country_rate": float(rate_result.country_rate) if rate_result.country_rate else None,
            "country_code": rate_result.country_code,
            "product_override_rate": float(rate_result.product_override_rate) if rate_result.product_override_rate else None,
            "override_rate": float(rate_result.override_rate) if rate_result.override_rate else None,
            "category_rate": float(rate_result.category_rate) if rate_result.category_rate else None,
            "badge_rate": float(rate_result.badge_rate) if rate_result.badge_rate else None,
            "global_default_rate": float(rate_result.global_default_rate),
            "badge_level": rate_result.badge_level,
            "category_slug": rate_result.category_slug,
        },
    }

# === MERGED from tax_service.py ===

def _safe_json_list(raw: str | None) -> set[str]:
    if not raw:
        return set()
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return set()
    if not isinstance(parsed, list):
        return set()
    return {str(item).strip().lower() for item in parsed if str(item).strip()}


def _safe_json_map(raw: str | None) -> dict[str, Decimal]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}

    normalized: dict[str, Decimal] = {}
    for key, value in parsed.items():
        k = str(key).strip().lower()
        if not k:
            continue
        normalized[k] = to_decimal(value)
    return normalized


def get_country_config(db: Session, country_code: str) -> CountryConfig:
    code = normalize_country_code(country_code)
    if not code:
        raise ValueError("Unknown country: empty code")

    config = (
        db.query(CountryConfig)
        .filter(CountryConfig.code == code, CountryConfig.is_active == True)  # noqa: E712
        .first()
    )
    if not config:
        raise ValueError(f"Unknown country: {code}")
    return config


def resolve_tax_rate(config: CountryConfig, category: str | None = None) -> Decimal:
    category_key = (category or "").strip().lower()

    exempt = _safe_json_list(getattr(config, "tax_exempt_categories_json", None))
    if category_key and category_key in exempt:
        return Decimal("0.0000")

    reduced = _safe_json_map(getattr(config, "tax_reduced_rates_json", None))
    if category_key and category_key in reduced:
        return reduced[category_key]

    return to_decimal(getattr(config, "tax_rate", 0) or 0)


def calculate_tax(
    amount: Decimal,
    country_code: str,
    db: Session,
    *,
    category: str | None = None,
    inclusive: bool | None = None,
) -> dict[str, Any]:
    config = get_country_config(db, country_code)
    amount_decimal = round_money(to_decimal(amount))
    rate = resolve_tax_rate(config, category)

    if inclusive is None:
        inclusive_mode = bool(getattr(config, "tax_inclusive", False))
    else:
        inclusive_mode = bool(inclusive)

    if inclusive_mode and rate > 0:
        net_amount = round_money(amount_decimal / (Decimal("1.0") + rate))
        tax_amount = round_money(amount_decimal - net_amount)
        total_amount = amount_decimal
    else:
        tax_amount = round_money(amount_decimal * rate)
        net_amount = amount_decimal
        total_amount = round_money(amount_decimal + tax_amount)

    return {
        "country_code": normalize_country_code(country_code),
        "tax_type": str(getattr(config, "tax_type", "TAX") or "TAX"),
        "tax_name": str(getattr(config, "tax_name", "Tax") or "Tax"),
        "tax_rate": rate,
        "tax_amount": tax_amount,
        "net_amount": net_amount,
        "total_amount": total_amount,
        "is_inclusive": inclusive_mode,
        "currency": str(getattr(config, "currency", settings.default_currency) or settings.default_currency),
    }

# === MERGED from vat_rates.py ===

"""
Curated VAT / sales-tax rates per country — used as fallback when the
external VAT API is unavailable.

``VAT_RATES`` stores the standard VAT percentage (e.g. 5 = 5 %).
``LEGAL_DEFAULTS`` stores per-country legal rule overrides such as
minimum order age, return windows, and product restrictions.

Add entries here as new countries are onboarded.
"""

from typing import Any, Optional

# Standard VAT / sales-tax rate as a percentage (e.g. 5 = 5 %).
VAT_RATES: dict[str, float] = {
    "SA": 15.0,
    "AE": 5.0,
    "OM": 5.0,
    "BH": 5.0,
    "KW": 5.0,
    "QA": 0.0,
    "US": 0.0,  # sales tax varies by state — handled inline
    "GB": 20.0,
    "DE": 19.0,
    "FR": 20.0,
    "IT": 22.0,
    "ES": 21.0,
    "PK": 18.0,
    "IN": 18.0,
}

# Country-code → legal-rule overrides.
# Keys not present here inherit the GCC defaults from the auto-populate engine.
LEGAL_DEFAULTS: dict[str, dict[str, Any]] = {
    "SA": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 14,
        "refund_processing_days": 7,
        "requires_commercial_license": True,
        "requires_vat_registration": True,
        "product_restrictions": ["alcohol", "pork", "gambling_related"],
    },
    "OM": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 10,
        "refund_processing_days": 5,
        "requires_commercial_license": True,
        "requires_vat_registration": True,
        "product_restrictions": ["alcohol", "pork"],
    },
}


def get_vat_rate(country_code: str) -> Optional[float]:
    """Return the standard VAT/sales-tax percentage for *country_code*, or ``None``.

    Example: ``get_vat_rate("SA")`` → ``15.0`` (15%).
    """
    return VAT_RATES.get(country_code.upper())


def get_legal_defaults(country_code: str) -> dict[str, Any]:
    """Return legal rule defaults for *country_code*, falling back to a sensible
    empty dict when no curated entry exists."""
    return LEGAL_DEFAULTS.get(country_code.upper(), {})

# === MERGED from erp_finance_service.py ===

"""ERP-level finance services: AR/AP, bank reconciliation matching, budgets.

All postings go through the canonical immutable ledger
(`general_ledger_service.create_journal_entry`) so balances and the audit trail
stay consistent.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from domains.finance.models.finance import Customer
from domains.finance.models.finance import Vendor
from domains.finance.models.finance import APBill
from domains.finance.models.finance import ARInvoice
from domains.finance.models.finance import BankStatementLine
from domains.finance.models.finance import BankReconciliation
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import FiscalPeriod
from domains.finance.models.finance import Budget
from domains.finance.models.finance import FinanceAuditLog
from domains.finance.models.finance import BankMappingRule
from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput
# Removed circular self-import
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


def _audit(db: Session, action: str, entity_id: int, country_code, detail: dict, actor_id=None) -> None:
    try:
        db.add(FinanceAuditLog(
            action=action, entity_type="finance", entity_id=entity_id,
            actor_id=actor_id, country_code=country_code, detail=detail,
        ))
        db.commit()
    except Exception as e:
        logger.warning("finance audit failed: %s", e)


# ── AR (Receivables) ──────────────────────────────────────────────────────────


def create_ar_invoice(
    db: Session, *, customer_id: int, invoice_number: str, invoice_date: datetime,
    due_date: Optional[datetime], account_code: str, amount: Decimal,
    tax_amount: Decimal = Decimal("0"), description: str = "", country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> ARInvoice:
    inv = ARInvoice(
        customer_id=customer_id, invoice_number=invoice_number, invoice_date=invoice_date,
        due_date=due_date, account_code=account_code, amount=amount, tax_amount=tax_amount,
        description=description, country_code=country_code, created_by=created_by, status="issued",
    )
    db.add(inv)
    db.flush()
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=invoice_date, reference_type="ar_invoice", reference_id=inv.id,
        description=f"AR invoice {invoice_number} to customer {customer_id}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code=account_code, side="debit", amount=amount,
                             description=f"Receivable {invoice_number}", entity_type="ar_invoice", entity_id=inv.id),
            JournalLineInput(account_code="4010", side="credit", amount=amount,
                             description=f"Revenue {invoice_number}", entity_type="ar_invoice", entity_id=inv.id),
        ],
    ), user_id=created_by)
    inv.linked_journal_entry_id = entry.id
    db.commit()
    db.refresh(inv)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ar_invoice", "invoice": invoice_number}, created_by)
    return inv


def receive_ar_payment(
    db: Session, *, invoice_id: int, amount: Decimal, payment_date: datetime,
    cash_account_code: str = "1010", country_code: Optional[str] = None, created_by: Optional[int] = None,
) -> ARInvoice:
    inv = db.query(ARInvoice).filter(ARInvoice.id == invoice_id).first()
    if not inv:
        raise ValueError("AR invoice not found")
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=payment_date, reference_type="ar_receipt", reference_id=invoice_id,
        description=f"Receipt for AR invoice {inv.invoice_number}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code=cash_account_code, side="debit", amount=amount,
                             description="Cash receipt", entity_type="ar_invoice", entity_id=invoice_id),
            JournalLineInput(account_code=inv.account_code, side="credit", amount=amount,
                             description="Receivable cleared", entity_type="ar_invoice", entity_id=invoice_id),
        ],
    ), user_id=created_by)
    inv.paid_journal_entry_id = entry.id
    inv.status = "paid"
    db.commit()
    db.refresh(inv)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ar_receipt", "invoice": inv.invoice_number}, created_by)
    return inv


def ar_aging(db: Session, as_of: date, country_code: Optional[str] = None) -> dict:
    q = db.query(ARInvoice).filter(ARInvoice.status.in_(["issued", "partially_paid"]))
    if country_code:
        q = q.filter((ARInvoice.country_code == country_code) | (ARInvoice.country_code.is_(None)))
    buckets = {"current": Decimal("0"), "b0_30": Decimal("0"), "b31_60": Decimal("0"),
               "b61_90": Decimal("0"), "b90_plus": Decimal("0")}
    rows = []
    for inv in q.all():
        due = inv.due_date.date() if inv.due_date else inv.invoice_date.date()
        days = (as_of - due).days
        unpaid = inv.amount
        if days <= 0:
            key = "current"
        elif days <= 30:
            key = "b0_30"
        elif days <= 60:
            key = "b31_60"
        elif days <= 90:
            key = "b61_90"
        else:
            key = "b90_plus"
        buckets[key] += unpaid
        rows.append({"id": inv.id, "customer_id": inv.customer_id, "invoice_number": inv.invoice_number,
                     "amount": float(unpaid), "due_date": due.isoformat(), "days_overdue": max(days, 0)})
    return {"as_of": as_of.isoformat(), "buckets": {k: float(v) for k, v in buckets.items()},
            "total": float(sum(buckets.values())), "invoices": rows}


# ── AP (Payables) ─────────────────────────────────────────────────────────────


def create_ap_bill(
    db: Session, *, vendor_id: int, bill_number: str, bill_date: datetime,
    due_date: Optional[datetime], account_code: str, amount: Decimal,
    tax_amount: Decimal = Decimal("0"), description: str = "", country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> APBill:
    bill = APBill(
        vendor_id=vendor_id, bill_number=bill_number, bill_date=bill_date, due_date=due_date,
        account_code=account_code, amount=amount, tax_amount=tax_amount, description=description,
        country_code=country_code, created_by=created_by, status="received",
    )
    db.add(bill)
    db.flush()
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=bill_date, reference_type="ap_bill", reference_id=bill.id,
        description=f"AP bill {bill_number} from vendor {vendor_id}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code=account_code, side="debit", amount=amount,
                             description=f"Expense {bill_number}", entity_type="ap_bill", entity_id=bill.id),
            JournalLineInput(account_code="2010", side="credit", amount=amount,
                             description=f"Payable {bill_number}", entity_type="ap_bill", entity_id=bill.id),
        ],
    ), user_id=created_by)
    bill.linked_journal_entry_id = entry.id
    db.commit()
    db.refresh(bill)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ap_bill", "bill": bill_number}, created_by)
    return bill


def pay_ap_bill(
    db: Session, *, bill_id: int, amount: Decimal, payment_date: datetime,
    cash_account_code: str = "1010", country_code: Optional[str] = None, created_by: Optional[int] = None,
) -> APBill:
    bill = db.query(APBill).filter(APBill.id == bill_id).first()
    if not bill:
        raise ValueError("AP bill not found")
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=payment_date, reference_type="ap_payment", reference_id=bill_id,
        description=f"Payment for AP bill {bill.bill_number}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code="2010", side="debit", amount=amount,
                             description="Payable cleared", entity_type="ap_bill", entity_id=bill_id),
            JournalLineInput(account_code=cash_account_code, side="credit", amount=amount,
                             description="Cash payment", entity_type="ap_bill", entity_id=bill_id),
        ],
    ), user_id=created_by)
    bill.paid_journal_entry_id = entry.id
    bill.status = "paid"
    db.commit()
    db.refresh(bill)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ap_payment", "bill": bill.bill_number}, created_by)
    return bill


def ap_aging(db: Session, as_of: date, country_code: Optional[str] = None) -> dict:
    q = db.query(APBill).filter(APBill.status.in_(["received", "approved"]))
    if country_code:
        q = q.filter((APBill.country_code == country_code) | (APBill.country_code.is_(None)))
    buckets = {"current": Decimal("0"), "b0_30": Decimal("0"), "b31_60": Decimal("0"),
               "b61_90": Decimal("0"), "b90_plus": Decimal("0")}
    rows = []
    for bill in q.all():
        due = bill.due_date.date() if bill.due_date else bill.bill_date.date()
        days = (as_of - due).days
        unpaid = bill.amount
        if days <= 0:
            key = "current"
        elif days <= 30:
            key = "b0_30"
        elif days <= 60:
            key = "b31_60"
        elif days <= 90:
            key = "b61_90"
        else:
            key = "b90_plus"
        buckets[key] += unpaid
        rows.append({"id": bill.id, "vendor_id": bill.vendor_id, "bill_number": bill.bill_number,
                     "amount": float(unpaid), "due_date": due.isoformat(), "days_overdue": max(days, 0)})
    return {"as_of": as_of.isoformat(), "buckets": {k: float(v) for k, v in buckets.items()},
            "total": float(sum(buckets.values())), "bills": rows}


# ── Bank Reconciliation ───────────────────────────────────────────────────────


def suggest_matches(db: Session, line: BankStatementLine) -> list[dict]:
    """Find candidate journal-entry lines matching a statement line by amount ± date."""
    amt = abs(line.amount)
    lo = (line.txn_date or _utcnow()) 
    candidates = (
        db.query(JournalEntryLine, JournalEntry)
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .filter(
            func.abs(JournalEntryLine.amount) == float(amt),
            JournalEntryLine.country_code == line.country_code if line.country_code else True,
        )
        .order_by(func.abs(func.julianday(JournalEntry.entry_date) - func.julianday(lo)).asc())
        .limit(5)
        .all()
    )
    out = []
    for jl, je in candidates:
        out.append({"journal_entry_id": je.id, "reference_number": je.reference_number,
                    "entry_date": je.entry_date.isoformat() if je.entry_date else None,
                    "account_code": jl.account_code if hasattr(jl, "account_code") else None,
                    "amount": float(jl.amount), "side": jl.side})
    return out


def match_statement_line(
    db: Session, *, line_id: int, journal_entry_id: int, country_code: Optional[str] = None,
    matched_by: Optional[int] = None,
) -> BankReconciliation:
    line = db.query(BankStatementLine).filter(BankStatementLine.id == line_id).first()
    if not line:
        raise ValueError("statement line not found")
    rec = db.query(BankReconciliation).filter(BankReconciliation.statement_line_id == line_id).first()
    if not rec:
        rec = BankReconciliation(statement_line_id=line_id)
        db.add(rec)
    rec.journal_entry_id = journal_entry_id
    rec.matched_amount = line.amount
    rec.status = "matched"
    rec.matched_by = matched_by
    rec.country_code = country_code or line.country_code
    rec.matched_at = _utcnow()
    line.status = "reconciled"
    db.commit()
    db.refresh(rec)
    _audit(db, "reconciliation", line_id, rec.country_code, {"journal_entry_id": journal_entry_id}, matched_by)
    return rec


def auto_match_import(db: Session, import_id: int, country_code: Optional[str] = None,
                      matched_by: Optional[int] = None) -> dict:
    lines = db.query(BankStatementLine).filter(
        BankStatementLine.import_id == import_id,
        BankStatementLine.status.in_(["unmapped", "mapped"]),
    ).all()
    matched = 0
    for line in lines:
        sugg = suggest_matches(db, line)
        if sugg:
            match_statement_line(db, line_id=line.id, journal_entry_id=sugg[0]["journal_entry_id"],
                                 country_code=country_code, matched_by=matched_by)
            matched += 1
    return {"import_id": import_id, "total": len(lines), "matched": matched}


# ── Budgets ───────────────────────────────────────────────────────────────────


def set_budget(db: Session, *, account_code: str, fiscal_period_id: int, amount: Decimal,
               currency: str = "OMR", country_code: Optional[str] = None, notes: str = "",
               created_by: Optional[int] = None) -> Budget:
    existing = db.query(Budget).filter(
        Budget.account_code == account_code, Budget.fiscal_period_id == fiscal_period_id,
        (Budget.country_code == country_code) | (Budget.country_code.is_(None)),
    ).first()
    if existing:
        existing.amount = amount
        existing.currency = currency
        existing.notes = notes
        existing.updated_at = _utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    b = Budget(account_code=account_code, fiscal_period_id=fiscal_period_id, amount=amount,
              currency=currency, country_code=country_code, notes=notes, created_by=created_by)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def budget_variance(db: Session, fiscal_period_id: int, country_code: Optional[str] = None) -> dict:
    period = db.query(FiscalPeriod).filter(FiscalPeriod.id == fiscal_period_id).first()
    budgets = db.query(Budget).filter(Budget.fiscal_period_id == fiscal_period_id)
    if country_code:
        budgets = budgets.filter((Budget.country_code == country_code) | (Budget.country_code.is_(None)))
    rows = []
    total_budget = Decimal("0")
    total_actual = Decimal("0")
    for b in budgets.all():
        acct = db.query(Account).filter(Account.code == b.account_code).first()
        actual = Decimal("0")
        if acct:
            bal = db.query(AccountBalance).filter(
                AccountBalance.account_id == acct.id, AccountBalance.currency == b.currency,
            ).first()
            if bal:
                actual = bal.balance if acct.normal_side == "debit" else -bal.balance
        total_budget += b.amount
        total_actual += actual
        rows.append({
            "account_code": b.account_code, "account_name": acct.name if acct else None,
            "budget": float(b.amount), "actual": float(actual),
            "variance": float(b.amount - actual),
        })
    return {
        "fiscal_period_id": fiscal_period_id,
        "period_label": f"{period.period_year}-{period.period_month:02d}" if period else None,
        "country_code": country_code,
        "total_budget": float(total_budget), "total_actual": float(total_actual),
        "total_variance": float(total_budget - total_actual), "rows": rows,
    }

# === MERGED from erp_read_service.py ===

"""ERP read-access service (finance).

Thin read helpers over the chart-of-accounts, consumed by
``data.ledger_impl_bridge`` so the general-ledger facade can resolve account
lookups without creating a ``general_ledger -> finance`` dependency edge.

Implementations are intentionally lightweight: the canonical GL/ERP logic is
consolidated in ``services.finance.general_ledger_service`` and
``services.treasury``; these leaf functions exist so the import graph stays
acyclic and ``import main`` succeeds.
"""

from typing import Any, List, Optional

# TODO: Module not yet created
# from domains.comms.services.utility.db_read import first
# TODO: Module not yet created
# from domains.comms.services.utility.db_read import all_rows
import structlog

logger = structlog.get_logger(__name__)

__all__ = ["get_account_by_code", "list_accounts_paged"]


def get_account_by_code(db: Any, code: str) -> Optional[Any]:
    """Return the account row matching ``code`` (or ``None``)."""
    from domains.finance.models.finance import Account

    return first(db, Account, filters=[Account.code == code])


def list_accounts_paged(
    db: Any,
    skip: int = 0,
    limit: int = 50,
    country_code: Optional[str] = None,
) -> List[Any]:
    """Return a page of account rows, optionally filtered by ``country_code``."""
    from domains.finance.models.finance import Account

    filters = []
    if country_code is not None:
        filters.append(Account.country_code == country_code)
    return all_rows(
        db,
        Account,
        filters=filters,
        order_by=Account.code,
        offset=skip,
        limit=limit,
    )

# === MERGED from finance_erp_write_service.py ===

"""ERP finance write service.

Owns the DB mutations behind the ERP finance router endpoints that write
directly (GL account edit, recurring template creation) so the router and
controller layers stay write-free (W1 layer contract).

Each function takes ``db: Session`` first, mutates, commits, and raises
``HTTPException`` exactly as the original router code did.

Endpoints that already delegate to ``data.services.finance.erp_finance_service`` /
``data.services.finance.finance_automation`` are intentionally not duplicated here.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountGroup
from domains.finance.models.finance import RecurringTemplate
import structlog
logger = structlog.get_logger(__name__)


def update_gl_account(db: Session, code: str, payload: dict) -> dict:
    """Apply a partial update to a GL account identified by ``code``."""
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        raise HTTPException(404, f"Account '{code}' not found")

    name = payload.get("name")
    if name is not None:
        acct.name = name

    normal_side = payload.get("normal_side")
    if normal_side is not None:
        acct.normal_side = normal_side

    currency = payload.get("currency")
    if currency is not None:
        acct.currency = currency

    group_code = payload.get("group_code")
    if group_code is not None:
        grp = db.query(AccountGroup).filter(AccountGroup.code == group_code).first()
        if not grp:
            raise HTTPException(404, f"Group '{group_code}' not found")
        acct.group_id = grp.id

    db.commit()
    return {"status": "updated", "code": code}


def create_recurring_template(
    db: Session,
    *,
    name: str,
    frequency: str,
    next_run_date: Optional[datetime],
    description: str,
    lines: list[dict],
    currency: str,
    country_code: Optional[str],
    created_by: Any,
) -> RecurringTemplate:
    """Persist a new recurring journal-entry template."""
    tpl = RecurringTemplate(name=name, frequency=frequency, next_run_date=next_run_date,
                            description=description, lines=lines, currency=currency,
                            country_code=country_code, created_by=created_by)
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl

# === MERGED from import_service.py ===

logger = logging.getLogger(__name__)

GOODS_IN_TRANSIT = "1410"
INVENTORY = "1060"
AP_ACCOUNT = "2010"
CASH_ACCOUNT = "1010"
CUSTOMS_DUTY_PAYABLE = "2095"
FX_GAIN_LOSS = "6060"


def _ensure_import_accounts(db: Session) -> None:
    existing = {a.code for a in db.query(Account).all()}
    groups = {g.code: g.id for g in db.query(AccountGroup).all()}
    asset_group = groups.get("1.1")
    liability_group = groups.get("2.1")
    expense_group = groups.get("5.2")
    to_create = []
    if "1410" not in existing and asset_group:
        to_create.append(Account(code="1410", name="Goods in Transit", group_id=asset_group,
                                 normal_side="debit", currency="OMR"))
    if "2095" not in existing and liability_group:
        to_create.append(Account(code="2095", name="Customs Duty Payable", group_id=liability_group,
                                 normal_side="credit", currency="OMR"))
    if "6060" not in existing and expense_group:
        to_create.append(Account(code="6060", name="Unrealized FX Gain/Loss", group_id=expense_group,
                                 normal_side="debit", currency="OMR"))
    for acct in to_create:
        db.add(acct)
        db.flush()
        db.add(AccountBalance(account_id=acct.id, currency="OMR", balance=Decimal("0.00")))
    if to_create:
        db.commit()
        logger.info("Created import GL accounts: %s", [a.code for a in to_create])


def _next_number(db: Session, prefix: str, table_column) -> str:
    last = db.query(func.max(table_column)).filter(
        table_column.like(f"{prefix}-%")
    ).scalar()
    seq = 1
    if last:
        try:
            seq = int(last.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}-{seq:05d}"


def _get_cost_template(db: Session, country_code: str = None) -> Optional[ImportCostTemplate]:
    q = db.query(ImportCostTemplate).filter(ImportCostTemplate.is_active == True)
    if country_code:
        q = q.filter(ImportCostTemplate.country_code == country_code)
    return q.first()


# ── Shipment ──


def create_import_shipment(
    db: Session, *, po_id: int = None, supplier_id: int = None,
    origin_country: str = None, port_of_loading: str = None,
    port_of_discharge: str = None, vessel_name: str = None,
    bill_of_lading: str = None, container_number: str = None,
    shipment_date: datetime = None, estimated_arrival: datetime = None,
    currency: str = "OMR", exchange_rate: Decimal = Decimal("1"),
    warehouse_id: int = None, country_code: str = None,
    notes: str = None, created_by: int = None,
    lines: list[dict] = None,
) -> ImportShipment:
    _ensure_import_accounts(db)
    shipment_ref = _next_number(db, "SHIP", ImportShipment.shipment_ref)
    po = None
    if po_id:
        po = db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError("Purchase order not found")
        if not supplier_id:
            supplier_id = po.supplier_id
        if not warehouse_id:
            warehouse_id = po.warehouse_id
        if not country_code:
            country_code = po.country_code
        if not currency:
            currency = po.currency
        if not lines:
            lines = [
                {
                    "po_line_id": pl.id, "product_id": pl.product_id,
                    "product_name": pl.product_name, "sku": pl.sku,
                    "quantity": float(pl.quantity_ordered),
                    "unit_cost_fx": float(pl.unit_price),
                    "weight_kg": float(pl.weight) if pl.weight else None,
                    "volume_cbm": float(pl.volume) if pl.volume else None,
                }
                for pl in po.lines if pl.quantity_ordered > 0
            ]
    supplier = db.query(Vendor).filter(Vendor.id == supplier_id).first() if supplier_id else None
    shipment = ImportShipment(
        shipment_ref=shipment_ref, po_id=po_id,
        supplier_id=supplier_id, supplier_name=supplier.name if supplier else None,
        origin_country=origin_country, port_of_loading=port_of_loading,
        port_of_discharge=port_of_discharge, vessel_name=vessel_name,
        bill_of_lading=bill_of_lading, container_number=container_number,
        shipment_date=shipment_date or _utcnow(),
        estimated_arrival=estimated_arrival,
        currency=currency, exchange_rate=Decimal(str(exchange_rate)),
        warehouse_id=warehouse_id, country_code=country_code,
        notes=notes, created_by=created_by, status="draft",
    )
    db.add(shipment)
    db.flush()
    product_cost_total = Decimal("0")
    for ld in (lines or []):
        qty = Decimal(str(ld.get("quantity", 0)))
        cost_fx = Decimal(str(ld.get("unit_cost_fx", 0)))
        cost_local = cost_fx * Decimal(str(exchange_rate))
        line_total = qty * cost_fx
        product_cost_total += line_total
        sl = ImportShipmentLine(
            shipment_id=shipment.id,
            po_line_id=ld.get("po_line_id"),
            product_id=ld.get("product_id"),
            product_name=ld.get("product_name"), sku=ld.get("sku"),
            hs_code=ld.get("hs_code"),
            quantity=qty, unit_cost_fx=cost_fx, unit_cost_local=cost_local,
            line_total_fx=line_total,
            weight_kg=Decimal(str(ld.get("weight_kg", 0))) if ld.get("weight_kg") else None,
            volume_cbm=Decimal(str(ld.get("volume_cbm", 0))) if ld.get("volume_cbm") else None,
            country_code=country_code,
        )
        db.add(sl)
    shipment.product_cost_total = product_cost_total
    db.commit()
    db.refresh(shipment)
    return shipment


def confirm_shipment(db: Session, shipment_id: int, actual_arrival: datetime = None) -> ImportShipment:
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    if shipment.status != "draft":
        raise ValueError(f"Cannot confirm shipment in status '{shipment.status}'")
    shipment.status = "in_transit"
    if actual_arrival:
        shipment.actual_arrival = actual_arrival
    _post_goods_in_transit_journal(db, shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


def _post_goods_in_transit_journal(db: Session, shipment: ImportShipment) -> None:
    total = Decimal("0")
    lines_by_product = {}
    for sl in shipment.lines:
        cost = (sl.unit_cost_local or sl.unit_cost_fx) * sl.quantity
        total += cost
        lines_by_product[sl.product_id] = cost
    if total <= 0:
        return
    if not db.query(Account).filter(Account.code == GOODS_IN_TRANSIT).first():
        logger.warning("Goods in Transit account (%s) not found — skipping journal", GOODS_IN_TRANSIT)
        return
    try:
        gl.create_journal_entry(db, JournalEntryCreate(
            entry_date=shipment.shipment_date or _utcnow(),
            reference_type="import_shipment", reference_id=shipment.id,
            description=f"Goods in transit — {shipment.shipment_ref}",
            currency=shipment.currency, country_code=shipment.country_code,
            lines=[
                JournalLineInput(
                    account_code=GOODS_IN_TRANSIT, side="debit",
                    amount=total,
                    description=f"Goods in transit {shipment.shipment_ref}",
                    entity_type="import_shipment", entity_id=shipment.id,
                ),
                JournalLineInput(
                    account_code=AP_ACCOUNT, side="credit",
                    amount=total,
                    description=f"AP accrual — {shipment.shipment_ref}",
                    entity_type="import_shipment", entity_id=shipment.id,
                ),
            ],
        ))
    except Exception as e:
        logger.warning("Goods in transit journal post failed: %s", e)


# ── Landed Cost Allocation ──


def allocate_landed_costs(
    db: Session, shipment_id: int, *,
    freight_cost: Decimal = None, insurance_cost: Decimal = None,
    port_charges: Decimal = None, inland_freight: Decimal = None,
    bank_charges: Decimal = None, other_costs: Decimal = None,
    allocation_method: str = "by_value",
    freight_vendor_id: int = None, insurance_vendor_id: int = None,
    created_by: int = None,
) -> ImportShipment:
    _ensure_import_accounts(db)
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    if shipment.status not in ("in_transit", "draft"):
        raise ValueError(f"Cannot allocate costs for shipment in status '{shipment.status}'")
    costs = {}
    if freight_cost is not None:
        costs["freight"] = Decimal(str(freight_cost))
    if insurance_cost is not None:
        costs["insurance"] = Decimal(str(insurance_cost))
    if port_charges is not None:
        costs["port_charges"] = Decimal(str(port_charges))
    if inland_freight is not None:
        costs["inland_freight"] = Decimal(str(inland_freight))
    if bank_charges is not None:
        costs["bank_charges"] = Decimal(str(bank_charges))
    if other_costs is not None:
        costs["other_costs"] = Decimal(str(other_costs))
    if not costs:
        return shipment
    lines = shipment.lines
    if not lines:
        raise ValueError("Shipment has no lines to allocate costs against")
    weights = _compute_allocation_weights(lines, allocation_method)
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("Cannot allocate — total allocation weight is zero")
    for cost_type, cost_amount in costs.items():
        _create_cost_allocation(db, shipment, cost_type, cost_amount, weights, total_weight,
                                allocation_method, created_by)
    shipment.freight_cost = (shipment.freight_cost or 0) + costs.get("freight", 0)
    shipment.insurance_cost = (shipment.insurance_cost or 0) + costs.get("insurance", 0)
    shipment.port_charges = (shipment.port_charges or 0) + costs.get("port_charges", 0)
    shipment.inland_freight = (shipment.inland_freight or 0) + costs.get("inland_freight", 0)
    shipment.bank_charges = (shipment.bank_charges or 0) + costs.get("bank_charges", 0)
    shipment.other_costs = (shipment.other_costs or 0) + costs.get("other_costs", 0)
    t = (shipment.freight_cost + shipment.insurance_cost + shipment.port_charges
         + shipment.inland_freight + shipment.bank_charges + shipment.other_costs)
    shipment.total_landed_cost = shipment.product_cost_total + t
    _post_landed_cost_journals(db, shipment, costs, created_by)
    db.commit()
    db.refresh(shipment)
    return shipment


def _compute_allocation_weights(lines: list[ImportShipmentLine], method: str) -> dict[int, Decimal]:
    weights = {}
    if method == "by_value":
        for l in lines:
            weights[l.id] = l.line_total_fx
    elif method == "by_weight":
        for l in lines:
            w = l.weight_kg or Decimal("0")
            weights[l.id] = w
    elif method == "by_volume":
        for l in lines:
            v = l.volume_cbm or Decimal("0")
            weights[l.id] = v
    elif method == "by_quantity":
        for l in lines:
            weights[l.id] = l.quantity
    else:
        for l in lines:
            weights[l.id] = l.line_total_fx
    return weights


def _create_cost_allocation(db: Session, shipment: ImportShipment, cost_type: str,
                             total_amount: Decimal, weights: dict, total_weight: Decimal,
                             method: str, created_by: int = None) -> None:
    cost_label = cost_type.replace("_", " ").title()
    alloc = LandedCostAllocation(
        shipment_id=shipment.id,
        cost_type=cost_type,
        description=f"{cost_label} — {shipment.shipment_ref}",
        total_amount=total_amount,
        allocation_method=method,
        currency=shipment.currency,
        exchange_rate=shipment.exchange_rate,
        country_code=shipment.country_code,
        status="allocated",
    )
    db.add(alloc)
    db.flush()
    field_map = {
        "freight": "allocated_freight",
        "insurance": "allocated_insurance",
        "port_charges": "allocated_port",
        "inland_freight": "allocated_other",
        "bank_charges": "allocated_other",
        "other_costs": "allocated_other",
    }
    target_field = field_map.get(cost_type, "allocated_other")
    for sl in shipment.lines:
        share = total_amount * (weights.get(sl.id, Decimal("0")) / total_weight)
        share = share.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        setattr(sl, target_field, (getattr(sl, target_field) or 0) + share)
        allocated = (sl.allocated_freight + sl.allocated_insurance + sl.allocated_port
                     + sl.allocated_other)
        total_cost = (sl.unit_cost_local or sl.unit_cost_fx) * sl.quantity + allocated
        sl.landed_unit_cost = (total_cost / sl.quantity).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _post_landed_cost_journals(db: Session, shipment: ImportShipment, costs: dict,
                                created_by: int = None) -> None:
    account_map = {
        "freight": (GOODS_IN_TRANSIT, AP_ACCOUNT),
        "insurance": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "port_charges": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "inland_freight": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "bank_charges": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
        "other_costs": (GOODS_IN_TRANSIT, CASH_ACCOUNT),
    }
    for cost_type, amount in costs.items():
        if amount <= 0:
            continue
        dr, cr = account_map.get(cost_type, (GOODS_IN_TRANSIT, CASH_ACCOUNT))
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="landed_cost", reference_id=shipment.id,
                description=f"{cost_type.replace('_', ' ').title()} — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=dr, side="debit", amount=amount,
                        description=f"{cost_type} allocated to {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                    JournalLineInput(
                        account_code=cr, side="credit", amount=amount,
                        description=f"{cost_type} — {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                ],
            ))
        except Exception as e:
            logger.warning("Landed cost journal failed for %s: %s", cost_type, e)


# ── Customs ──


def record_customs_entry(db: Session, shipment_id: int, *,
                          customs_declaration_number: str = None,
                          customs_broker: str = None,
                          entry_date: datetime = None,
                          duty_rate: Decimal = None,
                          duty_amount: Decimal = None,
                          vat_on_duty: Decimal = None,
                          penalties: Decimal = None,
                          notes: str = None,
                          created_by: int = None) -> CustomsEntry:
    _ensure_import_accounts(db)
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    duty = Decimal(str(duty_amount)) if duty_amount else Decimal("0")
    vat = Decimal(str(vat_on_duty)) if vat_on_duty else Decimal("0")
    penalty = Decimal(str(penalties)) if penalties else Decimal("0")
    total_customs = duty + vat + penalty
    entry = CustomsEntry(
        shipment_id=shipment_id,
        customs_declaration_number=customs_declaration_number,
        customs_broker=customs_broker,
        entry_date=entry_date or _utcnow(),
        duty_rate_applied=Decimal(str(duty_rate)) if duty_rate else None,
        duty_amount=duty, vat_on_duty=vat,
        penalties=penalty, total_customs_cost=total_customs,
        status="cleared", notes=notes,
        country_code=shipment.country_code,
    )
    db.add(entry)
    db.flush()
    shipment.duty_cost = duty
    t = (shipment.freight_cost + shipment.insurance_cost + shipment.port_charges
         + shipment.inland_freight + shipment.bank_charges + shipment.other_costs)
    shipment.total_landed_cost = shipment.product_cost_total + t + duty + vat + penalty
    if total_customs > 0:
        for sl in shipment.lines:
            share = duty * (sl.line_total_fx / shipment.product_cost_total) if shipment.product_cost_total > 0 else 0
            sl.duty_amount = share
            allocated = (sl.allocated_freight + sl.allocated_insurance + sl.allocated_port
                         + sl.allocated_other + (sl.duty_amount or 0))
            total_cost = (sl.unit_cost_local or sl.unit_cost_fx) * sl.quantity + allocated
            sl.landed_unit_cost = (total_cost / sl.quantity).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=entry.entry_date,
                reference_type="customs_duty", reference_id=entry.id,
                description=f"Customs duty — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=GOODS_IN_TRANSIT, side="debit",
                        amount=total_customs,
                        description=f"Duty for {shipment.shipment_ref}",
                        entity_type="customs_entry", entity_id=entry.id,
                    ),
                    JournalLineInput(
                        account_code=CUSTOMS_DUTY_PAYABLE, side="credit",
                        amount=total_customs,
                        description=f"Duty payable for {shipment.shipment_ref}",
                        entity_type="customs_entry", entity_id=entry.id,
                    ),
                ],
            ))
        except Exception as e:
            logger.warning("Customs journal post failed: %s", e)
    db.commit()
    db.refresh(entry)
    return entry


# ── Finalize ──


def finalize_landed_cost(db: Session, shipment_id: int, warehouse_id: int = None,
                          created_by: int = None) -> ImportShipment:
    from domains.catalog.ports import Product
    shipment = db.query(ImportShipment).options(
        joinedload(ImportShipment.lines)
    ).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    if shipment.status not in ("in_transit", "customs_cleared"):
        raise ValueError(f"Cannot finalize shipment in status '{shipment.status}'")
    warehouse = None
    if warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    elif shipment.warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == shipment.warehouse_id).first()
    if not warehouse:
        raise ValueError("Warehouse is required to finalize landed cost")
    total_inventory = Decimal("0")
    for sl in shipment.lines:
        if sl.landed_unit_cost and sl.quantity:
            line_total = sl.landed_unit_cost * sl.quantity
            total_inventory += line_total
            product = db.query(Product).filter(Product.id == sl.product_id).first()
            if product:
                new_cost = sl.landed_unit_cost
                product.cost_price = new_cost
                product.stock = (product.stock or 0) + int(sl.quantity)
    if total_inventory > 0:
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=_utcnow(),
                reference_type="landed_cost_finalize", reference_id=shipment.id,
                description=f"Landed cost finalization — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=INVENTORY, side="debit",
                        amount=total_inventory,
                        description=f"Inventory from {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                    JournalLineInput(
                        account_code=GOODS_IN_TRANSIT, side="credit",
                        amount=total_inventory,
                        description=f"Goods in transit cleared — {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                ],
            ))
        except Exception as e:
            logger.warning("Landed cost finalization journal failed: %s", e)
    shipment.warehouse_id = warehouse.id
    shipment.status = "landed"
    db.commit()
    db.refresh(shipment)
    return shipment


# ── FX Revaluation ──


def run_fx_revaluation(db: Session, as_of: date = None, country_code: str = None,
                        created_by: int = None) -> list[dict]:
    _ensure_import_accounts(db)
    as_of = as_of or date.today()
    results = []
    shipments = db.query(ImportShipment).filter(
        ImportShipment.status.in_(["in_transit", "customs_cleared", "landed"]),
        ImportShipment.exchange_rate.isnot(None),
    )
    if country_code:
        shipments = shipments.filter(ImportShipment.country_code == country_code)
    for shipment in shipments.all():
        current_rate = Decimal(str(shipment.exchange_rate))
        diff = Decimal("0")
        if current_rate != Decimal("1"):
            open_balance = shipment.total_landed_cost or shipment.product_cost_total
            revalued = open_balance * current_rate
            diff = revalued - open_balance
        if abs(diff) < Decimal("0.01"):
            continue
        try:
            entry = gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=datetime(as_of.year, as_of.month, as_of.day, 23, 59, 59),
                reference_type="fx_revaluation", reference_id=shipment.id,
                description=f"FX revaluation — {shipment.shipment_ref}",
                currency=shipment.currency, country_code=shipment.country_code,
                lines=[
                    JournalLineInput(
                        account_code=FX_GAIN_LOSS, side="debit" if diff > 0 else "credit",
                        amount=abs(diff),
                        description=f"FX adj for {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                    JournalLineInput(
                        account_code=AP_ACCOUNT, side="credit" if diff > 0 else "debit",
                        amount=abs(diff),
                        description=f"FX adj AP — {shipment.shipment_ref}",
                        entity_type="import_shipment", entity_id=shipment.id,
                    ),
                ],
            ))
            results.append({
                "shipment_id": shipment.id,
                "shipment_ref": shipment.shipment_ref,
                "fx_adjustment": float(diff),
                "journal_entry_id": entry.id,
            })
        except Exception as e:
            logger.warning("FX revaluation failed for %s: %s", shipment.shipment_ref, e)
    return results


# ── Cost Template ──


def create_cost_template(db: Session, *, name: str,
                          default_duty_rate: Decimal = None,
                          default_freight_percent: Decimal = None,
                          default_insurance_percent: Decimal = None,
                          default_port_charges_percent: Decimal = None,
                          default_bank_charges_percent: Decimal = None,
                          allocation_method: str = "by_value",
                          country_code: str = None) -> ImportCostTemplate:
    existing = db.query(ImportCostTemplate).filter(
        ImportCostTemplate.name == name,
        ImportCostTemplate.country_code == country_code,
    ).first()
    if existing:
        raise ValueError(f"Cost template '{name}' already exists for this country")
    tmpl = ImportCostTemplate(
        name=name,
        default_duty_rate=default_duty_rate,
        default_freight_percent=default_freight_percent,
        default_insurance_percent=default_insurance_percent,
        default_port_charges_percent=default_port_charges_percent,
        default_bank_charges_percent=default_bank_charges_percent,
        allocation_method=allocation_method,
        country_code=country_code,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


def auto_allocate_from_template(db: Session, shipment_id: int,
                                  template_id: int = None,
                                  country_code: str = None,
                                  created_by: int = None) -> ImportShipment:
    shipment = db.query(ImportShipment).filter(ImportShipment.id == shipment_id).first()
    if not shipment:
        raise ValueError("Shipment not found")
    tmpl = None
    if template_id:
        tmpl = db.query(ImportCostTemplate).filter(ImportCostTemplate.id == template_id).first()
    else:
        tmpl = _get_cost_template(db, country_code or shipment.country_code)
    if not tmpl:
        raise ValueError("No cost template found. Create one or specify template_id.")
    product_cost = shipment.product_cost_total or Decimal("0")
    costs = {}
    if tmpl.default_freight_percent:
        costs["freight_cost"] = product_cost * tmpl.default_freight_percent / Decimal("100")
    if tmpl.default_insurance_percent:
        costs["insurance_cost"] = product_cost * tmpl.default_insurance_percent / Decimal("100")
    if tmpl.default_port_charges_percent:
        costs["port_charges"] = product_cost * tmpl.default_port_charges_percent / Decimal("100")
    if tmpl.default_bank_charges_percent:
        costs["bank_charges"] = product_cost * tmpl.default_bank_charges_percent / Decimal("100")
    return allocate_landed_costs(
        db, shipment_id, allocation_method=tmpl.allocation_method,
        created_by=created_by, **costs,
    )


# ── Listing ──


def list_shipments(db: Session, status: str = None, po_id: int = None,
                    country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(ImportShipment)
    if status:
        q = q.filter(ImportShipment.status == status)
    if po_id:
        q = q.filter(ImportShipment.po_id == po_id)
    if country_code:
        q = q.filter(ImportShipment.country_code == country_code)
    total = q.count()
    rows = keyset_offset_window(q.order_by(ImportShipment.id.desc()), offset=offset, limit=limit)
    return {"total": total, "items": rows}


def list_templates(db: Session, country_code: str = None) -> list[ImportCostTemplate]:
    q = db.query(ImportCostTemplate)
    if country_code:
        q = q.filter(ImportCostTemplate.country_code == country_code)
    return q.order_by(ImportCostTemplate.name).all()


def get_import_shipment(db: Session, shipment_id: int) -> ImportShipment | None:
    """Fetch a single import shipment by id (extracted from the admin logistics
    imports router so it stays a thin HTTP layer)."""
    return db.query(ImportShipment).filter(ImportShipment.id == shipment_id).first()


def __getattr__(name: str):
    import sys

    if name == "import_service":
        return sys.modules[__name__]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# === MERGED from expense_processing.py ===

_AuditLog_model = None
def _get_AuditLog():
    global _AuditLog_model
    if _AuditLog_model is None:
        from domains.governance.ports import AuditLog as _A
        _AuditLog_model = _A
    return _AuditLog_model
from domains.governance.models.admin import EmployeeExpense
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class ExpenseProcessingService:
    """
    Expense validation and reimbursement processing.
    """
    
    PER_DIEM_LIMITS = {
        "OMR": Decimal("50.000"),
        "AED": Decimal("50.000"),
        "SAR": Decimal("50.000"),
        "QAR": Decimal("50.000"),
        "KWD": Decimal("15.000"),
        "BHD": Decimal("50.000"),
        "OMR": Decimal("50.000"),
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_expense(self, expense: EmployeeExpense) -> tuple:
        """Validate expense against policy."""
        errors = []
        
        if expense.amount <= 0:
            errors.append("Amount must be positive")
        
        per_diem = self.PER_DIEM_LIMITS.get(expense.currency, Decimal("50.000"))
        if expense.amount > per_diem:
            errors.append(f"Exceeds per-diems limit of {per_diem} {expense.currency}")
        
        return len(errors) == 0, errors
    
    def submit_expense(
        self,
        employee_id: int,
        expense_type: str,
        amount: float,
        currency: str,
        expense_date: datetime,
        receipt_url: Optional[str] = None,
    ) -> EmployeeExpense:
        """Submit an expense for approval."""
        expense = EmployeeExpense(
            employee_id=employee_id,
            expense_type=expense_type,
            amount=amount,
            currency=currency,
            expense_date=expense_date,
            receipt_url=receipt_url,
            submitted_at=_utcnow(),
            status="submitted",
        )
        
        is_valid, errors = self.validate_expense(expense)
        if not is_valid:
            expense.status = "rejected"
            expense.approval_notes = "; ".join(errors)
        
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def approve_expense(self, expense_id: int, approver_id: int, approved: bool) -> bool:
        """Approve or reject an expense."""
        expense = (
            self.db.query(EmployeeExpense)
            .filter(EmployeeExpense.id == expense_id)
            .first()
        )
        if not expense:
            return False
        
        expense.status = "approved" if approved else "rejected"
        expense.approved_by = approver_id
        expense.approved_at = _utcnow()
        
        audit = _get_AuditLog()(
            event_type="expense_approval",
            actor_id=approver_id,
            action="approve" if approved else "reject",
            resource_type="expense",
            resource_id=expense_id,
            occurred_at=_utcnow(),
        )
        self.db.add(audit)
        self.db.commit()
        return True
    
    def process_reimbursement(self, expense_id: int) -> dict:
        """Process reimbursement payment."""
        expense = (
            self.db.query(EmployeeExpense)
            .filter(EmployeeExpense.id == expense_id)
            .first()
        )
        if not expense:
            return {"status": "not_found"}
        
        expense.status = "paid"
        self.db.commit()
        
        return {"status": "processed", "amount": expense.amount}

# === MERGED from expense_routing.py ===

"""
Expense Claims Routing System
Routes expense claims based on amount, department, and approval hierarchy
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict

from sqlalchemy import and_
from sqlalchemy.orm import Session

from domains.hr.ports import Employee
from domains.governance.ports import User

logger = logging.getLogger("zozi.expense")


class ExpenseRoutingEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def get_approval_chain(self, employee_id: int, amount: Decimal) -> List[Dict]:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return []
        
        chain = []
        current_level = 1
        
        reporting_manager_id = employee.reporting_manager_id
        if reporting_manager_id:
            manager = self.db.query(Employee).filter(Employee.id == reporting_manager_id).first()
            if manager:
                chain.append({
                    "level": current_level,
                    "employee_id": manager.id,
                    "approver_id": manager.user_id,
                    "max_amount": Decimal("5000.00"),
                    "required": amount > Decimal("1000.00")
                })
                current_level += 1
        
        if employee.department in ["finance", "operations", "admin"]:
            department_head = self.db.query(Employee).filter(
                Employee.department == employee.department,
                Employee.position.ilike("%head%")
            ).first()
            if department_head and department_head.id != reporting_manager_id:
                chain.append({
                    "level": current_level,
                    "employee_id": department_head.id,
                    "approver_id": department_head.user_id,
                    "max_amount": Decimal("50000.00"),
                    "required": amount > Decimal("10000.00")
                })
                current_level += 1
        
        if amount > Decimal("50000.00"):
            cfo = self.db.query(Employee).filter(
                Employee.position.ilike("%cfo%")
            ).first()
            if cfo:
                chain.append({
                    "level": current_level,
                    "employee_id": cfo.id,
                    "approver_id": cfo.user_id,
                    "max_amount": Decimal("1000000.00"),
                    "required": True
                })
        
        return chain
    
    def route_expense_claim(self, employee_id: int, amount: Decimal, 
                            category: str, description: str) -> dict:
        chain = self.get_approval_chain(employee_id, amount)
        
        if not chain:
            return {
                "routed": False,
                "error": "No approval chain found",
                "employee_id": employee_id
            }
        
        first_approver = next((a for a in chain if a["required"]), chain[0])
        
        return {
            "routed": True,
            "employee_id": employee_id,
            "amount": str(amount),
            "category": category,
            "approval_chain": chain,
            "first_approver": first_approver,
            "routing_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def calculate_reimbursement_deadline(self, submission_date: datetime, 
                                         priority: str = "normal") -> datetime:
        from datetime import timedelta
        
        if priority == "urgent":
            return submission_date + timedelta(days=3)
        elif priority == "high":
            return submission_date + timedelta(days=7)
        else:
            return submission_date + timedelta(days=14)


def get_expense_router(db: Session) -> ExpenseRoutingEngine:
    return ExpenseRoutingEngine(db)

# === MERGED from invoice_service.py ===

"""
Invoice Controller — supply chain invoice management.
Covers the full lifecycle: supplier → logistics → customer receipt.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from domains.governance.ports import User
from domains.catalog.ports import Product
from domains.finance.models.finance import Invoice
from domains.finance.models.finance import InvoiceItem
from domains.logistics.models.logistics import Shipment
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem

logger = logging.getLogger(__name__)
_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731

ALLOWED_STATUSES = ("draft", "issued", "in_transit", "delivered", "cancelled")


def _generate_invoice_number() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    uid = str(uuid.uuid4()).split("-")[0].upper()
    return f"INV-{stamp}-{uid}"


def _serialize_invoice(inv: Invoice) -> dict:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "order_id": inv.order_id,
        "supplier_id": inv.supplier_id,
        "shipment_id": inv.shipment_id,
        "status": inv.status,
        "invoice_type": inv.invoice_type,
        "subtotal": float(inv.subtotal or 0),
        "tax_amount": float(inv.tax_amount or 0),
        "shipping_amount": float(inv.shipping_amount or 0),
        "discount_amount": float(inv.discount_amount or 0),
        "total_amount": float(inv.total_amount or 0),
        "currency": inv.currency,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "due_at": inv.due_at.isoformat() if inv.due_at else None,
        "picked_at": inv.picked_at.isoformat() if inv.picked_at else None,
        "dispatched_at": inv.dispatched_at.isoformat() if inv.dispatched_at else None,
        "delivered_at": inv.delivered_at.isoformat() if inv.delivered_at else None,
        "notes": inv.notes,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "supplier_name": inv.supplier.username if inv.supplier else None,
        "items": [_serialize_item(i) for i in (inv.items or [])],
    }


def _serialize_item(item: InvoiceItem) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "description": item.description,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price or 0),
        "discount_amount": float(item.discount_amount or 0),
        "tax_rate": item.tax_rate,
        "line_total": float(item.line_total or 0),
    }


# ── List ──────────────────────────────────────────────────────────────────────

def list_invoices(
    current_user: dict,
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    order_id: Optional[int] = None,
) -> dict:
    role = current_user.get("role")
    q = db.query(Invoice)

    if role == "supplier":
        q = q.filter(Invoice.supplier_id == current_user["id"])
    elif role not in ("admin", "sub_admin", "moderator", "support"):
        # Customer: only their orders
        q = q.join(Order).filter(Order.user_id == current_user["id"])

    if status:
        q = q.filter(Invoice.status == status)
    if order_id:
        q = q.filter(Invoice.order_id == order_id)

    total = q.count()
    items = q.order_by(desc(Invoice.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": [_serialize_invoice(i) for i in items],
    }


def get_invoice(invoice_id: int, current_user: dict, db: Session) -> dict:
    inv = (
        db.query(Invoice)
        .options(selectinload(Invoice.supplier), selectinload(Invoice.items))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    role = current_user.get("role")
    uid = current_user["id"]
    if role == "supplier" and inv.supplier_id != uid:
        raise HTTPException(status_code=403, detail="Access denied")
    if role == "customer":
        order = db.query(Order).filter(Order.id == inv.order_id, Order.user_id == uid).first()
        if not order:
            raise HTTPException(status_code=403, detail="Access denied")

    return _serialize_invoice(inv)


# ── Create from order ─────────────────────────────────────────────────────────

def create_invoice_from_order(data: dict, current_user: dict, db: Session) -> dict:
    """Supplier or admin creates an invoice for an order."""
    role = current_user.get("role")
    if role not in ("supplier", "admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Supplier or admin access required")

    order_id = data.get("order_id")
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id is required")

    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    supplier_id = current_user["id"] if role == "supplier" else data.get("supplier_id", current_user["id"])

    # Check no duplicate invoice for same order+supplier
    existing = db.query(Invoice).filter(
        Invoice.order_id == order_id,
        Invoice.supplier_id == supplier_id,
        Invoice.invoice_type == "sale",
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Invoice already exists for this order")

    # Build line items from order items belonging to this supplier
    supplier_items = [
        item for item in order.items
        if item.product and item.product.supplier_id == supplier_id
    ]
    if role == "admin" and not supplier_items:
        supplier_items = order.items  # Admin can create for full order

    if not supplier_items:
        raise HTTPException(status_code=404, detail="No items found for this supplier in the order")

    subtotal = sum(float(i.price) * i.quantity for i in supplier_items)
    country_code = order.country_code or "SA"
    tax_result = calculate_tax(Decimal(str(subtotal)), country_code, db)
    tax_rate = float(tax_result["tax_rate"])
    tax_amount = float(tax_result["tax_amount"])
    shipping_amount = float(order.shipping_amount or 0)
    discount_amount = float(order.discount_amount or 0)
    total_amount = subtotal + tax_amount + shipping_amount - discount_amount

    inv = Invoice(
        invoice_number=_generate_invoice_number(),
        order_id=order_id,
        supplier_id=supplier_id,
        shipment_id=data.get("shipment_id"),
        status="issued",
        invoice_type="sale",
        subtotal=subtotal,
        tax_amount=tax_amount,
        shipping_amount=shipping_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        currency=data.get("currency", "AED"),
        issued_at=_utcnow(),
        notes=data.get("notes"),
    )
    db.add(inv)
    db.flush()

    for item in supplier_items:
        line_total = float(item.price) * item.quantity
        db.add(InvoiceItem(
            invoice_id=inv.id,
            product_id=item.product_id,
            description=item.product.name if item.product else f"Product #{item.product_id}",
            quantity=item.quantity,
            unit_price=float(item.price),
            discount_amount=0,
            tax_rate=tax_rate * 100,
            line_total=line_total,
        ))

    db.commit()
    db.refresh(inv)
    audit_log(
        db=db,
        user_id=current_user["id"],
        username=current_user.get("username", ""),
        user_role=role,
        action=AuditAction.INVOICE_CREATED,
        resource_type="invoice",
        resource_id=str(inv.id),
        details={"invoice_number": inv.invoice_number, "order_id": order_id},
    )
    # Email the invoice to the customer — enqueued async, failure is non-blocking
    try:
        from domains.comms.ports import enqueue_invoice_email
        enqueue_invoice_email(cast(int, inv.id))
    except Exception:
        logger.warning("Failed to enqueue invoice email for invoice %s", inv.id)
    return _serialize_invoice(inv)


# ── Update status ─────────────────────────────────────────────────────────────

def update_invoice_status(invoice_id: int, data: dict, current_user: dict, db: Session) -> dict:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    role = current_user.get("role")
    if role == "supplier" and inv.supplier_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if role not in ("supplier", "admin", "sub_admin", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    new_status = data.get("status")
    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed: {ALLOWED_STATUSES}")

    prev_status = inv.status
    inv.status = new_status
    now = _utcnow()
    if new_status == "in_transit":
        if not inv.picked_at:
            inv.picked_at = data.get("picked_at") or now
        if not inv.dispatched_at:
            inv.dispatched_at = data.get("dispatched_at") or now
    if new_status == "delivered" and not inv.delivered_at:
        inv.delivered_at = data.get("delivered_at") or now
    if "notes" in data:
        inv.notes = data["notes"]
    if "shipment_id" in data:
        inv.shipment_id = data["shipment_id"]

    inv.updated_at = now
    db.commit()
    db.refresh(inv)
    audit_log(
        db=db,
        user_id=current_user["id"],
        username=current_user.get("username", ""),
        user_role=role,
        action=AuditAction.INVOICE_STATUS_UPDATED,
        resource_type="invoice",
        resource_id=str(inv.id),
        details={"invoice_number": inv.invoice_number, "prev_status": prev_status, "new_status": new_status},
    )
    # Email delivery confirmation to customer — enqueued async, failure is non-blocking
    if new_status == "delivered":
        try:
            enqueue_invoice_email(cast(int, inv.id))
        except Exception:
            logger.warning("Failed to enqueue delivery confirmation email for invoice %s", inv.id)
    return _serialize_invoice(inv)


# ── Admin overview ─────────────────────────────────────────────────────────────

def get_invoice_overview(db: Session) -> dict:
    from sqlalchemy import func as sqlfunc
    total = db.query(Invoice).count()
    by_status = db.query(Invoice.status, sqlfunc.count(Invoice.id)).group_by(Invoice.status).all()
    total_value = db.query(sqlfunc.sum(Invoice.total_amount)).scalar() or 0
    recent = db.query(Invoice).order_by(desc(Invoice.created_at)).limit(10).all()
    return {
        "total_invoices": total,
        "total_value": float(total_value),
        "by_status": {s: c for s, c in by_status},
        "recent": [_serialize_invoice(i) for i in recent],
    }

# === MERGED from invoice_write_service.py ===

"""Invoice write operations (canonical module).

Implements the invoice domain write surface. Previously stubbed with
``_missing_symbol`` placeholders; now contains real DB-write logic.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from domains.finance.models.finance import Invoice
from domains.finance.models.finance import InvoiceItem
import structlog
logger = structlog.get_logger(__name__)


def _apply_changes(record, changes: dict) -> None:
    for key, value in changes.items():
        if value is not None:
            setattr(record, key, value)


def create_invoice_with_items(
    db: Session,
    invoice_data: dict | None = None,
    items: list[dict] | None = None,
    **fields,
) -> Invoice:
    """Create an invoice with line items.

    Tolerant of both call shapes:
      * ``create_invoice_with_items(db, invoice_data, items)``  (controller, positional)
      * ``create_invoice_with_items(db, order_id=..., items=..., ...)`` (keyword/legacy)
    """
    if isinstance(invoice_data, dict):
        data = dict(invoice_data)
        if items is not None:
            data.setdefault("items", items)
        data.update(fields)
    else:
        data = dict(fields)
        if items is not None:
            data.setdefault("items", items)

    items_list = data.pop("items", None) or []

    order_id = data.get("order_id")
    if order_id is None:
        raise ValueError("order_id is required to create an invoice")
    order_id = int(order_id)
    shipment_id = data.get("shipment_id")
    supplier_id = data.get("supplier_id")
    invoice_type = data.get("invoice_type", "sale")
    tax_amount = data.get("tax_amount")
    shipping_amount = data.get("shipping_amount")
    discount_amount = data.get("discount_amount")
    currency = data.get("currency", "USD")
    country_code = data.get("country_code")
    notes = data.get("notes")

    subtotal = Decimal("0")
    invoice_items = []
    for item in items_list:
        quantity = int(item.get("quantity", 1))
        unit_price = Decimal(str(item.get("unit_price", 0)))
        discount = Decimal(str(item.get("discount_amount") or 0))
        tax_rate = Decimal(str(item.get("tax_rate") or 0))
        line_total = (unit_price * quantity - discount) * (Decimal("1") + tax_rate / Decimal("100"))
        subtotal += line_total
        invoice_items.append(
            InvoiceItem(
                product_id=item.get("product_id"),
                description=item.get("description", ""),
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=discount,
                tax_rate=tax_rate,
                line_total=line_total,
                country_code=country_code,
            )
        )

    total = subtotal + Decimal(str(shipping_amount or 0)) - Decimal(str(discount_amount or 0)) + Decimal(str(tax_amount or 0))
    invoice = Invoice(
        order_id=order_id,
        shipment_id=shipment_id,
        supplier_id=supplier_id,
        invoice_type=invoice_type,
        subtotal=subtotal,
        tax_amount=tax_amount,
        shipping_amount=shipping_amount,
        discount_amount=discount_amount,
        total_amount=total,
        currency=currency,
        country_code=country_code,
        notes=notes,
        **{k: v for k, v in data.items() if k not in _RESERVED_INVOICE_KEYS},
    )
    db.add(invoice)
    db.flush()
    for item in invoice_items:
        item.invoice_id = invoice.id
        db.add(item)
    db.commit()
    db.refresh(invoice)
    return invoice


# Keys consumed explicitly by create_invoice_with_items so they are not
# double-applied as generic model fields.
_RESERVED_INVOICE_KEYS = frozenset(
    {
        "order_id",
        "shipment_id",
        "supplier_id",
        "invoice_type",
        "tax_amount",
        "shipping_amount",
        "discount_amount",
        "currency",
        "country_code",
        "notes",
        "items",
    }
)


def update_invoice(db: Session, invoice_id: int, **changes) -> Invoice:
    obj = db.get(Invoice, invoice_id)
    if obj is None:
        raise ValueError(f"Invoice {invoice_id} not found")
    _apply_changes(obj, changes)
    db.commit()
    db.refresh(obj)
    return obj

# === MERGED from finance_automation.py ===

"""Finance Automation Service.



Implements the ERP-level automation requested for the admin Finance module:

  * Bill scanning (OCR) -> expense record -> GL posting

  * Configurable bank-statement line -> GL account mapping

  * Auto bank reconciliation driven by mapping rules

  * Fixed-asset depreciation runs

  * Accrual / reversal engine



All GL writes go through `general_ledger_service.create_journal_entry` so the

immutable, double-entry ledger and audit trail remain the single source of truth.

"""

from infrastructure.utils.datetime_utils import utcnow



import logging

from datetime import datetime, date, timedelta

from decimal import Decimal

from typing import Optional



from sqlalchemy.orm import Session



from domains.finance.models.finance import Account
from domains.finance.models.finance import ScannedExpense
from domains.finance.models.finance import BankMappingRule
from domains.finance.models.finance import BankStatementImport
from domains.finance.models.finance import BankStatementLine
from domains.finance.models.finance import FixedAsset
from domains.finance.models.finance import Accrual
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import JournalEntry

from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput

from kernel.money import round_money




logger = logging.getLogger(__name__)





# ── OCR / bill scanning ────────────────────────────────────────────────────────





def post_scanned_expense(

    db: Session,

    *,

    employee_id: Optional[int],

    vendor_name: str,

    amount: Decimal,

    currency: str = "OMR",

    expense_date: Optional[datetime] = None,

    tax_amount: Decimal = Decimal("0.00"),

    category: Optional[str] = None,

    description: Optional[str] = None,

    image_url: Optional[str] = None,

    ocr_raw_text: Optional[str] = None,

    ocr_confidence: Optional[Decimal] = None,

    expense_account_code: str = "5030",

    country_code: Optional[str] = None,

    reviewed_by: Optional[int] = None,

) -> ScannedExpense:

    """Record a bill scanned by OCR and post it to the GL (expense -> accrued payable).



    Dr.  <expense_account>   (net of VAT)

    Dr.  VAT Payable (2040)  (input VAT, if any)

    Cr.  Accrued Expenses (2080)

    """

    expense_date = expense_date or utcnow()

    net_amount = round_money(amount - tax_amount)



    scanned = ScannedExpense(

        employee_id=employee_id,

        vendor_name=vendor_name,

        amount=round_money(amount),

        currency=currency,

        expense_date=expense_date,

        tax_amount=round_money(tax_amount),

        category=category,

        description=description,

        image_url=image_url,

        ocr_raw_text=ocr_raw_text,

        ocr_confidence=ocr_confidence,

        expense_account_code=expense_account_code,

        status="posted",

        reviewed_by=reviewed_by,

        country_code=country_code,

    )

    db.add(scanned)

    db.flush()



    lines = [

        JournalLineInput(

            account_code=expense_account_code, side="debit", amount=net_amount,

            description=f"Expense: {vendor_name}", entity_type="scanned_expense", entity_id=scanned.id,

        ),

    ]

    if tax_amount > 0:

        lines.append(JournalLineInput(

            account_code="2040", side="debit", amount=round_money(tax_amount),

            description=f"Input VAT on {vendor_name}", entity_type="scanned_expense", entity_id=scanned.id,

        ))

    lines.append(JournalLineInput(

        account_code="2080", side="credit", amount=round_money(amount),

        description=f"Accrued expense {vendor_name}", entity_type="scanned_expense", entity_id=scanned.id,

    ))



    entry = _post_gl(db, lines, f"OCR scanned expense - {vendor_name}", "scanned_expense",

                     scanned.id, currency, country_code, reviewed_by)

    scanned.posted_journal_entry_id = entry.id

    db.commit()

    db.refresh(scanned)

    return scanned





# ── Bank statement mapping ──────────────────────────────────────────────────────





def create_mapping_rule(

    db: Session,

    *,

    name: str,

    match_pattern: str,

    account_code: str,

    normal_side: str,

    country_code: Optional[str] = None,

    description_contains: Optional[str] = None,

    category: Optional[str] = None,

    priority: int = 100,

    created_by: Optional[int] = None,

) -> BankMappingRule:

    if not _account_exists(db, account_code):

        raise ValueError(f"Account '{account_code}' not found")

    rule = BankMappingRule(

        name=name, match_pattern=match_pattern, account_code=account_code,

        normal_side=normal_side, country_code=country_code,

        description_contains=description_contains, category=category,

        priority=priority, created_by=created_by,

    )

    db.add(rule)

    db.commit()

    db.refresh(rule)

    return rule





def _account_exists(db: Session, code: str) -> bool:

    return db.query(Account).filter(Account.code == code).first() is not None





def _parse_date(value) -> Optional[date]:

    if value is None or value == "":

        return None

    if isinstance(value, date) and not isinstance(value, datetime):

        return value

    if isinstance(value, datetime):

        return value.date()

    s = str(value).strip()

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):

        try:

            return datetime.strptime(s, fmt).date()

        except ValueError:

            continue

    # last resort: try ISO with time

    try:

        return datetime.fromisoformat(s).date()

    except ValueError:

        return None





def _match_rule(db: Session, description: str, country_code: Optional[str]) -> Optional[BankMappingRule]:

    q = db.query(BankMappingRule).filter(BankMappingRule.is_active == True)  # noqa: E712

    if country_code:

        q = q.filter((BankMappingRule.country_code == country_code) | (BankMappingRule.country_code.is_(None)))

    else:

        q = q.filter(BankMappingRule.country_code.is_(None))

    rules = q.order_by(BankMappingRule.priority.asc(), BankMappingRule.id.asc()).all()

    desc = (description or "").lower()

    for rule in rules:

        pattern = (rule.match_pattern or "").lower()

        if not pattern:

            continue

        if pattern in desc:

            return rule

    return None





def import_bank_statement(

    db: Session,

    *,

    lines: list[dict],

    bank_name: Optional[str] = None,

    file_name: Optional[str] = None,

    currency: str = "OMR",

    country_code: Optional[str] = None,

    imported_by: Optional[int] = None,

    period_start: Optional[datetime] = None,

    period_end: Optional[datetime] = None,

) -> BankStatementImport:

    """Bulk import statement lines and auto-map them via mapping rules."""

    imp = BankStatementImport(

        bank_name=bank_name, file_name=file_name, currency=currency,

        country_code=country_code, imported_by=imported_by,

        statement_period_start=period_start, statement_period_end=period_end,

        total_lines=len(lines),

    )

    db.add(imp)

    db.flush()



    matched = 0

    for ln in lines:

        desc = ln.get("description") or ""

        rule = _match_rule(db, desc, country_code)

        line = BankStatementLine(

            import_id=imp.id,

            txn_date=_parse_date(ln.get("txn_date")),

            description=desc,

            reference=ln.get("reference"),

            amount=Decimal(str(ln.get("amount", 0))),

            mapped_account_code=rule.account_code if rule else None,

            mapped_side=rule.normal_side if rule else None,

            mapping_rule_id=rule.id if rule else None,

            status="mapped" if rule else "unmapped",

            country_code=country_code,

        )

        db.add(line)

        if rule:

            matched += 1

    imp.matched_lines = matched

    imp.unmatched_lines = len(lines) - matched

    db.commit()

    db.refresh(imp)

    return imp





def auto_post_mapped_lines(

    db: Session,

    import_id: int,

    *,

    country_code: Optional[str] = None,

    run_by: Optional[int] = None,

) -> dict:

    """Post all mapped-but-unposted statement lines to the GL."""

    lines = (

        db.query(BankStatementLine)

        .filter(BankStatementLine.import_id == import_id,

                BankStatementLine.status == "mapped",

                BankStatementLine.posted_journal_entry_id.is_(None))

        .all()

    )

    posted = 0

    for line in lines:

        side = line.mapped_side or "debit"

        je_lines = [JournalLineInput(

            account_code=line.mapped_account_code, side=side,

            amount=round_money(line.amount),

            description=line.description or "Bank statement line",

            entity_type="bank_statement_line", entity_id=line.id,

        )]

        contra = "1010" if line.mapped_account_code not in ("1010", "1020") else "2080"

        je_lines.append(JournalLineInput(

            account_code=contra, side="credit" if side == "debit" else "debit",

            amount=round_money(line.amount),

            description=f"Bank clearing for {line.description or line.id}",

            entity_type="bank_statement_line", entity_id=line.id,

        ))

        entry = _post_gl(db, je_lines, f"Bank statement: {line.description or line.id}",

                         "bank_statement_line", line.id, "OMR", country_code, run_by)

        line.posted_journal_entry_id = entry.id

        line.status = "posted"

        posted += 1

    db.commit()

    _log_automation(db, "mapping", len(lines), posted, {"import_id": import_id}, run_by, country_code)

    return {"lines": len(lines), "posted": posted}





# ── Fixed asset depreciation ────────────────────────────────────────────────────





def run_depreciation(

    db: Session,

    *,

    as_of: Optional[date] = None,

    country_code: Optional[str] = None,

    run_by: Optional[int] = None,

) -> dict:

    """Straight-line monthly depreciation for all active fixed assets."""

    as_of = as_of or date.today()

    q = db.query(FixedAsset).filter(FixedAsset.status == "active")  # noqa: E712

    if country_code:

        q = q.filter(FixedAsset.country_code == country_code)

    assets = q.all()



    processed = 0

    depreciated = 0

    for asset in assets:

        if asset.last_depreciated_date and asset.last_depreciated_date.date() >= as_of:

            continue

        months = _months_between(asset.last_depreciated_date or asset.purchase_date, as_of)

        if months <= 0:

            continue

        depreciable = round_money(asset.purchase_cost - asset.salvage_value)

        monthly = round_money(depreciable / Decimal(asset.useful_life_months))

        amount = round_money(monthly * months)

        remaining = round_money(depreciable - asset.accumulated_depreciation)

        if amount > remaining:

            amount = remaining

        if amount <= 0:

            asset.status = "fully_depreciated"

            db.flush()

            continue



        je_lines = [

            JournalLineInput(

                account_code=asset.depreciation_account_code, side="debit", amount=amount,

                description=f"Depreciation - {asset.name}", entity_type="fixed_asset", entity_id=asset.id,

            ),

            JournalLineInput(

                account_code=asset.accumulated_depr_account_code, side="credit", amount=amount,

                description=f"Accumulated depreciation - {asset.name}", entity_type="fixed_asset", entity_id=asset.id,

            ),

        ]

        entry = _post_gl(db, je_lines, f"Depreciation {asset.name}", "depreciation",

                         asset.id, "OMR", country_code, run_by)

        asset.accumulated_depreciation = round_money(asset.accumulated_depreciation + amount)

        asset.last_depreciated_date = datetime(as_of.year, as_of.month, as_of.day)

        if asset.accumulated_depreciation >= depreciable:

            asset.status = "fully_depreciated"

        processed += 1

        depreciated += 1

    db.commit()

    _log_automation(db, "depreciation", processed, depreciated, {}, run_by, country_code)

    return {"processed": processed, "depreciated": depreciated}





def _months_between(start: datetime, end: date) -> int:

    """Whole months between a datetime and a date (calendar-month boundaries)."""

    s = start.date() if isinstance(start, datetime) else start

    return (end.year - s.year) * 12 + (end.month - s.month)





# ── Accruals ─────────────────────────────────────────────────────────────────





def create_accrual(

    db: Session,

    *,

    accrual_type: str,

    amount: Decimal,

    expense_account_code: str,

    accrual_account_code: str,

    accrual_date: datetime,

    description: Optional[str] = None,

    reversal_date: Optional[datetime] = None,

    country_code: Optional[str] = None,

    created_by: Optional[int] = None,

) -> Accrual:

    accrual = Accrual(

        accrual_type=accrual_type, amount=round_money(amount),

        expense_account_code=expense_account_code, accrual_account_code=accrual_account_code,

        accrual_date=accrual_date, description=description, reversal_date=reversal_date,

        country_code=country_code, created_by=created_by,

    )

    db.add(accrual)

    db.flush()



    if accrual_type == "expense":

        lines = [

            JournalLineInput(account_code=expense_account_code, side="debit", amount=round_money(amount),

                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),

            JournalLineInput(account_code=accrual_account_code, side="credit", amount=round_money(amount),

                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),

        ]

    else:

        lines = [

            JournalLineInput(account_code=accrual_account_code, side="debit", amount=round_money(amount),

                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),

            JournalLineInput(account_code=expense_account_code, side="credit", amount=round_money(amount),

                             description=description or "Accrual", entity_type="accrual", entity_id=accrual.id),

        ]

    entry = _post_gl(db, lines, f"Accrual: {description or accrual_type}", "accrual",

                     accrual.id, "OMR", country_code, created_by)

    accrual.journal_entry_id = entry.id

    accrual.status = "open"

    db.commit()

    db.refresh(accrual)

    return accrual





def reverse_accrual(db: Session, accrual_id: int, *, run_by: Optional[int] = None) -> Accrual:

    accrual = db.query(Accrual).filter(Accrual.id == accrual_id).first()

    if not accrual:

        raise ValueError(f"Accrual {accrual_id} not found")

    if accrual.status != "open":

        raise ValueError(f"Accrual {accrual_id} is {accrual.status}")

    orig = db.query(JournalEntry).filter(JournalEntry.id == accrual.journal_entry_id).first()

    lines = []

    if orig:

        for l in orig.lines:

            lines.append(JournalLineInput(

                account_code=l.account.code, side="credit" if l.side == "debit" else "debit",

                amount=round_money(l.amount), description=f"Reverse accrual {accrual.id}",

                entity_type="accrual", entity_id=accrual.id,

            ))

    entry = _post_gl(db, lines, f"Reverse accrual {accrual.id}", "accrual_reversal",

                     accrual.id, "OMR", accrual.country_code, run_by)

    accrual.reversal_entry_id = entry.id

    accrual.status = "reversed"

    db.commit()

    db.refresh(accrual)

    return accrual





# ── Helpers ──────────────────────────────────────────────────────────────────





def _post_gl(

    db: Session,

    lines: list[JournalLineInput],

    description: str,

    reference_type: str,

    reference_id: int,

    currency: str,

    country_code: Optional[str],

    user_id: Optional[int],

) -> JournalEntry:

    # Removed circular self-import



    entry = gl.create_journal_entry(db, JournalEntryCreate(

        entry_date=utcnow(),

        reference_type=reference_type,

        reference_id=reference_id,

        description=description,

        currency=currency,

        country_code=country_code,

        lines=lines,

    ), user_id=user_id)

    if user_id:

        try:

            audit_log(

                db=db, action=AuditAction.JOURNAL_ENTRY_CREATED, user_id=user_id,

                username=None, user_role=None, resource_type="journal_entry",

                resource_id=entry.get("id") if isinstance(entry, dict) else entry.id,

                details={"reference_type": reference_type, "source": "automation"},

            )

        except Exception:

            pass

    return entry





def _log_automation(

    db: Session, kind: str, processed: int, changed: int,

    detail: dict = None, run_by: Optional[int] = None, country_code: Optional[str] = None,

) -> None:

    log = FinanceAutomationLog(

        kind=kind, records_processed=processed, records_changed=changed,

        detail=detail, run_by=run_by, country_code=country_code,

    )

    db.add(log)

    db.flush()





def import_bank_statement_csv(

    db: Session,

    *,

    raw_csv: str,

    bank_name: Optional[str] = None,

    file_name: Optional[str] = None,

    currency: str = "OMR",

    country_code: Optional[str] = None,

    imported_by: Optional[int] = None,

) -> dict:

    """Parse an uploaded CSV server-side (robust) and import + auto-map lines."""

    # TODO: Module not yet created
# from domains.finance.services.shared.ocr_parser import parse_statement_csv



    parsed = parse_statement_csv(raw_csv)

    imp = import_bank_statement(

        db, lines=parsed, bank_name=bank_name, file_name=file_name,

        currency=currency, country_code=country_code, imported_by=imported_by,

    )

    return {"import_id": imp.id, "total_lines": imp.total_lines,

            "matched_lines": imp.matched_lines, "unmatched_lines": imp.unmatched_lines}





def run_daily_automation(

    db: Session, *,

    as_of: Optional[date] = None,

    country_code: Optional[str] = None,

    run_by: Optional[int] = None,

) -> dict:

    """Idempotent per-day automation: depreciation + accrual reversals + orphan scan."""

    as_of = as_of or date.today()

    # 1. Depreciation

    dep = run_depreciation(db, as_of=as_of, country_code=country_code, run_by=run_by)

    # 2. Reverse accruals whose reversal date has passed

    from domains.finance.models.finance import Accrual



    due = db.query(Accrual).filter(

        Accrual.status == "open",

        Accrual.reversal_date.isnot(None),

        Accrual.reversal_date <= datetime(as_of.year, as_of.month, as_of.day),

    ).all()

    reversed_count = 0

    for acc in due:

        try:

            reverse_accrual(db, acc.id, run_by=run_by)

            reversed_count += 1

        except Exception as e:

            logger.warning("accrual reverse failed %s: %s", acc.id, e)

    # 3. Orphan detection (uses corrected reference_type values)

    # TODO: Module not yet created
# from domains.finance.services.treasury.treasury_engine import TreasuryEngine



    try:

        orphans = TreasuryEngine(db).run_orphan_detector()

    except Exception as e:

        logger.warning("orphan detector failed: %s", e)

        orphans = []

    _log_automation(db, "daily_run", len(due) + len(orphans), reversed_count + dep.get("depreciated", 0),

                    {"depreciated": dep, "accruals_reversed": reversed_count, "orphans": len(orphans)},

                    run_by, country_code)

    db.commit()

    return {"as_of": as_of.isoformat(), "depreciation": dep,

            "accruals_reversed": reversed_count, "orphans": orphans}





def trigger_recurring(

    db: Session, *,

    template_id: int,

    run_date: Optional[datetime] = None,

    run_by: Optional[int] = None,

) -> dict:

    """Generate a journal entry from a recurring template."""

    from domains.finance.models.finance import RecurringTemplate



    tpl = db.query(RecurringTemplate).filter(RecurringTemplate.id == template_id).first()

    if not tpl or not tpl.is_active:

        raise ValueError("recurring template not found/inactive")

    run_date = run_date or _utcnow()

    lines = []

    for ln in (tpl.lines or []):

        lines.append(JournalLineInput(

            account_code=ln["account_code"], side=ln["side"],

            amount=Decimal(str(ln["amount"])), description=ln.get("description"),

        ))

    entry = _post_gl(

        db, lines=lines, description=tpl.description or f"Recurring: {tpl.name}",

        reference_type="recurring", reference_id=tpl.id, currency=tpl.currency,

        country_code=tpl.country_code, user_id=run_by,

    )

    if tpl.next_run_date and isinstance(tpl.next_run_date, datetime):

        # advance ~1 month (safe, dependency-free)

        nd = tpl.next_run_date

        try:

            tpl.next_run_date = nd.replace(month=nd.month % 12 + 1, year=nd.year + (nd.month == 12))

        except ValueError:

            tpl.next_run_date = nd + timedelta(days=30)

    db.commit()

    return {"template_id": tpl.id, "journal_entry_id": entry.id if not isinstance(entry, dict) else entry.get("id")}

# === MERGED from finance_automation_write_service.py ===

"""Finance-automation admin writes (chart of accounts + fixed assets).

Owns every DB mutation that used to live in ``routers/finance_automation.py``
so routers and controllers stay write-free (W1). Each function takes the
injected ``db`` session first, performs its own ``add``/``flush``/``commit``
and raises the same ``HTTPException`` values the router used to raise.
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import AccountGroup
from domains.finance.models.finance import FixedAsset
# Removed circular self-import
import structlog
logger = structlog.get_logger(__name__)


def _as_dict(body: Any) -> dict:
    """Accept either a pydantic model or a plain mapping."""
    if hasattr(body, "model_dump"):
        return body.model_dump(exclude_none=True)
    return dict(body or {})


def create_gl_account(db: Session, body: Any) -> Any:
    """Create a GL account plus its zero-balance row, then return the new COA.

    Mirrors the previous router behaviour: 409 when the code already exists,
    404 when the parent account group is unknown.
    """
    if db.query(Account).filter(Account.code == body.code).first():
        raise HTTPException(409, f"Account '{body.code}' already exists")
    grp = db.query(AccountGroup).filter(AccountGroup.code == body.group_code).first()
    if not grp:
        raise HTTPException(404, f"Account group '{body.group_code}' not found")
    acct = Account(
        code=body.code,
        name=body.name,
        group_id=grp.id,
        normal_side=body.normal_side,
        currency=body.currency,
        country_code=body.country_code,
    )
    db.add(acct)
    db.flush()
    db.add(AccountBalance(account_id=acct.id, currency=body.currency, balance=Decimal("0.00")))
    db.commit()
    db.refresh(acct)
    return gl.list_accounts(db)


def deactivate_gl_account(db: Session, code: str) -> dict:
    """Soft-disable a GL account by code (404 when missing)."""
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        raise HTTPException(404, f"Account '{code}' not found")
    acct.is_active = False
    db.commit()
    return {"status": "deactivated", "code": code}


def create_fixed_asset(db: Session, body: Any, created_by: Optional[int] = None) -> dict:
    """Register a fixed asset and return its identity/status summary."""
    asset = FixedAsset(**_as_dict(body), created_by=created_by)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"id": asset.id, "name": asset.name, "status": asset.status}


# Re-export from the journal-reversal service so historical callers/routers that
# imported ``reverse_journal_entry`` from this module keep working (Law 3).
from domains.finance.services.ledger.je_reversal_service import (  # noqa: E402,F401
    reverse_journal_entry,
)
