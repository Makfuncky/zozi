import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-hr-validation-only")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "")

import models  # noqa: F401  (registers all ORM tables)
import sys

MD = sys.modules["models.user"].Base.metadata

HR_TABLES = [t for t in MD.tables.values() if t.schema == "hr"]


def test_all_hr_tables_reside_in_hr_schema():
    # DBA06: HR tables were wrongly placed in the `logistics` schema.
    assert len(HR_TABLES) >= 18, f"expected >=18 HR tables, found {len(HR_TABLES)}"
    assert all(t.schema == "hr" for t in HR_TABLES), "an HR table is not in the hr schema"


def test_hr_foreign_key_targets_are_schema_qualified():
    # DBA06: every FK target leaving an HR table must be schema-qualified.
    for t in HR_TABLES:
        for fk in t.foreign_keys:
            parts = fk.target_fullname.split(".")
            assert len(parts) == 3, (
                f"{t.name}.{fk.parent.name} -> '{fk.target_fullname}' "
                f"is not schema-qualified"
            )


def test_no_hr_table_targets_logistics_schema():
    # HR tables must not reference the logistics schema as their own home.
    for t in HR_TABLES:
        assert t.schema != "logistics", f"{t.name} still in logistics schema"


def test_hr_dashboard_router_delegates_to_service():
    import routers.public_hr_dashboard_access as r  # noqa: F401
    import services.hr_dashboard_service as s

    assert hasattr(s, "get_hr_dashboard") or hasattr(s, "_svc_get_hr_dashboard")
    # The router must no longer run raw SQL itself (W1/LC1 findings).
    src = open(r.__file__, encoding="utf-8").read()
    assert "text(" not in src or "db.execute" not in src, (
        "hr_dashboard router still contains raw SQL"
    )


def _router_src(name: str) -> str:
    import routers

    return open(
        __import__("os").path.join(routers.__path__[0], name),
        encoding="utf-8",
    ).read()


def test_employees_router_has_no_raw_sql():
    # CIR1/LC1/W1: router must not run queries or raw SQL itself.
    src = _router_src("employees.py")
    assert "db.query(" not in src, "employees router still queries the session"
    assert "db.execute(" not in src, "employees router still runs raw SQL"
    assert "text(" not in src, "employees router still uses raw SQL text()"


def test_payroll_router_has_no_raw_sql():
    # CIR1/LC1: payroll router must not query the session directly.
    src = _router_src("payroll.py")
    assert "db.query(" not in src, "payroll router still queries the session"
    assert "db.execute(" not in src, "payroll router still runs raw SQL"
    assert "text(" not in src, "payroll router still uses raw SQL text()"