"""suppliers domain - service layer package.

Owns all business logic and DB access for the suppliers domain. Module routers
import from here (never query the session directly). Services depend only on
infrastructure, kernel, providers (via services), and their own domain models
(per the dependency laws in ARCHITECTURE_DIAGRAM.md).
"""

from __future__ import annotations

__all__ = []
