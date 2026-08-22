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
        # only domains/ test files surface; a correct resolution must also cover
        # the lower layers that carry real Law 1 debt (and only exist in the
        # real backend root).
        baseline = load_baseline()
        covered = {rel.split("/")[0] for rel in baseline}
        assert covered & {"infrastructure", "providers", "rbac", "kernel"}, (
            "Import-laws baseline only covers domains — the scanner likely "
            "resolved the wrong backend root and is enforcing nothing. Check "
            "_gen_import_laws_baseline.BACKEND resolution."
        )
