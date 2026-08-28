"""governance domain — exceptions.

Domain-specific exceptions for the governance domain.
Routers catch these and convert to appropriate HTTP responses.
"""
from __future__ import annotations


class GovernanceDomainError(Exception):
    """Base exception for governance domain errors."""
    pass


class EntityNotFoundError(GovernanceDomainError):
    """Raised when a requested entity does not exist."""
    def __init__(self, entity_type: str, entity_id: int | str | None = None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        msg = f"{entity_type} not found"
        if entity_id is not None:
            msg += f" (id={entity_id})"
        super().__init__(msg)


class ValidationError(GovernanceDomainError):
    """Raised when input validation fails."""
    def __init__(self, field: str, detail: str):
        self.field = field
        self.detail = detail
        super().__init__(f"{field}: {detail}")


class TicketAccessDeniedError(GovernanceDomainError):
    """Raised when a user tries to access a ticket they don't own."""
    def __init__(self, ticket_id: int, user_id: int):
        self.ticket_id = ticket_id
        self.user_id = user_id
        super().__init__(f"User {user_id} cannot access ticket {ticket_id}")


class InvalidExportParameterError(GovernanceDomainError):
    """Raised when an export parameter is invalid."""
    def __init__(self, param: str, detail: str):
        self.param = param
        self.detail = detail
        super().__init__(f"Invalid export parameter '{param}': {detail}")
