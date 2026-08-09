import os, sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
import models
from models.catalog.products import Category
from sqlalchemy import create_engine, inspect
eng = create_engine("sqlite:///:memory:")
models.Base.metadata.create_all(eng)
insp = inspect(eng)
cols = [c["name"] for c in insp.get_columns("categories", schema="commerce")]
print("categories columns:", sorted(cols))
# verify no duplicates and required DBA03 columns present
for need in ("uuid","country_code","version","is_active","created_at","updated_at",
             "created_by","updated_by","is_deleted","deleted_at","deleted_by","delete_reason"):
    assert need in cols, f"MISSING {need}"
print("DBA03 columns present; no duplicate error -> Category pilot OK")
