"""Tests for transaction management utilities."""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch

from db.transaction import (
    db_transaction_context,
    get_transaction_context,
    atomic_transaction,
    transactional,
)


class TestDbTransactionContext:
    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_successful_transaction(self, mock_engine, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        with db_transaction_context() as session:
            session.execute("SELECT 1")

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_rollback_on_error(self, mock_engine, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        with pytest.raises(ValueError):
            with db_transaction_context() as session:
                raise ValueError("test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_commit_error_propagates(self, mock_engine, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.commit.side_effect = RuntimeError("deadlock")

        with pytest.raises(RuntimeError):
            with db_transaction_context() as session:
                session.execute("SELECT 1")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestAtomicTransaction:
    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_atomic_transaction_success(self, mock_engine, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        with atomic_transaction() as session:
            session.add(MagicMock())

        mock_session.commit.assert_called_once()

    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_atomic_transaction_rollback(self, mock_engine, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        with pytest.raises(RuntimeError):
            with atomic_transaction() as session:
                raise RuntimeError("atomic fail")

        mock_session.rollback.assert_called_once()


class TestGetTransactionContext:
    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_get_transaction_context_callable(self, mock_engine, mock_session_local):
        ctx = get_transaction_context()
        assert callable(ctx)

    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_get_transaction_context_works(self, mock_engine, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        ctx = get_transaction_context()

        with ctx() as session:
            session.execute("SELECT 1")

        mock_session.commit.assert_called_once()


class TestTransactionalDecorator:
    @patch("db.transaction.SessionLocal")
    @patch("db.transaction.engine")
    def test_transactional_decorator(self, mock_engine, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        @transactional()
        def my_func(session=None):
            return "done"

        result = my_func()
        assert result == "done"
