import os, sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base
from models.mixins import StandardMixin, TenantMixin, AuditMixin, SoftDeleteMixin

B = declarative_base()
class Foo(B, StandardMixin):
    __tablename__ = "_validation_foo"
    id = Column(Integer, primary_key=True)

cols = sorted(c.name for c in Foo.__table__.columns)
print("columns:", cols)
assert cols.count("version") == 1, "version must appear exactly once"
for need in ("created_at","updated_at","created_by","updated_by",
             "is_deleted","deleted_at","deleted_by","delete_reason",
             "uuid","country_code","is_active","version"):
    assert need in cols, f"missing {need}"
print("StandardMixin OK: 12 expected columns, version unique")
