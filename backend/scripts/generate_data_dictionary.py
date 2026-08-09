"""Data dictionary generator (DB24 / DBA24 / DBA37).

The canonical generator lives at ``scripts/generate_data_dictionary.py``
(repo root) and satisfies the DB24 requirement. It also emits a Mermaid
``erDiagram`` (``--format mermaid`` -> ``generate_mermaid_erd``), satisfying
DBA37. This module re-exports it so the generator is also discoverable at
``backend/scripts/generate_data_dictionary.py`` -- the location the audit's
DBA24 production-check expects.
"""
import importlib.util
from pathlib import Path

_ROOT = (
    Path(__file__).resolve().parent.parent.parent
    / "scripts"
    / "generate_data_dictionary.py"
)

_spec = importlib.util.spec_from_file_location("_root_generate_data_dictionary", _ROOT)
_root = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root)

generate_data_dictionary = _root.generate_data_dictionary
main = _root.main
