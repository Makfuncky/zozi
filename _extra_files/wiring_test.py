"""Functional wiring smoke test via TestClient."""
import os

os.environ.setdefault("FIELD_ENCRYPTION_KEY", "test-key-1234567890abcdef")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-wiring-test")

import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

# 1. Core health
r = client.get("/health")
print("health", r.status_code)

# 2. The 5 previously-broken routers must have mounted routes.
expected_prefixes = [
    "/api/v1/admin/geography/config",
    "/api/v1/admin/treasury/payments",
    "/api/v1/customer/coupons",
    "/api/v1/public/geography/config",
    "/api/v1/country/communications",
    "/admin",  # country_router mount
]
paths = {getattr(rt, "path", None) for rt in main.app.routes}
for p in expected_prefixes:
    hits = [x for x in paths if x and x.startswith(p)]
    print("PREFIX", p, "routes:", len(hits))

# 3. Smoke test every /status endpoint (hollow-filled routers).
status_paths = sorted({x for x in paths if x and x.endswith("/status")})
print("STATUS_ENDPOINTS", len(status_paths))
bad = []
for p in status_paths:
    try:
        rr = client.get(p)
        if rr.status_code >= 500:
            bad.append((p, rr.status_code))
    except Exception as e:  # noqa: BLE001
        bad.append((p, str(e)[:80]))
print("STATUS_5XX", len(bad))
for p, code in bad[:30]:
    print("BAD", p, code)
