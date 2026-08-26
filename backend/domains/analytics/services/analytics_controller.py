"""Migration re-export shim for the old controller module `analytics_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

# Upward import from modules removed — these should be called via the module layer
# analytics_chatbot, analytics_timeseries, analytics_top_products, analytics_user_growth
# are now accessed through modules.admin.routers.admin (the module layer)

# Unresolved during migration: analytics_customers, analytics_overview
