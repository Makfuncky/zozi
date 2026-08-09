import ast
from pathlib import Path

B = Path("backend")
need = ['add_and_flush','add_notification','add_to_session','commit_only','create_payout',
'create_shipment','create_shipment_event','create_supplier_bank_account','create_supplier_document',
'create_supplier_profile','create_supplier_settlement','delete_payout','delete_shipment',
'delete_shipment_event','delete_supplier_bank_account','delete_supplier_document',
'delete_supplier_profile','delete_supplier_settlement','flush_session','refresh_model',
'update_payout','update_shipment','update_shipment_event','update_supplier_bank_account',
'update_supplier_document','update_supplier_profile','update_supplier_settlement']

defs = {s: [] for s in need}
files = [p for p in B.rglob("*.py") if "venv" not in str(p) and "__pycache__" not in str(p)]
for p in files:
    try:
        t = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        continue
    rel = p.relative_to(B).as_posix()
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in need:
            defs[n.name].append(f"{rel}:{n.lineno}")

for s in need:
    print(f"{s:32s} -> {defs[s][:4]}")
