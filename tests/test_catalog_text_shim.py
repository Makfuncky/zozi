"""Regression tests locking in the repair of the catalog AI-text import chain.

The SYM1 dead-symbol renaming prefixed ``_ollama_vision_chat`` in the canonical
module (``providers/ai/text.py``) which correctly re-exports the public alias
``ollama_vision_chat = _ollama_vision_chat``. The backward-compat shim
``providers/catalog/text.py`` was regenerated WITHOUT that alias, so three
routers (``api_catalog_query``, ``supplier_supplier_experiments``,
``api_media_bulk``) failed to load with
``cannot import name 'ollama_vision_chat' from 'providers.catalog.text'``.

Resolution (accepted over re-adding the shim): ``providers/catalog/
parcel_verification.py`` now imports the public alias directly from the
canonical ``providers.ai.text``, and the redundant shim was deleted after
confirming zero importers.

These tests assert that contract so a future regen cannot drop the public
alias again (the same bug class as the earlier order_payment_functions shim).
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"

# Routers that transitively depend on providers/catalog/parcel_verification.
DEPENDENT_ROUTERS = [
    "routers.api_catalog_query",
    "routers.supplier_supplier_experiments",
    "routers.api_media_bulk",
]


def _insert_backend_path() -> None:
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))


def test_public_alias_survives_in_canonical_module():
    """providers/ai/text.py must keep the public ollama_vision_chat alias."""
    _insert_backend_path()
    text = importlib.import_module("providers.ai.text")
    alias = getattr(text, "ollama_vision_chat", None)
    assert callable(alias), "providers.ai.text lost callable ollama_vision_chat"


def test_parcel_verification_imports_public_alias():
    """The direct consumer must bind the public alias from the canonical module."""
    _insert_backend_path()
    pv = importlib.import_module("providers.catalog.parcel_verification")
    assert callable(getattr(pv, "ollama_vision_chat", None)), (
        "parcel_verification lost its ollama_vision_chat binding"
    )
    # It must be the SAME object as the canonical alias (no duplicate impl).
    canonical = importlib.import_module("providers.ai.text").ollama_vision_chat
    assert pv.ollama_vision_chat is canonical, (
        "parcel_verification does not reuse the canonical ollama_vision_chat"
    )


def test_dependent_routers_import():
    """Every router that hit the broken chain must now import cleanly."""
    _insert_backend_path()
    for module_name in DEPENDENT_ROUTERS:
        importlib.import_module(module_name)  # raises ImportError if broken


def test_deleted_shim_has_no_importers():
    """The removed providers/catalog/text.py must not be referenced in source."""
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py", "providers.catalog.text", str(BACKEND)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, (
        "providers.catalog.text is still referenced:\n" + result.stdout
    )
