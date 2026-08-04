"""Tests for multi-country support."""

import pytest
from unittest.mock import patch


@pytest.mark.integration
def test_list_countries(client):
    resp = client.get("/api/v1/countries")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_get_country_by_code(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.get("/api/v1/countries/OM", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("code") == "OM"


@pytest.mark.integration
def test_get_country_not_found(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.get("/api/v1/countries/XX", headers=admin_headers)
    assert resp.status_code == 404


@pytest.mark.integration
def test_country_auto_populate_admin(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    with patch("routers.country_auto_populate.auto_populate_country", return_value={"status": "success", "cached": False, "data": {"code": "OM"}}):
        resp = client.post(
            "/api/v1/country-auto-populate/auto-populate",
            headers=admin_headers,
            params={"search_term": "OM"},
        )
    assert resp.status_code in (200, 202)


@pytest.mark.integration
def test_country_dropdown(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.get("/api/v1/country-dropdown/dropdown/countries", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_country_maps(client):
    resp = client.get("/api/v1/country-maps/OM/map.geojson")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


@pytest.mark.integration
def test_currency_runtime(client):
    resp = client.get("/api/v1/currency/rates")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)


@pytest.mark.integration
def test_country_staff_assignments(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.get("/api/v1/country-staff/countries/OM/staff", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


@pytest.mark.integration
def test_cross_border_session_creation(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.get("/api/v1/cross-border/admin/countries/OM/localization", headers=admin_headers)
    assert resp.status_code in (200, 404)
