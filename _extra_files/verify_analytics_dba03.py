"""Verify analytics DBA03 model changes: no mapper conflict, columns present, migration imports."""
import sys, traceback
sys.path.insert(0, ".")

ok = True

# 1) import changed model modules + force mapper configuration (surfaces clashes)
try:
    from sqlalchemy.orm import configure_mappers
    from models.analytics.analytics import (
        DailySalesSnapshot, MonthlySalesSnapshot, KPICustomer, KPISupplier,
        KPICountry, KPIRevenue, KPIOrders, KPIRetention, KPIConversion,
        CashPositionSnapshotMV, FacetCountsSnapshot,
    )
    from models.logistics.admin import AdminAnalyticsSnapshot
    from models.catalog.products import VideoAnalytics
    configure_mappers()
    print("MAPPERS_CONFIGURE: ok (no duplicate-column conflict)")
except Exception as e:
    ok = False
    print("MAPPERS_CONFIGURE: FAIL", repr(e))
    traceback.print_exc()

# 2) confirm new columns are registered on the ORM models
def cols(model):
    return {c.name for c in model.__table__.columns}

checks = {
    "DailySalesSnapshot": {"created_by", "updated_by", "is_deleted"} <= cols(DailySalesSnapshot),
    "AdminAnalyticsSnapshot": {"created_at", "updated_at", "created_by", "updated_by", "is_deleted"} <= cols(AdminAnalyticsSnapshot),
    "VideoAnalytics": {"updated_at", "created_by", "updated_by", "is_deleted"} <= cols(VideoAnalytics),
}
for name, passed in checks.items():
    print(f"COLUMNS[{name}]: {'ok' if passed else 'MISSING'}")
    if not passed:
        ok = False

# 3) migration module imports (parse + import)
try:
    import importlib.util
    path = "alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py"
    spec = importlib.util.spec_from_file_location("m_20260806_0001", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.revision == "20260806_0001"
    assert m.down_revision == "20260805_0001"
    print("MIGRATION_IMPORT: ok (rev=%s down=%s)" % (m.revision, m.down_revision))
except Exception as e:
    ok = False
    print("MIGRATION_IMPORT: FAIL", repr(e))
    traceback.print_exc()

print("RESULT:", "ALL_OK" if ok else "HAS_FAILURES")
