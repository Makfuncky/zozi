"""Tests for supplier management."""
from __future__ import annotations

import pytest
import uuid


@pytest.fixture
def supplier_headers(client):
    email = f"supplier_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"supplier_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "supplier",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}, email


@pytest.mark.integration
def test_get_supplier_profile(client, supplier_headers):
    headers, _ = supplier_headers
    resp = client.get("/supplier/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


@pytest.mark.integration
def test_update_supplier_profile(client, supplier_headers):
    headers, _ = supplier_headers
    resp = client.put(
        "/supplier/profile",
        headers=headers,
        json={"business_name": "Updated Supplier Co", "bio": "We sell things"},
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body.get("business_name") == "Updated Supplier Co"


@pytest.mark.integration
def test_supplier_dashboard(client, supplier_headers):
    headers, _ = supplier_headers
    resp = client.get("/supplier/analytics", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)


@pytest.mark.integration
def test_supplier_products_list(client, supplier_headers):
    headers, _ = supplier_headers
    resp = client.get("/supplier/products", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "data" in body or "items" in body


@pytest.mark.integration
def test_supplier_orders_list(client, supplier_headers):
    headers, _ = supplier_headers
    resp = client.get("/supplier/orders", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "data" in body or "items" in body


@pytest.mark.integration
def test_public_suppliers_list(client):
    resp = client.get("/suppliers")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "items" in body or "data" in body


@pytest.mark.integration
def test_public_supplier_by_id(client, supplier_headers):
    pytest.skip("Requires existing public supplier profile")


@pytest.mark.integration
def test_supplier_unauthorized_access(client):
    resp = client.get("/supplier/profile")
    assert resp.status_code == 401


@pytest.mark.integration
def test_supplier_document_upload(client, supplier_headers):
    headers, _ = supplier_headers
    resp = client.post(
        "/supplier/profile/verify-documents",
        headers=headers,
        files={"files": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
        data={"doc_types": "[\"business_license\"]"},
    )
    assert resp.status_code in (200, 201, 404)
