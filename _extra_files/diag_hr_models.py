import os, sys
os.environ.setdefault("SECRET_KEY", "diag-key")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SEED_ADMIN_PASSWORD", "diag")
os.environ.setdefault("CSRF_DISABLED", "true")

import importlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import data.models_employee_models as dm
print("data.models_employee_models OK, module:", dm.__name__)
emp1 = dm.Employee
print("data Employee module:", emp1.__module__)

try:
    import models.hr.employee_models as hm
    print("models.hr.employee_models OK (NO conflict on import)")
    emp2 = hm.Employee
    print("hr Employee module:", emp2.__module__)
except Exception as e:
    print("CONFLICT importing models.hr.employee_models:", repr(e))

# Inspect which 'hr.employees' table is in Base.metadata
from db.base import Base
t = Base.metadata.tables.get("hr.employees")
print("hr.employees in metadata:", t is not None)
if t is not None:
    idx_names = [i.name for i in t.indexes]
    print("indexes:", idx_names)
    cols = [c.name for c in t.columns]
    print("has country_code:", "country_code" in cols, "has created_at:", "created_at" in cols)
    # Which module owns this table's mapper?
    print("mapper module:", t.tables[0].__module__ if False else "n/a")
