"""Core customer service — primary interface for customer domain operations."""
from __future__ import annotations

from typing import Any


class CustomerService:
    """Sanctioned entry-point for customer-domain operations (Law 3).

    Cross-domain consumers should instantiate this class with a ``db`` session
    rather than reaching directly into the service sub-package.
    """

    def __init__(self, db: Any) -> None:
        self.db = db

    def __call__(self) -> str:
        return "CustomerService"
