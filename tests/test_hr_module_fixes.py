"""Regression tests for the HR / Employees module fixes.

Verifies:
  1. DB31 fix - composite (country_code, created_at) indexes exist on
     `hr.employees` and `hr.employee_addresses` (tenant time-series queries).
  2. OB101 fix - HR service modules carry a structured logger
     (`logging.getLogger(__name__)`).

Run:  python tests/test_hr_module_fixes.py
"""
import os
import sys
import glob

ZOZI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ZOZI, "backend")
sys.path.insert(0, BACKEND)

os.environ.setdefault("SECRET_KEY", "test-key")
os.environ["APP_ENV"] = "test"
os.environ["CSRF_DISABLED"] = "true"


def _load_metadata():
    import data.models_employee_models  # noqa: F401  (populates Base.metadata)
    from db.base import Base
    return Base.metadata


def test_hr_composite_indexes():
    md = _load_metadata()
    expected = {
        "hr.employees": "ix_employees_country_code_created_at",
        "hr.employee_addresses": "ix_employee_addresses_country_code_created_at",
    }
    for table, idx in expected.items():
        t = md.tables.get(table)
        assert t is not None, f"table {table} missing from metadata"
        names = {i.name for i in t.indexes}
        assert idx in names, f"{table} missing composite index {idx}; have {names}"


def test_hr_service_modules_have_logger():
    hr_dir = os.path.join(BACKEND, "services", "hr")
    files = [
        p for p in glob.glob(os.path.join(hr_dir, "*.py"))
        if os.path.basename(p) != "__init__.py"
    ]
    assert files, "no HR service modules found"
    missing = []
    for path in files:
        with open(path, "r", encoding="utf-8") as fh:
            if "getLogger" not in fh.read():
                missing.append(os.path.basename(path))
    assert not missing, f"HR service modules missing structured logger: {missing}"


if __name__ == "__main__":
    import traceback
    failures = 0
    for fn in (test_hr_composite_indexes, test_hr_service_modules_have_logger):
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"FAIL {fn.__name__}: {e}")
            traceback.print_exc()
    sys.exit(1 if failures else 0)
