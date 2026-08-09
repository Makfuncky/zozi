import os, sys
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("APP_ENV","test"); os.environ.setdefault("SECRET_KEY","t")
os.environ.setdefault("SEED_ADMIN_PASSWORD","a"); os.environ.setdefault("CSRF_DISABLED","true")
from fastapi.testclient import TestClient
import main
client = TestClient(main.app, raise_server_exceptions=True)
tests = [
 ("GET /api/v1/categories", client.get("/api/v1/categories")),
 ("GET /api/v1/categories/admin/flat", client.get("/api/v1/categories/admin/flat")),
 ("GET /api/v1/product-moderation/US/product-restrictions", client.get("/api/v1/product-moderation/US/product-restrictions")),
 ("GET /api/v1/admin/categories/US", client.get("/api/v1/admin/categories/US")),
 ("GET /api/v1/products", client.get("/api/v1/products")),
 ("GET /api/v1/supplier-products", client.get("/api/v1/supplier-products")),
 ("GET /api/v1/admin/products/US", client.get("/api/v1/admin/products/US")),
]
for name, r in tests:
    print(f"{name} -> {r.status_code}")
