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
def chat_translate(body: TranslateBody,
    _rf_gate: None = Depends(require_feature("comms.notification.read"))
):
    """Translate chat message text between languages."""
    return translate_text(body.text, body.source_lang, body.target_lang)


@router.post("/format-currency")
def chat_format_currency(body: CurrencyFormatBody,
    _rf_gate: None = Depends(require_feature("comms.notification.read"))
):
    """Format a currency amount for the given locale."""
    return format_currency(body.amount, body.currency_code, body.locale)

