import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
sys.path.insert(0, str(ROOT / "backend"))

from config import Settings  # noqa: E402

s = Settings(
    app_env="test",
    secret_key="S" * 64,
    field_encryption_key="F" * 64,
    field_encryption_salt="a" * 32,
    audit_chain_key="a" * 32,
)
r = repr(s)
print("repr leaks secret_key plaintext      :", ("S" * 64) in r)
print("repr leaks field_encryption_key      :", ("F" * 64) in r)
print("repr leaks audit_chain_key (32 chars):", "audit_chain_key='" + ("a" * 32) in r)
print("model_fields['secret_key'].json_schema_extra =", Settings.model_fields["secret_key"].json_schema_extra)