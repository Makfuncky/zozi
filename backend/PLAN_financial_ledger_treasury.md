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

