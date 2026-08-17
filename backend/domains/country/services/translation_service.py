"""Translation service (routers -> controllers -> services).

Wraps the free Google Translate implementation (deep-translator). Degrades
gracefully to the original text if translation is unavailable so the UI stays
functional.
"""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TranslateRequest(BaseModel):
    texts: List[str]
    target: str = "ar"
    source: str = "en"


class TranslateResponse(BaseModel):
    translations: List[str]


def translate_texts(body: TranslateRequest) -> TranslateResponse:
    if not body.texts:
        return TranslateResponse(translations=[])

    if body.target == body.source:
        return TranslateResponse(translations=body.texts)

    try:
        from deep_translator import GoogleTranslator  # lazy import

        translator = GoogleTranslator(source=body.source, target=body.target)
        results: List[str] = []
        for text in body.texts:
            if not text or not text.strip():
                results.append(text)
                continue
            try:
                translated = translator.translate(text)
                results.append(translated if translated else text)
            except Exception as exc:
                logger.warning("Translation failed for text %r: %s", text[:50], exc)
                results.append(text)
        return TranslateResponse(translations=results)

    except ImportError:
        logger.error("deep-translator not installed. Run: pip install deep-translator")
        return TranslateResponse(translations=body.texts)
    except Exception as exc:
        logger.error("Translation service error: %s", exc)
        return TranslateResponse(translations=body.texts)
