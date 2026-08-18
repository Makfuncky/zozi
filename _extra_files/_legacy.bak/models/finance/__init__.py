"""Canonical ``models.finance`` domain package.

The previous flat ``models/finance.py`` was promoted to this package
(``models/finance/general_ledger.py``) to satisfy the AI File Placement
Contract (``backend/models/`` must be organised as domain folders) and to
reduce the coupling of ``models/__init__.py`` (god-module MET5).

``Base`` is re-exported from the parent ``models`` package so the submodule
can keep using the relative ``from . import Base`` idiom.
"""
from __future__ import annotations

from .. import Base

from .general_ledger import *  # noqa: F401,F403
# ``commission`` stays a flat module (preserved for backward compatibility);
# forward it here so ``models.finance.CommissionAgreement`` and
# ``models.CommissionAgreement`` resolve to the same class object.
from _legacy.models.commission import *  # noqa: F401,F403
