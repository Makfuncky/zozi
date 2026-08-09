import os, sys
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("APP_ENV","test"); os.environ.setdefault("SECRET_KEY","t")
os.environ.setdefault("SEED_ADMIN_PASSWORD","a"); os.environ.setdefault("CSRF_DISABLED","true")
from fastapi import FastAPI
from fastapi.testclient import TestClient
import routers.public_categories_access as rc
import routers.public_product_moderation_access as rm
import routers.supplier_products as rsp
import routers.admin_categories_governance as rac
import routers.admin_products_governance as rap
import routers.public_products_access as rp
app = FastAPI()
app.include_router(rc.router, prefix="/api/v1/categories")
app.include_router(rm.router, prefix="/api/v1/product-moderation")
app.include_router(rsp.router, prefix="/api/v1/supplier-products")
app.include_router(rac.router, prefix="/api/v1/admin")
app.include_router(rap.router, prefix="/api/v1/admin")
app.include_router(rp.router, prefix="/api/v1/products")
client = TestClient(app, raise_server_exceptions=True)
for name, fn in [
  ("GET /api/v1/categories", lambda: client.get("/api/v1/categories")),
  ("GET /api/v1/categories/admin/flat", lambda: client.get("/api/v1/categories/admin/flat")),
  ("GET /api/v1/product-moderation/US/product-restrictions", lambda: client.get("/api/v1/product-moderation/US/product-restrictions")),
  ("GET /api/v1/admin/categories/US", lambda: client.get("/api/v1/admin/categories/US")),
  ("GET /api/v1/products", lambda: client.get("/api/v1/products")),
  ("GET /api/v1/supplier-products", lambda: client.get("/api/v1/supplier-products")),
]:
    try:
        r = fn()
        print(f"{name} -> {r.status_code}")
    except Exception as e:
        print(f"{name} -> EXC {type(e).__name__}: {str(e)[:80]}")
