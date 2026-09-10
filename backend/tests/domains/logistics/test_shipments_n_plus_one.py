"""Law 45 smoke test: Shipment relationships must use ``selectin`` eager loading.

ARCHITECTURE_DIAGRAM.md Law 45 (N+1 prevention) requires the
``domains.logistics.models.logistics_entities.Shipment`` model's most-touched
foreign keys to be eager-loaded so a list endpoint does not fan out into
per-row SELECTs. Closes audit finding #18.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_MODEL_PATH = pathlib.Path(
    "domains/logistics/models/logistics_entities.py"
)
_REQUIRED_LAZY = {"order", "supplier", "assigned_partner", "carrier"}


def test_shipment_relationships_use_selectin() -> None:
    backend_root = pathlib.Path(__file__).resolve().parent.parent.parent.parent
    target = backend_root / _MODEL_PATH
    text = target.read_text(encoding="utf-8")
    tree = ast.parse(text)

    shipment_cls = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Shipment":
            shipment_cls = node
            break
    assert shipment_cls is not None, "Shipment model not found in logistics_entities.py"

    found: dict[str, str] = {}
    for stmt in shipment_cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        target_name = stmt.targets[0].id
        if target_name not in _REQUIRED_LAZY:
            continue
        if not isinstance(stmt.value, ast.Call):
            continue
        # Check kwargs for lazy="selectin"
        lazy_kw = None
        for kw in stmt.value.keywords:
            if kw.arg == "lazy" and isinstance(kw.value, ast.Constant):
                lazy_kw = kw.value.value
        found[target_name] = lazy_kw

    missing = _REQUIRED_LAZY - found.keys()
    assert not missing, (
        f"Shipment missing relationship declarations: {sorted(missing)}"
    )

    not_selectin = [k for k, v in found.items() if v != "selectin"]
    assert not not_selectin, (
        "Shipment relationships must use lazy='selectin' to avoid N+1:\n  "
        + "\n  ".join(f"{k}: {found[k]!r}" for k in not_selectin)
    )