"""conftest.py for architecture tests."""
import os
import sys

# Add the tests/architecture directory to sys.path so that the test files
# can import the _gen_* helper modules.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
