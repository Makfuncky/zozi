from typing import Optional

from pydantic import BaseModel, Field


class PaymentResult(BaseModel):
    success: bool
    transaction_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[dict] = None


class ConnectionTestResult(PaymentResult):
    gateway_id: Optional[str] = None
    response_time_ms: Optional[float] = None


class RefundResult(BaseModel):
    success: bool
    refund_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class BasePaymentGateway:
    display_name: str = "Base Gateway"
    supported_countries: list[str] = []
    
    def validate_credentials(self, credentials: dict) -> bool:
        return bool(credentials)
    
    def process_payment(
        self,
        amount: float,
        currency: str,
        credentials: dict,
        *,
        order_id: Optional[int] = None,
        description: str = "",
        customer: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        return PaymentResult(success=False, error_code="not_implemented", error_message="Gateway not implemented")
    
    def process_refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        credentials: Optional[dict] = None,
        *,
        reason: str = "",
    ) -> RefundResult:
        return RefundResult(success=False, refund_id=None, error_code="not_implemented", error_message="Gateway not implemented")
    
    def test_connection(self, credentials: dict) -> ConnectionTestResult:
        return ConnectionTestResult(
            success=False,
            error_code="not_implemented",
            error_message="Gateway not implemented"
        )