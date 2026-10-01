"""Regression tests for accounts/ports.py wiring correctness."""
from __future__ import annotations

import inspect

import pytest


class TestOCRResultRelocation:
    """CONTR-013: OCRResult is colocated in accounts but belongs in media."""

    def test_ocr_result_import_surfaces_in_ports(self):
        """OCRResult import and helpers are present with relocation notice."""
        import domains.accounts.ports as ports

        assert hasattr(ports, "OCRResult")
        assert hasattr(ports, "get_o_c_r_result_by_id")
        assert hasattr(ports, "list_o_c_r_results")
        assert hasattr(ports, "list_o_c_r_results_page")

    def test_ocr_result_documented_as_colocated(self):
        """ports.py documents that OCRResult is colocated, not owned."""
        import domains.accounts.ports as ports

        source = inspect.getsource(ports)
        assert "media" in source.lower()
        assert "CONTR-013" in source
