"""Tests for search functionality."""
from __future__ import annotations

import pytest


@pytest.mark.integration
def test_search_products_returns_results(client):
    resp = client.get("/api/v1/search/products?q=phone&limit=4")
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert isinstance(body["results"], list)


@pytest.mark.integration
def test_search_products_empty_query(client):
    resp = client.get("/api/v1/search/products?q=")
    assert resp.status_code == 422


@pytest.mark.integration
def test_search_products_with_price_filter(client):
    resp = client.get("/api/v1/search/products?q=phone&min_price=10&max_price=100")
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    for p in body["results"]:
        price = p.get("price", 0)
        assert 10 <= price <= 100


@pytest.mark.integration
def test_search_products_with_category_filter(client):
    resp = client.get("/api/v1/search/products?q=phone&category=electronics")
    assert resp.status_code == 200
    for p in resp.json()["results"]:
        assert p.get("category", "").lower() == "electronics"


@pytest.mark.integration
def test_search_products_parsed_query(client):
    resp = client.get("/api/v1/search/products?q=laptops+under+500")
    assert resp.status_code == 200
    parsed = resp.json().get("parsed", {})
    assert parsed.get("max_price") == 500.0


@pytest.mark.integration
def test_search_products_pagination(client):
    resp = client.get("/api/v1/search/products?q=phone&limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()["results"]) <= 2


@pytest.mark.integration
def test_search_categories(client):
    resp = client.get("/api/v1/search/filters?q=phone")
    assert resp.status_code == 200
    assert "filters" in resp.json()


@pytest.mark.integration
def test_search_suggestions(client):
    resp = client.get("/api/v1/search/filters?q=ph")
    assert resp.status_code == 200
    assert "filters" in resp.json()
