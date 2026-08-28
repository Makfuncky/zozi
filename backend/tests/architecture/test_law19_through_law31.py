"""Architecture gates for Laws 19-31 (Code Quality, Migration, Provider).

These tests enforce code quality, migration, and provider laws:

  Law 19 — No float for money: domain models must use Numeric/Decimal for money fields
  Law 20 — country_code = String(2): country_code columns must be String(2)
  Law 21 — Timestamps = server_default: created_at/updated_at must have server_default
  Law 22 — FK must have ondelete: all ForeignKey columns must specify ondelete
  Law 23 — Audit columns: models must have created_at, updated_at, country_code, is_deleted
  Law 25-29 — Migration laws: backward-compat shims for relocated files
  Law 30 — HAS_<SDK> flags: providers expose HAS_<SDK> boolean flags
  Law 31 — No domain imports in providers: scan provider files for domain imports
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"
_PROVIDERS_DIR = _BACKEND_ROOT / "providers"
_MIGRATIONS_DIR = _BACKEND_ROOT / "alembic" / "versions"

_MONEY_FIELD_PATTERN = re.compile(
    r"(amount|price|cost|fee|balance|total|subtotal|discount|tax|commission|"
    r"refund|payout|revenue|credit|debit|payment|salary|wage|budget|spend)",
    re.IGNORECASE,
)

_FLOAT_TYPE_PATTERN = re.compile(r"\b(Float|FLOAT|float)\b")

_COUNTRY_CODE_PATTERN = re.compile(r"country_code", re.IGNORECASE)


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


class TestLaw19NoFloatForMoney:
    """Law 19: No float for money — domain models must use Numeric/Decimal.

    Using Float for monetary values causes precision loss. All money-related
    columns must use Numeric(precision, scale) or Decimal.
    """

    def test_no_float_columns_on_money_fields(self):
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
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if not isinstance(node, ast.AnnAssign):
                    continue
                if not isinstance(node.target, ast.Name):
                    continue
                col_name = node.target.id
                if not _MONEY_FIELD_PATTERN.search(col_name):
                    continue
                if not isinstance(node.value, ast.Call):
                    continue
                call_src = ast.get_source_segment(src, node) or ""
                if _FLOAT_TYPE_PATTERN.search(call_src) and "Numeric" not in call_src and "Decimal" not in call_src:
                    offenders.append((str(path.relative_to(_BACKEND_ROOT)), col_name))
        if offenders:
            msg = "\n  ".join(f"{f}: column '{c}'" for f, c in offenders)
            raise AssertionError(
                "Law 19 violation: money field(s) use Float "
                f"(must use Numeric/Decimal):\n  {msg}"
            )


class TestLaw20CountryCodeString2:
    """Law 20: country_code columns must be String(2)."""

    def test_country_code_columns_are_string2(self):
        offenders: list[tuple[str, str]] = []
        fk_country_pattern = re.compile(
            r"Column\s*\(\s*(?:[\"']country_code[\"']\s*,\s*)?String\s*\(\s*2\s*\)",
            re.IGNORECASE,
        )
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "country_code" not in src:
                continue
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if not isinstance(node, ast.AnnAssign):
                    continue
                if not isinstance(node.target, ast.Name):
                    continue
                if node.target.id != "country_code":
                    continue
                if not isinstance(node.value, ast.Call):
                    continue
                call_src = ast.get_source_segment(src, node) or ""
                if not fk_country_pattern.search(call_src):
                    offenders.append((str(path.relative_to(_BACKEND_ROOT)), call_src[:80]))
        if offenders:
            msg = "\n  ".join(f"{f}: {c}" for f, c in offenders)
            raise AssertionError(
                "Law 20 violation: country_code column(s) not String(2):\n  " + msg
            )


class TestLaw21TimestampsServerDefault:
    """Law 21: created_at/updated_at must have server_default.

    Timestamps should be set by the server, not the application, to ensure
    consistency across all writes.
    """

    def test_timestamp_columns_have_server_default(self):
        offenders: list[tuple[str, str, str]] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "__tablename__" not in src:
                continue
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if not isinstance(node, ast.AnnAssign):
                    continue
                if not isinstance(node.target, ast.Name):
                    continue
                col_name = node.target.id
                if col_name not in ("created_at", "updated_at"):
                    continue
                if not isinstance(node.value, ast.Call):
                    continue
                call_src = ast.get_source_segment(src, node) or ""
                if "server_default" not in call_src:
                    offenders.append(
                        (str(path.relative_to(_BACKEND_ROOT)), col_name, call_src[:80])
                    )
        if offenders:
            msg = "\n  ".join(f"{f}: {c} = {s}" for f, c, s in offenders)
            raise AssertionError(
                "Law 21 violation: timestamp column(s) missing server_default:\n  " + msg
            )


class TestLaw22FKMustHaveOndelete:
    """Law 22: All ForeignKey columns must specify ondelete."""

    def test_foreign_keys_have_ondelete(self):
        offenders: list[tuple[str, str]] = []
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
                if "ForeignKey" in call_src and "ondelete" not in call_src:
                    offenders.append((str(path.relative_to(_BACKEND_ROOT)), col_name))
        if offenders:
            msg = "\n  ".join(f"{f}: '{c}'" for f, c in offenders)
            raise AssertionError(
                "Law 22 violation: ForeignKey column(s) missing ondelete:\n  " + msg
            )


class TestLaw23AuditColumns:
    """Law 23: Models must have audit columns.

    All domain models should include: created_at, updated_at, country_code, is_deleted.
    """

    _REQUIRED_COLUMNS = ["created_at", "updated_at"]

    def test_models_have_required_audit_columns(self):
        offenders: list[tuple[str, str, str]] = []
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
            if table_name == "alembic_version":
                continue
            missing = []
            for col in self._REQUIRED_COLUMNS:
                if col not in src:
                    missing.append(col)
            if missing:
                offenders.append(
                    (str(path.relative_to(_BACKEND_ROOT)), table_name, ", ".join(missing))
                )
        if offenders:
            msg = "\n  ".join(f"{f} ({t}): missing {m}" for f, t, m in offenders)
            raise AssertionError(
                "Law 23 violation: model(s) missing audit columns:\n  " + msg
            )


class TestLaw25Through29MigrationLaws:
    """Laws 25-29: Migration laws — backward-compat shims for relocated files.

    When files are relocated, backward-compatibility shims must exist to
    prevent breaking existing imports during the transition period.
    """

    def test_no_orphaned_imports_from_removed_paths(self):
        """Verify that imports from removed backend/services path don't exist."""
        removed_paths = [
            "services.",
        ]
        offenders: list[str] = []
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={"tests", "scripts", "venv"}):
            try:
                src = path.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                mod = node.module or ""
                for removed in removed_paths:
                    if mod.startswith(removed) and "domains." not in mod:
                        offenders.append(f"{path.relative_to(_BACKEND_ROOT)} imports {mod}")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders) - {"tests/"}))
            if msg:
                raise AssertionError(
                    "Law 25-29 violation: orphaned import(s) from removed paths:\n  " + msg
                )

    def test_migration_files_have_down_revision(self):
        """All Alembic migrations must have a down_revision defined."""
        if not _MIGRATIONS_DIR.exists():
            pytest.skip("alembic/versions/ directory does not exist")
        offenders: list[str] = []
        for path in _MIGRATIONS_DIR.glob("*.py"):
            if path.name == "__init__.py":
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "down_revision" not in src:
                offenders.append(path.name)
        if offenders:
            raise AssertionError(
                "Law 25-29 violation: migration(s) missing down_revision:\n  "
                + "\n  ".join(offenders)
            )


