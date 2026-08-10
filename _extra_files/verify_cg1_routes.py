"""Temporary verification: build a FastAPI app from the 7 CG1-edited geography
routers in isolation (no other routers) and assert the CG1-affected routes are
registered and FastAPI can analyse their endpoint signatures.

This avoids the pre-existing broken routers (chatbot.py / commission.py) that
crash a full `main` import, while still proving the CG1 refactor is sound.
"""
import logging
logging.disable(logging.CRITICAL)

from fastapi import FastAPI
import routers.admin_geography_payments as pay
import routers.admin_geography_orders as orders
import routers.admin_geography_populate as pop
import routers.admin_geography_configuration as cfg
import routers.admin_geography_staff as staff
import routers.admin_comms_geography as comms
import routers.admin_finance_geography as fin

app = FastAPI()
for mod in (pay, orders, pop, staff, comms, fin):
    app.include_router(mod.router)
# cfg includes auto_populate_router (empty-path route) so it mirrors the
# production mount prefix instead of an empty one.
app.include_router(cfg.router, prefix="/admin/countries")

paths = sorted({getattr(r, "path", "") for r in app.routes})
print("TOTAL ROUTES:", len(paths))

checks = [
    "/admin/countries/{code}/payout-rules/categories",
    "/admin/countries/{code}/payout-rules/products",
    "/session/{customer_id}",
    "/admin/countries/{code}/feature-flags",
    "/{code}/cities",
    "/countries/{code}/commission-rates",
    "/countries/{code}/staff",
    "/campaigns/{country_code}",
    "/{country_code}/rates",
    "/{country_code}/badge-tiers",
]
missing = [c for c in checks if not any(c in p for p in paths)]
print("MISSING CG1 ROUTES:", missing if missing else "NONE")
assert not missing, "Some CG1-affected routes are missing/undeployable"
print("ALL CG1 GEOGRAPHY ROUTES BUILD OK")
