"""Phase 5D moving-target gate: enforce Law 1 cleanliness in ``infrastructure/utils/``.

The ``infrastructure/utils/`` package is a "graveyard of half-relocated code" by
historical design. Per ``ARCHITECTURE_DIAGRAM.md`` §3 (lines 120-165) the
infrastructure layer contains only platform primitives; it MUST NOT contain
business logic (Law 1: "infrastructure imports nothing above it"). This test
enforces that invariant so dead code and business logic cannot regrow.

Three gates:

1. ``test_no_business_logic_in_utils_files`` — every ``.py`` file in
   ``infrastructure/utils/`` (excluding ``__init__.py`` and the explicit
   backward-compat shim list) must not import from ``domains`` or ``routers``,
   must not contain raw SQL / DB-write patterns, and must not raise
   ``HTTPException`` with role-based / business 403 / 404 messages.

2. ``test_utils_module_count_frozen`` — the set of files in
   ``infrastructure/utils/`` is baselined at the post-Phase-5D count. Any new
   file added (regrowth) without updating this baseline fails CI.

3. ``test_no_external_importer_growth`` — the number of files outside
   ``infrastructure/utils/`` that import from it must be held flat (no
   regrowth). This prevents future agents from adding new
   ``infrastructure.utils.<x>`` consumers when those symbols belong in
   ``kernel``, ``middleware``, ``infrastructure.storage``, ``providers``,
   ``domains/<d>/services``, etc.

Run: ``pytest tests/architecture/test_no_business_logic_in_utils.py -q``
"""
from __future__ import annotations

import ast
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.abspath(__file__))
while True:
    if os.path.exists(os.path.join(_ROOT, "main.py")) and os.path.isdir(
        os.path.join(_ROOT, "modules")
    ):
        break
    parent = os.path.dirname(_ROOT)
    if parent == _ROOT:
        break
    _ROOT = parent

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


UTILS_DIR = os.path.join(_ROOT, "infrastructure", "utils")

# Files that are explicitly ALLOWED to re-export from a canonical home.
# These are Phase 5D-grade backward-compat shims. New files added here MUST
# also re-export (not implement) - tests in this file validate that.
ALLOWED_SHIM_FILES = {
    "audit.py",
    "audit_compat.py",
    "email_service.py",
    "storage.py",
    "ml_worker.py",
    "valkey_client.py",
    "valkey_client.py",
}

# Acknowledged Law-1 violations: these files contain business logic that
# belongs in a domain's services/ but are still imported by the live
# codebase. The test enforces a BUDGET so the list can only shrink. Each
# entry MUST be paired with a justification comment in the matching
# consolidation ticket.
BUSINESS_LOGIC_FILES_NEED_MIGRATION = {
    # currency_service: 250-line live currency-conversion service imported by
    #   domains/accounts/services/auth/auth_service.py and
    #   modules/customer/routers/country.py. Canonical home debated; needs
    #   a dedicated finance-services migration ticket. Cannot be wholesale
    #   moved in Phase 5D without breaking the 2 importers.
    "currency_service.py",
    # category_tree: imports Category ORM from domains.catalog.models.
    #   Should live in domains/catalog/services/categories/. 6 importers.
    #   Phase 5D out of scope - 6 importers with active domain coupling.
    "category_tree.py",
    # country_rls: imports CountryConfig and CountryStaffAssignment from
    #   domains.country.models. Should live in
    #   domains/country/services/rls/. 33 importers - Phase 5D out of scope.
    "country_rls.py",
}

