"""
Real-time Translation Service
Features: Multi-language chat translation, locale formatting
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("zozi.translation")


class TranslationService:
    """Provides real-time translation for chat messages."""
    
    SUPPORTED_LANGUAGES = ["en", "ar", "ur", "es", "fr", "de", "id", "ms", "bn", "hi"]
    CURRENCY_SYMBOLS = {
        "USD": "$", "EUR": "€", "GBP": "£", "OMR": "ر.ع.", "SAR": "﷼",
        "AED": "د.إ", "KWD": "د.ك", "QAR": "ق.ر", "BHD": "ب.ح"
    }
    
    @staticmethod
    def translate(text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate text between languages (placeholder for AI integration)."""
        if source_lang == target_lang:
            return {"translated": text, "source": source_lang, "target": target_lang}
        
        translations = {
            ("en", "ar"): "[AR] " + text,
            ("ar", "en"): "[EN] " + text,
            ("en", "ur"): "[UR] " + text,
            ("ur", "en"): "[EN] " + text,
        }
        
        key = (source_lang, target_lang)
        translated = translations.get(key, f"[{target_lang.upper()}] {text}")
        
        return {
            "translated": translated,
            "source": source_lang,
            "target": target_lang,
            "original": text
        }
    
    @staticmethod
    def format_currency(amount: float, currency_code: str, locale: str) -> str:
        """Format currency for locale."""
        symbol = TranslationService.CURRENCY_SYMBOLS.get(currency_code, currency_code)
        if locale in ("ar", "ar-SA", "ar-OM"):
            return f"{symbol} {amount:,.2f}"
        return f"{amount:,.2f} {symbol}"
    
    @staticmethod
    def format_date(date_str: str, locale: str) -> str:
        """Format date for locale."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if locale.startswith("ar"):
                return dt.strftime("%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str


class ChatTranslationMiddleware:
    """Middleware for real-time chat translation."""
    
    def __init__(self, db=None):
        self.db = db
        self.translator = TranslationService()
    
    def process_message(
        self,
        message: str,
        sender_locale: str,
        recipient_locale: str,
        sender_currency: str = "USD"
    ) -> Dict[str, Any]:
        """Process message for translation and formatting."""
        result = {
            "original": message,
            "sender_locale": sender_locale,
            "recipient_locale": recipient_locale
        }
        
        if sender_locale != recipient_locale:
            translated = self.translator.translate(
                message, sender_locale, recipient_locale
            )
            result["translated"] = translated["translated"]
        else:
            result["translated"] = message
        
        return result


def get_translation_service():
    return TranslationService()
