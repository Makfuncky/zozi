"""FILE-70 regression tests for backend/infrastructure/utils/country_rls.py.

Verifies that the Law 1 architectural fix is preserved:
  * No top-level imports from domains.country.models.
  * get_country_or_404 raises HTTPException(404) when a country is missing.
"""
from __future__ import annotations

import ast

import pytest

_BACKEND_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
_RLS_PATH = _BACKEND_ROOT / "infrastructure" / "utils" / "country_rls.py"


class TestFile70Law1Regression:
    """Regression guard for the FILE-70 Law 1 fix."""

    def test_no_top_level_domain_imports(self):
        source = _RLS_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("domains."):
                    pytest.fail(
                        f"Top-level import from domains found: {module}. "
                        "Law 1 forbids infrastructure from importing domains."
                    )

    def test_country_staff_assignment_not_imported_at_module_scope(self):
        source = _RLS_PATH.read_text(encoding="utf-8")
        assert "CountryStaffAssignment" not in source.split("def ")[0], (
            "CountryStaffAssignment must not appear in the module-level import block"
        )


class TestFile70ErrorPath:
    """Error-path tests for get_country_or_404."""

    def test_get_country_or_404_raises_404_for_unknown_country(self):
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from infrastructure.utils.country_rls import get_country_or_404

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_country_or_404("XX", mock_db)
        assert exc_info.value.status_code == 404
        assert "Country config not found" in exc_info.value.detail
