import os, sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
import models
from models.catalog.products import Category
names = [c.name for c in Category.__table__.columns]
from collections import Counter
dup = [n for n, k in Counter(names).items() if k > 1]
print("total cols:", len(names))
print("duplicates:", dup)
print("has created_by:", "created_by" in names, "| has updated_by:", "updated_by" in names,
      "| has is_deleted:", "is_deleted" in names, "| has version:", "version" in names)
assert not dup, "DUPLICATE COLUMNS: " + str(dup)
for need in ("uuid","country_code","version","is_active","created_at","updated_at",
             "created_by","updated_by","is_deleted","deleted_at","deleted_by","delete_reason"):
    assert need in names, f"MISSING {need}"
print("Category pilot OK: 12 DBA03 columns, no duplicates")
