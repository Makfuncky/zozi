import sys, os, importlib.util
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
sys.path.insert(0, os.path.join(os.getcwd(), "backend", "alembic"))
spec = importlib.util.spec_from_file_location("rev_0005", "backend/alembic/versions/2026_08_06_0005-dba03_version_column_backfill.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("module imports OK")
print("'models' imported at load?", "models" in sys.modules)
print("revision:", mod.revision, "down_revision:", mod.down_revision)
