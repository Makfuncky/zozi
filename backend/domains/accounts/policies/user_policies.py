"""User authorization policies."""
from __future__ import annotations


class UserPolicy:
    """Authorization policies for user operations."""

    @staticmethod
    def can_view_user(actor: dict, target_user_id: int) -> bool:
        """Check if actor can view user details."""
        if actor.get("role") in ("admin", "super_admin"):
            return True
        return actor.get("user_id") == target_user_id

    @staticmethod
    def can_create_user(actor: dict) -> bool:
        """Check if actor can create users."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_delete_user(actor: dict) -> bool:
        """Check if actor can delete users."""
        return actor.get("role") == "super_admin"

    @staticmethod
    def can_assign_role(actor: dict) -> bool:
        """Check if actor can assign roles."""
        return actor.get("role") in ("admin", "super_admin")
