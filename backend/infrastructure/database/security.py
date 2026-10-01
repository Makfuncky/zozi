"""Single consolidated Row-Level Security (RLS) enforcer.

NEW_STRUCTURE.md (step 5) requires the scattered RLS enforcers
(rls_interceptor, rls_dependency, rls_middleware, rls_context,
country_context) to be consolidated into ONE module:
infrastructure/database/security.py.

This module is the canonical import surface for RLS infrastructure primitives.
Country-context middleware lives in middleware.country_context and should be
imported directly from there — infrastructure must not import middleware
(Law 1: modules → domains → infrastructure).
"""

from __future__ import annotations

# Canonical RLS context + SQLA event interceptor.
from infrastructure.database.rls_interceptor import (  # noqa: F401
    COUNTRY_AWARE_TABLES,
    SecurityContextMissingError,
    clear_rls_context,
    derive_country_aware_tables_from_db,
    generate_rls_policy_sql,
    install_rls_policies,
    instrument_rls,
    rls_before_execute,
    set_rls_context,
    validate_rls_coverage,
)

__all__ = [
    "COUNTRY_AWARE_TABLES",
    "SecurityContextMissingError",
    "clear_rls_context",
    "derive_country_aware_tables_from_db",
    "generate_rls_policy_sql",
    "install_rls_policies",
    "instrument_rls",
    "rls_before_execute",
    "set_rls_context",
    "validate_rls_coverage",
]
