"""ZOZI 3-layer coherence gate test.

Enforces the unidirectional dependency contract:

    routers -> controllers -> services -> models   (leaf)
    services -> providers -> EXTERNAL

Run: pytest tests/architecture/test_coherence.py -v

This test is the authoritative CI gate. It must report 0 hard and 0 soft
directional violations. ``scripts/coherence_gate.py`` is the single source of
truth for the layer ordering and violation classification — do not duplicate
or fork its logic here.
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import coherence_gate as cg  # noqa: E402


@pytest.fixture(scope="module")
def gate():
    layers, allmods, graph, model_classes = cg.build()
    hard, soft = cg.directional_violations(layers, allmods, graph)
    return layers, allmods, graph, model_classes, hard, soft


def test_no_hard_directional_violations(gate):
    """No module may import a layer above it (services->controllers, models->services, etc.)."""
    _layers, _allmods, _graph, _mc, hard, _soft = gate
    if hard:
        lines = sorted(f"  {m} -> {r} ({li}->{lj})" for (m, r, li, lj) in hard)
        pytest.fail("Found %d HARD directional violations:\n%s" % (len(hard), "\n".join(lines)))


def test_no_soft_directional_violations(gate):
    """No controllers->routers facade re-exports (routers live in routers, not controllers)."""
    _layers, _allmods, _graph, _mc, _hard, soft = gate
    if soft:
        lines = sorted(f"  {m} -> {r} ({li}->{lj})" for (m, r, li, lj) in soft)
        pytest.fail("Found %d SOFT directional violations:\n%s" % (len(soft), "\n".join(lines)))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
