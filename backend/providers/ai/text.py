from __future__ import annotations

"""
Text Provider
=============
Text processing, embedding, and Ollama chat integration.
Test file: backend/tests/_test_provider/test_text.py
"""
import base64
import json
import logging
import re
import time
import urllib.error
from typing import Any, Dict, List, Optional

from ..config import settings

logger = logging.getLogger(__name__)

__all__ = [
    "_ollama_chat",
    "_ollama_vision_chat",
    "_OLLAMA_TEXT_MODEL",
    "_OLLAMA_VISION_MODEL",
    "transcribe_audio",
    "embed_text",
    "cosine_similarity",
    "_extract_json",
    "_extract_variant_from_text",
    "_extract_product_name",
    "_extract_tags",
    "translate_en_to_ar",
    "_ollama_chat_completion",
    "ollama_chat_json",
]

_OLLAMA_TEXT_MODEL = settings.ollama_text_model
_OLLAMA_VISION_MODEL = settings.ollama_model

# ============================================================================
# REFERENCE
# ============================================================================
# This module provides text processing capabilities for the Zozi AI provider
# system. It integrates with Ollama for LLM inference and supports:
# - Chat completions (_ollama_chat)
# - Vision/image understanding (_ollama_vision_chat)
# - Speech-to-text transcription (transcribe_audio)
# - Text embedding generation (embed_text)
# - JSON extraction with phi3:mini fallback fixes
# - Product variant and tag extraction
#
# Test file: backend/tests/_test_provider/test_text.py
# Run: python -m pytest backend/tests/_test_provider/test_text.py -v


def _ollama_chat(prompt: str, model: Optional[str] = None) -> str:
    """Send a chat prompt to Ollama and return the response text.

    Args:
        prompt: The user prompt to send.
        model: Optional Ollama model name. Defaults to _OLLAMA_TEXT_MODEL.

    Returns:
        The model's response text, or an empty string on failure.
    """
    import urllib.request

    model_name = model or _OLLAMA_TEXT_MODEL
    url = f"{settings.ollama_base_url}/api/generate"

    payload = json.dumps({
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 2048,
        },
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=settings.finance_ai_timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, ValueError, OSError) as exc:
        logger.error("Ollama chat failed: %s", exc)
        return ""


def _ollama_vision_chat(prompt: str, image_bytes: bytes, model: Optional[str] = None) -> str:
    """Send a vision prompt with an image to Ollama and return the response text.

    Args:
        prompt: The user prompt to send.
        image_bytes: Raw image bytes.
        model: Optional Ollama model name. Defaults to settings.ollama_model.

    Returns:
        The model's response text, or an empty string on failure.
    """
    import urllib.request

    model_name = model or _OLLAMA_VISION_MODEL
    url = f"{settings.ollama_base_url}/api/generate"

    payload = json.dumps({
        "model": model_name,
        "prompt": prompt,
        "images": [base64.b64encode(image_bytes).decode("utf-8")],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 2048,
        },
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=settings.finance_ai_timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, ValueError, OSError) as exc:
        logger.error("Ollama vision chat failed: %s", exc)
        return ""


def transcribe_audio(audio_bytes: bytes, model: Optional[str] = None) -> str:
    """Transcribe audio bytes to text using Ollama whisper or local STT.

    Supports two modes:
    1. Ollama whisper: Uses Ollama's /api/generate with a whisper model
    2. SpeechRecognition: Falls back to Google STT if available

    Args:
        audio_bytes: Raw audio bytes (WAV, MP3, etc.).
        model: Optional model name (e.g., 'whisper:small', 'whisper:base').

    Returns:
        Transcribed text string, or empty string on failure.
    """
    import urllib.request

    model_name = model or "whisper:small"
    url = f"{settings.ollama_base_url}/api/generate"

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    payload = json.dumps({
        "model": model_name,
        "prompt": "Transcribe the following audio to text:",
        "images": [audio_b64],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, ValueError, OSError) as exc:
        logger.warning("Ollama whisper failed (%s), trying local fallback", exc)

    # Fallback: SpeechRecognition library
    try:
        import io
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)
    except ImportError:
        logger.warning("speech_recognition not installed, STT unavailable")
    except (sr.UnknownValueError, sr.RequestError, OSError, ValueError) as exc:
        logger.error("Speech recognition failed: %s", exc)

    return ""


