from typing import Optional

from services.payments.base import BasePaymentGateway, PaymentResult


_registries: dict[str, type[BasePaymentGateway]] = {}


def register_gateway(gateway_id: str):
    def decorator(cls: type[BasePaymentGateway]) -> type[BasePaymentGateway]:
        _registries[gateway_id] = cls
        return cls
    return decorator


class PaymentGatewayRegistry:
    @classmethod
    def list_available(cls) -> list[str]:
        return list(_registries.keys())
    
    @classmethod
    def get(cls, gateway_id: str) -> Optional[type[BasePaymentGateway]]:
        return _registries.get(gateway_id)
    
    @classmethod
    def get_or_raise(cls, gateway_id: str) -> type[BasePaymentGateway]:
        result = cls.get(gateway_id)
        if result is None:
            raise ValueError(f"Gateway '{gateway_id}' not found")
        return result
    
    @classmethod
    def is_supported(cls, gateway_id: str) -> bool:
        return gateway_id in _registries