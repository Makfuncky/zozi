"""Tests for paginated response integration in routers and utilities."""
from __future__ import annotations
import pytest

from utils.pagination import (
    safe_page,
    MAX_PAGE_SIZE,
    MAX_EXPORT_SIZE,
    paginated_query,
    paginated_response,
)


class TestSafePage:
    def test_default_values(self):
        page, size = safe_page(None, None)
        assert page == 1
        assert size == 20

    def test_clamp_negative(self):
        page, size = safe_page(-1, -5)
        assert page == 1
        assert size == 1

    def test_clamp_oversized(self):
        page, size = safe_page(0, 999)
        assert page == 1
        assert size == MAX_PAGE_SIZE

    def test_explicit_values(self):
        page, size = safe_page(3, 50)
        assert page == 3
        assert size == 50

    def test_custom_max_size(self):
        page, size = safe_page(1, 500, max_size=200)
        assert size == 200


class TestPaginatedQuery:
    def test_returns_tuple(self):
        items, total = paginated_query(
            _make_query([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            page=1,
            size=5,
        )
        assert len(items) <= 5
        assert total == 10

    def test_second_page(self):
        items, total = paginated_query(
            _make_query(list(range(20))),
            page=2,
            size=5,
        )
        assert list(items) == [5, 6, 7, 8, 9]
        assert total == 20

    def test_empty_result(self):
        items, total = paginated_query(_make_query([]), page=1, size=20)
        assert items == []
        assert total == 0

    def test_last_page_partial(self):
        items, total = paginated_query(
            _make_query(list(range(7))),
            page=2,
            size=5,
        )
        assert list(items) == [5, 6]
        assert total == 7


class TestPaginatedResponse:
    def test_returns_correct_envelope(self):
        result = paginated_response(
            _make_query(list(range(25))),
            page=1,
            size=10,
        )
        assert result["items"] == list(range(10))
        assert result["total"] == 25
        assert result["page"] == 1
        assert result["size"] == 10
        assert result["pages"] == 3

    def test_empty_response(self):
        result = paginated_response(_make_query([]), page=1, size=20)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["pages"] == 1  # max(1, 0) = 1

    def test_single_item(self):
        result = paginated_response(_make_query(["only"]), page=1, size=20)
        assert result["total"] == 1
        assert result["pages"] == 1

    def test_with_serializer(self):
        result = paginated_response(
            _make_query([{"id": 1}, {"id": 2}]),
            page=1,
            size=10,
            serializer=lambda x: x["id"],
        )
        assert result["items"] == [1, 2]


def _make_query(data: list):
    """Create a mock SQLAlchemy-style query object for testing."""
    from unittest.mock import MagicMock

    class MockQuery:
        def __init__(self, data):
            self._data = data

        def count(self):
            return len(self._data)

        def offset(self, n):
            self._offset = n
            return self

        def limit(self, n):
            self._limit = n
            return self

        def all(self):
            start = getattr(self, "_offset", 0)
            end = start + getattr(self, "_limit", len(self._data))
            return self._data[start:end]

    return MockQuery(data)
