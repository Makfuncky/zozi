"""Law 1 invariant: infrastructure.utils.image_ai_service must not contain a
static cross-layer import from providers at module load time.
"""
from __future__ import annotations

import ast
import pathlib

import pytest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[2] / "infrastructure" / "utils" / "image_ai_service.py"


def test_no_static_provider_import() -> None:
    src = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert not any(
        getattr(i, "module", "").startswith("providers") for i in imports
    ), "static provider import found in image_ai_service.py"
