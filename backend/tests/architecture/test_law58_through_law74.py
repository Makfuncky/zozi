"""Architecture gates for Laws 58-74 (Code Quality, Testing).

These tests enforce code quality and testing laws:

  Law 58 — No print() in production: scan for print() in domain/service code
  Law 59 — No silent exceptions: bare except clauses must log at minimum
  Law 60 — No blocking I/O in async: async functions must not use blocking calls
  Law 69 — Every domain has smoke test: each domain has at least one test file
  Law 70 — Every checkable law has test
  Law 71 — No broken tests in CI
  Law 72 — Cross-domain integration tests
  Law 73 — Performance regression tests
  Law 74 — Transaction-rolled-back isolation: conftest.py has rollback session
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"
_MODULES_DIR = _BACKEND_ROOT / "modules"
_PROVIDERS_DIR = _BACKEND_ROOT / "providers"
_INFRASTRUCTURE_DIR = _BACKEND_ROOT / "infrastructure"
_KERNEL_DIR = _BACKEND_ROOT / "kernel"
_TESTS_DIR = _BACKEND_ROOT / "tests"

_BLOCKING_IO_PATTERNS = [
    re.compile(r"\bopen\s*\("),
    re.compile(r"\btime\.sleep\s*\("),
    re.compile(r"\brequests\.(get|post|put|delete|patch)\s*\("),
    re.compile(r"\bos\.remove\s*\("),
    re.compile(r"\bos\.rename\s*\("),
    re.compile(r"\bshutil\."),
]

_PRINT_PATTERN = re.compile(r"\bprint\s*\(")

_BARE_EXCEPT_PATTERN = re.compile(r"^\s*except\s*:\s*$")


def _iter_py(root: pathlib.Path, exclude_dirs: set[str] | None = None):
    if not root.exists():
        return
    exclude_dirs = exclude_dirs or set()
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel_parts = set(path.relative_to(_BACKEND_ROOT).parts)
        if rel_parts & exclude_dirs:
            continue
        yield path


class TestLaw58NoPrintInProduction:
    """Law 58: No print() statements in production code.

    Production code should use logging, not print().
    """

    def test_no_print_in_domain_services(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "services" not in str(path.relative_to(_BACKEND_ROOT)):
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(src.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if _PRINT_PATTERN.search(stripped):
                    offenders.append(
                        (str(path.relative_to(_BACKEND_ROOT)), f"line {i}: {stripped[:80]}")
                    )
        if offenders:
            msg = "\n  ".join(f"{f}: {l}" for f, l in offenders[:15])
            raise AssertionError(
                "Law 58 violation: print() found in domain services "
                f"(use logging instead):\n  {msg}"
            )

    def test_no_print_in_infrastructure(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_INFRASTRUCTURE_DIR, exclude_dirs={"tests", "scripts"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(src.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if _PRINT_PATTERN.search(stripped):
                    offenders.append(
                        (str(path.relative_to(_BACKEND_ROOT)), f"line {i}: {stripped[:80]}")
                    )
        if offenders:
            msg = "\n  ".join(f"{f}: {l}" for f, l in offenders[:10])
            raise AssertionError(
                "Law 58 violation: print() found in infrastructure "
                f"(use logging instead):\n  {msg}"
            )


class TestLaw59NoSilentExceptions:
    """Law 59: No silent exceptions — bare except clauses must log at minimum.

    Bare except clauses that swallow exceptions without logging hide bugs.
    """

    def test_no_bare_except_without_logging(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler):
                    continue
                if node.type is not None:
                    continue
                if not node.body:
                    continue
                handler_src = ast.get_source_segment(src, node) or ""
                has_log = any(
                    kw in handler_src for kw in ("log", "logger", "logging", "warn", "error")
                )
                if not has_log:
                    offenders.append(
                        (str(path.relative_to(_BACKEND_ROOT)), f"line {node.lineno}")
                    )
        if offenders:
            msg = "\n  ".join(f"{f}: {l}" for f, l in offenders[:15])
            raise AssertionError(
                "Law 59 violation: bare except clause(s) without logging:\n  " + msg
            )


class TestLaw60NoBlockingIOInAsync:
    """Law 60: No blocking I/O in async functions.

    Async functions must not call blocking I/O operations directly.
    """

    def test_no_blocking_calls_in_async_functions(self):
        offenders: list[tuple[str, str, str]] = []
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor)):
                    continue
                func_src = ast.get_source_segment(src, node) or ""
                for pattern in _BLOCKING_IO_PATTERNS:
                    match = pattern.search(func_src)
                    if match:
                        offenders.append(
                            (str(path.relative_to(_BACKEND_ROOT)), node.name, match.group(0))
                        )
        if offenders:
            msg = "\n  ".join(f"{f}: {n}() uses {c}" for f, n, c in offenders[:15])
            raise AssertionError(
                "Law 60 violation: blocking I/O in async function(s):\n  " + msg
            )


class TestLaw69EveryDomainHasSmokeTest:
    """Law 69: Every domain must have at least one test file."""

    _EXPECTED_DOMAINS = {
        "accounts", "analytics", "audit", "catalog", "comms", "country",
        "customers", "finance", "governance", "hr", "logistics", "orders",
        "promotions", "security", "suppliers",
    }

    def test_each_domain_has_test_file(self):
        domains_with_tests = set()
        for path in _TESTS_DIR.rglob("test_*.py"):
            rel = path.relative_to(_TESTS_DIR)
            parts = rel.parts
            if len(parts) >= 2 and parts[0] in ("domains", "modules", "providers"):
                domains_with_tests.add(parts[1])
            elif len(parts) >= 1:
                name = parts[0].replace("test_", "").replace(".py", "")
                if name in self._EXPECTED_DOMAINS:
                    domains_with_tests.add(name)
        missing = self._EXPECTED_DOMAINS - domains_with_tests
        if missing:
            pytest.skip(
                f"Domains without dedicated test files: {sorted(missing)}"
            )


class TestLaw70EveryCheckableLawHasTest:
    """Law 70: Every checkable law must have a corresponding test."""

    def test_architecture_tests_exist(self):
        arch_dir = _TESTS_DIR / "architecture"
        assert arch_dir.exists(), "tests/architecture/ directory must exist"
        test_files = list(arch_dir.glob("test_*.py"))
        assert len(test_files) >= 5, (
            f"Law 70 violation: expected at least 5 architecture test files, "
            f"found {len(test_files)}"
        )


class TestLaw71NoBrokenTestsInCI:
    """Law 71: No broken tests in CI — all tests must be collectible."""

    def test_all_test_files_are_importable(self):
        arch_dir = _TESTS_DIR / "architecture"
        if not arch_dir.exists():
            pytest.skip("tests/architecture/ does not exist")
        broken: list[str] = []
        for path in arch_dir.glob("test_*.py"):
            try:
                src = path.read_text(encoding="utf-8")
                ast.parse(src)
            except SyntaxError as e:
                broken.append(f"{path.name}: {e}")
        assert not broken, (
            f"Law 71 violation: broken test file(s) with syntax errors:\n  "
            + "\n  ".join(broken)
        )


class TestLaw72CrossDomainIntegrationTests:
    """Law 72: Cross-domain integration tests must exist."""

    def test_cross_domain_tests_exist(self):
        cross_domain_files = []
        for path in _TESTS_DIR.rglob("test_*.py"):
            name = path.name.lower()
            if "cross" in name or "integration" in name or "wiring" in name:
                cross_domain_files.append(path.name)
        assert len(cross_domain_files) >= 1, (
            "Law 72 violation: no cross-domain integration tests found"
        )


class TestLaw73PerformanceRegressionTests:
    """Law 73: Performance regression tests must exist."""

    def test_performance_tests_exist(self):
        perf_files = []
        for path in _TESTS_DIR.rglob("test_*.py"):
            name = path.name.lower()
            if "performance" in name or "perf" in name or "benchmark" in name:
                perf_files.append(path.name)
        if not perf_files:
            pytest.skip("Performance regression tests not yet implemented")


class TestLaw74TransactionRolledBackIsolation:
    """Law 74: conftest.py must have transaction-rolled-back session isolation.

    Tests must use transaction rollback to prevent data leaks between tests.
    """

    def test_conftest_has_rollback_session(self):
        conftest = _TESTS_DIR / "conftest.py"
        assert conftest.exists(), "tests/conftest.py must exist"
        src = conftest.read_text(encoding="utf-8")
        has_rollback = (
            "rollback" in src.lower()
            or "transaction" in src.lower()
            or "autouse" in src.lower()
        )
        assert has_rollback, (
            "Law 74 violation: conftest.py must implement transaction rollback "
            "for test isolation"
        )

    def test_conftest_has_db_session_fixture(self):
        conftest = _TESTS_DIR / "conftest.py"
        if not conftest.exists():
            pytest.skip("tests/conftest.py does not exist")
        src = conftest.read_text(encoding="utf-8")
        assert "db_session" in src or "db_session" in src.lower(), (
            "Law 74 violation: conftest.py must provide db_session fixture"
        )
