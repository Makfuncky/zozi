"""
Text Provider
=============
Text processing, embedding, and Ollama chat integration.
Test file: backend/tests/_test_provider/test_text.py
"""
from __future__ import annotations
import base64
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional


class settings:
    ollama_text_model = "gpt-4o-mini"
    ollama_model = "gpt-4o-mini"
    ollama_base_url = "http://localhost:11434"
    finance_ai_timeout = 60

logger = logging.getLogger(__name__)

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
    except Exception as exc:
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
    except Exception as exc:
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
    except Exception as exc:
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
    except Exception as exc:
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
    except Exception as exc:
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