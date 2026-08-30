"""payments domain — feature atoms (AXIS 3).

Per ARCHITECTURE_DIAGRAM.md §3 and §7, every feature gate used by a module
router's ``require_feature(...)`` call MUST be single-sourced here. The RBAC
catalog (``rbac/catalog.py``) aggregates these via package scan.
"""
from __future__ import annotations

FEATURES: dict[str, str] = {
    # ── Payment transactions ──────────────────────────────────────────────────
    "payments.transaction.read": "View payment transactions and history",
    "payments.transaction.process": "Process payments and refunds through gateways",
    "payments.transaction.refund": "Issue refunds to customers",
    # ── Gateways / providers ──────────────────────────────────────────────────
    "payments.gateway.read": "View configured payment gateways",
    "payments.gateway.manage": "Configure payment gateways and credentials",
    # ── Payouts ───────────────────────────────────────────────────────────────
    "payments.payout.read": "View payouts and payout batches",
    "payments.payout.approve": "Approve payouts (maker-checker)",
}