def embed_text(text: str, model: Optional[str] = None) -> List[float]:
    """Generate an embedding vector for a text string using Ollama.

    Args:
        text: The text to embed.
        model: Optional embedding model name. Defaults to 'nomic-embed-text'.

    Returns:
        List of floats representing the embedding vector, or empty list on failure.
    """
    import urllib.request

    model_name = model or "nomic-embed-text"
    url = f"{settings.ollama_base_url}/api/embeddings"

    payload = json.dumps({
        "model": model_name,
        "prompt": text,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding", [])
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, ValueError, OSError) as exc:
        logger.error("Embedding generation failed: %s", exc)
        return []


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity score (0-1), or 0 if vectors are invalid.
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from a text string.

    Searches for the first `{...}` or `[...]` block in the text
    and attempts to parse it as JSON. Includes phi3:mini fallback fixes:
    - Escapes unescaped single quotes
    - Fixes Python None/True/False -> JSON null/true/false
    - Removes trailing commas before } or ]
    - Removes JS-style comments

    Args:
        text: The text to search.

    Returns:
        Parsed JSON dict/list, or None if no valid JSON found.
    """
    # Strip markdown code fences first
    if "```" in text:
        text = re.sub(r'```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)

    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # Fix common phi3:mini JSON issues and retry
                        fixed = candidate
                        # Fix unquoted keys (e.g., {name: "value"} -> {"name": "value"})
                        fixed = re.sub(r'(\w+)(?=\s*:)', r'"\1"', fixed)
                        # Fix single quotes to double quotes
                        fixed = re.sub(r"(?<!\\)'", '"', fixed)
                        # Fix Python None/True/False -> JSON null/true/false
                        fixed = re.sub(r'\bNone\b', 'null', fixed)
                        fixed = re.sub(r'\bTrue\b', 'true', fixed)
                        fixed = re.sub(r'\bFalse\b', 'false', fixed)
                        # Remove trailing commas before } or ]
                        fixed = re.sub(r',\s*}', '}', fixed)
                        fixed = re.sub(r',\s*]', ']', fixed)
                        # Remove JS-style comments
                        fixed = re.sub(r'//[^\n]*', '', fixed)
                        try:
                            return json.loads(fixed)
                        except json.JSONDecodeError:
                            continue
    # Last resort: try to extract key-value pairs
    kv = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', text)
    if kv:
        return dict(kv)
    return None


def _extract_variant_from_text(text: str) -> Dict[str, Any]:
    """Extract product variant information from text using pattern matching."""
    import re

    result: Dict[str, Any] = {
        "color": "",
        "size": "",
        "material": "",
        "pattern": "",
        "gender": "",
        "sleeve_length": "",
        "fit": "",
        "neckline": "",
        "hem_length": "",
        "raw_variants": {},
    }

    color_keywords = [
        "black", "white", "red", "blue", "green", "yellow", "orange",
        "purple", "pink", "brown", "grey", "silver", "gold", "beige",
        "navy", "olive", "maroon", "teal", "coral", "ivory", "cream",
        "charcoal", "slate", "burgundy", "ruby", "sapphire", "emerald",
    ]

    size_patterns = [
        r"\b(XS|S|M|L|XL|XXL|XXXL)\b",
        r"\b(\d{2,3})\b",
        r"\b(3[0-9]|4[0-9]|5[0-9])\b",
    ]

    material_keywords = [
        "cotton", "polyester", "leather", "silk", "wool", "denim",
        "linen", "nylon", "spandex", "cashmere", "velvet", "suede",
        "canvas", "rubber", "plastic", "metal", "wood", "glass",
        "ceramic", "stainless steel", "aluminum", "carbon fiber",
    ]

    text_lower = text.lower()

    for color in color_keywords:
        if color in text_lower:
            result["color"] = color.capitalize()
            break

    for pattern in size_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["size"] = match.group(1)
            break

    for material in material_keywords:
        if material in text_lower:
            result["material"] = material.capitalize()
            break

    result["raw_variants"] = {
        "color": result["color"],
        "size": result["size"],
        "material": result["material"],
    }

    return result


def _extract_product_name(text: str) -> str:
    """Extract product name from text."""
    lines = text.strip().split("\n")
    if lines:
        return lines[0].strip()
    return ""


def _extract_tags(text: str, category: str = "") -> List[str]:
    """Extract relevant tags from text."""
    import re

    tags: List[str] = []
    text_lower = text.lower()

    tag_patterns = {
        "electronics": ["wireless", "smart", "portable", "rechargeable", "bluetooth", "usb"],
        "fashion": ["fashion", "everyday", "comfort", "style", "casual", "formal"],
        "home": ["durable", "eco-friendly", "modern", "minimalist", "rustic"],
        "sports": ["breathable", "waterproof", "lightweight", "performance"],
        "beauty": ["skincare", "natural", "organic", "hydrating"],
    }

    category_tags = tag_patterns.get(category.lower(), [])
    for tag in category_tags:
        if tag in text_lower:
            tags.append(tag)

    return tags


# ============================================================================
# Translation (shifted from domains.comms.services.content_service)
# ============================================================================
# External LLM/provider code belongs in ``providers/``. This keeps the Ollama
# translation implementation out of the services layer. Behavior is preserved
# exactly: Ollama (OpenAI-compatible chat completions) first, curated
# EN→AR glossary fallback so the feature never hard-fails.

_OLLAMA_TRANSLATE_BASE_URL = settings.ollama_base_url
_OLLAMA_TRANSLATE_MODEL = "phi3:mini"

# Curated EN→AR glossary for the fallback translator (common e-commerce terms).
_TRANSLATE_GLOSSARY = {
    "product": "منتج", "products": "منتجات", "price": "السعر", "new": "جديد",
    "sale": "تخفيض", "free": "مجاني", "shipping": "شحن", "delivery": "توصيل",
    "fast": "سريع", "premium": "ممتاز", "quality": "جودة", "red": "أحمر",
    "blue": "أزرق", "black": "أسود", "white": "أبيض", "green": "أخضر",
    "size": "المقاس", "color": "اللون", "colour": "اللون", "warranty": "ضمان",
    "available": "متوفر", "order": "اطلب", "best": "الأفضل", "discount": "خصم",
    "offer": "عرض", "buy": "اشترِ", "watch": "ساعة", "phone": "هاتف",
    "dress": "فستان", "shirt": "قميص", "shoes": "أحذية", "bag": "حقيبة",
    "gold": "ذهبي", "silver": "فضي", "cotton": "قطني", "leather": "جلدي",
    "waterproof": "مقاوم للماء", "original": "أصلي", "style": "ستايل",
}


def _translate_glossary_fallback(text: str) -> str:
    """Word-by-word substitution using the curated glossary (keeps structure)."""
    import re

    parts = re.split(r"(\s+)", text)
    out: List[str] = []
    for part in parts:
        low = part.lower().strip(".,!?;:")
        out.append(_TRANSLATE_GLOSSARY.get(low, part))
    return "".join(out)


async def translate_en_to_ar(text: str) -> str:
    """Translate English text to Arabic. Ollama first, glossary fallback.

    Shifted from ``services.comms.content_service`` so provider/SDK code lives
    in ``providers/``. Behavior preserved exactly.
    """
    if not text or not text.strip():
        return ""
    try:
        import httpx  # noqa: F401

        prompt = (
            "Translate the following e-commerce product text into Arabic (Modern "
            "Standard Arabic). Reply with ONLY the Arabic translation, no quotes, "
            "no explanation:\n\n" + text
        )
        payload = {
            "model": _OLLAMA_TRANSLATE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "stream": False,
            "options": {"num_predict": 500, "keep_alive": "5m"},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_OLLAMA_TRANSLATE_BASE_URL}/v1/chat/completions", json=payload
            )
            if resp.status_code == 200:
                out = resp.json()["choices"][0]["message"]["content"].strip().strip('"')
                if out:
                    return out
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        logger.info("providers.text: Ollama translation unavailable (%s)", exc)
    return _translate_glossary_fallback(text)


async def _ollama_chat_completion(
    base_url: str,
    model: str,
    content: str,
    images: Optional[List[str]] = None,
    num_predict: int = 600,
    temperature: float = 0.2,
    timeout: float = 90.0,
) -> Optional[str]:
    """Low-level Ollama chat completion over the OpenAI-compatible endpoint.

    Builds the request, performs the HTTP call, and returns the assistant
    message text. Returns ``None`` if the model is unreachable or the response
    is unusable so the caller can fall back gracefully.
    """
    try:
        import httpx
    except ImportError:
        return None
    if images:
        content_msg: Any = [
            {"type": "text", "text": content},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{images[0]}"}},
        ]
    else:
        content_msg = content
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content_msg}],
        "temperature": temperature,
        "max_tokens": num_predict,
        "keep_alive": "5m",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{base_url}/v1/chat/completions", json=payload)
            if resp.status_code != 200:
                return None
            return resp.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None


def ollama_chat_json(
    prompt: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    *,
    timeout: float = 900.0,
    temperature: float = 0.2,
    num_ctx: int = 8192,
) -> Dict[str, Any]:
    """Generate a structured JSON object from an Ollama ``/api/chat`` call.

    Shifted from ``services.ai.country_ai_research`` so the Ollama vendor HTTP
    call lives in ``providers/``. On any failure (unreachable, invalid JSON,
    provider error) a ``RuntimeError`` is raised so the caller can fall back.
    """
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - httpx is a hard dep of services
        raise RuntimeError("httpx is required for Ollama chat") from exc

    model_name = model or _OLLAMA_TEXT_MODEL
    url = f"{(base_url or settings.ollama_base_url).rstrip('/')}/api/chat"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature, "num_ctx": num_ctx},
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    content = data.get("message", {}).get("content", "")
    parsed = _extract_json(content)
    if parsed is None:
        raise RuntimeError("Ollama returned invalid JSON.")
    return parsed