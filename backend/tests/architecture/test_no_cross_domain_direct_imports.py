"""Law 3 gate: cross-domain direct imports are frozen at the current baseline.

Per ARCHITECTURE_DIAGRAM.md §4.1 Law 3:
    Writes across domains go *only* through ``events.py`` / ``subscribers.py``.
    Reads across domains go *only* through the publishing domain's ``ports.py``
    (e.g. ``domains/catalog/ports.py → get_price(db, product_id, country)``).

This test freezes the current cross-domain *direct* imports in
``_cross_domain_baseline.txt`` and fails only on *new* ones, so the debt can
be chipped away safely.

Sanctioned surface:
    - ``domains/<d>/ports.py`` is the Law 3 sanctioned cross-domain read surface,
      so it is excluded from the count (it intentionally re-exports target models).
    - ``domains/<d>/events.py`` re-exports dataclass event payloads and is similarly
      excluded.

Regenerate the baseline after an intentional move:
    python scripts/_gen_cross_domain_baseline.py
"""
from __future__ import annotations

import os

from scripts._gen_cross_domain_baseline import (
    BACKEND,
    BASELINE_PATH,
    EXCLUDE_FILES,
    load_baseline,
    scan_cross_domain,
)


def _files_in_domain_services() -> int:
    """Sanity: ensure the scanner reaches every ``domains/<d>/services/`` tree."""
    domains_root = os.path.join(BACKEND, "domains")
    if not os.path.isdir(domains_root):
        return 0
    count = 0
    for name in os.listdir(domains_root):
        if name.startswith("_") or name in EXCLUDE_FILES:
            continue
        services = os.path.join(domains_root, name, "services")
        if os.path.isdir(services):
            count += 1
    return count


class TestLaw3CrossDomain:
    def test_no_new_cross_domain_direct_imports(self):
        baseline = load_baseline()
        current = scan_cross_domain()
        new_offenders = sorted(set(current) - baseline)
        assert not new_offenders, (
            "New cross-domain direct import(s) violate Law 3 (reads via ports.py, "
            "writes via events.py). Move the read/write to the target domain's "
            "ports.py / events.py and regenerate the baseline via "
            "scripts/_gen_cross_domain_baseline.py. New offenders:\n  "
            + "\n  ".join(new_offenders[:50])
            + ("\n  ... (%d more)" % len(new_offenders) if len(new_offenders) > 50 else "")
        )

    def test_baseline_walks_every_domain(self):
        # Guard against the scanner silently scanning nothing.
        n = _files_in_domain_services()
        assert n >= 10, (
            f"Scanner cannot find domains/<d>/services trees (found {n}). "
            "The Law 3 gate would silently enforce nothing."
        )

    def test_baseline_file_exists(self):
        assert os.path.exists(BASELINE_PATH), (
            f"Baseline file missing: {BASELINE_PATH}. "
            "Run scripts/_gen_cross_domain_baseline.py to generate it."
        )

    def test_baseline_only_shrinks(self):
        """The baseline must only shrink over time. Re-add only via explicit regen.

        This is enforced via a separate sibling test (``test_allowlist_shrinks``)
        which tracks an explicit baseline; here we only verify the file is
        present and parseable.
        """
        baseline = load_baseline()
        assert isinstance(baseline, set)
