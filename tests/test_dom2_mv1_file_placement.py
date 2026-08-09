"""Test DOM2/MV1 file placement fixes.

Validates that:
1. All 15 moved files are importable from their new canonical locations
2. All backward-compat shims at old locations resolve correctly
3. All 143 routers load without errors
"""
import importlib
import re
import ast
import sys
import os
import pytest

# Ensure backend/ is on sys.path
BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


# ─── Moved files: new canonical locations must be importable ───
MOVED_FILES = [
    # Providers — DOM2 fixes
    ("providers.geography.geo", "providers/logistics/geo.py → providers/geography/geo.py"),
    ("providers.ai.text", "providers/catalog/text.py → providers/ai/text.py"),
    ("providers.ai.ocr", "providers/ocr.py → providers/ai/ocr.py"),
    ("providers.ai.vision", "providers/vision.py → providers/ai/vision.py"),
    ("providers.ai.voice_to_text", "providers/voice_to_text.py → providers/ai/voice_to_text.py"),
    ("providers.media.bg_remover", "providers/bg_remover.py → providers/media/bg_remover.py"),
    ("providers.media.image", "providers/image.py → providers/media/image.py"),
    # Services — DOM2 + MV1 fixes
    ("services.ai.automation_read_service", "services/finance/ → services/ai/"),
    ("services.commerce.wishlist_read_service", "services/catalog/ → services/commerce/"),
    ("services.commerce.customer_router_service", "services/customer/ → services/commerce/"),
    ("services.cross_border_tracker", "services/commerce/ → services/ (consolidated)"),
    ("services.geography.geo_service", "services/location/ → services/geography/"),
    ("services.geo_fence_service", "services/logistics/ → services/ (consolidated)"),
    ("services.orders.cart_write_service", "services/commerce/ → services/orders/"),
    ("services.country_read_service", "services/ → services/ (consolidated)"),
]


@pytest.mark.parametrize(
    "module_path,description",
    MOVED_FILES,
    ids=[m[0].split(".")[-1] for m in MOVED_FILES],
)
def test_moved_file_importable(module_path, description):
    """Each moved file must be importable from its new canonical location."""
    mod = importlib.import_module(module_path)
    assert mod is not None, f"{module_path} ({description}) imported as None"


# ─── Backward-compat shims: old locations must still resolve ───
BACKWARD_COMPAT_SHIMS = [
    ("providers.logistics.geo", "providers/logistics/geo.py shim"),
    ("providers.catalog.text", "providers/catalog/text.py shim"),
    ("providers.ocr", "providers/ocr.py shim"),
    ("providers.vision", "providers/vision.py shim"),
    ("providers.voice_to_text", "providers/voice_to_text.py shim"),
    ("providers.bg_remover", "providers/bg_remover.py shim"),
    ("providers.image", "providers/image.py shim"),
]


@pytest.mark.parametrize(
    "module_path,description",
    BACKWARD_COMPAT_SHIMS,
    ids=[m[0].split(".")[-1] for m in BACKWARD_COMPAT_SHIMS],
)
def test_backward_compat_shim(module_path, description):
    """Old import paths must still resolve via backward-compat shims."""
    mod = importlib.import_module(module_path)
    assert mod is not None, f"{module_path} ({description}) shim returned None"
    # Verify it actually re-exports something
    public_names = [n for n in dir(mod) if not n.startswith("_")]
    assert len(public_names) > 0, (
        f"{module_path} shim re-exports no public names"
    )


# ─── All 143 routers must load ───
def test_all_routers_load():
    """Every router in main.py's router_names list must import cleanly."""
    main_path = os.path.join(BACKEND, "main.py")
    with open(main_path, "r", encoding="utf-8") as f:
        src = f.read()

    match = re.search(r"router_names = \[(.*?)\]", src, re.S)
    assert match, "Could not find router_names in main.py"

    names = [t[0] for t in ast.literal_eval("[" + match.group(1) + "]")]

    failures = []
    for name in names:
        try:
            importlib.import_module(f"routers.{name}")
        except Exception as exc:
            failures.append((name, str(exc)[:200]))

    assert failures == [], (
        f"{len(failures)}/{len(names)} routers failed to load:\n"
        + "\n".join(f"  FAIL {n}: {e}" for n, e in failures)
    )


# ─── Cross-cutting: no circular imports in restored providers ───
def test_providers_text_no_circular_import():
    """providers.text must not circularly import itself."""
    import providers.text as pt

    assert hasattr(pt, "_ollama_chat"), "providers.text missing _ollama_chat"
    assert hasattr(pt, "embed_text"), "providers.text missing embed_text"
    assert hasattr(pt, "cosine_similarity"), "providers.text missing cosine_similarity"


def test_providers_vision_no_circular_import():
    """providers.ai.vision must not circularly import itself."""
    import providers.ai.vision as pv

    assert hasattr(pv, "suggest_price"), "providers.ai.vision missing suggest_price"
    assert hasattr(pv, "analyze_product_image"), "providers.ai.vision missing analyze_product_image"
    assert hasattr(pv, "VariantConfig"), "providers.ai.vision missing VariantConfig"
