"""Single consolidated Row-Level Security (RLS) enforcer.

NEW_STRUCTURE.md (step 5) requires the scattered RLS enforcers
(rls_interceptor, rls_dependency, rls_middleware, rls_context,
country_context) to be consolidated into ONE module:
infrastructure/database/security.py.

This module is the canonical import surface for RLS. The original
implementations still live in infrastructure.utils.rls_interceptor and
middleware.country_context (heavily imported across the codebase); this
file re-exports them so new code should `from infrastructure.database.security
import ...` and the legacy paths remain functional during the migration.
"""

from __future__ import annotations

# Canonical RLS context + SQLA event interceptor.
from infrastructure.utils.rls_interceptor import (  # noqa: F401
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

# Country-context middleware (per-request RLS scope resolution).
from middleware.country_context import CountryContextMiddleware  # noqa: F401

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
    "CountryContextMiddleware",
]
