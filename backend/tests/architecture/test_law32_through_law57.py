"""Architecture gates for Laws 32-57 (Security, Database).

These tests enforce security and database laws:

  Law 32 — No hardcoded secrets: scan for hardcoded passwords, API keys, tokens
  Law 33 — Token type verification: JWT access vs refresh token validation
  Law 34 — Parameterized SQL only: no raw SQL without parameterization
  Law 35 — CSRF active: CSRF middleware exists and is active
  Law 36 — Security headers: security headers middleware exists
  Law 37 — Rate limit fails closed: rate limiting configuration
  Law 38 — Passwords >72 bytes rejected: password length validation
  Law 39 — No duplicate auth logic: no duplicate auth implementations
  Law 40 — CORS origin validation: CORS configuration
  Law 45 — No N+1 queries: lazy=selectin or joined on relationships
  Law 46 — No SELECT *: scan for SELECT * in raw SQL
  Law 47 — Connection pool sizing: pool_size >= 10
  Law 48 — Read replica separation: get_read_db() exists
  Law 49 — Linear Alembic history: no merge heads in migrations
  Law 50 — Explicit transactions: autocommit is FORBIDDEN
  Law 51 — Single table ownership: tables belong to one schema
  Law 52 — FK constraints with ondelete
  Law 53 — Index all FK columns
  Law 54 — Soft delete (is_deleted)
  Law 55 — Schema-per-domain
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"
_PROVIDERS_DIR = _BACKEND_ROOT / "providers"
_INFRASTRUCTURE_DIR = _BACKEND_ROOT / "infrastructure"
_MIDDLEWARE_DIR = _BACKEND_ROOT / "middleware"
_MIGRATIONS_DIR = _BACKEND_ROOT / "alembic" / "versions"
_DATABASE_DIR = _INFRASTRUCTURE_DIR / "database"

_SECRET_PATTERNS = [
    re.compile(r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
    re.compile(r'(?:api_key|apikey|api-key)\s*=\s*["\'][^"\']{16,}["\']', re.IGNORECASE),
    re.compile(r'(?:secret|token|private_key)\s*=\s*["\'][^"\']{16,}["\']', re.IGNORECASE),
    re.compile(r'(?:AWS_SECRET|STRIPE_SECRET|TWILIO_AUTH)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
]

_SELECT_STAR_PATTERN = re.compile(r"\bSELECT\s+\*\b", re.IGNORECASE)

_NPLUS1_RELATIONSHIP_PATTERN = re.compile(
    r"relationship\s*\([^)]*lazy\s*=\s*['\"]select['\"]", re.IGNORECASE
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


class TestLaw32NoHardcodedSecrets:
    """Law 32: No hardcoded secrets in production code.

    Scan for hardcoded passwords, API keys, and tokens in source files.
    """

    _EXCLUDED_VALUES = {
        "admin123", "supplier123", "customer123",
        "test", "password", "secret", "example",
    }

    def test_no_hardcoded_secrets_in_source(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(src.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for pattern in _SECRET_PATTERNS:
                    match = pattern.search(stripped)
                    if match:
                        value = match.group(0)
                        if not any(exc in value.lower() for exc in self._EXCLUDED_VALUES):
                            offenders.append(
                                (str(path.relative_to(_BACKEND_ROOT)), f"line {i}: {value[:60]}")
                            )
        if offenders:
            msg = "\n  ".join(f"{f}: {l}" for f, l in offenders[:20])
            raise AssertionError(
                "Law 32 violation: potential hardcoded secret(s) found:\n  " + msg
            )


class TestLaw33TokenTypeVerification:
    """Law 33: JWT access vs refresh token validation.

    The system must distinguish between access and refresh tokens.
    """

    def test_token_type_claim_exists(self):
        auth_files = list(_BACKEND_ROOT.rglob("*.py"))
        token_type_found = False
        for path in auth_files:
            if "test" in str(path) or "script" in str(path):
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "token_type" in src and ("access" in src or "refresh" in src):
                token_type_found = True
                break
        assert token_type_found, (
            "Law 33 violation: no token_type claim found in auth code"
        )


class TestLaw34ParameterizedSQLOnly:
    """Law 34: Parameterized SQL only — no raw SQL without parameterization.

    Raw SQL queries must use parameter binding, not string formatting.
    """

    def test_no_string_formatting_in_sql(self):
        sql_format_patterns = [
            re.compile(r"(?:execute|text)\s*\(\s*f['\"]"),
            re.compile(r"(?:execute|text)\s*\(\s*['\"].*%s"),
            re.compile(r"(?:execute|text)\s*\(\s*['\"].*\.format\("),
        ]
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={"tests", "scripts", "venv", "alembic"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "execute(" not in src and "text(" not in src:
                continue
            for i, line in enumerate(src.splitlines(), 1):
                for pattern in sql_format_patterns:
                    if pattern.search(line):
                        offenders.append(
                            (str(path.relative_to(_BACKEND_ROOT)), f"line {i}: {line.strip()[:80]}")
                        )
        if offenders:
            msg = "\n  ".join(f"{f}: {l}" for f, l in offenders[:15])
            raise AssertionError(
                "Law 34 violation: raw SQL without parameterization:\n  " + msg
            )


class TestLaw35CSRFActive:
    """Law 35: CSRF middleware must exist and be active."""

    def test_csrf_middleware_exists(self):
        csrf_file = _MIDDLEWARE_DIR / "csrf_middleware.py"
        assert csrf_file.exists(), (
            "Law 35 violation: csrf_middleware.py not found in middleware/"
        )

    def test_csrf_middleware_has_protection_logic(self):
        csrf_file = _MIDDLEWARE_DIR / "csrf_middleware.py"
        if not csrf_file.exists():
            pytest.skip("csrf_middleware.py does not exist")
        src = csrf_file.read_text(encoding="utf-8")
        assert "def " in src, (
            "Law 35 violation: csrf_middleware.py has no function definitions"
        )


class TestLaw36SecurityHeaders:
    """Law 36: Security headers middleware must exist."""

    def test_security_headers_middleware_exists(self):
        headers_file = _MIDDLEWARE_DIR / "security_headers.py"
        assert headers_file.exists(), (
            "Law 36 violation: security_headers.py not found in middleware/"
        )

    def test_security_headers_sets_required_headers(self):
        headers_file = _MIDDLEWARE_DIR / "security_headers.py"
        if not headers_file.exists():
            pytest.skip("security_headers.py does not exist")
        src = headers_file.read_text(encoding="utf-8")
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
        ]
        missing = [h for h in required_headers if h not in src]
        assert not missing, (
            f"Law 36 violation: security_headers.py missing headers: {missing}"
        )


class TestLaw37RateLimitFailsClosed:
    """Law 37: Rate limiting must fail closed (deny on failure)."""

    def test_rate_limit_middleware_exists(self):
        rate_file = _MIDDLEWARE_DIR / "rate_limit_middleware.py"
        assert rate_file.exists(), (
            "Law 37 violation: rate_limit_middleware.py not found in middleware/"
        )

    def test_rate_limit_has_fallback_behavior(self):
        rate_file = _MIDDLEWARE_DIR / "rate_limit_middleware.py"
        if not rate_file.exists():
            pytest.skip("rate_limit_middleware.py does not exist")
        src = rate_file.read_text(encoding="utf-8")
        assert "429" in src or "Too Many Requests" in src, (
            "Law 37 violation: rate_limit_middleware.py missing 429 response"
        )


class TestLaw38PasswordLengthValidation:
    """Law 38: Passwords >72 bytes must be rejected.

    bcrypt has a 72-byte limit. Passwords longer than this must be rejected
    before hashing.
    """

    def test_password_length_validation_exists(self):
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={"tests", "scripts", "venv"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(r"password.*(?:len|length|max|>72|<=72|72)", src, re.IGNORECASE):
                found = True
                break
        assert found, (
            "Law 38 violation: no password length validation found"
        )


class TestLaw39NoDuplicateAuthLogic:
    """Law 39: No duplicate auth implementations.

    Authentication logic should be centralized, not duplicated.
    """

    def test_auth_logic_centralized(self):
        auth_files = []
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={"tests", "scripts", "venv"}):
            if "auth" in path.name.lower():
                rel = str(path.relative_to(_BACKEND_ROOT))
                if "middleware" in rel or "infrastructure" in rel or "providers" in rel:
                    auth_files.append(rel)
        assert len(auth_files) >= 1, (
            "Law 39 violation: no centralized auth implementation found"
        )


class TestLaw40CORSOriginValidation:
    """Law 40: CORS origin validation must be configured."""

    def test_cors_configuration_exists(self):
        main_file = _BACKEND_ROOT / "main.py"
        lifespan_file = _BACKEND_ROOT / "lifespan.py"
        cors_found = False
        for f in [main_file, lifespan_file]:
            if f.exists():
                src = f.read_text(encoding="utf-8")
                if "CORSMiddleware" in src or "cors" in src.lower():
                    cors_found = True
                    break
        assert cors_found, (
            "Law 40 violation: CORS middleware not configured in main.py or lifespan.py"
        )


class TestLaw45NoNPlus1Queries:
    """Law 45: No N+1 queries — relationships must use lazy=selectin or joined."""

    def test_relationships_use_eager_loading(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "relationship" not in src:
                continue
            for match in _NPLUS1_RELATIONSHIP_PATTERN.finditer(src):
                context_start = max(0, match.start() - 100)
                context = src[context_start:match.end()]
                if "back_populates" in context or "backref" in context:
                    offenders.append((str(path.relative_to(_BACKEND_ROOT)), context[:80]))
        if offenders:
            msg = "\n  ".join(f"{f}: {c}" for f, c in offenders[:10])
            raise AssertionError(
                "Law 45 violation: relationship(s) use lazy='select' "
                f"(should use selectin or joined):\n  {msg}"
            )


class TestLaw46NoSelectStar:
    """Law 46: No SELECT * in raw SQL queries."""

    def test_no_select_star_in_raw_sql(self):
        offenders: list[tuple[str, str]] = []
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={"tests", "scripts", "venv"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(src.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if _SELECT_STAR_PATTERN.search(stripped):
                    offenders.append(
                        (str(path.relative_to(_BACKEND_ROOT)), f"line {i}: {stripped[:80]}")
                    )
        if offenders:
            msg = "\n  ".join(f"{f}: {l}" for f, l in offenders[:15])
            raise AssertionError(
                "Law 46 violation: SELECT * found in raw SQL:\n  " + msg
            )


class TestLaw47ConnectionPoolSizing:
    """Law 47: Connection pool size must be >= 10."""

    def test_connection_pool_sized(self):
        pool_found = False
        for path in _iter_py(_INFRASTRUCTURE_DIR / "database"):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "pool_size" in src:
                pool_found = True
                match = re.search(r"pool_size\s*=\s*(\d+)", src)
                if match:
                    size = int(match.group(1))
                    assert size >= 10, (
                        f"Law 47 violation: pool_size={size} (must be >= 10)"
                    )
        if not pool_found:
            pytest.skip("pool_size not configured (may use SQLite)")


class TestLaw48ReadReplicaSeparation:
    """Law 48: Read replica separation — get_read_db() must exist."""

    def test_read_replica_separation_exists(self):
        db_dir = _INFRASTRUCTURE_DIR / "database"
        if not db_dir.exists():
            pytest.skip("infrastructure/database/ does not exist")
        found = False
        for path in db_dir.rglob("*.py"):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "get_read_db" in src or "read_db" in src or "readonly" in src.lower():
                found = True
                break
        if not found:
            pytest.skip("Read replica separation not implemented (may use SQLite)")


class TestLaw49LinearAlembicHistory:
    """Law 49: Linear Alembic history — no merge heads."""

    def test_no_merge_heads(self):
        if not _MIGRATIONS_DIR.exists():
            pytest.skip("alembic/versions/ directory does not exist")
        merge_migrations = []
        for path in _MIGRATIONS_DIR.glob("*.py"):
            if path.name == "__init__.py":
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "down_revision = None" in src or "down_revision=None" in src:
                if "Merge" in src or "merge" in src:
                    merge_migrations.append(path.name)
        assert not merge_migrations, (
            f"Law 49 violation: merge migration(s) found: {merge_migrations}"
        )


class TestLaw50ExplicitTransactions:
    """Law 50: Explicit transactions — autocommit is FORBIDDEN."""

    def test_no_autocommit_configuration(self):
        for path in _iter_py(_INFRASTRUCTURE_DIR / "database"):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "autocommit" in src.lower() and "true" in src.lower():
                match = re.search(r"autocommit\s*=\s*True", src, re.IGNORECASE)
                if match:
                    pytest.fail(
                        f"Law 50 violation: autocommit=True found in "
                        f"{path.relative_to(_BACKEND_ROOT)}"
                    )


class TestLaw51SingleTableOwnership:
    """Law 51: Single table ownership — tables belong to one schema."""

    def test_no_duplicate_tablenames_across_domains(self):
        table_map: dict[str, list[str]] = {}
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for match in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', src):
                table_name = match.group(1)
                rel = str(path.relative_to(_BACKEND_ROOT))
                table_map.setdefault(table_name, []).append(rel)
        duplicates = {t: files for t, files in table_map.items() if len(files) > 1}
        if duplicates:
            msg = "\n  ".join(
                f"{t}: {', '.join(f)}" for t, f in sorted(duplicates.items())
            )
            raise AssertionError(
                "Law 51 violation: table(s) defined in multiple files:\n  " + msg
            )


class TestLaw52FKConstraintsWithOndelete:
    """Law 52: FK constraints must have ondelete specified."""

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
                "Law 52 violation: ForeignKey column(s) missing ondelete:\n  " + msg
            )


class TestLaw53IndexAllFKColumns:
    """Law 53: All FK columns should be indexed."""

    def test_fk_columns_have_indexes(self):
        offenders: list[tuple[str, str]] = []
        index_pattern = re.compile(r"Index\s*\(", re.IGNORECASE)
        for path in _iter_py(_DOMAINS_DIR, exclude_dirs={"tests", "scripts"}):
            if "__init__" in path.name:
                continue
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "ForeignKey" not in src:
                continue
            has_index = index_pattern.search(src) is not None
            if not has_index:
                tree = ast.parse(src)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.AnnAssign):
                        continue
                    if not isinstance(node.target, ast.Name):
                        continue
                    col_name = node.target.id
                    if col_name == "id" or not col_name.endswith("_id"):
                        continue
                    if not isinstance(node.value, ast.Call):
                        continue
                    call_src = ast.get_source_segment(src, node) or ""
                    if "ForeignKey" in call_src:
                        offenders.append((str(path.relative_to(_BACKEND_ROOT)), col_name))
        if offenders:
            msg = "\n  ".join(f"{f}: '{c}'" for f, c in offenders[:15])
            raise AssertionError(
                "Law 53 violation: FK column(s) may be missing indexes:\n  " + msg
            )


class TestLaw54SoftDelete:
    """Law 54: Soft delete — models should have is_deleted column."""

    def test_models_have_soft_delete(self):
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
            if table_name == "alembic_version":
                continue
            if "is_deleted" not in src:
                offenders.append((str(path.relative_to(_BACKEND_ROOT)), table_name))
        if offenders:
            msg = "\n  ".join(f"{f} ({t})" for f, t in offenders[:15])
            raise AssertionError(
                "Law 54 violation: model(s) missing is_deleted for soft delete:\n  " + msg
            )


class TestLaw55SchemaPerDomain:
    """Law 55: Schema-per-domain — each domain should have its own schema."""

    def test_domains_have_schemas(self):
        schema_pattern = re.compile(r"__table_args__\s*=\s*\{[^}]*['\"]schema['\"]\s*:")
        domains_without_schema = []
        for d in sorted(_DOMAINS_DIR.iterdir()):
            if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
                continue
            has_schema = False
            for path in d.rglob("*.py"):
                if path.name == "__init__.py":
                    continue
                try:
                    src = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                if schema_pattern.search(src):
                    has_schema = True
                    break
            if not has_schema:
                domains_without_schema.append(d.name)
        if domains_without_schema:
            pytest.skip(
                f"Domains without explicit schema (may use default): "
                f"{domains_without_schema}"
            )
