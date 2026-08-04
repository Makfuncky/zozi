"""Tests for the standardized API response wrapper."""
import pytest
from fastapi.responses import JSONResponse

from utils.response_wrapper import (
    PaginatedResponseWrapper,
    create_paginated_response,
)
from data.schemas import PaginatedResponse


class TestPaginatedResponseWrapper:
    def test_from_query(self):
        items = [{"id": 1}, {"id": 2}]
        result = PaginatedResponseWrapper.from_query(
            items=items,
            total=50,
            page=1,
            size=20,
        )
        assert result.items == items
        assert result.total == 50
        assert result.page == 1
        assert result.size == 20
        assert result.pages == 3

    def test_from_query_empty(self):
        result = PaginatedResponseWrapper.from_query(
            items=[],
            total=0,
            page=1,
            size=20,
        )
        assert result.items == []
        assert result.total == 0
        assert result.pages == 0

    def test_from_query_single_page(self):
        result = PaginatedResponseWrapper.from_query(
            items=[{"id": 1}],
            total=1,
            page=1,
            size=20,
        )
        assert result.pages == 1

    def test_to_dict(self):
        wrapper = PaginatedResponseWrapper.from_query(
            items=["a", "b"],
            total=10,
            page=1,
            size=5,
        )
        d = wrapper.to_dict()
        assert d["items"] == ["a", "b"]
        assert d["total"] == 10
        assert d["page"] == 1
        assert d["size"] == 5
        assert d["pages"] == 2

    def test_inherits_from_base(self):
        assert issubclass(PaginatedResponseWrapper, PaginatedResponse)


class TestCreatePaginatedResponse:
    def test_returns_json_response(self):
        resp = create_paginated_response(
            items=[1, 2, 3],
            total=30,
            page=1,
            size=10,
        )
        assert isinstance(resp, JSONResponse)
        assert resp.status_code == 200

    def test_correct_content(self):
        resp = create_paginated_response(
            items=["x"],
            total=1,
            page=1,
            size=20,
        )
        import json
        body = json.loads(resp.body)
        assert body["items"] == ["x"]
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["size"] == 20
        assert body["pages"] == 1

    def test_empty_result(self):
        resp = create_paginated_response([], total=0)
        import json
        body = json.loads(resp.body)
        assert body["items"] == []
        assert body["total"] == 0
        assert body["pages"] == 0

    def test_multiple_pages(self):
        resp = create_paginated_response(
            items=list(range(10)),
            total=100,
            page=3,
            size=10,
        )
        import json
        body = json.loads(resp.body)
        assert body["page"] == 3
        assert body["pages"] == 10
