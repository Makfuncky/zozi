"""Law 7 gate: allowlist rule — DOMAIN_ALLOWLIST.yaml only shrinks.

Verifies:
  1. DOMAIN_ALLOWLIST.yaml exists and has valid structure.
  2. Entries reference valid domain paths.
  3. Allowlist entries are sanctioned (reference real domains).
  4. The allowlist format is parseable.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_ALLOWLIST_PATH = _BACKEND_ROOT / "DOMAIN_ALLOWLIST.yaml"

_KNOWN_DOMAINS = {
    "accounts", "analytics", "audit", "catalog", "comms", "country",
    "customers", "finance", "governance", "hr", "logistics", "orders",
    "payments", "promotions", "security", "suppliers",
}


class TestAllowlistExists:
    """DOMAIN_ALLOWLIST.yaml must exist."""

    def test_allowlist_file_exists(self):
        assert _ALLOWLIST_PATH.exists(), (
            "DOMAIN_ALLOWLIST.yaml must exist to track temporary cross-domain imports"
        )

    def test_allowlist_is_readable(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_allowlist_has_cross_domain_imports_section(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        assert "cross_domain_imports:" in content


class TestAllowlistEntriesValid:
    """Allowlist entries must reference valid domains."""

    def _get_entries(self) -> list[str]:
        if not _ALLOWLIST_PATH.exists():
            return []
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        return [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("- ")
        ]

    def test_entries_are_sanctioned(self):
        entries = self._get_entries()
        if not entries:
            pytest.skip("No entries in DOMAIN_ALLOWLIST.yaml")
        # At least one entry should reference a known domain
        has_known = False
        for entry in entries:
            for domain in _KNOWN_DOMAINS:
                if f"domains.{domain}" in entry:
                    has_known = True
                    break
            if has_known:
                break
        assert has_known, "Allowlist should contain at least one entry referencing a known domain"

    def test_entries_reference_domains(self):
        entries = self._get_entries()
        if not entries:
            pytest.skip("No entries in DOMAIN_ALLOWLIST.yaml")
        domain_ref_pattern = re.compile(r"domains\.\w+")
        for entry in entries:
            assert domain_ref_pattern.search(entry), (
                f"Allowlist entry does not reference a valid domain path: {entry}"
            )

    def test_entries_have_arrow_separator(self):
        """Entries should use '->' to indicate source -> target."""
        entries = self._get_entries()
        if not entries:
            pytest.skip("No entries in DOMAIN_ALLOWLIST.yaml")
        entries_with_arrow = [e for e in entries if "->" in e]
        assert len(entries_with_arrow) > 0, (
            "At least some allowlist entries should use '->' separator"
        )


class TestAllowlistFormat:
    """Allowlist file format must be valid."""

    def test_file_is_valid_yaml(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        try:
            import yaml
            with open(_ALLOWLIST_PATH, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict)
        except ImportError:
            # If PyYAML not installed, skip
            pytest.skip("PyYAML not installed")
        except Exception as e:
            pytest.fail(f"DOMAIN_ALLOWLIST.yaml is not valid YAML: {e}")

    def test_notes_section_exists(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        assert "notes:" in content, "Allowlist should have a 'notes:' section explaining entries"

    def test_no_duplicate_entries(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        entries = [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("- ")
        ]
        duplicates = [e for e in entries if entries.count(e) > 1]
        if duplicates:
            msg = "\n  ".join(sorted(set(duplicates)))
            pytest.fail(f"Duplicate allowlist entries found:\n  {msg}")


class TestAllowlistOnlyShrinks:
    """The allowlist must only shrink over time (never grow silently).

    This is enforced by tracking the count in a baseline file.
    """

    _BASELINE_PATH = pathlib.Path(__file__).parent / "_allowlist_shrink_baseline.txt"

    def test_allowlist_count_tracked(self):
        if not _ALLOWLIST_PATH.exists():
            pytest.skip("DOMAIN_ALLOWLIST.yaml does not exist")
        content = _ALLOWLIST_PATH.read_text(encoding="utf-8")
        entries = [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("- ")
        ]
        current_count = len(entries)

        if self._BASELINE_PATH.exists():
            baseline_count = int(self._BASELINE_PATH.read_text().strip())
            assert current_count <= baseline_count, (
                f"Allowlist grew from {baseline_count} to {current_count} entries. "
                f"Law 7: allowlist must only shrink. Remove entries before adding new ones."
            )
        else:
            # First run — write baseline
            self._BASELINE_PATH.write_text(str(current_count))
