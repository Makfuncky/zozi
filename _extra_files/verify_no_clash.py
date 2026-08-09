"""Confirm no duplicate 'version' column on the 13 changed tables (clash guard)."""
import sys
sys.path.insert(0, ".")
from models.analytics.analytics import (
    DailySalesSnapshot, MonthlySalesSnapshot, KPICustomer, KPISupplier,
    KPICountry, KPIRevenue, KPIOrders, KPIRetention, KPIConversion,
    CashPositionSnapshotMV, FacetCountsSnapshot,
)
from models.logistics.admin import AdminAnalyticsSnapshot
from models.catalog.products import VideoAnalytics

models = [DailySalesSnapshot, MonthlySalesSnapshot, KPICustomer, KPISupplier,
          KPICountry, KPIRevenue, KPIOrders, KPIRetention, KPIConversion,
          CashPositionSnapshotMV, FacetCountsSnapshot, AdminAnalyticsSnapshot, VideoAnalytics]

all_ok = True
for m in models:
    names = [c.name for c in m.__table__.columns]
    vcount = names.count("version")
    status = "ok" if vcount == 1 else "BAD(%d)" % vcount
    if vcount != 1:
        all_ok = False
    print(f"{m.__tablename__:24s} version_cols={vcount} {status}")
print("RESULT:", "NO_CLASH" if all_ok else "CLASH_DETECTED")
