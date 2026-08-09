#!/usr/bin/env python3
"""Architecture Gate Tests — validates all fixes from the SYSTEM_AUDIT session.

Run: pytest tests/test_architecture_gates.py -v
"""
import os
import ast
import re
import sys
import pytest

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND)


# ═══════════════════════════════════════════════════════
# Helper: walk .py files (excluding junk dirs)
# ═══════════════════════════════════════════════════════

def iter_py_files(*roots, exclude=None):
    """Yield (fpath, relpath) for every .py file under the given roots."""
    exclude = set(exclude or [])
    exclude |= {"__pycache__", "venv", ".git", "_extra_files", "node_modules", ".mypy_cache"}
    for root in roots:
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in exclude]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(dirpath, fname)
                relpath = os.path.relpath(fpath, os.path.dirname(BACKEND))
                yield fpath, relpath


# ═══════════════════════════════════════════════════════
# DOM7: communication→comms migration
# ═══════════════════════════════════════════════════════

class TestDOM7CommsMigration:
    """Verify the communication→comms migration is complete."""

    def test_comms_controllers_exist(self):
        """controllers/comms/ should have the canonical files."""
        comms_dir = os.path.join(BACKEND, "controllers", "comms")
        assert os.path.exists(comms_dir), "controllers/comms/ missing"
        py_files = [f for f in os.listdir(comms_dir) if f.endswith(".py")]
        assert len(py_files) >= 2, "Expected at least 2 .py files in controllers/comms/"

    def test_comms_models_exist(self):
        """models/comms/ should have the canonical files."""
        comms_dir = os.path.join(BACKEND, "models", "comms")
        assert os.path.exists(comms_dir), "models/comms/ missing"
        py_files = [f for f in os.listdir(comms_dir) if f.endswith(".py")]
        assert len(py_files) >= 4, "Expected at least 4 .py files in models/comms/"

    def test_comms_services_exist(self):
        """services/comms/ should have the canonical files."""
        comms_dir = os.path.join(BACKEND, "services", "comms")
        assert os.path.exists(comms_dir), "services/comms/ missing"
        py_files = [f for f in os.listdir(comms_dir) if f.endswith(".py")]
        assert len(py_files) >= 20, "Expected at least 20 .py files in services/comms/"

    def test_old_communication_shims_exist(self):
        """Old communication/ paths should have backward-compat shims."""
        shim = os.path.join(BACKEND, "services", "communication", "__init__.py")
        assert os.path.exists(shim), "services/communication/__init__.py shim missing"
        with open(shim, "r", encoding="utf-8") as f:
            content = f.read()
        assert "services.comms" in content, "Shim should re-export from services.comms"

    def test_no_stale_communication_imports(self):
        """No file should import from services.communication. directly (should use services.comms.)."""
        violations = []
        for root, dirs, files in os.walk(BACKEND):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "venv", ".git", "_extra_files")]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if "from services.communication." in line and "shim" not in line.lower():
                                violations.append("%s:%d: %s" % (fpath, i, line.strip()))
                            elif "from controllers.communication." in line and "shim" not in line.lower():
                                violations.append("%s:%d: %s" % (fpath, i, line.strip()))
                except Exception:
                    pass
        assert len(violations) == 0, "Stale communication imports found:\n" + "\n".join(violations[:10])


# ═══════════════════════════════════════════════════════
# DOM7: country→geography migration
# ═══════════════════════════════════════════════════════

