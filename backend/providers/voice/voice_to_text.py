from __future__ import annotations

"""
Voice to Text Provider
======================
Voice processing for product and finance commands.
Test file: backend/tests/_test_provider/test_voice_to_text.py
"""
import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional

from .config import settings

logger = logging.getLogger(__name__)

_OLLAMA_WHISPER_MODEL = "whisper:small"
_OLLAMA_TEXT_MODEL = settings.ollama_text_model

_VariantKeywords = {
    "color": ["black", "white", "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "grey", "silver", "gold", "beige", "navy", "olive", "maroon", "teal", "coral", "ivory", "cream", "charcoal", "slate", "burgundy", "ruby", "sapphire", "emerald"],
    "size": ["xs", "s", "m", "l", "xl", "xxl", "xxxl", "small", "medium", "large", "extra small", "extra large"],
    "material": ["cotton", "polyester", "leather", "silk", "wool", "denim", "linen", "nylon", "spandex", "cashmere", "velvet", "suede", "canvas"],
}

_FinanceKeywords = {
    "expense": ["expense", "bill", "receipt", "invoice", "payment", "cost", "price", "amount", "total", "purchase"],
    "asset": ["asset", "property", "equipment", "inventory", "stock", "investment"],
    "task": ["task", "do", "process", "record", "log", "update", "create", "add", "remove"],
}


def transcribe_audio(audio_bytes: bytes, model: Optional[str] = None) -> str:
    """Transcribe audio bytes to text using Ollama whisper model.

    Args:
        audio_bytes: Raw audio bytes (WAV, MP3, etc.).
        model: Optional whisper model name. Defaults to 'whisper:small'.

    Returns:
        Transcribed text string, or empty string on failure.
    """
    import urllib.request

    model_name = model or _OLLAMA_WHISPER_MODEL
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
        logger.warning("Ollama whisper transcription failed (%s), returning empty", exc)

    return ""


def process_product_voice_command(transcript: str) -> Dict[str, Any]:
    """Process a product-related voice command to extract variant and quantity info.

    Args:
        transcript: The transcribed voice text.

    Returns:
        Dict with extracted fields: product_name, color, size, material, quantity, action.
    """
    result: Dict[str, Any] = {
        "product_name": "",
        "color": "",
        "size": "",
        "material": "",
        "quantity": 1,
        "action": "add",
        "raw_text": transcript,
    }

    if not transcript.strip():
        return result

    transcript_lower = transcript.lower()

    # Extract quantity - explicit "quantity N" or "N [unit]" patterns override each other
    explicit_qty = re.search(r'(?:quantity|qty)\s*(\d+)', transcript_lower)
    if explicit_qty:
        result["quantity"] = int(explicit_qty.group(1))
    else:
        first_qty = re.search(r'\b(\d+)\s*(?:pieces?|units?|items?|pcs|boxes?|bags?|sets?)', transcript_lower)
        if first_qty:
            result["quantity"] = int(first_qty.group(1))
        else:
            fallback_qty = re.search(r'\b(\d+)\b', transcript_lower)
            if fallback_qty:
                result["quantity"] = int(fallback_qty.group(1))

    # Extract action keywords
    if any(w in transcript_lower for w in ["remove", "delete", "drop", "subtract", "take away"]):
        result["action"] = "remove"
    elif any(w in transcript_lower for w in ["update", "change", "modify", "edit"]):
        result["action"] = "update"
    else:
        result["action"] = "add"

    # Extract variant info
    for variant_type, keywords in _VariantKeywords.items():
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, transcript_lower):
                result[variant_type] = keyword.capitalize() if variant_type != "size" else keyword.upper()
                break

    # Extract product name
    words = transcript.split()
    product_words = []
    for word in words:
        w = word.lower().strip(",.;!?")
        if w not in {k for vlist in _VariantKeywords.values() for k in vlist} and not w.isdigit():
            product_words.append(word)
        if len(product_words) >= 5:
            break
    result["product_name"] = " ".join(product_words).strip()

    return result


def process_finance_voice_command(transcript: str) -> Dict[str, Any]:
    """Process a finance-related voice command to extract task info.

    Args:
        transcript: The transcribed voice text.

    Returns:
        Dict with extracted fields: task_type, amount, category, description, action.
    """
    result: Dict[str, Any] = {
        "task_type": "",
        "amount": 0.0,
        "currency": "USD",
        "category": "",
        "description": "",
        "action": "record",
        "raw_text": transcript,
    }

    if not transcript.strip():
        return result

    transcript_lower = transcript.lower()

    # Extract amount
    amount_match = re.search(r'(?:\$|USD|rs|₹|€|£)?\s*(\d+(?:[.,]\d{1,2})?)\s*(?:dollars?|usd|rupees|rs|yuan|eur|pounds?)?', transcript_lower)
    if amount_match:
        amount_str = amount_match.group(1).replace(",", ".")
        try:
            result["amount"] = float(amount_str)
        except ValueError:
            pass

    # Extract task type based on keywords
    for task_type, keywords in _FinanceKeywords.items():
        for keyword in keywords:
            if keyword in transcript_lower:
                result["task_type"] = task_type
                break
        if result["task_type"]:
            break

    # Extract action
    if any(w in transcript_lower for w in ["delete", "remove", "cancel", "reverse", "refund"]):
        result["action"] = "delete"
    elif any(w in transcript_lower for w in ["update", "change", "modify", "edit", "correct"]):
        result["action"] = "update"
    else:
        result["action"] = "record"

    # Extract category
    categories = ["office supplies", "travel", "food", "utilities", "rent", "salary", "marketing", "equipment", "services", "shipping", "insurance", "tax", "maintenance"]
    for cat in categories:
        if cat in transcript_lower:
            result["category"] = cat
            break

    # Extract description (first sentence or meaningful content)
    sentences = re.split(r'[.!?]', transcript)
    if sentences:
        result["description"] = sentences[0].strip()[:200]

    return result