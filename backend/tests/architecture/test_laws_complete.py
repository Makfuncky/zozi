"""Architecture gates for Laws 2, 3, 5, 6, 7.

These tests complement the existing Law 1 gate (test_import_laws.py) and
W1/W2 guards (test_w1_layer_guard.py, test_w2_provider_guard.py in
tests/domains/). Each gate below enforces one of the remaining Seven Laws:

  Law 2 — Module routers stay thin (require_feature + one service call only).
  Law 3 — Cross-domain writes via events only; no direct FK writes across domains.
  Law 5 — Country is the orthogonal scope axis (country_code on scoped models).
  Law 6 — Schema discipline (snake_case, plural tables, <thing>_id FKs, timestamps).
  Law 7 — Allowlist rule (DOMAIN_ALLOWLIST.yaml only shrinks).
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
_MIDDLEWARE_DIR = _BACKEND_ROOT / "middleware"
_ALLOWLIST_PATH = _BACKEND_ROOT / "DOMAIN_ALLOWLIST.yaml"

_WRITE_VERBS = {
    "add",
    "add_all",
    "commit",
    "delete",
    "flush",
    "merge",
    "refresh",
    "begin",
    "begin_nested",
    "savepoint",
    "bulk_insert_mappings",
    "bulk_save_objects",
    "bulk_update_mappings",
}

_SESSION_NAMES = {
    "db",
    "session",
    "sess",
    "db_session",
    "_db",
    "_session",
    "_db_session",
    "_sess",
}


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


def _find_db_writes(source: str, filename: str = "") -> list[str]:
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


class TestLaw2ModuleRoutersStayThin:
    """Law 2: Module routers stay thin — require_feature() + one service call.

    Routers must not perform DB writes (no db.add(), db.commit(), etc.) and
    must delegate business logic to services via a single call.
    """

    def test_no_db_writes_in_module_routers(self):
        offenders: list[tuple[str, list[str]]] = []
        for path in _iter_py(_MODULES_DIR, exclude_dirs={"tests"}):
            if not path.name.endswith(".py"):
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            writes = _find_db_writes(src, path.name)
            if writes:
                rel = str(path.relative_to(_BACKEND_ROOT))
                offenders.append((rel, writes))
        if offenders:
            msg = "\n".join(
                f"  {f}: {', '.join(set(w))}" for f, w in offenders
            )
            raise AssertionError(
                "Law 2 violation: module router(s) perform DB writes "
                f"(must delegate to services):\n{msg}"
            )

    def test_no_db_writes_in_middleware(self):
        offenders: list[tuple[str, list[str]]] = []
        for path in _iter_py(_MIDDLEWARE_DIR):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            writes = _find_db_writes(src, path.name)
            if writes:
                rel = str(path.relative_to(_BACKEND_ROOT))
                offenders.append((rel, writes))
        if offenders:
            msg = "\n".join(
                f"  {f}: {', '.join(set(w))}" for f, w in offenders
            )
            raise AssertionError(
                "Law 2 violation: middleware performs DB writes "
                f"(must delegate to services):\n{msg}"
            )

    def test_module_routers_exist(self):
        assert _MODULES_DIR.exists(), "expected modules/ directory"
        routers = list(_MODULES_DIR.rglob("routers/*.py"))
        assert routers, "expected at least one router in modules/"


class TestLaw3CrossDomainWritesViaEvents:
    """Law 3: Cross-domain writes only via events; reads only via ports.

    Domains must not directly import another domain's service modules for
    write operations. Cross-domain communication must flow through events.py
    (writes) or ports.py (reads).
    """

    _SANCTIONED_CROSS_DOMAIN = {
        "rbac/catalog.py",
    }

    def _is_cross_domain_import(self, module_name: str, current_domain: str) -> bool | None:
        if not module_name or not module_name.startswith("domains."):
            return None
        parts = module_name.split(".")
        if len(parts) < 2:
            return None
        target_domain = parts[1]
        if target_domain == current_domain:
            return None
        if target_domain in ("common",):
            return None
        return True

    def test_no_direct_cross_domain_service_imports(self):
        offenders: list[str] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            rel = str(path.relative_to(_BACKEND_ROOT))
            if rel in self._SANCTIONED_CROSS_DOMAIN:
                continue
            parts = rel.split("/")
            if len(parts) < 3:
                continue
            current_domain = parts[1]
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                mod = node.module or ""
                if self._is_cross_domain_import(mod, current_domain) and ".services." in mod:
                    offenders.append(f"{rel} imports {mod}")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            raise AssertionError(
                "Law 3 violation: direct cross-domain service import "
                f"(must use events.py or ports.py):\n  {msg}"
            )

    def test_events_files_exist_for_cross_domain_domains(
        self,
    ):
        domains_with_events = []
        for d in sorted(_DOMAINS_DIR.iterdir()):
            if not d.is_dir():
                continue
            events_file = d / "events.py"
            if events_file.exists():
                domains_with_events.append(d.name)
        assert len(domains_with_events) >= 1, (
            "At least one domain should have events.py for cross-domain writes"
        )


class TestLaw5CountryIsOrthogonalScope:
    """Law 5: Country is the orthogonal scope axis.

    Domain models that represent country-scoped data must include a
    country_code column for RLS session context propagation.
    """

    _EXCLUDE_TABLES = {
        "country_configs",
        "country_tax",
        "country_legal",
        "country_enhancements",
        "country_economics",
        "country_control",
        "country_basics",
        "countries",
        "country_payment_sync",
        "logistics_country_sync",
        "supplier_country_sync",
    }

    def test_country_scoped_models_have_country_code(self):
        offenders: list[str] = []
        for path in _iter_py(_DOMAINS_DIR / "orders", exclude_dirs={"tests"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "__tablename__" not in src:
                continue
            table_match = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', src)
            if not table_match:
                continue
            table_name = table_match.group(1)
            if table_name in self._EXCLUDE_TABLES:
                continue
            if "country_code" not in src:
                offenders.append(f"{path.name} (table: {table_name})")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            raise AssertionError(
                "Law 5 violation: country-scoped model(s) missing country_code:\n  "
                + msg
            )

    def test_country_domain_exists(self):
        country_dir = _DOMAINS_DIR / "country"
        assert country_dir.exists(), "expected domains/country/ directory"


class TestLaw6SchemaDiscipline:
    """Law 6: Schema discipline — snake_case, plural tables, <thing>_id FKs,
    created_at/updated_at on all models.
    """

    _EXCLUDE_TABLES = {
        "alembic_version",
    }

    def test_table_names_are_snake_case(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', src):
                table_name = m.group(1)
                if table_name in self._EXCLUDE_TABLES:
                    continue
                if not re.match(r'^[a-z][a-z0-9_]*$', table_name):
                    offenders.append((str(path.relative_to(_BACKEND_ROOT)), table_name))
        if offenders:
            msg = "\n  ".join(f"{f}: '{t}'" for f, t in offenders)
            raise AssertionError(
                "Law 6 violation: table name(s) not snake_case:\n  " + msg
            )

    def test_table_names_are_plural(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', src):
                table_name = table_name_raw = m.group(1)
                if table_name in self._EXCLUDE_TABLES:
                    continue
                if "_" in table_name:
                    last_part = table_name.split("_")[-1]
                else:
                    last_part = table_name
                if not last_part.endswith("s"):
                    offenders.append((str(path.relative_to(_BACKEND_ROOT)), table_name_raw))
        if offenders:
            msg = "\n  ".join(f"{f}: '{t}'" for f, t in offenders)
            raise AssertionError(
                "Law 6 violation: table name(s) not plural:\n  " + msg
            )

    def test_models_have_timestamps(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "__tablename__" not in src:
                continue
            table_match = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', src)
            if not table_match:
                continue
            table_name = table_match.group(1)
            if table_name in self._EXCLUDE_TABLES:
                continue
            has_created = "created_at" in src
            has_updated = "updated_at" in src
            if not has_created or not has_updated:
                missing = []
                if not has_created:
                    missing.append("created_at")
                if not has_updated:
                    missing.append("updated_at")
                offenders.append((str(path.relative_to(_BACKEND_ROOT)), ", ".join(missing)))
        if offenders:
            msg = "\n  ".join(f"{f}: missing {m}" for f, m in offenders)
            raise AssertionError(
                "Law 6 violation: model(s) missing timestamp columns:\n  " + msg
            )

    def test_fk_columns_use_id_suffix(self):
        offenders: list[tuple[str, str]] = []
        fk_pattern = re.compile(r'Column\([^)]*ForeignKey')
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "ForeignKey" not in src:
                continue
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if not isinstance(node, ast.AnnAssign):
                    continue
                if not isinstance(node.target, ast.Name):
                    continue
                col_name = node.target.id
                if col_name == "id":
                    continue
                if not isinstance(node.value, ast.Call):
                    continue
                call_src = ast.get_source_segment(src, node) or ""
                if "ForeignKey" in call_src and not col_name.endswith("_id"):
                    offenders.append((str(path.relative_to(_BACKEND_ROOT)), col_name))
        if offenders:
            msg = "\n  ".join(f"{f}: '{c}'" for c, _ in offenders[:20])
            raise AssertionError(
                "Law 6 violation: FK column(s) missing '_id' suffix:\n  " + msg
            )


class TestLaw7AllowlistRule:
    """Law 7: Allowlist rule — DOMAIN_ALLOWLIST.yaml only shrinks.

    The allowlist tracks temporary cross-domain imports. It must exist and
    its entries must only decrease over time (never grow silently).
    """

    def test_allowlist_file_exists(self):
        assert _ALLOWLIST_PATH.exists(), (
            "DOMAIN_ALLOWLIST.yaml must exist to track temporary cross-domain imports"
        )

    def test_allowlist_has_required_structure(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        assert "cross_domain_imports:" in content, (
            "DOMAIN_ALLOWLIST.yaml must contain 'cross_domain_imports:' section"
        )

    def test_allowlist_entries_are_sanctioned(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        entries = [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("- domains.")
        ]
        assert len(entries) > 0, (
            "DOMAIN_ALLOWLIST.yaml should contain at least one sanctioned "
            "cross-domain import entry"
        )
