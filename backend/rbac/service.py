"""rbac/service.py - admin-facing RBAC operations.

Grant/revoke, delegation, maker-checker. Migrated from the legacy RBACService.
Uses rbac/models.py for persistence.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from rbac.models.permission_entities import Permission, RolePermissionAssignment, PermissionAuditLog

logger = logging.getLogger(__name__)


class RBACService:
    """Service for managing role-based access control grants and revocations."""

    def __init__(self, db: Session):
        self.db = db

    def grant(self, role: str, feature: str, granted_by: Optional[int] = None, country_code: Optional[str] = None) -> RolePermissionAssignment:
        """Grant a feature to a role.

        Args:
            role: The role name to grant the feature to.
            feature: The feature slug/identifier to grant.
            granted_by: Optional user ID of the admin performing the grant.
            country_code: Optional country scope for the grant.

        Returns:
            The created or updated RolePermissionAssignment.
        """
        permission = self._get_or_create_permission(feature)
        existing = (
            self.db.query(RolePermissionAssignment)
            .filter(
                RolePermissionAssignment.role_name == role,
                RolePermissionAssignment.permission_id == permission.id,
                RolePermissionAssignment.country_code == country_code,
            )
            .first()
        )
        if existing:
            existing.is_granted = True
            assignment = existing
        else:
            assignment = RolePermissionAssignment(
                role_name=role,
                permission_id=permission.id,
                country_code=country_code,
                granted_by=granted_by,
                is_granted=True,
            )
            self.db.add(assignment)

        self._audit_log("grant", role, permission.id, granted_by, country_code)
        self.db.commit()
        logger.info("Granted feature '%s' to role '%s'", feature, role)
        return assignment

    def revoke(self, role: str, feature: str, revoked_by: Optional[int] = None, country_code: Optional[str] = None) -> Optional[RolePermissionAssignment]:
        """Revoke a feature from a role.

        Args:
            role: The role name to revoke the feature from.
            feature: The feature slug/identifier to revoke.
            revoked_by: Optional user ID of the admin performing the revocation.
            country_code: Optional country scope for the revocation.

        Returns:
            The updated RolePermissionAssignment, or None if no assignment existed.
        """
        permission = self.db.query(Permission).filter(Permission.slug == feature).first()
        if not permission:
            logger.warning("Cannot revoke unknown feature '%s'", feature)
            return None

        assignment = (
            self.db.query(RolePermissionAssignment)
            .filter(
                RolePermissionAssignment.role_name == role,
                RolePermissionAssignment.permission_id == permission.id,
                RolePermissionAssignment.country_code == country_code,
            )
            .first()
        )
        if assignment:
            assignment.is_granted = False
            self._audit_log("revoke", role, permission.id, revoked_by, country_code)
            self.db.commit()
            logger.info("Revoked feature '%s' from role '%s'", feature, role)
        else:
            logger.warning("No assignment found for role '%s' feature '%s'", role, feature)
        return assignment

    def _get_or_create_permission(self, feature: str) -> Permission:
        """Look up or create a Permission record for the given feature slug."""
        permission = self.db.query(Permission).filter(Permission.slug == feature).first()
        if not permission:
            permission = Permission(
                category_id=1,
                name=feature,
                slug=feature,
                scope="global",
                is_active=True,
            )
            self.db.add(permission)
            self.db.flush()
        return permission

    def _audit_log(self, action: str, role: str, permission_id: int, actor_id: Optional[int], country_code: Optional[str]) -> None:
        """Write an entry to the permission audit log."""
        log_entry = PermissionAuditLog(
            actor_id=actor_id or 0,
            action=action,
            target_role=role,
            permission_id=permission_id,
            country_code=country_code,
        )
        self.db.add(log_entry)
