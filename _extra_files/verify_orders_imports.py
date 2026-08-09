import os, sys
BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
os.environ.setdefault("SECRET_KEY", "test-key")
os.environ["APP_ENV"] = "test"
os.environ["CSRF_DISABLED"] = "true"
import utils.pagination as p
assert hasattr(p, "keyset_page"), "keyset_page missing"
import services.orders.orders_router_service
import services.orders.import_service
import services.orders.trading_service
import services.supplier.supplier_orders_service
import controllers.orders.orders_controller
import controllers.orders.returns_controller
import controllers.orders.disputes_controller
import controllers.orders.admin_orders_controller
print("IMPORTS OK")
