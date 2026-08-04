"""Deterministic variant identity (Phase 3b).

A product's physical variants are uniquely identified by the combination of its
axes (size/color/material/pattern/gender), not by a mutable ``sku``/``barcode``
(which are nullable and may be reassigned). We hash the normalized axes into a
stable ``variant_key`` so uploads are idempotent: re-running the same payload
neither creates duplicate rows nor churns primary-key ids (which would orphan
``order_items.variant_id`` references).
"""

import hashlib


def normalize_variant_axis(value) -> str:
    return (value or "").strip().lower()


def compute_variant_key(
    product_id: object,
    size: object = None,
    color: object = None,
    material: object = None,
    pattern: object = None,
    gender: object = None,
) -> str:
    """sha256 of ``product_id|size|color|material|pattern|gender`` (normalized).

    A single-variant product (all axes empty) still yields a unique key per
    ``product_id``.
    """
    axes = [
        normalize_variant_axis(size),
        normalize_variant_axis(color),
        normalize_variant_axis(material),
        normalize_variant_axis(pattern),
        normalize_variant_axis(gender),
    ]
    raw = "|".join([str(product_id), *axes])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

