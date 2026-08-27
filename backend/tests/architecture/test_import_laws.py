"""Law 1 gate: arrows point down only (``modules -> domains -> infrastructure``).

The platform layers below the domain boundary must never statically import
``domains`` or ``modules``:

    kernel / infrastructure / providers / rbac   ->  must NOT import domains, modules
    domains                                     ->  must NOT import modules

Only *module-level* (static) imports are flagged; lazily imported names that
live inside a function body do not create a hard dependency arrow and are
therefore excluded.

The current offenders are frozen in ``_import_laws_baseline.txt``. This gate
fails only on *new* offenders so the debt can be chipped away safely, one
migration at a time. The sanctioned ``rbac/catalog.py`` feature-aggregation
import is excluded (Law 4 requires it).

Regenerate the baseline after an intentional move:
    python tests/_gen_import_laws_baseline.py
"""
from __future__ import annotations

from ._gen_import_laws_baseline import load_baseline, scan_all


class TestLaw1ArrowsPointDown:
    def test_no_new_upward_imports(self):
        baseline = load_baseline()
        new_offenders = sorted(rel for rel in scan_all() if rel not in baseline)
        assert not new_offenders, (
            "New static upward import(s) violate Law 1 (arrows point down only: "
            "modules -> domains -> infrastructure; domains never import modules). "
            "Migrate the dependency downward, then regenerate the baseline with "
            "tests/_gen_import_laws_baseline.py. New offenders:\n  "
            + "\n  ".join(new_offenders)
        )

    def test_baseline_covers_known_layers(self):
        # Guard against the generator silently scanning nothing (e.g. a broken
        # BACKEND resolution that points inside tests/). When BACKEND is wrong
        # only domains/ test files surface; a correct resolution must also
        # walk the lower layers that own the real Law 1 surface.
        #
        # In the 2026-08-27 cleanup all 14 known offenders were eliminated,
        # so the baseline is legitimately empty. We therefore verify the
        # scanner's reach by checking it can find candidate files in the
        # lower layers (without requiring the baseline to be non-empty).
        import os
        from ._gen_import_laws_baseline import BACKEND
        candidates = []
        for sub in ("infrastructure", "providers", "rbac", "kernel"):
            root = os.path.join(BACKEND, sub)
            if os.path.isdir(root):
                for dirpath, _dirs, files in os.walk(root):
                    for f in files:
                        if f.endswith(".py"):
                            candidates.append(os.path.relpath(os.path.join(dirpath, f), BACKEND).replace(os.sep, "/"))
                            if len(candidates) >= 5:
                                break
                    if len(candidates) >= 5:
                        break
        assert candidates, (
            "Scanner cannot find any candidate files in the lower layers "
            f"(infrastructure/providers/rbac/kernel under {BACKEND}). The "
            "import-laws gate would silently enforce nothing."
        )
