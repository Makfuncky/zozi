
"""
Content services for the Dynamic Supplier Upload flow (Step 6):

* ``translate_en_to_ar`` — best-effort EN→AR translation. The Ollama/LLM
  implementation now lives in ``providers.text`` (provider layer); this module
  re-exports it so first-party callers are unaffected. The provider falls back
  to a curated e-commerce glossary when Ollama is unreachable so the feature
  never hard-fails.
* ``moderate_content`` — scans text for GCC-restricted items (alcohol,
  pork, gambling, tobacco) and returns a pass/fail verdict with reasons.
  This is pure, dependency-free logic and stays in the services layer.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List

import structlog

logger = structlog.get_logger(__name__)
logger = logging.getLogger(__name__)

# The Ollama translation implementation was shifted to the provider layer.
from providers.ai.text import translate_en_to_ar  # noqa: F401  (re-exported API)

# Restricted-term → category used for moderation flags.
_RESTRICTED_KEYWORDS = {
    "alcohol": "alcohol", "wine": "alcohol", "beer": "alcohol", "liquor": "alcohol",
    "vodka": "alcohol", "whisky": "alcohol", "whiskey": "alcohol", "rum": "alcohol",
    "champagne": "alcohol", "pork": "pork", "bacon": "pork", "ham": "pork",
    "gambling": "gambling", "casino": "gambling", "bet": "gambling", "betting": "gambling",
    "lottery": "gambling", "cigar": "tobacco", "cigarette": "tobacco", "tobacco": "tobacco",
}


def moderate_content(text: str = "", category: str = "") -> Dict[str, object]:
    """
    Scan text for GCC-restricted content.

    Returns ``{"passed": bool, "flags": list[str], "notice": str}``.
    """
    flags: List[str] = []
    low = (text or "").lower()
    for kw, reason in _RESTRICTED_KEYWORDS.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", low):
            if reason not in flags:
                flags.append(reason)

    if flags:
        notice = (
            "Restricted content detected (" + ", ".join(flags) +
            "). This listing may be blocked in GCC markets. Review before publishing."
        )
        passed = False
    else:
        notice = "Content looks compliant for GCC markets."
        passed = True

    return {"passed": passed, "flags": flags, "notice": notice}
