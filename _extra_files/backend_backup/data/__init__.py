"""
Curated data sources for the Country Control Plane auto-population system.

Each module provides lookup functions that return structured data about
countries, cities, tax rates, and related metadata.  This data is used
by ``services.country_auto_populate`` as:
  1. A fallback when external API calls fail or time out.
  2. A source of curated defaults that override generic API responses.

Populate these modules with real country-specific data as part of the
GCC / MENA market expansion.
"""