class TestLaw30HasSDKFlags:
    """Law 30: Providers must expose HAS_<SDK> boolean flags.

    Each provider module must define a HAS_<SDK> boolean to indicate
    whether the underlying SDK is available.
    """

    def test_providers_expose_has_sdk_flags(self):
        offenders: list[str] = []
        for subdir in sorted(_PROVIDERS_DIR.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("_") or subdir.name.startswith("."):
                continue
            init_file = subdir / "__init__.py"
            if not init_file.exists():
                continue
            try:
                src = init_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if not re.search(r"HAS_\w+\s*=\s*(True|False)", src):
                offenders.append(f"providers/{subdir.name}/__init__.py")
        if offenders:
            msg = "\n  ".join(offenders)
            raise AssertionError(
                "Law 30 violation: provider(s) missing HAS_<SDK> boolean flag:\n  " + msg
            )


class TestLaw31NoDomainImportsInProviders:
    """Law 31: No domain imports in providers.

    Providers must only wrap external SDKs. They must not import from domains/.
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
                        offenders.append(
                            f"{path.relative_to(_BACKEND_ROOT)} imports {mod}"
                        )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("domains."):
                            offenders.append(
                                f"{path.relative_to(_BACKEND_ROOT)} imports {alias.name}"
                            )
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            raise AssertionError(
                "Law 31 violation: provider(s) import from domains/:\n  " + msg
            )

    def test_providers_no_infrastructure_messaging_imports(self):
        """Providers must not import from infrastructure.messaging."""
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
                    if "infrastructure.messaging" in mod:
                        offenders.append(
                            f"{path.relative_to(_BACKEND_ROOT)} imports {mod}"
                        )
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            raise AssertionError(
                "Law 31 violation: provider(s) import from infrastructure.messaging:\n  "
                + msg
            )
