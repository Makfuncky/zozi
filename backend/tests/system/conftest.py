"""conftest.py for tests/system/ — ensure tests._support is importable."""
import os
import sys
from pathlib import Path

# Add the tests/ directory to sys.path so tests._support can be imported
# by test modules in this directory.
_TESTS_DIR = Path(__file__).resolve().parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

# Also add the backend root for good measure.
_BACKEND_ROOT = _TESTS_DIR.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
