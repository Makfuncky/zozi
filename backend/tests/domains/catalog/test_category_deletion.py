"""Tests for category deletion centralization (AIDRIFT-008).

Verifies:
  * _CATEGORY_DELETED_MESSAGE is the single source of truth.
  * _delete_category performs soft-delete consistently.
  * deactivate_category and delete_category_by_id delegate to _delete_category.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from domains.catalog.services.categories.category_service import (
    _CATEGORY_DELETED_MESSAGE,
    _delete_category,
    deactivate_category,
    delete_category,
    delete_category_by_id,
)


class TestCategoryDeletedMessageConstant:
    """Centralized response message must be stable."""

    def test_message_constant_value(self):
        assert _CATEGORY_DELETED_MESSAGE == {"message": "Category deleted"}

    def test_message_constant_is_dict(self):
        assert isinstance(_CATEGORY_DELETED_MESSAGE, dict)


class TestDeleteCategoryHelper:
    """_delete_category is the single shared deletion path."""

    def test_soft_delete_sets_is_active_false(self):
        mock_db = MagicMock()
        mock_category = MagicMock()
        mock_category.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_category

        result = _delete_category(1, mock_db)

        assert result == _CATEGORY_DELETED_MESSAGE
        assert mock_category.is_active is False
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_category)

    def test_delete_missing_raises_404(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            _delete_category(999999, mock_db)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Category not found"

    def test_uses_soft_delete_strategy(self):
        mock_db = MagicMock()
        mock_category = MagicMock()
        mock_category.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_category

        _delete_category(1, mock_db)

        assert mock_category.is_active is False
        mock_db.commit.assert_called_once()


class TestDeactivateCategoryDelegates:
    """deactivate_category must delegate to _delete_category."""

    def test_deactivate_returns_deleted_category(self):
        mock_db = MagicMock()
        mock_category = MagicMock()
        mock_category.id = 1

        with patch(
            "domains.catalog.services.categories.category_service._delete_category",
            return_value=_CATEGORY_DELETED_MESSAGE,
        ) as mock_delete:
            result = deactivate_category(mock_db, mock_category)

        assert result is mock_category
        mock_delete.assert_called_once_with(1, mock_db)
        mock_db.refresh.assert_called_once_with(mock_category)

    def test_delete_category_alias_works(self):
        mock_db = MagicMock()
        mock_category = MagicMock()
        mock_category.id = 1

        with patch(
            "domains.catalog.services.categories.category_service._delete_category",
            return_value=_CATEGORY_DELETED_MESSAGE,
        ) as mock_delete:
            result = delete_category(mock_db, mock_category)

        assert result is mock_category
        mock_delete.assert_called_once_with(1, mock_db)
        mock_db.refresh.assert_called_once_with(mock_category)


class TestDeleteCategoryByIdDelegates:
    """delete_category_by_id must delegate to _delete_category."""

    def test_delete_by_id_returns_message(self):
        mock_db = MagicMock()
        mock_category = MagicMock()
        mock_category.id = 1

        with patch(
            "domains.catalog.services.categories.category_service._delete_category",
            return_value=_CATEGORY_DELETED_MESSAGE,
        ) as mock_delete, patch(
            "domains.catalog.services.categories.category_service.get_category_by_id",
            return_value=mock_category,
        ):
            result = delete_category_by_id(mock_db, "AE", 1)

        assert result == _CATEGORY_DELETED_MESSAGE
        mock_delete.assert_called_once_with(1, mock_db)

    def test_delete_by_id_missing_country_raises_404(self):
        mock_db = MagicMock()

        with patch(
            "domains.catalog.services.categories.category_service.get_category_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                delete_category_by_id(mock_db, "AE", 999999)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Category not found"

    def test_delete_by_id_wrong_country_raises_404(self):
        mock_db = MagicMock()
        mock_category = MagicMock()
        mock_category.id = 1

        with patch(
            "domains.catalog.services.categories.category_service.get_category_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                delete_category_by_id(mock_db, "AE", 1)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Category not found"
