"""Test that each A2 candidate module imports cleanly (no import-time errors).
This guards the wiring step: a module that raises on import must not be force-imported at startup."""
from __future__ import annotations
import importlib
import os
import sys
import traceback

BACKEND = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
sys.path.insert(0, BACKEND)

A2 = [
    "controllers.audit_controller",
    "controllers.catalog.admin_products_controller",
    "controllers.communication.invoice_controller",
    "controllers.communication.notifications_controller",
    "controllers.communication.video_controller",
    "controllers.expense_controller",
    "controllers.finance.payments_controller",
    "controllers.financial_controller",
    "controllers.hr.command_center",
    "controllers.operational_controller",
    "controllers.security.admin_auth_controller",
    "controllers.security.admin_permissions_controller",
    "controllers.supplier.supplier_document_controller",
    "controllers.treasury.cash_management_controller",
    "services.ai.ai_automation_service",
    "services.commerce.promotion_points_service",
    "services.communication.chat_admin_service",
    "services.core.health_service",
    "services.country.country_communication_service",
    "services.finance.gateway_auto_enable",
    "services.finance.invoice_service",
    "services.finance.je_reversal_service",
    "services.finance.payments_service",
    "services.finance.refund_posting_service",
    "services.orders.import_service",
    "services.orders.trading_service",
    "services.security.auth_service",
    "services.suppliers.suppliers_read_service",
    "services.support.tickets_read_service",
    "services.support.tickets_write_service",
    "services.treasury.auto_payout_scheduler",
    "services.treasury.command_center_background",
    "services.treasury.treasury_query_service",
    "utils._wire_orphans",
    "utils.analyze_fk_detailed",
    "utils.analyze_fk_refs",
]


def main():
    ok, bad = [], []
    for mod in A2:
        try:
            importlib.import_module(mod)
            ok.append(mod)
        except Exception as e:
            bad.append((mod, repr(e)))
    print(f"IMPORTABLE ({len(ok)}):")
    for m in ok:
        print(f"  OK  {m}")
    print(f"\nFAILED ({len(bad)}):")
    for m, e in bad:
        print(f"  FAIL {m}: {e}")


if __name__ == "__main__":
    main()
