"""Payment gateway adapter registry.

Central lookup used by ``services/treasury/payment_engine.py`` and
``services/gateways/webhook_processor.py`` to resolve a provider code to its
adapter class. Adapters self-register (via :meth:`PaymentGatewayRegistry.register`
or the :func:`adapter` decorator) so the orchestration layer never imports a
concrete gateway directly.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, Type

from .base import BasePaymentGateway


class PaymentGatewayRegistry:
    """Registry mapping ``provider_code`` -> adapter class."""

    _registry: dict[str, Type[BasePaymentGateway]] = {}

    @classmethod
    def register(
        cls,
        provider_code: str,
        adapter_cls: Type[BasePaymentGateway],
    ) -> Type[BasePaymentGateway]:
        cls._registry[str(provider_code).strip().lower()] = adapter_cls
        return adapter_cls

    @classmethod
    def register_adapter(cls, provider_code: str) -> Callable:
        """Decorator: register an adapter class under ``provider_code``."""

        def _wrap(adapter_cls: Type[BasePaymentGateway]) -> Type[BasePaymentGateway]:
            cls.register(provider_code, adapter_cls)
            return adapter_cls

        return _wrap

    @classmethod
    def get(cls, provider_code: str) -> Optional[Type[BasePaymentGateway]]:
        return cls._registry.get(str(provider_code).strip().lower())

    @classmethod
    def get_or_raise(cls, provider_code: str) -> Type[BasePaymentGateway]:
        adapter_cls = cls.get(provider_code)
        if adapter_cls is None:
            raise KeyError(f"No gateway adapter registered for '{provider_code}'")
        return adapter_cls

    @classmethod
    def list_available(cls) -> list[str]:
        return sorted(cls._registry)

    @classmethod
    def unregister(cls, provider_code: str) -> None:
        cls._registry.pop(str(provider_code).strip().lower(), None)

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()

    @classmethod
    def all(cls) -> dict[str, Type[BasePaymentGateway]]:
        return dict(cls._registry)

    @classmethod
    def build(cls, provider_code: str, *args: Any, **kwargs: Any) -> BasePaymentGateway:
        """Resolve and instantiate the adapter for ``provider_code``."""
        return cls.get_or_raise(provider_code)(*args, **kwargs)
