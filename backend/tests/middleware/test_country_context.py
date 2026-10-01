"""Regression test for FILE-78: middleware must not import from providers.geography.

Law 104 restricts middleware to ``infrastructure/`` + ``rbac/`` only.
``backend/middleware/country_context.py`` must resolve IP→country through
``infrastructure.geography`` (or another sanctioned layer), never through a
direct ``providers.geography`` import.
"""
from __future__ import annotations

import ast
import pathlib

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[2]
_COUNTRY_CONTEXT_PATH = _BACKEND_ROOT / "middleware" / "country_context.py"


def test_country_context_has_no_providers_geography_import() -> None:
    source = _COUNTRY_CONTEXT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("providers.geography"):
                offenders.append(node.module)
    assert not offenders, (
        "Forbidden providers.geography import(s) in country_context.py: "
        f"{', '.join(offenders)}. Middleware must import from "
        "infrastructure.geography instead."
    )


def test_country_context_imports_infrastructure_geography() -> None:
    source = _COUNTRY_CONTEXT_PATH.read_text(encoding="utf-8")
    assert "from infrastructure.geography import detect_country_from_ip" in source
