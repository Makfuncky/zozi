import os, sys
sys.path.insert(0, os.path.abspath("backend"))
os.environ.setdefault("APP_ENV","test"); os.environ.setdefault("SECRET_KEY","t")
os.environ.setdefault("SEED_ADMIN_PASSWORD","a"); os.environ.setdefault("CSRF_DISABLED","true")
from fastapi.testclient import TestClient
import main
client = TestClient(main.app, raise_server_exceptions=True)
# categories list (public)
r = client.get("/api/categories")
print("GET /api/categories ->", r.status_code, "| rm:", r.request is not None)
# product moderation restrictions
r2 = client.get("/api/US/product-restrictions")
print("GET /api/US/product-restrictions ->", r2.status_code)
# admin categories list requires auth
r3 = client.get("/api/admin/categories/US")
print("GET admin categories ->", r3.status_code, "(expect 401/403)")
