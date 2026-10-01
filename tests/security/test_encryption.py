import os
from pathlib import Path


def test_no_raw_os_getenv_for_field_encryption_key():
    encryption_path = Path(__file__).resolve().parents[2] / "backend" / "infrastructure" / "security" / "encryption.py"
    source = encryption_path.read_text(encoding="utf-8")
    assert 'os.getenv("FIELD_ENCRYPTION_KEY"' not in source
    assert "os.getenv('FIELD_ENCRYPTION_KEY'" not in source
