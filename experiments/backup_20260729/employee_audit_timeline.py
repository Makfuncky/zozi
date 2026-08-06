"""ORM model for the employee_audit_timeline orphaned table.

This table was created by _GAP_DDL in tests/conftest.py but had no ORM model.
Tracks audit trail events for employee-related actions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from .employee_models import Employee
    from .user import User

__all__ = ["EmployeeAuditTimeline"]


class EmployeeAuditTimeline(Base):
    """Audit trail for employee-related events and actions."""

    __tablename__ = "employee_audit_timeline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(
        DateTime, nullable=True, server_default="CURRENT_TIMESTAMP"
    )

    employee: Mapped[Employee] = relationship(
        "Employee",
        back_populates="audit_timeline",
        foreign_keys=[employee_id],
    )
    actor: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[actor_id],
    )

    __table_args__ = (
        Index("idx_audit_timeline_employee", "employee_id"),
        Index("idx_audit_timeline_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmployeeAuditTimeline id={self.id} "
            f"employee_id={self.employee_id} "
            f"event={self.event_type!r}>"
        )
