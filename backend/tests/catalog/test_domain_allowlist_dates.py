import yaml
import pytest
from pathlib import Path


def test_removal_dates_are_staggered():
    allowlist_path = Path(__file__).resolve().parents[2] / "DOMAIN_ALLOWLIST.yaml"
    with open(allowlist_path, "r") as f:
        data = yaml.safe_load(f)

    entries = data.get("cross_domain_imports", [])
    dates = [e.get("removal_date") for e in entries]

    assert len(dates) == len(entries), "Every entry must have a removal_date"
    assert len(set(dates)) == len(dates), "removal_date values must be unique (staggered)"
    assert all(d != "2026-10-28" for d in dates), "Uniform removal_date 2026-10-28 must be replaced"


def test_migration_status_present():
    allowlist_path = Path(__file__).resolve().parents[2] / "DOMAIN_ALLOWLIST.yaml"
    with open(allowlist_path, "r") as f:
        data = yaml.safe_load(f)

    entries = data.get("cross_domain_imports", [])
    valid_statuses = {"pending", "in_progress", "completed"}

    for entry in entries:
        status = entry.get("migration_status")
        assert status in valid_statuses, f"Invalid migration_status: {status}"
