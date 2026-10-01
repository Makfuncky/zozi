from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from domains.customers.services.customer_router_service import _delete_response, delete_address


class TestDeleteResponseFormat:
    def test_delete_response_structure(self):
        result = _delete_response("address", 1)
        assert result == {"entity": "address", "id": 1, "status": "deleted"}

    def test_delete_response_for_customer(self):
        result = _delete_response("customer", 42)
        assert result == {"entity": "customer", "id": 42, "status": "deleted"}

    def test_delete_response_for_order(self):
        result = _delete_response("order", 7)
        assert result == {"entity": "order", "id": 7, "status": "deleted"}
