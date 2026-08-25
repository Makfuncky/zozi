"""Customer comms router — consolidated from 1 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/customer/comms", tags=["customer", "comms"])


# === From chat.py ===
"""Customer chat router — real-time translation service."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from domains.comms.services._auto_stubs import TranslationService

class TranslateBody(BaseModel):
    text: str
    source_lang: str = "en"
    target_lang: str = "ar"


class CurrencyFormatBody(BaseModel):
    amount: float
    currency_code: str = "USD"
    locale: str = "en"


# ── Translation ─────────────────────────────────────────────────────────────────

@router.post("/translate")
def chat_translate(body: TranslateBody):
    """Translate chat message text between languages."""
    return TranslationService.translate(body.text, body.source_lang, body.target_lang)


@router.post("/format-currency")
def chat_format_currency(body: CurrencyFormatBody):
    """Format a currency amount for the given locale."""
    return {
        "formatted": TranslationService.format_currency(body.amount, body.currency_code, body.locale),
        "amount": body.amount,
        "currency_code": body.currency_code,
        "locale": body.locale,
    }

