import importlib, traceback, sys

ROUTERS = [
    "accounting", "admin_fallback", "admin_finance_creation", "admin_logistics_fallback",
    "admin_logistics_imports", "admin_supplier_trading", "automation", "country_communications",
    "finance", "imports", "public_finance_creation", "store_payments_routes",
    "supplier_supplier_upload", "system_ai_reporting", "trading", "upload",
    "logistics_logistics_status", "logistics_partner_verify",
]

for name in ROUTERS:
    try:
        importlib.import_module("routers." + name)
        print(f"OK    {name}")
    except Exception as e:
        # get the deepest, most specific error line
        lines = traceback.format_exception_only(type(e), e)
        msg = " ".join(lines).strip().replace("\n", " ")
        print(f"FAIL  {name}: {msg[:300]}")
