"""Verify A2 orphan allegations: detect inbound STATIC imports of each candidate module
across backend/ (the audit's core definition of A2: no inbound imports + not entrypoint).

Usage: python tests/verify_a2.py
"""
from __future__ import annotations
import ast
import os
import re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
SKIP_DIRS = {"__pycache__", ".git", "node_modules", "venv", "env"}

A2 = [
    "controllers/audit_controller.py",
    "controllers/catalog/admin_products_controller.py",
    "controllers/communication/invoice_controller.py",
    "controllers/communication/notifications_controller.py",
    "controllers/communication/video_controller.py",
    "controllers/expense_controller.py",
    "controllers/finance/payments_controller.py",
    "controllers/financial_controller.py",
    "controllers/hr/command_center.py",
    "controllers/operational_controller.py",
    "controllers/security/admin_auth_controller.py",
    "controllers/security/admin_permissions_controller.py",
    "controllers/supplier/supplier_document_controller.py",
    "controllers/treasury/cash_management_controller.py",
    "services/ai/ai_automation_service.py",
    "services/commerce/promotion_points_service.py",
    "services/communication/chat_admin_service.py",
    "services/core/health_service.py",
    "services/country/country_communication_service.py",
    "services/finance/gateway_auto_enable.py",
    "services/finance/invoice_service.py",
    "services/finance/je_reversal_service.py",
    "services/finance/payments_service.py",
    "services/finance/refund_posting_service.py",
    "services/orders/import_service.py",
    "services/orders/trading_service.py",
    "services/security/auth_service.py",
    "services/suppliers/suppliers_read_service.py",
    "services/support/tickets_read_service.py",
    "services/support/tickets_write_service.py",
    "services/treasury/auto_payout_scheduler.py",
    "services/treasury/command_center_background.py",
    "services/treasury/treasury_query_service.py",
    "utils/_wire_orphans.py",
    "utils/analyze_fk_detailed.py",
    "utils/analyze_fk_refs.py",
]


def module_to_importpath(relpath: str) -> str:
    p = relpath.replace("/", ".").replace("\\", ".")
    if p.endswith(".py"):
        p = p[:-3]
    if p.endswith(".__init__"):
        p = p[: -len(".__init__")]
    return p


def collect_py_files(root: str):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".py"):
                out.append(os.path.join(dp, f))
    return out


def main():
    files = collect_py_files(BACKEND)
    texts = {}
    for fp in files:
        try:
            texts[fp] = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            texts[fp] = ""

    for rel in A2:
        abspath = os.path.join(BACKEND, rel)
        if not os.path.exists(abspath):
            print(f"MISSING  {rel}")
            continue
        import_path = module_to_importpath(rel)
        mod_basename = import_path.split(".")[-1]

        hits = []
        for fp, txt in texts.items():
            if os.path.abspath(fp) == os.path.abspath(abspath):
                continue
            if re.search(r"(^|\n)\s*from\s+" + re.escape(import_path) + r"\s+import", txt) or \
               re.search(r"(^|\n)\s*import\s+" + re.escape(import_path) + r"(\s|$|\n)", txt) or \
               re.search(r"(^|\n)\s*import\s+" + re.escape(mod_basename) + r"\b", txt):
                hits.append(os.path.relpath(fp, BACKEND))

        verdict = "WIRED" if hits else "DEAD?"
        print(f"[{verdict}] {rel}")
        if hits:
            for h in hits[:6]:
                print(f"    -> {h}")


if __name__ == "__main__":
    main()
