# Implementation Plan: Unified Financial Ledger & Treasury Engine

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Phase 1: Chart of Accounts & Double-Entry Ledger](#2-phase-1-chart-of-accounts--double-entry-ledger)
3. [Phase 2: Treasury Engine](#3-phase-2-treasury-engine)
4. [Phase 3: Integration & Migration](#4-phase-3-integration--migration)
5. [Phase 4: API & Controllers](#5-phase-4-api--controllers)
6. [Files to Create/Modify](#6-files-to-createmodify)

---

## 1. Architecture Overview

### Existing Financial Models (to coexist, then supersede)

| Model | Status | Role in new design |
|-------|--------|-------------------|
| `TransactionLedger` | Keep | Feeds into JournalEntry; order-level financial snapshot |
| `RefundLedger` | Keep | Feeds into JournalEntry; refund reversal snapshot |
| `CommissionLedgerEntry` | Keep | Immutable audit trail; feeds into JournalEntry |
| `BankTransaction` | Keep | Feeds into JournalEntry; bank reconciliation source |
| `SupplierSettlement` | Keep | Feeds into Treasury (supplier_payable reserve) |
| `LogisticsSettlement` | Keep | Feeds into Treasury (logistics_payable reserve) |
| `CashAccount` | Soft-deprecate | Replaced by TreasuryAccount |
| `CashTransaction` | Soft-deprecate | Replaced by JournalEntry lines on treasury accounts |
| `VATRemittance` | Keep | Feeds into Treasury (vat_reserve) |
| `BadgeBillingRecord` | Keep | Feeds into JournalEntry; revenue recognition |

### New Financial Architecture

```
                    ┌─────────────────────────┐
                    │     Chart of Accounts    │
                    │  (Account, AccountGroup) │
                    └────────────┬────────────┘
                                 │ maps to
                    ┌────────────▼────────────┐
                    │     Journal Entry        │
                    │  (header + debit/credit  │
                    │   line items)            │
                    └────────────┬────────────┘
                                 │ feeds
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │  Account     │  │  Treasury    │  │  Settlement  │
     │  Balance     │  │  Account     │  │  Schedule    │
     │  (running)   │  │  (position)  │  │  (forecast)  │
     └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 2. Phase 1: Chart of Accounts & Double-Entry Ledger

### 2.1 Models (`backend/db/models.py`)

#### `AccountGroup`
```python
class AccountGroup(Base):
    """Hierarchical grouping for Chart of Accounts (e.g. Assets, Liabilities, Revenue)."""
    __tablename__ = "account_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)         # e.g. "Current Assets"
    code = Column(String(20), nullable=False, unique=True)  # e.g. "1000"
    parent_id = Column(Integer, ForeignKey("account_groups.id"), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    children = relationship("AccountGroup", backref="parent", remote_side=[id])
    accounts = relationship("Account", back_populates="group")
```

#### `Account`
```python
class Account(Base):
    """A single account in the Chart of Accounts (COA).

    Follows standard accounting: Assets (1xxx), Liabilities (2xxx),
    Equity (3xxx), Revenue (4xxx), Expenses (5xxx).
    """
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("code", name="uq_accounts_code"),
        CheckConstraint("normal_side IN ('debit', 'credit')", name="ck_accounts_normal_side"),
    )
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False, unique=True)    # e.g. "1100"
    name = Column(String(200), nullable=False)                 # e.g. "Cash - Operating Account"
    normal_side = Column(String(10), nullable=False)           # "debit" or "credit"
    currency = Column(String(10), nullable=False, default="OMR")
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    group = relationship("AccountGroup", back_populates="accounts")
```

#### `JournalEntry`
```python
class JournalEntry(Base):
    """The core double-entry record. Every financial movement is recorded here."""
    __tablename__ = "journal_entries"
    __table_args__ = (
        Index("ix_journal_entries_date", "entry_date"),
        Index("ix_journal_entries_reference", "reference_type", "reference_id"),
    )
    id = Column(Integer, primary_key=True)
    entry_date = Column(DateTime, nullable=False, index=True)
    reference_type = Column(String(40), nullable=False)  # "order" | "payout" | "refund" | "vat" | "commission" | "fee" | "adjustment" | "transfer"
    reference_id = Column(Integer, nullable=False)       # FK to the source entity (order_id, payout_id, etc.)
    reference_number = Column(String(100), nullable=True) # e.g. "ORD-12345"
    description = Column(String(500), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    fx_rate = Column(Numeric(12, 6), nullable=True, default=Decimal("1.000000"))
    is_reconciled = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")
```

#### `JournalEntryLine`
```python
class JournalEntryLine(Base):
    """Individual debit/credit line within a journal entry."""
    __tablename__ = "journal_entry_lines"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_jel_amount_positive"),
        CheckConstraint("side IN ('debit', 'credit')", name="ck_jel_side"),
    )
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    side = Column(String(10), nullable=False)         # "debit" or "credit"
    amount = Column(Numeric(12, 2), nullable=False)   # always positive
    description = Column(String(300), nullable=True)
    entity_type = Column(String(40), nullable=True)   # "supplier" | "customer" | "logistics" | "system"
    entity_id = Column(Integer, nullable=True)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")
```

#### `AccountBalance`
```python
class AccountBalance(Base):
    """Materialized running balance per account (updated on each journal entry)."""
    __tablename__ = "account_balances"
    __table_args__ = (
        UniqueConstraint("account_id", "currency", name="uq_account_balances_account_currency"),
    )
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    currency = Column(String(10), nullable=False, default="OMR")
    balance = Column(Numeric(16, 2), nullable=False, default=Decimal("0.00"))
    last_entry_id = Column(Integer, nullable=True)     # last journal entry line that updated this
    last_entry_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
```

### 2.2 Standard Chart of Accounts

Seed data for a marketplace:

| Code | Name | Group | Normal Side |
|------|------|-------|-------------|
| **Assets** | | | |
| 1010 | Cash - Operating | Current Assets | Debit |
| 1020 | Cash - Gateway Settlement | Current Assets | Debit |
| 1030 | Accounts Receivable | Current Assets | Debit |
| 1040 | Gateway Settlement Receivable | Current Assets | Debit |
| 1050 | Supplier Prepayments | Current Assets | Debit |
| **Liabilities** | | | |
| 2010 | Supplier Payables | Current Liabilities | Credit |
| 2020 | Logistics Payables | Current Liabilities | Credit |
| 2030 | Customer Refund Reserve | Current Liabilities | Credit |
| 2040 | VAT Payable | Current Liabilities | Credit |
| 2050 | Commission Payable | Current Liabilities | Credit |
| 2060 | Deferred Revenue | Current Liabilities | Credit |
| 2070 | Gateway Settlement Payable | Current Liabilities | Credit |
| **Revenue** | | | |
| 4010 | Commission Revenue | Revenue | Credit |
| 4020 | Badge Fee Revenue | Revenue | Credit |
| 4030 | Delivery Fee Revenue | Revenue | Credit |
| 4040 | Other Revenue | Revenue | Credit |
| **Expenses** | | | |
| 5010 | Payment Gateway Fees | Expenses | Debit |
| 5020 | Bank Charges | Expenses | Debit |
| 5030 | Operating Expenses | Expenses | Debit |

### 2.3 Journal Entry Mapping Rules

Mapping from existing events to double-entry journal entries:

#### Order Payment (card):
```
Dr. 1020 Cash - Gateway Settlement     total_amount      (funds in transit from gateway)
Cr. 2060 Deferred Revenue              total_amount      (obligation to fulfill order)
```
On Delivery:
```
Dr. 2060 Deferred Revenue              total_amount
    Cr. 4010 Commission Revenue        zozi_commission    (Zozi's commission earned)
    Cr. 4030 Delivery Fee Revenue      delivery_total     (delivery fee earned)
    Cr. 2040 VAT Payable               vat_amount         (VAT collected)
    Cr. 2010 Supplier Payables         net_supplier_amount (owed to supplier)
    Cr. 2020 Logistics Payables        net_logistics_amount (owed to logistics)
```

#### Order Refund:
```
Dr. 2040 VAT Payable                   vat_adjustment
Dr. 2010 Supplier Payables             supplier_reversal
Dr. 2020 Logistics Payables            logistics_reversal
Dr. 4010 Commission Revenue            commission_reversal
Cr. 1030 Accounts Receivable           customer_refund_amount (refund due to customer)
```

#### Payout to Supplier:
```
Dr. 2010 Supplier Payables             payout_amount
Cr. 1010 Cash - Operating              payout_amount
```

#### VAT Remittance:
```
Dr. 2040 VAT Payable                   remittance_amount
Cr. 1010 Cash - Operating              remittance_amount
```

#### Badge Fee Charged:
```
Dr. 1030 Accounts Receivable           badge_fee_amount
Cr. 4020 Badge Fee Revenue             badge_fee_amount
```

#### Gateway Fee Incurred:
```
Dr. 5010 Payment Gateway Fees          gateway_fee_amount
Cr. 1020 Cash - Gateway Settlement     gateway_fee_amount (reduces settlement receivable)
```

### 2.4 Service Layer (`backend/services/general_ledger_service.py`)

```python
class GeneralLedgerService:
    """
    Core service for creating double-entry journal entries.
    Every financial event in the platform flows through here.
    """

    def create_journal_entry(
        db: Session,
        entry_date: datetime,
        reference_type: str,
        reference_id: int,
        reference_number: str | None,
        description: str,
        lines: list[JournalLineInput],
        created_by: int | None = None,
        currency: str = "OMR",
    ) -> JournalEntry:
        """Create a balanced journal entry (debits == credits)."""
        1. Validate total debits == total credits
        2. Create JournalEntry header
        3. Create JournalEntryLine rows
        4. Update AccountBalance for each account
        5. Return the entry

    def post_order_payment_journal(
        db, order_id, total_amount, currency="OMR"
    ) -> JournalEntry:
        """Dr GatewaySettlement, Cr DeferredRevenue"""

    def post_delivery_revenue_journal(
        db, ledger: TransactionLedger
    ) -> JournalEntry:
        """Split DeferredRevenue into commission, VAT, supplier, logistics payables."""

    def post_refund_journal(
        db, refund_ledger: RefundLedger
    ) -> JournalEntry:
        """Reverse all revenue splits."""

    def post_payout_journal(
        db, payout: Payout, amount: Decimal
    ) -> JournalEntry:
        """Dr SupplierPayables, Cr CashOperating."""

    def post_gateway_fee_journal(
        db, gateway_fee_amount, gateway_settlement_entry_id
    ) -> JournalEntry:
        """Dr GatewayFeeExpense, Cr GatewaySettlement."""

    def post_vat_remittance_journal(
        db, vat_remittance: VATRemittance
    ) -> JournalEntry:
        """Dr VATPayable, Cr CashOperating."""

    def get_account_balance(
        db, account_code: str, currency: str = "OMR"
    ) -> Decimal:
        """Return current balance for an account."""

    def get_trial_balance(
        db, as_of: datetime | None = None
    ) -> list[dict]:
        """Return all account balances (trial balance report)."""

    def validate_entry_balanced(
        lines: list[JournalLineInput]
    ) -> bool:
        """Ensure sum(debits) == sum(credits)."""
```

### 2.5 Pydantic Schemas (`backend/db/schemas.py`)

```python
# ── General Ledger ─────────────────────────────────────────────────────────

class JournalLineInput(BaseModel):
    account_code: str
    side: Literal["debit", "credit"]
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class JournalEntryCreate(BaseModel):
    entry_date: datetime
    reference_type: str
    reference_id: int
    reference_number: Optional[str] = None
    description: str
    currency: str = "OMR"
    lines: List[JournalLineInput]

class JournalEntryLineOut(OrmBase):
    id: int
    entry_id: int
    account_code: str
    account_name: str
    side: str
    amount: Decimal
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class JournalEntryOut(OrmBase):
    id: int
    entry_date: datetime
    reference_type: str
    reference_id: int
    reference_number: Optional[str] = None
    description: str
    currency: str
    is_reconciled: bool
    created_by: Optional[int] = None
    created_at: datetime
    lines: List[JournalEntryLineOut]

class AccountBalanceOut(OrmBase):
    account_code: str
    account_name: str
    group_name: str
    normal_side: str
    currency: str
    balance: Decimal

class TrialBalanceOut(BaseModel):
    as_of: datetime
    accounts: List[AccountBalanceOut]
    total_debit_balances: Decimal
    total_credit_balances: Decimal
```

---

## 3. Phase 2: Treasury Engine

### 3.1 Models (`backend/db/models.py`)

#### `TreasuryAccount`
```python
class TreasuryAccount(Base):
    """Cash position buckets for treasury management.
    
    Each account tracks a specific pool of cash/liquidity.
    Balances are derived from the General Ledger but cached here for performance.
    """
    __tablename__ = "treasury_accounts"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_treasury_accounts_slug"),
        CheckConstraint("account_type IN ('cash', 'reserve', 'receivable', 'payable')",
                        name="ck_treasury_accounts_type"),
    )
    id = Column(Integer, primary_key=True)
    slug = Column(String(60), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    account_type = Column(String(30), nullable=False)   # cash | reserve | receivable | payable
    currency = Column(String(10), nullable=False, default="OMR")
    gl_account_code = Column(String(20), nullable=True)  # link to Chart of Accounts
    balance = Column(Numeric(16, 2), nullable=False, default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
```

Default treasury accounts to seed:

| Slug | Name | Type | GL Account |
|------|------|------|------------|
| `cash_operating` | Available Cash (Operating) | cash | 1010 |
| `cash_gateway_settlement` | Cash in Gateway Settlement | receivable | 1020 |
| `reserve_supplier_payable` | Supplier Payables Reserve | payable | 2010 |
| `reserve_logistics_payable` | Logistics Payables Reserve | payable | 2020 |
| `reserve_refund` | Customer Refund Reserve | reserve | 2030 |
| `reserve_vat` | VAT Liability Reserve | reserve | 2040 |
| `reserve_commission` | Commission Reserve | reserve | 2050 |
| `receivable_customer` | Customer Accounts Receivable | receivable | 1030 |

#### `CashPositionSnapshot`
```python
class CashPositionSnapshot(Base):
    """Daily cash position record for audit and forecasting."""
    __tablename__ = "cash_position_snapshots"
    __table_args__ = (
        Index("ix_cash_position_snapshots_date", "snapshot_date"),
        UniqueConstraint("snapshot_date", "currency", name="uq_cash_position_snapshots_date_currency"),
    )
    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date, nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")

    # Available cash
    cash_operating = Column(Numeric(16, 2), nullable=False, default=0)
    cash_gateway_settlement = Column(Numeric(16, 2), nullable=False, default=0)

    # Reserves
    reserve_supplier_payable = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_logistics_payable = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_refund = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_vat = Column(Numeric(16, 2), nullable=False, default=0)
    reserve_commission = Column(Numeric(16, 2), nullable=False, default=0)
    receivable_customer = Column(Numeric(16, 2), nullable=False, default=0)

    # Derived
    total_cash = Column(Numeric(16, 2), nullable=False, default=0)
    total_reserves = Column(Numeric(16, 2), nullable=False, default=0)
    free_cash = Column(Numeric(16, 2), nullable=False, default=0)   # available after reserves
    net_working_capital = Column(Numeric(16, 2), nullable=False, default=0)

    created_at = Column(DateTime, default=_utcnow)
```

#### `CashFlowForecast`
```python
class CashFlowForecast(Base):
    """Projected cash inflows and outflows for a future period."""
    __tablename__ = "cash_flow_forecasts"
    __table_args__ = (
        Index("ix_cash_flow_forecasts_date", "forecast_date"),
        Index("ix_cash_flow_forecasts_category", "forecast_category", "forecast_date"),
    )
    id = Column(Integer, primary_key=True)
    forecast_date = Column(Date, nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    forecast_category = Column(String(40), nullable=False)  # "settlement_inflow" | "payout_outflow" | "vat_outflow" | "refund_outflow" | "badge_inflow"
    forecast_type = Column(String(10), nullable=False)       # "inflow" | "outflow"
    expected_amount = Column(Numeric(16, 2), nullable=False)
    confidence = Column(String(20), nullable=False, default="medium")  # high | medium | low
    source_entity = Column(String(40), nullable=True)       # e.g. "order", "payout", "vat"
    source_id = Column(Integer, nullable=True)
    description = Column(String(300), nullable=True)
    expected_settlement_date = Column(Date, nullable=True)  # when cash actually moves
    created_at = Column(DateTime, default=_utcnow)
```

#### `GatewaySettlementSchedule`
```python
class GatewaySettlementSchedule(Base):
    """Expected settlements from payment gateways (funds in transit)."""
    __tablename__ = "gateway_settlement_schedules"
    __table_args__ = (
        Index("ix_gw_settlement_schedule_date", "expected_settlement_date"),
        Index("ix_gw_settlement_schedule_gateway", "gateway_code", "expected_settlement_date"),
    )
    id = Column(Integer, primary_key=True)
    gateway_code = Column(String(60), nullable=False)      # stripe | tap | etc.
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    transaction_id = Column(String(255), nullable=False)    # gateway transaction reference
    amount = Column(Numeric(16, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    gateway_fee = Column(Numeric(12, 2), nullable=False, default=0)
    net_amount = Column(Numeric(16, 2), nullable=False)     # amount - fee
    transaction_date = Column(DateTime, nullable=False)
    expected_settlement_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="pending")   # pending | settled | failed
    settled_at = Column(DateTime, nullable=True)
    settlement_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
```

#### `TreasuryTransaction` (optional audit log)
```python
class TreasuryTransaction(Base):
    """Audit trail for treasury movements (transfers between treasury accounts)."""
    __tablename__ = "treasury_transactions"
    id = Column(Integer, primary_key=True)
    from_treasury_account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=True)
    to_treasury_account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    amount = Column(Numeric(16, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="OMR")
    transaction_type = Column(String(40), nullable=False)  # "settlement_received" | "payout_made" | "vat_paid" | "reserve_topup"
    description = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
```

### 3.2 Service Layer (`backend/services/treasury_service.py`)

```python
class TreasuryService:
    """
    Treasury management: cash positioning, forecasting, reserve management.
    """

    def compute_cash_position(
        db: Session, currency: str = "OMR"
    ) -> CashPositionSnapshot:
        """
        Derive current cash position from GL account balances + pending settlements.
        1. Query AccountBalance for each treasury-linked account
        2. Query pending GatewaySettlementSchedule for funds in transit
        3. Query pending payouts for future outflows
        4. Create a CashPositionSnapshot
        """

    def compute_daily_snapshot(
        db: Session, snapshot_date: date | None = None
    ) -> CashPositionSnapshot:
        """Compute and store an end-of-day cash position snapshot."""

    def generate_cash_flow_forecast(
        db: Session, days_ahead: int = 30, currency: str = "OMR"
    ) -> list[CashFlowForecast]:
        """
        Forecast cash inflows/outflows for the next N days.
        Sources:
        - GatewaySettlementSchedule (pending settlements -> cash in)
        - SupplierSettlement pending payouts (cash out, after holding period)
        - LogisticsSettlement pending payouts (cash out, after holding period)
        - VATRemittance pending (cash out)
        - Estimated refunds (based on historical refund rate, confidence=low)
        """

    def schedule_gateway_settlement(
        db: Session,
        gateway_code: str,
        order_id: int,
        transaction_id: str,
        amount: Decimal,
        gateway_fee: Decimal,
        transaction_date: datetime,
        settlement_cycle_days: int,
    ) -> GatewaySettlementSchedule:
        """
        Record expected settlement from a payment gateway.
        settlement_cycle_days from PaymentGatewayConnection.settlement_cycle config.
        """

    def mark_gateway_settlement_received(
        db: Session,
        schedule_id: int,
        settlement_reference: str | None = None,
    ) -> tuple[GatewaySettlementSchedule, JournalEntry]:
        """Mark settlement as received, create journal entry transferring from
        'Cash - Gateway Settlement' to 'Cash - Operating'."""

    def get_free_cash(
        db: Session, currency: str = "OMR"
    ) -> Decimal:
        """Cash available after deducting all reserves."""

    def get_reserve_balance(
        db: Session, reserve_slug: str, currency: str = "OMR"
    ) -> Decimal:
        """Get current balance for a specific reserve."""

    def transfer_between_reserves(
        db: Session,
        from_slug: str,
        to_slug: str,
        amount: Decimal,
        reason: str,
        performed_by: int | None = None,
    ) -> TreasuryTransaction:
        """Transfer between treasury accounts (with corresponding journal entry)."""

    def get_treasury_summary(
        db: Session, currency: str = "OMR"
    ) -> dict:
        """
        Return full treasury dashboard data:
        - Current cash position by bucket
        - Pending settlements total
        - Pending payouts total
        - Free cash
        - Reserves breakdown
        """
```

### 3.3 Pydantic Schemas

```python
# ── Treasury ───────────────────────────────────────────────────────────────

class TreasuryAccountOut(OrmBase):
    id: int
    slug: str
    name: str
    account_type: str
    currency: str
    gl_account_code: Optional[str] = None
    balance: Decimal
    description: Optional[str] = None
    is_active: bool

class CashPositionOut(OrmBase):
    id: int
    snapshot_date: date
    currency: str
    cash_operating: Decimal
    cash_gateway_settlement: Decimal
    reserve_supplier_payable: Decimal
    reserve_logistics_payable: Decimal
    reserve_refund: Decimal
    reserve_vat: Decimal
    reserve_commission: Decimal
    receivable_customer: Decimal
    total_cash: Decimal
    total_reserves: Decimal
    free_cash: Decimal
    net_working_capital: Decimal

class CashFlowForecastOut(OrmBase):
    id: int
    forecast_date: date
    currency: str
    forecast_category: str
    forecast_type: str
    expected_amount: Decimal
    confidence: str
    source_entity: Optional[str] = None
    source_id: Optional[int] = None
    description: Optional[str] = None
    expected_settlement_date: Optional[date] = None

class GatewaySettlementScheduleOut(OrmBase):
    id: int
    gateway_code: str
    order_id: int
    transaction_id: str
    amount: Decimal
    currency: str
    gateway_fee: Decimal
    net_amount: Decimal
    transaction_date: datetime
    expected_settlement_date: date
    status: str
    settled_at: Optional[datetime] = None

class TreasuryDashboardOut(BaseModel):
    current_position: CashPositionOut
    pending_settlements_total: Decimal
    pending_payouts_total: Decimal
    free_cash: Decimal
    reserves_breakdown: dict[str, Decimal]
    forecast_next_30_days: List[CashFlowForecastOut]
    recent_transactions: List[Any]  # journal entries
```

---

## 4. Phase 3: Integration & Migration

### 4.1 Integration Points

#### Order Confirmation (in `payments_controller._apply_successful_payment`)
After existing `create_ledger_entries_for_order()`, add:
```python
from services.general_ledger_service import post_order_payment_journal

# Record the initial payment journal entry
post_order_payment_journal(db, order_id, total_amount)
```

#### Order Delivery (in existing settlement creation)
When settlements are created on delivery:
```python
from services.general_ledger_service import post_delivery_revenue_journal

# Recognize revenue from deferred to earned, create supplier/logistics payables
post_delivery_revenue_journal(db, ledger_entry)
```

#### Order Refund (in `create_refund_ledger_entry`)
```python
from services.general_ledger_service import post_refund_journal

# Reverse all revenue entries
post_refund_journal(db, refund_ledger_entry)
```

#### Payout Processing (in `process_supplier_payout_batch`)
```python
from services.general_ledger_service import post_payout_journal

# Record payout cash outflow
post_payout_journal(db, payout, amount)
```

#### Gateway Fee Recording (in order confirmation + webhook)
```python
from services.general_ledger_service import post_gateway_fee_journal
from services.treasury_service import schedule_gateway_settlement

# Record fee and expected settlement
post_gateway_fee_journal(db, gateway_fee, gateway_entry_id)
schedule_gateway_settlement(db, gateway_code, order_id, ...)
```

### 4.2 Existing Model Migration Strategy

| Step | Action | Details |
|------|--------|---------|
| 1 | Seed Chart of Accounts | Create AccountGroup + Account rows for the standard COA |
| 2 | Create journal entries for existing unsettled orders | Backfill open orders into JournalEntry (one-time migration script) |
| 3 | Create treasury accounts | Seed TreasuryAccount rows |
| 4 | Create initial CashPositionSnapshot | Compute from current bank balances |
| 5 | Gradually wire up event hooks | Add GL calls to payment_controller, cash_management_service |

### 4.3 Stale Model Handling

- `CashAccount` / `CashTransaction`: Mark as `@deprecated` in docstring. Keep working for existing admin_cash router users until the new treasury dashboard replaces it.
- `TransactionLedger`: Keep as the order-level financial snapshot (useful for reporting). GL journal entries reference it indirectly via `reference_type='order'`.

---

## 5. Phase 4: API & Controllers

### 5.1 New Routers

#### `backend/routers/accounting.py`
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/accounting/accounts` | List chart of accounts |
| GET | `/accounting/accounts/{code}` | Get single account details |
| GET | `/accounting/journal-entries` | List journal entries (filterable by date range, reference_type) |
| GET | `/accounting/journal-entries/{id}` | Get journal entry with lines |
| GET | `/accounting/trial-balance` | Trial balance report |
| GET | `/accounting/account-balances` | All account balances |

#### `backend/routers/treasury.py`
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/treasury/dashboard` | Full treasury dashboard |
| GET | `/treasury/position` | Current cash position |
| GET | `/treasury/position/history` | Historical daily snapshots |
| GET | `/treasury/forecast` | Cash flow forecast |
| GET | `/treasury/gateway-settlements` | Pending gateway settlements |
| PUT | `/treasury/gateway-settlements/{id}/settle` | Mark settlement received |
| GET | `/treasury/reserves` | Reserve balances |
| POST | `/treasury/transfer` | Transfer between reserves |
| GET | `/treasury/accounts` | List all treasury accounts |

### 5.2 Controllers

#### `backend/controllers/accounting_controller.py`
- `list_accounts()` — Paginated, filterable by group
- `get_account()` — Single account with current balance
- `list_journal_entries()` — Paginated, filterable (reference_type, date_range, account_code)
- `get_journal_entry()` — Single entry with all lines
- `get_trial_balance()` — Aggregated account balances
- `get_account_balances()` — Current balance per account

#### `backend/controllers/treasury_controller.py`
- `get_treasury_dashboard()` — Aggregated treasury data
- `get_cash_position()` — Current position or specific date
- `get_cash_position_history()` — Daily snapshots for a date range
- `get_cash_flow_forecast()` — Forecast for next N days
- `list_gateway_settlements()` — Paginated gateway settlements
- `mark_settlement_received()` — Mark gateway settlement as settled
- `list_reserves()` — All reserve balances
- `transfer_funds()` — Transfer between treasury accounts

### 5.3 Router Registration

Add to `backend/main.py`:
```python
from routers import accounting, treasury

app.include_router(accounting.router, prefix="/api/admin", tags=["accounting"])
app.include_router(treasury.router, prefix="/api/admin", tags=["treasury"])
```

---

## 6. Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `backend/services/general_ledger_service.py` | Double-entry journal creation, account balances |
| `backend/services/treasury_service.py` | Cash positioning, forecasting, reserves |
| `backend/controllers/accounting_controller.py` | GL API handlers |
| `backend/controllers/treasury_controller.py` | Treasury API handlers |
| `backend/routers/accounting.py` | `/api/admin/accounting/*` routes |
| `backend/routers/treasury.py` | `/api/admin/treasury/*` routes |

### Existing Files to Modify

| File | Change |
|------|--------|
| `backend/db/models.py` | Add 8 new models: AccountGroup, Account, JournalEntry, JournalEntryLine, AccountBalance, TreasuryAccount, CashPositionSnapshot, CashFlowForecast, GatewaySettlementSchedule, TreasuryTransaction |
| `backend/db/schemas.py` | Add Pydantic schemas for all new models |
| `backend/controllers/payments_controller.py` | Integrate `post_order_payment_journal()` + `schedule_gateway_settlement()` in `_apply_successful_payment()` (around line 900) |
| `backend/services/cash_management_service.py` | Integrate `post_delivery_revenue_journal()` in settlement creation; `post_refund_journal()` in `create_refund_ledger_entry()`; `post_payout_journal()` in `process_supplier_payout_batch()`/`process_logistics_payout_batch()` |
| `backend/main.py` | Register new routers |
| `backend/alembic/versions/` | New migration for all new tables + seed data |

---

## Implementation Order (Recommended Sequence)

```
Week 1: DB Models + Migration
  Day 1-2: Create AccountGroup, Account, JournalEntry, JournalEntryLine models
  Day 3: Migration file + seed Chart of Accounts
  Day 4: Create AccountBalance model + migration

Week 2: GL Service + Schemas + Controllers
  Day 1-2: GeneralLedgerService (create_journal_entry core, all post_* methods)
  Day 3: Pydantic schemas + accounting_controller + accounting router
  Day 4: Testing GL service (balance checks, trial balance)

Week 3: Treasury Models + Service
  Day 1: TreasuryAccount, CashPositionSnapshot, CashFlowForecast, GatewaySettlementSchedule models + migration
  Day 2: TreasuryService (position computation, forecasting, reserve management)
  Day 3: Seed treasury accounts + create initial snapshot
  Day 4: Treasury schemas + controller + router

Week 4: Integration with Existing Code
  Day 1: Wire order payment journal into payments_controller._apply_successful_payment()
  Day 2: Wire delivery revenue journal into settlement creation
  Day 3: Wire refund journal, payout journal, gateway fee/settlement
  Day 4: Integration testing, edge cases, validation
```

















































































----------------------------------------------------------------------------------

### Finding 1: Unified Financial Ledger

**Status:** 🔴 CRITICAL

**Solution Map:**
```
Ledger Architecture:

Every financial movement becomes:
{
  "id": uuid,
  "transaction_type": "order_revenue | commission | payout | refund | vat",
  "debit_account": "revenue | supplier_payable | vat_liability",
  "credit_account": "cash | receivable",
  "amount": 100.00,
  "currency": "OMR",
  "country": "OM",
  "entity_type": "order | supplier | customer",
  "entity_id": uuid,
  "reference_number": "ORD-12345",
  "description": "Order payment for order #12345",
  "timestamp": "2024-01-01T00:00:00Z",
  "created_by": "system",
  "is_reconciled": false
}
```

---

### Finding 2: Treasury Engine

**Status:** 🔴 CRITICAL

**Solution Map:**
```
Treasury Structure:
├── Available Cash (free to use)
├── Locked Cash (pending settlement)
├── Supplier Payables (owed to suppliers)
├── Logistics Payables (owed to logistics)
├── Refund Reserve (for potential refunds)
├── VAT Reserve (tax liabilities)
├── Commission Reserve (pending)
└── Operating Cash (for operations)

Cash Flow Monitoring:
├── Daily cash position
├── Weekly reconciliation
├── Monthly forecast
├── Payment gateway settlement tracking
├── Payout scheduling
├── Reserve management
└── Risk assessment
```

### 🏛️ Pillar 1: The Architectural Shift (The Core Philosophy)
Currently, your system uses **State-Based Balances** (e.g., `Supplier.wallet_balance += 100`). This is dangerous because if a server crashes mid-transaction, or a bug allows a negative payout, the money is simply "gone" or "created" out of thin air.

**The New Rule: Event-Based Double-Entry Accounting**
* We will **never** `UPDATE` a balance column directly. 
* Balances are only ever calculated by summing up immutable `JournalEntryLine` records (Debits and Credits).
* The Operational Layer (Orders, Payouts, Refunds) acts as the **Trigger**. The Treasury Layer acts as the **Immutable Truth**.

---

### 🗄️ Pillar 2: The Database Schema (The 4 Tiers)
Your codebase already has the foundational models (`Account`, `JournalEntry`, `TreasuryAccount`). We will organize them into 4 strict tiers:

#### Tier 1: The Chart of Accounts (CoA)
The "buckets" where money lives.
* `account_groups` (Assets, Liabilities, Equity, Revenue, Expenses)
* `accounts` (e.g., `1010 Cash Operating`, `2010 Supplier Payables`, `4010 Commission Revenue`)
* `account_balances` (A materialized cache of the current balance for fast dashboard loading).

#### Tier 2: The Immutable Ledger (The Truth)
* `journal_entries` (Header: Timestamp, Event Type, Reference ID, Currency, Created By).
* `journal_entry_lines` (Lines: Account ID, Debit Amount, Credit Amount).
* **Constraint:** A database-level trigger or strict application logic must enforce that `SUM(Debits) == SUM(Credits)` for every single entry. If they don't match, the transaction is aborted.

#### Tier 3: The Treasury Buckets (Cash Management)
* `treasury_accounts` (Physical cash pools: `cash_operating`, `cash_gateway_settlement`, `reserve_supplier_payable`, `reserve_vat`).
* `treasury_transactions` (Audit trail for manual transfers between treasury buckets).

#### Tier 4: Forecasting & Reconciliation
* `gateway_settlement_schedules` (Expected payouts from Stripe/Tap).
* `cash_flow_forecasts` (Projected inflows/outflows).
* `cash_position_snapshots` (End-of-day historical cash states).

---

### ⚖️ Pillar 3: The Double-Entry Matrix (How Money Moves)
This is the exact accounting logic the `TreasuryService` must execute for every major platform event.

| Business Event | Debit (Dr) | Credit (Cr) |
| :--- | :--- | :--- |
| **1. Customer Pays via Card** | Gateway Clearing (Asset) | Deferred Revenue (Liability) |
| **2. Gateway Settles to Bank** | Cash Operating (Asset) <br> Gateway Fee (Expense) | Gateway Clearing (Asset) |
| **3. Order Delivered (Card)** | Deferred Revenue (Liability) | Supplier Payable (Liability) <br> Logistics Payable (Liability) <br> Commission Revenue (Revenue) <br> VAT Payable (Liability) |
| **4. Order Delivered (COD)** | COD Receivable (Asset) | Supplier Payable <br> Logistics Payable <br> Commission Revenue <br> VAT Payable |
| **5. Logistics Remits COD** | Cash Operating (Asset) | COD Receivable (Asset) |
| **6. Supplier Payout Dispatched** | Supplier Payable (Liability) | Cash Operating (Asset) |
| **7. Customer Refund Approved** | Revenue / Deferred Revenue | Cash Operating / Gateway Clearing |

---

### ⚙️ Pillar 4: The Treasury Engine Logic (The "Brain")
The `TreasuryService` will be the only service allowed to write to the Ledger. It must enforce the following workflows:

1. **The Atomic Lock:** When posting a journal entry, the service must acquire a `SELECT ... FOR UPDATE` lock on the affected `account_balances` rows to prevent race conditions (e.g., two payouts processing at the exact same millisecond).
2. **The Maker-Checker Protocol:** For manual treasury transfers or manual payout batch approvals, the system creates a `PendingJournalEntry`. A second Admin (Checker) must cryptographically approve it before it is committed to the immutable ledger.
3. **The Orphan Detector:** A daily cron job must scan the `orders` and `payouts` tables to ensure every `status=delivered` or `status=paid` has a corresponding `journal_entry`. If an order is delivered but lacks a ledger entry, it triggers a **Critical Alert** to the Finance Command Center.

---

### 🗺️ Pillar 5: The Step-by-Step Execution Roadmap

This is the exact order of operations for your engineering team to implement this without breaking the live system.

#### Phase 1: Foundation & Seeding (Week 1)
* **Step 1:** Finalize and run the Alembic migration for the 4 Tiers of database tables.
* **Step 2:** Write a seed script to populate the **Chart of Accounts** (Assets, Liabilities, Revenue, Expenses) based on standard GCC accounting practices.
* **Step 3:** Seed the default **Treasury Buckets** (Operating Cash, VAT Reserve, Supplier Payable Reserve).
* **Step 4:** Build the `TreasuryService.post_journal_entry()` core function with the `Debit == Credit` validation and row-level locking.

#### Phase 2: The "Read-Only" Shadow Mode (Week 2)
* *Crucial Strategy:* Do not connect the Ledger to the live payout engine yet. 
* **Step 1:** Inject the `TreasuryService` into the `payments_controller`, `orders_controller`, and `payouts_controller`.
* **Step 2:** Set it to **Shadow Mode**: It calculates and writes the Journal Entries to the database, but the actual operational flow (updating `Supplier.wallet_balance`) continues using the legacy logic.
* **Step 3:** Run a reconciliation script at the end of the day comparing the Legacy Balances vs. the New Ledger Balances. Fix any discrepancies in the logic.

#### Phase 3: The Cutover & Treasury Integration (Week 3)
* **Step 1:** Once Shadow Mode proves 100% accurate, **kill the legacy balance updates**. The system now relies entirely on the Ledger.
* **Step 2:** Wire the `GatewaySettlementSchedule` to automatically match incoming bank webhooks from Stripe/Tap and mark settlements as `settled`, triggering the final Cash Operating journal entry.
* **Step 3:** Implement the **COD Remittance Engine**, matching logistics partner uploads to the `COD Receivable` ledger account.

#### Phase 4: The Finance Command Center UI (Week 4)
* **Step 1:** Build the **General Ledger View** in the Admin Panel (a searchable, filterable table of all `journal_entries`).
* **Step 2:** Build the **Trial Balance & Cash Position Dashboard**, showing real-time `Free Cash` (Total Cash minus Supplier/VAT Reserves).
* **Step 3:** Build the **Payout Dispatch UI**, which reads from the `Supplier Payable` ledger and generates the bank CSV/API payload.

---

### 🛡️ Pillar 6: Testing & Validation Strategy (How we know it works)

You cannot launch this without passing these three strict tests:

1. **The "Chaos Monkey" Test:** 
   * Simulate 1,000 concurrent checkouts and 500 concurrent payout requests. 
   * *Pass Condition:* The database throws zero deadlocks, and `SUM(Debits) == SUM(Credits)` across the entire database remains mathematically perfect.
2. **The "Penny Rounding" Test:** 
   * Process orders with complex commission splits (e.g., $100.00 order, 15% commission, 3% logistics, 5% VAT). 
   * *Pass Condition:* The Ledger handles fractional cents perfectly without losing or creating money due to floating-point math (must use Python `Decimal` and Postgres `NUMERIC(16,4)`).
3. **The "Time Travel" Audit Test:** 
   * Pick a random date 6 months in the past. 
   * *Pass Condition:* The system can reconstruct the exact `CashPositionSnapshot` and `Supplier Payable` balance for that exact second by replaying the immutable `journal_entries`.

---


### 🏛️ PART 1: The GCC E-Commerce Chart of Accounts (CoA)
This CoA is specifically engineered for a **multi-vendor marketplace** operating in the GCC (Oman, KSA, UAE). It accounts for high COD (Cash on Delivery) volumes, regional VAT regulations (5% to 15%), and local payment gateway settlement cycles (Tap, Thawani, Stripe, Mada).

#### 1000 - ASSETS (What Zozi Owns or Controls)
| GL Code | Account Name | Normal Side | Description & GCC Context |
| :--- | :--- | :--- | :--- |
| **1010** | Cash - Operating Bank | Debit | Main corporate bank account holding free cash. |
| **1020** | Gateway Settlement Clearing | Debit | Funds captured by Stripe/Tap/Thawani but not yet settled to the bank (T+2 or T+7 days). |
| **1030** | COD Receivable (Logistics) | Debit | Cash physically collected by delivery drivers but not yet remitted to Zozi. |
| **1040** | Supplier Prepayments | Debit | Funds advanced to suppliers for inventory or marketing campaigns. |
| **1050** | Customer Refund Deposits | Debit | Cash held in escrow pending customer return verification. |
| **1100** | Accounts Receivable (B2B) | Debit | Invoices issued to corporate/B2B customers on net-30 terms. |

#### 2000 - LIABILITIES (What Zozi Owes)
| GL Code | Account Name | Normal Side | Description & GCC Context |
| :--- | :--- | :--- | :--- |
| **2010** | Supplier Payables | Credit | Net earnings owed to suppliers pending payout batch approval. |
| **2020** | Logistics Payables | Credit | Delivery fees and COD handling fees owed to 3PL partners. |
| **2030** | Customer Refund Reserve | Credit | Liability for approved refunds not yet processed back to the customer's card. |
| **2040** | VAT Payable (Output) | Credit | **Crucial for GCC:** VAT collected from customers, held in trust for the government (ZATCA/FTA). |
| **2050** | VAT Receivable (Input) | Debit | VAT paid on Zozi's operational expenses (offsets Output VAT). |
| **2060** | Deferred Revenue | Credit | Customer payments held in limbo before the order is marked "Delivered". |
| **2070** | Withholding Tax Payable | Credit | Applicable for cross-border B2B supplier payouts depending on local tax treaties. |

#### 3000 - EQUITY (Net Worth)
| GL Code | Account Name | Normal Side | Description & GCC Context |
| :--- | :--- | :--- | :--- |
| **3010** | Owner's / Shareholder Equity | Credit | Initial capital injected into the platform. |
| **3020** | Retained Earnings | Credit | Accumulated net profits reinvested into the business. |

#### 4000 - REVENUE (What Zozi Earns)
*Note: In a marketplace, Gross Merchandise Value (GMV) is NOT revenue. Only Zozi's cut is revenue.*
| GL Code | Account Name | Normal Side | Description & GCC Context |
| :--- | :--- | :--- | :--- |
| **4010** | Platform Commission Revenue | Credit | Zozi’s core percentage fee taken from supplier sales. |
| **4020** | Logistics Markup Revenue | Credit | Margin made on shipping (e.g., charging customer $5, paying 3PL $4). |
| **4030** | Payment Processing Fee Rev | Credit | Revenue from passing gateway fees or currency conversion to the buyer. |
| **4040** | Subscription / SaaS Revenue | Credit | Monthly fees charged to suppliers for premium storefront tiers. |

#### 5000 - COST OF GOODS SOLD (COGS)
| GL Code | Account Name | Normal Side | Description & GCC Context |
| :--- | :--- | :--- | :--- |
| **5010** | Direct Product Costs (1P) | Debit | Cost of inventory sold (only if Zozi holds 1st-party stock). |
| **5020** | Packaging & Dunnage | Debit | Costs for Zozi-branded packaging materials used by 3PLs. |

#### 6000 - OPERATING EXPENSES (What Zozi Spends)
| GL Code | Account Name | Normal Side | Description & GCC Context |
| :--- | :--- | :--- | :--- |
| **6010** | Payment Gateway Fees | Debit | Fees paid to Tap, Stripe, Thawani, OmanNet (usually 1.5% - 2.9%). |
| **6020** | Marketing & Ad Spend | Debit | Facebook, Snapchat, TikTok ads (highly relevant in GCC). |
| **6030** | Payroll & Benefits | Debit | Salaries, WPS (Wage Protection System) compliance, health insurance. |
| **6040** | Server & Tech Infrastructure | Debit | AWS, Cloudflare, Redis, Database costs. |
| **6050** | Fraud & Bad Debt Expense | Debit | Losses from unrecoverable COD fraud or stolen credit card chargebacks. |

---

### 🔌 PART 2: Finance Command Center API Endpoints
These endpoints will power the Next.js Admin Finance Dashboard. They are secured by the `require_finance_admin` or `require_country_head` middleware (enforcing Row-Level Security for country-specific financial data).

#### 1. Dashboard & Cash Position (The "Heartbeat")
*   **`GET /finance/dashboard/metrics`**
    *   *Returns:* Real-time totals for Free Cash, Locked Cash (Reserves), Total GMV (Today/MTD), Net Revenue, and Pending Payouts.
*   **`GET /finance/cash-position`**
    *   *Returns:* Breakdown of `1010 Operating`, `1020 Gateway Clearing`, and `1030 COD Receivable` to show exactly where the company's cash physically sits.
*   **`GET /finance/liabilities/exposure`**
    *   *Returns:* Total Supplier Payables, Logistics Payables, and **VAT Payable** (critical for end-of-month tax remittance).

#### 2. General Ledger & Audit (The "Truth")
*   **`GET /finance/ledger`**
    *   *Query Params:* `?start_date`, `?end_date`, `?account_code`, `?country_code`, `?reference_id`
    *   *Returns:* Paginated list of `JournalEntry` records with their Debit/Credit lines.
*   **`GET /finance/ledger/{entry_id}`**
    *   *Returns:* Full detail of a specific journal entry, including the operational trigger (e.g., "Order #9921 Delivered") and the user/system that created it.
*   **`POST /finance/ledger/manual-adjustment`**
    *   *Payload:* `debit_account`, `credit_account`, `amount`, `reason`, `attachment_url`.
    *   *Action:* Creates a manual journal entry (requires Maker-Checker approval if amount > threshold).

#### 3. Trial Balance & Tax Reporting (The "Compliance")
*   **`GET /finance/reports/trial-balance`**
    *   *Query Params:* `?as_of_date`, `?country_code`
    *   *Returns:* Standard accounting trial balance (sum of debits and credits per GL account) to ensure the ledger is perfectly balanced.
*   **`GET /finance/reports/vat-liability`**
    *   *Query Params:* `?period` (e.g., "Q3-2026"), `?country_code`
    *   *Returns:* Output VAT collected minus Input VAT paid, generating the exact figure needed for ZATCA/FTA portal submission.
*   **`GET /finance/reports/supplier-earnings`**
    *   *Returns:* Exportable CSV/PDF data for supplier 1099/tax-equivalent reporting.

#### 4. Payout Batches & Disbursements (The "Maker-Checker")
*   **`GET /finance/payouts/batches`**
    *   *Returns:* List of payout batches grouped by status (`Draft`, `Pending_Approval`, `Approved`, `Dispatched`, `Settled`).
*   **`POST /finance/payouts/batches/generate`**
    *   *Payload:* `country_code`, `cutoff_date`, `include_logistics` (boolean).
    *   *Action:* Scans `Supplier Payables` and groups them into a proposed batch.
*   **`POST /finance/payouts/batches/{batch_id}/approve`**
    *   *Action:* The "Checker" approves the batch. Locks the funds in the Treasury.
*   **`POST /finance/payouts/batches/{batch_id}/dispatch`**
    *   *Action:* Triggers the Payment Orchestrator to send funds via bank API or generates the secure CSV for the corporate bank portal.

#### 5. Reconciliation (The "Matching Engine")
*   **`GET /finance/reconciliation/gateway-exceptions`**
    *   *Returns:* List of orders where the Gateway Webhook says "Paid", but the Bank Settlement hasn't matched yet, or amounts differ due to hidden gateway fees.
*   **`POST /finance/reconciliation/cod-remittance`**
    *   *Payload:* `logistics_partner_id`, `amount_remitted`, `bank_reference`, `proof_url`.
    *   *Action:* Clears the `1030 COD Receivable` ledger and moves cash to `1010 Operating`.

---

### 🗺️ PART 3: Step-by-Step Implementation Plan

#### Phase 1: Database Seeding & Foundation (Days 1-3)
1.  **Migration Execution:** Run the Alembic migration to create the `account_groups`, `accounts`, `journal_entries`, and `journal_entry_lines` tables.
2.  **Idempotent Seeding:** Execute the backend seed script to populate the exact GCC CoA mapped out in Part 1. Ensure the script checks for existing data so it doesn't duplicate accounts on server restart.
3.  **Treasury Buckets:** Seed the `treasury_accounts` table, mapping them to the new GL codes (e.g., mapping the "Main Bank" bucket to GL `1010`).

#### Phase 2: The Core Treasury Engine (Days 4-7)
1.  **Build the `post_journal_entry` Service:** Create the central backend service that accepts an array of Debits and Credits. 
2.  **Implement the Golden Rule Validation:** Add strict logic that aborts the transaction if `Sum(Debits) != Sum(Credits)`.
3.  **Implement Row-Level Locking:** Ensure the service uses `SELECT ... FOR UPDATE` on the `account_balances` cache table to prevent race conditions during high-volume checkout.
4.  **Wire the Operational Triggers:** 
    *   Inject the engine into the `Checkout Controller` (Dr Gateway Clearing / Cr Deferred Revenue).
    *   Inject the engine into the `Order Delivered Webhook` (Dr Deferred Revenue / Cr Supplier Payable, Logistics Payable, VAT Payable, Commission Revenue).

#### Phase 3: Finance API & Controllers (Days 8-12)
1.  **Build the Read-Only Endpoints:** Implement the `GET` endpoints for the Dashboard, Cash Position, and Trial Balance. Optimize these queries using PostgreSQL materialized views or Redis caching so the dashboard loads in <200ms.
2.  **Build the Payout State Machine:** Implement the `POST` endpoints for Payout Batches. Ensure the state transitions (`Draft` -> `Approved` -> `Dispatched`) trigger the correct Treasury Ledger movements.
3.  **Implement the Maker-Checker Middleware:** Add a decorator to the `/approve` and `/dispatch` endpoints ensuring the user approving the batch is *not* the same user who generated it.

#### Phase 4: Frontend Command Center UI (Days 13-18)
1.  **The "Heartbeat" Dashboard:** Build the top-level metrics cards using Next.js Server Components for instant initial load, hydrating with WebSockets for real-time GMV ticks.
2.  **The General Ledger Data Grid:** Implement a high-performance data table (using `@tanstack/react-table`) with sticky headers, tabular numerals, and deep-linking filters for the Ledger.
3.  **The Payout Control Room:** Build the UI for Finance Admins to review generated batches, view the "Maker's" notes, and click the cryptographic "Approve & Dispatch" button.
4.  **The VAT Remittance Wizard:** Build a dedicated UI that pulls the `2040 VAT Payable` ledger, formats it into the exact CSV structure required by the KSA ZATCA or Oman tax portals, and logs the remittance.

#### Phase 5: Reconciliation & Shadow Testing (Days 19-21)
1.  **Shadow Mode Execution:** For the first week, run the new Treasury Engine in "Shadow Mode" alongside the legacy `wallet_balance` system. 
2.  **Drift Detection:** Run a nightly cron job that compares the Legacy Supplier Balances against the New Ledger `Supplier Payables`. Alert the engineering team to any discrepancies.
3.  **Gateway Auto-Matching:** Implement the background worker that ingests daily CSV settlement reports from Tap/Stripe and automatically matches them against the `1020 Gateway Clearing` ledger, flagging exceptions for human review.

### Summary
By strictly adhering to this **GCC-Tailored CoA** and building the **Finance Command Center APIs** around the double-entry ledger rather than raw order tables, Zozi will achieve institutional-grade financial control. This architecture ensures that VAT liabilities are never accidentally spent, COD cash is rigorously tracked, and supplier payouts are mathematically flawless.


----------------------------


### 🏛️ 1. Core ERP Module Expansion (From Basic to Enterprise)
*   **Chart of Accounts (COA) Management**: Implement full hierarchical CRUD for accounts (Assets, Liabilities, Equity, Revenue, Expenses) with account codes, types, and multi-currency support.
*   **Accounts Receivable (AR) & Invoicing**: Dedicated tab for customer invoices, aging reports, payment tracking, and automated late-fee calculations.
*   **Accounts Payable (AP) & Vendor Bills**: Centralized vendor management, bill entry, approval workflows, and AP aging reports.
*   **General Ledger (GL) & Journal Entries**: Immutable double-entry ledger with manual journal entry creation, recurring journal templates, and period-close locking.
*   **Treasury & Cash Management**: Real-time cash position snapshots, multi-bank account tracking, and gateway settlement schedules.
*   **Fixed Assets & Depreciation**: Asset registry with automated depreciation runs (straight-line, declining balance) posting directly to the GL.

### 🤖 2. Intelligent Finance Automation
*   **OCR Bill Scanning**: Integration with AI/OCR to scan uploaded receipts/invoices, auto-extract vendor, date, amount, and tax, and draft an `ScannedExpense` record for approval.
*   **Auto Bank Reconciliation**: Import bank statement CSVs/APIs and use a configurable `BankMappingRule` engine to auto-match transactions with GL entries, flagging only exceptions for manual review.
*   **Accrual & Reversal Engine**: Automated month-end accruals for unpaid expenses/revenues, with a scheduled background job to auto-reverse them in the following period.
*   **Scheduled Finance Cycles**: Cron-driven automation for batch supplier payouts, logistics dispatch, and daily cash position snapshots (`cash_position_snapshots`).

### 🎨 3. Dynamic Frontend Architecture
*   **Modular Tabbed Interface**: A dynamic, route-driven sidebar (e.g., `/admin/finance?section=chart-of-accounts`, `expense-scan`, `bank-mapping`, `fixed-assets`, `accruals`) that loads components on demand.
*   **Real-Time Dashboards**: Live-updating KPI cards (Free Cash, Total Liabilities, Net Income) with skeleton loaders to prevent layout shift during data fetching.
*   **Advanced Data Tables**: Enterprise-grade tables with server-side pagination, filtering, sorting, and bulk actions (e.g., bulk approve AP bills).
*   **Responsive & Accessible Design**: Fully optimized for desktop (dense data views) and tablet, with proper ARIA labels and keyboard navigation.

### ⚡ 4. Performance & Scalability Optimization (1000s of Concurrent Users)
*   **Eliminate N+1 Queries**: Refactor all SQLAlchemy queries in finance controllers to use `selectinload()` or `joinedload()` for related entities (e.g., loading `JournalEntry` with its `JournalEntryLine`s and `Account` details in a single query).
*   **Database Indexing**: Ensure composite indexes exist on high-traffic columns: `(country_code, created_at)`, `(status, due_date)`, and `(vendor_id)`.
*   **Materialized Views for Dashboards**: Replace on-the-fly aggregate queries (e.g., total revenue, AP aging) with pre-computed materialized views refreshed hourly via background jobs.
*   **Frontend Performance**: Enable Next.js Turbopack for dev, implement React `Suspense` and dynamic imports (`next/dynamic`) for heavy finance charts, and cache static reference data (like COA lists) in Zustand/Redux.

### 🧪 5. Sample Transaction Seeding & Workflows
*   **End-to-End Sample Flow**: Provide a "Demo Mode" or seed script that creates:
    1. A vendor and an AP Bill.
    2. An OCR-scanned expense that gets approved and posted to the GL.
    3. A customer invoice (AR) that receives a partial payment.
    4. A manual journal entry for month-end depreciation.
    5. A bank reconciliation matching a statement line to the AP payment.

### 🔐 6. Admin CRUD & Role-Based Access Control (RBAC)
*   **Granular Finance Permissions**: Enforce strict permission checks (e.g., `finance.ap.view`, `finance.ap.post`, `finance.ledger.manual_adjust`, `finance.reconciliation`) via a `require_finance_permission` dependency.
*   **Maker-Checker Workflow**: Utilize the `pending_journal_entries` table as a staging area. Sub-admins can *create* entries, but only users with `finance.ledger.approve` can *post* them to the live `journal_entries` table.
*   **Delegated Access**: Admin UI to assign specific finance modules (e.g., "AR Clerk", "AP Manager", "Treasury Analyst") to employees or sub-admins without granting full super-admin access.

### 🔍 7. System Audit & Expert Enhancements
*   **Unified Finance Audit Log**: Ensure every financial action (post, reverse, approve, automate) is recorded in the `finance_audit_logs` table with `actor_id`, `action`, `entity_type`, `old_value_json`, and `new_value_json`.
*   **Budget vs. Actual Variance**: Add a new tab to compare posted GL entries against predefined departmental/category budgets for the active `FiscalPeriod`.
*   **Multi-Currency & FX Handling**: Ensure all ledgers track the transaction currency and convert to the base country currency (e.g., OMR) using a configurable, time-stamped exchange rate table.
*   **Tax & VAT Remittance Tracking**: Dedicated view to aggregate collected VAT (from sales) and paid VAT (from expenses) to simplify periodic government tax filings.

### 🛡️ 8. Comprehensive Testing Strategy
*   **Unit Tests**: Rigorous testing of GL math (ensuring debits == credits), accrual reversal logic, and depreciation calculations.
*   **Integration Tests**: Mocked tests for the OCR parsing service and the bank reconciliation mapping engine to verify they handle malformed data gracefully.
*   **End-to-End (E2E) Playwright Tests**: Automated browser tests simulating an admin logging in, navigating to `/admin/finance`, creating a manual journal entry, approving it, and verifying it appears in the trial balance.
*   **Load Testing**: Use tools like k6 or Locust to simulate 1000+ concurrent users hitting the financial dashboard endpoints to validate the effectiveness of the materialized views and indexing.

### 9. **Fixed Assets Management** (Partially present but needs enhancement)
- **Asset Registration**: Complete asset lifecycle tracking
- **Depreciation Schedules**: Automated depreciation calculation (straight-line, declining balance)
- **Asset Disposal**: Sale/scrap workflow with gain/loss calculation
- **Asset Transfer**: Inter-department/country asset transfers

### 10. **Tax Management & Compliance**
- **VAT/GST Configuration**: Multi-country tax rate management
- **Tax Remittance**: Automated tax liability calculation and filing reports
- **Tax Exemptions**: Customer/supplier tax exemption certificate management
- **Withholding Tax**: TDS/WHT calculation and reporting

### 11. **Multi-Currency & FX Management**
- **Exchange Rate Management**: Daily rate updates (manual + API integration)
- **FX Gain/Loss**: Automatic unrealized/realized gain/loss calculation
- **Currency Revaluation**: Month-end revaluation of foreign currency balances
- **Hedging Instruments**: Forward contract tracking (advanced)

### 12. **Inter-Company Accounting**
- **Inter-Company Transactions**: Automated IC sales/purchases
- **IC Reconciliation**: Automatic matching and elimination
- **Transfer Pricing**: TP policy enforcement and documentation

### 13. **Financial Reporting Enhancements**
- **Custom Report Builder**: Drag-and-drop report designer
- **Scheduled Reports**: Automated email delivery of reports
- **Consolidated Reporting**: Multi-country consolidation
- **Audit Trail Reports**: Complete change history with before/after values

### 14. **Cash Management & Treasury**
- **Cash Flow Forecasting**: 30/60/90-day cash flow projections
- **Bank Reconciliation Automation**: AI-powered statement matching
- **Petty Cash Management**: Petty cash fund tracking
- **Investment Tracking**: Short-term investment portfolio

### 15. **Expense Management Automation**
- **OCR Receipt Scanning**: AI-powered receipt data extraction
- **Expense Approval Workflow**: Multi-level approval routing
- **Corporate Card Integration**: Direct feed from corporate cards
- **Travel Expense Management**: Per diem, mileage, travel policy enforcement

### 16. **Revenue Recognition**
- **ASC 606/IFRS 15 Compliance**: Automated revenue recognition schedules
- **Deferred Revenue**: Subscription/contract revenue amortization
- **Milestone Billing**: Project-based revenue recognition

### 17. **Cost Accounting**
- **Cost Center Accounting**: Department/project cost allocation
- **Activity-Based Costing**: ABC cost driver allocation
- **Standard Costing**: Variance analysis (price, quantity, efficiency)
- **Job Costing**: Project-specific cost tracking

### 18. **Financial Controls & Compliance**
- **Segregation of Duties**: Role-based access controls
- **Journal Entry Approval**: Maker-checker workflow
- **Period Close Checklist**: Automated close process management
- **SOX Compliance Controls**: Control testing and documentation

### 19. **Analytics & Business Intelligence**
- **Financial Dashboards**: Real-time KPI visualization
- **Predictive Analytics**: ML-based cash flow forecasting
- **Benchmarking**: Industry comparison metrics
- **What-If Analysis**: Scenario planning tools

### 20. **Supplier & Customer Finance**
- **Supplier Portal**: Self-service invoice submission and status
- **Customer Credit Management**: Credit limit enforcement and scoring
- **Dunning Management**: Automated collection workflow
- **Early Payment Discounts**: Dynamic discounting offers

---

### 🤖 1. Next-Gen Intelligent Automations (The 75% Goal)
*   **AI-Powered Auto Bank Reconciliation**: 
    *   Ingest bank statements via API (Plaid/Yodlee) or CSV.
    *   Use an AI fuzzy-matching engine to match statement lines to `JournalEntry` or `APLedger` records based on amount, date variance (±3 days), and reference ID.
    *   **Auto-Post**: Matches with >95% confidence are auto-reconciled. Lower confidence items are flagged in an "Exception Dashboard" for manual review.
*   **Email-to-Ledger Parsing (Inbox Automation)**:
    *   Dedicated finance inbox (e.g., `finance@zozi.com`) monitored by an AI parser.
    *   Automatically extracts vendor invoices, gateway settlement reports (Stripe/Tap), and commission statements from email attachments (PDF/CSV).
    *   Auto-drafts `ScannedExpense` or `GatewaySettlementSchedule` records, attaching the original email as an immutable audit artifact.
*   **Smart Commission & Payout Automation**:
    *   Nightly cron job reads `commission_ledger_entries` and `payout_rules`.
    *   Auto-generates `payout_batches` grouped by supplier/logistics partner.
    *   Auto-sends an email/SMS to the supplier with a secure link to review and approve the batch before the Maker-Checker finance admin releases the funds.
*   **Auto-Accrual & Reversal Engine**:
    *   Automatically identifies unbilled expenses or uncollected revenues at month-end.
    *   Posts reversing journal entries on Day 1 of the next period, eliminating manual month-end close busywork.
*   **Automated Tax & VAT Remittance**:
    *   Continuously aggregates output VAT (from sales) and input VAT (from expenses) into a `VATRemittance` staging table.
    *   Auto-generates country-specific tax filing reports ready for government portal submission.

---

### 🏛️ 2. Core ERP Module Consolidation (De-duplicated)
*   **Unified Chart of Accounts (COA)**: Hierarchical, multi-currency COA with strict `account_type` (Asset, Liability, Equity, Revenue, Expense) and `normal_side` (Debit/Credit) enforcement.
*   **Immutable Double-Entry General Ledger**: The single source of truth. Every transaction *must` have equal debits and credits. Direct DB updates to `journal_entries` are blocked at the database level.
*   **Sub-Ledgers (AR & AP)**: 
    *   **AR**: Auto-generates invoices on order dispatch, tracks aging (30/60/90 days), and triggers automated dunning (collection) emails to customers.
    *   **AP**: Centralized vendor bill management with multi-level approval workflows before posting to the GL.
*   **Fixed Assets & Depreciation**: Asset registry with automated monthly depreciation runs (straight-line/declining balance) that auto-post to the GL, plus disposal/scrap workflows with gain/loss calculation.
*   **Advanced Cost & Revenue Accounting**: 
    *   Cost Center tagging on every journal line for departmental P&L.
    *   ASC 606 / IFRS 15 compliant deferred revenue amortization for subscriptions or milestone-based billing.

---

### 💰 3. Treasury, Cash & Multi-Currency Management
*   **Real-Time Cash Positioning**: `cash_position_snapshots` updated asynchronously via event listeners whenever a `1000`-series (Asset) account is touched, providing instant dashboard visibility without heavy queries.
*   **Automated FX Revaluation**: Month-end cron job that revalues foreign currency bank accounts and open AR/AP balances using the latest `exchange_rates`, auto-posting unrealized FX gain/loss journal entries.
*   **Cash Flow Forecasting**: ML-driven 30/60/90-day projections based on historical payment behaviors, open AR/AP, and scheduled `payout_batches`.

---

### 🎨 4. Dynamic, High-Performance Frontend Architecture
*   **Modular, Route-Driven UI**: Clean sidebar navigation (`/admin/finance?section=bank-mapping`, `accruals`, `coa`) that lazy-loads components to keep the initial bundle size tiny.
*   **Enterprise Data Grids**: Server-side paginated, filterable, and sortable tables for Journals, AR, and AP. Includes bulk actions (e.g., "Approve Selected 50 Bills").
*   **Real-Time KPI Dashboards**: Powered by pre-computed **Materialized Views** (refreshed hourly) for metrics like *Net Income, AP Aging, and Free Cash*, ensuring sub-second load times even with millions of rows.
*   **Interactive Reconciliation UI**: A split-screen interface showing the Bank Statement line on the left and suggested GL matches on the right, allowing one-click reconciliation or manual override.

---

### 🔐 5. Ironclad Security, RBAC & Compliance
*   **Granular Finance Permissions**: Strict enforcement via `require_finance_permission("finance.ap.post")`. Roles are segmented (e.g., "AP Clerk" can draft, "Finance Manager" can approve).
*   **Maker-Checker Workflow**: All manual journal entries and payout batches are created in `pending_journal_entries` or `payout_batches` (status: `draft`). They *cannot* be posted to the live ledger without a second, distinct user with `approve` rights.
*   **Immutable Audit Trail**: Every financial action (post, reverse, auto-reconcile) is logged in `finance_audit_logs` with `actor_id`, `old_value_json`, `new_value_json`, and `ip_address`. Logs are append-only.
*   **Period Close Locking**: Once a `FiscalPeriod` is marked "Closed", the system rejects any journal entry postings with a `created_at` date in that period, preventing historical tampering.

---

### ⚡ 6. Performance & Scalability (1000s of Concurrent Users)
*   **N+1 Query Eradication**: All SQLAlchemy finance queries must use `selectinload()` or `joinedload()` (e.g., fetching a `JournalEntry` with its `lines` and `account` details in a single DB round-trip).
*   **Strategic Indexing**: Composite indexes on `(country_code, created_at)`, `(status, due_date)`, and `(entity_type, entity_id)` to ensure sub-millisecond lookups.
*   **Read/Write Separation**: Analytical queries (Balance Sheet, P&L) are routed to read replicas or served from Materialized Views, protecting the primary transactional database from reporting load.

---

### 🛡️ 7. Triple-Verification Testing & Validation Strategy
*   **Mathematical Integrity Tests**: Unit tests that assert `SUM(debit) == SUM(credit)` for every generated journal entry. If not, the transaction is aborted and an alert is fired.
*   **Nightly Reconciliation Cron**: A background job that runs every night at 2 AM, verifying that the sum of all `ap_ledger_entries` and `ar_ledger_entries` perfectly matches the control account balances in the main `journal_entries`. Any variance triggers a critical Slack/Email alert.
*   **Mocked Automation Tests**: Integration tests that feed malformed CSVs, fake OCR data, and edge-case bank statements into the automation engine to prove it fails gracefully into the "Exception Queue" rather than crashing or posting bad data.
*   **E2E Playwright Scenarios**: Automated browser tests simulating the full lifecycle: *Upload Invoice CSV -> AI maps to GL -> Drafts Journal -> Manager Approves -> Appears in Trial Balance.*

---

### 🏛️ 1. Core ERP Module Consolidation (De-duplicated)
*   **Unified Chart of Accounts (COA)**: Hierarchical, multi-currency COA with strict `account_type` (Asset, Liability, Equity, Revenue, Expense) and `normal_side` (Debit/Credit) enforcement.
*   **Immutable Double-Entry General Ledger**: The single source of truth. Every transaction *must* have equal debits and credits. Direct DB updates to `journal_entries` are blocked at the database level.
*   **Sub-Ledgers (AR & AP)**: 
    *   **AR**: Auto-generates invoices on order dispatch, tracks aging (30/60/90 days), and triggers automated dunning (collection) emails.
    *   **AP**: Centralized vendor bill management with multi-level approval workflows before posting to the GL.
*   **Fixed Assets & Depreciation**: Asset registry with automated monthly depreciation runs (straight-line/declining balance) that auto-post to the GL, plus disposal/scrap workflows with gain/loss calculation.
*   **Advanced Cost & Revenue Accounting**: Cost Center tagging on every journal line for departmental P&L, and ASC 606 / IFRS 15 compliant deferred revenue amortization.

---

### 🤖 2. Next-Gen Intelligent Automations (The 75% Goal)
*   **AI-Powered Auto Bank Reconciliation**: Ingest statements via API/CSV. An AI fuzzy-matching engine matches lines to GL entries based on amount, date variance (±3 days), and reference ID. >95% confidence auto-posts; lower confidence routes to an Exception Dashboard.
*   **Email-to-Ledger Parsing (Inbox Automation)**: A dedicated finance inbox monitored by AI extracts vendor invoices, gateway settlement reports (Stripe/Tap), and commission statements from attachments. It auto-drafts `ScannedExpense` or `GatewaySettlementSchedule` records, attaching the original email as an immutable audit artifact.
*   **Smart Commission & Payout Automation**: A nightly cron reads `commission_ledger_entries` and `payout_rules`, auto-generates `payout_batches`, and sends secure email/SMS links to suppliers for review before the Maker-Checker finance admin releases funds.
*   **Auto-Accrual & Reversal Engine**: Automatically identifies unbilled expenses or uncollected revenues at month-end and posts reversing journal entries on Day 1 of the next period.
*   **Automated Tax & VAT Remittance**: Continuously aggregates output VAT (sales) and input VAT (expenses) into a `VATRemittance` staging table, auto-generating country-specific tax filing reports.

---

### 💰 3. Treasury, Cash & Multi-Currency Management
*   **Real-Time Cash Positioning**: `cash_position_snapshots` updated asynchronously via event listeners whenever an Asset account is touched, ensuring instant dashboard visibility without heavy queries.
*   **Automated FX Revaluation**: Month-end cron job revalues foreign currency bank accounts and open AR/AP balances using the latest `exchange_rates`, auto-posting unrealized FX gain/loss journal entries.
*   **Cash Flow Forecasting**: ML-driven 30/60/90-day projections based on historical payment behaviors, open AR/AP, and scheduled `payout_batches`.

---

### 🎨 4. Dynamic, High-Performance Frontend Architecture
*   **Modular, Route-Driven UI**: Clean sidebar navigation (e.g., `/admin/finance?section=bank-mapping`, `accruals`, `coa`) that lazy-loads components to keep the initial bundle size tiny.
*   **Enterprise Data Grids**: Server-side paginated, filterable, and sortable tables for Journals, AR, and AP, featuring bulk actions (e.g., "Approve Selected 50 Bills").
*   **Real-Time KPI Dashboards**: Powered by pre-computed **Materialized Views** (refreshed hourly) for metrics like Net Income, AP Aging, and Free Cash, ensuring sub-second load times.
*   **Interactive Reconciliation UI**: Split-screen interface showing Bank Statement lines on the left and suggested GL matches on the right for one-click reconciliation or manual override.

---

### ⚡ 5. Performance & Scalability (1000s of Concurrent Users)
*   **N+1 Query Eradication**: All SQLAlchemy finance queries must use `selectinload()` or `joinedload()` (e.g., fetching a `JournalEntry` with its `lines` and `account` details in a single DB round-trip).
*   **Strategic Indexing**: Composite indexes on `(country_code, created_at)`, `(status, due_date)`, and `(entity_type, entity_id)` for sub-millisecond lookups.
*   **Read/Write Separation**: Analytical queries (Balance Sheet, P&L) are routed to read replicas or served from Materialized Views, protecting the primary transactional database from reporting load.

---

### 🔐 6. Ironclad Security, RBAC & Compliance
*   **Granular Finance Permissions**: Strict enforcement via `require_finance_permission("finance.ap.post")`. Roles are segmented (e.g., "AP Clerk" can draft, "Finance Manager" can approve).
*   **Maker-Checker Workflow**: Manual journal entries and payout batches are created in `pending_journal_entries` or `payout_batches` (status: `draft`). They *cannot* be posted to the live ledger without a second, distinct user with `approve` rights.
*   **Immutable Audit Trail**: Every financial action (post, reverse, auto-reconcile) is logged in `finance_audit_logs` with `actor_id`, `old_value_json`, `new_value_json`, and `ip_address`. Logs are append-only.
*   **Period Close Locking**: Once a `FiscalPeriod` is marked "Closed", the system rejects any journal entry postings with a `created_at` date in that period, preventing historical tampering.

---

### 🛡️ 7. Triple-Verification Testing & Validation Strategy
*   **Mathematical Integrity Tests**: Unit tests asserting `SUM(debit) == SUM(credit)` for every generated journal entry. Failures abort the transaction and fire an alert.
*   **Nightly Reconciliation Cron**: A background job verifying that the sum of all `ap_ledger_entries` and `ar_ledger_entries` perfectly matches control account balances in `journal_entries`. Variances trigger critical Slack/Email alerts.
*   **Mocked Automation Tests**: Integration tests feeding malformed CSVs, fake OCR data, and edge-case bank statements into the automation engine to prove it fails gracefully into the "Exception Queue" rather than crashing or posting bad data.
*   **E2E Playwright Scenarios**: Automated browser tests simulating the full lifecycle: *Upload Invoice CSV → AI maps to GL → Drafts Journal → Manager Approves → Appears in Trial Balance.*

---

### 🧠 Core Philosophy & Architecture
*   **75% Zero-Touch Automation:** Routine tasks (reconciliation, accruals, commissions, tax) are handled by AI/rules engines without human intervention.
*   **Triple-Verification Engine:** Automated posts require: (1) Rule/Logic Match, (2) AI Confidence Score > 95%, (3) Cross-reference against the immutable General Ledger. Failures route to an "Exception Queue".
*   **Event-Driven Ledger:** Operational systems (Orders, Logistics) publish events (e.g., `OrderDelivered`); the Finance Engine listens and generates journal entries, preventing tight coupling.

---

### 🏛️ 1. Core ERP Models & Features
*   **Chart of Accounts (`accounts`, `account_groups`)**: Hierarchical, multi-currency COA with strict `account_type` (Asset, Liability, Equity, Revenue, Expense) and `normal_side` (Debit/Credit) enforcement.
*   **General Ledger (`journal_entries`, `journal_entry_lines`)**: Immutable double-entry ledger. Every transaction *must* have equal debits/credits. Direct DB updates are blocked at the database level.
*   **Accounts Receivable (`ar_invoices`, `ar_ledger_entries`)**: Auto-generates invoices on dispatch, tracks 30/60/90-day aging, and triggers automated dunning (collection) emails.
*   **Accounts Payable (`ap_bills`, `ap_ledger_entries`)**: Centralized vendor bill management with multi-level approval workflows before posting to the GL.
*   **Fixed Assets (`fixed_assets`)**: Asset registry with automated monthly depreciation runs (straight-line/declining balance) that auto-post to the GL, plus disposal/scrap workflows with gain/loss calculation.
*   **Cost & Revenue Accounting**: Cost Center tagging on every journal line for departmental P&L, and ASC 606 / IFRS 15 compliant deferred revenue amortization.

---

### 🤖 2. Next-Gen Intelligent Automations (The 75% Goal)
*   **AI Auto Bank Reconciliation (`bank_statement_imports`, `bank_statement_lines`, `bank_mapping_rules`)**: Ingests statements via API/CSV. Fuzzy-matches lines to GL entries based on amount, date variance (±3 days), and reference ID. >95% confidence auto-posts; lower confidence routes to an Exception Dashboard.
*   **Email-to-Ledger Parsing (`scanned_expenses`, `gateway_settlement_schedules`)**: AI monitors a dedicated finance inbox, extracts vendor invoices and gateway reports from attachments, auto-drafts records, and attaches the original email as an immutable audit artifact.
*   **Smart Commission & Payouts (`commission_ledger_entries`, `payout_rules`, `payout_batches`, `payout_batch_items`, `payouts`)**: Nightly cron generates payout batches grouped by partner, sending secure email/SMS links to suppliers for review before the Maker-Checker admin releases funds.
*   **Auto-Accrual & Reversal (`accruals`)**: Identifies unbilled expenses or uncollected revenues at month-end and posts reversing journal entries on Day 1 of the next period.
*   **Automated Tax & VAT (`vat_remittances`)**: Continuously aggregates output VAT (sales) and input VAT (expenses) into a staging table, auto-generating country-specific tax filing reports.

---

### 💰 3. Treasury, Cash & Multi-Currency Management
*   **Real-Time Cash Positioning (`cash_position_snapshots`)**: Updated asynchronously via event listeners whenever an Asset account is touched, ensuring instant dashboard visibility without heavy queries.
*   **Automated FX Revaluation (`exchange_rates`)**: Month-end cron job revalues foreign currency bank accounts and open AR/AP balances using the latest rates, auto-posting unrealized FX gain/loss journal entries.
*   **Cash Flow Forecasting (`cash_flow_forecasts`)**: ML-driven 30/60/90-day projections based on historical payment behaviors, open AR/AP, and scheduled `payout_batches`.

---

### 🎨 4. Dynamic, High-Performance Frontend Architecture
*   **Modular, Route-Driven UI**: Clean sidebar navigation (e.g., `/admin/finance?section=bank-mapping`, `accruals`, `coa`) that lazy-loads components to keep initial bundle size tiny.
*   **Enterprise Data Grids**: Server-side paginated, filterable, and sortable tables for Journals, AR, and AP, featuring bulk actions (e.g., "Approve Selected 50 Bills").
*   **Real-Time KPI Dashboards**: Powered by pre-computed **Materialized Views** (refreshed hourly) for metrics like Net Income, AP Aging, and Free Cash, ensuring sub-second load times.
*   **Interactive Reconciliation UI**: Split-screen interface showing Bank Statement lines on the left and suggested GL matches on the right for one-click reconciliation or manual override.

---

### ⚡ 5. Performance & Scalability (1000s of Concurrent Users)
*   **N+1 Query Eradication**: Mandatory use of `selectinload()` or `joinedload()` in SQLAlchemy (e.g., fetching a `JournalEntry` with its `lines` and `account` details in a single DB round-trip).
*   **Strategic Indexing**: Composite indexes on `(country_code, created_at)`, `(status, due_date)`, and `(entity_type, entity_id)` for sub-millisecond lookups.
*   **Read/Write Separation**: Analytical queries (Balance Sheet, P&L) are routed to read replicas or served from Materialized Views, protecting the primary transactional database.

---

### 🔐 6. Ironclad Security, RBAC & Compliance
*   **Granular Permissions**: Strict enforcement via `require_finance_permission("finance.ap.post")`. Roles are segmented (e.g., "AP Clerk" drafts, "Finance Manager" approves).
*   **Maker-Checker Workflow**: Manual journal entries and payout batches are created in `pending_journal_entries` or `payout_batches` (status: `draft`). They *cannot* be posted to the live ledger without a second, distinct user with `approve` rights.
*   **Immutable Audit Trail (`finance_audit_logs`)**: Every financial action (post, reverse, auto-reconcile) is logged with `actor_id`, `old_value_json`, `new_value_json`, and `ip_address`. Logs are append-only.
*   **Period Close Locking (`fiscal_periods`)**: Once a period is marked "Closed", the system rejects any journal entry postings with a `created_at` date in that period, preventing historical tampering.

---

### 🛡️ 7. Triple-Verification Testing & Validation Strategy
*   **Mathematical Integrity Tests**: Unit tests asserting `SUM(debit) == SUM(credit)` for every generated journal entry. Failures abort the transaction and fire an alert.
*   **Nightly Reconciliation Cron**: A 2 AM background job verifying that the sum of all `ap_ledger_entries` and `ar_ledger_entries` perfectly matches control account balances in `journal_entries`. Variances trigger critical Slack/Email alerts.
*   **Mocked Automation Tests**: Integration tests feeding malformed CSVs, fake OCR data, and edge-case bank statements into the automation engine to prove it fails gracefully into the "Exception Queue".
*   **E2E Playwright Scenarios**: Automated browser tests simulating the full lifecycle: *Upload Invoice CSV → AI maps to GL → Drafts Journal → Manager Approves → Appears in Trial Balance.*


-----------------------------------------------------------------------------------


Here is the **Ultimate, Comprehensive Master Roadmap** for the Zozi Accounts, Finance, and Treasury System. This is a complete, de-duplicated, end-to-end blueprint mapping every database model, ledger rule, automation workflow, UI page/tab, and implementation phase. 

This document is designed to be handed directly to your CTO, Backend, and Frontend teams as the single source of truth.

---

# 🗺️ ZOZI FINANCE & TREASURY MASTER ROADMAP

## 🧠 Phase 0: Core Architectural Mandates (Non-Negotiable)
1. **Event-Driven Ledger**: Operational systems (Orders, Logistics) *never* write to the GL. They publish events (e.g., `OrderDelivered`), and the `TreasuryService` listens and generates immutable journal entries.
2. **Immutable Double-Entry**: Zero direct `UPDATE` to balance columns. Balances are strictly calculated via immutable `JournalEntryLine` records. **Constraint:** `SUM(Debits) == SUM(Credits)` enforced at the DB level.
3. **Data Types**: Strict use of Python `Decimal` and PostgreSQL `NUMERIC(16,4)` for all financial figures. **No floating-point math.**
4. **75% Zero-Touch Automation**: Routine tasks are handled by AI/rules engines. Humans only handle the "Exception Queue".
5. **Triple-Verification Engine**: Automated posts must pass: (1) Rule/Logic Match, (2) AI Confidence > 95%, (3) GL Cross-reference. Failures route to manual review.

---

## 🗄️ Section 1: Complete Database Model Mapping (The Schema)
*Organized by functional domain. All tables require `created_at`, `updated_at`, `country_code`, and `currency`.*

### 1. Chart of Accounts & Ledger (The Truth)
* `account_groups`: Hierarchical buckets (1000 Assets, 2000 Liabilities, 3000 Equity, 4000 Revenue, 5000 COGS, 6000 Expenses).
* `accounts`: Specific GL codes (e.g., `1010 Cash Operating`, `2040 VAT Payable`), includes `account_type` and `normal_side` (Dr/Cr).
* `account_balances`: Materialized cache for fast dashboard loading (updated via triggers/events).
* `journal_entries`: Header (Timestamp, Event Type, Reference ID, Currency, Status: `draft`|`posted`|`reversed`).
* `journal_entry_lines`: Lines (Account ID, Debit Amount, Credit Amount, Cost Center ID).
* `pending_journal_entries`: Staging table for Maker-Checker manual approvals.
* `fiscal_periods`: Accounting periods (Month/Quarter/Year) with `is_closed` boolean to lock historical data.

### 2. Treasury & Cash Management
* `treasury_accounts`: Physical cash pools (Operating, Gateway Settlement, COD Receivable, VAT/Supplier Reserves).
* `treasury_transactions`: Audit trail for manual transfers between treasury buckets.
* `cash_position_snapshots`: Asynchronous, end-of-day/hourly historical cash states.
* `gateway_settlement_schedules`: Expected payouts from Stripe/Tap/Thawani (T+2/T+7 tracking).
* `cash_flow_forecasts`: ML-driven 30/60/90-day projections.
* `exchange_rates`: Time-stamped FX rates for multi-currency revaluation.

### 3. Sub-Ledgers (AR, AP, Marketplace)
* `ar_invoices` & `ar_ledger_entries`: B2B/Customer receivables, aging tracking, and payment application.
* `ap_bills` & `ap_ledger_entries`: Vendor bill management, multi-level approval workflows.
* `commission_ledger_entries`: Calculated marketplace cuts per order.
* `payout_rules`, `payout_batches`, `payout_batch_items`, `payouts`: Supplier/Logistics disbursement lifecycle (`draft` → `pending_approval` → `approved` → `dispatched` → `settled`).

### 4. Intelligent Automation & Compliance
* `bank_statement_imports` & `bank_statement_lines`: Ingested bank data (CSV/API).
* `bank_mapping_rules`: AI fuzzy-matching configurations (amount, date variance ±3 days, reference ID).
* `scanned_expenses`: OCR/AI-extracted invoice data with `approval_status`.
* `accruals`: Month-end unbilled expenses/revenues and auto-reversal tracking.
* `vat_remittances`: Aggregated output/input VAT staging for ZATCA/FTA filing.
* `fixed_assets`: Asset registry, depreciation schedules (straight-line/declining), and disposal tracking.
* `finance_audit_logs`: Append-only log (`actor_id`, `action`, `entity_type`, `old_value_json`, `new_value_json`, `ip_address`).

---

## ⚖️ Section 2: The Ledger Double-Entry Mapping System
*The exact accounting logic the `TreasuryService` must execute for every major platform event.*

| Business Event | Debit (Dr) Account | Credit (Cr) Account(s) |
| :--- | :--- | :--- |
| **1. Customer Pays via Card** | 1020 Gateway Clearing (Asset) | 2060 Deferred Revenue (Liability) |
| **2. Gateway Settles to Bank** | 1010 Cash Operating (Asset)<br>6010 Gateway Fees (Expense) | 1020 Gateway Clearing (Asset) |
| **3. Order Delivered (Card)** | 2060 Deferred Revenue (Liability) | 2010 Supplier Payable<br>2020 Logistics Payable<br>4010 Commission Revenue<br>2040 VAT Payable |
| **4. Order Delivered (COD)** | 1030 COD Receivable (Asset) | 2010 Supplier Payable<br>2020 Logistics Payable<br>4010 Commission Revenue<br>2040 VAT Payable |
| **5. Logistics Remits COD** | 1010 Cash Operating (Asset) | 1030 COD Receivable (Asset) |
| **6. Supplier Payout Dispatched**| 2010 Supplier Payable (Liability) | 1010 Cash Operating (Asset) |
| **7. Customer Refund Approved** | 4010 Revenue / 2060 Deferred Rev | 1010 Cash Operating / 1020 Gateway Clearing |
| **8. Month-End FX Revaluation** | 6060 Unrealized FX Loss (Expense) | 1010/1100 Foreign Currency Accounts (Asset) *(or vice versa for gain)* |

---

## 🤖 Section 3: Intelligent Automation Workflows (The 75% Goal)
*Every automation must have a fallback to the "Exception Queue" if confidence < 95%.*

1. **AI Auto Bank Reconciliation**: 
   - *Trigger*: Daily CSV/API bank statement ingest.
   - *Action*: Fuzzy-matches statement lines to `journal_entries` or `ap_ledger_entries`. Auto-reconciles >95% confidence matches. Flags exceptions for manual split-screen review.
2. **Email-to-Ledger Parsing (Inbox Automation)**:
   - *Trigger*: Email received at `finance@zozi.com` with PDF/CSV attachment.
   - *Action*: AI extracts vendor, date, amount, tax. Auto-drafts `scanned_expenses` or `gateway_settlement_schedules`. Attaches original email as immutable audit artifact.
3. **Smart Commission & Payouts**:
   - *Trigger*: Nightly cron (e.g., 2:00 AM).
   - *Action*: Reads `commission_ledger_entries` and `payout_rules`. Auto-generates `payout_batches`. Sends secure SMS/Email links to suppliers for pre-approval before Maker-Checker finance admin releases funds.
4. **Auto-Accrual & Reversal Engine**:
   - *Trigger*: Last day of the month (11:59 PM).
   - *Action*: Identifies unbilled expenses/uncollected revenues. Posts reversing journal entries automatically on Day 1 of the next period.
5. **Automated Tax & VAT Remittance**:
   - *Trigger*: Continuous (per transaction) + Month-end aggregation.
   - *Action*: Aggregates Output VAT (sales) and Input VAT (expenses) into `vat_remittances`. Auto-generates country-specific (KSA ZATCA / Oman FTA) CSV filing reports.
6. **Orphan Detector Cron**:
   - *Trigger*: Daily at 3:00 AM.
   - *Action*: Scans `orders` and `payouts` tables. If `status=delivered` or `paid` lacks a corresponding `journal_entry`, triggers a Critical Slack/Email alert to the Finance Command Center.

---

## 🎨 Section 4: UI/UX Architecture (Pages, Tabs & Sidebar)
*Route-driven, lazy-loaded Next.js architecture (`/admin/finance?section=...`)*

### 📊 1. Dashboard & Heartbeat (`/admin/finance/dashboard`)
* **Tabs**: Overview, Cash Position, Liabilities Exposure.
* **Components**: Real-time KPI cards (Free Cash, Locked Reserves, MTD Net Revenue, Pending Payouts), AP/AR Aging charts, Cash Flow Forecast graph (30/60/90 days).

### 📒 2. General Ledger & Chart of Accounts (`/admin/finance/ledger`)
* **Tabs**: Chart of Accounts, Journal Entries, Trial Balance, Pending Approvals.
* **Components**: Hierarchical COA tree view, Enterprise data grid for Journals (server-side paginated, filterable by date/account/reference), Maker-Checker approval modal.

### 💰 3. Accounts Receivable (AR) (`/admin/finance/ar`)
* **Tabs**: Customer Invoices, Receipts, Aging Report, Dunning Rules.
* **Components**: Invoice generation UI, payment application matching, automated late-fee configuration, bulk dunning email trigger.

### 🏢 4. Accounts Payable (AP) (`/admin/finance/ap`)
* **Tabs**: Vendor Bills, Payments, Aging Report, Expense Scanning.
* **Components**: Bill entry form, multi-level approval workflow tracker, OCR receipt upload zone, bulk payment approval.

### 🏦 5. Treasury & Banking (`/admin/finance/treasury`)
* **Tabs**: Cash Position, Bank Accounts, Reconciliation, Gateway Settlements.
* **Components**: Split-screen Bank Rec UI (Statement vs. GL), Gateway T+2/T+7 tracking table, manual treasury transfer form (Maker-Checker).

### 🤝 6. Marketplace Settlements (`/admin/finance/settlements`)
* **Tabs**: Commission Rules, Payout Batches, COD Remittance, Refunds.
* **Components**: Payout batch generator, supplier approval status tracker, COD logistics remittance matching tool, refund reconciliation queue.

### 🏛️ 7. Tax & Compliance (`/admin/finance/tax`)
* **Tabs**: VAT Configuration, VAT Remittance Reports, Withholding Tax, Fixed Assets.
* **Components**: ZATCA/FTA export generator, asset registry with depreciation schedule preview, gain/loss disposal calculator.

### ⚙️ 8. Automations & Settings (`/admin/finance/settings`)
* **Tabs**: Bank Mapping Rules, Fiscal Periods, Audit Logs, Exchange Rates.
* **Components**: AI confidence threshold slider, period close "Lock" button, append-only audit log viewer, manual FX rate updater.

---

## 🔌 Section 5: Core API Endpoints Mapping
*Secured by `require_finance_permission` middleware.*

* **Dashboard**: `GET /finance/dashboard/metrics`, `GET /finance/cash-position`, `GET /finance/liabilities/exposure`
* **Ledger**: `GET /finance/ledger` (paginated), `POST /finance/ledger/manual-adjustment` (triggers pending state)
* **Reports**: `GET /finance/reports/trial-balance`, `GET /finance/reports/vat-liability`, `GET /finance/reports/supplier-earnings`
* **Payouts**: `POST /finance/payouts/batches/generate`, `POST /finance/payouts/batches/{id}/approve` (Checker), `POST /finance/payouts/batches/{id}/dispatch`
* **Reconciliation**: `GET /finance/reconciliation/gateway-exceptions`, `POST /finance/reconciliation/cod-remittance`
* **Automation**: `POST /finance/automation/ocr-parse`, `POST /finance/automation/bank-rec-run`

---

## 🗓️ Section 6: Phased Implementation Roadmap (8-Week Execution)

### **Phase 1: Foundation & Seeding (Week 1)**
- [ ] Run Alembic migrations for all 4 Tiers of database tables.
- [ ] Execute idempotent seed script for GCC-tailored Chart of Accounts (1000-6000 series).
- [ ] Seed default Treasury Buckets and Fiscal Periods.
- [ ] Build core `TreasuryService.post_journal_entry()` with `Debit == Credit` validation and `SELECT ... FOR UPDATE` row locking.

### **Phase 2: The "Shadow Mode" Integration (Week 2-3)**
- [ ] Inject `TreasuryService` into `payments_controller`, `orders_controller`, and `payouts_controller`.
- [ ] Enable **Shadow Mode**: Engine writes Journal Entries to DB, but legacy `wallet_balance` logic still drives operational flow.
- [ ] Build nightly drift detection cron: Compare Legacy Balances vs. New Ledger Balances. Fix logic discrepancies.

### **Phase 3: The Cutover & Automation Engine (Week 4-5)**
- [ ] **Kill legacy balance updates**. System now relies 100% on the Ledger.
- [ ] Implement Gateway Settlement auto-matching (Stripe/Tap webhooks → `1020 Gateway Clearing`).
- [ ] Implement COD Remittance Engine (Logistics uploads → `1030 COD Receivable` clearance).
- [ ] Activate Auto-Accrual, Auto-Tax aggregation, and Smart Payout batch generation crons.

### **Phase 4: Finance Command Center UI (Week 6-7)**
- [ ] Build Dashboard & Cash Position views (powered by Materialized Views for <200ms load).
- [ ] Build General Ledger & AP/AR Enterprise Data Grids (with bulk actions and server-side pagination).
- [ ] Build Split-Screen Bank Reconciliation UI and Maker-Checker approval modals.
- [ ] Build VAT Remittance CSV export wizard.

### **Phase 5: Testing, Validation & Go-Live (Week 8)**
- [ ] **Chaos Monkey Test**: Simulate 1,000 concurrent checkouts + 500 payouts. Assert zero deadlocks and perfect `SUM(Dr) == SUM(Cr)`.
- [ ] **Penny Rounding Test**: Verify complex fractional commission splits (e.g., 15% comm, 3% logistics, 5% VAT) using `Decimal`/`NUMERIC`.
- [ ] **Time Travel Audit Test**: Reconstruct exact cash position for a random date 6 months in the past by replaying `journal_entries`.
- [ ] Final sign-off and production deployment.

---

## 🛡️ Section 7: Security, Compliance & Performance Matrix

### 🔐 Security & Compliance
- **Granular RBAC**: Strict role segmentation (e.g., `finance.ap.clerk` can draft, `finance.manager` can approve).
- **Maker-Checker Workflow**: No manual journal or payout batch goes live without a second, distinct user with `approve` rights.
- **Period Close Locking**: DB-level rejection of any journal entry with a `created_at` date in a `fiscal_period` marked `is_closed = true`.
- **Immutable Audit Trail**: Every action logged in `finance_audit_logs` with before/after JSON states and IP addresses.

### ⚡ Performance & Scalability
- **N+1 Query Eradication**: Mandatory `selectinload()` / `joinedload()` in all SQLAlchemy finance queries.
- **Strategic Indexing**: Composite indexes on `(country_code, created_at)`, `(status, due_date)`, and `(entity_type, entity_id)`.
- **Read/Write Separation**: Analytical queries (Balance Sheet, P&L) routed to read replicas or served from hourly-refreshed Materialized Views.
- **Frontend Optimization**: Next.js dynamic imports (`next/dynamic`) for heavy charts, Zustand caching for static COA lists, skeleton loaders for KPI cards.

---

### 🚀 Immediate Next Action for the Engineering Team:
1. **Backend Lead**: Copy **Section 1** and **Section 2** into `backend/PLAN_financial_ledger_treasury.md` and begin Phase 1 (Schema migration and CoA seeding).
2. **Frontend Lead**: Copy **Section 4** and begin scaffolding the Next.js route structure and Materialized View API contracts.
3. **QA Lead**: Copy **Section 7** and begin writing the "Chaos Monkey" and "Penny Rounding" Pytest suites.

This is the complete, exhaustive mapping. Every model, rule, page, and automation is accounted for. Let me know if you need the exact SQL Alembic migration scripts or the Python `TreasuryService` code for Phase 1.


