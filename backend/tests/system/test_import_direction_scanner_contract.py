"""ARCHTEST-008 — contract tests for the Law 1/97-106 import-direction scanner.

The scan root of ``tests/system/test_import_direction_all_packages.py`` pointed
inside ``backend/tests/`` instead of at the production ``backend/`` layer
packages. That single wrong constant made the gate

* enforce nothing on production code (the surface Law 1 actually governs), and
* report three false positives — test files importing ``rbac`` / ``providers``
  (a test exercising the provider it wraps) and ``__future__`` / ``sys`` /
  ``_ast_helpers`` (stdlib and a sibling helper, flagged because the allowlist
  was hand-maintained and never gained them).

These tests pin the three properties that bug violated, plus the properties
that keep the gate meaningful:

1. the scan root is the production backend package, never the tests mirror;
2. the modules allowlist is derived from the running interpreter, so no stdlib
   root can ever be reported as a layer crossing;
3. the frozen Law 1 debt is frozen EXACTLY — it can shrink, never grow;
4. the shared rule table still encodes the benchmark's Laws 97/100-104;
5. the scanner reaches every lower layer (guards against silently scanning
   nothing — the sibling guard in ``tests/architecture/test_import_laws.py``);
6. the scanner still BITES: a synthetic upward import is detected, and a lazy
   function-body import is not.

Run: cd backend && python -m pytest tests/system/test_import_direction_scanner_contract.py -q
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from tests._support import laws
from tests.system import test_import_direction_all_packages as gate

_TESTS_ROOT = Path(__file__).resolve().parent.parent


def _scan_module_scope_roots(path: Path) -> list[str]:
    """Independent re-implementation of the module-scope root extraction.

    Deliberately not calling into the gate: this cross-checks the gate rather
    than trusting it.
    """
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    roots: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.append(node.module.split(".")[0])
    return roots


def _live_law1_offenders() -> set[str]:
    """Recompute every Law 1 breach in production, from scratch."""
    live: set[str] = set()
    for layer, forbidden in laws.FORBIDDEN_IMPORT_RULES.items():
        if not forbidden:
            continue
        layer_dir = gate._BACKEND / layer
        if not layer_dir.is_dir():
            continue
        for path in sorted(layer_dir.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            rel = path.relative_to(gate._BACKEND).as_posix()
            try:
                roots = _scan_module_scope_roots(path)
            except SyntaxError:
                live.add(f"{layer}:{rel}:<syntax error>")
                continue
            live.update(f"{layer}:{rel}:{root}" for root in set(roots) if root in forbidden)
    return live


class TestScanRootIsTheProductionBackend:
    """Regression: the scan root used to resolve to ``backend/tests/``."""

    def test_scan_root_holds_the_production_layer_packages(self) -> None:
        assert (gate._BACKEND / "main.py").is_file(), (
            f"scan root {gate._BACKEND} has no main.py — it is not the production "
            "backend package, so Law 1 is being enforced against the wrong tree"
        )
        assert (gate._BACKEND / "modules").is_dir(), (
            f"scan root {gate._BACKEND} has no modules/ — same defect"
        )

    def test_scan_root_is_not_the_tests_mirror(self) -> None:
        assert gate._BACKEND != _TESTS_ROOT, (
            "the Law 1 scan root is the tests directory; layers are only "
            "mirrored there, so the gate enforces nothing on production while "
            "flagging test fixtures that exercise sanctioned seams"
        )
        assert _TESTS_ROOT not in gate._BACKEND.parents, (
            f"scan root {gate._BACKEND} is inside the tests tree {_TESTS_ROOT}"
        )

    def test_tests_mirror_layers_are_not_scanned(self) -> None:
        """A test importing the provider it wraps must not be a Law 1 breach."""
        offenders = {
            offender
            for offender in _live_law1_offenders()
        }
        assert offenders, (
            "expected the frozen production Law 1 debt to still be visible; an "
            "empty set means this contract file and the gate disagree about "
            "what production looks like"
        )
        assert not any(offender.startswith("tests/") for offender in offenders), (
            "a test-file path leaked into the Law 1 offender set"
        )


class TestModuleAllowlistCoversTheWholeStdlib:
    """Regression: ``sys`` and ``__future__`` were reported as layer crossings."""

    @pytest.mark.parametrize("root", ["__future__", "sys", "os", "ast", "typing"])
    def test_common_stdlib_roots_are_allowed(self, root: str) -> None:
        assert root in gate._MODULE_ALLOWED_ROOTS, (
            f"stdlib root '{root}' is not in the modules allowlist; a stdlib "
            "import must never be reported as a Law 1/99 layer crossing"
        )

    def test_allowlist_is_a_superset_of_the_interpreter_stdlib(self) -> None:
        missing = sorted(set(sys.stdlib_module_names) - set(gate._MODULE_ALLOWED_ROOTS))
        assert not missing, (
            f"modules allowlist is missing {len(missing)} stdlib root(s): "
            f"{missing[:10]}. It must be derived from sys.stdlib_module_names so "
            "it cannot go stale again."
        )

    def test_declared_layer_roots_are_still_allowed(self) -> None:
        for root in ("domains", "rbac", "infrastructure", "kernel", "providers", "middleware"):
            assert root in gate._MODULE_ALLOWED_ROOTS, (
                f"'{root}' left the modules allowlist; Law 97 permits modules -> "
                "rbac/domains and the pre-existing platform roots must stay declared"
            )

    def test_cross_module_roots_are_not_allowed(self) -> None:
        for root in ("supplier", "customer", "employee", "logistics"):
            assert root not in gate._MODULE_ALLOWED_ROOTS, (
                f"module root '{root}' must never be an allowed import root "
                "(Law 1/99: a module may not import another module)"
            )


class TestFrozenLaw1DebtIsFrozen:
    """The gate owns test code only; the production breaches it cannot repair
    are frozen EXACTLY, following the sibling baseline pattern in
    ``tests/architecture/_import_laws_baseline.txt``."""

    def test_frozen_debt_is_not_empty(self) -> None:
        frozen = getattr(gate, "_LAW1_FROZEN_DEBT", frozenset())
        assert frozen, (
            "no Law 1 debt is frozen. Either production was repaired — in which "
            "case delete the entries and keep the empty set asserted here — or "
            "the debt was undeclared and the gate is green for the wrong reason."
        )

    def test_frozen_debt_equals_the_live_breaches(self) -> None:
        frozen = set(getattr(gate, "_LAW1_FROZEN_DEBT", frozenset()))
        live = _live_law1_offenders()
        assert frozen == live, (
            "the frozen Law 1 debt drifted from the live breaches.\n"
            f"  new (must be fixed, not frozen): {sorted(live - frozen)}\n"
            f"  stale (must be deleted): {sorted(frozen - live)}\n"
            "Repair the dependency downward, then update the frozen set. It may "
            "only shrink."
        )

    def test_frozen_entries_are_well_formed(self) -> None:
        for entry in getattr(gate, "_LAW1_FROZEN_DEBT", frozenset()):
            layer, rel, root = entry.split(":", 2)
            assert layer in laws.FORBIDDEN_IMPORT_RULES, (
                f"{entry}: '{layer}' has no forbidden-import rule; the frozen set "
                "and the shared rule table have diverged"
            )
            assert root in laws.FORBIDDEN_IMPORT_RULES[layer], (
                f"{entry}: '{root}' is not forbidden for '{layer}', so this entry "
                "freezes a breach that the rule table does not recognise"
            )
            assert (gate._BACKEND / rel).is_file(), (
                f"{entry}: {rel} no longer exists; delete the stale frozen entry"
            )


class TestSharedRuleTableMatchesTheBenchmark:
    """``laws.FORBIDDEN_IMPORT_RULES`` is the single source of the forbidden set.
    Pin it to ARCHITECTURE_STACK.md Laws 97 / 100 / 101 / 102 / 103 / 104."""

    def test_rule_table_is_exactly_the_benchmark_derivation(self) -> None:
        assert laws.FORBIDDEN_IMPORT_RULES == {
            # Law 97 + 99: modules -> {rbac, domains}; domains never reach up.
            "domains": ("modules", "rbac"),
            # Law 102: infrastructure -> domains/modules/rbac/providers forbidden.
            "infrastructure": ("domains", "modules", "rbac", "providers"),
            # Law 101: kernel is the universal foundation; nothing above it.
            "kernel": (
                "domains", "modules", "rbac", "providers",
                "infrastructure", "jobs", "middleware",
            ),
            # Law 100: providers are pure wrappers.
            "providers": ("domains", "modules", "rbac", "jobs", "middleware"),
            # Law 103: jobs consume domains/infrastructure/providers only.
            "jobs": ("modules", "middleware"),
            # Law 104: middleware is the HTTP edge -> infrastructure + rbac only.
            "middleware": ("domains", "modules"),
        }

    def test_every_scanned_layer_has_a_rule(self) -> None:
        missing = [layer for layer in gate._LOWER_LAYERS if layer not in laws.FORBIDDEN_IMPORT_RULES]
        assert not missing, (
            f"layers {missing} are scanned by the gate but have no entry in "
            "FORBIDDEN_IMPORT_RULES, so the gate silently enforces nothing there"
        )


class TestScannerStillBites:
    """Positive controls: the gate must detect a real upward import.

    A repointed root is only a fix if the gate is still sharp. These controls
    run the gate's own scan against a synthetic layer tree via ``monkeypatch``;
    nothing is written into the production packages.
    """

    def test_module_scope_upward_import_is_detected(self, tmp_path: Path, monkeypatch) -> None:
        layer_dir = tmp_path / "kernel"
        layer_dir.mkdir()
        (layer_dir / "leaky.py").write_text(
            "from domains.orders.models import Order\n", encoding="utf-8"
        )
        (layer_dir / "lazy.py").write_text(
            "def load():\n    from domains.orders.models import Order\n    return Order\n",
            encoding="utf-8",
        )
        (layer_dir / "type_only.py").write_text(
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from domains.orders.models import Order\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(gate, "_BACKEND", tmp_path)

        offenders = gate._lower_layer_violations("kernel")
        assert "kernel:kernel/leaky.py:domains" in offenders, (
            "the scanner no longer detects a module-scope upward import; Law 1 "
            "would be unenforced"
        )
        assert "kernel:kernel/lazy.py:domains" not in offenders, (
            "a function-body import was reported; it creates no import-time arrow"
        )
        assert "kernel:kernel/type_only.py:domains" not in offenders, (
            "a TYPE_CHECKING-only import was reported; it is not loaded at runtime"
        )

    def test_unparseable_file_is_reported_not_skipped(self, tmp_path: Path, monkeypatch) -> None:
        layer_dir = tmp_path / "kernel"
        layer_dir.mkdir()
        (layer_dir / "broken.py").write_text("def oops(:\n", encoding="utf-8")
        monkeypatch.setattr(gate, "_BACKEND", tmp_path)

        offenders = gate._lower_layer_violations("kernel")
        assert any("<syntax error" in offender for offender in offenders), (
            "an unparseable file was silently skipped; a layer of broken source "
            "must not be able to satisfy the gate"
        )

    def test_bom_prefixed_file_is_analysed_not_reported_as_syntax_error(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        layer_dir = tmp_path / "infrastructure"
        layer_dir.mkdir()
        (layer_dir / "bom.py").write_text(
            "\ufefffrom domains.orders.models import Order\n", encoding="utf-8"
        )
        monkeypatch.setattr(gate, "_BACKEND", tmp_path)

        offenders = gate._lower_layer_violations("infrastructure")
        assert offenders == {"infrastructure:infrastructure/bom.py:domains"}, (
            "a UTF-8 BOM made the file unreadable instead of analysed; committed "
            f"backend files carry BOMs and were reported as syntax errors: {offenders}"
        )


class TestScannerReachesEveryLowerLayer:
    """Guard against a silently-empty scan (sibling: test_import_laws.py)."""

    @pytest.mark.parametrize("layer", gate._LOWER_LAYERS)
    def test_layer_directory_exists_in_production(self, layer: str) -> None:
        assert (gate._BACKEND / layer).is_dir(), (
            f"production layer '{layer}/' not found under {gate._BACKEND}; the "
            "gate would skip it and enforce nothing"
        )

    @pytest.mark.parametrize("layer", gate._LOWER_LAYERS)
    def test_layer_contributes_files_to_the_scan(self, layer: str) -> None:
        py_files = [
            path
            for path in (gate._BACKEND / layer).rglob("*.py")
            if path.name != "__init__.py"
        ]
        assert py_files, f"no .py files found under {gate._BACKEND / layer}"

    def test_modules_layer_is_present(self) -> None:
        assert (gate._BACKEND / "modules").is_dir()
        assert any((gate._BACKEND / "modules").rglob("*.py")), "modules/ is empty"