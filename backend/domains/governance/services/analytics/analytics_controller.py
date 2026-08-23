"""Migration re-export shim for the old controller module `analytics_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from modules.admin.routers.admin import analytics_chatbot, analytics_timeseries, analytics_top_products, analytics_user_growth

# Unresolved during migration: analytics_customers, analytics_overview
