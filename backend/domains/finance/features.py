"""finance domain — feature atoms (AXIS 3).

Per ARCHITECTURE_DIAGRAM.md §3 and §7, every feature gate used by a module
router's ``require_feature(...)`` call MUST be single-sourced here. The RBAC
catalog (``rbac/catalog.py``) aggregates these via package scan.
"""
from __future__ import annotations

FEATURES: dict[str, str] = {
    # ── Ledger / journal ───────────────────────────────────────────────────────
    "finance.ledger.read": "View general ledger entries and chart of accounts",
    "finance.ledger.write": "Create and post journal entries",
    "finance.ledger.post": "Create and post journal entries",
    "finance.ledger.reverse": "Reverse posted journal entries",
    # ── Invoices ──────────────────────────────────────────────────────────────
    "finance.invoice.read": "View invoices",
    "finance.invoice.create": "Create invoices",
    # ── Payouts ───────────────────────────────────────────────────────────────
    "finance.payout.read": "View payouts and payout batches",
    "finance.payout.write": "Create and manage payouts",
    "finance.payout.create": "Create payouts",
    "finance.payout.approve": "Approve payouts (maker-checker)",
    "finance.payout.dispatch": "Dispatch approved payout batches",
    # ── Commissions ───────────────────────────────────────────────────────────
    "finance.commission.read": "View commission structures and ledger",
    "finance.commission.write": "Manage commission rates and agreements",
    "finance.commission.manage": "Manage commission rates and agreements",
    # ── Treasury / cash management ────────────────────────────────────────────
    "finance.treasury.read": "View treasury accounts and cash positions",
    "finance.treasury.manage": "Manage treasury accounts and transfers",
    "finance.treasury.forecast": "Run cash-flow forecasts",
    # ── Period close ──────────────────────────────────────────────────────────
    "finance.period.close": "Close fiscal periods",
    "finance.period.manage": "Manage fiscal periods",
    # ── Reporting ──────────────────────────────────────────────────────────────
    "finance.reporting.read": "View financial reports",
    "finance.reporting.generate": "Generate financial reports",
    # ── ERP / sub-ledger ──────────────────────────────────────────────────────
    "finance.subledger.read": "View AR/AP sub-ledger",
    "finance.subledger.post": "Post AR/AP entries",
    "finance.erp.read": "View ERP documents (PO, GRN, sales orders)",
    "finance.erp.manage": "Manage ERP documents",
    # ── Bank / reconciliation ─────────────────────────────────────────────────
    "finance.bank.read": "View bank transactions and statements",
    "finance.bank.write": "Manage bank account details",
    "finance.bank.reconcile": "Reconcile bank statements",
    "finance.bank.mapping": "Manage bank statement mapping rules",
    # ── Credit control ────────────────────────────────────────────────────────
    "finance.credit.read": "View credit control data",
    "finance.credit.manage": "Manage customer credit",
    # ── Automation ─────────────────────────────────────────────────────────────
    "finance.automation.read": "View automation rules and logs",
    "finance.automation.manage": "Manage finance automation rules",
    # ── Audit ─────────────────────────────────────────────────────────────────
    "finance.audit.read": "View finance audit logs",
    # ── Invoices (plural form, legacy alias) ───────────────────────────────────
    "finance.invoices.read": "View invoices and billing records",
    "finance.invoices.manage": "Create, update, and manage invoices and billing records",
    # ── Payments ──────────────────────────────────────────────────────────────
    "finance.payments.read": "View payment transactions and history",
    "finance.payments.process": "Process payment transactions and refunds through gateways",
    # ── Payouts (plural form, legacy alias) ────────────────────────────────────
    "finance.payouts.read": "View supplier and partner payout records",
    "finance.payouts.manage": "Initiate, approve, and manage payouts to suppliers and partners",
    # ── Commissions (plural form, legacy alias) ───────────────────────────────
    "finance.commissions.read": "View commission calculations and agreements",
    "finance.commissions.manage": "Configure commission rates and manage commission agreements",
    # ── General Ledger ────────────────────────────────────────────────────────
    "finance.general_ledger.read": "View general ledger entries and accounting records",
    # ── Bank reconciliation ────────────────────────────────────────────────────
    "finance.bank_reconciliation": "Perform bank reconciliation and match transactions",
}
