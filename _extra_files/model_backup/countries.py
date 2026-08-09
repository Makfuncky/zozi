"""Re-export of the canonical countries models.

The ``models.geography`` package is the canonical home for these ORM classes.
This flat module now forwards to it so that ``models.CountryConfig`` and
``models.geography.countries.CountryConfig`` resolve to the *same* class object,
eliminating the duplicate-table collision flagged by the architecture audit.
"""
from __future__ import annotations

from models.geography.countries import *  # noqa: F401,F403
