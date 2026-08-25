"""HuggingFace Inference API provider.

Vendor integration for BLIP image captioning and BART zero-shot classification via
the HF Inference API. Extracted from ``services.ai.ai_service`` so the service layer
orchestrates business logic while the provider owns the HTTP/vendor details.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error

import os
import requests

logger = logging.getLogger(__name__)

__all__ = [
    "HF_API_TOKEN",
    "HF_API_BASE",
    "ZERO_SHOT_MODEL",
    "CAPTION_MODEL",
    "call_hf_image_api",
]

HF_API_TOKEN: str = os.environ.get("HF_API_TOKEN", "")  # resolved once at import; empty string -> unauthenticated
HF_API_BASE = "https://api-inference.huggingface.co/models"
ZERO_SHOT_MODEL = "facebook/bart-large-mnli"
CAPTION_MODEL = "Salesforce/blip-image-captioning-base"

_HF_HEADERS = lambda: {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
_TRANSIENT_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


def _post_hf_request(
    model: str,
    *,
    json: "Optional[dict]" = None,
    data: "Optional[bytes]" = None,
    timeout: int = 15,
    extra_headers: "Optional[dict]" = None,
    attempts: int = 3,
):
    last_error: "Optional[Exception]" = None
    last_response = None

    for attempt in range(attempts):
        try:
            response = requests.post(
                f"{HF_API_BASE}/{model}",
                headers={**_HF_HEADERS(), **(extra_headers or {})},
                json=json,
                data=data,
                timeout=timeout,
            )
            if response.status_code == 200:
                return response
            last_response = response
            if response.status_code not in _TRANSIENT_STATUS_CODES:
                return response
        except (
            urllib.error.URLError,
            requests.exceptions.RequestException,
            TimeoutError,
            OSError,
        ) as exc:
            last_error = exc

        if attempt < attempts - 1:
            time.sleep(0.4 * (attempt + 1))

    if last_error:
        raise last_error
    return last_response


def _blip_caption(image_bytes: bytes) -> str:
    """Call BLIP image captioning via HF Inference API."""
    try:
        resp = _post_hf_request(
            CAPTION_MODEL,
            data=image_bytes,
            timeout=30,
            extra_headers={"Content-Type": "application/octet-stream"},
        )
        if resp is not None and resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
            if isinstance(data, dict):
                return data.get("generated_text", "")
    except (
        urllib.error.URLError,
        requests.exceptions.RequestException,
        json.JSONDecodeError,
        TimeoutError,
        ValueError,
        OSError,
    ) as exc:
        if _is_transient_hf_error(exc):
            logger.debug("BLIP caption unavailable after retries; using fallback inference: %s", exc)
        else:
            logger.warning("BLIP caption failed: %s", exc)
    return ""


def _zero_shot_classify(text: str, labels: "list[str]") -> str:
    """Run zero-shot classification and return the top label."""
    if not text.strip():
        return ""
    try:
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": labels},
        }
        resp = _post_hf_request(ZERO_SHOT_MODEL, json=payload, timeout=15)
        if resp is not None and resp.status_code == 200:
            data = resp.json()
            labels_out = data.get("labels", [])
            if labels_out:
                return labels_out[0]
    except (
        urllib.error.URLError,
        requests.exceptions.RequestException,
        json.JSONDecodeError,
        TimeoutError,
        ValueError,
        OSError,
    ) as exc:
        logger.warning("Zero-shot classification failed: %s", exc)
    return ""


def call_hf_image_api(model: str, image_bytes: bytes, timeout: int = 60) -> "Optional[bytes]":
    """POST raw image bytes to an HF Inference API endpoint; return image bytes on success.

    Wraps the HF HTTP transport so callers in the image services never perform
    raw vendor HTTP. Returns ``None`` on any failure or non-image response.
    """
    try:
        resp = _post_hf_request(
            model,
            data=image_bytes,
            timeout=timeout,
            extra_headers={"Content-Type": "application/octet-stream"},
            attempts=1,
        )
        if resp is None:
            return None
        ct = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "image" in ct:
            return resp.content
        if resp.status_code == 410:
            logger.debug("HF model %s: HTTP 410 (removed from free tier)", model)
        elif resp.status_code == 503:
            logger.warning("HF model %s: 503 (loading); try again shortly", model)
        else:
            logger.warning("HF model %s: HTTP %d — %.200s", model, resp.status_code, resp.text)
    except (
        urllib.error.URLError,
        requests.exceptions.RequestException,
        TimeoutError,
        OSError,
    ) as exc:
        logger.warning("HF model %s: %s", model, exc)
    return None


def _is_transient_hf_error(exc: Exception) -> bool:
    message = str(exc).lower()
    transient_fragments = (
        "incompleteread",
        "connection broken",
        "connection aborted",
        "connection reset",
        "read timed out",
        "timed out",
        "temporary failure",
        "remote end closed connection",
        "503",
        "504",
        "502",
        "429",
    )
    return any(fragment in message for fragment in transient_fragments)

