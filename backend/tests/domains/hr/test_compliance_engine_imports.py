"""Regression tests for FILE-40: ARCH-010 compliance_engine import fix."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_TARGET = _BACKEND_ROOT / "domains" / "hr" / "services" / "compliance_engine.py"


class TestComplianceEngineImports:
    """Prove that compliance_engine no longer has forbidden direct model imports."""

    def test_no_direct_hr_model_imports(self):
        content = _TARGET.read_text()
        tree = ast.parse(content)
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if (
                    "domains.hr.models" in module
                    and "ports" not in module
                ):
                    offenders.append(module)
        assert not offenders, (
            "Forbidden direct hr model imports found: " + ", ".join(offenders)
        )

    def test_no_cross_domain_accounts_import(self):
        content = _TARGET.read_text()
        tree = ast.parse(content)
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if "domains.accounts" in module:
                    offenders.append(module)
        assert not offenders, (
            "Forbidden cross-domain accounts imports found: " + ", ".join(offenders)
        )

    def test_uses_ports_for_hr_models(self):
        content = _TARGET.read_text()
        assert "from domains.hr.ports import" in content, (
            "Expected compliance_engine to import hr models via domains.hr.ports"
        )

    def test_compliance_engine_imports_cleanly(self):
        from domains.hr.services.compliance_engine import (  # noqa: F401
            GCCComplianceEngine,
            get_compliance_engine,
        )

        assert GCCComplianceEngine is not None
        assert get_compliance_engine is not None

    def test_unused_user_import_removed(self):
        content = _TARGET.read_text()
        assert "User" not in content, (
            "Unused User import should have been removed from compliance_engine.py"
        )
