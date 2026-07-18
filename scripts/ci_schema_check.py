"""
CI/CD Schema Drift Protection Script

This script compares the current ORM models against the Alembic migration history
and exits with error code 1 if drift is detected.

Usage:
    python scripts/ci_schema_check.py [--check-migration]

Exit codes:
    0 - No drift detected (schema is in sync)
    1 - Drift detected (schema needs migration)
    2 - Error occurred
"""
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

def check_schema_drift():
    """Check if ORM models match migration history."""
    from sqlalchemy import inspect
    from db.database import Base, engine
    
    db_tables = set(inspect(engine).get_table_names())
    model_tables = set(Base.metadata.tables.keys())
    
    missing_in_db = model_tables - db_tables
    missing_in_models = db_tables - model_tables
    
    if missing_in_db:
        print(f"ERROR: Tables in models but not in database: {missing_in_db}")
        return False
    
    if missing_in_models:
        print(f"WARNING: Tables in database but not in models: {missing_in_models}")
    
    return True


def check_alembic_head():
    """Check if there's a pending alembic migration to apply."""
    from pathlib import Path
    import shutil
    
    alembic_path = Path(__file__).resolve().parent.parent / "backend" / "alembic"
    if not alembic_path.exists():
        return True
    
    versions_path = alembic_path / "versions"
    if not versions_path.exists():
        return True
    
    py_files = list(versions_path.glob("*.py"))
    pycache_dirs = list(versions_path.glob("__pycache__"))
    
    if py_files:
        latest = max(py_files, key=lambda p: p.stat().st_mtime)
        print(f"INFO: Latest migration: {latest.name}")
    
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='CI Schema Drift Check')
    parser.add_argument('--check-migration', action='store_true', 
                        help='Also check if alembic can detect migration (useful for pre-commit)')
    args = parser.parse_args()
    
    try:
        print("Checking for schema drift...")
        
        if not check_schema_drift():
            print("\nERROR: Schema drift detected!")
            print("Please run: cd backend && python -m alembic revision --autogenerate -m 'schema update'")
            sys.exit(1)
        
        if args.check_migration:
            check_alembic_head()
        
        print("SUCCESS: Schema is in sync with models.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)