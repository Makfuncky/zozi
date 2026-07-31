"""RLS Middleware — consolidated entry point for all RLS concerns.

This module re-exports the key RLS utilities from across the codebase,
providing a single import point for country-scoped row-level security.

Layers
------
1. **Interceptor** (``utils.rls_interceptor``) — SQLAlchemy ``before_execute``
   event listener that injects ``WHERE country_code IN (...)`` on every query
   targeting a country-aware table.

2. **Middleware** (``middleware.country_context``) — FastAPI ``BaseHTTPMiddleware``
   that resolves the country scope per-request from JWT claims, staff assignments,
   headers, or IP geolocation and calls ``set_rls_context()``.

3. **Dependencies** (``middleware.rls_dependency``) — FastAPI dependency functions
   for per-route country access checks (decorator-style or inline).

Usage
-----
    from middleware.rls import (
        CountryContextMiddleware,
        get_current_country_code,
        require_country_access,
        set_rls_context,
        clear_rls_context,
        instrument_rls,
        generate_rls_policy_sql,
    )

See Also
--------
- ``backend/utils/rls_interceptor.py`` — SQLAlchemy-level interceptor
- ``backend/middleware/country_context.py`` — request-level middleware
- ``backend/data/pg_rls_policies.sql`` — auto-generated PostgreSQL policies
"""
from __future__ import annotations

# ── Interceptor (SQLAlchemy level) ────────────────────────────────────────
from utils.rls_interceptor import (
    COUNTRY_AWARE_TABLES,
    SecurityContextMissingError,
    clear_rls_context,
    derive_country_aware_tables_from_db,
    generate_rls_policy_sql,
    instrument_rls,
    install_rls_policies,
    rls_before_execute,
    set_rls_context,
    validate_rls_coverage,
)

# ── Middleware (FastAPI request level) ─────────────────────────────────────
from middleware.country_context import (
    CountryContextMiddleware,
    EnhancedGeoBlockingMiddleware,
    RowLevelSecurityMiddleware,
    apply_rls_filter,
    clear_rls_context as clear_middleware_context,
    get_rls_context,
    resolve_user_country_scope,
    rls_context,
)

# ── Dependencies (FastAPI per-route level) ────────────────────────────────
from middleware.rls_dependency import (
    check_country_access,
    get_country_scope,
    get_current_country_code,
    require_country_access,
)

__all__ = [
    # Interceptor
    "COUNTRY_AWARE_TABLES",
    "SecurityContextMissingError",
    "clear_rls_context",
    "derive_country_aware_tables_from_db",
    "generate_rls_policy_sql",
    "instrument_rls",
    "install_rls_policies",
    "rls_before_execute",
    "set_rls_context",
    "validate_rls_coverage",
    # Middleware
    "CountryContextMiddleware",
    "EnhancedGeoBlockingMiddleware",
    "RowLevelSecurityMiddleware",
    "apply_rls_filter",
    "get_rls_context",
    "resolve_user_country_scope",
    "rls_context",
    # Dependencies
    "check_country_access",
    "get_country_scope",
    "get_current_country_code",
    "require_country_access",
]
