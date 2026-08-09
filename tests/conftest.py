import os
import sys
from pathlib import Path

# Make the tests/ directory importable so `import q1_rescue_utils` works.
sys.path.insert(0, str(Path(__file__).resolve().parent))
