"""Slug generation helpers."""
from __future__ import annotations

import hashlib
import re
import unicodedata


def generate_slug(text: str, max_length: int = 80) -> str:
    """Generate a URL-friendly slug from arbitrary text."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug or "item"


def generate_slug_hash(text: str) -> str:
    """Generate a short deterministic hash for slug uniqueness checks."""
    base = generate_slug(text)
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return digest[:12]
