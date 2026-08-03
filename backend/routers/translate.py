"""
/translate â€” Batch text translation endpoint.
Uses deep-translator (free Google Translate wrapper; no API key required).
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import logging

from utils.rate_limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


class TranslateRequest(BaseModel):
    texts: list[str]
    target: str = "ar"   # ISO 639-1 code: "ar", "en", etc.
    source: str = "en"


class TranslateResponse(BaseModel):
    translations: list[str]


@limiter.limit("20/minute")
@router.post("", response_model=TranslateResponse)
def translate_texts(request: Request, body: TranslateRequest) -> TranslateResponse:
    """
    Translate an array of strings to the target language.
    English â†’ Arabic is the primary use-case.
    Returns the same array (untranslated) if target == source.
    """
    if not body.texts:
        return TranslateResponse(translations=[])

    # If already the same language, return as-is
    if body.target == body.source:
        return TranslateResponse(translations=body.texts)

    try:
        from deep_translator import GoogleTranslator  # lazy import

        translator = GoogleTranslator(source=body.source, target=body.target)
        results: list[str] = []

        for text in body.texts:
            if not text or not text.strip():
                results.append(text)
                continue
            try:
                translated = translator.translate(text)
                results.append(translated if translated else text)
            except Exception as exc:
                logger.warning("Translation failed for text %r: %s", text[:50], exc)
                results.append(text)  # fall back to original

        return TranslateResponse(translations=results)

    except ImportError:
        logger.error("deep-translator not installed. Run: pip install deep-translator")
        # Graceful degradation â€” return originals so the UI stays functional
        return TranslateResponse(translations=body.texts)
    except Exception as exc:
        logger.error("Translation service error: %s", exc)
        return TranslateResponse(translations=body.texts)

