import re

import pytest

GEO_PATH = "backend/providers/geography/geo.py"
LOCATION_PATTERN = re.compile(r"os\.getenv\(['\"]LOCATION_[A-Z_]+['\"]")


def test_no_raw_os_getenv_for_location_config():
    with open(GEO_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    matches = LOCATION_PATTERN.findall(content)
    assert matches == [], (
        f"Found raw os.getenv for LOCATION_* config in {GEO_PATH}: {matches}"
    )
