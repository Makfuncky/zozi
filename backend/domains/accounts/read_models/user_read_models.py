"""User read-model projections for the accounts domain."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class UserProjection:
    """Flattened, read-optimised view of a User."""
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: str


@dataclass
class UserSummaryProjection:
    """Summary view of a user for list displays."""
    id: int
    username: str
    role: str
    is_active: bool
