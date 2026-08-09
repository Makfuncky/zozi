import os, sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic")
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
import migration_helpers as mh
print("migration_helpers OK; safe_add_column callable:", callable(mh.safe_add_column))
import importlib.util
spec = importlib.util.spec_from_file_location("m20260806_0004", r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions\2026_08_06_0004-catalog_categories_dba03_audit_softdelete.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("migration module OK; revision:", mod.revision, "down_revision:", mod.down_revision)
