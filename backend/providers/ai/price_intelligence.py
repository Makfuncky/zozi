from __future__ import annotations

"""
Price Intelligence Provider
===========================
Price positioning analysis, benchmarking, and suggestions.
Pure Python — no external SDK.
"""
import logging
import math
import statistics
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

HAS_PRICE_INTELLIGENCE = True

__all__ = [
    "get_category_price_benchmarks",
    "analyze_price",
    "suggest_price_range",
]

# Category price benchmarks (min, max, avg in USD)
# These serve as defaults when no historical data is available.
_CATEGORY_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "electronics":    {"min": 5.0, "max": 3000.0, "avg": 350.0, "std": 400.0},
    "fashion":        {"min": 3.0, "max": 500.0,  "avg": 60.0,  "std": 70.0},
    "home":           {"min": 5.0, "max": 2000.0, "avg": 120.0, "std": 200.0},
    "sports":         {"min": 5.0, "max": 800.0,  "avg": 55.0,  "std": 80.0},
    "beauty":         {"min": 2.0, "max": 300.0,  "avg": 35.0,  "std": 40.0},
    "jewelry":        {"min": 10.0, "max": 5000.0, "avg": 250.0, "std": 600.0},
    "toys":           {"min": 3.0, "max": 200.0,  "avg": 30.0,  "std": 30.0},
    "food":           {"min": 1.0, "max": 100.0,  "avg": 12.0,  "std": 15.0},
    "books":          {"min": 3.0, "max": 100.0,  "avg": 18.0,  "std": 15.0},
    "automotive":     {"min": 10.0, "max": 5000.0, "avg": 200.0, "std": 500.0},
    "health":         {"min": 3.0, "max": 500.0,  "avg": 45.0,  "std": 60.0},
    "pet":            {"min": 3.0, "max": 300.0,  "avg": 35.0,  "std": 40.0},
    "garden":         {"min": 5.0, "max": 800.0,  "avg": 60.0,  "std": 90.0},
    "office":         {"min": 3.0, "max": 500.0,  "avg": 40.0,  "std": 60.0},
    "music":          {"min": 5.0, "max": 3000.0, "avg": 150.0, "std": 300.0},
}

# Default benchmark for unknown categories
_DEFAULT_BENCHMARK = {"min": 5.0, "max": 500.0, "avg": 50.0, "std": 75.0}


def get_category_price_benchmarks(category: str) -> Dict[str, Any]:
    """Return price benchmarks for a given category.

    Args:
        category: Product category name (case-insensitive).

    Returns:
        Dict with min, max, avg, std, and percentile_25/75 benchmarks.
    """
    cat_key = category.lower().strip() if category else ""
    bench = _CATEGORY_BENCHMARKS.get(cat_key, _DEFAULT_BENCHMARK)

    # Compute percentile estimates from min/max/avg/std
    avg = bench["avg"]
    std = bench["std"]
    p25 = max(bench["min"], avg - 0.675 * std)
    p75 = min(bench["max"], avg + 0.675 * std)

    return {
        "category": category,
        "min": bench["min"],
        "max": bench["max"],
        "avg": round(avg, 2),
        "std": round(std, 2),
        "percentile_25": round(p25, 2),
        "percentile_75": round(p75, 2),
    }


