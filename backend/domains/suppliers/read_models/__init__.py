"""suppliers domain - CQRS-lite read models package (ARCHITECTURE_DIAGRAM.md §3).

Holds the suppliers domain's own CQRS-lite projections — optimized read models
populated incrementally as projections are extracted from write services. Cross-
domain dashboards read these via the suppliers ``ports.py`` rather than querying
the write tables directly.
"""

from __future__ import annotations

__all__ = []
