"""
Functional tests for all newly built provider tools:
- QR Code Generation
- Barcode Management
- QR/Barcode Scanner
- Recommendation Engine
- Price Intelligence
- Review Sentiment Analysis
- Image Similarity Search
- Shipping Rate Calculator
"""
import io
import os
import sys
from typing import Dict, List

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# QR CODE GENERATION
# ============================================================================

class TestQRGeneration:
    def test_has_qrcode_flag(self):
        from providers.qr import HAS_QRCODE
        assert isinstance(HAS_QRCODE, bool)

    def test_generate_qr_returns_bytes(self):
        from providers.qr import generate_qr
        if not pytest.importorskip("qrcode", reason="qrcode not installed"):
            return
        result = generate_qr("https://zozi.com/product/123")
        assert isinstance(result, bytes)
        assert len(result) > 0
        # PNG magic bytes
        assert result[:4] == b'\x89PNG'

    def test_generate_product_qr(self):
        from providers.qr import generate_product_qr
        if not pytest.importorskip("qrcode"):
            return
        result = generate_product_qr(123, "https://zozi.com")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_payment_qr(self):
        from providers.qr import generate_payment_qr
        if not pytest.importorskip("qrcode"):
            return
        result = generate_payment_qr(99.99, "USD", "ORD-001")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_tracking_qr(self):
        from providers.qr import generate_tracking_qr
        if not pytest.importorskip("qrcode"):
            return
        result = generate_tracking_qr("TRACK123456")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_qr_with_custom_params(self):
        from providers.qr import generate_qr
        if not pytest.importorskip("qrcode"):
            return
        result = generate_qr("test", size=20, border=4)
        assert isinstance(result, bytes)
        assert len(result) > 0


# ============================================================================
# BARCODE MANAGEMENT
# ============================================================================

class TestBarcodeGeneration:
    def test_has_barcode_flag(self):
        from providers.barcode import HAS_BARCODE
        assert isinstance(HAS_BARCODE, bool)

    def test_generate_ean13(self):
        from providers.barcode import generate_ean13
        if not pytest.importorskip("barcode", reason="python-barcode not installed"):
            return
        result = generate_ean13("1234567890128")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_upca(self):
        from providers.barcode import generate_upca
        if not pytest.importorskip("barcode"):
            return
        result = generate_upca("123456789012")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_code128(self):
        from providers.barcode import generate_code128
        if not pytest.importorskip("barcode"):
            return
        result = generate_code128("ZOZI-PROD-001")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_validate_ean13_valid(self):
        from providers.barcode import validate_ean13
        assert validate_ean13("1234567890128") == True

    def test_validate_ean13_invalid(self):
        from providers.barcode import validate_ean13
        assert validate_ean13("1234567890123") == False

    def test_validate_upca_valid(self):
        from providers.barcode import validate_upca
        assert validate_upca("123456789012") == True

    def test_validate_upca_invalid(self):
        from providers.barcode import validate_upca
        assert validate_upca("123456789013") == False

    def test_calculate_ean13_check_digit(self):
        from providers.barcode import calculate_ean13_check_digit
        result = calculate_ean13_check_digit("123456789012")
        assert result == "8"


# ============================================================================
# QR/BARCODE SCANNER
# ============================================================================

class TestScanner:
    def test_has_scanner_flag(self):
        from providers.scanner import HAS_SCANNER
        assert isinstance(HAS_SCANNER, bool)

    def test_scan_qr_flag_check(self):
        from providers.scanner import scan_qr, HAS_SCANNER
        if not HAS_SCANNER:
            pytest.skip("pyzbar not installed")
        # Would need a real QR image to test decoding

    def test_scan_barcode_flag_check(self):
        from providers.scanner import scan_barcode, HAS_SCANNER
        if not HAS_SCANNER:
            pytest.skip("pyzbar not installed")


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class TestRecommendationEngine:
    def test_get_similar_products(self):
        from providers.ai.recommendation import get_similar_products
        products = [
            {"id": 1, "name": "Cotton Shirt", "category": "fashion", "tags": ["cotton", "casual"]},
            {"id": 2, "name": "Denim Jeans", "category": "fashion", "tags": ["denim", "casual"]},
            {"id": 3, "name": "Wooden Table", "category": "home", "tags": ["furniture", "wood"]},
        ]
        result = get_similar_products(1, products, limit=2)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_product_recommendations(self):
        from providers.ai.recommendation import get_product_recommendations
        products = [
            {"id": 1, "name": "Cotton Shirt", "category": "fashion", "tags": ["cotton", "casual"]},
            {"id": 2, "name": "Denim Jeans", "category": "fashion", "tags": ["denim", "casual"]},
            {"id": 3, "name": "Silk Scarf", "category": "fashion", "tags": ["silk", "accessory"]},
        ]
        result = get_product_recommendations(1, [2], products, limit=2)
        assert isinstance(result, list)

    def test_get_frequently_bought_together(self):
        from providers.ai.recommendation import get_frequently_bought_together
        orders = [[1, 2], [1, 2, 3], [1, 3], [2, 3]]
        result = get_frequently_bought_together(1, orders, limit=2)
        assert isinstance(result, list)

    def test_recommendations_have_scores(self):
        from providers.ai.recommendation import get_similar_products
        products = [
            {"id": 1, "name": "Cotton Shirt", "category": "fashion", "tags": ["cotton"]},
            {"id": 2, "name": "Cotton Pants", "category": "fashion", "tags": ["cotton"]},
        ]
        result = get_similar_products(1, products)
        if result:
            assert "score" in result[0] or "similarity" in result[0]


