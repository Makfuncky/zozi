"""Verify AI task @shared_task decorators declare explicit per-task timeouts."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import os

os.environ.setdefault("APP_ENV", "test")

AI_TASKS_PATH = _BACKEND_ROOT / "jobs" / "ai_tasks.py"


def _get_shared_task_kwargs(node: ast.Call) -> dict[str, ast.Constant | ast.Num | ast.UnaryOp]:
    """Extract keyword arguments from an @shared_task(...) call."""
    kwargs = {}
    for keyword in node.keywords:
        kwargs[keyword.arg] = keyword.value
    return kwargs


def _get_constant_value(node: ast.Constant | ast.Num | ast.UnaryOp) -> int:
    """Get an integer value from an AST constant/number node."""
    if isinstance(node, ast.Constant):
        return int(node.value)
    if isinstance(node, ast.Num):
        return int(node.n)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_get_constant_value(node.operand)
    raise TypeError(f"Unsupported node type for constant: {type(node).__name__}")


def test_ai_tasks_have_explicit_time_limits():
    """Every @shared_task in jobs/ai_tasks.py must declare time_limit and soft_time_limit."""
    source = AI_TASKS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    task_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "shared_task"
                ):
                    kwargs = _get_shared_task_kwargs(decorator)
                    assert "time_limit" in kwargs, (
                        f"Task '{node.name}' is missing time_limit on @shared_task"
                    )
                    assert "soft_time_limit" in kwargs, (
                        f"Task '{node.name}' is missing soft_time_limit on @shared_task"
                    )
                    time_limit = _get_constant_value(kwargs["time_limit"])
                    soft_time_limit = _get_constant_value(kwargs["soft_time_limit"])
                    assert time_limit > 0, f"Task '{node.name}' has non-positive time_limit"
                    assert soft_time_limit > 0, f"Task '{node.name}' has non-positive soft_time_limit"
                    assert soft_time_limit < time_limit, (
                        f"Task '{node.name}' has soft_time_limit ({soft_time_limit}) "
                        f"not less than time_limit ({time_limit})"
                    )
                    task_names.append(node.name)

    # Ensure we actually found tasks to check
    assert task_names, "No @shared_task decorated functions found in ai_tasks.py"
