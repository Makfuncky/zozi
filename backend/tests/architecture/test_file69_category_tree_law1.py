"""FILE-069 regression tests for backend/infrastructure/utils/category_tree.py.

Verifies that the Law 1 architectural fix is preserved:
  * No top-level imports from domains.catalog.models.
  * rebuild_category_paths still resolves paths/depths correctly (error-path:
    empty category table returns 0).
"""
from __future__ import annotations

import ast

import pytest

_BACKEND_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
_TREE_PATH = _BACKEND_ROOT / "infrastructure" / "utils" / "category_tree.py"


class TestFile69Law1Regression:
    """Regression guard for the FILE-069 Law 1 fix."""

    def test_no_top_level_domain_imports(self):
        source = _TREE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("domains."):
                    pytest.fail(
                        f"Top-level import from domains found: {module}. "
                        "Law 1 forbids infrastructure from importing domains."
                    )

class TestFile69ErrorPath:
    """Error-path tests for category_tree helpers."""

    def test_rebuild_category_paths_empty_table_returns_zero(self):
        from unittest.mock import MagicMock

        from infrastructure.utils.category_tree import rebuild_category_paths

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        result = rebuild_category_paths(mock_db)
        assert result == 0
        mock_db.flush.assert_called_once()
