"""Pure currency primitives — no provider dependencies.

Kernel must not import from providers. Rate-dependent functions live in
infrastructure.utils.currency_service. This module re-exports the pure
primitives for backward compatibility.
"""
from __future__ import annotations

from decimal import Decimal

# Re-export pure constants and types for backward compatibility
# Rate-dependent functions are in infrastructure.utils.currency_service
