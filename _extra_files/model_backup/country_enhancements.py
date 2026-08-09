"""Re-export of the canonical country-enhancement models.

The ``models.geography`` package is the canonical home for these ORM classes.
This flat module now forwards to it so that ``models.CountryFeatureFlag`` and
``models.geography.country_enhancements.CountryFeatureFlag`` resolve to the
*same* class object, eliminating the duplicate-table collision flagged by the
architecture audit.
"""
from __future__ import annotations

from models.geography.country_enhancements import *  # noqa: F401,F403