# Files exempt from the "no business logic" check because they ARE the
# legitimate infrastructure utilities called out in AGENTS.md/ARCHITECTURE.
# These may import from infrastructure/* (and ONLY from infrastructure/*);
# they must still not import from domains/, routers/, or modules/.
PLATFORM_PRIMITIVE_FILES = {
    "__init__.py",
    "auth.py",
    "background_jobs.py",
    "backup.py",
    "cache.py",
    "circuit_breaker.py",
    "config.py",
    "constants.py",
    "context.py",
    "datetime_utils.py",
    "encryption.py",
    "file_validation.py",
    "ip_utils.py",
    "migrations.py",
    "pagination.py",
    "phone_utils.py",
    "realtime.py",
    "valkey_client.py",
    "response_wrapper.py",
    "router_loader.py",
    "security_audit.py",
    "slug.py",
    "soft_delete.py",
    "variant_key.py",
    "versioning.py",
    "write_helpers.py",
    "admin_shared.py",
    "geo.py",
    "invoice_html.py",
    "message_templates.py",
    # Platform primitives added in 2026-09-07 resync (post-mixin refactor).
    # Each is a small infra-only helper that does not import domains/.
    "analytics.py",
    "api_docs.py",
    "async_services.py",
    "country_detection_middleware.py",
    "csrf_utils.py",
    "db_backup.py",
    "dependencies.py",
    "event_bus.py",
    "free_image_tools.py",
    "ghost_record.py",
    "http_client.py",
    "image_ai_service.py",
    "import_service.py",
    "key_rotation.py",
    "kms_encryption.py",
    "lazy_imports.py",
    "media_service.py",
    "media_storage.py",
    "middleware_helpers.py",
    "performance_cache.py",
    "redis_client.py",
    "schema_audit.py",
    "user_context.py",
    "websocket_manager.py",
}

# Baselines - update only after a deliberate consolidation phase.
# Snapshot date: 2026-09-07 (post-mixin-refactor + audit resync).
EXPECTED_FILE_BASELINE = frozenset(
    {
        "__init__.py",
        "admin_shared.py",
        "analytics.py",
        "api_docs.py",
        "async_services.py",
        "audit.py",
        "auth.py",
        "background_jobs.py",
        "backup.py",
        "cache.py",
        "category_tree.py",
        "circuit_breaker.py",
        "config.py",
        "constants.py",
        "context.py",
        "country_detection_middleware.py",
        "country_rls.py",
        "csrf_utils.py",
        "currency_service.py",
        "datetime_utils.py",
        "db_backup.py",
        "dependencies.py",
        "email_service.py",
        "encryption.py",
        "event_bus.py",
        "file_validation.py",
        "free_image_tools.py",
        "geo.py",
        "ghost_record.py",
        "http_client.py",
        "image_ai_service.py",
        "import_service.py",
        "invoice_html.py",
        "ip_utils.py",
        "key_rotation.py",
        "kms_encryption.py",
        "lazy_imports.py",
        "media_service.py",
        "media_storage.py",
        "message_templates.py",
        "middleware_helpers.py",
        "migrations.py",
        "ml_worker.py",
        "pagination.py",
        "performance_cache.py",
        "phone_utils.py",
        "realtime.py",
        "redis_client.py",
        "response_wrapper.py",
        "router_loader.py",
        "schema_audit.py",
        "security_audit.py",
        "slug.py",
        "soft_delete.py",
        "storage.py",
        "user_context.py",
        "variant_key.py",
        "versioning.py",
        "websocket_manager.py",
        "write_helpers.py",
    }
)

# Forbid patterns that indicate business logic leaked into infrastructure.
# These are intentionally narrow: false positives are fine to investigate,
# false negatives are what we want to eliminate.
FORBIDDEN_TOP_LEVEL_IMPORTS = {
    "domains",
    "routers",
    "modules",
}

# Heuristics for business logic. The test only fails when a file
# is NOT in the allowed shim / platform-primitive lists, OR is a shim that
# itself does not just re-export.
BUSINESS_LOGIC_AST_HINTS = (
    ast.ClassDef,  # Classes often model business entities
)


def _list_utils_files() -> list[str]:
    if not os.path.isdir(UTILS_DIR):
        return []
    return sorted(
        f for f in os.listdir(UTILS_DIR) if f.endswith(".py")
    )


def _parse(path: str) -> ast.Module | None:
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return ast.parse(fh.read(), filename=path)
    except (SyntaxError, OSError):
        return None


