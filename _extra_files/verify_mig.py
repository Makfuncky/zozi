import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
# compile-check the migration module
import py_compile
py_compile.compile("backend/alembic/versions/2026_08_06_0005-dba03_version_column_backfill.py", doraise=True)
print("migration compiles OK")
import models
print("models import OK, tables=", len(models.Base.metadata.tables))
