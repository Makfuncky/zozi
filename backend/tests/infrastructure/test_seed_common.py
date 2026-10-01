"""Tests for backend/infrastructure/database/seed/_common.py.

Verifies:
  1. No FastAPI imports in the seed common module (TECHNOLOGY_STACK.md
     compliance — infrastructure layer must not depend on FastAPI).
  2. _common.py is acknowledged as a sanctioned DB seeder in the import-laws
     scanner EXCLUDE_PATHS (ARCH-008 / Law 1 compliance).
"""
from __future__ import annotations

import ast
import os
import sys

_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

_COMMON_PATH = os.path.join(_BACKEND_ROOT, "infrastructure", "database", "seed", "_common.py")


class TestSeedCommonTechnologicalCompliance:
    """Technological checks for _common.py."""

    def test_no_fastapi_imports_in_common(self):
        """_common.py must not import from FastAPI (infrastructure layer rule)."""
        with open(_COMMON_PATH, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=_COMMON_PATH)
        fastapi_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and "fastapi" in node.module
        ]
        assert not fastapi_imports, (
            "infrastructure/database/seed/_common.py must not import from FastAPI. "
            "Found: " + ", ".join(ast.unparse(n) for n in fastapi_imports)
        )


class TestSeedCommonArchitecturalCompliance:
    """Architectural checks for _common.py (ARCH-008)."""

    def test_common_in_import_laws_exclude_paths(self):
        """_common.py must be in the import-laws scanner EXCLUDE_PATHS as a
        sanctioned DB seeder (same category as seed_data.py)."""
        from scripts._gen_import_laws_baseline import EXCLUDE_PATHS

        assert "infrastructure/database/seed/_common.py" in EXCLUDE_PATHS, (
            "infrastructure/database/seed/_common.py is a sanctioned DB seeder "
            "and must be in EXCLUDE_PATHS (same category as "
            "infrastructure/database/seed_data.py)."
        )
