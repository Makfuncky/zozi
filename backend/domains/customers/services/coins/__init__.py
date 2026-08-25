"""customers/coins sub-domain — zozi coins earning and redemption services."""
from __future__ import annotations

from domains.customers.services.coins.zozi_coins_service import (
    COINS_PER_REFERRAL,
    COINS_PURCHASE_PERCENTAGE,
    MIN_PURCHASE_FOR_COINS,
    MAX_COINS_PER_TRANSACTION,
    get_customer_balance,
    get_coin_history,
    award_referral_coins,
    award_purchase_coins,
    redeem_coins,
    get_coin_summary,
)

__all__ = [
    "COINS_PER_REFERRAL",
    "COINS_PURCHASE_PERCENTAGE",
    "MIN_PURCHASE_FOR_COINS",
    "MAX_COINS_PER_TRANSACTION",
    "get_customer_balance",
    "get_coin_history",
    "award_referral_coins",
    "award_purchase_coins",
    "redeem_coins",
    "get_coin_summary",
]
