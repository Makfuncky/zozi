"""Domain wrapper for visual (image) and voice search.

Delegates to the image/voice providers so module routers never import
``providers.*`` directly (Law 1: modules -> domains -> infrastructure/providers).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from providers.image import process_image_search
from providers.voice import transcribe_audio


async def process_visual_search(
    image_bytes: bytes,
    db: Any = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Run visual similarity search over an uploaded image.

    ``db`` is accepted for call-site compatibility; the provider computes the
    similarity itself and does not consume the session directly.
    """
    return await process_image_search(image_bytes=image_bytes, limit=limit)


def transcribe_voice_search(audio_bytes: bytes) -> str:
    """Transcribe raw audio bytes to text via the voice provider."""
    return transcribe_audio(audio_bytes)
