"""Translate routes controller (routers -> controllers -> services).

Declares the HTTP contract with ``core.route_contract`` and delegates
the translation work to ``services.core.translation_service``. Replaces the
hand-written ``routers/translate.py`` so /api/v1/translate is auto-generated.
"""
from fastapi import Request

from core.route_contract import post

from services.core.translation_service import (
    TranslateRequest,
    TranslateResponse,
    translate_texts as translate_texts_svc,
)


@post("/api/v1/translate", deps=["request"], tags=["translate"], response_model=TranslateResponse)
def translate_texts(request: Request, body: TranslateRequest) -> TranslateResponse:
    return translate_texts_svc(body)
