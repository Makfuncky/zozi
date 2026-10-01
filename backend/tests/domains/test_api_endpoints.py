import pytest
import httpx
import os

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


class TestHealthEndpoint:
    def test_health_returns_200(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200

    def test_health_response_structure(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/health")
            data = response.json()
            assert "status" in data
            assert data["status"] == "ok"


class TestAuthEndpoints:
    def test_login_endpoint_exists(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.post("/api/v1/auth/login", json={"email": "test@test.com", "password": "wrong"})
            assert response.status_code in (200, 401)

    def test_register_endpoint_exists(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.post("/api/v1/auth/register", json={"email": "new@test.com", "password": "Test123!", "name": "Test User"})
            assert response.status_code in (200, 400, 409)

    def test_logout_endpoint_exists(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.post("/api/v1/auth/logout")
            assert response.status_code in (200, 401)

    def test_me_endpoint_requires_auth(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/auth/me")
            assert response.status_code in (401, 403)


class TestProductsEndpoints:
    def test_products_list_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/products")
            assert response.status_code in (200, 401)

    def test_product_search_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/products?search=test")
            assert response.status_code in (200, 401)


class TestSuppliersEndpoints:
    def test_suppliers_list_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/suppliers")
            assert response.status_code in (200, 401)

    def test_supplier_detail_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/suppliers/1")
            assert response.status_code in (200, 401, 404)


class TestCategoriesEndpoints:
    def test_categories_list_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/categories")
            assert response.status_code in (200, 401)


class TestCartEndpoints:
    def test_cart_get_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/cart")
            assert response.status_code in (200, 401)

    def test_cart_add_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.post("/api/v1/cart/add", json={"product_id": 1, "quantity": 1})
            assert response.status_code in (200, 401, 400)


class TestOrdersEndpoints:
    def test_orders_list_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/orders")
            assert response.status_code in (200, 401)


class TestCountriesEndpoints:
    def test_countries_list_endpoint(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/countries")
            assert response.status_code in (200, 401)


class TestAPIResponseFormat:
    def test_error_response_has_message(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/nonexistent-endpoint-12345")
            if response.status_code == 404:
                data = response.json()
                assert "message" in data or "error" in data or "detail" in data

    def test_api_returns_json(self):
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            response = client.get("/api/v1/health")
            if response.status_code == 200:
                assert "application/json" in response.headers.get("content-type", "")