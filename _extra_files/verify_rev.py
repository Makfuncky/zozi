import sys, os, py_compile
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
py_compile.compile("backend/alembic/versions/2026_08_06_0005-dba03_version_column_backfill.py", doraise=True)
print("compiles OK")
# Simulate the audit's isolated import: import the module, models must NOT be imported at module load
import importlib.util
spec = importlib.util.spec_from_file_location("rev_0005", "backend/alembic/versions/2026_08_06_0005-dba03_version_column_backfill.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("module imports OK; top-level names:", [n for n in ("revision","down_revision") if hasattr(mod,n)])
print("'models' imported at load?", "models" in sys.modules)
