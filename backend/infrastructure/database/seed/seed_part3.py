"""Seed part 3 — re-exports from _common (Law 1 compliant).

All seed logic lives in infrastructure/database/seed/_common.py using
lazy model loading. This module re-exports for backwards compatibility.
"""
from __future__ import annotations

from infrastructure.database.seed._common import *  # noqa: F401,F403

__all__: list[str] = []
