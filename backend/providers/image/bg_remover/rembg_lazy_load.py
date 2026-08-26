# ========================== REMBG LAZY LOAD ==========================

from typing import Optional

_HAS_REMBG = False
remove = None
new_session = None


def _ensure_rembg():
    global remove, new_session, _HAS_REMBG
    if not _HAS_REMBG:
        try:
            from rembg import remove as _remove, new_session as _new_session
            remove = _remove
            new_session = _new_session
            _HAS_REMBG = True
        except ImportError:
            pass

