"""Law 32/33/34/37/38/42/43 — static security scans.

Conservative AST/regex checks that assert only CLEAR violations:
  (a) No hardcoded secrets (JWT keys, API keys, passwords as string literals).
  (b) JWT decoders verify the type claim (Law 33).
  (c) No f-string SQL interpolation into execute() (Law 34).
  (d) Passwords >72 bytes rejected (Law 38).
  (e) Public endpoints use Pydantic schemas for body params (Law 42) where checkable.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from tests._support import laws

_BACKEND = laws.BACKEND_ROOT

# Patterns that strongly indicate hardcoded secrets (conservative).
_SECRET_PATTERNS = [
    # JWT_SECRET = "..." or JWT_SECRET = '...'
    re.compile(r"""(?i)(JWT_SECRET|SECRET_KEY|API_KEY|API_SECRET|PASSWORD)\s*=\s*["'][A-Za-z0-9_\-+=/]{16,}["']"""),
    # Hardcoded AWS keys
    re.compile(r"""AKIA[0-9A-Z]{16}"""),
    # Generic high-entropy strings assigned to secret vars
    re.compile(r"""(?i)(secret|token|key|password|api_key)\s*[:=]\s*["'][A-Za-z0-9_\-+=/]{32,}["']"""),
]

# Files to exclude from secret scanning (test configs, .env examples, etc.)
_SECRET_SCAN_EXCLUDES = {
    "conftest.py",
    ".env.example",
    "seed_all.py",
}


def _iter_py(root: Path, exclude: set[str] | None = None):
    exclude = exclude or set()
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        if path.name in exclude:
            continue
        rel = str(path.relative_to(_BACKEND))
        if "/tests/" in rel or "\\tests\\" in rel:
            continue  # skip test files
        yield path


class TestNoHardcodedSecrets:
    """Law 32: no hardcoded JWT keys, API keys, or passwords in source."""

    @pytest.mark.parametrize("layer", ["domains", "infrastructure", "kernel", "providers", "jobs", "middleware"])
    def test_no_hardcoded_secrets(self, layer):
        source_dir = _BACKEND / layer
        if not source_dir.exists():
            pytest.skip(f"{layer}/ does not exist")

        offenders: list[str] = []
        for path in _iter_py(source_dir, exclude=_SECRET_SCAN_EXCLUDES):
            try:
                source = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for pattern in _SECRET_PATTERNS:
                for m in pattern.finditer(source):
                    # Check it's not an env var read
                    line_start = source.rfind("\n", 0, m.start()) + 1
                    line_end = source.find("\n", m.end())
                    if line_end == -1:
                        line_end = len(source)
                    line = source[line_start:line_end]
                    if "os.environ" in line or "os.getenv" in line or "settings." in line:
                        continue
                    offenders.append(f"{path.relative_to(_BACKEND)}: {line.strip()[:80]}")

        assert not offenders, (
            "Law 32 violation: possible hardcoded secret(s):\n  "
            + "\n  ".join(sorted(set(offenders))[:20])
        )


class TestJWTDecodersVerifyTypeClaim:
    """Law 33: all JWT decoders must verify the type claim."""

    def test_jwt_decode_checks_type(self):
        offenders: list[str] = []
        scan_dirs = ["domains", "infrastructure", "kernel", "providers", "jobs", "middleware"]
        for layer in scan_dirs:
            source_dir = _BACKEND / layer
            if not source_dir.exists():
                continue
            for path in _iter_py(source_dir):
                try:
                    source = path.read_text(encoding="utf-8")
                    tree = ast.parse(source)
                except (OSError, SyntaxError):
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.FunctionDef):
                        continue
                    func_name = node.name.lower()
                    if "jwt" not in func_name and "token" not in func_name:
                        continue
                    has_type_check = any(
                        isinstance(n, ast.Compare) or isinstance(n, ast.If)
                        for n in ast.walk(node)
                    )
                    if not has_type_check:
                        offenders.append(
                            f"{path.relative_to(_BACKEND)}: {node.name} may not verify type claim"
                        )
        assert not offenders, (
            "Law 33 violation: JWT/token decoders without type-claim verification:\n  "
            + "\n  ".join(sorted(set(offenders))[:20])
        )


