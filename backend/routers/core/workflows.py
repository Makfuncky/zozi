"""
Workflow Automation API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from dependencies.auth import get_current_user
from services.workflow_engine import get_workflow_engine

router = APIRouter()


@router.post("/workflows/create")
def create_workflow(
    name: str,
    workflow_type: str,
    steps: list,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_workflow_engine(db)
    return engine.create_workflow(name, workflow_type, steps)


@router.post("/workflows/execute/{workflow_type}")
def execute_workflow(
    workflow_type: str,
    entity_type: str,
    entity_id: int,
    trigger_by: int,
    context: dict = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_workflow_engine(db)
    return engine.execute_workflow(workflow_type, entity_type, entity_id, trigger_by, context or {})
