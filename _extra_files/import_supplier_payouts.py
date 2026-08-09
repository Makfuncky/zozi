import sys, importlib
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
m = importlib.import_module("routers.supplier_payouts")
print("router OK ->", [r.path for r in m.router.routes])
importlib.import_module("services.supplier.supplier_payout_service")
print("service OK")
