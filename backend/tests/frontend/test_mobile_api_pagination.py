"""Regression tests for mobile api.ts pagination contract.

Verifies that backend endpoints consumed by frontend/mobile_app/lib/api.ts
return response shapes compatible with the mobile client's normalizeCollectionResponse
and normalizeOffsetPageResponse helpers.

These tests ensure:
1. Customer orders endpoint returns a plain list (mobile wraps it with normalizeOffsetPageResponse)
2. Referral history endpoint returns {items, total, limit, offset} envelope
3. The normalization logic handles all envelope shapes the mobile client expects
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def _normalize_collection_response(payload, extra_keys=None):
    """Python mirror of mobile lib/api.ts normalizeCollectionResponse."""
    if extra_keys is None:
        extra_keys = []
    if isinstance(payload, list):
        return payload
    if not payload or not isinstance(payload, dict):
        return []
    envelope = payload
    for key in list(extra_keys) + ["items", "data", "results"]:
        value = envelope.get(key)
        if isinstance(value, list):
            return value
    return []


def _normalize_offset_page_response(payload, limit, offset, extra_keys=None):
    """Python mirror of mobile lib/api.ts normalizeOffsetPageResponse."""
    if extra_keys is None:
        extra_keys = []
    items = _normalize_collection_response(payload, extra_keys)
    envelope = payload if (payload and isinstance(payload, dict) and not isinstance(payload, list)) else None
    total = envelope.get("total") if isinstance(envelope, dict) and isinstance(envelope.get("total"), int) else offset + len(items)
    has_more = isinstance(envelope, dict) and isinstance(envelope.get("total"), int) and (offset + len(items) < total)
    if not has_more:
        has_more = len(items) >= limit
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "hasMore": has_more,
    }


class TestMobileOrdersPagination:
    """GET /api/v1/customer/orders returns a plain list (not envelope)."""

    def test_orders_returns_plain_list(self, customer_client):
        resp = customer_client.get("/api/v1/customer/orders?skip=0&limit=10")
        assert resp.status_code == 200
        body = resp.json()
        # Mobile api.ts normalizeOffsetPageResponse handles both plain lists
        # and envelopes; backend returns a plain list here.
        assert isinstance(body, list)

    def test_orders_response_items_have_expected_fields(self, customer_client):
        resp = customer_client.get("/api/v1/customer/orders?skip=0&limit=10")
        assert resp.status_code == 200
        body = resp.json()
        if body:
            assert "id" in body[0]
            assert "status" in body[0]


class TestMobileReferralHistoryPagination:
    """GET /auth/referrals/history returns {items, total, limit, offset}."""

    def test_referral_history_returns_offset_envelope(self, customer_client):
        resp = customer_client.get("/api/v1/customer/auth/referrals/history?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "limit" in body
        assert "offset" in body
        assert isinstance(body["items"], list)
        assert isinstance(body["total"], int)
        assert body["limit"] == 10
        assert body["offset"] == 0


class TestMobileNormalizationLogic:
    """Unit tests for the normalization logic used by mobile api.ts."""

    def test_plain_array(self):
        result = _normalize_collection_response([{"id": 1}, {"id": 2}])
        assert result == [{"id": 1}, {"id": 2}]

    def test_envelope_with_items(self):
        result = _normalize_collection_response({"items": [{"id": 1}]})
        assert result == [{"id": 1}]

    def test_envelope_with_extra_keys(self):
        result = _normalize_collection_response({"orders": [{"id": 1}]}, ["orders"])
        assert result == [{"id": 1}]

    def test_empty_envelope(self):
        result = _normalize_collection_response({})
        assert result == []

    def test_offset_page_with_plain_list(self):
        result = _normalize_offset_page_response([{"id": 1}, {"id": 2}], limit=10, offset=0)
        assert result["items"] == [{"id": 1}, {"id": 2}]
        assert result["total"] == 2
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert result["hasMore"] is False

    def test_offset_page_with_envelope(self):
        result = _normalize_offset_page_response({"items": [{"id": 1}], "total": 100}, limit=10, offset=0)
        assert result["items"] == [{"id": 1}]
        assert result["total"] == 100
        assert result["hasMore"] is True

    def test_offset_page_error_path_null_payload(self):
        result = _normalize_offset_page_response(None, limit=10, offset=0)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["hasMore"] is False
