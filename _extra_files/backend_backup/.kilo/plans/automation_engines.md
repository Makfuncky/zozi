# Automation Engines Implementation Plan

## Audit Summary

The current codebase has ~27 automation-related modules across `backend/services/finance/`, `backend/finance/`, and `backend/routers/finance/`. The blueprint specifies 28 automation engines. The audit identified 15 missing or incomplete engines.

## Missing Automation Engines

### E-Commerce (6 missing)
1. **Refund Automation** — Auto-process refunds: create credit notes, GL entries, update order status
2. **Gateway 3-Way Reconciliation** — Reconcile gateway transactions with bank statements and orders
3. **Auto Dunning Automation** — Automated collection dunning with escalation tiers
4. **Subscription Billing Automation** — Recurring subscription billing with proration
5. **Price Change Automation** — Handle price changes in pending/active orders
6. **Inventory Reconciliation Automation** — Reconcile inventory counts with GL

### Trading (4 missing)
7. **PO/GRN/3-Way Match** — Match purchase orders with goods receipts and invoices
8. **Trading P&L Automation** — Calculate trading profit/loss per position
9. **Trading Risk Automation** — Risk monitoring and limit checks for trading positions
10. **Trading Settlement Automation** — Automate trading settlement and confirmation

### Imports & Distribution (6 missing)
11. **Landed Cost Automation** — Calculate landed costs for imported goods
12. **Import Duty Automation** — Automate import duty calculations and filings
13. **Warehouse Receipt Automation** — Process warehouse receipts and put-away
14. **Distribution Order Automation** — Process distribution orders to retailers
15. **Distribution Billing Automation** — Bill distribution orders to retailers
16. **Distribution Reconciliation Automation** — Reconcile distribution transactions

### Finance (4 missing)
17. **Automated Period Close** — Automate fiscal period closing (partially exists)
18. **Automated Financial Reporting** — Scheduled report generation and delivery
19. **Multi-Currency Transaction Automation** — Automate multi-currency FX transactions
20. **Intercompany Automation** — Automate intercompany transactions and eliminations

## Implementation Order

### Batch 1 (E-Commerce — highest business impact)
1. Refund Automation
2. Gateway 3-Way Reconciliation
3. Auto Dunning Automation

### Batch 2 (Trading & Imports)
4. PO/GRN/3-Way Match
5. Landed Cost Automation
6. Import Duty Automation

### Batch 3 (Finance & Distribution)
7. Automated Period Close (enhance existing)
8. Multi-Currency Transaction Automation
9. Intercompany Automation

### Batch 4 (Remaining)
10. Subscription Billing Automation
11. Price Change Automation
12. Inventory Reconciliation Automation
13. Distribution Order/Billing/Reconciliation
14. Trading P&L/Risk/Settlement
15. Automated Financial Reporting

## Implementation Pattern

Each engine follows the existing 4-layer pattern:
1. **Model** (if new DB table needed) — `backend/models/finance.py` or new model file
2. **Service** — `backend/services/finance/<engine>_service.py`
3. **Facade** — `backend/finance/<engine>.py`
4. **Controller** — `backend/controllers/finance/<engine>_controller.py`
5. **Router** — `backend/routers/finance/<engine>.py`
6. **Registration** — Update `__init__.py` files at each layer
7. **Orchestrator** — Add to `finance_automation_orchestrator.py`

## Key Dependencies

- All GL writes go through `general_ledger_service.create_journal_entry`
- All facades use `from services.finance import <module>` pattern
- All routers use `from finance import <module>` pattern
- The orchestrator composes all automation steps with per-step error isolation