def analyze_price(
    product_name: str,
    category: str,
    current_price: float,
    competitor_prices: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Analyze price positioning for a product.

    Determines whether the price is premium, budget, or mid-range relative
    to category benchmarks and competitor prices.

    Args:
        product_name: Product name for context.
        product_name: Product name for context.
        category: Product category.
        current_price: The product's current price.
        competitor_prices: Optional list of competitor prices for comparison.

    Returns:
        Dict with positioning, percentile_rank, price_label, and analysis.
    """
    if current_price <= 0:
        return {
            "product_name": product_name,
            "category": category,
            "current_price": current_price,
            "positioning": "invalid",
            "percentile_rank": 0.0,
            "price_label": "invalid",
            "message": "Price must be greater than zero.",
        }

    bench = get_category_price_benchmarks(category)
    min_price = bench["min"]
    max_price = bench["max"]
    avg_price = bench["avg"]
    std_price = bench["std"]

    # Category-based percentile (normal approximation)
    if std_price > 0:
        z_score = (current_price - avg_price) / std_price
        percentile = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))
        percentile_rank = round(percentile * 100, 2)
    else:
        if current_price <= min_price:
            percentile_rank = 0.0
        elif current_price >= max_price:
            percentile_rank = 100.0
        else:
            percentile_rank = round(
                (current_price - min_price) / (max_price - min_price) * 100, 2
            )

    # Competitor-based percentile
    competitor_percentile = None
    if competitor_prices:
        below = sum(1 for p in competitor_prices if current_price > p)
        competitor_percentile = round(below / len(competitor_prices) * 100, 2)

    # Label
    if percentile_rank >= 80:
        price_label = "premium"
    elif percentile_rank >= 60:
        price_label = "above-average"
    elif percentile_rank >= 40:
        price_label = "mid-range"
    elif percentile_rank >= 20:
        price_label = "below-average"
    else:
        price_label = "budget"

    # Positioning relative to category
    if current_price > bench["percentile_75"]:
        positioning = "premium"
    elif current_price > avg_price:
        positioning = "above-average"
    elif current_price > bench["percentile_25"]:
        positioning = "mid-range"
    elif current_price > min_price:
        positioning = "budget"
    else:
        positioning = "entry-level"

    result: Dict[str, Any] = {
        "product_name": product_name,
        "category": category,
        "current_price": current_price,
        "positioning": positioning,
        "price_label": price_label,
        "percentile_rank": percentile_rank,
        "category_benchmarks": bench,
    }

    if competitor_prices:
        result["competitor_analysis"] = {
            "competitor_count": len(competitor_prices),
            "competitor_min": round(min(competitor_prices), 2),
            "competitor_max": round(max(competitor_prices), 2),
            "competitor_avg": round(statistics.mean(competitor_prices), 2),
            "competitor_percentile": competitor_percentile,
            "price_difference_from_avg": round(
                current_price - statistics.mean(competitor_prices), 2
            ),
        }

    return result


def suggest_price_range(
    product_name: str,
    category: str,
    cost_price: float = 0.0,
) -> Dict[str, Any]:
    """Suggest a price range based on category benchmarks and cost.

    Args:
        product_name: Product name for context.
        category: Product category.
        cost_price: The cost/wholesale price of the product (0 if unknown).

    Returns:
        Dict with suggested_min, suggested_max, suggested_optimal, and margin.
    """
    bench = get_category_price_benchmarks(category)
    avg = bench["avg"]
    p25 = bench["percentile_25"]
    p75 = bench["percentile_75"]

    # Suggested range spans from percentile 25 to 75 of the category
    suggested_min = max(p25 * 0.9, cost_price * 1.15) if cost_price > 0 else p25 * 0.9
    suggested_max = p75 * 1.1

    # Optimal price: weighted toward category average, adjusted for cost
    if cost_price > 0:
        target_margin = 0.35  # 35% target margin
        cost_based = cost_price / (1 - target_margin)
        suggested_optimal = round((cost_based + avg) / 2, 2)
    else:
        suggested_optimal = round(avg, 2)

    suggested_min = round(max(suggested_min, 0.01), 2)
    suggested_max = round(max(suggested_max, suggested_min + 0.01), 2)
    suggested_optimal = round(
        max(suggested_min, min(suggested_optimal, suggested_max)), 2
    )

    # Compute margin if cost is known
    margin = None
    if cost_price > 0:
        margin = round((suggested_optimal - cost_price) / suggested_optimal * 100, 2)

    return {
        "product_name": product_name,
        "category": category,
        "cost_price": cost_price,
        "suggested_min": suggested_min,
        "suggested_max": suggested_max,
        "suggested_optimal": suggested_optimal,
        "expected_margin_pct": margin,
        "category_benchmarks": bench,
    }