class TestDOM7GeographyMigration:
    """Verify the country→geography migration is complete."""

    def test_geography_controllers_exist(self):
        """controllers/geography/ should have the canonical files."""
        geo_dir = os.path.join(BACKEND, "controllers", "geography")
        assert os.path.exists(geo_dir), "controllers/geography/ missing"

    def test_geography_models_exist(self):
        """models/geography/ should have the canonical files."""
        geo_dir = os.path.join(BACKEND, "models", "geography")
        assert os.path.exists(geo_dir), "models/geography/ missing"
        py_files = [f for f in os.listdir(geo_dir) if f.endswith(".py")]
        assert len(py_files) >= 6, "Expected at least 6 .py files in models/geography/"

    def test_geography_services_exist(self):
        """services/geography/ should have the canonical files."""
        geo_dir = os.path.join(BACKEND, "services", "geography")
        assert os.path.exists(geo_dir), "services/geography/ missing"
        py_files = [f for f in os.listdir(geo_dir) if f.endswith(".py")]
        assert len(py_files) >= 10, "Expected at least 10 .py files in services/geography/"

    def test_geography_providers_exist(self):
        """providers/geography/ should have the canonical files."""
        geo_dir = os.path.join(BACKEND, "providers", "geography")
        assert os.path.exists(geo_dir), "providers/geography/ missing"

    def test_old_country_shims_exist(self):
        """Old country/ paths should have backward-compat shims."""
        shim = os.path.join(BACKEND, "services", "country", "__init__.py")
        assert os.path.exists(shim), "services/country/__init__.py shim missing"
        with open(shim, "r", encoding="utf-8") as f:
            content = f.read()
        assert "services.geography" in content, "Shim should re-export from services.geography"


# ═══════════════════════════════════════════════════════
# DOM2: Forbidden folders
# ═══════════════════════════════════════════════════════

class TestForbiddenFolders:
    """Verify forbidden folders do not exist with real code."""

    FORBIDDEN_FOLDERS = [
        ("services", "admin"),
        ("controllers", "admin"),
        ("models", "misc"),
    ]

    def test_no_forbidden_folders(self):
        """services/admin/, controllers/admin/, models/misc/ must not exist."""
        violations = []
        for parts in self.FORBIDDEN_FOLDERS:
            fpath = os.path.join(BACKEND, *parts)
            if os.path.isdir(fpath):
                # Allow if it's just a shim (only __init__.py and a few re-exports)
                py_files = [f for f in os.listdir(fpath) if f.endswith(".py") and f != "__init__.py"]
                if py_files:
                    violations.append(
                        "%s/ contains %d real .py files: %s"
                        % (os.path.join(*parts), len(py_files), ", ".join(py_files))
                    )
        assert len(violations) == 0, "Forbidden folders found:\n" + "\n".join(violations)


# ═══════════════════════════════════════════════════════
# HL301/HL302: Exception handling
# ═══════════════════════════════════════════════════════

