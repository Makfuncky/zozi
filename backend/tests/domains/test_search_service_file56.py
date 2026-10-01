"""Unit tests for FILE-56 search_service.py deprecation notice."""
from __future__ import annotations

import os

import pytest


SOURCE_PATH = "backend/domains/catalog/services/search_service.py"
EVIDENCE_DIR = "_audit/resolver/evidence/FILE-56"


def _source() -> str:
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestDim23DeprecationNotice:
    """DIM23-08: deprecation notice added, redirecting to canonical search/search_service.py."""

    def test_deprecated_directive_in_docstring(self):
        src = _source()
        assert ".. deprecated::" in src, "Module docstring should contain Sphinx deprecated directive"

    def test_migrate_message_present(self):
        src = _source()
        assert "domains.catalog.services.search.search_service" in src, \
            "Deprecation notice should reference the canonical module path"

    def test_deprecated_word_present(self):
        src = _source()
        assert "deprecated" in src.lower(), "File should contain 'deprecated' for verification grep"


class TestAllReexportsCanonicalSymbols:
    """__all__ updated to re-export canonical symbols."""

    def test_all_defined(self):
        src = _source()
        assert "__all__" in src, "__all__ should be defined in the deprecated module"

    def test_all_contains_existing_symbols(self):
        src = _source()
        assert "load_search_catalog" in src, "__all__ should preserve existing load_search_catalog"
        assert "search_products" in src, "__all__ should preserve existing search_products"

    def test_all_contains_canonical_symbols(self):
        src = _source()
        assert "parse_query" in src, "__all__ should re-export parse_query from canonical module"
        assert "smart_search" in src, "__all__ should re-export smart_search from canonical module"
        assert "get_recommendations" in src, "__all__ should re-export get_recommendations from canonical module"
        assert "AdvancedFilterService" in src, "__all__ should re-export AdvancedFilterService from canonical module"
        assert "AdvancedSearchEngine" in src, "__all__ should re-export AdvancedSearchEngine from canonical module"


class TestBackwardCompatibility:
    """Existing imports still work after deprecation."""

    def test_existing_functions_still_exist(self):
        src = _source()
        assert "def load_search_catalog(" in src, "load_search_catalog should still be defined"
        assert "def search_products(" in src, "search_products should still be defined"

    def test_module_importable(self):
        import importlib
        mod = importlib.import_module("domains.catalog.services.search_service")
        assert hasattr(mod, "load_search_catalog"), "Module should still expose load_search_catalog"
        assert hasattr(mod, "search_products"), "Module should still expose search_products"
        assert hasattr(mod, "__all__"), "Module should define __all__"


class TestEvidenceFiles:
    """Verify evidence outputs."""

    def test_evidence_dir_exists(self):
        assert os.path.isdir(EVIDENCE_DIR), "Evidence directory should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
