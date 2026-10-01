"""Regression tests for chat_threads_query.py (FILE-22 / DB-021).

Law 46: No SELECT * — application queries must select explicit columns.
"""
from __future__ import annotations

import pytest

from domains.comms.services.shared.chat_threads_query import build_unified_inbox_sql


class TestBuildUnifiedInboxSql:
    """Outcome + error-path coverage for the Law 46 fix."""

    def test_no_select_star_in_outer_query(self):
        sql = build_unified_inbox_sql("1=1")
        assert "SELECT * FROM (" not in sql.upper()

    def test_explicit_columns_present(self):
        expected_columns = [
            "id",
            "local_id",
            "transport",
            "title",
            "preview",
            "unread",
            "updated_at",
            "channel_type",
            "participants",
            "peer_avatar",
            "folder",
        ]
        sql = build_unified_inbox_sql("1=1")
        upper_sql = sql.upper()
        for col in expected_columns:
            assert col.upper() in upper_sql, f"Column '{col}' missing from generated SQL"

    def test_returns_string_with_unioned_subqueries(self):
        sql = build_unified_inbox_sql("1=1")
        assert "UNION ALL" in sql.upper()
        assert "FROM (" in sql.upper()

    def test_where_clause_is_appended(self):
        sql = build_unified_inbox_sql("transport = :transport")
        assert "transport = :transport" in sql
        assert "ORDER BY updated_at DESC, id DESC" in sql

    def test_error_path_invalid_cursor_handling(self):
        """execute_unified_inbox_query must not crash on invalid cursor."""
        from unittest.mock import MagicMock

        from domains.comms.services.shared.chat_threads_query import execute_unified_inbox_query

        db = MagicMock()
        db.execute.return_value.mappings.return_value.all.return_value = []

        result = execute_unified_inbox_query(db, user_id=1, cursor="not-a-valid-cursor")
        assert "items" in result
        assert result["items"] == []
        assert result["hasMore"] is False
