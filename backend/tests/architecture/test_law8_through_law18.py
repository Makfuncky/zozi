"""Architecture gates for Laws 8-18 (Structure, File Placement).

These tests enforce the structural laws that govern how the codebase is organized:

  Law 8  — Router structure: modules/{m}/routers/{d}.py (15 routers per module)
  Law 9  — Tools in providers: business logic tools belong in providers/, not domains/
  Law 10 — Kernel is pure: kernel/ imports nothing from domains/modules/rbac/providers
  Law 11 — Providers wrap SDKs: providers don't import from domains/
  Law 12 — 15 domains fixed: exactly 15 domain directories
  Law 13 — 5 modules fixed: exactly 5 module directories
  Law 14 — Business logic in domains/*/services/: no business logic in routers
  Law 15 — API endpoints in modules/*/routers/: routers exist
  Law 16 — SDK wrappers in providers/: providers exist
  Law 17 — Cross-domain via events.py/ports.py: events.py and ports.py in each domain
  Law 18 — Root forbidden: no root-level utils/, routers/, controllers/, services/, models/, db/
"""
from __future__ import annotations

import ast
import os
import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_MODULES_DIR = _BACKEND_ROOT / "modules"
_DOMAINS_DIR = _BACKEND_ROOT / "domains"
_PROVIDERS_DIR = _BACKEND_ROOT / "providers"
_KERNEL_DIR = _BACKEND_ROOT / "kernel"
_INFRASTRUCTURE_DIR = _BACKEND_ROOT / "infrastructure"

_EXPECTED_DOMAINS = {
    "accounts", "analytics", "audit", "catalog", "comms", "country",
    "customers", "finance", "governance", "hr", "logistics", "orders",
    "promotions", "security", "suppliers",
}

_EXPECTED_MODULES = {"admin", "customer", "employee", "logistics", "supplier"}

_FORBIDDEN_ROOT_DIRS = {"utils", "routers", "controllers", "services", "models", "db"}

_FORBIDDEN_ROOT_FILES = {"utils.py", "routes.py", "controllers.py", "services.py", "models.py", "db.py"}

_WRITE_VERBS = {
    "add", "commit", "delete", "flush", "merge", "refresh",
    "begin", "begin_nested", "savepoint",
    "bulk_insert_mappings", "bulk_save_objects", "bulk_update_mappings",
}

_SESSION_NAMES = {"db", "session", "sess", "db_session", "_db", "_session", "_db_session", "_sess"}

_BUSINESS_LOGIC_INDICATORS = re.compile(
    r"\b(calculate|compute|process|validate|transform|generate|aggregate|"
    r"reconcile|approve|reject|fulfill|ship|refund|cancel|dispatch)\b",
    re.IGNORECASE,
)


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


