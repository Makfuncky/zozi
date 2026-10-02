"""Verify email task @shared_task decorators declare exponential backoff and per-task timeouts."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import os

os.environ.setdefault("APP_ENV", "test")

EMAIL_TASKS_PATH = _BACKEND_ROOT / "jobs" / "email_tasks.py"


def _get_shared_task_kwargs(node: ast.Call) -> dict[str, ast.expr]:
    kwargs = {}
    for keyword in node.keywords:
        kwargs[keyword.arg] = keyword.value
    return kwargs


def _get_constant_value(node: ast.expr) -> int:
    if isinstance(node, ast.Constant):
        return int(node.value)
    if isinstance(node, ast.Num):
        return int(node.n)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_get_constant_value(node.operand)
    raise TypeError(f"Unsupported node type for constant: {type(node).__name__}")


def test_email_tasks_have_exponential_backoff():
    source = EMAIL_TASKS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    task_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "shared_task"
                ):
                    kwargs = _get_shared_task_kwargs(decorator)
                    task_names.append(node.name)
                    if node.name == "health_check":
                        continue
                    assert "default_retry_delay" not in kwargs, (
                        f"Task '{node.name}' uses deprecated default_retry_delay; "
                        "use retry_backoff=True, retry_jitter=True instead"
                    )
                    assert "retry_backoff" in kwargs, (
                        f"Task '{node.name}' is missing retry_backoff"
                    )
                    assert "retry_jitter" in kwargs, (
                        f"Task '{node.name}' is missing retry_jitter"
                    )
                    assert "retry_backoff_max" in kwargs, (
                        f"Task '{node.name}' is missing retry_backoff_max"
                    )

    assert task_names, "No @shared_task decorated functions found in email_tasks.py"


def test_email_tasks_have_explicit_time_limits():
    source = EMAIL_TASKS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    task_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "shared_task"
                ):
                    kwargs = _get_shared_task_kwargs(decorator)
                    task_names.append(node.name)
                    if node.name == "health_check":
                        continue
                    assert "time_limit" in kwargs, (
                        f"Task '{node.name}' is missing time_limit on @shared_task"
                    )
                    assert "soft_time_limit" in kwargs, (
                        f"Task '{node.name}' is missing soft_time_limit on @shared_task"
                    )
                    time_limit = _get_constant_value(kwargs["time_limit"])
                    soft_time_limit = _get_constant_value(kwargs["soft_time_limit"])
                    assert time_limit > 0, f"Task '{node.name}' has non-positive time_limit"
                    assert soft_time_limit > 0, (
                        f"Task '{node.name}' has non-positive soft_time_limit"
                    )
                    assert soft_time_limit < time_limit, (
                        f"Task '{node.name}' has soft_time_limit ({soft_time_limit}) "
                        f"not less than time_limit ({time_limit})"
                    )

    assert task_names, "No @shared_task decorated functions found in email_tasks.py"
