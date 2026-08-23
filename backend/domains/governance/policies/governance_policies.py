"""governance domain — authorization policies.

Business authorization rules that gate governance operations. These complement
the feature atoms in features.py (which are infrastructure-level gates) with
context-aware business logic (country scoping, hierarchy, ownership).
"""

from __future__ import annotations


class PermissionPolicy:
    """Authorization policies for permission and role operations."""

    @staticmethod
    def can_manage_permissions(actor: dict) -> bool:
        """Only super_admin can modify permission catalog."""
        return actor.get("role") == "super_admin"

    @staticmethod
    def can_assign_role(actor: dict, target_role: str) -> bool:
        """Check if actor can assign a specific role."""
        actor_role = actor.get("role")
        if actor_role == "super_admin":
            return True
        if actor_role == "admin" and target_role not in ("super_admin",):
            return True
        return False

    @staticmethod
    def can_update_role_permissions(actor: dict) -> bool:
        """Only super_admin can change role-permission mappings."""
        return actor.get("role") == "super_admin"


class UserPolicy:
    """Authorization policies for user management operations."""

    @staticmethod
    def can_view_user(actor: dict, target_user_id: int) -> bool:
        """Check if actor can view user details."""
        if actor.get("role") in ("admin", "super_admin"):
            return True
        return actor.get("user_id") == target_user_id

    @staticmethod
    def can_create_user(actor: dict) -> bool:
        """Admin and above can create users."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_update_user(actor: dict, target_user_id: int) -> bool:
        """Admin can update users; users can update themselves."""
        if actor.get("role") in ("admin", "super_admin"):
            return True
        return actor.get("user_id") == target_user_id

    @staticmethod
    def can_delete_user(actor: dict) -> bool:
        """Only super_admin can delete users."""
        return actor.get("role") == "super_admin"

    @staticmethod
    def can_toggle_user_active(actor: dict) -> bool:
        """Admin and above can activate/deactivate users."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_force_reset_password(actor: dict) -> bool:
        """Admin and above can force password resets."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_bulk_manage_users(actor: dict) -> bool:
        """Only super_admin can perform bulk user operations."""
        return actor.get("role") == "super_admin"


class SupplierPolicy:
    """Authorization policies for supplier management."""

    @staticmethod
    def can_verify_supplier(actor: dict) -> bool:
        """Admin and above can verify suppliers."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_reject_supplier(actor: dict) -> bool:
        """Admin and above can reject suppliers."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_manage_suppliers(actor: dict) -> bool:
        """Admin and above can manage supplier accounts."""
        return actor.get("role") in ("admin", "super_admin")


class OrderPolicy:
    """Authorization policies for order management."""

    @staticmethod
    def can_update_order_status(actor: dict) -> bool:
        """Admin and above can change order status."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_refund_order(actor: dict) -> bool:
        """Admin and above can issue refunds."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_delete_order(actor: dict) -> bool:
        """Only super_admin can delete orders."""
        return actor.get("role") == "super_admin"


class ProductPolicy:
    """Authorization policies for product management."""

    @staticmethod
    def can_approve_product(actor: dict) -> bool:
        """Admin and above can approve products."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_delete_product(actor: dict) -> bool:
        """Admin and above can delete products."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_moderate_products(actor: dict) -> bool:
        """Admin and above can moderate products."""
        return actor.get("role") in ("admin", "super_admin")


class TreasuryPolicy:
    """Authorization policies for treasury operations."""

    @staticmethod
    def can_view_treasury(actor: dict) -> bool:
        """Admin and above can view treasury reports."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_verify_payout(actor: dict) -> bool:
        """Admin and above can verify payouts."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_record_remittance(actor: dict) -> bool:
        """Admin and above can record COD remittances."""
        return actor.get("role") in ("admin", "super_admin")


class FraudPolicy:
    """Authorization policies for fraud management."""

    @staticmethod
    def can_view_fraud(actor: dict) -> bool:
        """Admin and above can view fraud events."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_manage_fraud(actor: dict) -> bool:
        """Admin and above can manage fraud cases."""
        return actor.get("role") in ("admin", "super_admin")


class SecurityPolicy:
    """Authorization policies for security operations."""

    @staticmethod
    def can_view_incidents(actor: dict) -> bool:
        """Admin and above can view security incidents."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_manage_incidents(actor: dict) -> bool:
        """Admin and above can manage security incidents."""
        return actor.get("role") in ("admin", "super_admin")


class AuditPolicy:
    """Authorization policies for audit and compliance."""

    @staticmethod
    def can_view_audit_trail(actor: dict) -> bool:
        """Admin and above can view audit trails."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_view_compliance(actor: dict) -> bool:
        """Admin and above can view compliance status."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_manage_retention(actor: dict) -> bool:
        """Only super_admin can manage data retention policies."""
        return actor.get("role") == "super_admin"
