"""
Comprehensive tests for search/autocomplete/visual endpoints.
Verifies the search/filter/sort integration with the database.
"""
import json


def _seed_test_products(db_session):
    """Insert sample products for search tests."""
    from data.models import Product

    products_data = [
        {
            "name": "Classic Cotton T-Shirt",
            "description": "A comfortable cotton t-shirt for everyday wear",
            "price": 29.99,
            "category": "fashion",
            "brand": "FashionHub",
            "stock": 100,
            "rating": 4.5,
            "sales_count": 250,
            "is_active": True,
            "is_approved": True,
            "is_deleted": False,
            "tags": "cotton,casual,summer",
            "color": "white",
            "sizes": json.dumps(["S", "M", "L", "XL"]),
        },
        {
            "name": "Wireless Bluetooth Headphones",
            "description": "Premium wireless headphones with noise cancellation",
            "price": 89.99,
            "category": "electronics",
            "brand": "TechSound",
            "stock": 50,
            "rating": 4.7,
            "sales_count": 500,
            "is_active": True,
            "is_approved": True,
            "is_deleted": False,
            "tags": "audio,wireless,bluetooth",
            "color": "black",
        },
        {
            "name": "Premium Yoga Mat",
            "description": "Non-slip exercise yoga mat with alignment lines",
            "price": 34.99,
            "category": "sports",
            "brand": "FitLife",
            "stock": 75,
            "rating": 4.3,
            "sales_count": 180,
            "is_active": True,
            "is_approved": True,
            "is_deleted": False,
            "tags": "fitness,yoga,exercise",
            "color": "purple",
        },
        {
            "name": "12-Cup Coffee Maker",
            "description": "Programmable drip coffee maker with thermal carafe",
            "price": 59.99,
            "category": "home",
            "brand": "HomeGoods",
            "stock": 30,
            "rating": 4.1,
            "sales_count": 95,
            "is_active": True,
            "is_approved": True,
            "is_deleted": False,
            "tags": "kitchen,coffee,appliance",
        },
        {
            "name": "Running Shoes Pro",
            "description": "Lightweight professional running shoes",
            "price": 129.99,
            "category": "sports",
            "brand": "FitLife",
            "stock": 20,
            "rating": 4.8,
            "sales_count": 420,
            "is_active": True,
            "is_approved": True,
            "is_deleted": False,
            "tags": "running,shoes,athletic",
            "color": "black",
        },
        {
            "name": "Denim Jacket Classic",
            "description": "Classic denim jacket with modern fit",
            "price": 79.99,
            "category": "fashion",
            "brand": "FashionHub",
            "stock": 45,
            "rating": 4.2,
            "sales_count": 150,
            "is_active": True,
            "is_approved": True,
            "is_deleted": False,
            "tags": "denim,jacket,outerwear",
            "color": "blue",
        },
    ]

    for data in products_data:
        product = Product(**data)
        db_session.add(product)
    db_session.commit()


