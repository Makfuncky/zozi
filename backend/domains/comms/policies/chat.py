"""Chat authorization policies."""
from __future__ import annotations


class ChatPolicy:
    """Authorization policies for chat operations."""

    @staticmethod
    def can_create_thread(actor: dict, entity_type: str, entity_id: int) -> bool:
        """Check if actor can create a chat thread."""
        if actor.get("role") in ("admin", "super_admin"):
            return True
        if actor.get("role") == "employee":
            return True
        return False

    @staticmethod
    def can_send_message(actor: dict, thread_participants: list[int]) -> bool:
        """Check if actor can send a message to a thread."""
        if thread_participants is None:
            return False
        return actor.get("user_id") in thread_participants

    @staticmethod
    def can_moderate_chat(actor: dict) -> bool:
        """Check if actor can moderate chat."""
        return actor.get("role") in ("admin", "super_admin")