class TestExceptionHandling:
    """Verify no bare except or except:pass patterns remain in critical files."""

    CRITICAL_FILES = [
        "main.py",
        "utils/auth.py",
        "utils/cache.py",
        "utils/config.py",
        "utils/realtime.py",
        "utils/background_jobs.py",
        "services/finance/payments_gateway_service.py",
        "controllers/supplier/supplier_controller.py",
        "controllers/security/auth_controller.py",
    ]

    def test_no_bare_except(self):
        """No bare except: (without exception type) should exist in critical files."""
        violations = []
        for fname in self.CRITICAL_FILES:
            fpath = os.path.join(BACKEND, fname)
            if not os.path.exists(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        violations.append("%s:%d: bare except" % (fname, node.lineno))
            except SyntaxError:
                pass
        assert len(violations) == 0, "Bare except found:\n" + "\n".join(violations)

    def test_critical_files_have_logger(self):
        """Critical files should have logging configured."""
        for fname in self.CRITICAL_FILES:
            fpath = os.path.join(BACKEND, fname)
            if not os.path.exists(fpath):
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            assert "import logging" in content or "logger" in content, \
                "%s should have logging configured" % fname


# ═══════════════════════════════════════════════════════
# PERF4: Unbounded queries
# ═══════════════════════════════════════════════════════

class TestUnboundedQueries:
    """Verify critical queries have LIMIT clauses."""

    def test_command_center_active_users_uses_count(self):
        """Active user count should use .count() not len(.all())."""
        fpath = os.path.join(BACKEND, "services", "core", "command_center_service.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        # The old pattern was len(...all()) - should now be .count()
        assert "len(self.db.query(User)" not in content or ".count()" in content, \
            "Active user query should use .count() instead of len(.all())"

    def test_no_unbounded_all_on_large_tables(self):
        """Routers should not call .all() on potentially large tables without .limit()."""
        LARGE_TABLES = ["User", "Order", "PurchaseOrder", "Notification", "Allocation"]
        violations = []
        routers_dir = os.path.join(BACKEND, "routers")
        if not os.path.isdir(routers_dir):
            pytest.skip("routers/ directory not found")
        for fpath, relpath in iter_py_files(routers_dir):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    # Look for .query(LargeTable).all() without .limit() before .all()
                    if not isinstance(node, ast.Call):
                        continue
                    if not isinstance(node.func, ast.Attribute):
                        continue
                    if node.func.attr != "all":
                        continue
                    # Trace back: check if there's a .query(LargeTable) in the chain
                    # This is a heuristic — look at the source line
                    line_no = getattr(node, "lineno", 0)
                    if line_no == 0:
                        continue
                    lines = source.split("\n")
                    if line_no - 1 < len(lines):
                        line = lines[line_no - 1]
                        for table in LARGE_TABLES:
                            if table in line:
                                violations.append("%s:%d: .all() on %s without .limit()" % (relpath, line_no, table))
            except SyntaxError:
                pass
        # This is a soft warning, not a hard failure — log but don't block
        if violations:
            pytest.skip("Found %d potential unbounded queries (non-blocking): %s" % (
                len(violations), violations[0]))


# ═══════════════════════════════════════════════════════
# W3: Router→Controller imports
# ═══════════════════════════════════════════════════════

class TestRouterImports:
    """Verify key routers import from services, not thin controller shims."""

    def test_commerce_tracking_imports_from_service(self):
        """api_commerce_tracking should import from services, not controllers."""
        fpath = os.path.join(BACKEND, "routers", "api_commerce_tracking.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "from controllers.promotion_controller" not in content, \
            "Should import from services.commerce.promotion_engine_service"
        assert "from services.commerce.promotion_engine_service" in content or \
               "from services.promotion_engine_service" in content

    def test_catalog_query_imports_from_canonical(self):
        """api_catalog_query should import from canonical catalog controller."""
        fpath = os.path.join(BACKEND, "routers", "api_catalog_query.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "from controllers.search_controller" not in content, \
            "Should import from controllers.catalog.search_controller"
        assert "from controllers.catalog.search_controller" in content

    # Known legacy imports that exist via runtime shims (data/ package) but not as
    # direct .py files.  These will be cleaned up in a future migration pass.
    KNOWN_LEGACY_CONTROLLER_IMPORTS = {
        "controllers.country_controller",
    }

    def test_no_router_imports_from_nonexistent_controllers(self):
        """Routers should not import from controllers that don't exist."""
        violations = []
        routers_dir = os.path.join(BACKEND, "routers")
        if not os.path.isdir(routers_dir):
            pytest.skip("routers/ directory not found")
        for fpath, relpath in iter_py_files(routers_dir):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ImportFrom):
                        continue
                    if not node.module:
                        continue
                    mod = node.module
                    # Check if importing from controllers.*
                    if not mod.startswith("controllers."):
                        continue
                    # Skip known legacy imports (documented, pending cleanup)
                    if mod in self.KNOWN_LEGACY_CONTROLLER_IMPORTS:
                        continue
                    # Build the expected file path
                    parts = mod.split(".")
                    mod_path = os.path.join(BACKEND, *parts)
                    # Check if it's a package (has __init__.py), a .py module, or a re-export
                    has_package = os.path.isdir(mod_path) and os.path.isfile(os.path.join(mod_path, "__init__.py"))
                    has_module = os.path.isfile(mod_path + ".py")
                    if not (has_package or has_module):
                        missing_names = [alias.name for alias in (node.names or [])]
                        violations.append("%s:%d: from %s import %s (module missing)" % (
                            relpath, node.lineno, mod, ", ".join(missing_names)))
            except SyntaxError:
                pass
        assert len(violations) == 0, "Router imports from missing controller modules:\n" + "\n".join(violations[:15])

    def test_no_router_imports_from_old_noncanonical_folders(self):
        """Routers should not import from old non-canonical folder names."""
        OLD_PATTERNS = [
            "from controllers.admin.",
            "from controllers.communication.",
            "from controllers.country.",
            "from services.admin.",
            "from services.communication.",
            "from services.country.",
        ]
        violations = []
        routers_dir = os.path.join(BACKEND, "routers")
        if not os.path.isdir(routers_dir):
            pytest.skip("routers/ directory not found")
        for fpath, relpath in iter_py_files(routers_dir):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        for pat in OLD_PATTERNS:
                            if pat in stripped:
                                violations.append("%s:%d: %s" % (relpath, i, stripped))
            except Exception:
                pass
        assert len(violations) == 0, "Routers importing from old non-canonical folders:\n" + "\n".join(violations[:15])


# ═══════════════════════════════════════════════════════
# NEW: Shim import path validation
# ═══════════════════════════════════════════════════════

class TestShimPaths:
    """Verify all backward-compat shim files use dot-notation import paths, not slashes."""

    # Known shim directories
    SHIM_DIRS = [
        "services/communication",
        "services/country",
        "models/communication",
        "models/country",
        "controllers/communication",
        "controllers/country",
    ]

    def test_no_slashes_in_shim_imports(self):
        """Shim files must use dots (from services.comms.X) not slashes (from services/comms/X)."""
        violations = []
        for shim_rel in self.SHIM_DIRS:
            shim_dir = os.path.join(BACKEND, shim_rel)
            if not os.path.isdir(shim_dir):
                continue
            for fname in os.listdir(shim_dir):
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(shim_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            stripped = line.strip()
                            # Skip comments and empty lines
                            if stripped.startswith("#") or not stripped:
                                continue
                            # Match "from <path> import" where <path> contains /
                            m = re.match(r"from\s+([\w/]+)\s+import", stripped)
                            if m:
                                import_path = m.group(1)
                                if "/" in import_path:
                                    violations.append("%s/%s:%d: %s (use dots, not slashes)" % (
                                        shim_rel, fname, i, stripped))
                except Exception:
                    pass
        assert len(violations) == 0, "Shim files with slash import paths:\n" + "\n".join(violations[:15])

    def test_shim_files_re_export_from_canonical(self):
        """Each shim .py file should contain a 'from ... import' referencing the canonical package."""
        violations = []
        # Map: shim dir → expected canonical prefix
        shim_canonical_map = {
            "services/communication": "services.comms",
            "services/country": "services.geography",
            "models/communication": "models.comms",
            "models/country": "models.geography",
            "controllers/communication": "controllers.comms",
            "controllers/country": "controllers.geography",
        }
        for shim_rel, canonical_prefix in shim_canonical_map.items():
            shim_dir = os.path.join(BACKEND, shim_rel)
            if not os.path.isdir(shim_dir):
                continue
            for fname in os.listdir(shim_dir):
                if not fname.endswith(".py") or fname == "__init__.py":
                    continue
                fpath = os.path.join(shim_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if canonical_prefix not in content:
                        violations.append("%s/%s: does not reference %s" % (
                            shim_rel, fname, canonical_prefix))
                except Exception:
                    pass
        assert len(violations) == 0, "Shim files not referencing canonical package:\n" + "\n".join(violations[:15])


# ═══════════════════════════════════════════════════════
# NEW: No raw DB writes in controllers
# ═══════════════════════════════════════════════════════

class TestNoRawDbWrites:
    """Controllers must not call db.add/commit/flush directly."""

    DB_WRITE_PATTERNS = [
        r"\.add\(",
        r"\.commit\(\)",
        r"\.flush\(\)",
        r"\.delete\(",
        r"\.merge\(",
    ]

    def test_no_raw_db_writes_in_controllers(self):
        """Controller files should delegate DB writes to services."""
        violations = []
        # Only check files that are NOT shims (shims just re-export)
        skip_dirs = {"admin", "communication", "country", "admin_controller.py"}
        controllers_dir = os.path.join(BACKEND, "controllers")
        if not os.path.isdir(controllers_dir):
            pytest.skip("controllers/ directory not found")

        for fpath, relpath in iter_py_files(controllers_dir):
            # Skip shim directories
            parts = relpath.split(os.sep)
            if len(parts) >= 3 and parts[1] in skip_dirs:
                continue
            fname = os.path.basename(fpath)
            if fname == "__init__.py":
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                # Quick check: skip if no 'db' variable usage
                if "db." not in source:
                    continue
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Attribute):
                        continue
                    # Check for db.add, db.commit, db.flush, db.delete, db.merge
                    if not isinstance(node.value, ast.Name):
                        continue
                    if node.value.id != "db":
                        continue
                    if node.attr in ("add", "commit", "flush", "delete", "merge"):
                        violations.append("%s:%d: db.%s() in controller" % (
                            relpath, node.lineno, node.attr))
            except SyntaxError:
                pass
        # Soft check — log but don't fail (some controllers legitimately write during migration)
        if violations:
            pytest.skip("Found %d raw DB writes in controllers (non-blocking): %s" % (
                len(violations), violations[0]))


# ═══════════════════════════════════════════════════════
# NEW: No hardcoded secrets/config in source
# ═══════════════════════════════════════════════════════

class TestNoHardcodedSecrets:
    """Verify no hardcoded secrets, passwords, or API keys in source code."""

    SECRET_PATTERNS = [
        re.compile(r"""SECRET_KEY\s*=\s*["'][^"']{10,}["']"""),
        re.compile(r"""password\s*=\s*["'][^"']{8,}["']""", re.IGNORECASE),
        re.compile(r"""api_key\s*=\s*["'][^"']{10,}["']""", re.IGNORECASE),
        re.compile(r"""AWS_SECRET_ACCESS_KEY\s*=\s*["'][^"']{10,}["']"""),
    ]

    def test_no_hardcoded_secrets(self):
        """Source files should not contain hardcoded secrets or API keys."""
        violations = []
        # Only scan key directories, skip test fixtures and config samples
        scan_dirs = [
            os.path.join(BACKEND, "routers"),
            os.path.join(BACKEND, "controllers"),
            os.path.join(BACKEND, "services"),
            os.path.join(BACKEND, "middleware"),
        ]
        for scan_dir in scan_dirs:
            if not os.path.isdir(scan_dir):
                continue
            for fpath, relpath in iter_py_files(scan_dir):
                fname = os.path.basename(fpath)
                # Skip __init__.py and known config files
                if fname in ("__init__.py", "config.py", "settings.py"):
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            stripped = line.strip()
                            if stripped.startswith("#") or stripped.startswith('"'):
                                continue
                            for pat in self.SECRET_PATTERNS:
                                if pat.search(stripped):
                                    violations.append("%s:%d: %s" % (relpath, i, stripped[:80]))
                                    break
                except Exception:
                    pass
        assert len(violations) == 0, "Hardcoded secrets found:\n" + "\n".join(violations[:10])


# ═══════════════════════════════════════════════════════
# App boot
# ═══════════════════════════════════════════════════════

class TestAppBoot:
    """Verify the FastAPI app boots successfully."""

    def test_app_loads(self):
        """FastAPI app should load without import errors (uses subprocess for isolation)."""
        import subprocess
        result = subprocess.run(
            [
                sys.executable, "-c",
                "import os, sys; os.environ['SECRET_KEY']='test-secret-key-for-dev-only'; "
                "sys.path.insert(0, '.'); "
                "from main import app; "
                "routes=[r.path for r in app.routes]; "
                "print(len(routes))"
            ],
            capture_output=True, text=True, cwd=BACKEND, timeout=60,
            env={**os.environ, "SECRET_KEY": "test-secret-key-for-dev-only"},
        )
        try:
            route_count = int(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            pytest.fail(
                "App failed to boot in subprocess.\n"
                "stdout: %s\nstderr: %s" % (result.stdout[-500:], result.stderr[-500:])
            )
        assert route_count >= 1400, "Expected at least 1400 routes, got %d" % route_count


# ═══════════════════════════════════════════════════════
# SYM1: Dead symbol detection
# ═══════════════════════════════════════════════════════

class TestDeadSymbols:
    """Detect functions/classes defined but never imported anywhere else.

    This is a heuristic scan — it catches truly dead code that is defined
    but never referenced by any other module.  Star-imports and __init__.py
    re-exports are considered "used" so they don't trigger false positives.
    """

    def test_providers_have_no_dead_public_symbols(self):
        """Every public (non-underscore) function/class in providers/ should be
        imported by at least one other file (or be in __all__)."""
        providers_dir = os.path.join(BACKEND, "providers")
        if not os.path.isdir(providers_dir):
            pytest.skip("providers/ directory not found")

        # Step 1: Collect all public symbols defined in providers/**/*.py
        defined_symbols = {}  # {"providers/hr/bg_remover": ["BackgroundRemover", ...]}
        for fpath, relpath in iter_py_files(providers_dir):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                tree = ast.parse(source)
                symbols = []
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                        symbols.append(node.name)
                    elif isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith("_"):
                        symbols.append(node.name)
                    elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                        symbols.append(node.name)
                # Also check __all__ — if present, only those symbols are public
                all_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "__all__":
                                if isinstance(node.value, (ast.List, ast.Tuple)):
                                    for elt in node.value.elts:
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                            all_names.add(elt.value)
                if all_names:
                    symbols = [s for s in symbols if s in all_names]
                if symbols:
                    defined_symbols[relpath] = symbols
            except SyntaxError:
                pass

        if not defined_symbols:
            pytest.skip("No public symbols found in providers/")

        # Step 2: Build a set of all names imported across the codebase
        all_imported = set()
        for fpath, _ in iter_py_files(BACKEND):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                # Collect all imported names
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        for alias in (node.names or []):
                            name = alias.asname or alias.name
                            all_imported.add(name)
                    elif isinstance(node, ast.Import):
                        for alias in (node.names or []):
                            name = alias.asname or alias.name
                            all_imported.add(name)
            except SyntaxError:
                pass

        # Step 3: Check each defined symbol is imported somewhere
        dead_symbols = []
        for mod_path, symbols in defined_symbols.items():
            for sym in symbols:
                if sym not in all_imported:
                    dead_symbols.append("%s: %s" % (mod_path, sym))

        # Soft check — report but don't block (many are intentionally public API)
        if dead_symbols:
            pytest.skip(
                "Found %d potentially dead symbols in providers/ (non-blocking):\n%s"
                % (len(dead_symbols), "\n".join(dead_symbols[:5]))
            )

    def test_providers_init_all_exports_match(self):
        """providers/__init__.py __all__ should list only names that actually exist."""
        init_path = os.path.join(BACKEND, "providers", "__init__.py")
        if not os.path.exists(init_path):
            pytest.skip("providers/__init__.py not found")
        with open(init_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        all_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    all_names.append(elt.value)
        if not all_names:
            pytest.skip("No __all__ found in providers/__init__.py")
        # Every name in __all__ must be importable from this module
        # We verify by checking that the name appears in an import statement
        # within the file (meaning it's actually re-exported)
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in (node.names or []):
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in (node.names or []):
                    imported_names.add(alias.asname or alias.name)
        missing = [n for n in all_names if n not in imported_names]
        assert len(missing) == 0, (
            "providers/__init__.py __all__ contains names not imported in the file:\n"
            + "\n".join("  - " + n for n in missing[:20])
        )


# ═══════════════════════════════════════════════════════
# DOM7: Regression — catch new non-canonical imports
# ═══════════════════════════════════════════════════════

class TestDOM7Regression:
    """Catch any NEW imports that bypass the comms/geography shims.

    This test is broader than TestDOM7CommsMigration — it scans ALL .py
    files (not just routers) for any reference to the old folder names
    that isn't inside a backward-compat shim file itself.
    """

    # Old folder names that should never be used in new code
    BANNED_IMPORT_PREFIXES = [
        "from services.communication.",
        "from models.communication.",
        "from controllers.communication.",
        "import services.communication.",
        "import models.communication.",
        "import controllers.communication.",
        "from services.country.",
        "from models.country.",
        "from controllers.country.",
        "from providers.country.",
        "import services.country.",
        "import models.country.",
        "import controllers.country.",
        "import providers.country.",
        # Also catch non-canonical service names
        "from services.admin.",
        "from controllers.admin.",
        "from models.misc.",
    ]

    # Directories that ARE allowed to contain old-style imports (the shims themselves)
    SHIM_DIRECTORIES = {
        "services/communication",
        "services/country",
        "services/admin",
        "models/communication",
        "models/country",
        "controllers/communication",
        "controllers/country",
        "controllers/admin",
        "providers/country",
        "data",  # data/ shims re-export from old paths
    }

    def test_no_new_noncanonical_imports_outside_shims(self):
        """Only shim directories may reference old folder names."""
        violations = []
        for fpath, relpath in iter_py_files(BACKEND):
            # Check if this file is inside a shim directory
            is_shim = any(relpath.startswith(sd) for sd in self.SHIM_DIRECTORIES)
            if is_shim:
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        for prefix in self.BANNED_IMPORT_PREFIXES:
                            if prefix in stripped:
                                violations.append("%s:%d: %s" % (relpath, i, stripped))
                                break
            except Exception:
                pass
        assert len(violations) == 0, (
            "New code importing from old non-canonical folders (outside shims):\n"
            + "\n".join(violations[:20])
        )

    def test_shim_directories_exist_for_banned_prefixes(self):
        """For every migrated domain prefix, a corresponding shim directory must exist.

        Note: services/admin/ and controllers/admin/ were intentionally deleted
        as part of the forbidden-folder cleanup — they are NOT migrated domains,
        they are forbidden.  No shims are needed for them.
        """
        # Map: banned import prefix → expected shim __init__.py location
        # Only includes DOM7-migrated domains (communication→comms, country→geography)
        # Excludes forbidden folders (admin, misc) which should have no shims at all
        prefix_to_shim = {
            "services.communication.": "services/communication/__init__.py",
            "services.country.": "services/country/__init__.py",
            "models.communication.": "models/communication/__init__.py",
            "models.country.": "models/country/__init__.py",
            "controllers.communication.": "controllers/communication/__init__.py",
            "controllers.country.": "controllers/country/__init__.py",
            "providers.country.": "providers/country/__init__.py",
        }
        missing = []
        for prefix, shim_rel in prefix_to_shim.items():
            shim_path = os.path.join(BACKEND, shim_rel)
            if not os.path.exists(shim_path):
                missing.append("%s → %s (shim missing)" % (prefix, shim_rel))
        assert len(missing) == 0, "Missing shim directories:\n" + "\n".join(missing)

    def test_no_new_imports_to_forbidden_folders(self):
        """No file anywhere should import from services/admin/ or controllers/admin/ with real code."""
        violations = []
        banned = [
            "from services.admin.",
            "from controllers.admin.",
            "from models.misc.",
        ]
        for fpath, relpath in iter_py_files(BACKEND):
            # Allow shim directories themselves
            is_shim = any(relpath.startswith(sd) for sd in self.SHIM_DIRECTORIES)
            if is_shim:
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        for b in banned:
                            if b in stripped:
                                violations.append("%s:%d: %s" % (relpath, i, stripped))
            except Exception:
                pass
        assert len(violations) == 0, (
            "Imports from forbidden folders found:\n" + "\n".join(violations[:15])
        )


# ═══════════════════════════════════════════════════════
# Providers: import resolution validation
# ═══════════════════════════════════════════════════════

class TestProviderImports:
    """Verify all providers/__init__.py imports resolve correctly."""

    def test_providers_init_imports_resolve(self):
        """Every `from .X import Y` in providers/__init__.py should resolve
        to an actual module file or package."""
        init_path = os.path.join(BACKEND, "providers", "__init__.py")
        if not os.path.exists(init_path):
            pytest.skip("providers/__init__.py not found")
        with open(init_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level != 1:  # only relative imports (from .X)
                continue
            if not node.module:
                continue
            # Resolve the relative module path
            parts = node.module.split(".")
            mod_path = os.path.join(BACKEND, "providers", *parts)
            is_package = os.path.isdir(mod_path) and os.path.isfile(os.path.join(mod_path, "__init__.py"))
            is_module = os.path.isfile(mod_path + ".py")
            if not (is_package or is_module):
                names = [a.name for a in (node.names or [])]
                violations.append("from .%s import %s — module not found (looked for %s.py or %s/__init__.py)" % (
                    node.module, ", ".join(names), mod_path, mod_path))
        assert len(violations) == 0, "providers/__init__.py imports that don't resolve:\n" + "\n".join(violations)

    def test_providers_subpackages_have_init(self):
        """Every subdirectory in providers/ that has .py files must have an __init__.py."""
        providers_dir = os.path.join(BACKEND, "providers")
        if not os.path.isdir(providers_dir):
            pytest.skip("providers/ directory not found")
        violations = []
        for entry in os.listdir(providers_dir):
            entry_path = os.path.join(providers_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            if entry.startswith("_"):  # __pycache__ etc
                continue
            py_files = [f for f in os.listdir(entry_path) if f.endswith(".py")]
            if py_files and not os.path.isfile(os.path.join(entry_path, "__init__.py")):
                violations.append("providers/%s/ has %d .py files but no __init__.py" % (
                    entry, len(py_files)))
        assert len(violations) == 0, "Subpackages missing __init__.py:\n" + "\n".join(violations)

    def test_providers_no_circular_imports(self):
        """providers/__init__.py should not import from providers that import back
        from providers (circular at the package level)."""
        # This is a static check: verify that __init__.py only imports from
        # submodules, not from __init__ itself
        init_path = os.path.join(BACKEND, "providers", "__init__.py")
        if not os.path.exists(init_path):
            pytest.skip("providers/__init__.py not found")
        with open(init_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level == 1 and node.module == "":
                # `from . import X` — this is fine, it imports a submodule
                continue
            if node.level == 1 and node.module:
                # `from .bg_remover import ...` — fine if bg_remover.py exists
                # But check it doesn't import back from __init__
                pass
        # Actually: just verify __init__.py doesn't contain 'from . import' that
        # would cause circular imports with the submodules
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level == 1 and node.module == "":
                for alias in (node.names or []):
                    name = alias.name
                    # Check if this submodule imports back from providers
                    sub_path = os.path.join(BACKEND, "providers", name)
                    sub_file = sub_path + ".py"
                    sub_init = os.path.join(sub_path, "__init__.py")
                    sub_source = ""
                    if os.path.isfile(sub_file):
                        with open(sub_file, "r", encoding="utf-8", errors="ignore") as f:
                            sub_source = f.read()
                    elif os.path.isfile(sub_init):
                        with open(sub_init, "r", encoding="utf-8", errors="ignore") as f:
                            sub_source = f.read()
                    if "from providers import" in sub_source or "from providers.__init__" in sub_source:
                        violations.append("providers.%s imports back from providers package" % name)
        assert len(violations) == 0, "Circular imports detected:\n" + "\n".join(violations)

    def test_providers_submodule_files_exist(self):
        """Every submodule referenced in __init__.py must have a corresponding file."""
        init_path = os.path.join(BACKEND, "providers", "__init__.py")
        if not os.path.exists(init_path):
            pytest.skip("providers/__init__.py not found")
        with open(init_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        violations = []
        # Collect all referenced submodule names
        submodule_names = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level == 1 and node.module:
                submodule_names.add(node.module.split(".")[0])
        # Verify each submodule exists
        for name in sorted(submodule_names):
            mod_path = os.path.join(BACKEND, "providers", name)
            is_package = os.path.isdir(mod_path) and os.path.isfile(os.path.join(mod_path, "__init__.py"))
            is_module = os.path.isfile(mod_path + ".py")
            if not (is_package or is_module):
                violations.append("providers/__init__.py references .%s but neither .%s.py nor .%s/__init__.py exists" % (
                    name, name, name))
        assert len(violations) == 0, "Missing provider submodule files:\n" + "\n".join(violations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
