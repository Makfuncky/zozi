import sys
sys.path.insert(0, r"F:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

# admin_banners does: from routers.banners import router
# banners does: from routers.auth import get_current_user
# This is potentially a cross-module reference.
try:
    import routers.admin_banners
    print("admin_banners imported OK")
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    import routers.banners
    print("banners imported OK")
except Exception as e:
    import traceback
    traceback.print_exc()

# Also check the routers that are NOT in main.py but exist
for r in ["admin_banners", "admin_cash", "admin_commission", "admin_email", "admin_payouts", "admin_settings", "ai_image", "flash_sales", "logistics_orders", "referrals", "shipments", "supplier_analytics", "supplier_orders", "supplier_payouts", "supplier_products", "supplier_profile", "upload", "users"]:
    try:
        importlib = __import__("importlib")
        mod = importlib.import_module(f"routers.{r}")
        print(f"  OK: {r}")
    except Exception as e:
        print(f"  ERROR: {r}: {e}")

