from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from rbac.dependencies import require_feature
from pydantic import BaseModel
from domains.country.ports import translate_text, format_currency


"""Customer comms router — consolidated from 1 source files."""



router = APIRouter(prefix="/api/v1/customer/comms", tags=["customer", "comms"])


# === From chat.py ===
"""Customer chat router — real-time translation service."""


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
    require_feature("comms.notification.read")
    return translate_text(body.text, body.source_lang, body.target_lang)


@router.post("/format-currency")
def chat_format_currency(body: CurrencyFormatBody):
    """Format a currency amount for the given locale."""
    require_feature("comms.notification.read")
    return format_currency(body.amount, body.currency_code, body.locale)

