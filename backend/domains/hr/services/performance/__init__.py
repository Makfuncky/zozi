"""hr domain — performance services."""
from __future__ import annotations

from domains.hr.services.performance.okr import *  # noqa: F401,F403
from domains.hr.services.performance.kpi import *  # noqa: F401,F403
from domains.hr.services.performance.reviews import *  # noqa: F401,F403
from domains.hr.services.performance.health import *  # noqa: F401,F403
from domains.hr.services.performance.endpoints import *  # noqa: F401,F403
from domains.hr.services.performance.dei_auditor import *  # noqa: F401,F403

__all__: list[str] = [
    "create_objective",
    "get_objective_tree",
    "update_objective_progress",
    "create_kpi_metric",
    "record_kpi_value",
    "get_kpi_dashboard",
    "submit_performance_review",
    "get_employee_reviews",
    "_recompute_employee_score",
    "compute_performance_health",
    "get_performance_health_board",
    "KpiCreate",
    "KpiValueUpdate",
    "ObjectiveCreate",
    "ObjectiveProgressUpdate",
    "ReviewSubmit",
    "coi_check_endpoint",
    "compute_health_endpoint",
    "create_kpi_endpoint",
    "create_objective_endpoint",
    "get_employee_reviews_endpoint",
    "get_kpi_dashboard_endpoint",
    "get_objective_tree_endpoint",
    "health_board_endpoint",
    "record_kpi_value_endpoint",
    "submit_review_endpoint",
    "update_objective_progress_endpoint",
]
