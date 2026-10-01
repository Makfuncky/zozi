"""finance domain — exceptions.

Domain-specific exceptions for the finance domain.
Routers catch these and convert to appropriate HTTP responses.
"""
from __future__ import annotations


class FinanceDomainError(Exception):
    """Base exception for finance domain errors."""
    pass


class EntityNotFoundError(FinanceDomainError):
    """Raised when a requested entity does not exist."""
    def __init__(self, entity_type: str, entity_id: int | str | None = None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        msg = f"{entity_type} not found"
        if entity_id is not None:
            msg += f" (id={entity_id})"
        super().__init__(msg)


class InsufficientFundsError(FinanceDomainError):
    """Raised when there are insufficient funds for an operation."""
    def __init__(self, account_id: int, required: float, available: float):
        self.account_id = account_id
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient funds in account {account_id}: "
            f"required {required}, available {available}"
        )


class InvalidStateTransitionError(FinanceDomainError):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, entity_type: str, from_state: str, to_state: str):
        self.entity_type = entity_type
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Cannot transition {entity_type} from '{from_state}' to '{to_state}'"
        )


class PeriodClosedError(FinanceDomainError):
    """Raised when an operation is attempted on a closed fiscal period."""
    def __init__(self, period_id: int):
        self.period_id = period_id
        super().__init__(f"Fiscal period {period_id} is closed")


class GatewayConnectionError(FinanceDomainError):
    """Raised when a payment gateway connection fails."""
    def __init__(self, provider_code: str, reason: str):
        self.provider_code = provider_code
        self.reason = reason
        super().__init__(f"Gateway '{provider_code}' connection failed: {reason}")
