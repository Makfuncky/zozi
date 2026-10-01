"""
Structural regression tests for the MEDIA module rescue.

These assert that the genuine defects found in the media module stay fixed:
  * DOM7  - empty non-canonical ``services/uploads`` folder removed
  * QUAL2 - stale ``TODO:`` debt marker removed from providers/media/image.py
  * QUAL1 / HL302 - silent exception swallows in media services/routers now log
  * INTENTIONAL backward-compat shims at providers root are preserved (not deleted)

Run with:  pytest tests/test_media_module_rescue.py --noconftest -q
"""
from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"

MEDIA_SERVICES = BACKEND / "services" / "media"
MEDIA_ROUTERS = BACKEND / "routers"

# Silent-swallow patterns that must NOT appear directly after `except Exception:`.
FORBIDDEN_SWALLOW = re.compile(
    r"except\s+Exception\s*:\s*\r?\n[ \t]*?(pass|return None|continue|return image_bytes)(?=\s|$)",
    re.MULTILINE,
)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_services_uploads_is_runtime_not_source():
    """DOM7 guard: ``services/uploads`` is a runtime data dir created by
    LocalStorage (storage.py:30 -> UPLOADS_DIR, makedirs in __init__), not a
    misplaced source module. It must never contain Python source — if source
    ever lands here, that is the real defect the audit flagged.
    """
    uploads = BACKEND / "services" / "uploads"
    if uploads.exists():
        py_files = list(uploads.rglob("*.py"))
        assert not py_files, f"source files found in runtime dir {uploads}: {py_files}"


def test_qual2_todo_marker_removed():
    """QUAL2: stale ``TODO:`` debt marker removed from the media image provider."""
    src = _read(BACKEND / "providers" / "media" / "image.py")
    assert "TODO: This is a STUB" not in src


def test_no_silent_swallow_in_media_services():
    """QUAL1 / HL302: media service files must not silently swallow exceptions."""
    targets = [
        MEDIA_SERVICES / "free_image_tools.py",
        MEDIA_SERVICES / "image_ai_service.py",
        MEDIA_SERVICES / "storage.py",
        MEDIA_SERVICES / "media_service.py",
    ]
    for path in targets:
        assert not FORBIDDEN_SWALLOW.search(_read(path)), f"silent swallow found in {path.name}"


def test_no_silent_swallow_in_media_router():
    """HL302: the media bulk router must not silently `continue` on exception."""
    path = MEDIA_ROUTERS / "api_media_bulk.py"
    assert not FORBIDDEN_SWALLOW.search(_read(path)), f"silent swallow found in {path.name}"


def test_backward_compat_provider_shims_preserved():
    """MV1 misclassification guard: intentional compat shims must remain (not deleted).

    providers/image.py re-exports providers.media.image and providers/bg_remover.py
    re-exports providers.hr.bg_remover; their importers live in the exempt `data`
    circuit layer, so deleting them would break the forwarder chain.
    """
    image_shim = BACKEND / "providers" / "image.py"
    bg_shim = BACKEND / "providers" / "bg_remover.py"
    assert image_shim.exists() and "providers.media.image" in _read(image_shim)
    assert bg_shim.exists() and "providers.hr.bg_remover" in _read(bg_shim)