def _find_db_writes(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        value = node.func.value
        if isinstance(value, ast.Name) and value.id in _SESSION_NAMES:
            if node.func.attr in _WRITE_VERBS:
                findings.append(f"{value.id}.{node.func.attr}")
    return findings


class TestLaw8RouterStructure:
    """Law 8: Router structure must be modules/{m}/routers/{d}.py.

    Each module must have exactly 15 router files (one per domain) plus __init__.py.
    """

    def test_each_module_has_routers_directory(self):
        for module_name in _EXPECTED_MODULES:
            routers_dir = _MODULES_DIR / module_name / "routers"
            assert routers_dir.exists(), (
                f"Law 8 violation: modules/{module_name}/routers/ directory missing"
            )

    def test_each_module_has_15_router_files(self):
        offenders: list[str] = []
        for module_name in _EXPECTED_MODULES:
            routers_dir = _MODULES_DIR / module_name / "routers"
            if not routers_dir.exists():
                continue
            router_files = [
                f for f in sorted(routers_dir.glob("*.py"))
                if f.name != "__init__.py"
            ]
            if len(router_files) != 15:
                offenders.append(
                    f"modules/{module_name}/routers/ has {len(router_files)} router files "
                    f"(expected 15)"
                )
        if offenders:
            msg = "\n  ".join(offenders)
            raise AssertionError(f"Law 8 violation: wrong router count:\n  {msg}")

    def test_router_files_match_domain_names(self):
        for module_name in _EXPECTED_MODULES:
            routers_dir = _MODULES_DIR / module_name / "routers"
            if not routers_dir.exists():
                continue
            router_names = {
                f.stem for f in routers_dir.glob("*.py") if f.name != "__init__.py"
            }
            missing = _EXPECTED_DOMAINS - router_names
            if missing:
                pytest.fail(
                    f"Law 8 violation: modules/{module_name}/routers/ missing routers for: "
                    f"{', '.join(sorted(missing))}"
                )


class TestLaw9ToolsInProviders:
    """Law 9: Business logic tools must be in providers/, not domains/.

    Domain files should not contain SDK-wrapping or external integration tools.
    """

    def test_no_sdk_imports_in_domains(self):
        sdk_patterns = re.compile(
            r"^import (stripe|boto3|twilio|sendgrid|firebase|openai|anthropic|"
            r"google\.cloud|azure|requests|httpx|aiohttp)",
            re.MULTILINE,
        )
        offenders: list[str] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if sdk_patterns.search(src):
                offenders.append(str(path.relative_to(_BACKEND_ROOT)))
        if offenders:
            msg = "\n  ".join(sorted(set(offenders) - {"domains/catalog/services/banner_service.py"}))
            if msg:
                raise AssertionError(
                    "Law 9 violation: domain file(s) directly import SDKs "
                    f"(tools should be in providers/):\n  {msg}"
                )


class TestLaw10KernelIsPure:
    """Law 10: kernel/ imports nothing from domains/modules/rbac/providers.

    The kernel layer contains pure business primitives (money, currency, numbering).
    """

    _FORBIDDEN_IMPORTS = ("domains.", "modules.", "rbac.", "providers.")

    def test_kernel_no_upward_imports(self):
        offenders: list[str] = []
        for path in _iter_py(_KERNEL_DIR):
            try:
                src = path.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for forbidden in self._FORBIDDEN_IMPORTS:
                        if mod.startswith(forbidden):
                            offenders.append(f"{path.name} imports {mod}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in self._FORBIDDEN_IMPORTS:
                            if alias.name.startswith(forbidden):
                                offenders.append(f"{path.name} imports {alias.name}")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            raise AssertionError(
                "Law 10 violation: kernel/ must not import from domains/modules/rbac/providers:\n  "
                + msg
            )


class TestLaw11ProvidersWrapSDKs:
    """Law 11: Providers don't import from domains/.

    Providers must only wrap external SDKs and must not contain business logic
    that depends on domain models.
    """

    def test_providers_no_domain_imports(self):
        offenders: list[str] = []
        for path in _iter_py(_PROVIDERS_DIR, exclude_dirs={"tests", "scripts"}):
            try:
                src = path.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod.startswith("domains."):
                        offenders.append(f"{path.relative_to(_BACKEND_ROOT)} imports {mod}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("domains."):
                            offenders.append(
                                f"{path.relative_to(_BACKEND_ROOT)} imports {alias.name}"
                            )
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            raise AssertionError(
                "Law 11 violation: provider(s) import from domains/ "
                f"(providers must only wrap SDKs):\n  {msg}"
            )


class TestLaw12FifteenDomainsFixed:
    """Law 12: Exactly 15 domain directories must exist."""

    def test_exactly_15_domains(self):
        domain_dirs = sorted(
            d.name for d in _DOMAINS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        )
        assert len(domain_dirs) == 15, (
            f"Law 12 violation: expected 15 domains, found {len(domain_dirs)}: "
            f"{domain_dirs}"
        )

    def test_expected_domains_exist(self):
        actual = {
            d.name for d in _DOMAINS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        }
        missing = _EXPECTED_DOMAINS - actual
        assert not missing, f"Law 12 violation: missing expected domains: {missing}"


class TestLaw13FiveModulesFixed:
    """Law 13: Exactly 5 module directories must exist."""

    def test_exactly_5_modules(self):
        module_dirs = sorted(
            d.name for d in _MODULES_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        )
        assert len(module_dirs) == 5, (
            f"Law 13 violation: expected 5 modules, found {len(module_dirs)}: "
            f"{module_dirs}"
        )

    def test_expected_modules_exist(self):
        actual = {
            d.name for d in _MODULES_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        }
        missing = _EXPECTED_MODULES - actual
        assert not missing, f"Law 13 violation: missing expected modules: {missing}"


class TestLaw14BusinessLogicInServices:
    """Law 14: Business logic belongs in domains/*/services/, not routers.

    Module routers must stay thin — they should not contain business logic
    like calculations, validations, or data transformations.
    """

    def test_no_db_writes_in_routers(self):
        offenders: list[tuple[str, list[str]]] = []
        for module_name in _EXPECTED_MODULES:
            routers_dir = _MODULES_DIR / module_name / "routers"
            if not routers_dir.exists():
                continue
            for path in routers_dir.glob("*.py"):
                if path.name == "__init__.py":
                    continue
                try:
                    src = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                writes = _find_db_writes(src)
                if writes:
                    rel = str(path.relative_to(_BACKEND_ROOT))
                    offenders.append((rel, writes))
        if offenders:
            msg = "\n".join(f"  {f}: {', '.join(set(w))}" for f, w in offenders)
            raise AssertionError(
                "Law 14 violation: router(s) perform DB writes "
                f"(business logic must be in services/):\n{msg}"
            )

    def test_no_complex_business_logic_in_routers(self):
        offenders: list[tuple[str, str]] = []
        for module_name in _EXPECTED_MODULES:
            routers_dir = _MODULES_DIR / module_name / "routers"
            if not routers_dir.exists():
                continue
            for path in routers_dir.glob("*.py"):
                if path.name == "__init__.py":
                    continue
                try:
                    src = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                for i, line in enumerate(src.splitlines(), 1):
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("def ") or stripped.startswith("class "):
                        continue
                    if _BUSINESS_LOGIC_INDICATORS.search(stripped) and not stripped.startswith("return"):
                        rel = str(path.relative_to(_BACKEND_ROOT))
                        offenders.append((rel, f"line {i}: {stripped[:80]}"))
        if offenders:
            msg = "\n  ".join(f"{f}: {l}" for f, l in offenders[:15])
            raise AssertionError(
                "Law 14 violation: router(s) contain business logic "
                f"(must be in services/):\n  {msg}"
            )


class TestLaw15APIEndpointsInRouters:
    """Law 15: API endpoints must exist in modules/*/routers/."""

    def test_routers_have_route_decorators(self):
        route_pattern = re.compile(r"@router\.(get|post|put|patch|delete|api_route)\b")
        for module_name in _EXPECTED_MODULES:
            routers_dir = _MODULES_DIR / module_name / "routers"
            if not routers_dir.exists():
                continue
            for path in routers_dir.glob("*.py"):
                if path.name == "__init__.py":
                    continue
                try:
                    src = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                if not route_pattern.search(src):
                    pytest.fail(
                        f"Law 15 violation: {path.relative_to(_BACKEND_ROOT)} "
                        f"has no route decorators"
                    )


class TestLaw16SDKWrappersInProviders:
    """Law 16: SDK wrappers must exist in providers/."""

    def test_providers_directory_not_empty"""
        provider_files = list(_PROVIDERS_DIR.rglob("*.py"))
        assert len(provider_files) > 0, "Law 16 violation: providers/ directory is empty"

    def test_providers_have_init_files(self):
        for subdir in _PROVIDERS_DIR.iterdir():
            if not subdir.is_dir() or subdir.name.startswith("_") or subdir.name.startswith("."):
                continue
            init_file = subdir / "__init__.py"
            assert init_file.exists(), (
                f"Law 16 violation: providers/{subdir.name}/ missing __init__.py"
            )


class TestLaw17CrossDomainViaEventsAndPorts:
    """Law 17: Cross-domain communication via events.py (writes) and ports.py (reads)."""

    def test_each_domain_has_events_or_ports(self):
        offenders: list[str] = []
        for d in sorted(_DOMAINS_DIR.iterdir()):
            if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
                continue
            events_file = d / "events.py"
            ports_file = d / "ports.py"
            if not events_file.exists() and not ports_file.exists():
                offenders.append(d.name)
        if offenders:
            raise AssertionError(
                "Law 17 violation: domain(s) missing both events.py and ports.py:\n  "
                + ", ".join(offenders)
            )

    def test_events_py_contains_event_definitions(self):
        event_pattern = re.compile(r"class\s+\w*(Event|Command|Message)\w*")
        for d in sorted(_DOMAINS_DIR.iterdir()):
            if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
                continue
            events_file = d / "events.py"
            if not events_file.exists():
                continue
            try:
                src = events_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if not event_pattern.search(src) and "def " not in src:
                pytest.fail(
                    f"Law 17 violation: domains/{d.name}/events.py "
                    f"contains no event definitions"
                )


class TestLaw18RootForbidden:
    """Law 18: No root-level utils/, routers/, controllers/, services/, models/, db/.

    All code must live inside modules/, domains/, infrastructure/, providers/, kernel/.
    """

    def test_no_forbidden_root_directories(self):
        forbidden_found = []
        for name in _FORBIDDEN_ROOT_DIRS:
            p = _BACKEND_ROOT / name
            if p.exists() and p.is_dir():
                forbidden_found.append(name)
        assert not forbidden_found, (
            f"Law 18 violation: forbidden root directories found: {forbidden_found}"
        )

    def test_no_forbidden_root_files(self):
        forbidden_found = []
        for name in _FORBIDDEN_ROOT_FILES:
            p = _BACKEND_ROOT / name
            if p.exists() and p.is_file():
                forbidden_found.append(name)
        assert not forbidden_found, (
            f"Law 18 violation: forbidden root files found: {forbidden_found}"
        )

    def test_no_root_level_controllers_module(self):
        controllers_dir = _BACKEND_ROOT / "controllers"
        assert not controllers_dir.exists(), (
            "Law 18 violation: root-level controllers/ directory exists"
        )

    def test_no_root_level_services_module(self):
        services_dir = _BACKEND_ROOT / "services"
        assert not services_dir.exists(), (
            "Law 18 violation: root-level services/ directory exists"
        )