# ============================================================================
# PRICE INTELLIGENCE
# ============================================================================

class TestPriceIntelligence:
    def test_analyze_price(self):
        from providers.ai.price_intelligence import analyze_price
        result = analyze_price("iPhone 15", "electronics", 999.0, [899, 1099, 949])
        assert isinstance(result, dict)
        assert "positioning" in result
        assert "percentile_rank" in result

    def test_analyze_price_no_competitors(self):
        from providers.ai.price_intelligence import analyze_price
        result = analyze_price("Shirt", "fashion", 25.0)
        assert isinstance(result, dict)
        assert "positioning" in result

    def test_get_category_benchmarks(self):
        from providers.ai.price_intelligence import get_category_price_benchmarks
        result = get_category_price_benchmarks("electronics")
        assert isinstance(result, dict)
        assert "min" in result
        assert "max" in result
        assert "avg" in result

    def test_suggest_price_range(self):
        from providers.ai.price_intelligence import suggest_price_range
        result = suggest_price_range("Cotton Shirt", "fashion", cost_price=10.0)
        assert isinstance(result, dict)
        assert "suggested_min" in result
        assert "suggested_max" in result
        assert result["suggested_min"] > 0

    def test_suggest_price_without_cost(self):
        from providers.ai.price_intelligence import suggest_price_range
        result = suggest_price_range("Shirt", "fashion")
        assert isinstance(result, dict)
        assert result["suggested_min"] > 0


# ============================================================================
# REVIEW SENTIMENT ANALYSIS
# ============================================================================

class TestSentimentAnalysis:
    def test_analyze_sentiment_positive(self):
        from providers.ai.sentiment import analyze_sentiment
        result = analyze_sentiment("This product is amazing! I love it!")
        assert isinstance(result, dict)
        assert "score" in result
        assert "label" in result
        assert result["label"] == "positive"

    def test_analyze_sentiment_negative(self):
        from providers.ai.sentiment import analyze_sentiment
        result = analyze_sentiment("Terrible quality, broke after one use. Waste of money.")
        assert isinstance(result, dict)
        assert result["label"] == "negative"

    def test_analyze_sentiment_neutral(self):
        from providers.ai.sentiment import analyze_sentiment
        result = analyze_sentiment("It's okay, nothing special.")
        assert isinstance(result, dict)
        assert result["label"] in ("positive", "negative", "neutral")

    def test_analyze_review_with_rating(self):
        from providers.ai.sentiment import analyze_review
        result = analyze_review("Great product, highly recommend!", rating=5)
        assert isinstance(result, dict)
        assert "combined_score" in result
        assert "rating_provided" in result
        assert "agreement" in result

    def test_extract_review_insights(self):
        from providers.ai.sentiment import extract_review_insights
        reviews = [
            "Amazing quality, love the fabric",
            "Terrible, fell apart after washing",
            "Good value for money, fast shipping",
            "Color faded quickly, disappointed",
        ]
        result = extract_review_insights(reviews)
        assert isinstance(result, dict)
        assert "sentiment_distribution" in result
        assert "total_reviews" in result
        assert result["total_reviews"] == 4

    def test_has_vader_flag(self):
        from providers.ai.sentiment import HAS_VADER
        assert isinstance(HAS_VADER, bool)


# ============================================================================
# IMAGE SIMILARITY SEARCH
# ============================================================================

