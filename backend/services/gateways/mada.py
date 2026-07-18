from __future__ import annotations

import logging
from typing import Any

from .base import BasePaymentGateway
from .base_models import ConnectionTestResult, PaymentResult, RefundResult

logger = logging.getLogger(__name__)

# Mada is typically processed through another gateway (Stripe, Tap, etc.)
# with Mada-specific card bin ranges. This adapter serves as a
# configuration placeholder for Mada-specific settings, while actual
# processing goes through the underlying gateway.


class MadaAdapter(BasePaymentGateway):
    gateway_id = "mada"
    display_name = "Mada (Saudi Arabia)"

    MADA_BIN_RANGES = [
        "493428", "530906", "531196", "535825", "536023",
        "539000", "543068", "543085", "549993", "554340",
        "555610", "555710", "555750", "555760", "555790",
        "555800", "555810", "555820", "555830", "555840",
        "555850", "555860", "555870", "555880", "555890",
        "555900", "555910", "555920", "555930", "555940",
        "555950", "555960", "555970", "555980", "555990",
        "556000", "556001", "556002", "556003", "556004",
        "556005", "556006", "556007", "556008", "556009",
        "558848", "559300", "559310", "559320", "559330",
        "559340", "559350", "559360", "559370", "559380",
        "559390", "559400", "559410", "559420", "559430",
        "559440", "559450", "559460", "559470", "559480",
        "559490", "559500", "559510", "559520", "559530",
        "559540", "559550", "559560", "559570", "559580",
        "559590", "559600", "559610", "559620", "559630",
        "559640", "559650", "559660", "559670", "559680",
        "559690", "559700", "559710", "559720", "559730",
        "559740", "559750", "559760", "559770", "559780",
        "559790", "559800", "588845", "968301",
    ]

    def is_mada_card(self, card_bin: str) -> bool:
        """Check if a card BIN belongs to Mada."""
        return any(card_bin.startswith(bin_prefix) for bin_prefix in self.MADA_BIN_RANGES)

    def process_payment(
        self,
        amount: float,
        currency: str,
        credentials: dict[str, Any],
        *,
        order_id: int | None = None,
        description: str = "",
        customer: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> PaymentResult:
        return PaymentResult(
            success=False,
            error_code="mada_delegate_required",
            error_message="Mada payments must be routed through an underlying gateway (Stripe/Tap). "
                          "Use mada_adapter.is_mada_card() to detect and route accordingly.",
        )

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        return RefundResult(
            success=False,
            error_code="mada_delegate_required",
            error_message="Mada refunds must be processed through the underlying gateway.",
        )

