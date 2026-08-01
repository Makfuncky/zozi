"""
Workflow Automation Engine - Configurable business process workflows.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session

from models import SystemSetting


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkflowEngine:
    """Manage configurable business workflows."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_workflow(
        self,
        name: str,
        workflow_type: str,
        steps: List[Dict[str, Any]],
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create a new workflow definition."""
        workflow_id = SystemSetting(
            key=f"workflow_{workflow_type}_{name}",
            value=str({
                "name": name,
                "type": workflow_type,
                "steps": steps,
                "config": config or {},
                "created_at": datetime.utcnow().isoformat(),
            }),
            category="workflows",
        )
        self.db.add(workflow_id)
        self.db.commit()
        return {"id": workflow_id.id, "name": name, "type": workflow_type}
    
    def execute_workflow(
        self,
        workflow_type: str,
        entity_type: str,
        entity_id: int,
        trigger_by: int,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow for an entity."""
        setting = self.db.query(SystemSetting).filter(
            SystemSetting.key.like(f"workflow_{workflow_type}_%")
        ).first()
        
        if not setting:
            return {"error": "Workflow not found", "status": "not_configured"}
        
        import json
        try:
            workflow = json.loads(setting.value)
        except json.JSONDecodeError:
            return {"error": "Invalid workflow configuration", "status": "error"}
        
        steps = workflow.get("steps", [])
        results = []
        
        for step in steps:
            step_result = self._execute_step(step, entity_type, entity_id, context)
            results.append(step_result)
            if not step_result.get("success", False):
                return {
                    "status": "failed",
                    "entity_id": entity_id,
                    "failed_step": step.get("name"),
                    "results": results,
                }
        
        return {
            "status": "completed",
            "entity_id": entity_id,
            "results": results,
        }
    
    def _execute_step(self, step: Dict[str, Any], entity_type: str, entity_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        step_type = step.get("type")
        action = step.get("action")
        
        if step_type == "approval":
            return self._handle_approval_step(step, entity_type, entity_id, context)
        elif step_type == "notification":
            return self._handle_notification_step(step, entity_type, entity_id, context)
        elif step_type == "update":
            return self._handle_update_step(step, entity_type, entity_id, context)
        
        return {"success": False, "error": f"Unknown step type: {step_type}"}
    
    def _handle_approval_step(self, step: Dict[str, Any], entity_type: str, entity_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        required_role = step.get("required_role", "admin")
        return {
            "success": True,
            "step": "approval",
            "status": "pending_approval",
            "required_role": required_role,
        }
    
    def _handle_notification_step(self, step: Dict[str, Any], entity_type: str, entity_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        channel = step.get("channel", "email")
        return {
            "success": True,
            "step": "notification",
            "channel": channel,
            "sent_to": context.get("actor_email", "unknown"),
        }
    
    def _handle_update_step(self, step: Dict[str, Any], entity_type: str, entity_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        field = step.get("field")
        value = step.get("value")
        return {
            "success": True,
            "step": "update",
            "field": field,
            "value": value,
        }


def get_workflow_engine(db: Session) -> WorkflowEngine:
    return WorkflowEngine(db)
