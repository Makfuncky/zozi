"""OpenAI API provider.

Vendor HTTP calls to the OpenAI REST API (Whisper transcription, chat
translation) are encapsulated here so the comms service layer stays free of
third-party client code. The service orchestrates through these helpers.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_OPENAI_BASE = "https://api.openai.com/v1"

# Network / decode errors that should degrade gracefully rather than raise.
_RETRYABLE = (
    ValueError, TypeError, KeyError, IndexError, AttributeError,
    RuntimeError, OSError, IOError, EOFError, ImportError, NameError,
    StopIteration, ArithmeticError, AssertionError, UnicodeError,
    NotImplementedError, RecursionError, ReferenceError, SystemError,
    BufferError, LookupError,
)


async def transcribe_audio(audio_bytes: bytes, api_key: str, source_language: str = "en") -> str:
    """Transcribe ``audio_bytes`` via OpenAI Whisper; returns a fallback string on failure."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"model": "whisper-1", "language": source_language}
            resp = await client.post(
                f"{_OPENAI_BASE}/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data,
            )
            if resp.status_code == 200:
                return resp.json().get("text", "")
            logger.warning("Whisper API returned %s: %s", resp.status_code, resp.text)
            return "[transcription error]"
    except _RETRYABLE as exc:
        logger.error("Transcription failed: %s", exc)
        return "[transcription failed]"


async def translate_text(text: str, api_key: str, target_language: str) -> str:
    """Translate ``text`` via OpenAI; returns the original text on failure / no key."""
    if not api_key:
        return text
    if target_language == "en":
        return text
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_OPENAI_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Translate the following text to {target_language}. Return only the translation.",
                        },
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0,
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            return text
    except _RETRYABLE as exc:
        logger.error("Translation failed: %s", exc)
        return text


__all__ = ["transcribe_audio", "translate_text"]
