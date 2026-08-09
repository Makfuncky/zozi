"""ORM model for the employee_risk_scores orphaned table.

This table was created by _GAP_DDL in tests/conftest.py but had no ORM model.
Tracks risk assessment scores for employees across different metrics.
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from .employee_models import Employee

__all__ = ["EmployeeRiskScore"]


class EmployeeRiskScore(Base):
    """Risk assessment scores for employees across different metrics."""

    __tablename__ = "employee_risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    recorded_at: Mapped[str | None] = mapped_column(
        DateTime, nullable=True, server_default="CURRENT_TIMESTAMP"
    )

    employee: Mapped[Employee] = relationship(
        "Employee",
        back_populates="risk_scores",
        foreign_keys=[employee_id],
    )

    __table_args__ = (
        Index("idx_risk_scores_employee", "employee_id"),
        UniqueConstraint("employee_id", "metric_name", name="uq_risk_scores_employee_metric"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmployeeRiskScore id={self.id} "
            f"employee_id={self.employee_id} "
            f"metric={self.metric_name!r} score={self.score}>"
        )
