from __future__ import annotations

"""
Recommendation Engine Provider
==============================
Content-based and collaborative filtering for product recommendations.
Pure Python implementation using TF-IDF + cosine similarity.
"""
import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

HAS_RECOMMENDATION = True

__all__ = [
    "get_product_recommendations",
    "get_similar_products",
    "get_frequently_bought_together",
]


def _tokenize(text: str) -> List[str]:
    """Lowercase and split text into alphanumeric tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _build_tfidf_vectors(corpus: List[List[str]]) -> List[Dict[str, float]]:
    """Build TF-IDF vectors for a corpus of tokenized documents.

    Args:
        corpus: List of token lists, one per document.

    Returns:
        List of dicts mapping token -> tfidf weight.
    """
    n_docs = len(corpus)
    if n_docs == 0:
        return []

    # Document frequency per token
    df: Counter = Counter()
    for doc in corpus:
        df.update(set(doc))

    # IDF with smoothing
    idf: Dict[str, float] = {}
    for token, freq in df.items():
        idf[token] = math.log((1 + n_docs) / (1 + freq)) + 1.0

    # TF-IDF vectors
    vectors: List[Dict[str, float]] = []
    for doc in corpus:
        tf: Counter = Counter(doc)
        max_tf = max(tf.values()) if tf else 1
        vec: Dict[str, float] = {}
        for token, count in tf.items():
            normalized_tf = 0.5 + 0.5 * (count / max_tf)
            vec[token] = normalized_tf * idf.get(token, 0.0)
        vectors.append(vec)
    return vectors


def _cosine_similarity_vec(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors (dict representation)."""
    if not a or not b:
        return 0.0
    common = set(a.keys()) & set(b.keys())
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _product_text(product: Dict[str, Any]) -> str:
    """Build searchable text from a product dict."""
    parts: List[str] = []
    for key in ("name", "category", "description", "brand"):
        val = product.get(key)
        if val:
            parts.append(str(val))
    tags = product.get("tags", [])
    if isinstance(tags, list):
        parts.extend(str(t) for t in tags)
    return " ".join(parts)


def get_product_recommendations(
    product_id: int,
    user_history: List[int],
    all_products: List[Dict[str, Any]],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Get ranked product recommendations using content-based + collaborative signals.

    Combines:
    - Content-based filtering (tags, category, name similarity)
    - Collaborative signal from user_history (products the user interacted with)

    Args:
        product_id: The reference product ID.
        user_history: List of product IDs the user has viewed/purchased.
        all_products: Full product catalog as list of dicts.
        limit: Maximum number of recommendations.

    Returns:
        List of recommended product dicts with 'score' key, sorted descending.
    """
    if not all_products:
        return []

    # Find the target product
    target: Optional[Dict[str, Any]] = None
    for p in all_products:
        if p.get("id") == product_id:
            target = p
            break

    # Build TF-IDF corpus
    corpus = [_tokenize(_product_text(p)) for p in all_products]
    vectors = _build_tfidf_vectors(corpus)

    scores: Dict[int, float] = {}

    # Content-based signal: similarity to the target product
    if target is not None:
        target_idx = next(
            (i for i, p in enumerate(all_products) if p.get("id") == product_id),
            None,
        )
        if target_idx is not None:
            target_vec = vectors[target_idx]
            for i, vec in enumerate(vectors):
                if i == target_idx:
                    continue
                sim = _cosine_similarity_vec(target_vec, vec)
                pid = all_products[i].get("id")
                if pid is not None:
                    scores[pid] = scores.get(pid, 0.0) + sim * 0.6

    # Collaborative signal: similarity to user history products
    if user_history:
        history_indices = [
            i for i, p in enumerate(all_products) if p.get("id") in set(user_history)
        ]
        for i, vec in enumerate(vectors):
            pid = all_products[i].get("id")
            if pid is None or pid in set(user_history) or pid == product_id:
                continue
            max_sim = 0.0
            for hi in history_indices:
                sim = _cosine_similarity_vec(vec, vectors[hi])
                if sim > max_sim:
                    max_sim = sim
            scores[pid] = scores.get(pid, 0.0) + max_sim * 0.4

    # If no target found, use collaborative-only scoring
    if target is None and user_history:
        pass  # scores already populated

    # Build result list
    results: List[Dict[str, Any]] = []
    for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        product = next((p for p in all_products if p.get("id") == pid), None)
        if product:
            rec = dict(product)
            rec["score"] = round(score, 6)
            results.append(rec)
        if len(results) >= limit:
            break

    return results


def get_similar_products(
    product_id: int,
    products: List[Dict[str, Any]],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Find similar products based on category, tags, and name similarity.

    Uses TF-IDF + cosine similarity over product text.

    Args:
        product_id: The reference product ID.
        products: Product catalog as list of dicts.
        limit: Maximum number of results.

    Returns:
        List of similar product dicts with 'score' key.
    """
    if not products:
        return []

    corpus = [_tokenize(_product_text(p)) for p in products]
    vectors = _build_tfidf_vectors(corpus)

    target_idx = next(
        (i for i, p in enumerate(products) if p.get("id") == product_id),
        None,
    )
    if target_idx is None:
        return []

    target_vec = vectors[target_idx]
    scored: List[tuple] = []
    for i, vec in enumerate(vectors):
        if i == target_idx:
            continue
        sim = _cosine_similarity_vec(target_vec, vec)
        scored.append((sim, i))

    scored.sort(key=lambda x: x[0], reverse=True)

    results: List[Dict[str, Any]] = []
    for sim, idx in scored[:limit]:
        rec = dict(products[idx])
        rec["score"] = round(sim, 6)
        results.append(rec)
    return results


def get_frequently_bought_together(
    product_id: int,
    orders: List[List[int]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Market basket analysis from order history.

    Finds products that frequently appear in orders containing the given product.

    Args:
        product_id: The reference product ID.
        orders: List of orders, where each order is a list of product IDs.
        limit: Maximum number of results.

    Returns:
        List of dicts with 'product_id', 'frequency', 'confidence', 'support'.
    """
    if not orders:
        return []

    # Count co-occurrences
    co_counter: Counter = Counter()
    total_orders = 0
    product_orders = 0

    for order in orders:
        unique_order = set(order)
        if product_id in unique_order:
            product_orders += 1
            for pid in unique_order:
                if pid != product_id:
                    co_counter[pid] += 1
        total_orders += 1

    if product_orders == 0:
        return []

    results: List[Dict[str, Any]] = []
    for co_pid, freq in co_counter.most_common(limit):
        results.append({
            "product_id": co_pid,
            "frequency": freq,
            "confidence": round(freq / product_orders, 6),
            "support": round(freq / total_orders, 6) if total_orders > 0 else 0.0,
        })
    return results
