"""A2 verification step 2 (pure-python): for each candidate module, check whether ANY of
its public top-level symbols are referenced (by name) anywhere else in backend/."""
from __future__ import annotations
import ast
import os
import re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
SKIP_DIRS = {"__pycache__", ".git", "node_modules", "venv", "env"}
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

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


def extract_symbols(filepath: str):
    names = set()
    try:
        tree = ast.parse(open(filepath, encoding="utf-8").read())
    except Exception:
        return names
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


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
    file_tokens = {}
    for fp in files:
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        file_tokens[fp] = set(IDENT_RE.findall(txt))

    for rel in A2:
        abspath = os.path.join(BACKEND, rel)
        if not os.path.exists(abspath):
            print(f"MISSING  {rel}")
            continue
        symbols = extract_symbols(abspath)
        if not symbols:
            print(f"[NO-SYMBOLS] {rel}")
            continue
        used_in = []
        for fp, toks in file_tokens.items():
            if os.path.abspath(fp) == os.path.abspath(abspath):
                continue
            if symbols & toks:
                used_in.append(os.path.relpath(fp, BACKEND))
        if used_in:
            print(f"[USED] {rel}")
            for f in used_in[:6]:
                print(f"    -> {f}")
        else:
            print(f"[DEAD] {rel}")


if __name__ == "__main__":
    main()
