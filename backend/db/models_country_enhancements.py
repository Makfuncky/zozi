"""
Compatibility module — re-exports country-scoped models from the ``models``
package sub-modules (``models.country_enhancements``, etc.).

All definitions are now in ``models/`` so that they share the unified
``Base`` (from ``db.base.Base``) with the rest of the ORM registry.
"""
from __future__ import annotations

from data.models_country_enhancements import *  # noqa: F401, F403
