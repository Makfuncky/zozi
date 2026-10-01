"""
Regression test for FILE-101: .github/workflows/rollback.yml

The rollback workflow is an emergency recovery workflow and MUST trigger
on `workflow_dispatch` only (manual). Automatic triggers such as
`deployment_status` are forbidden because they can cause unintended
rollbacks on transient deployment failures.
"""

import pathlib

import yaml

ROLLBACK_WORKFLOW = pathlib.Path(__file__).resolve().parents[3] / ".github" / "workflows" / "rollback.yml"


def _get_triggers(data):
    on = data.get("on")
    if on is None:
        on = data.get(True)
    return on or {}


def test_rollback_workflow_manual_trigger_only():
    data = yaml.safe_load(ROLLBACK_WORKFLOW.read_text(encoding="utf-8"))
    triggers = _get_triggers(data)

    assert "workflow_dispatch" in triggers, (
        "rollback.yml must define workflow_dispatch trigger"
    )
    assert "deployment_status" not in triggers, (
        "rollback.yml must NOT define deployment_status trigger; "
        "emergency recovery must be manual-only"
    )
    assert len(triggers) == 1, (
        f"rollback.yml must have exactly one trigger, found: {list(triggers)}"
    )