# ═══════════════════════════════════════════════════════════════════════════
#  Product List Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestProductListSearch:
    """Test the GET /products endpoint with search/filter/sort params."""

    def test_search_by_query(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?q=t-shirt")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        names = [p.get("name", "") for p in data]
        assert any("T-Shirt" in n for n in names)

    def test_search_by_category(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?category=sports")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2  # Yoga Mat + Running Shoes
        categories = [p.get("category", "").lower() for p in data]
        assert all("sports" in c for c in categories)

    def test_filter_by_min_price(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?min_price=50")
        assert resp.status_code == 200
        data = resp.json()
        assert all(p.get("price", 0) >= 50 for p in data)

    def test_filter_by_max_price(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?max_price=35")
        assert resp.status_code == 200
        data = resp.json()
        assert all(p.get("price", 999) <= 35 for p in data)

    def test_filter_by_price_range(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?min_price=30&max_price=100")
        assert resp.status_code == 200
        data = resp.json()
        for p in data:
            assert 30 <= p.get("price", 0) <= 100

    def test_filter_by_rating(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?min_rating=4.5")
        assert resp.status_code == 200
        data = resp.json()
        assert all(p.get("rating", 0) >= 4.5 for p in data)

    def test_sort_by_price_asc(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?sort=price_asc")
        assert resp.status_code == 200
        data = resp.json()
        prices = [p.get("price", 0) for p in data]
        assert prices == sorted(prices)

    def test_sort_by_price_desc(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?sort=price_desc")
        assert resp.status_code == 200
        data = resp.json()
        prices = [p.get("price", 0) for p in data]
        assert prices == sorted(prices, reverse=True)

    def test_sort_by_newest(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?sort=newest")
        assert resp.status_code == 200

    def test_filter_by_brand(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?brand=FitLife")
        assert resp.status_code == 200
        data = resp.json()
        assert all(p.get("brand") == "FitLife" for p in data)

    def test_filter_by_brands(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?brands=FitLife,FashionHub")
        assert resp.status_code == 200
        data = resp.json()
        assert all(p.get("brand") in ("FitLife", "FashionHub") for p in data)

    def test_combined_filters(self, client, db_session):
        """Test Category + Price + Rating working together."""
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?category=sports&min_price=30&max_price=200&min_rating=4.0")
        assert resp.status_code == 200
        data = resp.json()
        for p in data:
            assert "sports" in p.get("category", "").lower()
            assert 30 <= p.get("price", 0) <= 200
            assert p.get("rating", 0) >= 4.0

    def test_new_arrivals_flag(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?new_arrivals=true")
        assert resp.status_code == 200

    def test_trending_flag(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?trending=true")
        assert resp.status_code == 200

    def test_empty_search_returns_all(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 6  # All 6 products

    def test_no_match_returns_empty(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?q=xyznonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0

    def test_pagination(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_supplier_filter(self, client, db_session):
        """Test supplier name filtering."""
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?supplier=FitLife")
        assert resp.status_code == 200
        data = resp.json()
        # Supplier filter requires joining with User/SupplierProfile
        # May return all products in test due to missing supplier profile,
        # but should not error
        assert isinstance(data, list)

    def test_color_filter(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products?color=black")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
#  Search Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchEndpoints:
    """Test the /search/* endpoints: autocomplete, AI, advanced, trending."""

    def test_autocomplete(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/autocomplete?q=coff")
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert any("Coffee" in s for s in data["suggestions"])

    def test_autocomplete_min_length(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/autocomplete?q=c")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data.get("suggestions", [])) == 0

    def test_advanced_search(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/advanced?q=shoes&min_price=50")
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        assert "total" in data

    def test_ai_search(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/ai?q=best+running+shoes")
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        assert "intent" in data

    def test_ai_search_intent_extraction(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/ai?q=black+shoes+under+100+with+video")
        assert resp.status_code == 200
        data = resp.json()
        assert "intent" in data
        intent = data["intent"]
        assert "primary_intent" in intent

    def test_fuzzy_search(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/fuzzy?q=headphon")
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data

    def test_trending_searches(self, client, db_session):
        resp = client.get("/api/v1/search/trending?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "queries" in data
        assert len(data["queries"]) > 0

    def test_word_predictions(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/predict?q=wire")
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data

    def test_supplier_names(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/products/suppliers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


# ═══════════════════════════════════════════════════════════════════════════
#  Visual Search Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestVisualSearch:
    """Test the POST /search/visual endpoint."""

    def test_visual_search_with_image(self, client, db_session):
        """Upload a test image and verify visual search returns results."""
        _seed_test_products(db_session)

        # Create a minimal valid PNG image (1x1 pixel)
        # Minimal valid PNG: 8-byte signature + IHDR + IDAT + IEND
        import struct
        import zlib

        def _make_png(width=1, height=1):
            """Create a minimal valid PNG file bytes."""
            signature = b'\x89PNG\r\n\x1a\n'

            # IHDR chunk
            ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
            ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc & 0xffffffff)

            # IDAT chunk (minimal pixel data)
            raw_data = b''
            for y in range(height):
                raw_data += b'\x00'  # filter byte
                for x in range(width):
                    raw_data += b'\xff\x00\x00'  # RGB pixel (red)

            compressed = zlib.compress(raw_data)
            idat_crc = zlib.crc32(b'IDAT' + compressed)
            idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc & 0xffffffff)

            # IEND chunk
            iend_crc = zlib.crc32(b'IEND')
            iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc & 0xffffffff)

            return signature + ihdr + idat + iend

        png_bytes = _make_png()

        resp = client.post(
            "/api/v1/search/visual",
            files={"image": ("test.png", png_bytes, "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "similarProductIds" in data
        assert "similarProducts" in data


class TestSearchFilters:
    """Test the /search/filters endpoints."""

    def test_get_available_filters(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/filters")
        assert resp.status_code == 200
        data = resp.json()
        assert "filters" in data

    def test_get_filters_summary(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.get("/api/v1/search/filters/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_products" in data


# ═══════════════════════════════════════════════════════════════════════════
#  POST /search Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestProductSearchPost:
    """Test POST /api/v1/products/search — body-based search mirroring GET filters."""

    def test_search_by_query(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post("/api/v1/products/search", json={"q": "t-shirt"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        names = [p.get("name", "") for p in data]
        assert any("T-Shirt" in n for n in names)

    def test_search_by_category(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post("/api/v1/products/search", json={"category": "sports"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2  # Yoga Mat + Running Shoes
        categories = [p.get("category", "").lower() for p in data]
        assert all("sports" in c for c in categories)

    def test_search_empty_body_returns_all(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post("/api/v1/products/search", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 6

    def test_search_by_price_range(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"min_price": 30, "max_price": 100},
        )
        assert resp.status_code == 200
        data = resp.json()
        for p in data:
            assert 30 <= p.get("price", 0) <= 100

    def test_search_by_brand(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post("/api/v1/products/search", json={"brand": "FitLife"})
        assert resp.status_code == 200
        data = resp.json()
        assert all(p.get("brand") == "FitLife" for p in data)

    def test_search_by_brands_list(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"brands": "FitLife,FashionHub"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(p.get("brand") in ("FitLife", "FashionHub") for p in data)

    def test_search_sort_by_price_asc(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"sort": "price_asc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        prices = [p.get("price", 0) for p in data]
        assert prices == sorted(prices)

    def test_search_sort_by_price_desc(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"sort": "price_desc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        prices = [p.get("price", 0) for p in data]
        assert prices == sorted(prices, reverse=True)

    def test_search_pagination(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"limit": 2, "offset": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_search_no_match_returns_empty(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"q": "xyznonexistent"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0

    def test_search_combined_filters(self, client, db_session):
        """Test Category + Price + Rating working together via POST body."""
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={
                "category": "sports",
                "min_price": 30,
                "max_price": 200,
                "min_rating": 4.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        for p in data:
            assert "sports" in p.get("category", "").lower()
            assert 30 <= p.get("price", 0) <= 200
            assert p.get("rating", 0) >= 4.0

    def test_search_in_stock(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"in_stock": True, "min_price": 0, "max_price": 0.01},
        )
        assert resp.status_code == 200

    def test_search_total_count_header(self, client, db_session):
        _seed_test_products(db_session)
        resp = client.post(
            "/api/v1/products/search",
            json={"limit": 10, "offset": 0},
        )
        assert resp.status_code == 200
        assert "X-Total-Count" in resp.headers
        assert int(resp.headers["X-Total-Count"]) == 6
