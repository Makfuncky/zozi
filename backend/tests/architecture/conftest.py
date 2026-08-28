"""conftest.py for architecture tests."""
import os
import sys

# Add the tests/architecture directory to sys.path so that the test files
# can import the _gen_* helper modules.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# Add the scripts directory to sys.path so that the _gen_* helper modules
# (moved out of tests/) can be imported.
_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(_THIS_DIR)), "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
