"""Migration re-export shim for the old controller module `translate_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from domains.governance.services.translation_service import TranslateRequest, TranslateResponse, translate_texts