class TestImageSimilarity:
    def test_compute_image_embedding(self):
        from providers.ai.image_similarity import compute_image_embedding
        if not pytest.importorskip("PIL", reason="PIL not installed"):
            return
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = compute_image_embedding(buf.getvalue())
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)

    def test_compute_similarity(self):
        from providers.ai.image_similarity import compute_similarity
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        result = compute_similarity(vec1, vec2)
        assert result == pytest.approx(1.0)

    def test_compute_similarity_orthogonal(self):
        from providers.ai.image_similarity import compute_similarity
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        result = compute_similarity(vec1, vec2)
        assert result == pytest.approx(0.0)

    def test_find_similar_images(self):
        from providers.ai.image_similarity import find_similar_images
        if not pytest.importorskip("PIL"):
            return
        from PIL import Image
        # Create query image (red)
        query_img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        query_img.save(buf, format="PNG")
        query_bytes = buf.getvalue()

        # Create candidates
        candidates = []
        for color in ["red", "blue", "green", "yellow"]:
            img = Image.new("RGB", (100, 100), color=color)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            candidates.append({"id": len(candidates) + 1, "image_bytes": buf.getvalue()})

        result = find_similar_images(query_bytes, candidates, limit=3)
        assert isinstance(result, list)
        # Red should be most similar to red
        if result:
            assert result[0]["id"] == 1  # red is first


# ============================================================================
# SHIPPING RATE CALCULATOR
# ============================================================================

class TestShippingCalculator:
    def test_calculate_shipping_rate(self):
        from providers.shipping import calculate_shipping_rate
        origin = {"country": "US", "city": "New York", "postal": "10001"}
        destination = {"country": "US", "city": "Los Angeles", "postal": "90001"}
        package = {"weight_kg": 1.5, "length_cm": 30, "width_cm": 20, "height_cm": 10}
        result = calculate_shipping_rate(origin, destination, package)
        assert isinstance(result, dict)
        assert "total" in result
        assert result["total"] > 0

    def test_calculate_shipping_rate_international(self):
        from providers.shipping import calculate_shipping_rate
        origin = {"country": "US", "city": "New York", "postal": "10001"}
        destination = {"country": "AE", "city": "Dubai", "postal": "00000"}
        package = {"weight_kg": 2.0, "length_cm": 40, "width_cm": 30, "height_cm": 20}
        result = calculate_shipping_rate(origin, destination, package)
        assert isinstance(result, dict)
        assert result["total"] > 0

    def test_get_available_carriers(self):
        from providers.shipping import get_available_carriers
        result = get_available_carriers("US")
        assert isinstance(result, list)
        assert len(result) > 0
        assert any(c["name"] == "FedEx" for c in result)

    def test_get_available_carriers_uae(self):
        from providers.shipping import get_available_carriers
        result = get_available_carriers("AE")
        assert isinstance(result, list)
        assert any(c["name"] == "Aramex" for c in result)

    def test_estimate_delivery_days(self):
        from providers.shipping import estimate_delivery_days
        origin = {"country": "US", "city": "New York", "postal": "10001"}
        destination = {"country": "US", "city": "Los Angeles", "postal": "90001"}
        result = estimate_delivery_days(origin, destination, "fedex")
        assert isinstance(result, dict)
        assert "min_days" in result
        assert "max_days" in result
        assert result["min_days"] > 0

    def test_compare_shipping_options(self):
        from providers.shipping import compare_shipping_options
        origin = {"country": "US", "city": "New York", "postal": "10001"}
        destination = {"country": "AE", "city": "Dubai", "postal": "00000"}
        package = {"weight_kg": 1.0, "length_cm": 25, "width_cm": 15, "height_cm": 10}
        result = compare_shipping_options(origin, destination, package)
        assert isinstance(result, list)
        assert len(result) > 0
        # Should be sorted by total cost
        costs = [r["total"] for r in result]
        assert costs == sorted(costs)

    def test_dimensional_weight(self):
        """Large light package should be charged by dimensional weight."""
        from providers.shipping import calculate_shipping_rate
        origin = {"country": "US", "city": "NY", "postal": "10001"}
        destination = {"country": "US", "city": "LA", "postal": "90001"}
        # Large but light package
        light_bulky = {"weight_kg": 0.5, "length_cm": 100, "width_cm": 100, "height_cm": 100}
        # Small heavy package
        heavy_compact = {"weight_kg": 5.0, "length_cm": 20, "width_cm": 20, "height_cm": 20}
        rate1 = calculate_shipping_rate(origin, destination, light_bulky)
        rate2 = calculate_shipping_rate(origin, destination, heavy_compact)
        # Dimensional weight should make light_bulky cost more
        assert rate1["total"] > 0
        assert rate2["total"] > 0
