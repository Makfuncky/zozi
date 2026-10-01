import pathlib
import re

import pytest
import yaml

ALERTS_PATH = pathlib.Path(__file__).resolve().parents[2] / ".." / "monitoring" / "alerts.yml"


def test_alert_rules_have_runbook_url():
    alerts_path = ALERTS_PATH.resolve()
    with alerts_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    rules = []
    for group in data.get("groups", []):
        for rule in group.get("rules", []):
            rules.append(rule)

    assert rules, "alerts.yml must define at least one alert rule"

    missing = []
    for rule in rules:
        annotations = rule.get("annotations", {})
        if not annotations.get("runbook_url"):
            missing.append(rule.get("alert", "<unnamed>"))

    assert not missing, f"alert rules missing runbook_url: {missing}"


def test_runbook_urls_point_to_docs_runbooks():
    alerts_path = ALERTS_PATH.resolve()
    with alerts_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    bad = []
    for group in data.get("groups", []):
        for rule in group.get("rules", []):
            url = rule.get("annotations", {}).get("runbook_url", "")
            if url and "docs/runbooks/" not in url:
                bad.append((rule.get("alert"), url))

    assert not bad, f"runbook_url does not point to docs/runbooks/: {bad}"


def test_all_five_alert_rules_present():
    alerts_path = ALERTS_PATH.resolve()
    with alerts_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    names = {
        rule.get("alert")
        for group in data.get("groups", [])
        for rule in group.get("rules", [])
    }
    expected = {
        "DatabaseConnectionPoolExhausted",
        "BackendErrorRateHigh",
        "APIHighLatency",
        "SentryNewErrors",
        "SlowDatabaseQueries",
    }
    missing = expected - names
    assert not missing, f"missing expected alert rules: {missing}"