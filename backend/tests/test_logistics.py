"""Tests for logistics and shipping."""

import pytest
import uuid


@pytest.fixture
def customer_headers(client):
    email = f"loguser_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"loguser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.integration
def test_shipping_quote(client, customer_headers):
    resp = client.post(
        "/logistics-partner/shipping-quote",
        headers=customer_headers,
        json={"country": "OM", "city": "Muscat", "subtotal": 50.0},
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body.get("destination", {}).get("country_code") == "OM"
    assert "shipping_amount" in body or "amount" in body


@pytest.mark.integration
def test_shipping_quote_unauthorized(client):
    resp = client.post("/logistics-partner/shipping-quote", json={"country": "OM", "subtotal": 50.0})
    assert resp.status_code == 401


@pytest.mark.integration
def test_list_logistics_partners(client):
    resp = client.get("/logistics-partner/public")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "items" in body


@pytest.mark.integration
def test_get_logistics_partner(client):
    resp = client.get("/logistics-partner/public")
    body = resp.json()
    items = body.get("items") if isinstance(body, dict) else body
    if items:
        pid = items[0]["id"]
        resp2 = client.get(f"/logistics-partner/public/{pid}")
        assert resp2.status_code == 200


@pytest.mark.integration
def test_track_shipment(client, admin_headers):
    resp = client.get("/logistics/shipments/scan", headers=admin_headers, params={"code": "TRK999999"})
    assert resp.status_code in (200, 404)


@pytest.mark.integration
def test_logistics_health(client, admin_headers):
    resp = client.get("/logistics-health/health/logistics", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "logistics_partners" in body


@pytest.mark.integration
def test_parcel_tracking_create(client, customer_headers):
    resp = client.post(
        "/parcel-tracking/parcel/1/tracking",
        headers=customer_headers,
        json={"country_code": "OM", "latitude": 23.5, "longitude": 58.4, "location_name": "Muscat"},
    )
    assert resp.status_code in (200, 201, 404)


@pytest.mark.integration
def test_geo_location_lookup(client):
    resp = client.get("/api/v1/geo/geo/countries")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
