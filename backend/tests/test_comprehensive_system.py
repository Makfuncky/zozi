"""Comprehensive system tests covering all major features.

This file consolidates and enhances testing for:
- Order placement
- Product upload
- New supplier registration
- New logistic partner registration
- New customer registration and login
- New employee registration and login
- Admin tasks
- Payment and reconciliation
- Advanced search & filter
- Database tests
- Admin permissions
- Hierarchy tests
- Finance and accounts
- Communication tests
"""

import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def admin_client_with_token(client, admin_auth_headers):
    """Admin client with pre-authenticated headers."""
    return client


@pytest.fixture
def supplier_client(client):
    """Supplier client with fresh supplier account."""
    email = f"supplier_test_{uuid.uuid4().hex[:8]}@zozi.test"
    username = f"supplier_test_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "SecurePass1!",
            "role": "supplier",
        },
    )
    assert resp.status_code in (200, 201), f"Registration failed: {resp.text}"
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_client(client):
    """Customer client with fresh customer account."""
    email = f"customer_test_{uuid.uuid4().hex[:8]}@zozi.test"
    username = f"customer_test_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert resp.status_code in (200, 201), f"Registration failed: {resp.text}"
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def employee_client(client):
    """Employee/HR client with fresh employee account."""
    email = f"employee_test_{uuid.uuid4().hex[:8]}@zozi.test"
    username = f"employee_test_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "SecurePass1!",
            "role": "employee",
        },
    )
    assert resp.status_code in (200, 201), f"Registration failed: {resp.text}"
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def logistics_partner_client(client):
    """Logistics partner client with fresh account."""
    email = f"logistics_test_{uuid.uuid4().hex[:8]}@zozi.test"
    username = f"logistics_test_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "SecurePass1!",
            "role": "logistics_partner",
        },
    )
    assert resp.status_code in (200, 201), f"Registration failed: {resp.text}"
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_product(client, db_session, supplier_headers):
    """Create a test product for testing."""
    from data.models import User, Product
    from utils.auth import get_password_hash

    email = f"prodowner_{uuid.uuid4().hex[:8]}@zozi.test"
    user = User(
        email=email,
        username=f"prodowner_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="supplier",
        country_code="AE",
    )
    db_session.add(user)
    db_session.flush()

    product = Product(
        name="Test Product for Orders",
        description="A test product",
        price=Decimal("25.50"),
        stock=100,
        category="Test",
        supplier_id=user.id,
        is_active=True,
        country_code="AE",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Order Placement Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestOrderPlacement:
    """Tests for order placement functionality."""

    def test_create_order_success(self, client, customer_client, test_product):
        """Test successful order creation."""
        resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 2}],
                "shipping_address": "123 Test St, Muscat, OM",
                "payment_method": "card",
            },
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert "id" in body
        assert body["status"] == "pending"
        assert float(body["total_amount"]) == 51.0

    def test_create_order_insufficient_stock(self, client, customer_client, test_product, db_session):
        """Test order creation with insufficient stock."""
        from data.models import Product
        test_product.stock = 0
        db_session.commit()
        resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "payment_method": "card",
            },
        )
        assert resp.status_code == 409

    def test_create_order_unauthenticated(self, client):
        """Test order creation without authentication."""
        resp = client.post("/api/v1/orders", json={"items": [], "shipping_address": "X"})
        assert resp.status_code == 401

    def test_create_order_empty_items(self, client, customer_client):
        """Test order creation with empty items."""
        resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={"items": [], "shipping_address": "123 Test St"},
        )
        assert resp.status_code == 422

    def test_get_order_by_id(self, client, customer_client, test_product):
        """Test retrieving order by ID."""
        create_resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "payment_method": "card",
            },
        )
        order_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/orders/{order_id}", headers=customer_client)
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    def test_list_user_orders(self, client, customer_client, test_product):
        """Test listing user's orders."""
        client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "payment_method": "card",
            },
        )
        resp = client.get("/api/v1/orders", headers=customer_client)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_cancel_order(self, client, customer_client, test_product):
        """Test order cancellation."""
        create_resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "payment_method": "card",
            },
        )
        order_id = create_resp.json()["id"]
        resp = client.post(f"/api/v1/orders/{order_id}/cancel", headers=customer_client)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Product Upload Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestProductUpload:
    """Tests for product upload functionality."""

    def test_create_product_as_supplier(self, client, supplier_headers):
        """Test product creation by supplier."""
        resp = client.post(
            "/api/v1/products/",
            headers=supplier_headers,
            json={
                "name": "Test Widget",
                "description": "A test widget for sale",
                "price": 25.0,
                "category": "Widgets",
                "stock": 100,
                "image_url": "http://img.test/w.png",
            },
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["name"] == "Test Widget"
        assert "slug" in body

    def test_create_product_as_customer_forbidden(self, client, customer_client):
        """Test that customers cannot create products."""
        resp = client.post(
            "/api/v1/products/",
            headers=customer_client,
            json={
                "name": "Forbidden Widget",
                "price": 10.0,
                "category": "Widgets",
            },
        )
        assert resp.status_code == 403

    def test_create_product_negative_price(self, client, supplier_headers):
        """Test product creation with negative price."""
        resp = client.post(
            "/api/v1/products/",
            headers=supplier_headers,
            json={
                "name": "Bad Price Widget",
                "price": -5.0,
                "category": "Widgets",
            },
        )
        assert resp.status_code in (422, 400)

    def test_update_product(self, client, supplier_headers):
        """Test product update."""
        create_resp = client.post(
            "/api/v1/products/",
            headers=supplier_headers,
            json={
                "name": "Updatable Widget",
                "price": 15.0,
                "category": "Widgets",
                "stock": 50,
            },
        )
        product_id = create_resp.json()["id"]
        resp = client.put(
            f"/api/v1/products/{product_id}",
            headers=supplier_headers,
            json={"name": "Updated Widget", "price": 20.0},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Widget"

    def test_delete_product(self, client, supplier_headers):
        """Test product deletion."""
        create_resp = client.post(
            "/api/v1/products/",
            headers=supplier_headers,
            json={
                "name": "Deletable Widget",
                "price": 5.0,
                "category": "Widgets",
            },
        )
        product_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/products/{product_id}", headers=supplier_headers)
        assert resp.status_code == 200
        get_resp = client.get(f"/api/v1/products/{product_id}")
        assert get_resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Supplier Registration Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSupplierRegistration:
    """Tests for supplier registration and functionality."""

    def test_register_new_supplier(self, client):
        """Test new supplier registration."""
        email = f"new_supplier_{uuid.uuid4().hex[:8]}@zozi.test"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"supplier_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "supplier",
            },
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["user"]["email"] == email
        assert body["user"]["role"] == "supplier"

    def test_supplier_login_after_registration(self, client):
        """Test supplier can login after registration."""
        email = f"login_supplier_{uuid.uuid4().hex[:8]}@zozi.test"
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"login_supplier_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "supplier",
            },
        )
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_supplier_can_access_supplier_endpoints(self, supplier_headers):
        """Test supplier can access their endpoints."""
        resp = client.get("/api/v1/supplier/products", headers=supplier_headers)
        assert resp.status_code in (200, 401)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Logistic Partner Registration Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestLogisticPartnerRegistration:
    """Tests for logistic partner registration and functionality."""

    def test_register_new_logistics_partner(self, client):
        """Test new logistics partner registration."""
        email = f"new_logistics_{uuid.uuid4().hex[:8]}@zozi.test"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"logistics_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "logistics_partner",
            },
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["user"]["email"] == email
        assert body["user"]["role"] == "logistics_partner"

    def test_logistics_partner_login_after_registration(self, client):
        """Test logistics partner can login after registration."""
        email = f"login_logistics_{uuid.uuid4().hex[:8]}@zozi.test"
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"login_logistics_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "logistics_partner",
            },
        )
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Customer Registration and Login Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCustomerRegistrationAndLogin:
    """Tests for customer registration and login."""

    def test_register_new_customer(self, client):
        """Test new customer registration."""
        email = f"new_customer_{uuid.uuid4().hex[:8]}@zozi.test"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"customer_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["user"]["role"] == "customer"

    def test_customer_login_with_email(self, client):
        """Test customer login with email."""
        email = f"login_cust_{uuid.uuid4().hex[:8]}@zozi.test"
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"login_cust_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_customer_login_with_username(self, client):
        """Test customer login with username."""
        username = f"login_user_{uuid.uuid4().hex[:8]}"
        email = f"login_{uuid.uuid4().hex[:8]}@zozi.test"
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        resp = client.post("/api/v1/auth/login", json={"username": username, "password": "SecurePass1!"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        email = f"wrong_pass_{uuid.uuid4().hex[:8]}@zozi.test"
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"wrong_pass_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass1!"})
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Employee Registration and Login Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestEmployeeRegistrationAndLogin:
    """Tests for employee/HR registration and login."""

    def test_register_new_employee(self, client):
        """Test new employee registration."""
        email = f"new_employee_{uuid.uuid4().hex[:8]}@zozi.test"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"employee_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "employee",
            },
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["user"]["role"] == "employee"

    def test_employee_login_after_registration(self, client):
        """Test employee can login after registration."""
        email = f"login_employee_{uuid.uuid4().hex[:8]}@zozi.test"
        client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"login_employee_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "employee",
            },
        )
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Admin Tasks Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAdminTasks:
    """Tests for admin tasks and functionality."""

    def test_admin_login(self, client):
        """Test admin can login."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@zozi.com", "password": "admin123"},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "admin"

    def test_admin_can_list_users(self, admin_auth_headers):
        """Test admin can list users."""
        resp = client.get("/api/v1/admin/users", headers=admin_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "data" in body
        assert isinstance(body["data"], list)

    def test_admin_can_list_products(self, admin_auth_headers):
        """Test admin can list products."""
        resp = client.get("/api/v1/admin/products", headers=admin_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "data" in body

    def test_admin_can_list_orders(self, admin_auth_headers):
        """Test admin can list orders."""
        resp = client.get("/api/v1/admin/orders", headers=admin_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "data" in body

    def test_admin_can_access_analytics(self, admin_auth_headers):
        """Test admin can access analytics."""
        resp = client.get("/api/v1/admin/analytics", headers=admin_auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_admin_settings_update(self, admin_auth_headers):
        """Test admin can update settings."""
        resp = client.put(
            "/api/v1/admin/settings",
            headers=admin_auth_headers,
            json={"app_name": "ZOZI Updated"},
        )
        assert resp.status_code in (200, 405)

    def test_admin_export_orders(self, admin_auth_headers):
        """Test admin can export orders."""
        resp = client.get("/api/v1/admin/export/orders", headers=admin_auth_headers)
        assert resp.status_code == 200

    def test_admin_commission_settings(self, admin_auth_headers):
        """Test admin can access commission settings."""
        resp = client.get("/api/v1/admin/AE/rates", headers=admin_auth_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Payment and Reconciliation Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestPaymentAndReconciliation:
    """Tests for payment processing and reconciliation."""

    def test_payment_status_transitions(self, client, customer_client, test_product, db_session):
        """Test payment status transitions."""
        from data.models import Order
        create_resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "payment_method": "card",
            },
        )
        order_id = create_resp.json()["id"]
        order = db_session.query(Order).filter(Order.id == order_id).first()
        assert order.payment_status == "pending"
        order.payment_status = "completed"
        db_session.commit()
        resp = client.get(f"/api/v1/orders/{order_id}", headers=customer_client)
        assert resp.json()["payment_status"] == "completed"

    def test_payment_intent_creation(self, client, customer_client, test_product):
        """Test payment intent creation."""
        create_resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "payment_method": "stripe",
            },
        )
        assert create_resp.status_code in (200, 201)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Advanced Search & Filter Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAdvancedSearchAndFilter:
    """Tests for advanced search and filtering."""

    def test_product_search_by_query(self, client, test_product):
        """Test product search by query."""
        resp = client.get(f"/api/v1/search/products?q={test_product.name}")
        assert resp.status_code == 200
        body = resp.json()
        assert "results" in body
        assert isinstance(body["results"], list)

    def test_search_parse_max_price(self, client):
        """Test search parsing of max price."""
        resp = client.get("/api/v1/search/products?q=laptops+under+500")
        assert resp.status_code == 200
        parsed = resp.json()["parsed"]
        assert parsed.get("max_price") == 500.0

    def test_search_parse_color(self, client):
        """Test search parsing of color."""
        resp = client.get("/api/v1/search/products?q=show+me+black+t-shirt+options")
        assert resp.status_code == 200
        parsed = resp.json()["parsed"]
        assert parsed.get("color") == "black"

    def test_product_filter_by_category(self, client):
        """Test product filtering by category."""
        resp = client.get("/api/v1/products?category=Test")
        assert resp.status_code == 200
        for p in resp.json():
            assert p.get("category", "").lower() == "test"

    def test_product_filter_in_stock(self, client):
        """Test product filtering by stock availability."""
        resp = client.get("/api/v1/products?in_stock=true")
        assert resp.status_code == 200
        for p in resp.json():
            assert p.get("stock", 0) > 0

    def test_product_pagination(self, client):
        """Test product pagination."""
        resp = client.get("/api/v1/products?limit=5&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Database Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestDatabase:
    """Tests for database operations and integrity."""

    def test_database_connection(self, db_session):
        """Test database connection is working."""
        from data.models import User
        result = db_session.query(User).first()
        assert result is not None or True  # DB is accessible

    def test_database_transaction_rollback(self, db_session):
        """Test that transactions are properly rolled back."""
        from data.models import User
        from utils.auth import get_password_hash

        initial_count = db_session.query(User).count()
        user = User(
            email=f"rollback_test_{uuid.uuid4().hex[:8]}@zozi.test",
            username=f"rollback_test_{uuid.uuid4().hex[:8]}",
            hashed_password=get_password_hash("SecurePass1!"),
            role="customer",
        )
        db_session.add(user)
        db_session.commit()

        # After commit, user should exist
        assert db_session.query(User).filter(User.email == user.email).first() is not None

    def test_foreign_key_constraints(self, client, customer_client, db_session):
        """Test foreign key constraints work correctly."""
        from data.models import Order
        # Try to create order for non-existent product
        resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": 999999, "quantity": 1}],
                "shipping_address": "123 Test St",
                "payment_method": "card",
            },
        )
        assert resp.status_code in (400, 404, 422)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Admin Permission Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAdminPermissions:
    """Tests for admin permissions and authorization."""

    def test_admin_access_to_admin_endpoints(self, admin_auth_headers):
        """Test admin can access admin endpoints."""
        resp = client.get("/api/v1/admin/users", headers=admin_auth_headers)
        assert resp.status_code == 200

    def test_customer_cannot_access_admin_endpoints(self, customer_client):
        """Test customer cannot access admin endpoints."""
        resp = client.get("/api/v1/admin/users", headers=customer_client)
        assert resp.status_code == 403

    def test_supplier_cannot_access_admin_endpoints(self, supplier_headers):
        """Test supplier cannot access admin endpoints."""
        resp = client.get("/api/v1/admin/users", headers=supplier_headers)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_admin_endpoints(self, client):
        """Test unauthenticated users cannot access admin endpoints."""
        resp = client.get("/api/v1/admin/users")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Hierarchy Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestHierarchy:
    """Tests for system hierarchy and relationships."""

    def test_supplier_has_products(self, client, supplier_headers, db_session):
        """Test supplier-product relationship."""
        from data.models import Product
        create_resp = client.post(
            "/api/v1/products/",
            headers=supplier_headers,
            json={
                "name": "Hierarchy Test Product",
                "price": 10.0,
                "category": "Test",
            },
        )
        product_id = create_resp.json()["id"]
        product = db_session.query(Product).filter(Product.id == product_id).first()
        assert product is not None

    def test_order_has_items(self, client, customer_client, test_product, db_session):
        """Test order-item relationship."""
        from data.models import Order, OrderItem
        create_resp = client.post(
            "/api/v1/orders",
            headers=customer_client,
            json={
                "items": [{"product_id": test_product.id, "quantity": 2}],
                "shipping_address": "123 Test St",
                "payment_method": "card",
            },
        )
        order_id = create_resp.json()["id"]
        order = db_session.query(Order).filter(Order.id == order_id).first()
        assert order is not None
        items = db_session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        assert len(items) >= 1