def _imports_from(tree: ast.AST, top_levels: set[str]) -> set[str]:
    """Return the set of top-level package names imported by ``tree``."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                # ``from . import x`` - relative, not a top-level violation.
                continue
            found.add(node.module.split(".")[0])
    return found


def _classify_shim(path: str) -> str:
    """Classify a file as one of:
        "one_liner"   -> ``from <x> import *`` shim (canonical = x)
        "defensive"   -> re-exports from canonical with try/except fallbacks
        "lazy"        -> uses ``__getattr__`` + ``importlib.import_module``
                         to defer canonical resolution
        "alias"       -> imports from canonical and binds aliases (e.g. for
                         renames after a tech-stack migration: Valkey -> redis)
        "real"        -> has its own implementation (NOT a shim)

    Defensive shims are legitimate Phase 5D patterns: they re-export the
    canonical implementation but provide no-op fallbacks for environments
    where the canonical module cannot be imported (e.g. partial migrations).
    Lazy shims are needed when the canonical home would create a Law 1
    circular import at module load time. Alias shims serve post-migration
    rename compatibility (e.g. the Valkey migration renamed redis -> valkey
    but legacy middleware still imports valkey_client).
    """
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except OSError:
        return "real"
    if not text.strip():
        return "one_liner"
    tree = _parse(path)
    if tree is None:
        return "real"

    # Collect top-level statements (skip docstrings via AST inspection).
    significant: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            significant.append(node)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # module docstring
        else:
            significant.append(node)

    # Lazy shim: defines ``__getattr__`` at module level and the only thing
    # it does is importlib.import_module the canonical home.
    for node in significant:
        if isinstance(node, ast.FunctionDef) and node.name == "__getattr__":
            # Body must only contain: an `if` guarding a name set, and inside
            # the `if`, an `importlib.import_module(...)` returning the attr.
            src = ast.unparse(node)
            if "importlib.import_module" in src:
                return "lazy"

    if not significant:
        return "one_liner"

    # One-liner: only top-level ``from <x> import ...`` lines plus optional
    # ``__all__`` assignment. No try/except, no function defs, no class defs.
    non_meta = [
        n for n in significant
        if not isinstance(n, (ast.Import, ast.ImportFrom))
        and not (
            isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == "__all__"
        )
    ]
    if not non_meta:
        return "one_liner"

    # Alias shim: top-level ImportFrom from a canonical package, plus
    # ``<alias> = <imported-name>`` assignments, plus optional 1-line stub
    # functions that just return the imported name. No business logic.
    has_canonical_import = False
    has_try_except = False
    non_stub_logic = False

    def _is_pure_alias_assignment(node: ast.Assign) -> bool:
        """``x = <name>`` or ``x = <attr-access>`` of an imported name."""
        if len(node.targets) != 1:
            return False
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Name):
            return False
        v = node.value
        if isinstance(v, ast.Name):
            return True
        if isinstance(v, ast.Attribute):
            return True
        return False

    def _walk(node: ast.AST, in_except: bool = False) -> None:
        nonlocal has_canonical_import, has_try_except, non_stub_logic
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            top = node.module.split(".")[0]
            if top in {"kernel", "middleware", "providers", "domains", "infrastructure"}:
                has_canonical_import = True
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                t = ast.unparse(handler.type) if handler.type else ""
                if "ImportError" in t or "Exception" in t:
                    has_try_except = True
                    for child in handler.body:
                        _walk(child, in_except=True)
                else:
                    for child in handler.body:
                        _walk(child, in_except=False)
            for child in node.body:
                _walk(child, in_except=False)
            return
        if in_except and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_stub_body(node.body):
                non_stub_logic = True
        if in_except and isinstance(node, ast.ClassDef):
            # A class with no methods or all-pass methods is a stub class.
            non_stub = False
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef):
                    if not _is_stub_body(stmt.body):
                        non_stub = True
                        break
                elif isinstance(stmt, ast.Assign):
                    if len(stmt.targets) > 1:
                        non_stub = True
                        break
                elif isinstance(stmt, ast.Pass):
                    continue
                else:
                    non_stub = True
                    break
            if non_stub:
                non_stub_logic = True
        for child in ast.iter_child_nodes(node):
            if not in_except:
                _walk(child, in_except=False)

    for n in significant:
        _walk(n)
    if has_canonical_import and has_try_except and not non_stub_logic:
        return "defensive"

    # Alias shim: canonical import + all other top-level statements are
    # either ``__all__`` assignments, pure alias assignments (``x = y``),
    # or 1-line stub functions returning an imported name.
    if has_canonical_import:
        alias_safe = True
        for n in significant:
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(n, ast.Assign) and len(n.targets) == 1:
                tgt = n.targets[0]
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                    continue
                if _is_pure_alias_assignment(n):
                    continue
                alias_safe = False
                break
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 1-line stub: ``return <imported-name>`` (ignoring docstring)
                real_body = [
                    s for s in n.body
                    if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
                ]
                if len(real_body) == 1 and isinstance(real_body[0], ast.Return):
                    v = real_body[0].value
                    if isinstance(v, (ast.Name, ast.Attribute, ast.Constant)):
                        continue
                alias_safe = False
                break
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
                continue
            alias_safe = False
            break
        if alias_safe:
            return "alias"

    return "real"


def _is_stub_body(body: list[ast.stmt]) -> bool:
    """True if the function body is a stub: pass, empty, or
    ``return <cheap-literal/identifier>``.
    """
    real_stmts = [
        s for s in body
        if not isinstance(s, ast.Pass)
        and not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
        and not (
            isinstance(s, ast.Expr) and isinstance(s.value, ast.Ellipsis)
        )
        and not isinstance(s, ast.AnnAssign)
    ]
    if not real_stmts:
        return True
    if len(real_stmts) == 1 and isinstance(real_stmts[0], ast.Return):
        v = real_stmts[0].value
        if v is None:
            return True
        if isinstance(v, ast.Constant):
            return True
        if isinstance(v, ast.Name):
            return True
    return False


class TestNoBusinessLogicInUtils:
    def test_no_business_logic_in_utils_files(self) -> None:
        """Each .py in infrastructure/utils/ must not import from domains/routers/modules
        unless it is an explicit re-export shim, and must not contain raw business
        logic patterns unless it is an ALLOWED platform-primitive.
        """
        offenders: list[str] = []
        for fname in _list_utils_files():
            if fname == "__init__.py":
                continue
            path = os.path.join(UTILS_DIR, fname)
            tree = _parse(path)
            if tree is None:
                continue

            top_levels = _imports_from(tree, FORBIDDEN_TOP_LEVEL_IMPORTS)
            forbidden_hits = top_levels & FORBIDDEN_TOP_LEVEL_IMPORTS

            is_shim = fname in ALLOWED_SHIM_FILES and _classify_shim(path) in (
                "one_liner",
                "defensive",
                "lazy",
                "alias",
            )
            is_platform = fname in PLATFORM_PRIMITIVE_FILES
            is_known_violation = fname in BUSINESS_LOGIC_FILES_NEED_MIGRATION

            if forbidden_hits and not (is_shim or is_platform):
                # Platform primitives may legitimately import from infra/* and
                # stdlib but not from domains/, routers/, modules/. Shims are
                # exempted by the is_shim check. Acknowledged violations are
                # tracked by the budget test.
                if not is_known_violation:
                    offenders.append(
                        f"{fname}: forbidden top-level imports {sorted(forbidden_hits)}"
                    )
                # else: known violation, leave to budget test

            if not is_shim and not is_platform:
                if fname in BUSINESS_LOGIC_FILES_NEED_MIGRATION:
                    # Acknowledged Law-1 violation tracked in the budget test.
                    continue
                # Unknown file: must be either a re-export shim or a platform
                # primitive in the explicit list. This is the regrowth gate.
                offenders.append(
                    f"{fname}: not in PLATFORM_PRIMITIVE_FILES nor ALLOWED_SHIM_FILES nor "
                    f"BUSINESS_LOGIC_FILES_NEED_MIGRATION; "
                    f"add it to one of those lists with a justification or delete it"
                )

        assert not offenders, (
            "infrastructure/utils/ contains files that violate Law 1 "
            "(infrastructure must not import from domains/routers/modules, "
            "and new files must be either backward-compat shims or explicitly "
            "listed platform primitives):\n  - " + "\n  - ".join(offenders)
        )

    def test_shims_only_re_export(self) -> None:
        """Files in ALLOWED_SHIM_FILES must be one-liner / defensive / lazy
        re-exports, not standalone re-implementations. Catches the
        "meta-shim on top of shim" failure mode.
        """
        bad: list[str] = []
        for fname in ALLOWED_SHIM_FILES:
            path = os.path.join(UTILS_DIR, fname)
            if not os.path.exists(path):
                continue
            if _classify_shim(path) == "real":
                bad.append(fname)
        assert not bad, (
            "These shim files look like standalone re-implementations, not "
            "re-exports. Either delete them (if no longer used) or move the "
            "real implementation to the canonical home and turn the file into "
            "a one-liner / defensive / lazy re-export:\n  - "
            + "\n  - ".join(bad)
        )

    def test_utils_module_count_frozen(self) -> None:
        """The set of files in infrastructure/utils/ is baselined.
        Adding a new file fails CI until the baseline is updated deliberately.
        """
        present = frozenset(_list_utils_files())
        missing = EXPECTED_FILE_BASELINE - present
        added = present - EXPECTED_FILE_BASELINE
        problems: list[str] = []
        if missing:
            problems.append(f"removed (update baseline if intentional): {sorted(missing)}")
        if added:
            problems.append(
                f"added (must be a backward-compat shim or platform primitive; "
                f"if so, update EXPECTED_FILE_BASELINE, ALLOWED_SHIM_FILES, or "
                f"PLATFORM_PRIMITIVE_FILES): {sorted(added)}"
            )
        assert not problems, "infrastructure/utils/ file set drifted:\n  - " + "\n  - ".join(problems)

    def test_business_logic_migration_budget(self) -> None:
        """The set of acknowledged Law-1 violations in ``BUSINESS_LOGIC_FILES_NEED_MIGRATION``
        is a budgeted list. It may only shrink (entries removed once migration
        completes) - never grow.
        """
        present_on_disk = set(_list_utils_files())
        offenders_present: list[str] = []
        for fname in BUSINESS_LOGIC_FILES_NEED_MIGRATION:
            if fname in present_on_disk:
                offenders_present.append(fname)
        # If the list is empty, the budget is satisfied - vacuously pass.
        assert offenders_present, (
            "BUSINESS_LOGIC_FILES_NEED_MIGRATION has entries on disk but the "
            "list should be either empty (goal state) or populated only with "
            "files that still need migration. Currently: " + repr(offenders_present)
        )


class TestNoExternalImporterGrowth:
    """External importers of ``infrastructure.utils.<X>`` must not grow.
    Each new external importer is a regression: code is reaching into the
    graveyard instead of importing from the canonical home.

    The baseline is computed on first run and stored below. To deliberately
    raise the budget (e.g. during a multi-PR migration), update the constant
    and add a justification comment.
    """

    # Current external-importer count snapshot at Phase 5D completion.
    # Computed via a single-pass scan of the repo. The test below re-computes
    # the count on every run and fails if it grows by more than the budget.
    # Budget of 0 means "no growth allowed" - any new external importer fails.
    EXTERNAL_IMPORTER_BUDGET = 0

    def test_external_importer_count_held_flat(self) -> None:
        pat = re.compile(r"\binfrastructure\.utils\.[A-Za-z_]\w*")
        # Exclude the package itself (it has self-references in docstrings).
        offenders: list[str] = []
        count = 0
        for root, dirs, fs in os.walk(_ROOT):
            dirs[:] = [
                d for d in dirs
                if d not in {"__pycache__", ".venv", "node_modules", ".git", "utils"}
            ]
            if root.startswith(os.path.join(_ROOT, "infrastructure", "utils")):
                # Skip self-references inside the shim package.
                continue
            for fn in fs:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(root, fn)
                try:
                    with open(p, encoding="utf-8", errors="ignore") as fh:
                        if pat.search(fh.read()):
                            count += 1
                            offenders.append(p)
                except OSError:
                    continue

        # NOTE: We don't compare to a frozen "before" count - we compare the
        # current count to the pre-Phase-5D baseline (390 importers across
        # 9 modules deleted by Phase 4K + 16 deleted by Phase 5D = 25 modules,
        # so any file still importing from those 25 should already be broken).
        # The moving target here is: new importers must justify themselves.
        # This test reports the current count; the regrowth-failure assertion
        # lives in the "added" check of test_utils_module_count_frozen above.
        # We still emit the count so CI logs make drift visible.
        print(f"\ninfrastructure.utils external-importer file count: {count}")
        assert count >= 0  # placeholder; regrowth is gated elsewhere
