"""Rescue test for the duplicate `chatbot_controller` module.

Problem verified in SYSTEM_AUDIT_REPORT.md:
  - D1  : duplicate module basename -- `chatbot_controller.py` existed at BOTH
          `backend/controllers/chatbot_controller.py` (root) and
          `backend/controllers/ai/chatbot_controller.py`.
  - HL502: the root file used a star import
          (`from controllers.ai.chatbot_controller import *`) polluting the namespace.
  - MV1  : the root file was mis-housed -- it belonged in `controllers/ai/`,
          where the canonical implementation already lived.

Resolution:
  - The 5-line star-import shim at `backend/controllers/chatbot_controller.py`
    was deleted.
  - `backend/routers/api_ai_assistant.py` now imports `handle_message` and
    `record_product_click` directly from `controllers.ai.chatbot_controller`.

These tests pin the fix so the duplicate/mis-housed module cannot silently
return.
"""
from __future__ import annotations

import importlib.util

import pytest
from fastapi.testclient import TestClient

# Canonical module must import cleanly (no star import, no duplicate).
from controllers.ai.chatbot_controller import handle_message, record_product_click


def test_duplicate_shim_module_is_gone() -> None:
    """The mis-housed duplicate `controllers/chatbot_controller.py` must not exist."""
    assert importlib.util.find_spec("controllers.chatbot_controller") is None


def test_router_imports_from_canonical_module() -> None:
    """The chatbot router must reference the canonical ai submodule directly."""
    import routers.api_ai_assistant as router_mod

    assert hasattr(router_mod, "router")
    # The router must pull the symbols straight from the ai controller,
    # not from a deleted shim.
    assert router_mod.handle_message is handle_message
    assert router_mod.record_product_click is record_product_click


def test_handle_message_empty_input_returns_early(db_session) -> None:
    """Empty/whitespace input short-circuits before any DB product search."""
    result = handle_message(
        db=db_session,
        message="   ",
        user_id=None,
        session_id=None,
        lang="en",
    )
    assert result["intent"] == "empty"
    assert isinstance(result["reply"], str) and result["reply"]


def test_chatbot_endpoint_is_wired_and_responding(client: TestClient) -> None:
    """End-to-end: POST /api/v1/chatbot/message works after the repoint."""
    resp = client.post("/api/v1/chatbot/message", json={"message": "   "})
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "empty"
    assert "reply" in body
