"""Canonical ``models.permissions`` domain package.

The previous flat ``models/permissions.py`` was promoted to this package
(``models/permissions/permission_entities.py``) to satisfy the AI File
Placement Contract (``backend/models/`` must be organised as domain folders)
and to reduce the coupling of ``models/__init__.py`` (god-module MET5).

``Base`` is imported from the parent ``models`` package (``from .. import Base``)
rather than the package ``__init__`` so the submodule can avoid re-entering this
package and breaking the intra-package import cycle flagged by DG2.
"""
from __future__ import annotations

from .. import Base

from .permission_entities import (
    PermissionCategory,
    Permission,
    RolePermissionAssignment,
    UserPermissionOverride,
    PermissionAuditLog,
)
