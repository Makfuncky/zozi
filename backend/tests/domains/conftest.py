"""conftest.py for tests/domains/ — ensure backend root is on sys.path.

Some test files import domain services whose import chain reaches
``infrastructure.*`` modules. Without this conftest, sub-directories
without their own conftest (e.g. ``tests/domains/catalog/``) fail to
resolve ``infrastructure`` / ``providers`` / ``domains`` because the
parent conftest only runs for tests collected under ``tests/`` and the
local conftests only run for their sub-trees.

Also handles package shadowing: empty ``__init__.py`` files in test
sub-directories (e.g. ``tests/kernel/__init__.py``) can shadow real
backend packages of the same name (``backend/kernel/``). Putting the
backend root at sys.path[0] before any test imports ensures the real
packages win.
"""
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_TESTS_DIR = _THIS_DIR.parent
_BACKEND_ROOT = _TESTS_DIR.parent

# Remove ALL existing references to these dirs so we can pin them in
# the correct order (backend first to win over any test shadowing).
for _p in (str(_BACKEND_ROOT), str(_TESTS_DIR)):
    while _p in sys.path:
        sys.path.remove(_p)

sys.path.insert(0, str(_BACKEND_ROOT))
sys.path.insert(1, str(_TESTS_DIR))
