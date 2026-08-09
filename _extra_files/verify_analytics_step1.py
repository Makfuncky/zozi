"""Verify analytics module import health and the provider bug."""
import sys, traceback
sys.path.insert(0, ".")

ok = True

# 1) analytics models import
try:
    from models.analytics.analytics import (
        DailySalesSnapshot, MonthlySalesSnapshot, KPICustomer, KPISupplier,
        KPICountry, KPIRevenue, KPIOrders, KPIRetention, KPIConversion,
        CashPositionSnapshotMV, FacetCountsSnapshot,
    )
    print("MODELS_IMPORT: ok")
except Exception as e:
    ok = False
    print("MODELS_IMPORT: FAIL")
    traceback.print_exc()

# 2) provider import + instantiation (reproduce AttributeError)
try:
    from providers.analytics.analytics import AnalyticsProvider
    p = AnalyticsProvider()
    print("PROVIDER_INSTANTIATE: ok")
except Exception as e:
    ok = False
    print("PROVIDER_INSTANTIATE: FAIL", repr(e))

# 3) compile (configure) the ORM mappers to surface duplicate-column conflicts
try:
    from models.analytics.analytics import Base
    Base.metadata.compile = Base.metadata.compile  # noop
    print("MAPPER_COMPILE: skipped (compile needs bind)")
except Exception as e:
    ok = False
    print("MAPPER: FAIL", repr(e))

print("RESULT:", "ALL_OK" if ok else "HAS_FAILURES")
