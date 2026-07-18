"""General Ledger — double-entry accounting core."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from models import (
    Account,
    AccountBalance,
    AccountGroup,
    JournalEntry,
    JournalEntryLine,
    Order,
    OrderItem,
    User,
    Payout,
    TransactionLedger,
    RefundLedger,
    VATRemittance,
    CommissionLedgerEntry,
    TreasuryAccount,
)
from db.schemas import (
    AccountBalanceOut,
    AccountOut,
    JournalEntryCreate,
    JournalEntryLineOut,
    JournalEntryOut,
    JournalLineInput,
    TrialBalanceOut,
)
from utils.money import round_money


# ── Chart of Accounts ─────────────────────────────────────────────────────


def seed_chart_of_accounts(db: Session) -> list[Account]:
    """GCC E-COMMERCE Chart of Accounts - Standard for GCC marketplace operations.

    Idempotent AND additive: existing accounts/groups are preserved, while any
    missing accounts (e.g. new EPR-level accounts added in later releases) are
    appended. This allows the COA to grow without wiping prior data.
    """
    existing_accounts = {a.code for a in db.query(Account.code).all()}
    existing_groups = {g.code for g in db.query(AccountGroup.code).all()}

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
    group_by_code = {g.code: g.id for g in db.query(AccountGroup).all()}

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
    return db.query(Account).all()


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
    for code, (acct_type, normal_side) in group_fixes.items():
        grp = db.query(AccountGroup).filter(AccountGroup.code == code).first()
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
    for code, name, normal_side in equity_accounts:
        existing = db.query(Account).filter(Account.code == code).first()
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
    bal.last_entry_at = datetime.utcnow()
    bal.updated_at = datetime.utcnow()
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
    account_cache: dict[str, "Account"] = {}
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
    entries = q.order_by(JournalEntry.entry_date.desc()).offset(offset).limit(limit).all()
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
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Order {order_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=datetime.utcnow(),
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
    order = db.query(Order).filter(Order.id == refund_ledger.order_id).first()
    if not order:
        raise ValueError(f"Order {refund_ledger.order_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=datetime.utcnow(),
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
            entry_date=datetime.utcnow(),
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
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Order {order_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=datetime.utcnow(),
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
            entry_date=datetime.utcnow(),
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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    return create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=datetime.utcnow(),
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
            entry_date=datetime.utcnow(),
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
            entry_date=datetime.utcnow(),
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
    balance_map = {b.account_id: b.balance for b in bal_q.all()}

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
        as_of=as_of_date or datetime.utcnow(),
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


