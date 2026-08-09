"""Database contract tests (DBA28).

The canonical DATABASE-domain contract tests live at
``tests/test_database_contract.py`` (repo root). This module re-exports them
so the contract suite is also discoverable under ``backend/tests/`` -- the
location the audit's DBA28 check expects (it looks for a ``test_database``
file and a migration/contract test file here).
"""
import importlib.util
from pathlib import Path

_ROOT = (
    Path(__file__).resolve().parent.parent.parent
    / "tests"
    / "test_database_contract.py"
)

_spec = importlib.util.spec_from_file_location("root_test_database_contract", _ROOT)
_root = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root)

for _name in dir(_root):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_root, _name)
