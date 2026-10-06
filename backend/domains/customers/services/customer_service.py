"""Customer service — primary interface for customer-domain operations.

Per Law 3, cross-domain consumers should import ``CustomerService`` from
``domains.customers.services.customer_service`` rather than reaching directly
into the service sub-package tree.
"""
from __future__ import annotations

from typing import Any

from domains.customers.services.core.customer_service import CustomerService

__all__ = ["CustomerService"]
