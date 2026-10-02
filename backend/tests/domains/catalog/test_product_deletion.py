"""Catalog domain — product deletion event test.

Verifies that ``delete_product`` emits a ``product.deleted`` event and
does not directly mutate cross-domain tables (Law 3).

Per the worklist block for FILE 3.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.catalog
def test_delete_product_emits_event() -> None:
    """delete_product should emit product.deleted and not touch cross-domain tables directly."""
    from domains.catalog.services.products.products_service import delete_product

    mock_db = MagicMock()
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Test Event Product"
    mock_product.supplier_id = 999
    mock_product.is_deleted = False

    mock_db.query.return_value.filter.return_value.first.return_value = mock_product

    current_user = {"id": 999}

    with patch(
        "domains.catalog.events.publish_product_deleted"
    ) as mock_publish:
        result = delete_product(1, current_user, mock_db)

    mock_publish.assert_called_once_with(
        product_id=1,
        product_name="Test Event Product",
        supplier_id=999,
    )
    assert result["message"] == "Product deleted"
    assert "orders_notified" not in result

    # Verify product is soft-deleted
    assert mock_product.is_deleted is True
    mock_db.commit.assert_called()

    # Verify cross-domain tables were NOT directly mutated
    calls = [str(call) for call in mock_db.query.call_args_list]
    for call in calls:
        assert "CartItem" not in str(call)
        assert "Notification" not in str(call)
        assert "Order" not in str(call)
        assert "OrderItem" not in str(call)
