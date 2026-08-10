import sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

# 1) A hollow router health endpoint
r = client.get("/api/v1/chatbot/core_chatbot_routes/health")
print("chatbot health:", r.status_code, r.json())

# 2) promotions router health
r = client.get("/api/v1/admin/promotions/admin_promotions_routes/health")
print("promotions health:", r.status_code, r.json())

# 3) country_router route registration (mounted under /admin)
paths = [getattr(rt, "path", "") for rt in main.app.routes]
country_paths = [p for p in paths if p.startswith("/admin/") and "coupons" in p or p.startswith("/admin/") and "banners" in p]
print("country routes present:", any(p.startswith("/admin/{code}/coupons") for p in paths),
      any(p.startswith("/admin/{code}/banners") for p in paths))

# 4) ensure core_auth get_current_user resolves (import path used by cross routers)
try:
    from routers.core_auth_routes import get_current_user
    print("get_current_user re-export: OK", callable(get_current_user))
except Exception as e:
    print("get_current_user re-export: FAIL", repr(e))
