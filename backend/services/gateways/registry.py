from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Any, ClassVar

from .base import BasePaymentGateway

logger = logging.getLogger(__name__)


class PaymentGatewayRegistry:
    """Auto-discovers and caches all payment gateway adapter classes."""

    _gateways: ClassVar[dict[str, type[BasePaymentGateway]]] = {}
    _discovered: ClassVar[bool] = False

    @classmethod
    def discover(cls) -> None:
        if cls._discovered:
            return
        cls._gateways.clear()
        import services.gateways as gateway_pkg
        path = getattr(gateway_pkg, "__path__", [])
        for importer, modname, ispkg in pkgutil.iter_modules(path):
            if modname in ("base", "base_models", "registry"):
                continue
            try:
                module = importlib.import_module(f".{modname}", __name__)
            except Exception:
                logger.warning("Failed to import gateway module: %s", modname)
                continue
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePaymentGateway)
                    and attr is not BasePaymentGateway
                ):
                    gid = getattr(attr, "gateway_id", None) or modname.lower()
                    cls._gateways[gid] = attr
                    logger.debug("Discovered gateway adapter: %s (id=%s)", attr.__name__, gid)
        cls._discovered = True

    @classmethod
    def get(cls, gateway_id: str) -> type[BasePaymentGateway] | None:
        cls.discover()
        return cls._gateways.get(gateway_id)

    @classmethod
    def get_or_raise(cls, gateway_id: str) -> type[BasePaymentGateway]:
        cls.discover()
        adapter = cls._gateways.get(gateway_id)
        if adapter is None:
            raise ValueError(
                f"Unknown payment gateway: {gateway_id}. "
                f"Available: {', '.join(sorted(cls._gateways))}"
            )
        return adapter

    @classmethod
    def list_available(cls) -> list[str]:
        cls.discover()
        return sorted(cls._gateways)

    @classmethod
    def is_supported(cls, gateway_id: str) -> bool:
        cls.discover()
        return gateway_id in cls._gateways

