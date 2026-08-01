"""ORM model for the employee_active_tasks orphaned table.

This table was created by _GAP_DDL in tests/conftest.py but had no ORM model.
The schema matches the existing SQLite table exactly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from .employee_models import Employee

__all__ = ["EmployeeActiveTask"]


class EmployeeActiveTask(Base):
    """Tracks currently active tasks assigned to employees."""

    __tablename__ = "employee_active_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    permission_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[str | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    created_at: Mapped[str | None] = mapped_column(
        DateTime, nullable=True, server_default="CURRENT_TIMESTAMP"
    )

    employee: Mapped[Employee] = relationship(
        "Employee",
        back_populates="active_tasks",
        foreign_keys=[employee_id],
    )

    __table_args__ = (
        Index("idx_active_tasks_employee", "employee_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmployeeActiveTask id={self.id} "
            f"employee_id={self.employee_id} "
            f"task={self.task_name!r} status={self.status!r}>"
        )
