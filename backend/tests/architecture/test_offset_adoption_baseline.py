"""B6 / R6 gate: adoption-layer OFFSET must not regress.

The ``ports.py`` read surface is enforced offset-free by
``test_keyset_pagination.py::test_all_domain_ports_are_offset_free``. This gate
locks the remaining **adoption-layer** OFFSET calls (``domains/*/services``,
``modules/*/routers``, ``infrastructure``, ``middleware``) so the ~245 SQL
``OFFSET`` calls cannot grow while the PART 0.7 deferred sweep (frontend cursor
adoption) is in flight. It fails only on:

  * a NEW file starting to use ``.offset(`` (not in the baseline), or
  * an existing baseline file whose ``.offset(`` count INCREASES.

Removing OFFSET (porting to a ``list_*_keyset`` reader) is allowed and should be
followed by regenerating the baseline::

    python tests/_gen_offset_adoption_baseline.py
"""
from __future__ import annotations

from ._gen_offset_adoption_baseline import load_baseline, scan_all


class TestOffsetAdoptionNoRegress:
    def test_no_new_or_grown_offset_callers(self):
        baseline = load_baseline()
        current = scan_all()

        new_files = sorted(rel for rel in current if rel not in baseline)
        assert not new_files, (
            "New file(s) introduced SQL OFFSET pagination, violating B6 / R6 "
            "(keyset/cursor pagination on hot lists — never OFFSET). Port the "
            "list to a keyset reader (see domains/orders/ports.list_orders_keyset) "
            "or, if intentional, regenerate the baseline with "
            "tests/_gen_offset_adoption_baseline.py. New offenders:\n  "
            + "\n  ".join(new_files)
        )

        grown = sorted(
            rel for rel, cnt in current.items()
            if rel in baseline and cnt > baseline[rel]
        )
        assert not grown, (
            "OFFSET call count GREW in file(s) — B6 / R6 forbids growing SQL "
            "OFFsets on hot lists. Reduce to a keyset reader or regenerate the "
            "baseline only after an intentional migration. Regressed files:\n  "
            + "\n  ".join(f"{rel}: {baseline[rel]} -> {current[rel]}" for rel in grown)
        )

    def test_baseline_covers_known_layers(self):
        # Guard against the scanner silently resolving the wrong backend root
        # (e.g. pointing inside tests/) and enforcing nothing.
        baseline = load_baseline()
        covered = {rel.split("/")[0] for rel in baseline}
        assert covered & {"domains", "modules", "infrastructure", "middleware"}, (
            "OFFSET baseline covers none of the adoption layers — the scanner "
            "likely resolved the wrong backend root and is enforcing nothing. "
            "Check _gen_offset_adoption_baseline.BACKEND resolution."
        )
        # Floor guards against the scanner silently resolving the wrong backend
        # root (enforcing nothing). It is intentionally low: the PART 1.2 keyset
        # sweep removed ~215 adoption-layer OFFSET calls, so the remaining debt
        # is small (a few dozen). Any non-trivial positive count covering the
        # adoption layers proves the scanner is walking the right tree.
        assert sum(baseline.values()) >= 10, (
            "OFFSET baseline unexpectedly small (<10 calls) — verify the scanner "
            "is actually walking domains/ modules/ infrastructure/ middleware/."
        )
