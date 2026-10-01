"""Regression tests for per-task time_limit / soft_time_limit on ai_tasks jobs."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

# We avoid importing jobs.ai_tasks directly because jobs.celery_app has a
# pre-existing Celery 5.5 signals compatibility issue (outside this file's scope).
AI_TASKS_PATH = Path(__file__).resolve().parents[2] / "jobs" / "ai_tasks.py"

EXPECTED_TIMEOUTS = {
    "remove_background": (300, 240),
    "analyze_product_image": (180, 120),
    "generate_angles": (600, 540),
    "nlp_extract": (300, 240),
    "health_check": (30, 25),
}


def _get_decorator_kwargs(node: ast.AST) -> dict[str, ast.constant | int]:
    """Extract keyword arguments from a @shared_task(...) decorator call."""
    if not isinstance(node, ast.Call):
        return {}
    kwargs = {}
    for keyword in node.keywords:
        if isinstance(keyword.value, ast.Constant):
            kwargs[keyword.arg] = keyword.value.value
        elif isinstance(keyword.value, ast.UnaryOp) and isinstance(
            keyword.value.op, ast.USub
        ):
            kwargs[keyword.arg] = -keyword.value.operand.value  # type: ignore[attr-defined]
        elif isinstance(keyword.value, ast.Num):  # pragma: no cover - PY<39
            kwargs[keyword.arg] = keyword.value.n
    return kwargs


def _load_ai_tasks_ast() -> ast.Module:
    """Parse ai_tasks.py and return its AST."""
    source = AI_TASKS_PATH.read_text(encoding="utf-8")
    return ast.parse(source)


def test_all_ai_tasks_have_time_limit_and_soft_time_limit() -> None:
    """Every @shared_task in ai_tasks.py must declare time_limit and soft_time_limit."""
    tree = _load_ai_tasks_ast()
    found_tasks: dict[str, dict[str, int]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Name):
                continue
            if decorator.func.id != "shared_task":
                continue
            kwargs = _get_decorator_kwargs(decorator)
            name_value = kwargs.get("name", "")
            if not isinstance(name_value, str) or not name_value.startswith(
                "tasks.ai_tasks."
            ):
                continue
            task_short_name = name_value.replace("tasks.ai_tasks.", "")
            found_tasks[task_short_name] = {
                "time_limit": kwargs.get("time_limit"),
                "soft_time_limit": kwargs.get("soft_time_limit"),
            }

    for task_name, (expected_tl, expected_stl) in EXPECTED_TIMEOUTS.items():
        assert task_name in found_tasks, f"Task {task_name} not found in ai_tasks.py"
        actual_tl = found_tasks[task_name]["time_limit"]
        actual_stl = found_tasks[task_name]["soft_time_limit"]
        assert actual_tl == expected_tl, (
            f"{task_name}.time_limit expected {expected_tl}, got {actual_tl}"
        )
        assert actual_stl == expected_stl, (
            f"{task_name}.soft_time_limit expected {expected_stl}, got {actual_stl}"
        )


def test_no_ai_task_missing_timeout_kwargs() -> None:
    """No @shared_task in ai_tasks.py may omit time_limit or soft_time_limit."""
    tree = _load_ai_tasks_ast()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Name):
                continue
            if decorator.func.id != "shared_task":
                continue
            kwargs = _get_decorator_kwargs(decorator)
            name_value = kwargs.get("name", "")
            if not isinstance(name_value, str) or not name_value.startswith(
                "tasks.ai_tasks."
            ):
                continue
            assert "time_limit" in kwargs, (
                f"@shared_task({name_value}) missing time_limit"
            )
            assert "soft_time_limit" in kwargs, (
                f"@shared_task({name_value}) missing soft_time_limit"
            )


def test_timeout_invariant_soft_below_hard() -> None:
    """soft_time_limit must be strictly less than time_limit for every ai task."""
    for task_name, (hard, soft) in EXPECTED_TIMEOUTS.items():
        assert soft < hard, (
            f"{task_name}: soft_time_limit ({soft}) must be < time_limit ({hard})"
        )


def test_invalid_timeout_configuration_rejected() -> None:
    """A timeout spec with soft_time_limit >= time_limit must be rejected."""
    with pytest.raises(ValueError):
        _validate_timeout_spec(time_limit=10, soft_time_limit=20)


def _validate_timeout_spec(*, time_limit: int | None, soft_time_limit: int | None) -> None:
    """Validate that a timeout specification is sane."""
    if time_limit is None or soft_time_limit is None:
        raise ValueError("Both time_limit and soft_time_limit must be set")
    if soft_time_limit >= time_limit:
        raise ValueError(
            f"soft_time_limit ({soft_time_limit}) must be < time_limit ({time_limit})"
        )
    if time_limit <= 0:
        raise ValueError(f"time_limit must be positive, got {time_limit}")
