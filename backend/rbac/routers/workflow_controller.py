"""controllers.users.workflow_controller (CONTROLLERS layer).

Wraps ``services.users.workflow_engine`` and exposes the workflow automation
endpoints. The HTTP contract is declared with ``core.route_contract`` decorators
so ``routers/generated/auto_router.py`` can auto-generate the thin router — the
previous hand-written ``routers/workflows.py`` only instantiated the engine and
passed args through, which is controller-level orchestration that now lives
here.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.route_contract import post

from domains.accounts.services.workflow_engine import get_workflow_engine

@post("/workflows/create", deps=["user", "db"], query=["name", "workflow_type"])
def create_workflow(
    name: str,
    workflow_type: str,
    steps: list,
    current_user: dict,
    db: Session,
):
    """Create a new workflow definition."""
    engine = get_workflow_engine(db)
    return engine.create_workflow(name, workflow_type, steps)

@post(
    "/workflows/execute/{workflow_type}",
    deps=["user", "db"],
    query=["entity_type", "entity_id", "trigger_by"],
)
def execute_workflow(
    workflow_type: str,
    entity_type: str,
    entity_id: int,
    trigger_by: int,
    context: Optional[dict] = None,
    current_user: dict = None,
    db: Session = None,
):
    """Execute a workflow for a given entity."""
    engine = get_workflow_engine(db)
    return engine.execute_workflow(
        workflow_type, entity_type, entity_id, trigger_by, context or {}
    )

__all__ = ["create_workflow", "execute_workflow"]
