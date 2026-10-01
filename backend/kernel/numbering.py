"""Shared kernel - reference numbering (spec: kernel/numbering.py).

Centralised, configurable reference-number generation for business documents
(ORD-, INV-, PAY-, BATCH-, ...). Domains call this instead of inventing local IDs.
"""
import time
from typing import Dict, Optional

_PREFIXES: Dict[str, str] = {
    "order": "ORD",
    "invoice": "INV",
    "payout": "PAY",
    "batch": "BATCH",
}

def next_reference(kind: str, country: Optional[str] = None, seq: Optional[int] = None) -> str:
    prefix = _PREFIXES.get(kind, kind.upper()[:4])
    if seq is None:
        seq = int(time.time() * 1000) % 1_000_000
    suffix = f"-{country}" if country else ""
    return f"{prefix}-{seq:06d}{suffix}"
