"""Analytics domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. This domain currently
exposes no permission atoms. Add atoms here as capabilities are introduced; CI
must fail on any ``require_feature("analytics.*")`` literal not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {}