class TestNoFStringSQLInterpolation:
    """Law 34: no f-string SQL interpolation into execute()."""

    def test_no_fstring_sql(self):
        offenders: list[str] = []
        scan_dirs = ["domains", "infrastructure", "kernel", "providers", "jobs", "middleware"]

        for layer in scan_dirs:
            source_dir = _BACKEND / layer
            if not source_dir.exists():
                continue
            for path in _iter_py(source_dir):
                try:
                    source = path.read_text(encoding="utf-8")
                    tree = ast.parse(source)
                except (OSError, SyntaxError):
                    continue
                for node in ast.walk(tree):
                    # Look for execute(f"...") or execute(f'...')
                    if not isinstance(node, ast.Call):
                        continue
                    func = node.func
                    func_name = ""
                    if isinstance(func, ast.Attribute):
                        func_name = func.attr
                    elif isinstance(func, ast.Name):
                        func_name = func.id
                    if func_name not in {"execute", "executemany"}:
                        continue
                    for arg in node.args:
                        if isinstance(arg, ast.JoinedStr):  # f-string
                            offenders.append(f"{path.relative_to(_BACKEND)}: execute(f-string)")

        assert not offenders, (
            "Law 34 violation: f-string SQL interpolation into execute():\n  "
            + "\n  ".join(sorted(set(offenders)))
        )


class TestPasswordLengthEnforcement:
    """Law 38: passwords >72 bytes rejected with error, never truncated."""

    def test_password_hash_rejects_long_passwords(self):
        """get_password_hash must reject passwords >72 chars."""
        from infrastructure.utils.auth import get_password_hash

        long_pw = "a" * 73
        with pytest.raises(ValueError, match="72"):
            get_password_hash(long_pw)

    def test_password_hash_accepts_valid_length(self):
        """get_password_hash should accept passwords <=72 chars."""
        from infrastructure.utils.auth import get_password_hash

        valid_pw = "a" * 72
        result = get_password_hash(valid_pw)
        assert result, "get_password_hash should return a hash for valid-length password"


class TestPublicEndpointsUsePydanticSchemas:
    """Law 42: public endpoints (no Depends auth) should use Pydantic body schemas.

    We check that router functions with Body(...) params use annotated Pydantic
    models rather than raw dict. This is a best-effort static scan.
    """

    def test_no_raw_dict_body_in_public_endpoints(self):
        modules_dir = _BACKEND / "modules"
        if not modules_dir.exists():
            pytest.skip("modules/ does not exist")

        # Find router files
        offenders: list[str] = []
        for path in _iter_py(modules_dir):
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                # Check if it's a router endpoint (has decorator with .get/.post etc.)
                is_endpoint = False
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in {"get", "post", "put", "patch", "delete"}:
                            is_endpoint = True
                            break
                if not is_endpoint:
                    continue
                # Check for payload: dict = Body(...)
                for arg in node.args.args:
                    if arg.arg in {"payload", "body", "data"}:
                        annotation = arg.annotation
                        if isinstance(annotation, ast.Name) and annotation.id == "dict":
                            offenders.append(
                                f"{path.relative_to(_BACKEND)}: {node.name} uses raw dict body"
                            )

        # Law 42 requires Pydantic body schemas for public endpoints.
        # A raw dict body is a clear violation, so we fail the gate.
        assert not offenders, (
            "Law 42 violation: public endpoint(s) use raw dict body instead of "
            "Pydantic schema:\n  " + "\n  ".join(sorted(set(offenders))[:20])
        )


class TestJWTTypeVerification:
    """Law 33: verify that JWT decode functions check the type claim."""

    def test_verify_token_checks_type(self):
        """verify_token must check type == 'access'."""
        from infrastructure.security.auth import verify_token, _decode_and_validate
        import inspect

        source = inspect.getsource(verify_token)
        helper_source = inspect.getsource(_decode_and_validate)
        combined = source + helper_source
        assert 'type' in combined.lower(), "verify_token must verify the type claim"
        assert 'access' in combined, "verify_token must check for 'access' type"

    def test_verify_refresh_token_checks_type(self):
        """verify_refresh_token must check type == 'refresh'."""
        from infrastructure.security.auth import verify_refresh_token, _decode_and_validate
        import inspect

        source = inspect.getsource(verify_refresh_token)
        helper_source = inspect.getsource(_decode_and_validate)
        combined = source + helper_source
        assert 'type' in combined.lower(), "verify_refresh_token must verify the type claim"
        assert 'refresh' in combined, "verify_refresh_token must check for 'refresh' type"
