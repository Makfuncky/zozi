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
