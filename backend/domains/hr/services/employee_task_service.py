"""Employee task service — business logic for task management."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from domains.hr.models.employee_models import EmployeeTask, EmployeeTaskComment
from infrastructure.utils.pagination import (
    MAX_PAGE_SIZE,
    keyset_paginate,
)

logger = logging.getLogger(__name__)


class EmployeeTaskService:
    """Service for managing employee tasks."""

    def __init__(self, db: Session):
        self.db = db

    def list_employee_tasks_keyset(
        self,
        employee_id: int,
        *,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = MAX_PAGE_SIZE,
    ) -> dict:
        """Keyset-paginated tasks assigned to an employee (B6 / R6: never OFFSET).

        Returns ``{items, next_cursor, page_size, has_next}``. Sort key is
        ``(due_date asc, id asc)`` — the prior list endpoint ordered by
        ``due_date`` alone, but a non-unique sort key causes the keyset cursor
        to be ambiguous; ``id`` is appended as the deterministic tiebreaker.
        """
        limit = max(1, min(int(limit or MAX_PAGE_SIZE), MAX_PAGE_SIZE))
        q = self.db.query(EmployeeTask).filter(
            EmployeeTask.assigned_to_id == employee_id,
            EmployeeTask.is_deleted.is_(False),
        )
        if status:
            q = q.filter(EmployeeTask.status == status)
        if priority:
            q = q.filter(EmployeeTask.priority == priority)
        return keyset_paginate(
            q,
            sort_keys=[(EmployeeTask.due_date, "asc"), (EmployeeTask.id, "asc")],
            cursor=cursor,
            page_size=limit,
        )

    def get_task_by_id(self, task_id: int, employee_id: int) -> Optional[EmployeeTask]:
        """Get a specific task by ID (only if assigned to the employee)."""
        return self.db.query(EmployeeTask).filter(
            EmployeeTask.id == task_id,
            EmployeeTask.assigned_to_id == employee_id,
            EmployeeTask.is_deleted.is_(False),
        ).first()

    def create_task(
        self,
        title: str,
        description: str,
        task_type: str,
        assigned_to_id: int,
        assigned_by_id: int,
        priority: str = "medium",
        due_date: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        entity_url: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> EmployeeTask:
        """Create a new task and assign it to an employee."""
        task = EmployeeTask(
            title=title,
            description=description,
            task_type=task_type,
            assigned_to_id=assigned_to_id,
            assigned_by_id=assigned_by_id,
            priority=priority,
            due_date=due_date,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_url=entity_url,
            country_code=country_code,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        logger.info("Task %d created for employee %d by %d", task.id, assigned_to_id, assigned_by_id)
        return task

    def update_task_status(
        self,
        task_id: int,
        employee_id: int,
        status: str,
    ) -> Optional[EmployeeTask]:
        """Update the status of a task."""
        task = self.get_task_by_id(task_id, employee_id)
        if not task:
            return None
        task.status = status
        if status == "in_progress" and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        if status == "completed":
            task.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task

    def add_comment(
        self,
        task_id: int,
        employee_id: int,
        comment: str,
    ) -> Optional[EmployeeTaskComment]:
        """Add a comment to a task."""
        task = self.get_task_by_id(task_id, employee_id)
        if not task:
            return None
        task_comment = EmployeeTaskComment(
            task_id=task_id,
            employee_id=employee_id,
            comment=comment,
        )
        self.db.add(task_comment)
        self.db.commit()
        self.db.refresh(task_comment)
        return task_comment

    def get_task_stats(self, employee_id: int) -> dict:
        """Get task statistics for an employee."""
        from sqlalchemy import func
        stats = self.db.query(
            EmployeeTask.status,
            func.count(EmployeeTask.id),
        ).filter(
            EmployeeTask.assigned_to_id == employee_id,
            EmployeeTask.is_deleted.is_(False),
        ).group_by(EmployeeTask.status).all()
        result = {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0, "cancelled": 0}
        for status, count in stats:
            result[status] = count
        result["total"] = sum(result.values())
        # Count overdue
        overdue = self.db.query(func.count(EmployeeTask.id)).filter(
            EmployeeTask.assigned_to_id == employee_id,
            EmployeeTask.is_deleted.is_(False),
            EmployeeTask.status.notin_(["completed", "cancelled"]),
            EmployeeTask.due_date < datetime.now(timezone.utc),
        ).scalar() or 0
        result["overdue"] = overdue
        return result


def get_employee_task_service(db: Session) -> EmployeeTaskService:
    """Factory for EmployeeTaskService."""
    return EmployeeTaskService(db)
